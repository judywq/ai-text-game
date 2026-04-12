from django.conf import settings
from django.contrib.auth.models import AbstractUser
from django.db import models
from django.db.models import CharField
from django.db.models.signals import post_save
from django.dispatch import receiver
from django.utils.translation import gettext_lazy as _


class User(AbstractUser):
    """
    Default custom user model for ATG.
    If adding fields that need to be filled at user signup,
    check forms.SignupForm and forms.SocialSignupForms accordingly.
    """

    # First and last name do not cover name patterns around the globe
    name = CharField(_("Name of User"), blank=True, max_length=255)
    first_name = None  # type: ignore[assignment]
    last_name = None  # type: ignore[assignment]


class UserProfile(models.Model):
    NATIVE_ENGLISH = "en"
    NATIVE_FRENCH = "fr"
    NATIVE_JAPANESE = "ja"
    NATIVE_CHINESE = "zh"
    NATIVE_LANGUAGE_CHOICES = [
        (NATIVE_ENGLISH, _("English")),
        (NATIVE_FRENCH, _("French")),
        (NATIVE_JAPANESE, _("Japanese")),
        (NATIVE_CHINESE, _("Chinese")),
    ]

    user = models.OneToOneField(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    must_change_password = models.BooleanField(default=False)
    is_demo_account = models.BooleanField(
        default=False,
        help_text="Whether this is a demo account that should use demo prompts",
    )
    native_language = models.CharField(
        _("Native language"),
        max_length=10,
        choices=NATIVE_LANGUAGE_CHOICES,
        null=True,
        blank=True,
        help_text="Language used for word explanations and UI copy where relevant.",
    )

    def __str__(self) -> str:
        return f"{self.user.name} ({self.user.email})"

    @staticmethod
    def native_language_prompt_label(code: str | None) -> str:
        """English name for LLM prompts (stable, not translated)."""
        labels = {
            UserProfile.NATIVE_ENGLISH: "English",
            UserProfile.NATIVE_FRENCH: "French",
            UserProfile.NATIVE_JAPANESE: "Japanese",
            UserProfile.NATIVE_CHINESE: "Chinese",
        }
        if not code:
            return "English"
        return labels.get(code, "English")


@receiver(post_save, sender=User)
def create_user_profile(sender, instance, created, **kwargs):
    if created:
        UserProfile.objects.create(user=instance)


@receiver(post_save, sender=User)
def save_user_profile(sender, instance, **kwargs):
    if hasattr(instance, "userprofile"):
        instance.userprofile.save()
