from allauth.account.adapter import get_adapter
from allauth.account.models import EmailAddress
from dj_rest_auth.models import TokenModel
from dj_rest_auth.registration.serializers import RegisterSerializer
from dj_rest_auth.serializers import LoginSerializer
from dj_rest_auth.serializers import PasswordChangeSerializer
from dj_rest_auth.serializers import UserDetailsSerializer
from django.contrib.auth import get_user_model
from django.utils.translation import gettext_lazy as _
from rest_framework import serializers

from ai_text_game.users.models import UserProfile

UserModel = get_user_model()


class NativeLanguageChoiceField(serializers.ChoiceField):
    """Read/write UserProfile.native_language on a User serializer instance."""

    def get_attribute(self, instance):
        profile = getattr(instance, "userprofile", None)
        if not profile:
            return None
        return profile.native_language or None


class CustomLoginSerializer(LoginSerializer):
    @staticmethod
    def validate_email_verification_status(user, email=None):
        # Skip validation for superusers
        if user.is_superuser:
            return

        # Call parent's static method
        LoginSerializer.validate_email_verification_status(user, email)


class CustomUserDetailsSerializer(UserDetailsSerializer):
    """
    User model w/o password
    """

    must_change_password = serializers.SerializerMethodField()
    native_language = NativeLanguageChoiceField(
        choices=UserProfile.NATIVE_LANGUAGE_CHOICES,
        allow_null=True,
        required=False,
    )

    class Meta:
        extra_fields = []
        # see https://github.com/iMerica/dj-rest-auth/issues/181
        # UserModel.XYZ causing attribute error while importing other
        # classes from `serializers.py`. So, we need to check whether the auth model has
        # the attribute or not
        if hasattr(UserModel, "USERNAME_FIELD"):
            extra_fields.append(UserModel.USERNAME_FIELD)
        if hasattr(UserModel, "EMAIL_FIELD"):
            extra_fields.append(UserModel.EMAIL_FIELD)
        if hasattr(UserModel, "first_name"):
            extra_fields.append("first_name")
        if hasattr(UserModel, "last_name"):
            extra_fields.append("last_name")
        model = UserModel
        fields = ("pk", *extra_fields, "must_change_password", "native_language")
        read_only_fields = ("email",)

    def get_must_change_password(self, obj):
        # Return False if no profile exists (shouldn't happen)
        if hasattr(obj, "userprofile"):
            return obj.userprofile.must_change_password
        return False

    def update(self, instance, validated_data):
        native_language = validated_data.pop("native_language", serializers.empty)
        user = super().update(instance, validated_data)
        if native_language is not serializers.empty and hasattr(user, "userprofile"):
            user.userprofile.native_language = native_language or ""
            user.userprofile.save(update_fields=["native_language"])
        return user


class TokenSerializer(serializers.ModelSerializer):
    user = CustomUserDetailsSerializer()

    class Meta:
        model = TokenModel
        fields = ["key", "created", "user"]


class CustomRegisterSerializer(RegisterSerializer):
    name = serializers.CharField(required=True)

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["username"].required = False
        self.fields["username"].allow_blank = True
        self._pending_verification_user = None

    @property
    def pending_verification_user(self):
        return self._pending_verification_user

    def validate_username(self, username):
        if not username:
            return username
        existing = UserModel.objects.filter(username__iexact=username).first()
        if (
            existing
            and EmailAddress.objects.filter(user=existing, verified=False).exists()
        ):
            return username
        return get_adapter().clean_username(username)

    def validate(self, attrs):
        if not attrs.get("username"):
            attrs["username"] = attrs["email"]

        existing = UserModel.objects.filter(email__iexact=attrs["email"]).first()
        if existing:
            try:
                email_address = EmailAddress.objects.get(
                    user=existing,
                    email__iexact=attrs["email"],
                )
            except EmailAddress.DoesNotExist:
                pass
            else:
                if email_address.verified:
                    raise serializers.ValidationError(
                        {
                            "email": [
                                _(
                                    "A user is already registered with this "
                                    "e-mail address.",
                                ),
                            ],
                        },
                    )
                self._pending_verification_user = existing

        return super().validate(attrs)

    def get_cleaned_data(self):
        data = super().get_cleaned_data()
        data["name"] = self.validated_data.get("name", "")
        if not data.get("username"):
            data["username"] = data.get("email", "")
        return data

    def save(self, request):
        pending_user = self._pending_verification_user
        if pending_user:
            pending_user.set_password(self.validated_data["password1"])
            pending_user.name = self.validated_data.get("name", pending_user.name)
            pending_user.save()
            self.cleaned_data = self.get_cleaned_data()
            self.custom_signup(request, pending_user)
            return pending_user

        user = super().save(request)
        user.name = self.cleaned_data.get("name")
        user.save()
        return user


class CustomPasswordChangeSerializer(PasswordChangeSerializer):
    def save(self):
        if hasattr(self.user, "userprofile"):
            self.user.userprofile.must_change_password = False
            self.user.userprofile.save()
        return super().save()
