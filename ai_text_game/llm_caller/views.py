from dataclasses import asdict

from django.conf import settings
from django.db import transaction
from rest_framework import status
from rest_framework import viewsets
from rest_framework.pagination import PageNumberPagination
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from .models import APIRequest
from .models import LLMConfig
from .models import LLMModel
from .serializers import APIRequestSerializer
from .serializers import LLMModelSerializer
from .tasks import LLMRequestParams
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
