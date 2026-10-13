
from django.urls import path
from . import views

app_name = "reports"

urlpatterns = [
    path("", views.dashboard, name="dashboard"),
    path("export/<str:report_type>/", views.export_csv, name="export_csv"),
]
