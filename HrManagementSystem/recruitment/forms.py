
from django import forms
from .models import CandidateApplication, JobOpening


class CandidateApplicationForm(forms.ModelForm):
    class Meta:
        model = CandidateApplication
        fields = [
            "job",
            "candidate_name",
            "email",
            "phone",
            "source",
            "source_reference",
            "resume",
            "skills",
            "notes",
        ]
        widgets = {
            "job": forms.Select(attrs={"class": "form-select"}),
            "candidate_name": forms.TextInput(attrs={"class": "form-control"}),
            "email": forms.EmailInput(attrs={"class": "form-control"}),
            "phone": forms.TextInput(attrs={"class": "form-control"}),
            "source": forms.Select(attrs={"class": "form-select"}),
            "source_reference": forms.URLInput(
                attrs={"class": "form-control"}
            ),
            "resume": forms.ClearableFileInput(
                attrs={"class": "form-control", "accept": ".pdf,.doc,.docx"}
            ),
            "skills": forms.TextInput(attrs={"class": "form-control"}),
            "notes": forms.Textarea(
                attrs={"class": "form-control", "rows": 3}
            ),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["job"].queryset = JobOpening.objects.filter(is_active=True)
        self.fields["job"].required = False


class JobOpeningForm(forms.ModelForm):
    class Meta:
        model = JobOpening
        fields = [
            "title",
            "department",
            "location",
            "job_type",
            "description",
            "is_active",
        ]
        widgets = {
            "title": forms.TextInput(attrs={"class": "form-control"}),
            "department": forms.TextInput(attrs={"class": "form-control"}),
            "location": forms.TextInput(attrs={"class": "form-control"}),
            "job_type": forms.Select(attrs={"class": "form-select"}),
            "description": forms.Textarea(
                attrs={"class": "form-control", "rows": 5}
            ),
            "is_active": forms.CheckboxInput(
                attrs={"class": "form-check-input"}
            ),
        }
