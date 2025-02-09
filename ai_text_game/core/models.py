from django.db import models


class TimestampedBase(models.Model):
    """Base model that adds created_at and updated_at timestamps."""

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        abstract = True


class TaskTimestampedBase(TimestampedBase):
    """Base model that adds task-related timestamps."""

    started_at = models.DateTimeField(null=True, blank=True)
    ended_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        abstract = True


class CreatableBase(models.Model):
    """
    Abstract base model that adds a created_by field.
    """

    created_by = models.ForeignKey(
        "users.User",
        on_delete=models.SET_NULL,
        blank=True,
        null=True,
        related_name="%(class)s_created",
    )

    class Meta:
        abstract = True
