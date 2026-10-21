from django import forms

from .models import (
    PerformanceReview,
    PerformanceGoal,
    PerformanceAppraisal,
)


class DateValidationMixin:
    start_field = None
    end_field = None

    def clean(self):
        cleaned = super().clean()

        start = cleaned.get(self.start_field)
        end = cleaned.get(self.end_field)

        if start and end and end < start:
            self.add_error(
                self.end_field,
                "End date cannot be before the start date.",
            )

        return cleaned


class PerformanceReviewForm(DateValidationMixin, forms.ModelForm):
    start_field = "review_period_start"
    end_field = "review_period_end"

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
            "review_period_start": forms.DateInput(
                attrs={"type": "date"}
            ),
            "review_period_end": forms.DateInput(
                attrs={"type": "date"}
            ),
            "goals": forms.Textarea(attrs={"rows": 3}),
            "achievements": forms.Textarea(attrs={"rows": 3}),
            "feedback": forms.Textarea(attrs={"rows": 3}),
            "rating": forms.Select(
                choices=[
                    ("", "Select rating"),
                    (1, "1 - Needs improvement"),
                    (2, "2 - Below expectations"),
                    (3, "3 - Meets expectations"),
                    (4, "4 - Exceeds expectations"),
                    (5, "5 - Outstanding"),
                ]
            ),
        }


class PerformanceGoalForm(DateValidationMixin, forms.ModelForm):
    start_field = "start_date"
    end_field = "target_date"

    class Meta:
        model = PerformanceGoal
        fields = [
            "employee",
            "title",
            "description",
            "start_date",
            "target_date",
            "progress",
            "status",
        ]
        widgets = {
            "start_date": forms.DateInput(
                attrs={"type": "date"}
            ),
            "target_date": forms.DateInput(
                attrs={"type": "date"}
            ),
            "description": forms.Textarea(attrs={"rows": 4}),
            "progress": forms.NumberInput(
                attrs={"min": 0, "max": 100}
            ),
        }


class PerformanceAppraisalForm(
    DateValidationMixin,
    forms.ModelForm,
):
    start_field = "appraisal_period_start"
    end_field = "appraisal_period_end"

    class Meta:
        model = PerformanceAppraisal
        fields = [
            "employee",
            "title",
            "appraisal_period_start",
            "appraisal_period_end",
            "overall_rating",
            "strengths",
            "improvement_areas",
            "comments",
            "status",
        ]
        widgets = {
            "appraisal_period_start": forms.DateInput(
                attrs={"type": "date"}
            ),
            "appraisal_period_end": forms.DateInput(
                attrs={"type": "date"}
            ),
            "strengths": forms.Textarea(attrs={"rows": 3}),
            "improvement_areas": forms.Textarea(attrs={"rows": 3}),
            "comments": forms.Textarea(attrs={"rows": 3}),
            "overall_rating": forms.Select(
                choices=[
                    ("", "Select rating"),
                    (1, "1 - Needs improvement"),
                    (2, "2 - Below expectations"),
                    (3, "3 - Meets expectations"),
                    (4, "4 - Exceeds expectations"),
                    (5, "5 - Outstanding"),
                ]
            ),
        }
