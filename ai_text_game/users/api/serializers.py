from dj_rest_auth.models import TokenModel
from dj_rest_auth.registration.serializers import RegisterSerializer
from dj_rest_auth.serializers import LoginSerializer
from dj_rest_auth.serializers import PasswordChangeSerializer
from dj_rest_auth.serializers import UserDetailsSerializer
from django.contrib.auth import get_user_model
from rest_framework import serializers

UserModel = get_user_model()


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
        fields = ("pk", *extra_fields, "must_change_password")
        read_only_fields = ("email",)

    def get_must_change_password(self, obj):
        # Return False if no profile exists (shouldn't happen)
        if hasattr(obj, "userprofile"):
            return obj.userprofile.must_change_password
        return False


class TokenSerializer(serializers.ModelSerializer):
    user = CustomUserDetailsSerializer()

    class Meta:
        model = TokenModel
        fields = ["key", "created", "user"]


class CustomRegisterSerializer(RegisterSerializer):
    name = serializers.CharField(required=True)

    def get_cleaned_data(self):
        data = super().get_cleaned_data()
        data["name"] = self.validated_data.get("name", "")
        return data

    def save(self, request):
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
