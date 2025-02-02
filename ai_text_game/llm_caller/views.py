import json
import time
from dataclasses import asdict

import openai
from django.conf import settings
from django.db import transaction
from django.http import StreamingHttpResponse
from rest_framework import status
from rest_framework import viewsets
from rest_framework.decorators import action
from rest_framework.pagination import PageNumberPagination
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from .models import APIRequest
from .models import GameInteraction
from .models import GameScenario
from .models import GameStory
from .models import LLMConfig
from .models import LLMModel
from .models import OpenAIKey
from .models import TextExplanation
from .negotiation import IgnoreClientContentNegotiation
from .serializers import APIRequestSerializer
from .serializers import GameScenarioSerializer
from .serializers import GameStorySerializer
from .serializers import LLMModelSerializer
from .tasks import LLMRequestParams
from .tasks import process_openai_request
from .utils import get_openai_client


class StandardResultsSetPagination(PageNumberPagination):
    page_size = 10
    page_size_query_param = "page_size"
    max_page_size = 100


class APIRequestViewSet(viewsets.ModelViewSet):
    serializer_class = APIRequestSerializer
    permission_classes = [IsAuthenticated]
    pagination_class = StandardResultsSetPagination

    def get_queryset(self):
        queryset = APIRequest.objects.filter(user=self.request.user)
        # Add ordering to ensure consistent pagination
        return queryset.order_by("-created_at")

    @transaction.atomic
    def create(self, request, *args, **kwargs):
        # Create request first to validate the model
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        # Get the model instance
        model_name = serializer.validated_data["model_name"]
        model = LLMModel.objects.filter(name=model_name, is_active=True).first()
        if not model:
            return Response(
                {"model_name": f"Model not found: {model_name}"},
                status=status.HTTP_400_BAD_REQUEST,
            )

        # Check quota
        has_quota = model.check_quota(request.user)
        if not has_quota:
            msg = f"Daily quota exceeded for model {model.display_name}"
            return Response(
                {"model_name": msg},
                status=status.HTTP_429_TOO_MANY_REQUESTS,
            )

        # Create and save the request
        api_request = serializer.save(user=request.user)

        llm_params = LLMRequestParams(
            request_id=api_request.id,
            model_name=api_request.model.name,
            temperature=LLMConfig.get_active_config().temperature,
            system_prompt=LLMConfig.get_active_config().system_prompt,
            user_prompt_template=LLMConfig.get_active_config().user_prompt_template,
        )

        # Ensure the actual task execution happens after transaction commit
        transaction.on_commit(
            lambda: process_openai_request.delay(
                asdict(llm_params),
                delay_seconds=getattr(settings, "TASK_DELAY", 0),
            ),
        )
        return Response(serializer.data, status=status.HTTP_201_CREATED)


class ActiveModelsView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        active_models = LLMModel.get_active_models()
        serializer = LLMModelSerializer(
            active_models,
            many=True,
            context={"request": request},
        )
        return Response(serializer.data)


class GameScenarioViewSet(viewsets.ReadOnlyModelViewSet):
    serializer_class = GameScenarioSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        return GameScenario.objects.filter(is_active=True)


def stream_response(model_name, context, interaction):
    try:
        # Add fake response handling
        if settings.FAKE_LLM_REQUEST:
            import re

            # Send fake content in chunks to simulate streaming
            fake_response = "This is a test response. " * 10

            result = re.split(r"(?<= )", fake_response)
            accumulated_response = ""
            for word in result:
                yield f"data: {json.dumps({'content': word})}\n\n"
                accumulated_response += word
                time.sleep(0.05)  # Add small delay to simulate real streaming

            interaction.system_output = accumulated_response
            interaction.status = "completed"
            interaction.save()
            yield "data: [DONE]\n\n"
            return

        # Existing code...
        key = OpenAIKey.get_available_key()
        client = get_openai_client(key)
        accumulated_response = ""
        for chunk in client.chat.completions.create(
            model=model_name,
            messages=context,
            stream=True,
        ):
            if chunk and chunk.choices[0].delta.content:
                content = chunk.choices[0].delta.content
                accumulated_response += content
                # Send the chunk to the client
                yield f"data: {json.dumps({'content': content})}\n\n"

        # Update interaction status when done
        interaction.system_output = accumulated_response
        interaction.status = "completed"
        interaction.save()
        yield "data: [DONE]\n\n"
    except (openai.OpenAIError, ValueError) as e:
        interaction.status = "failed"
        interaction.error = str(e)
        interaction.save()
        yield f"data: {json.dumps({'error': str(e)})}\n\n"


class GameStoryViewSet(viewsets.ModelViewSet):
    serializer_class = GameStorySerializer
    permission_classes = [IsAuthenticated]
    # https://stackoverflow.com/a/78210808/1938012
    content_negotiation_class = IgnoreClientContentNegotiation

    def get_queryset(self):
        return GameStory.objects.filter(user=self.request.user)

    def perform_create(self, serializer):
        return serializer.save(user=self.request.user)

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        story = self.perform_create(serializer)
        return Response(self.get_serializer(story).data, status=status.HTTP_201_CREATED)

    def _create_streaming_response(self, story, interaction):
        """Helper method to create a streaming response."""
        context = story.get_context()
        response = StreamingHttpResponse(
            streaming_content=stream_response(story.model.name, context, interaction),
            content_type="text/event-stream",
        )
        response["Cache-Control"] = "no-cache"
        response["Connection"] = "keep-alive"
        response["X-Accel-Buffering"] = "no"
        return response

    @action(detail=True, methods=["post", "get"])
    @transaction.atomic
    def interact(self, request, pk=None):
        story = self.get_object()

        # Handle GET request for SSE
        if request.method == "GET":
            system_input = request.GET.get("system_input")
        else:
            system_input = request.data.get("system_input")

        if not system_input:
            return Response(
                {"error": "system_input is required"},
                status=status.HTTP_400_BAD_REQUEST,
            )

        # Create the interaction
        interaction = GameInteraction.objects.create(
            story=story,
            role="user",
            system_input=system_input,
            status="pending",
        )

        return self._create_streaming_response(story, interaction)

    @action(detail=True, methods=["post", "get"])
    @transaction.atomic
    def start(self, request, pk=None):
        story = self.get_object()

        # Get the existing system interaction
        try:
            interaction = story.interactions.get(role="system")
        except GameInteraction.DoesNotExist:
            return Response(
                {"error": "System interaction not found"},
                status=status.HTTP_400_BAD_REQUEST,
            )
        if interaction.status != "pending":
            return Response(
                {"error": "System interaction already completed"},
                status=status.HTTP_400_BAD_REQUEST,
            )

        return self._create_streaming_response(story, interaction)

    # NEW: Nested explanations endpoint for a specific game story
    @action(detail=True, methods=["get", "post"])
    def explanations(self, request, pk=None):
        from django.conf import settings

        from .serializers import TextExplanationSerializer

        story = self.get_object()
        if request.method == "GET":
            # Return lookup history for this story
            lookups = story.explanations.all().order_by("-created_at")
            serializer = TextExplanationSerializer(lookups, many=True)
            return Response(serializer.data, status=status.HTTP_200_OK)
        # POST: create a new explanation lookup
        selected_text = request.data.get("selected_text")
        context_text = request.data.get("context_text")
        if not all([selected_text, context_text]):
            return Response(
                {"error": "Missing required fields."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        active_config = LLMConfig.get_active_config(purpose="text_explanation")

        prompt = active_config.system_prompt.format(
            context_text=context_text,
            selected_text=selected_text,
        )

        if settings.FAKE_LLM_REQUEST:
            explanation = "This is a fake explanation based on the provided context."
            time.sleep(0.1)
        else:
            try:
                client = get_openai_client(OpenAIKey.get_available_key())
                response = client.chat.completions.create(
                    model=settings.EXPLANATION_MODEL,
                    messages=[{"role": "user", "content": prompt}],
                    temperature=settings.EXPLANATION_TEMPERATURE,
                )
                explanation = response.choices[0].message.content.strip()
            except (openai.OpenAIError, ValueError) as e:
                return Response(
                    {"error": str(e)},
                    status=status.HTTP_500_INTERNAL_SERVER_ERROR,
                )

        lookup = TextExplanation.objects.create(
            user=request.user,
            story=story,
            selected_text=selected_text,
            context_text=context_text,
            explanation=explanation,
        )
        serializer = TextExplanationSerializer(lookup)
        return Response(serializer.data, status=status.HTTP_200_OK)


class GameSceneGeneratorView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        genre = request.data.get("genre")
        details = request.data.get("details")
        if not genre:
            return Response(
                {"error": "Genre is required"},
                status=status.HTTP_400_BAD_REQUEST,
            )

        active_config = LLMConfig.get_active_config(purpose="scene_generation")

        # Format the details prompt
        details_prompt = (
            f"\n* Additional details of the story: {details}" if details else ""
        )

        # Format the prompt
        prompt = active_config.system_prompt.format(
            genre=genre,
            details_prompt=details_prompt,
        )

        if settings.FAKE_LLM_REQUEST:
            # Return fake data for testing
            scenes = {
                "scenes": [
                    {
                        "level": "A1",
                        "text": "A test scene in A1",
                    },
                    {
                        "level": "A2",
                        "text": "A test scene in A2",
                    },
                    {
                        "level": "B1",
                        "text": "A test scene in B1",
                    },
                    {
                        "level": "B2",
                        "text": "A test scene in B2",
                    },
                    {
                        "level": "C1",
                        "text": "A test scene in C1",
                    },
                    {
                        "level": "C2",
                        "text": "A test scene in C2",
                    },
                ],
            }
        else:
            try:
                client = get_openai_client(OpenAIKey.get_available_key())
                response = client.chat.completions.create(
                    model=settings.SCENE_GENERATION_MODEL,
                    messages=[{"role": "user", "content": prompt}],
                    temperature=0.7,
                    response_format={"type": "json_object"},
                )
                scenes = json.loads(response.choices[0].message.content)
            except (openai.OpenAIError, ValueError) as e:
                return Response(
                    {"error": str(e)},
                    status=status.HTTP_500_INTERNAL_SERVER_ERROR,
                )

        return Response(scenes)
