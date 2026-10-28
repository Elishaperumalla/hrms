from django.urls import path

from . import views
from .profile_edit import edit_profile_view


urlpatterns = [
    path("login/", views.login_view, name="login"),
    path("register/",views.register_view, name="register"),
    path("logout/", views.logout_view, name="logout"),
    path("profile/", views.profile_view, name="profile"),
    path("edit-profile/", edit_profile_view, name="edit_profile"),
    path("change-password/",views.change_password_view, name="change_password"),
    path("forgot-password/",views.forgot_password_view,name="forgot_password"),
    path("verify-otp/",views.verify_otp_view,name="verify_otp"),
    path("reset-password/",views.reset_password_view,name="reset_password"),
    

    path("face-enrollment/", views.face_enrollment_view, name="face_enrollment"),
]
