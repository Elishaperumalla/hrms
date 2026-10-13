from django import forms
from django.contrib.auth.forms import (
    AuthenticationForm,
    UserCreationForm,
    SetPasswordForm,
    PasswordChangeForm,
)

from .models import User


# ============================================================
# LOGIN
# ============================================================

class LoginForm(AuthenticationForm):

    username = forms.CharField(
        widget=forms.TextInput(
            attrs={
                "class": "form-control",
                "placeholder": "Username",
                "autocomplete": "username",
            }
        )
    )

    password = forms.CharField(
        widget=forms.PasswordInput(
            attrs={
                "class": "form-control",
                "placeholder": "Password",
                "autocomplete": "current-password",
            }
        )
    )


# ============================================================
# REGISTER
# ============================================================
# Kept for compatibility.
# Public registration is disabled in account/views.py.
# HRMS users will be created through the authorized HR/Admin
# employee-management workflow.

class RegisterForm(UserCreationForm):

    first_name = forms.CharField(
        required=False,
        widget=forms.TextInput(
            attrs={
                "class": "form-control",
                "placeholder": "First Name",
            }
        ),
    )

    last_name = forms.CharField(
        required=False,
        widget=forms.TextInput(
            attrs={
                "class": "form-control",
                "placeholder": "Last Name",
            }
        ),
    )

    email = forms.EmailField(
        widget=forms.EmailInput(
            attrs={
                "class": "form-control",
                "placeholder": "Email",
            }
        ),
    )

    phone = forms.CharField(
        required=False,
        widget=forms.TextInput(
            attrs={
                "class": "form-control",
                "placeholder": "Phone",
            }
        ),
    )

    class Meta:
        model = User
        fields = (
            "username",
            "first_name",
            "last_name",
            "email",
            "phone",
            "password1",
            "password2",
        )

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        self.fields["username"].widget.attrs.update(
            {
                "class": "form-control",
                "placeholder": "Username",
            }
        )

        self.fields["password1"].widget.attrs.update(
            {
                "class": "form-control",
                "placeholder": "Password",
            }
        )

        self.fields["password2"].widget.attrs.update(
            {
                "class": "form-control",
                "placeholder": "Confirm Password",
            }
        )

    def save(self, commit=True):
        user = super().save(commit=False)

        user.role = User.Role.EMPLOYEE
        user.must_change_password = False

        if commit:
            user.save()

        return user


# ============================================================
# FORGOT PASSWORD
# ============================================================

class ForgotPasswordForm(forms.Form):

    email = forms.EmailField(
        widget=forms.EmailInput(
            attrs={
                "class": "form-control",
                "placeholder": "Enter your registered email",
                "autocomplete": "email",
            }
        )
    )


# ============================================================
# OTP VERIFICATION
# ============================================================

class OTPVerificationForm(forms.Form):

    otp = forms.CharField(
        max_length=6,
        min_length=6,
        widget=forms.TextInput(
            attrs={
                "class": "form-control",
                "placeholder": "Enter 6-digit OTP",
                "maxlength": "6",
                "autocomplete": "one-time-code",
            }
        ),
    )


# ============================================================
# RESET PASSWORD
# ============================================================

class ResetPasswordForm(SetPasswordForm):

    new_password1 = forms.CharField(
        label="New Password",
        widget=forms.PasswordInput(
            attrs={
                "class": "form-control",
                "placeholder": "New Password",
                "autocomplete": "new-password",
            }
        ),
    )

    new_password2 = forms.CharField(
        label="Confirm New Password",
        widget=forms.PasswordInput(
            attrs={
                "class": "form-control",
                "placeholder": "Confirm New Password",
                "autocomplete": "new-password",
            }
        ),
    )


# ============================================================
# CHANGE PASSWORD
# ============================================================

class ChangePasswordForm(PasswordChangeForm):

    old_password = forms.CharField(
        label="Current Password",
        widget=forms.PasswordInput(
            attrs={
                "class": "form-control",
                "placeholder": "Current Password",
                "autocomplete": "current-password",
            }
        ),
    )

    new_password1 = forms.CharField(
        label="New Password",
        widget=forms.PasswordInput(
            attrs={
                "class": "form-control",
                "placeholder": "New Password",
                "autocomplete": "new-password",
            }
        ),
    )

    new_password2 = forms.CharField(
        label="Confirm New Password",
        widget=forms.PasswordInput(
            attrs={
                "class": "form-control",
                "placeholder": "Confirm New Password",
                "autocomplete": "new-password",
            }
        ),
    )