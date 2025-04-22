from django.contrib import admin
from django.template.defaultfilters import truncatechars

from .models import APIKey
from .models import GameScenario
from .models import GameStory
from .models import LLMConfig
from .models import LLMModel
from .models import QuotaConfig
from .models import StoryProgress
from .models import StorySkeleton
from .models import TextExplanation


@admin.register(QuotaConfig)
class QuotaConfigAdmin(admin.ModelAdmin):
    list_display = ["id", "model", "daily_limit", "created_at", "updated_at"]
    list_filter = ["model"]


@admin.register(LLMModel)
class LLMModelAdmin(admin.ModelAdmin):
    list_display = [
        "id",
        "display_name",
        "name",
        "llm_type",
        "url",
        "order",
        "is_default",
        "is_active",
        "created_at",
        "updated_at",
    ]
    list_filter = ["is_active", "is_default"]
    search_fields = ["name", "display_name"]
    ordering = ["order"]
    fieldsets = (
        (
            None,
            {
                "fields": (
                    "name",
                    "display_name",
                    "llm_type",
                    "url",
                ),
            },
        ),
        (
            "Settings",
            {
                "fields": (
                    "order",
                    "is_default",
                    "is_active",
                ),
            },
        ),
    )


@admin.register(LLMConfig)
class LLMConfigAdmin(admin.ModelAdmin):
    list_display = [
        "id",
        "purpose",
        "model",
        "get_system_prompt",
        "temperature",
        "is_active",
        "updated_at",
    ]
    list_filter = ["model"]
    actions = ["change_llm_model"]

    @admin.display(description="System Prompt", ordering="system_prompt")
    def get_system_prompt(self, obj):
        return truncatechars(obj.system_prompt, 50)

    @admin.action(description="Change LLM model for selected configs")
    def change_llm_model(self, request, queryset):
        from django import forms
        from django.contrib import messages
        from django.http import HttpResponseRedirect
        from django.template.response import TemplateResponse

        class ModelChangeForm(forms.Form):
            _selected_action = forms.CharField(widget=forms.MultipleHiddenInput)
            model = forms.ModelChoiceField(
                queryset=LLMModel.objects.filter(is_active=True),
            )

        # Step 1: Initialize form with selected items
        form = ModelChangeForm(
            request.POST or None,
            initial={"_selected_action": request.POST.getlist("_selected")},
        )

        # Step 2: If this is a POST request with the apply button
        if request.POST and "apply" in request.POST:
            if form.is_valid():
                try:
                    model = form.cleaned_data["model"]
                    count = 0
                    for config in queryset:
                        config.model = model
                        config.save()
                        count += 1
                    msg = (
                        f"Successfully updated {count} configs "
                        f"to use: {model.display_name}"
                    )
                    messages.success(request, msg)
                    return HttpResponseRedirect(request.get_full_path())
                except (ValueError, KeyError) as e:
                    messages.error(request, f"Error updating models: {e!s}")
            else:
                messages.error(request, f"Form validation failed: {form.errors}")

        # Step 3: Show the form
        context = {
            "title": "Change LLM Model",
            "objects": queryset,
            "form": form,
        }
        return TemplateResponse(request, "admin/llm_config_change_model.html", context)


@admin.register(APIKey)
class APIKeyAdmin(admin.ModelAdmin):
    list_display = [
        "id",
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
        "id",
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
        "id",
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
        "id",
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
        "id",
        "story",
        "get_created_by",
        "background",
        "created_at",
        "updated_at",
    ]

    @admin.display(description="Created By")
    def get_created_by(self, obj):
        return obj.story.created_by


@admin.register(StoryProgress)
class StoryProgressAdmin(admin.ModelAdmin):
    list_display = [
        "id",
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
