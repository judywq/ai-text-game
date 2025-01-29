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
            "description",
            "created_at",
        ]


class GameInteractionSerializer(serializers.ModelSerializer):
    class Meta:
        model = GameInteraction
        fields = [
            "id",
            "user_input",
            "system_response",
            "created_at",
        ]


class GameStorySerializer(serializers.ModelSerializer):
    scenario = GameScenarioSerializer(read_only=True)
    scenario_id = serializers.IntegerField(write_only=True)
    model_name = serializers.CharField(write_only=True)
    interactions = GameInteractionSerializer(many=True, read_only=True)

    class Meta:
        model = GameStory
        fields = [
            "id",
            "title",
            "scenario",
            "scenario_id",
            "model_name",
            "status",
            "created_at",
            "updated_at",
            "interactions",
        ]
        read_only_fields = ["title", "status", "created_at", "updated_at"]

    def create(self, validated_data):
        scenario_id = validated_data.pop("scenario_id")
        model_name = validated_data.pop("model_name")

        try:
            scenario = GameScenario.objects.get(id=scenario_id, is_active=True)
            model = LLMModel.objects.get(name=model_name, is_active=True)
        except (GameScenario.DoesNotExist, LLMModel.DoesNotExist) as e:
            raise serializers.ValidationError(str(e)) from e

        # Copy the title from scenario
        return GameStory.objects.create(
            scenario=scenario,
            model=model,
            title=scenario.title,  # Use scenario title as story title
            **validated_data,
        )
