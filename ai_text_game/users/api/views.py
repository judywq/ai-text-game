from allauth.account import app_settings as allauth_account_settings
from allauth.account.internal.flows.email_verification_by_code import (
    EmailVerificationProcess,
)
from allauth.account.internal.textkit import compare_code
from allauth.account.models import EmailAddress
from allauth.account.utils import complete_signup
from dj_rest_auth.app_settings import api_settings
from dj_rest_auth.registration.views import RegisterView
from dj_rest_auth.registration.views import ResendEmailVerificationView
from dj_rest_auth.registration.views import VerifyEmailView as DjRestAuthVerifyEmailView
from dj_rest_auth.utils import jwt_encode
from django.utils.translation import gettext_lazy as _
from rest_framework import status
from rest_framework.decorators import action
from rest_framework.exceptions import ValidationError
from rest_framework.mixins import ListModelMixin
from rest_framework.mixins import RetrieveModelMixin
from rest_framework.mixins import UpdateModelMixin
from rest_framework.response import Response
from rest_framework.viewsets import GenericViewSet

from ai_text_game.users.models import User

from .serializers import CustomUserDetailsSerializer


class CustomRegisterView(RegisterView):
    def perform_create(self, serializer):
        pending_user = serializer.pending_verification_user
        user = serializer.save(self.request)

        if (
            allauth_account_settings.EMAIL_VERIFICATION
            != allauth_account_settings.EmailVerificationMethod.MANDATORY
        ):
            if api_settings.USE_JWT:
                self.access_token, self.refresh_token = jwt_encode(user)
            elif self.token_model:
                api_settings.TOKEN_CREATOR(self.token_model, user, serializer)

        if pending_user:
            django_request = getattr(self.request, "_request", self.request)
            email_address = EmailAddress.objects.get(
                user=user,
                email__iexact=user.email,
            )
            email_address.send_confirmation(django_request)
            return user

        django_request = getattr(self.request, "_request", self.request)
        complete_signup(
            django_request,
            user,
            allauth_account_settings.EMAIL_VERIFICATION,
            None,
        )
        return user


class CustomVerifyEmailView(DjRestAuthVerifyEmailView):
    """
    dj-rest-auth's VerifyEmailView uses link-based confirmation keys, which
    allauth does not support when ACCOUNT_EMAIL_VERIFICATION_BY_CODE_ENABLED is on.
    """

    def post(self, request, *args, **kwargs):
        if not allauth_account_settings.EMAIL_VERIFICATION_BY_CODE_ENABLED:
            return super().post(request, *args, **kwargs)

        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        code = serializer.validated_data["key"]

        django_request = getattr(request, "_request", request)
        process = EmailVerificationProcess.resume(django_request)
        if not process:
            raise ValidationError(
                {
                    "non_field_errors": [
                        _(
                            "Verification session expired. Use resend code to get "
                            "a new one.",
                        ),
                    ],
                },
            )

        if not compare_code(actual=code, expected=process.code):
            if not process.record_invalid_attempt():
                raise ValidationError(
                    {
                        "non_field_errors": [
                            _(
                                "Too many invalid attempts. Use resend code to try "
                                "again.",
                            ),
                        ],
                    },
                )
            raise ValidationError({"key": [_("Incorrect code.")]})

        email_address = process.email_address
        if not email_address.can_set_verified():
            raise ValidationError(
                {"non_field_errors": [_("This email address is already in use.")]},
            )

        confirmed = process.finish()
        if not confirmed:
            raise ValidationError(
                {
                    "non_field_errors": [
                        _("Email verification failed. Please try again."),
                    ],
                },
            )

        return Response({"detail": _("ok")}, status=status.HTTP_200_OK)


class CustomResendEmailVerificationView(ResendEmailVerificationView):
    """Resend a verification code and refresh the session-bound process."""

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        django_request = getattr(request, "_request", request)
        email_address = self.get_queryset().filter(**serializer.validated_data).first()
        if email_address and not email_address.verified:
            email_address.send_confirmation(django_request)

        return Response({"detail": _("ok")}, status=status.HTTP_200_OK)


class UserViewSet(RetrieveModelMixin, ListModelMixin, UpdateModelMixin, GenericViewSet):
    serializer_class = CustomUserDetailsSerializer
    queryset = User.objects.all()
    lookup_field = "username"

    def get_queryset(self, *args, **kwargs):
        assert isinstance(self.request.user.id, int)
        return self.queryset.filter(id=self.request.user.id)

    @action(detail=False)
    def me(self, request):
        serializer = CustomUserDetailsSerializer(
            request.user,
            context={"request": request},
        )
        return Response(status=status.HTTP_200_OK, data=serializer.data)
