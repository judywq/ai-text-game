import json

import openai
from django.conf import settings
from django.http import StreamingHttpResponse
from django.utils.decorators import method_decorator
from django.views.decorators.csrf import csrf_exempt
from langchain_core.output_parsers import JsonOutputParser
from langchain_core.prompts import ChatPromptTemplate
from rest_framework import status
from rest_framework import viewsets
from rest_framework.decorators import action
from rest_framework.pagination import PageNumberPagination
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from .models import APIKey
from .models import GameScenario
from .models import GameStory
from .models import LLMConfig
from .models import LLMModel
from .models import StoryProgress
from .models import TextExplanation
from .negotiation import IgnoreClientContentNegotiation
from .serializers import GameScenarioSerializer
from .serializers import GameStorySerializer
from .serializers import LLMModelSerializer
from .serializers import StoryProgressSerializer
from .serializers import TextExplanationSerializer
from .utils import get_llm_model


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
        user = self.request.user
        if user.is_staff or user.is_superuser:
            # TODO: This is a temporary solution to allow admin to view all stories
            # The admin will be able to view all stories in recent stories list and
            # cannot distinguish between their own and others' stories
            queryset = GameStory.objects.all()
        else:
            queryset = GameStory.objects.filter(created_by=user)
        return queryset.order_by("-created_at")

    def perform_create(self, serializer):
        return serializer.save(created_by=self.request.user)

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        story = self.perform_create(serializer)
        return Response(self.get_serializer(story).data, status=status.HTTP_201_CREATED)

    @action(detail=True, methods=["get"])
    def explanations(self, request, pk=None):
        story = self.get_object()
        lookups = story.explanations.all().order_by("-created_at")
        serializer = TextExplanationSerializer(lookups, many=True)
        return Response(serializer.data, status=status.HTTP_200_OK)

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

    @action(detail=True, methods=["GET"])
    def progress(self, request, pk=None):
        """Get story progress entries"""
        story = self.get_object()
        progress = StoryProgress.objects.filter(story=story).order_by("created_at")
        serializer = StoryProgressSerializer(progress, many=True)
        return Response(serializer.data)


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

        try:
            active_config = LLMConfig.get_active_config(purpose="scene_generation")
            key = APIKey.get_available_key(model_name=active_config.model.name)
            prompt = ChatPromptTemplate.from_template(active_config.system_prompt)
            json_parser = JsonOutputParser()

            llm = get_llm_model(
                {
                    "model_name": active_config.model.name,
                    "llm_type": active_config.model.llm_type,
                    "url": active_config.model.url,
                    "temperature": active_config.temperature,
                    "key": key,
                },
                fake=settings.FAKE_LLM_REQUEST,
                name="scene_generation",
            )
            chain = prompt | llm | json_parser
            response = chain.invoke(
                {
                    "genre": genre,
                    "details_prompt": details_prompt,
                },
            )
            scenes = response
        except (openai.OpenAIError, ValueError) as e:
            return Response(
                {"error": str(e)},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )

        return Response(scenes)


@method_decorator(csrf_exempt, name="dispatch")
class GameSceneGeneratorStreamView(APIView):
    permission_classes = [IsAuthenticated]
    content_negotiation_class = IgnoreClientContentNegotiation

    def get(self, request):
        genre = request.GET.get("genre")
        details = request.GET.get("details")

        if not genre:
            return Response(
                {"error": "Genre is required"},
                status=status.HTTP_400_BAD_REQUEST,
            )

        # Format the details prompt
        details_prompt = (
            f"\n* Additional details of the story: {details}" if details else ""
        )

        active_config = LLMConfig.get_active_config(purpose="scene_generation")
        key = APIKey.get_available_key(model_name=active_config.model.name)
        prompt = ChatPromptTemplate.from_template(active_config.system_prompt)
        json_parser = JsonOutputParser()

        llm = get_llm_model(
            {
                "model_name": active_config.model.name,
                "llm_type": active_config.model.llm_type,
                "url": active_config.model.url,
                "temperature": active_config.temperature,
                "key": key,
            },
            fake=settings.FAKE_LLM_REQUEST,
            name="scene_generation",
        )
        # Create the chain
        chain = prompt | llm | json_parser

        # Set up the response for SSE
        response = StreamingHttpResponse(
            self.generate_scenes_stream(genre, details_prompt, chain),
            content_type="text/event-stream",
        )
        response["Cache-Control"] = "no-cache"
        response["X-Accel-Buffering"] = "no"
        return response

    async def generate_scenes_stream(self, genre, details_prompt, chain):
        try:
            # Send initial event
            yield f"event: start\ndata: Starting scene generation for {genre}\n\n"

            chunk = {}
            async for chunk in chain.astream(
                {
                    "genre": genre,
                    "details_prompt": details_prompt,
                },
            ):
                yield f"event: scene\ndata: {json.dumps(chunk)}\n\n"

            # Send complete event with all scenes
            yield f"event: complete\ndata: {json.dumps(chunk)}\n\n"

        except Exception as e:
            # Send error event
            error_data = {"error": str(e)}
            yield f"event: error\ndata: {json.dumps(error_data)}\n\n"
            raise
