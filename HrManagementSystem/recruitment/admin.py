
from django.contrib import admin
from .models import CandidateApplication, JobOpening


@admin.register(JobOpening)
class JobOpeningAdmin(admin.ModelAdmin):
    list_display = (
        "title", "department", "location", "job_type", "is_active",
        "created_at",
    )
    list_filter = ("job_type", "is_active", "department")
    search_fields = ("title", "department", "location")


@admin.register(CandidateApplication)
class CandidateApplicationAdmin(admin.ModelAdmin):
    list_display = (
        "candidate_name", "email", "job", "source", "status", "applied_at",
    )
    list_filter = ("status", "source", "job")
    search_fields = ("candidate_name", "email", "phone", "skills")
    readonly_fields = ("applied_at", "updated_at")
