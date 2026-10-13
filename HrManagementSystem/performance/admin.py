
from django.contrib import admin
from .models import PerformanceReview


@admin.register(PerformanceReview)
class PerformanceReviewAdmin(admin.ModelAdmin):
    list_display = (
        "review_title", "employee", "review_period_start",
        "review_period_end", "rating", "status",
    )
    list_filter = ("status", "rating", "review_period_start")
    search_fields = ("review_title", "goals", "employee__id")
