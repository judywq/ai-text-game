# ruff: noqa: PERF401

from typing import Literal

from django.contrib.auth import get_user_model
from django.core.exceptions import ValidationError
from django.core.validators import MaxValueValidator
from django.core.validators import MinValueValidator
from django.core.validators import URLValidator
from django.db import models
from langchain_core.prompts import ChatPromptTemplate

from ai_text_game.core.models import CreatableBase
from ai_text_game.core.models import TimestampedBase

User = get_user_model()


LLM_TYPE_CHOICES = [
    ("openai", "OpenAI"),
    ("anthropic", "Anthropic"),
    ("groq", "Groq"),
    ("deepseek", "DeepSeek"),
    ("custom", "Custom"),
]


class LLMModel(TimestampedBase):
    order = models.IntegerField(
        default=10,
        help_text="Order of the model in the UI (smaller number comes first)",
    )
    name = models.CharField(
        max_length=200,
        help_text=(
            "The model name for calling the LLM API (e.g., gpt-4o-2024-11-20)."
            " Check <a href='https://platform.openai.com/docs/models#current-model-aliases'"
            " target='_blank'>OpenAI</a>, "
            " <a href='https://docs.anthropic.com/en/docs/about-claude/models'"
            " target='_blank'>Anthropic</a>, "
            " <a href='https://console.groq.com/docs/models'"
            " target='_blank'>Groq</a>, "
            " <a href='https://api-docs.deepseek.com/quick_start/pricing'"
            " target='_blank'>DeepSeek</a> "
            " for model list."
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
    llm_type = models.CharField(
        max_length=20,
        choices=LLM_TYPE_CHOICES,
        default="openai",
        help_text="The type of LLM service to use",
    )
    url = models.URLField(
        max_length=500,
        blank=True,
        help_text=(
            "URL for custom LLM service "
            "(e.g., http://host.docker.internal:8080/v1). "
            "Leave empty for OpenAI."
        ),
        validators=[URLValidator()],
    )

    class Meta:
        ordering = ["order"]
        get_latest_by = "created_at"

    def __str__(self):
        return (
            f"{self.llm_type}: {self.display_name} "
            f"({'Active' if self.is_active else 'Inactive'})"
        )

    def save(self, *args, **kwargs):
        # If this model is being set as default, reset all others
        if self.is_default:
            LLMModel.objects.exclude(id=self.id).update(is_default=False)
        super().save(*args, **kwargs)

    @classmethod
    def get_active_models(cls):
        return cls.objects.filter(is_active=True)

    def clean(self):
        super().clean()
        if self.llm_type == "custom" and not self.url:
            raise ValidationError(
                {"url": "URL is required for custom LLM services"},
            )


class QuotaConfig(TimestampedBase):
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

    class Meta:
        get_latest_by = "created_at"

    def __str__(self):
        return f"QuotaConfig({self.model.display_name}, limit={self.daily_limit})"


class LLMConfig(TimestampedBase):
    PURPOSE_CHOICES = [
        ("scene_generation", "Scene Generation"),
        ("text_explanation", "Text Explanation"),
        ("story_skeleton_generation", "Story Skeleton Generation"),
        ("story_continuation", "Story Continuation"),
        ("story_ending", "Story Ending"),
    ]

    purpose = models.CharField(
        max_length=50,
        choices=PURPOSE_CHOICES,
        help_text="The purpose of this configuration",
    )
    model = models.ForeignKey(
        LLMModel,
        on_delete=models.SET_NULL,
        related_name="llm_configs",
        help_text="The LLM model this config applies to",
        null=True,
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
        purpose: Literal[
            "scene_generation",
            "adventure_gameplay",
            "text_explanation",
            "story_skeleton_generation",
            "story_continuation",
            "story_ending",
        ],
    ):
        """Get the active config for the given purpose."""
        try:
            return cls.objects.get(purpose=purpose, is_active=True)
        except cls.DoesNotExist:
            msg = (
                f"No active config found for purpose: {purpose}."
                f"Please create one in the admin panel."
            )
            raise ValueError(msg) from None

    def get_prompt_template(self):
        """Get a ChatPromptTemplate for this config."""
        return ChatPromptTemplate.from_template(self.system_prompt)


class APIKey(TimestampedBase):
    key = models.CharField(
        max_length=255,
        help_text="API Key (e.g., 'sk-...')",
    )
    name = models.CharField(
        max_length=100,
        help_text="A name to identify this key (e.g., 'Primary Key', 'Backup Key')",
    )
    llm_model = models.ForeignKey(
        LLMModel,
        on_delete=models.SET_NULL,
        related_name="api_keys",
        help_text="The LLM model this key applies to",
        blank=True,
        null=True,
    )
    llm_type = models.CharField(
        max_length=20,
        choices=LLM_TYPE_CHOICES,
        blank=True,
        help_text="The type of LLM service to use",
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

    class Meta:
        ordering = ["order"]

    def __str__(self):
        return f"{self.name} ({'Active' if self.is_active else 'Inactive'})"

    @classmethod
    def get_available_key(cls, model_name: str):
        """Get the first available active key."""
        found = (
            cls.objects.filter(
                is_active=True,
                llm_model__name=model_name,
            )
            .order_by("order")
            .first()
        )

        if found:
            return found

        try:
            llm_model = LLMModel.objects.get(name=model_name)
        except LLMModel.DoesNotExist:
            msg = f"LLM model {model_name} does not exist"
            raise ValueError(msg) from None

        return (
            cls.objects.filter(
                is_active=True,
                llm_type=llm_model.llm_type,
            )
            .order_by("order")
            .first()
        )

    def clean(self):
        super().clean()
        if self.llm_type == "custom" and not self.llm_model:
            raise ValidationError(
                {"llm_model": "LLM model is required for custom LLM services"},
            )

        if not self.llm_model and not self.llm_type:
            raise ValidationError(
                {"llm_model": "LLM model or LLM type is required"},
            )


class GameScenario(TimestampedBase):
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

    class Meta:
        ordering = ["order"]

    def __str__(self):
        return f"{self.name} ({'Active' if self.is_active else 'Inactive'})"


class StorySkeleton(TimestampedBase):
    story = models.OneToOneField(
        "GameStory",
        on_delete=models.CASCADE,
        related_name="skeleton",
    )
    background = models.TextField(blank=True)
    raw_data = models.JSONField(blank=True, default=dict)
    status = models.CharField(
        max_length=20,
        choices=[
            ("INIT", "Init"),
            ("GENERATING", "Generating"),
            ("COMPLETED", "Completed"),
            ("FAILED", "Failed"),
        ],
        default="INIT",
    )

    def has_milestones(self) -> bool:
        """Check if the skeleton has milestones"""
        return self.count_milestones() > 0

    @staticmethod
    def count_milestones(raw_data: dict) -> int:
        """Count the number of milestones in the raw data"""
        return len(raw_data.get("milestones", []))


class StoryProgress(TimestampedBase):
    story = models.ForeignKey(
        "GameStory",
        on_delete=models.CASCADE,
        related_name="progress_entries",
    )
    content = models.TextField()
    decision_point_id = models.CharField(max_length=50, blank=True)
    chosen_option_id = models.CharField(max_length=50, blank=True)
    chosen_option_text = models.TextField(blank=True)
    is_end_point = models.BooleanField(default=False)

    class Meta:
        ordering = ["created_at"]

    @property
    def is_fulfilled(self):
        """Check if the progress entry is fulfilled (has a chosen option)"""
        return bool(self.chosen_option_id)

    def set_chosen_option(self, option_id: str, option_text: str):
        if not self.is_option_valid(option_id):
            return False
        self.chosen_option_id = option_id
        self.chosen_option_text = option_text
        self.save()
        return True

    def is_option_valid(self, option_id: str) -> bool:
        """Check if the option ID is valid"""
        # Remove the last part of the option ID (the option ID)
        decision_point_id = ".".join(option_id.split(".")[:-1])
        return self.decision_point_id == decision_point_id

    @property
    def options_data(self):
        """Return options in the format expected by the frontend"""
        return [
            {
                "option_id": option.option_id,
                "option_name": option.option_name,
            }
            for option in self.options.all()
        ]


class StoryOption(TimestampedBase):
    progress = models.ForeignKey(
        "StoryProgress",
        on_delete=models.CASCADE,
        related_name="options",
    )
    option_id = models.CharField(max_length=50)
    option_name = models.TextField()

    class Meta:
        ordering = ["created_at"]

    def __str__(self):
        return f"{self.option_id}: {self.option_name}"


class GameStory(CreatableBase, TimestampedBase):
    CEFR_CHOICES = [
        ("A1", "A1"),
        ("A2", "A2"),
        ("B1", "B1"),
        ("B2", "B2"),
        ("C1", "C1"),
        ("C2", "C2"),
    ]
    genre = models.CharField(
        max_length=100,
        help_text="Genre of the story (e.g., Fantasy, Sci-Fi)",
    )
    cefr_level = models.CharField(
        max_length=10,
        choices=CEFR_CHOICES,
        help_text="CEFR level of the story (e.g., A1, B2)",
        default="A1",
    )
    scene_text = models.TextField(
        blank=True,
        help_text="Scene text of the story (generated or user-provided)",
    )
    details = models.TextField(
        blank=True,
        help_text="Additional details of the story (generated or user-provided)",
    )
    title = models.CharField(
        max_length=200,
        help_text="Title of the story (generated or user-provided)",
    )
    status = models.CharField(
        max_length=20,
        choices=[
            ("INIT", "Init"),
            ("IN_PROGRESS", "In Progress"),
            ("COMPLETED", "Completed"),
            ("ABANDONED", "Abandoned"),
        ],
        default="INIT",
    )

    class Meta:
        ordering = ["-updated_at"]
        verbose_name_plural = "Game stories"

    def __str__(self):
        return f"{self.id}: {self.title} ({self.created_by})"

    def get_context(self):
        return [
            interaction.format_message()
            for interaction in self.interactions.all().order_by("created_at")
        ]

    def get_option_text(self, option_id: str) -> str | None:
        """Get the text for the option ID"""
        if not hasattr(self, "skeleton"):
            return None
        skeleton = self.skeleton.raw_data
        for milestone in skeleton["milestones"]:
            for decision_point in milestone["decision_points"]:
                if (
                    decision_point["decision_point_id"]
                    == self.get_current_decision_point()
                ):
                    for option in decision_point["options"]:
                        if option["option_id"] == option_id:
                            return option["option_name"]
        return None

    def get_next_decision_point(self):
        # Flatten the story skeleton into a single list of decision points
        decision_points = []
        for milestone in self.skeleton.raw_data["milestones"]:
            for decision_point in milestone["decision_points"]:
                decision_points.append(
                    (
                        decision_point["decision_point_id"],
                        milestone["milestone_id"],
                    ),
                )

        # Sort decision points by decision id
        decision_points.sort(key=lambda x: x[0])

        # Find the next decision point
        current_decision_point = self._get_last_decision_point()
        next_decision_point = next(
            (dp for dp in decision_points if dp[0] > current_decision_point),
            None,
        )

        if next_decision_point:
            return next_decision_point[0]
        return ""

    @property
    def story_state(self) -> dict:
        """Get the current story state for the graph"""
        progress_entries = self.progress_entries.all()
        return {
            "story_skeleton": self.skeleton.raw_data
            if hasattr(self, "skeleton")
            else None,
            "current_decision_point": self.get_current_decision_point(),
            "story_progress": [entry.content for entry in progress_entries],
            "chosen_decisions": [
                entry.chosen_option_id
                for entry in progress_entries
                if entry.chosen_option_id
            ],
            "cefr_level": self.cefr_level,
            "status": self.status,
        }

    def get_current_decision_point(self):
        """Get the current decision point ID"""
        if self.progress_entries.count() == 0:
            return "M1.D1"
        latest_progress = self.progress_entries.last()
        if latest_progress.is_fulfilled:
            # Get the next decision point
            return self.get_next_decision_point()
        return latest_progress.decision_point_id

    def _get_last_decision_point(self):
        """Get the last decision point ID"""
        if self.progress_entries.count() == 0:
            return "M1.D1"
        latest_progress = self.progress_entries.last()
        return latest_progress.decision_point_id


class TextExplanation(CreatableBase, TimestampedBase):
    STATUS_CHOICES = [
        ("pending", "Pending"),
        ("completed", "Completed"),
        ("failed", "Failed"),
    ]
    model = models.ForeignKey(
        LLMModel,
        on_delete=models.SET_NULL,
        related_name="text_explanations",
        null=True,
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

    def __str__(self):
        return f"Explanation for {self.selected_text[:30]} by {self.created_by}"
