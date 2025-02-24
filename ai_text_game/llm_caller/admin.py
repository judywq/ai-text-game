from django.contrib import admin
from django.template.defaultfilters import truncatechars

from .models import GameScenario
from .models import GameStory
from .models import LLMConfig
from .models import LLMModel
from .models import OpenAIKey
from .models import QuotaConfig
from .models import StoryProgress
from .models import StorySkeleton
from .models import TextExplanation


@admin.register(QuotaConfig)
class QuotaConfigAdmin(admin.ModelAdmin):
    list_display = ["model", "daily_limit", "created_at", "updated_at"]
    list_filter = ["model"]


@admin.register(LLMModel)
class LLMModelAdmin(admin.ModelAdmin):
    list_display = [
        "name",
        "display_name",
        "order",
        "is_default",
        "is_active",
        "created_at",
        "updated_at",
    ]
    list_filter = ["is_active", "is_default"]
    search_fields = ["name", "display_name"]
    ordering = ["order"]


@admin.register(LLMConfig)
class LLMConfigAdmin(admin.ModelAdmin):
    list_display = [
        "purpose",
        "model",
        "get_system_prompt",
        "temperature",
        "is_active",
        "updated_at",
    ]
    list_filter = ["model"]

    @admin.display(description="System Prompt", ordering="system_prompt")
    def get_system_prompt(self, obj):
        return truncatechars(obj.system_prompt, 50)


@admin.register(OpenAIKey)
class OpenAIKeyAdmin(admin.ModelAdmin):
    list_display = [
        "name",
        "masked_key",
        "order",
        "is_active",
        "created_at",
        "updated_at",
    ]
    list_filter = ["is_active"]
    search_fields = ["name"]
    ordering = ["order"]

    @admin.display(
        description="API Key",
    )
    def masked_key(self, obj):
        """Show only the last 4 characters of the key."""
        return f"...{obj.key[-4:]}" if obj.key else ""


@admin.register(GameScenario)
class GameScenarioAdmin(admin.ModelAdmin):
    list_display = [
        "category",
        "name",
        "example",
        "order",
        "is_active",
        "created_at",
        "updated_at",
    ]
    list_filter = ["is_active"]
    search_fields = ["name", "example"]
    ordering = ["order"]


@admin.register(GameStory)
class GameStoryAdmin(admin.ModelAdmin):
    list_display = [
        "title",
        "created_by",
        "genre",
        "cefr_level",
        "get_scene_text",
        "get_details",
        "status",
        "created_at",
        "updated_at",
    ]
    list_filter = ["status", "genre", "created_by"]
    search_fields = ["title", "created_by__username"]

    @admin.display(description="Scene Text", ordering="scene_text")
    def get_scene_text(self, obj):
        return truncatechars(obj.scene_text, 50)

    @admin.display(description="Details", ordering="details")
    def get_details(self, obj):
        return truncatechars(obj.details, 50)


@admin.register(TextExplanation)
class TextExplanationAdmin(admin.ModelAdmin):
    list_display = [
        "created_by",
        "story",
        "model",
        "selected_text",
        "context_text",
        "explanation",
        "created_at",
    ]
    list_filter = ["created_by", "story", "model"]
    search_fields = ["selected_text", "explanation"]


@admin.register(StorySkeleton)
class StorySkeletonAdmin(admin.ModelAdmin):
    list_display = [
        "story",
        "background",
        "created_at",
        "updated_at",
    ]


@admin.register(StoryProgress)
class StoryProgressAdmin(admin.ModelAdmin):
    list_display = [
        "story",
        "get_content",
        "decision_point_id",
        "chosen_option_id",
        "created_at",
    ]
    list_filter = ["story", "created_at"]
    search_fields = ["content"]

    @admin.display(description="Content", ordering="content")
    def get_content(self, obj):
        return truncatechars(obj.content, 50)
