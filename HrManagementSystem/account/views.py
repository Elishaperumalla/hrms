import secrets
import string

from datetime import timedelta

from django.contrib import messages
from django.contrib.auth import (
    authenticate,
    login,
    logout,
    update_session_auth_hash,
)
from django.contrib.auth.decorators import login_required
from django.contrib.auth.forms import SetPasswordForm
from django.core.mail import send_mail
from django.db import transaction
from django.shortcuts import redirect, render
from django.utils import timezone

from .forms import (
    LoginForm,
    RegisterForm,
    ForgotPasswordForm,
    OTPVerificationForm,
    ResetPasswordForm,
    ChangePasswordForm,
)
from .models import User, PasswordResetOTP


# ============================================================
# TEMPORARY PASSWORD GENERATOR
# ============================================================

def generate_temporary_password(length=12):
    """
    Generate a secure temporary password containing:
    - uppercase
    - lowercase
    - digit
    - special character
    """

    if length < 8:
        length = 8

    alphabet = string.ascii_letters + string.digits + "!@#$%^&*"

    while True:
        password = "".join(
            secrets.choice(alphabet)
            for _ in range(length)
        )

        if (
            any(char.islower() for char in password)
            and any(char.isupper() for char in password)
            and any(char.isdigit() for char in password)
            and any(char in "!@#$%^&*" for char in password)
        ):
            return password


# ============================================================
# UNIQUE USERNAME
# ============================================================

def generate_unique_username(email):
    """
    Generate a username from the email address.

    Example:
        john.doe@gmail.com
        -> john.doe
        -> john.doe1 if already exists
    """

    base_username = email.split("@")[0].strip().lower()

    # Keep only safe username characters.
    base_username = "".join(
        char
        for char in base_username
        if char.isalnum() or char in "._-"
    )

    if not base_username:
        base_username = "user"

    username = base_username
    counter = 1

    while User.objects.filter(
        username__iexact=username
    ).exists():
        username = f"{base_username}{counter}"
        counter += 1

    return username


# ============================================================
# CREATE HRMS USER
# ============================================================

@transaction.atomic
def create_hrms_user(
    *,
    email,
    first_name="",
    last_name="",
    phone="",
    role=User.Role.EMPLOYEE,
):
    """
    Create a User account for an HRMS employee.

    This function:
        1. Validates email
        2. Generates username
        3. Generates temporary password
        4. Creates User securely
        5. Sends login credentials by email

    Employee ↔ User linking is intentionally NOT done here.
    That belongs to the employees workflow.
    """

    email = (email or "").strip().lower()

    if not email:
        raise ValueError("Email address is required.")

    if User.objects.filter(
        email__iexact=email
    ).exists():
        raise ValueError(
            "A user account with this email already exists."
        )

    if role not in dict(User.Role.choices):
        raise ValueError("Invalid user role.")

    username = generate_unique_username(email)
    temporary_password = generate_temporary_password()

    user = User(
        username=username,
        first_name=(first_name or "").strip(),
        last_name=(last_name or "").strip(),
        email=email,
        phone=(phone or "").strip(),
        role=role,
        must_change_password=True,
        is_active=True,
    )

    # NEVER store the temporary password directly.
    user.set_password(temporary_password)
    user.save()

    full_name = (
        f"{user.first_name} {user.last_name}"
    ).strip()

    if not full_name:
        full_name = user.username

    subject = "Your HRMS Account Credentials"

    message = f"""
Hello {full_name},

Your HRMS account has been created successfully.

Login details:

Username: {username}
Temporary Password: {temporary_password}

Please log in using these credentials.

For security reasons, you will be required to change
your password when you log in for the first time.

If you did not expect this account, please contact your HR administrator.

Regards,
HRMS Administration
""".strip()

    send_mail(
        subject,
        message,
        None,
        [email],
        fail_silently=False,
    )

    return user


# ============================================================
# LOGIN
# ============================================================

def login_view(request):

    if request.user.is_authenticated:
        return redirect("dashboard")

    if request.method == "POST":

        form = LoginForm(
            request,
            data=request.POST,
        )

        if form.is_valid():

            user = form.get_user()

            login(request, user)

            # Newly created HRMS users must change
            # their temporary password.
            if user.must_change_password:
                messages.info(
                    request,
                    "Please change your temporary password before continuing.",
                )

                return redirect("change_password")

            return redirect("dashboard")

    else:
        form = LoginForm()

    return render(
        request,
        "account/login.html",
        {
            "form": form,
        },
    )


# ============================================================
# REGISTER
# ============================================================

def register_view(request):
    """
    Public registration is intentionally disabled.

    HRMS accounts must be created by authorized
    HR/Admin workflows.
    """

    messages.warning(
        request,
        "Public registration is disabled. "
        "HRMS accounts are created by authorized administrators.",
    )

    return redirect("login")


# ============================================================
# LOGOUT
# ============================================================

@login_required
def logout_view(request):

    if request.method == "POST":
        logout(request)

        messages.success(
            request,
            "You have been logged out successfully.",
        )

        return redirect("login")

    return redirect("dashboard")


# ============================================================
# PROFILE
# ============================================================

@login_required
def profile_view(request):

    return render(
        request,
        "account/profile.html",
        {
            "user": request.user,
        },
    )


# ============================================================
# CHANGE PASSWORD
# ============================================================

@login_required
def change_password_view(request):

    if request.method == "POST":

        form = ChangePasswordForm(
            request.user,
            request.POST,
        )

        if form.is_valid():

            user = form.save()

            # Remove the first-login restriction.
            user.must_change_password = False
            user.save(
                update_fields=["must_change_password"]
            )

            update_session_auth_hash(
                request,
                user,
            )

            messages.success(
                request,
                "Your password has been changed successfully.",
            )

            return redirect("dashboard")

    else:
        form = ChangePasswordForm(
            request.user
        )

    return render(
        request,
        "account/change_password.html",
        {
            "form": form,
        },
    )


# ============================================================
# FORGOT PASSWORD
# ============================================================

def forgot_password_view(request):

    if request.method == "POST":

        form = ForgotPasswordForm(
            request.POST
        )

        if form.is_valid():

            email = form.cleaned_data[
                "email"
            ].strip().lower()

            user = User.objects.filter(
                email__iexact=email
            ).first()

            if user:

                # Remove previous unverified OTPs.
                PasswordResetOTP.objects.filter(
                    user=user,
                    is_verified=False,
                ).delete()

                otp = str(
                    secrets.randbelow(900000) + 100000
                )

                expires_at = (
                    timezone.now()
                    + timedelta(minutes=10)
                )

                PasswordResetOTP.objects.create(
                    user=user,
                    otp=otp,
                    expires_at=expires_at,
                )

                send_mail(
                    "HRMS Password Reset OTP",
                    (
                        f"Your HRMS password reset OTP is: {otp}\n\n"
                        "This OTP is valid for 10 minutes."
                    ),
                    None,
                    [user.email],
                    fail_silently=False,
                )

                request.session[
                    "password_reset_user_id"
                ] = user.id

                messages.success(
                    request,
                    "OTP has been sent to your registered email.",
                )

                return redirect("verify_otp")

            # Do not reveal whether an email exists.
            messages.success(
                request,
                "If an account exists for this email, "
                "a password reset OTP has been sent.",
            )

    else:
        form = ForgotPasswordForm()

    return render(
        request,
        "account/forgot_password.html",
        {
            "form": form,
        },
    )


# ============================================================
# VERIFY OTP
# ============================================================

def verify_otp_view(request):

    user_id = request.session.get(
        "password_reset_user_id"
    )

    if not user_id:
        messages.error(
            request,
            "Your password reset session has expired.",
        )

        return redirect("forgot_password")

    user = User.objects.filter(
        id=user_id
    ).first()

    if not user:
        request.session.pop(
            "password_reset_user_id",
            None,
        )

        messages.error(
            request,
            "Invalid password reset request.",
        )

        return redirect("forgot_password")

    if request.method == "POST":

        form = OTPVerificationForm(
            request.POST
        )

        if form.is_valid():

            otp_value = form.cleaned_data[
                "otp"
            ].strip()

            otp_record = (
                PasswordResetOTP.objects
                .filter(
                    user=user,
                    is_verified=False,
                )
                .order_by("-created_at")
                .first()
            )

            if not otp_record:

                messages.error(
                    request,
                    "Invalid or expired OTP.",
                )

            elif otp_record.is_expired():

                messages.error(
                    request,
                    "OTP has expired. Please request a new one.",
                )

            elif otp_record.otp != otp_value:

                messages.error(
                    request,
                    "Invalid OTP.",
                )

            else:

                otp_record.is_verified = True
                otp_record.save(
                    update_fields=["is_verified"]
                )

                request.session[
                    "password_reset_verified"
                ] = True

                messages.success(
                    request,
                    "OTP verified successfully.",
                )

                return redirect("reset_password")

    else:
        form = OTPVerificationForm()

    return render(
        request,
        "account/verify_otp.html",
        {
            "form": form,
        },
    )


# ============================================================
# RESET PASSWORD
# ============================================================

def reset_password_view(request):

    user_id = request.session.get(
        "password_reset_user_id"
    )

    verified = request.session.get(
        "password_reset_verified"
    )

    if not user_id or not verified:

        messages.error(
            request,
            "Please verify your OTP first.",
        )

        return redirect("forgot_password")

    user = User.objects.filter(
        id=user_id
    ).first()

    if not user:

        request.session.pop(
            "password_reset_user_id",
            None,
        )

        request.session.pop(
            "password_reset_verified",
            None,
        )

        messages.error(
            request,
            "Invalid password reset request.",
        )

        return redirect("forgot_password")

    if request.method == "POST":

        form = ResetPasswordForm(
            user,
            request.POST,
        )

        if form.is_valid():

            user = form.save()

            # A successful reset also removes
            # the temporary-password requirement.
            user.must_change_password = False
            user.save(
                update_fields=["must_change_password"]
            )

            request.session.pop(
                "password_reset_user_id",
                None,
            )

            request.session.pop(
                "password_reset_verified",
                None,
            )

            messages.success(
                request,
                "Your password has been reset successfully. "
                "Please log in.",
            )

            return redirect("login")

    else:
        form = ResetPasswordForm(
            user
        )

    return render(
        request,
        "account/reset_password.html",
        {
            "form": form,
        },
    )


# error
def bad_request(request, exception=None):
    return render(request, "error/400.html", status=400)


def permission_denied(request, exception=None):
    return render(request, "error/403.html", status=403)


def page_not_found(request, exception=None):
    return render(request, "error/404.html", status=404)


def server_error(request):
    return render(request, "error/500.html", status=500)