from django.contrib import admin

from .models import PerformanceReview, PerformanceGoal, PerformanceAppraisal


@admin.register(PerformanceReview)
class PerformanceReviewAdmin(admin.ModelAdmin):
    list_display = (
        "review_title",
        "employee",
        "review_period_start",
        "review_period_end",
        "rating",
        "status",
        "reviewer",
    )
    list_filter = ("status", "rating", "review_period_start")
    search_fields = (
        "review_title",
        "goals",
        "achievements",
        "feedback",
    )
    date_hierarchy = "review_period_start"


@admin.register(PerformanceGoal)
class PerformanceGoalAdmin(admin.ModelAdmin):
    list_display = (
        "title",
        "employee",
        "start_date",
        "target_date",
        "progress",
        "status",
        # "assigned_by",
    )
    list_filter = ("status", "target_date")
    search_fields = ("title", "description")


@admin.register(PerformanceAppraisal)
class PerformanceAppraisalAdmin(admin.ModelAdmin):
    list_display = (
        "title",
        "employee",
        "appraisal_period_start",
        "appraisal_period_end",
        "overall_rating",
        "status",
        "reviewer",
    )
    list_filter = ("status", "overall_rating")
    search_fields = ("title", "strengths", "improvement_areas", "comments")