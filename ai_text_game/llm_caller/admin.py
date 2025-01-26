from io import BytesIO

from django.contrib import admin
from django.http import HttpResponse
from django.utils import timezone
from openpyxl import Workbook

from .models import APIRequest
from .models import LLMConfig
from .models import LLMModel
from .models import OpenAIKey
from .models import QuotaConfig


@admin.register(QuotaConfig)
class QuotaConfigAdmin(admin.ModelAdmin):
    list_display = ["model", "daily_limit", "created_at", "updated_at"]
    list_filter = ["model"]


@admin.register(APIRequest)
class APIRequestAdmin(admin.ModelAdmin):
    list_display = [
        "user",
        "status",
        "get_model_name",
        "essay",
        "score",
        "created_at",
    ]
    list_filter = ["status", "user", "model"]
    search_fields = ["essay", "result"]

    @admin.display(
        description="Model",
        ordering="model__display_name",
    )
    def get_model_name(self, obj):
        return obj.model.display_name

    @admin.action(
        description="Export selected requests as Excel",
    )
    def export_as_csv(self, request, queryset):
        field_names = [
            "created_at",
            "user__email",
            "model__name",
            "essay",
            "score",
            "result",
        ]

        # Create workbook and select active sheet
        workbook = Workbook()
        worksheet = workbook.active

        # Write header
        headers = [
            "Timestamp",
            "User Email",
            "LLM Model",
            "Essay",
            "Score",
            "Raw Response",
        ]
        worksheet.append(headers)

        # Write data rows
        for obj in queryset:
            row = []
            for field in field_names:
                value = obj
                for attr in field.split("__"):
                    value = getattr(value, attr, None)
                    if value is None:
                        break

                # Format timestamp if it's the created_at field
                if field == "created_at" and value is not None:
                    value = timezone.localtime(value).strftime("%Y-%m-%d %H:%M:%S %Z")

                row.append(value if value is not None else "")
            worksheet.append(row)

        # Save to buffer
        excel_file = BytesIO()
        workbook.save(excel_file)
        excel_file.seek(0)

        # Create the HttpResponse
        now = timezone.localtime().strftime("%Y%m%d_%H%M%S")
        filename = f"Requests_{now}.xlsx"

        response = HttpResponse(
            excel_file.read(),
            content_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        )
        response["Content-Disposition"] = f'attachment; filename="{filename}"'

        return response


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
        "system_prompt",
        "user_prompt_template",
        "temperature",
        "updated_at",
    ]
    list_filter = ["created_at"]


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
