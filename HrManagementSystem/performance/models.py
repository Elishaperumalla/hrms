
from django.conf import settings
from django.db import models
from django.core.validators import MinValueValidator, MaxValueValidator


class PerformanceReview(models.Model):
    class Status(models.TextChoices):
        PENDING = "PENDING", "Pending"
        IN_PROGRESS = "IN_PROGRESS", "In Progress"
        COMPLETED = "COMPLETED", "Completed"

    employee = models.ForeignKey(
        "employees.Employee",
        on_delete=models.CASCADE,
        related_name="performance_reviews",
    )
    reviewer = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="performance_reviews_given",
    )
    review_title = models.CharField(max_length=200)
    review_period_start = models.DateField()
    review_period_end = models.DateField()
    goals = models.TextField(blank=True)
    achievements = models.TextField(blank=True)
    feedback = models.TextField(blank=True)
    rating = models.PositiveSmallIntegerField(
        null=True,
        blank=True,
        validators=[MinValueValidator(1), MaxValueValidator(5)],
    )
    status = models.CharField(
        max_length=20,
        choices=Status.choices,
        default=Status.PENDING,
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["-created_at"]

    def __str__(self):
        return f"{self.review_title} - {self.employee}"
