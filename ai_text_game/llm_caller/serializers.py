from rest_framework import serializers

from .models import GameInteraction
from .models import GameScenario
from .models import GameStory
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
            "content",
            "status",
            "created_at",
        ]

    def to_representation(self, instance):
        data = super().to_representation(instance)
        # For system messages, return empty content
        if instance.role == "system":
            data["content"] = ""
        return data


class GameStorySerializer(serializers.ModelSerializer):
    interactions = serializers.SerializerMethodField()
    scene_text = serializers.CharField(write_only=True, required=False)
    cefr_level = serializers.CharField(write_only=True, required=False)

    def get_interactions(self, obj):
        interactions = obj.interactions.filter(role__in=["assistant", "user"]).order_by(
            "created_at",
        )
        return GameInteractionSerializer(interactions, many=True).data

    class Meta:
        model = GameStory
        fields = [
            "id",
            "title",
            "genre",
            "scene_text",
            "details",
            "cefr_level",
            "status",
            "created_at",
            "updated_at",
            "interactions",
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
