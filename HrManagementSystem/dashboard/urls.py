from django.urls import path

from . import views


urlpatterns = [
    path("", views.dashboard, name="dashboard"),
    path("settings/", views.settings_view, name="settings"),
    path("settings/company/", views.company_settings, name="company_settings"),
    path("settings/system/", views.system_settings, name="system_settings"),
]