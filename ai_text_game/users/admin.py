import pandas as pd
from allauth.account.decorators import secure_admin_login
from allauth.account.models import EmailAddress
from django.conf import settings
from django.contrib import admin
from django.contrib import messages
from django.contrib.auth import admin as auth_admin
from django.db import transaction
from django.http import HttpRequest
from django.http import HttpResponseRedirect
from django.template.response import TemplateResponse
from django.urls import path
from django.urls import reverse
from django.utils.translation import gettext_lazy as _

from .forms import AdminUserRegistrationForm
from .forms import UserAdminChangeForm
from .forms import UserAdminCreationForm
from .forms import UserBatchUploadForm
from .models import User
from .models import UserProfile

if settings.DJANGO_ADMIN_FORCE_ALLAUTH:
    # Force the `admin` sign in process to go through the `django-allauth` workflow:
    # https://docs.allauth.org/en/latest/common/admin.html#admin
    admin.autodiscover()
    admin.site.login = secure_admin_login(admin.site.login)  # type: ignore[method-assign]


@admin.register(User)
class UserAdmin(auth_admin.UserAdmin):
    form = UserAdminChangeForm
    add_form = UserAdminCreationForm
    fieldsets = (
        (None, {"fields": ("username", "password")}),
        (_("Personal info"), {"fields": ("name", "email")}),
        (
            _("Permissions"),
            {
                "fields": (
                    "is_active",
                    "is_staff",
                    "is_superuser",
                    "groups",
                    "user_permissions",
                ),
            },
        ),
        (_("Important dates"), {"fields": ("last_login", "date_joined")}),
    )
    list_display = ["id", "username", "email", "name", "is_superuser", "date_joined"]
    search_fields = ["name", "email"]

    def has_add_permission(self, request: HttpRequest) -> bool:
        """Disable the default add user button"""
        return False

    def get_urls(self):
        urls = super().get_urls()
        custom_urls = [
            path(
                "register/",
                self.admin_site.admin_view(self.register_user_view),
                name="user_register",
            ),
            path(
                "batch-upload/",
                self.admin_site.admin_view(self.batch_upload_view),
                name="user_batch_upload",
            ),
        ]
        return custom_urls + urls

    def register_user_view(self, request):
        if request.method == "POST":
            form = AdminUserRegistrationForm(request.POST)
            if form.is_valid():
                form.save()
                messages.success(request, "User registered successfully.")
                return HttpResponseRedirect(reverse("admin:users_user_changelist"))
        else:
            form = AdminUserRegistrationForm()

        context = {
            "form": form,
            "title": "Register New User",
            **self.admin_site.each_context(request),
        }
        return TemplateResponse(request, "admin/users/user/register.html", context)

    def batch_upload_view(self, request):
        if request.method == "POST":
            form = UserBatchUploadForm(request.POST, request.FILES)
            if form.is_valid():
                file = request.FILES["file"]
                df_data = pd.read_excel(file, keep_default_na=False)
                success_count = 0
                errors = []

                for idx, row in df_data.iterrows():
                    try:
                        with transaction.atomic():
                            row_dict = row.to_dict()
                            user = User.objects.create(
                                email=row_dict["email"],
                                username=row_dict.get("username") or row_dict["email"],
                                name=row_dict.get("name") or "",
                            )
                            user.set_password(str(row_dict["password"]))
                            user.save()

                            # Set must_change_password for batch users
                            if hasattr(user, "userprofile"):
                                user.userprofile.must_change_password = True
                                user.userprofile.save()

                            # Create verified email address
                            EmailAddress.objects.create(
                                user=user,
                                email=row_dict["email"],
                                primary=True,
                                verified=True,
                            )
                            success_count += 1
                    except (KeyError, ValueError) as e:
                        msg = f"Row {idx + 2}: {e!s}"
                        errors.append(msg)

                if success_count > 0:
                    messages.success(
                        request,
                        f"Successfully created {success_count} users.",
                    )
                if errors:
                    messages.error(request, "Errors occurred: " + "; ".join(errors))
                return HttpResponseRedirect(reverse("admin:users_user_changelist"))
        else:
            form = UserBatchUploadForm()

        context = {
            "form": form,
            "title": "Batch Upload Users",
            **self.admin_site.each_context(request),
        }
        return TemplateResponse(request, "admin/users/user/batch_upload.html", context)

    def changelist_view(self, request, extra_context=None):
        extra_context = extra_context or {}
        extra_context["show_register_button"] = True
        extra_context["show_batch_upload_button"] = True
        return super().changelist_view(request, extra_context=extra_context)


@admin.register(UserProfile)
class UserProfileAdmin(admin.ModelAdmin):
    list_display = ["id", "user", "must_change_password"]
    search_fields = ["user__name", "user__email"]
