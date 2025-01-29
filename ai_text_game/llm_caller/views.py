from dataclasses import asdict

from django.conf import settings
from django.db import transaction
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
from .serializers import APIRequestSerializer
from .serializers import GameInteractionSerializer
from .serializers import GameScenarioSerializer
from .serializers import GameStorySerializer
from .serializers import LLMModelSerializer
from .tasks import GameInteractionParams
from .tasks import LLMRequestParams
from .tasks import process_game_interaction
from .tasks import process_openai_request


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


class GameStoryViewSet(viewsets.ModelViewSet):
    serializer_class = GameStorySerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        return GameStory.objects.filter(user=self.request.user)

    def perform_create(self, serializer):
        serializer.save(user=self.request.user)

    @action(detail=True, methods=["post"])
    @transaction.atomic
    def interact(self, request, pk=None):
        story = self.get_object()
        user_input = request.data.get("user_input")

        if not user_input:
            return Response(
                {"error": "user_input is required"},
                status=status.HTTP_400_BAD_REQUEST,
            )

        # Create the interaction first
        interaction = GameInteraction.objects.create(
            story=story,
            user_input=user_input,
            status="pending",
        )

        # Construct the context for the LLM
        context = [
            {"role": "system", "content": story.scenario.system_prompt},
        ]

        # Add previous interactions for context
        for prev_interaction in story.interactions.filter(status="completed"):
            context.extend(
                [
                    {"role": "user", "content": prev_interaction.user_input},
                    {"role": "assistant", "content": prev_interaction.system_response},
                ],
            )

        # Add the new user input
        context.append({"role": "user", "content": user_input})

        # Prepare parameters for the task
        interaction_params = GameInteractionParams(
            interaction_id=interaction.id,
            model_name=story.model.name,
            system_prompt=story.scenario.system_prompt,
            context=context,
        )

        # Schedule the task to run after transaction commit
        transaction.on_commit(
            lambda: process_game_interaction.delay(
                asdict(interaction_params),
                delay_seconds=getattr(settings, "TASK_DELAY", 0),
            ),
        )

        return Response(GameInteractionSerializer(interaction).data)
