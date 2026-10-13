
from django.db import models
from django.core.validators import FileExtensionValidator
from django.core.exceptions import ValidationError
from django.utils import timezone
import os


def validate_resume_size(file):
    if file.size > 5 * 1024 * 1024:
        raise ValidationError("Resume size must not exceed 5 MB.")


class JobOpening(models.Model):
    class JobType(models.TextChoices):
        FULL_TIME = "FULL_TIME", "Full-time"
        PART_TIME = "PART_TIME", "Part-time"
        INTERNSHIP = "INTERNSHIP", "Internship"
        CONTRACT = "CONTRACT", "Contract"

    title = models.CharField(max_length=150)
    department = models.CharField(max_length=100, blank=True)
    location = models.CharField(max_length=150, blank=True)
    job_type = models.CharField(
        max_length=20,
        choices=JobType.choices,
        default=JobType.FULL_TIME,
    )
    description = models.TextField(blank=True)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-created_at"]

    def __str__(self):
        return self.title


class CandidateApplication(models.Model):
    class Source(models.TextChoices):
        LINKEDIN = "LINKEDIN", "LinkedIn"
        NAUKRI = "NAUKRI", "Naukri"
        GOOGLE_FORMS = "GOOGLE_FORMS", "Google Forms"
        EMAIL = "EMAIL", "Email"
        REFERRAL = "REFERRAL", "Employee Referral"
        OTHER = "OTHER", "Other"

    class Status(models.TextChoices):
        NEW = "NEW", "New"
        SHORTLISTED = "SHORTLISTED", "Shortlisted"
        INTERVIEW = "INTERVIEW", "Interview"
        HIRED = "HIRED", "Hired"
        REJECTED = "REJECTED", "Rejected"

    job = models.ForeignKey(
        JobOpening,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="applications",
    )
    candidate_name = models.CharField(max_length=150)
    email = models.EmailField()
    phone = models.CharField(max_length=20, blank=True)
    source = models.CharField(
        max_length=20,
        choices=Source.choices,
        default=Source.OTHER,
    )
    source_reference = models.URLField(blank=True)
    resume = models.FileField(
        upload_to="recruitment/resumes/%Y/%m/",
        validators=[
            FileExtensionValidator(
                allowed_extensions=["pdf", "doc", "docx"]
            ),
            validate_resume_size,
        ],
    )
    skills = models.CharField(max_length=500, blank=True)
    notes = models.TextField(blank=True)
    status = models.CharField(
        max_length=20,
        choices=Status.choices,
        default=Status.NEW,
    )
    applied_at = models.DateTimeField(default=timezone.now)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["-applied_at"]

    def __str__(self):
        return f"{self.candidate_name} - {self.email}"

    @property
    def resume_filename(self):
        return os.path.basename(self.resume.name) if self.resume else ""
