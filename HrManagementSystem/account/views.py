import random
from datetime import timedelta
from django.contrib import messages
from django.contrib.auth import update_session_auth_hash
from django.contrib.auth.decorators import login_required
from django.core.mail import send_mail
from django.shortcuts import redirect, render
from django.contrib.auth import login, logout
from django.utils import timezone
from .forms import LoginForm,RegisterForm
from .forms import (ForgotPasswordForm,OTPVerificationForm,ResetPasswordForm,ChangePasswordForm)
from .models import PasswordResetOTP, User


def login_view(request):

    if request.user.is_authenticated:
        return redirect("dashboard")

    if request.method == "POST":

        form = LoginForm(request, data=request.POST)

        if form.is_valid():

            user = form.get_user()

            login(request, user)

            messages.success(
                request,
                f"Welcome back, {user.get_full_name() or user.username}!"
            )

            return redirect("dashboard")

    else:
        form = LoginForm()

    return render(
        request,
        "account/login.html",
        {"form": form}
    )

def register_view(request):

    if request.user.is_authenticated:
        return redirect("dashboard")

    if request.method == "POST":

        form = RegisterForm(request.POST)

        if form.is_valid():

            user = form.save()

            messages.success(
                request,
                "Account created successfully. You can now login."
            )

            return redirect("login")

    else:
        form = RegisterForm()

    return render(
        request,
        "account/register.html",
        {"form": form}
    )

@login_required
def logout_view(request):

    if request.method == "POST":

        logout(request)

        messages.success(
            request,
            "You have been logged out successfully."
        )

    return redirect("login")


@login_required
def profile_view(request):

    return render(
        request,
        "account/profile.html"
    )



@login_required
def change_password_view(request):

    if request.method == "POST":

        form = ChangePasswordForm(
            user=request.user,
            data=request.POST
        )

        if form.is_valid():

            user = form.save()

            # Keep the user logged in after password change
            update_session_auth_hash(
                request,
                user
            )

            messages.success(
                request,
                "Your password has been changed successfully."
            )

            return redirect("profile")

    else:

        form = ChangePasswordForm(
            user=request.user
        )


    return render(
        request,
        "account/change_password.html",
        {
            "form": form
        }
    )

def forgot_password_view(request):

    if request.method == "POST":

        form = ForgotPasswordForm(request.POST)

        if form.is_valid():

            email = form.cleaned_data["email"]

            try:

                user = User.objects.get(
                    email__iexact=email
                )

            except User.DoesNotExist:

                messages.error(
                    request,
                    "No account was found with this email address."
                )

                return render(
                    request,
                    "account/forgot_password.html",
                    {"form": form}
                )


            # Delete previous OTPs

            PasswordResetOTP.objects.filter(
                user=user,
                is_verified=False
            ).delete()


            # Generate 6 digit OTP

            otp = str(
                random.randint(
                    100000,
                    999999
                )
            )


            # OTP valid for 10 minutes

            expires_at = (
                timezone.now()
                + timedelta(minutes=10)
            )


            PasswordResetOTP.objects.create(
                user=user,
                otp=otp,
                expires_at=expires_at
            )


            # Send email

            send_mail(

                subject="HRMS - Password Reset OTP",

                message=(
                    f"Hello {user.get_full_name() or user.username},\n\n"
                    f"Your HRMS password reset OTP is: {otp}\n\n"
                    f"This OTP is valid for 10 minutes.\n\n"
                    f"If you did not request this password reset, "
                    f"please ignore this email.\n\n"
                    f"HRMS"
                ),

                from_email=None,

                recipient_list=[
                    user.email
                ],

                fail_silently=False,
            )


            # Store user ID in session

            request.session[
                "password_reset_user_id"
            ] = user.id


            messages.success(
                request,
                "OTP has been sent to your registered email."
            )


            return redirect(
                "verify_otp"
            )


    else:

        form = ForgotPasswordForm()


    return render(
        request,
        "account/forgot_password.html",
        {
            "form": form
        }
    )

def verify_otp_view(request):

    user_id = request.session.get(
        "password_reset_user_id"
    )


    if not user_id:

        messages.error(
            request,
            "Password reset session expired."
        )

        return redirect("forgot_password")


    try:

        user = User.objects.get(
            id=user_id
        )

    except User.DoesNotExist:

        messages.error(
            request,
            "Invalid password reset request."
        )

        return redirect("forgot_password")


    if request.method == "POST":

        form = OTPVerificationForm(
            request.POST
        )

        if form.is_valid():

            otp_value = form.cleaned_data["otp"]


            otp_record = (
                PasswordResetOTP.objects
                .filter(
                    user=user,
                    is_verified=False
                )
                .order_by("-created_at")
                .first()
            )


            if not otp_record:

                form.add_error(
                    "otp",
                    "Invalid or expired OTP."
                )

            elif otp_record.is_expired():

                form.add_error(
                    "otp",
                    "OTP has expired. Please request a new OTP."
                )

            elif otp_record.otp != otp_value:

                form.add_error(
                    "otp",
                    "Incorrect OTP."
                )

            else:

                otp_record.is_verified = True

                otp_record.save(
                    update_fields=[
                        "is_verified"
                    ]
                )


                request.session[
                    "password_reset_verified"
                ] = True


                return redirect(
                    "reset_password"
                )

    else:

        form = OTPVerificationForm()


    return render(
        request,
        "account/verify_otp.html",
        {
            "form": form
        }
    )


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
            "Please verify the OTP first."
        )

        return redirect(
            "forgot_password"
        )


    try:

        user = User.objects.get(
            id=user_id
        )

    except User.DoesNotExist:

        messages.error(
            request,
            "Invalid password reset request."
        )

        return redirect(
            "forgot_password"
        )


    if request.method == "POST":

        form = ResetPasswordForm(
            user,
            request.POST
        )

        if form.is_valid():

            form.save()


            # Clear reset session

            request.session.pop(
                "password_reset_user_id",
                None
            )

            request.session.pop(
                "password_reset_verified",
                None
            )


            messages.success(
                request,
                "Password reset successfully. You can now login."
            )


            return redirect(
                "login"
            )

    else:

        form = ResetPasswordForm(
            user
        )


    return render(
        request,
        "account/reset_password.html",
        {
            "form": form
        }
    )