
from django.urls import path
from . import views

app_name = "performance"

urlpatterns = [
    path("", views.dashboard, name="dashboard"),
    path("reviews/", views.review_list, name="review_list"),
    path("reviews/create/", views.review_create, name="review_create"),
    path("reviews/<int:pk>/", views.review_detail, name="review_detail"),
    path("reviews/<int:pk>/edit/", views.review_update, name="review_update"),
]
