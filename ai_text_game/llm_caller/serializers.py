from django.conf import settings
from rest_framework import serializers

from .models import APIRequest
from .models import GameInteraction
from .models import GameScenario
from .models import GameStory
from .models import LLMModel


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
            "title",
            "genre",
            "created_at",
        ]


class GameInteractionSerializer(serializers.ModelSerializer):
    class Meta:
        model = GameInteraction
        fields = [
            "id",
            "system_input",
            "system_output",
            "created_at",
        ]

    def to_representation(self, instance):
        # Only return non-system messages to frontend
        # if instance.role == "system":
        #     return None # noqa: ERA001
        return super().to_representation(instance)


class GameStorySerializer(serializers.ModelSerializer):
    interactions = serializers.SerializerMethodField()
    model_name = serializers.CharField(write_only=True)

    class Meta:
        model = GameStory
        fields = [
            "id",
            "title",
            "genre",
            "model_name",
            "status",
            "created_at",
            "updated_at",
            "interactions",
        ]
        read_only_fields = ["title", "status", "created_at", "updated_at"]

    def get_interactions(self, obj):
        # Filter out system messages
        interactions = obj.interactions.exclude(role="system")
        return GameInteractionSerializer(interactions, many=True).data

    def create(self, validated_data):
        model_name = validated_data.pop("model_name")

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

        # Create initial system message
        GameInteraction.objects.create(
            story=story,
            role="system",
            system_input=settings.DEFAULT_SYSTEM_PROMPT,
            system_output="",
            status="pending",
        )

        return story
