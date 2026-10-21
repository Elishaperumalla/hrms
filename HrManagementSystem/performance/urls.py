from django.urls import path
from . import views

app_name = "performance"

urlpatterns = [
    path("", views.dashboard, name="dashboard"),

    # Reviews
    path("reviews/", views.review_list, name="review_list"),
    path("reviews/create/", views.review_create, name="review_create"),
    path("reviews/<int:pk>/", views.review_detail, name="review_detail"),
    path("reviews/<int:pk>/edit/", views.review_update, name="review_update"),

    # Goals
    path("goals/", views.goal_list, name="goal_list"),
    path("goals/create/", views.goal_create, name="goal_create"),
    path("goals/<int:pk>/edit/", views.goal_update, name="goal_update"),

    # Appraisals
    path("appraisals/", views.appraisal_list, name="appraisal_list"),
    path("appraisals/create/", views.appraisal_create, name="appraisal_create"),

    # Reports
    path("reports/", views.performance_report, name="performance_report"),
]