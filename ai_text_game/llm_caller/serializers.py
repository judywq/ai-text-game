from rest_framework import serializers

from .models import APIRequest
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
