import json

import openai
from django.conf import settings
from django.db import transaction
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
from .models import VocabularyQuizSubmission
from .models import VocabularyQuizSubmissionItem
from .negotiation import IgnoreClientContentNegotiation
from .serializers import GameScenarioSerializer
from .serializers import GameStorySerializer
from .serializers import LLMModelSerializer
from .serializers import StoryProgressSerializer
from .serializers import TextExplanationSerializer
from .serializers import VocabularyQuizLatestSerializer
from .serializers import VocabularyQuizSubmitSerializer
from .utils import get_llm_model

VALID_VOCABULARY_SCORES = frozenset({0.0, 0.5, 1.0})


@transaction.atomic
def _persist_vocabulary_quiz_submission(
    story,
    user,
    merged,
    average_score,
    by_id,
    id_to_user_text,
):
    submission = VocabularyQuizSubmission.objects.create(
        story=story,
        created_by=user,
        average_score=average_score,
    )
    for row in merged:
        eid = row["explanation_id"]
        exp = by_id[eid]
        VocabularyQuizSubmissionItem.objects.create(
            submission=submission,
            text_explanation=exp,
            selected_text=row["selected_text"],
            context_text=exp.context_text,
            reference_explanation=(exp.explanation or "").strip(),
            user_explanation=id_to_user_text[eid].strip(),
            score=row["score"],
            feedback_reason=row["reason"],
        )
    return submission


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

    @action(detail=True, methods=["get"], url_path="vocabulary-quiz/latest")
    def latest_vocabulary_quiz(self, request, pk=None):
        """Return the current user's latest vocabulary quiz submission for this story."""
        story = self.get_object()
        submission = (
            VocabularyQuizSubmission.objects.filter(
                story=story,
                created_by=request.user,
            )
            .prefetch_related("items")
            .first()
        )
        if submission is None:
            return Response(
                {"error": "No vocabulary quiz submission found"},
                status=status.HTTP_404_NOT_FOUND,
            )
        results = []
        for item in submission.items.all():
            if item.text_explanation_id is None:
                continue
            results.append(
                {
                    "explanation_id": item.text_explanation_id,
                    "selected_text": item.selected_text,
                    "score": item.score,
                    "reason": item.feedback_reason,
                    "user_explanation": item.user_explanation,
                },
            )
        serializer = VocabularyQuizLatestSerializer(
            {
                "average_score": submission.average_score,
                "results": results,
            },
        )
        return Response(serializer.data)

    @action(detail=True, methods=["post"], url_path="vocabulary-quiz/submit")
    def submit_vocabulary_quiz(self, request, pk=None):
        """Evaluate user explanations for looked-up words via LLM."""
        story = self.get_object()
        submit_serializer = VocabularyQuizSubmitSerializer(data=request.data)
        submit_serializer.is_valid(raise_exception=True)
        answers = submit_serializer.validated_data["answers"]
        explanation_ids = [a["explanation_id"] for a in answers]
        id_to_user_text = {a["explanation_id"]: a["user_explanation"] for a in answers}

        explanations = list(
            TextExplanation.objects.filter(
                story=story,
                id__in=explanation_ids,
            ),
        )
        if len(explanations) != len(set(explanation_ids)):
            return Response(
                {"error": "One or more explanations were not found for this story"},
                status=status.HTTP_400_BAD_REQUEST,
            )

        incomplete = [
            e.id
            for e in explanations
            if e.status != "completed" or not (e.explanation or "").strip()
        ]
        if incomplete:
            return Response(
                {
                    "error": (
                        "Some lookups are not ready for review "
                        f"(ids: {sorted(incomplete)})"
                    ),
                },
                status=status.HTTP_400_BAD_REQUEST,
            )

        by_id = {e.id: e for e in explanations}

        if settings.FAKE_LLM_REQUEST:
            merged = [
                {
                    "explanation_id": eid,
                    "selected_text": by_id[eid].selected_text,
                    "score": 1.0,
                    "reason": "Fake LLM mode: response not evaluated.",
                }
                for eid in explanation_ids
            ]
            average = sum(r["score"] for r in merged) / len(merged) if merged else 0.0
            _persist_vocabulary_quiz_submission(
                story,
                request.user,
                merged,
                average,
                by_id,
                id_to_user_text,
            )
            return Response({"results": merged, "average_score": average})

        is_demo = False
        if hasattr(request.user, "userprofile"):
            is_demo = request.user.userprofile.is_demo_account

        try:
            active_config = LLMConfig.get_active_config_with_demo_fallback(
                purpose="vocabulary_quiz",
                is_demo=is_demo,
            )
        except ValueError as e:
            return Response(
                {"error": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

        quiz_items = [
            {
                "explanation_id": e.id,
                "selected_text": e.selected_text,
                "context_text": e.context_text,
                "reference_explanation": e.explanation.strip(),
                "user_explanation": id_to_user_text[e.id].strip(),
            }
            for e in explanations
        ]
        quiz_items_json = json.dumps(quiz_items, ensure_ascii=False)

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
            name="vocabulary_quiz",
        )
        chain = prompt | llm | json_parser

        try:
            parsed = chain.invoke({"quiz_items_json": quiz_items_json})
        except (openai.OpenAIError, ValueError, TypeError) as e:
            return Response(
                {"error": str(e)},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )

        raw_results = parsed.get("results") if isinstance(parsed, dict) else None
        if not isinstance(raw_results, list):
            return Response(
                {"error": "Model returned an unexpected JSON shape"},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )

        def normalize_score(value):
            try:
                s = float(value)
            except (TypeError, ValueError):
                return None
            for allowed in VALID_VOCABULARY_SCORES:
                if abs(s - allowed) < 1e-9:
                    return allowed
            return None

        merged = []
        seen = set()
        for row in raw_results:
            if not isinstance(row, dict):
                continue
            eid = row.get("explanation_id")
            try:
                eid = int(eid)
            except (TypeError, ValueError):
                continue
            if eid not in by_id or eid not in id_to_user_text:
                continue
            sc = normalize_score(row.get("score"))
            reason = row.get("reason")
            if not isinstance(reason, str) or not reason.strip():
                reason = "No reason provided."
            if sc is None:
                sc = 0.0
                reason = f"Unusable score from model; treating as 0. ({reason})"
            exp = by_id[eid]
            merged.append(
                {
                    "explanation_id": eid,
                    "selected_text": exp.selected_text,
                    "score": sc,
                    "reason": reason.strip(),
                },
            )
            seen.add(eid)

        missing = set(explanation_ids) - seen
        for eid in sorted(missing):
            exp = by_id[eid]
            merged.append(
                {
                    "explanation_id": eid,
                    "selected_text": exp.selected_text,
                    "score": 0.0,
                    "reason": "Model did not return an evaluation for this item.",
                },
            )

        merged.sort(key=lambda r: explanation_ids.index(r["explanation_id"]))
        average = sum(r["score"] for r in merged) / len(merged) if merged else 0.0
        _persist_vocabulary_quiz_submission(
            story,
            request.user,
            merged,
            average,
            by_id,
            id_to_user_text,
        )
        return Response({"results": merged, "average_score": average})


class GameSceneGeneratorView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        genre = request.data.get("genre")
        details = request.data.get("details")
        theme = request.data.get("theme", "")
        if not genre:
            return Response(
                {"error": "Genre is required"},
                status=status.HTTP_400_BAD_REQUEST,
            )

        # Check if user is demo account
        is_demo = False
        if hasattr(request.user, "userprofile"):
            is_demo = request.user.userprofile.is_demo_account

        active_config = LLMConfig.get_active_config_with_demo_fallback(
            purpose="scene_generation",
            is_demo=is_demo,
        )

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
                    "theme": theme or "",
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
        theme = request.GET.get("theme", "")

        if not genre:
            return Response(
                {"error": "Genre is required"},
                status=status.HTTP_400_BAD_REQUEST,
            )

        # Format the details prompt
        details_prompt = (
            f"\n* Additional details of the story: {details}" if details else ""
        )

        # Check if user is demo account
        is_demo = False
        if hasattr(request.user, "userprofile"):
            is_demo = request.user.userprofile.is_demo_account

        active_config = LLMConfig.get_active_config_with_demo_fallback(
            purpose="scene_generation",
            is_demo=is_demo,
        )
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
            self.generate_scenes_stream(genre, theme or "", details_prompt, chain),
            content_type="text/event-stream",
        )
        response["Cache-Control"] = "no-cache"
        response["X-Accel-Buffering"] = "no"
        return response

    async def generate_scenes_stream(self, genre, theme, details_prompt, chain):
        try:
            # Send initial event
            yield f"event: start\ndata: Starting scene generation for {genre}\n\n"

            chunk = {}
            async for chunk in chain.astream(
                {
                    "genre": genre,
                    "theme": theme or "",
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
