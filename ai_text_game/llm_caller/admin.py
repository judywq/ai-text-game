from django.contrib import admin
from django.template.defaultfilters import truncatechars
from django.utils.html import format_html

from .models import APIKey
from .models import GameScenario
from .models import GameStory
from .models import LLMConfig
from .models import LLMModel
from .models import QuotaConfig
from .models import StoryOption
from .models import StoryProgress
from .models import StorySkeleton
from .models import TextExplanation
from .utils import format_datetime
from .utils import generate_excel_response


@admin.register(QuotaConfig)
class QuotaConfigAdmin(admin.ModelAdmin):
    list_display = ["id", "model", "daily_limit", "created_at", "updated_at"]
    list_display_links = ["model"]
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
    list_display_links = ["display_name"]
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
    list_display_links = ["purpose"]
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
    list_display_links = ["name"]
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
    list_display_links = ["name"]
    list_filter = ["is_active"]
    search_fields = ["name", "example"]
    ordering = ["order"]


@admin.register(GameStory)
class GameStoryAdmin(admin.ModelAdmin):
    list_display = [
        "id",
        "title",
        "game_link",
        "created_by",
        "genre",
        "language_level",
        "get_scene_text",
        "get_details",
        "status",
        "created_at",
        "updated_at",
    ]
    list_display_links = ["title"]
    list_filter = ["status", "genre", "created_by"]
    search_fields = ["title", "created_by__username"]

    @admin.display(description="Game Link")
    def game_link(self, obj):
        url = f"/game/{obj.id}/"
        return format_html('<a href="{}" target="_blank">View Game</a>', url)

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
        "selected_text",
        "context_text",
        "explanation",
        "created_by",
        "story",
        "model",
        "created_at",
    ]
    list_display_links = ["selected_text"]
    list_filter = ["created_by", "story", "model"]
    search_fields = ["selected_text", "explanation"]

    actions = ["export_as_excel"]

    # Define field mapping for export
    export_field_mapping = [
        ("id", "Explanation ID"),
        ("created_by__username", "Username"),
        ("created_by__email", "Email"),
        ("created_by__name", "Name"),
        ("selected_text", "Selected Text"),
        ("context_text", "Context Text"),
        ("explanation", "Explanation"),
        ("created_at", "Created At"),
        ("error", "Error"),
        ("model__name", "LLM Model for Explanation"),
        ("story__id", "Story ID"),
        ("story__status", "Story Status"),
        ("story__title", "Story Title"),
        ("story__genre", "Story Genre"),
        ("story__language_level", "Story Language Level"),
        ("story__scene_text", "Story Scene Text"),
        ("story__details", "Story Details"),
    ]

    @admin.action(description="Export selected requests as Excel")
    def export_as_excel(self, request, queryset):
        rows = []
        # Write data rows
        for obj in queryset:
            row = {}
            for field, header in self.export_field_mapping:
                value = obj
                for attr in field.split("__"):
                    value = getattr(value, attr, None)
                    if value is None:
                        break

                # Format the value if it's a datetime field
                if (
                    field in ["created_at", "started_at", "ended_at"]
                    and value is not None
                ):
                    value = format_datetime(value)

                row.update({header: value})
            rows.append(row)
        return generate_excel_response(rows, "TextExplanations")


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
    list_display_links = ["story"]

    @admin.display(description="Created By")
    def get_created_by(self, obj):
        return obj.story.created_by


class StoryOptionInline(admin.TabularInline):
    model = StoryOption
    extra = 0
    can_delete = False
    fields = ["option_id", "option_name", "created_at"]
    readonly_fields = ["option_id", "option_name", "created_at"]
    ordering = ["option_id"]
    verbose_name = "Story Option"
    verbose_name_plural = "Story Options"

    def has_add_permission(self, request, obj=None):
        return False

    def has_change_permission(self, request, obj=None):
        return False


@admin.register(StoryProgress)
class StoryProgressAdmin(admin.ModelAdmin):
    list_display = [
        "id",
        "story",
        "get_content",
        "get_image_preview",
        "decision_point_id",
        "chosen_option_id",
        "created_at",
    ]
    list_display_links = ["story"]
    list_filter = ["story", "created_at"]
    search_fields = ["content"]
    inlines = [StoryOptionInline]
    readonly_fields = ["image_display"]

    fieldsets = (
        (
            None,
            {
                "fields": (
                    "story",
                    "content",
                    "summary",
                    "image_display",
                    "image_url",
                    "decision_point_id",
                    "chosen_option_id",
                    "chosen_option_text",
                    "is_end_point",
                ),
            },
        ),
    )

    @admin.display(description="Content", ordering="content")
    def get_content(self, obj):
        return truncatechars(obj.content, 50)

    @admin.display(description="Image")
    def get_image_preview(self, obj):
        if obj.image_url:
            return format_html(
                (
                    '<img src="{}" style="max-width: 100px;'
                    'max-height: 100px; object-fit: contain;" />'
                ),
                obj.image_url,
            )
        return "-"

    @admin.display(description="Image")
    def image_display(self, obj):
        if obj.image_url:
            return format_html(
                (
                    '<img src="{}" style="max-width: 500px;'
                    ' max-height: 500px; object-fit: contain;" />'
                ),
                obj.image_url,
            )
        return "No image available"
