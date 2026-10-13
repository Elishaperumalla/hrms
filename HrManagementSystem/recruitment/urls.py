
from django.urls import path
from . import views

app_name = "recruitment"

urlpatterns = [
    path("", views.recruitment_dashboard, name="dashboard"),
    path("applications/add/", views.application_create, name="application_create"),
    path(
        "applications/<int:pk>/",
        views.application_detail,
        name="application_detail",
    ),
    path(
        "applications/<int:pk>/status/",
        views.application_update_status,
        name="application_update_status",
    ),
    path("jobs/", views.job_list, name="job_list"),
    path("jobs/add/", views.job_create, name="job_create"),
]
