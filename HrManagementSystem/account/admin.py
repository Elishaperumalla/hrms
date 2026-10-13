from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin

from .models import User, PasswordResetOTP


@admin.register(User)
class UserAdmin(BaseUserAdmin):

    list_display = (
        "username",
        "email",
        "first_name",
        "last_name",
        "role",
        "is_active",
        "must_change_password",
        "last_login",
    )

    list_filter = (
        "role",
        "is_active",
        "is_staff",
        "must_change_password",
    )

    search_fields = (
        "username",
        "email",
        "first_name",
        "last_name",
        "phone",
    )

    ordering = (
        "username",
    )

    fieldsets = BaseUserAdmin.fieldsets + (
        (
            "HRMS Information",
            {
                "fields": (
                    "role",
                    "phone",
                    "profile_picture",
                    "must_change_password",
                )
            },
        ),
    )

    add_fieldsets = BaseUserAdmin.add_fieldsets + (
        (
            "HRMS Information",
            {
                "fields": (
                    "role",
                    "phone",
                    "profile_picture",
                    "must_change_password",
                )
            },
        ),
    )


@admin.register(PasswordResetOTP)
class PasswordResetOTPAdmin(admin.ModelAdmin):

    list_display = (
        "user",
        "otp",
        "created_at",
        "expires_at",
        "is_verified",
    )

    list_filter = (
        "is_verified",
        "created_at",
    )

    search_fields = (
        "user__username",
        "user__email",
    )

    ordering = (
        "-created_at",
    )

    readonly_fields = (
        "created_at",
    )