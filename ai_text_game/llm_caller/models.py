import re
from typing import Literal

from django.conf import settings
from django.contrib.auth import get_user_model
from django.core.exceptions import ValidationError
from django.core.validators import MaxValueValidator
from django.core.validators import MinValueValidator
from django.db import models

from .utils import get_today_date_range
from .utils import read_prompt_template

User = get_user_model()


class LLMModel(models.Model):
    order = models.IntegerField(
        default=10,
        help_text="Order of the model in the UI (smaller number comes first)",
    )
    name = models.CharField(
        max_length=200,
        help_text=(
            "The model name for calling the LLM API (e.g., gpt-4o-2024-11-20)."
            " Check <a href='https://platform.openai.com/docs/models#current-model-aliases'"
            " target='_blank'>OpenAI model list</a>."
        ),
    )
    display_name = models.CharField(
        max_length=200,
        help_text="Display name for the model (e.g., GPT-4o)",
    )
    is_default = models.BooleanField(
        default=False,
        help_text="This model will be pre-selected in the UI",
    )
    is_active = models.BooleanField(
        default=True,
        help_text="Only active models will be listed in the UI",
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["order"]
        get_latest_by = "created_at"

    def __str__(self):
        return f"{self.display_name} ({'Active' if self.is_active else 'Inactive'})"

    def save(self, *args, **kwargs):
        # If this model is being set as default, reset all others
        if self.is_default:
            LLMModel.objects.exclude(id=self.id).update(is_default=False)
        super().save(*args, **kwargs)

    @classmethod
    def get_active_models(cls):
        return cls.objects.filter(is_active=True)

    def get_used_quota(self, user) -> int:
        """Get the number of completed requests for today for this model and user."""
        today_start, today_end = get_today_date_range()

        return APIRequest.objects.filter(
            user=user,
            model=self,
            status="COMPLETED",
            created_at__range=(today_start, today_end),
        ).count()

    def check_quota(self, user) -> bool:
        """
        Check if the user has exceeded their quota for this model.
        Returns True if the user has exceeded their quota, False otherwise.
        """
        try:
            quota_config = self.quota_config
        except QuotaConfig.DoesNotExist:
            # No quota config means unlimited requests
            return True

        used_quota = self.get_used_quota(user)
        return used_quota < quota_config.daily_limit


class QuotaConfig(models.Model):
    model = models.OneToOneField(
        LLMModel,
        on_delete=models.CASCADE,
        related_name="quota_config",
        help_text="The LLM model this quota applies to",
    )
    daily_limit = models.IntegerField(
        default=10,
        help_text="Maximum number of requests per day for this model",
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        get_latest_by = "created_at"

    def __str__(self):
        return f"QuotaConfig({self.model.display_name}, limit={self.daily_limit})"


class APIRequest(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    essay = models.TextField()
    model = models.ForeignKey(
        LLMModel,
        on_delete=models.PROTECT,
        related_name="requests",
        help_text="The LLM model used for this request",
    )
    result = models.TextField(blank=True, default="")
    score = models.FloatField(null=True, blank=True)
    error = models.TextField(blank=True, default="")
    status = models.CharField(
        max_length=20,
        choices=[
            ("PENDING", "Pending"),
            ("COMPLETED", "Completed"),
            ("FAILED", "Failed"),
        ],
        default="PENDING",
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    task_id = models.CharField(max_length=100, blank=True, default="")

    def __str__(self):
        return f"APIRequest(user={self.user}, status={self.status}, \
            model={self.model.display_name}, essay={self.essay[:20]})"


def validate_user_prompt_template(value):
    # Count occurrences of {essay}
    essay_count = value.count("{essay}")
    if essay_count < 1:
        msg = "Did you forget to include a '{essay}' placeholder?"
        raise ValidationError(
            msg,
        )

    # Check for any other placeholders using regex
    # This will find anything like {word} or {word_word} except {essay}
    other_placeholders = re.findall(r"(?<!{){(?!essay})[^{}]+}(?!})", value)
    if other_placeholders:
        msg = (
            f"Template contains invalid placeholders: {', '.join(other_placeholders)}. "
            "Only '{essay}' is allowed."
        )
        raise ValidationError(
            msg,
        )


class LLMConfig(models.Model):
    PURPOSE_CHOICES = [
        ("scene_generation", "Scene Generation"),
        ("adventure_gameplay", "Adventure Gameplay"),
        ("text_explanation", "Text Explanation"),
    ]

    purpose = models.CharField(
        max_length=20,
        choices=PURPOSE_CHOICES,
        help_text="The purpose of this configuration",
    )
    system_prompt = models.TextField(
        help_text="The system prompt for the LLM.",
    )
    temperature = models.FloatField(
        default=0.7,
        validators=[
            MinValueValidator(0.0),
            MaxValueValidator(2.0),
        ],
        help_text="Value between 0 and 2",
    )
    is_active = models.BooleanField(
        default=False,
        help_text="Only one config can be active per purpose",
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        get_latest_by = "created_at"

    def __str__(self):
        return f"LLM Config ({self.get_purpose_display()}, Updated: {self.updated_at})"

    def save(self, *args, **kwargs):
        if self.is_active:
            # Deactivate other configs with the same purpose
            LLMConfig.objects.filter(purpose=self.purpose).exclude(id=self.id).update(
                is_active=False,
            )
        super().save(*args, **kwargs)

    def clean(self):
        super().clean()

        # Validate system prompt based on purpose
        if self.purpose == "scene_generation":
            if "{genre}" not in self.system_prompt:
                msg = "Scene generation prompt must include {genre} placeholder"
                raise ValidationError(msg)
        elif self.purpose == "adventure_gameplay":
            if (
                "{genre}" not in self.system_prompt
                or "{cefr_level}" not in self.system_prompt
            ):
                msg = (
                    "Adventure gameplay prompt must include {genre}"
                    " and {cefr_level} placeholders"
                )
                raise ValidationError(msg)
        elif self.purpose == "text_explanation":
            if (
                "{selected_text}" not in self.system_prompt
                or "{context_text}" not in self.system_prompt
            ):
                msg = (
                    "Text explanation prompt must include {selected_text}"
                    " and {context_text} placeholders"
                )
                raise ValidationError(msg)

    @classmethod
    def get_active_config(
        cls,
        purpose: Literal["scene_generation", "adventure_gameplay", "text_explanation"],
    ):
        """Get the active config for the given purpose."""
        try:
            return cls.objects.get(purpose=purpose, is_active=True)
        except cls.DoesNotExist:
            # Create a new config with default template
            template_map = {
                "scene_generation": "pre_game_prompt.txt",
                "adventure_gameplay": "gameplay_prompt.txt",
                "text_explanation": "text_explanation_prompt.txt",
            }

            template_filename = template_map.get(purpose)
            if not template_filename:
                msg = f"Invalid purpose: {purpose}"
                raise ValueError(msg) from None

            try:
                system_prompt = read_prompt_template(template_filename)
            except ValueError as e:
                msg = f"Failed to load template {template_filename}: {e!s}"
                raise ValueError(msg) from e

            return cls.objects.create(
                purpose=purpose,
                system_prompt=system_prompt,
                is_active=True,
                temperature=0.7,
            )


class OpenAIKey(models.Model):
    key = models.CharField(
        max_length=255,
        help_text="OpenAI API Key (starts with 'sk-')",
    )
    name = models.CharField(
        max_length=100,
        help_text="A name to identify this key (e.g., 'Primary Key', 'Backup Key')",
    )
    is_active = models.BooleanField(
        default=True,
        help_text="Only active keys will be used",
    )
    order = models.IntegerField(
        default=10,
        validators=[MinValueValidator(0)],
        help_text="Keys with lower order values will be used first",
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["order"]
        verbose_name = "OpenAI API Key"
        verbose_name_plural = "OpenAI API Keys"

    def __str__(self):
        return f"{self.name} ({'Active' if self.is_active else 'Inactive'})"

    @classmethod
    def get_available_key(cls):
        """Get the first available active key."""
        return cls.objects.filter(is_active=True).order_by("order").first()


class GameScenario(models.Model):
    category = models.CharField(
        max_length=100,
        choices=[
            ("genre", "Genre"),
            ("sub-genre", "Sub-Genre"),
        ],
        help_text="Category of the scenario",
        default="genre",
    )
    name = models.CharField(
        max_length=100,
        help_text="Name of the scenario (e.g., Fantasy, Sci-Fi)",
    )
    example = models.TextField(
        help_text="Example movies/books/etc. of this genre/sub-genre",
        blank=True,
    )
    order = models.IntegerField(
        default=10,
        help_text="Order in which scenarios are displayed (lower numbers first)",
    )
    is_active = models.BooleanField(
        default=True,
        help_text="Only active scenarios will be shown to users",
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["order"]

    def __str__(self):
        return f"{self.name} ({'Active' if self.is_active else 'Inactive'})"


class GameStory(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    genre = models.CharField(
        max_length=100,
        help_text="Genre of the story (e.g., Fantasy, Sci-Fi)",
    )
    model = models.ForeignKey(
        LLMModel,
        on_delete=models.PROTECT,
        related_name="game_stories",
    )
    title = models.CharField(
        max_length=200,
        help_text="Title of the story (generated or user-provided)",
    )
    status = models.CharField(
        max_length=20,
        choices=[
            ("IN_PROGRESS", "In Progress"),
            ("COMPLETED", "Completed"),
            ("ABANDONED", "Abandoned"),
        ],
        default="IN_PROGRESS",
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["-updated_at"]
        verbose_name_plural = "Game stories"

    def __str__(self):
        return f"{self.id}: {self.title} ({self.user.username})"

    def get_context(self):
        context = []
        for interaction in self.interactions.all().order_by("created_at"):
            context.extend(interaction.format_messages())
        return context


class GameInteraction(models.Model):
    story = models.ForeignKey(
        GameStory,
        on_delete=models.CASCADE,
        related_name="interactions",
    )
    role = models.CharField(
        max_length=10,
        choices=[
            ("system", "System"),
            ("user", "User"),
        ],
        default="user",
    )
    system_input = models.TextField()
    system_output = models.TextField(blank=True)
    status = models.CharField(
        max_length=20,
        choices=[
            ("pending", "Pending"),
            ("completed", "Completed"),
            ("failed", "Failed"),
        ],
        default="pending",
    )
    error = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-created_at"]

    def __str__(self):
        return f"Interaction in {self.story.title} at {self.created_at}"

    def save(self, *args, **kwargs):
        super().save(*args, **kwargs)
        # Update the parent story's updated_at timestamp
        self.story.save(update_fields=["updated_at"])

    def format_messages(self):
        """Format the message for the LLM API."""
        messages = [
            {
                "role": self.role,
                "content": self.system_input,
            },
        ]

        if self.system_output:
            messages.append(
                {
                    "role": "assistant",
                    "content": self.system_output,
                },
            )
        return messages


# New model for text explanation lookups
class TextExplanation(models.Model):
    STATUS_CHOICES = [
        ("pending", "Pending"),
        ("completed", "Completed"),
        ("failed", "Failed"),
    ]

    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="explanations",
    )
    story = models.ForeignKey(
        "GameStory",
        on_delete=models.CASCADE,
        related_name="explanations",
    )
    selected_text = models.TextField()
    context_text = models.TextField()
    explanation = models.TextField(blank=True)
    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default="pending",
    )
    error = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Explanation for {self.selected_text[:30]} by {self.user}"
