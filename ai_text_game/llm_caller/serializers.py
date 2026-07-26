from rest_framework import serializers

from .models import GameScenario
from .models import GameStory
from .models import LLMModel
from .models import StoryOption
from .models import StoryProgress
from .models import TextExplanation


class LLMModelSerializer(serializers.ModelSerializer):
    used_quota = serializers.SerializerMethodField()
    daily_limit = serializers.IntegerField(source="quota_config.daily_limit")

    class Meta:
        model = LLMModel
        fields = [
            "order",
            "is_default",
            "name",
            "display_name",
            "used_quota",
            "daily_limit",
        ]

    def get_used_quota(self, obj):
        try:
            user = self.context["request"].user
        except (KeyError, AttributeError):
            return 0

        return obj.get_used_quota(user)


class GameScenarioSerializer(serializers.ModelSerializer):
    class Meta:
        model = GameScenario
        fields = [
            "id",
            "category",
            "parent",
            "name",
            "description",
            "example",
            "order",
        ]


class GameStorySerializer(serializers.ModelSerializer):
    progress = serializers.SerializerMethodField()
    scene_text = serializers.CharField(write_only=True, required=False)

    def get_progress(self, obj):
        return StoryProgressSerializer(obj.progress_entries, many=True).data

    class Meta:
        model = GameStory
        fields = [
            "id",
            "title",
            "genre",
            "scene_text",
            "details",
            "theme",
            "language_level",
            "status",
            "created_at",
            "updated_at",
            "progress",
        ]
        read_only_fields = ["title", "status", "created_at", "updated_at"]

    def create(self, validated_data):
        # Create the story
        return GameStory.objects.create(
            title=f"A {validated_data['genre']} Story",  # Use genre in title
            **validated_data,
        )


class TextExplanationSerializer(serializers.ModelSerializer):
    class Meta:
        model = TextExplanation
        fields = "__all__"


class VocabularyQuizAnswerSerializer(serializers.Serializer):
    explanation_id = serializers.IntegerField(min_value=1)
    user_explanation = serializers.CharField(allow_blank=False, trim_whitespace=True)


class VocabularyQuizSubmitSerializer(serializers.Serializer):
    answers = serializers.ListField(
        child=VocabularyQuizAnswerSerializer(),
        min_length=1,
    )

    def validate_answers(self, answers):
        ids = [a["explanation_id"] for a in answers]
        if len(ids) != len(set(ids)):
            msg = "Duplicate explanation_id in answers"
            raise serializers.ValidationError(msg)
        return answers


class VocabularyQuizLatestResultSerializer(serializers.Serializer):
    explanation_id = serializers.IntegerField()
    selected_text = serializers.CharField()
    score = serializers.FloatField()
    reason = serializers.CharField()
    user_explanation = serializers.CharField()


class VocabularyQuizLatestSerializer(serializers.Serializer):
    average_score = serializers.FloatField()
    results = VocabularyQuizLatestResultSerializer(many=True)


class StoryOptionSerializer(serializers.ModelSerializer):
    class Meta:
        model = StoryOption
        fields = ["option_id", "option_name"]


class StoryProgressSerializer(serializers.ModelSerializer):
    options = StoryOptionSerializer(many=True, read_only=True)

    class Meta:
        model = StoryProgress
        fields = [
            "id",
            "content",
            "image_url",
            "decision_point_id",
            "chosen_option_id",
            "chosen_option_text",
            "is_end_point",
            "created_at",
            "options",
        ]
