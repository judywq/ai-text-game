from rest_framework import serializers

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
    interactions = serializers.SerializerMethodField()
    scene_text = serializers.CharField(write_only=True, required=False)
    cefr_level = serializers.CharField(write_only=True, required=False)

    def get_interactions(self, obj):
        interactions = obj.interactions.order_by("created_at")
        return GameInteractionSerializer(interactions, many=True).data

    class Meta:
        model = GameStory
        fields = [
            "id",
            "title",
            "genre",
            "scene_text",
            "cefr_level",
            "status",
            "created_at",
            "updated_at",
            "interactions",
        ]
        read_only_fields = ["title", "status", "created_at", "updated_at"]

    def create(self, validated_data):
        scene_text = validated_data.pop("scene_text", None)
        cefr_level = validated_data.pop("cefr_level", None)
        details = validated_data.pop("details", None)

        # Create initial system message with scene info if provided
        active_config = LLMConfig.get_active_config(purpose="adventure_gameplay")

        # Create the story
        story = GameStory.objects.create(
            model=active_config.model,
            title=f"A {validated_data['genre']} Story",  # Use genre in title
            **validated_data,
        )

        details_prompt = (
            f"\n* Additional details of the story: {details}" if details else ""
        )

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
