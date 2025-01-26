import io

import pandas as pd
from allauth.account.forms import SignupForm
from allauth.account.models import EmailAddress
from allauth.socialaccount.forms import SignupForm as SocialSignupForm
from django import forms
from django.contrib.auth import forms as admin_forms
from django.db import transaction
from django.utils.translation import gettext_lazy as _

from .models import User


class UserAdminChangeForm(admin_forms.UserChangeForm):
    class Meta(admin_forms.UserChangeForm.Meta):  # type: ignore[name-defined]
        model = User


class UserAdminCreationForm(admin_forms.UserCreationForm):
    """
    Form for User Creation in the Admin Area.
    To change user signup, see UserSignupForm and UserSocialSignupForm.
    """

    class Meta(admin_forms.UserCreationForm.Meta):  # type: ignore[name-defined]
        model = User
        error_messages = {
            "username": {"unique": _("This username has already been taken.")},
        }


class UserSignupForm(SignupForm):
    """
    Form that will be rendered on a user sign up section/screen.
    Default fields will be added automatically.
    Check UserSocialSignupForm for accounts created from social.
    """


class UserSocialSignupForm(SocialSignupForm):
    """
    Renders the form when user has signed up using social accounts.
    Default fields will be added automatically.
    See UserSignupForm otherwise.
    """


class AdminUserRegistrationForm(forms.ModelForm):
    """Form for registering a new user through admin."""

    email = forms.EmailField(required=True)
    password = forms.CharField(widget=forms.PasswordInput)
    username = forms.CharField(
        required=False,
        help_text="If not provided, email will be used",
    )

    class Meta:
        model = User
        fields = ["email", "username", "password", "name"]

    def clean_email(self):
        email = self.cleaned_data["email"]
        if User.objects.filter(email=email).exists():
            msg = "A user with this email already exists."
            raise forms.ValidationError(msg)
        return email

    def clean(self):
        cleaned_data = super().clean()
        username = cleaned_data.get("username")
        email = cleaned_data.get("email")

        # If username is empty, use email as username
        if not username and email:
            cleaned_data["username"] = email

        return cleaned_data

    def save(self, commit=True):  # noqa: FBT002
        user = super().save(commit=False)
        user.set_password(self.cleaned_data["password"])

        if commit:
            with transaction.atomic():
                user.save()
                # Create verified email address
                EmailAddress.objects.create(
                    user=user,
                    email=self.cleaned_data["email"],
                    primary=True,
                    verified=True,
                )
        return user


class UserBatchUploadForm(forms.Form):
    """Form for uploading Excel file containing user data."""

    file = forms.FileField()

    def clean_file(self):
        file = self.cleaned_data["file"]
        allowed_extension = ".xlsx"
        if not file.name.endswith(allowed_extension):
            msg = f"Only Excel ({allowed_extension}) files are allowed."
            raise forms.ValidationError(msg)

        # Validate file contents
        try:
            df_data = pd.read_excel(io.BytesIO(file.read()))
        except ValueError as e:
            msg = f"Invalid Excel file: {e!s}"
            raise forms.ValidationError(msg) from e
        else:
            required_columns = ["email", "password"]
            for col in required_columns:
                if col not in df_data.columns:
                    msg = f"Missing required column: {col}"
                    raise forms.ValidationError(msg)

            # Reset file pointer for later use
            file.seek(0)
            return file
