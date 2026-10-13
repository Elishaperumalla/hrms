
from django import forms
from .models import PerformanceReview


class PerformanceReviewForm(forms.ModelForm):
    class Meta:
        model = PerformanceReview
        fields = [
            "employee",
            "review_title",
            "review_period_start",
            "review_period_end",
            "goals",
            "achievements",
            "feedback",
            "rating",
            "status",
        ]
        widgets = {
            "review_period_start": forms.DateInput(attrs={"type": "date"}),
            "review_period_end": forms.DateInput(attrs={"type": "date"}),
            "goals": forms.Textarea(attrs={"rows": 3}),
            "achievements": forms.Textarea(attrs={"rows": 3}),
            "feedback": forms.Textarea(attrs={"rows": 3}),
            "rating": forms.Select(
                choices=[("", "Select rating"), (1, "1 - Needs improvement"),
                         (2, "2 - Below expectations"), (3, "3 - Meets expectations"),
                         (4, "4 - Exceeds expectations"), (5, "5 - Outstanding")]
            ),
        }

    def clean(self):
        cleaned = super().clean()
        start = cleaned.get("review_period_start")
        end = cleaned.get("review_period_end")
        if start and end and end < start:
            self.add_error(
                "review_period_end",
                "Review end date cannot be before the start date.",
            )
        return cleaned
