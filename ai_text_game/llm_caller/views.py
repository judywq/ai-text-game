import json
from dataclasses import asdict

import openai
from django.conf import settings
from django.db import transaction
from rest_framework import status
from rest_framework import viewsets
from rest_framework.decorators import action
from rest_framework.pagination import PageNumberPagination
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from .models import GameScenario
from .models import GameStory
from .models import LLMConfig
from .models import LLMModel
from .models import OpenAIKey
from .models import TextExplanation
from .negotiation import IgnoreClientContentNegotiation
from .serializers import GameScenarioSerializer
from .serializers import GameStorySerializer
from .serializers import LLMModelSerializer
from .serializers import TextExplanationSerializer
from .tasks import TextExplanationParams
from .tasks import process_text_explanation
from .utils import get_openai_client


class StandardResultsSetPagination(PageNumberPagination):
    page_size = 10
    page_size_query_param = "page_size"
    max_page_size = 100


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


class GameStoryViewSet(viewsets.ModelViewSet):
    serializer_class = GameStorySerializer
    permission_classes = [IsAuthenticated]
    pagination_class = StandardResultsSetPagination
    # https://stackoverflow.com/a/78210808/1938012
    content_negotiation_class = IgnoreClientContentNegotiation

    def get_queryset(self):
        queryset = GameStory.objects.filter(created_by=self.request.user)
        return queryset.order_by("-created_at")

    def perform_create(self, serializer):
        return serializer.save(created_by=self.request.user)

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        story = self.perform_create(serializer)
        return Response(self.get_serializer(story).data, status=status.HTTP_201_CREATED)

    # NEW: Nested explanations endpoint for a specific game story
    @action(detail=True, methods=["get", "post"])
    def explanations(self, request, pk=None):
        story = self.get_object()
        if request.method == "GET":
            lookups = story.explanations.all().order_by("-created_at")
            serializer = TextExplanationSerializer(lookups, many=True)
            return Response(serializer.data, status=status.HTTP_200_OK)

        selected_text = request.data.get("selected_text")
        context_text = request.data.get("context_text")
        if not all([selected_text, context_text]):
            return Response(
                {"error": "Missing required fields."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        active_config = LLMConfig.get_active_config(purpose="text_explanation")

        # Create pending explanation
        lookup = TextExplanation.objects.create(
            created_by=request.user,
            story=story,
            selected_text=selected_text,
            context_text=context_text,
            status="pending",
            model=active_config.model,
        )

        # Start async task
        explanation_params = TextExplanationParams(
            explanation_id=lookup.id,
            model_name=active_config.model.name,
            system_prompt=active_config.system_prompt,
            context_text=context_text,
            selected_text=selected_text,
            temperature=active_config.temperature,
        )

        transaction.on_commit(
            lambda: process_text_explanation.delay(
                asdict(explanation_params),
                delay_seconds=getattr(settings, "TASK_DELAY", 0),
            ),
        )

        serializer = TextExplanationSerializer(lookup)
        return Response(serializer.data, status=status.HTTP_201_CREATED)

    @action(
        detail=True,
        methods=["get"],
        url_path="explanations/(?P<explanation_id>[^/.]+)",
    )
    def explanation_detail(self, request, pk=None, explanation_id=None):
        """Get a specific explanation for a story."""
        story = self.get_object()
        try:
            explanation = story.explanations.get(id=explanation_id)
            serializer = TextExplanationSerializer(explanation)
            return Response(serializer.data)
        except TextExplanation.DoesNotExist:
            return Response(
                {"error": "Explanation not found"},
                status=status.HTTP_404_NOT_FOUND,
            )


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
                    model=active_config.model.name,
                    messages=[{"role": "user", "content": prompt}],
                    temperature=active_config.temperature,
                    response_format={"type": "json_object"},
                )
                scenes = json.loads(response.choices[0].message.content)
            except (openai.OpenAIError, ValueError) as e:
                return Response(
                    {"error": str(e)},
                    status=status.HTTP_500_INTERNAL_SERVER_ERROR,
                )

        return Response(scenes)
