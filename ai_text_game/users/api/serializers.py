from dj_rest_auth.models import TokenModel
from dj_rest_auth.registration.serializers import RegisterSerializer
from dj_rest_auth.serializers import LoginSerializer
from dj_rest_auth.serializers import UserDetailsSerializer
from django.contrib.auth import get_user_model
from rest_framework import serializers

from ai_text_game.users.models import Course

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
        if hasattr(UserModel, "role"):
            extra_fields.append("role")
        model = UserModel
        fields = ("pk", *extra_fields)
        read_only_fields = ("email", "role")


class TokenSerializer(serializers.ModelSerializer):
    user = CustomUserDetailsSerializer()

    class Meta:
        model = TokenModel
        fields = ["key", "created", "user"]


class CustomRegisterSerializer(RegisterSerializer):
    course_id = serializers.IntegerField(required=False, allow_null=True)

    def custom_signup(self, request, user):
        course_id = self.validated_data.get("course_id")
        if course_id:
            try:
                course = Course.objects.get(course_id=course_id)
                user.course = course
                user.save()
            except Course.DoesNotExist as e:
                raise serializers.ValidationError(
                    {"course_id": "Please enter a valid course id"},
                ) from e
