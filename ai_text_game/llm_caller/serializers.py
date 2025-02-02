from rest_framework import serializers

from .models import APIRequest
from .models import GameInteraction
from .models import GameScenario
from .models import GameStory
from .models import LLMConfig
from .models import LLMModel
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


class APIRequestSerializer(serializers.ModelSerializer):
    model_name = serializers.CharField(write_only=True)
    model_display_name = serializers.CharField(
        source="model.display_name",
        read_only=True,
    )

    class Meta:
        model = APIRequest
        fields = [
            "id",
            "essay",
            "score",
            "error",
            "status",
            "created_at",
            "model_name",
            "model_display_name",
        ]
        read_only_fields = ["score", "status", "created_at", "model_display_name"]

    def create(self, validated_data):
        model_name = validated_data.pop("model_name")
        try:
            model = LLMModel.objects.get(name=model_name, is_active=True)
        except LLMModel.DoesNotExist as e:
            raise serializers.ValidationError(
                {"model_name": "Selected model is not supported"},
            ) from e

        return APIRequest.objects.create(
            **validated_data,
            model=model,
        )


class GameScenarioSerializer(serializers.ModelSerializer):
    class Meta:
        model = GameScenario
        fields = [
            "id",
            "category",
            "name",
            "example",
            "order",
        ]


class GameInteractionSerializer(serializers.ModelSerializer):
    class Meta:
        model = GameInteraction
        fields = [
            "id",
            "role",
            "system_input",
            "system_output",
            "status",
            "created_at",
        ]

    def to_representation(self, instance):
        data = super().to_representation(instance)
        # For system messages, only return the system output as assistant message
        if instance.role == "system":
            data["system_input"] = None
        return data


class GameStorySerializer(serializers.ModelSerializer):
    interactions = GameInteractionSerializer(many=True, read_only=True)
    model_name = serializers.CharField(write_only=True)
    scene_text = serializers.CharField(write_only=True, required=False)
    cefr_level = serializers.CharField(write_only=True, required=False)

    class Meta:
        model = GameStory
        fields = [
            "id",
            "title",
            "genre",
            "model_name",
            "scene_text",
            "cefr_level",
            "status",
            "created_at",
            "updated_at",
            "interactions",
        ]
        read_only_fields = ["title", "status", "created_at", "updated_at"]

    def create(self, validated_data):
        model_name = validated_data.pop("model_name")
        scene_text = validated_data.pop("scene_text", None)
        cefr_level = validated_data.pop("cefr_level", None)
        details = validated_data.pop("details", None)
        try:
            model = LLMModel.objects.get(name=model_name, is_active=True)
        except LLMModel.DoesNotExist as e:
            raise serializers.ValidationError(str(e)) from e

        # Create the story
        story = GameStory.objects.create(
            model=model,
            title=f"A {validated_data['genre']} Story",  # Use genre in title
            **validated_data,
        )

        details_prompt = (
            f"\n* Additional details of the story: {details}" if details else ""
        )

        # Create initial system message with scene info if provided
        active_config = LLMConfig.get_active_config()
        system_prompt = active_config.system_prompt.format(
            genre=story.genre,
            scene_text=scene_text,
            cefr_level=cefr_level,
            details_prompt=details_prompt,
        )

        GameInteraction.objects.create(
            story=story,
            role="system",
            system_input=system_prompt,
            status="pending",
        )

        return story


class TextExplanationSerializer(serializers.ModelSerializer):
    class Meta:
        model = TextExplanation
        fields = "__all__"
