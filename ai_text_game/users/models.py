from django.contrib.auth.models import AbstractUser
from django.db import models
from django.db.models import CharField
from django.urls import reverse
from django.utils.translation import gettext_lazy as _


class Course(models.Model):
    course_id = models.IntegerField(primary_key=True)
    course_name = models.CharField(max_length=200)

    class Meta:
        ordering = ["course_id"]

    def __str__(self):
        return f"{self.course_id}: {self.course_name}"


class User(AbstractUser):
    """
    Default custom user model for ATG.
    If adding fields that need to be filled at user signup,
    check forms.SignupForm and forms.SocialSignupForms accordingly.
    """

    ROLE_CHOICES = (
        ("admin", "Admin"),
        ("student", "Student"),
    )
    role = CharField(max_length=20, choices=ROLE_CHOICES, default="student")

    course = models.ForeignKey(
        Course,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        help_text="The course this student belongs to",
    )

    def is_admin(self):
        return self.role == "admin"

    def is_student(self):
        return self.role == "student"

    # First and last name do not cover name patterns around the globe
    name = CharField(_("Name of User"), blank=True, max_length=255)
    first_name = None  # type: ignore[assignment]
    last_name = None  # type: ignore[assignment]

    def get_absolute_url(self) -> str:
        """Get URL for user's detail view.

        Returns:
            str: URL for user detail.

        """
        return reverse("users:detail", kwargs={"username": self.username})
