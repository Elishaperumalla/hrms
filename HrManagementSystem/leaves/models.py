from decimal import Decimal

from django.conf import settings
from django.core.exceptions import ValidationError
from django.db import models


class LeaveType(models.Model):

    name = models.CharField(
        max_length=100,
        unique=True,
    )

    code = models.CharField(
        max_length=30,
        unique=True,
    )

    description = models.TextField(
        blank=True,
    )

    days_per_year = models.DecimalField(
        max_digits=5,
        decimal_places=1,
        default=0,
    )

    is_paid = models.BooleanField(
        default=True,
    )

    requires_approval = models.BooleanField(
        default=True,
    )

    is_active = models.BooleanField(
        default=True,
    )

    created_at = models.DateTimeField(
        auto_now_add=True,
    )

    updated_at = models.DateTimeField(
        auto_now=True,
    )

    class Meta:
        ordering = ["name"]

    def __str__(self):
        return f"{self.name} ({self.code})"


class LeaveBalance(models.Model):

    employee = models.ForeignKey(
        "employees.Employee",
        on_delete=models.CASCADE,
        related_name="leave_balances",
    )

    leave_type = models.ForeignKey(
        LeaveType,
        on_delete=models.CASCADE,
        related_name="balances",
    )

    year = models.PositiveIntegerField()

    allocated_days = models.DecimalField(
        max_digits=5,
        decimal_places=1,
        default=Decimal("0.0"),
    )

    used_days = models.DecimalField(
        max_digits=5,
        decimal_places=1,
        default=Decimal("0.0"),
    )

    carried_forward_days = models.DecimalField(
        max_digits=5,
        decimal_places=1,
        default=Decimal("0.0"),
    )

    class Meta:
        ordering = [
            "employee",
            "leave_type",
        ]

        constraints = [
            models.UniqueConstraint(
                fields=[
                    "employee",
                    "leave_type",
                    "year",
                ],
                name="unique_employee_leave_balance",
            )
        ]

    @property
    def total_available_days(self):
        return (
            self.allocated_days
            + self.carried_forward_days
        )

    @property
    def available_days(self):
        return (
            self.total_available_days
            - self.used_days
        )

    def clean(self):

        if self.allocated_days < 0:
            raise ValidationError(
                "Allocated days cannot be negative."
            )

        if self.used_days < 0:
            raise ValidationError(
                "Used days cannot be negative."
            )

        if self.carried_forward_days < 0:
            raise ValidationError(
                "Carried forward days cannot be negative."
            )

    def __str__(self):
        return (
            f"{self.employee} - "
            f"{self.leave_type} - "
            f"{self.year}"
        )


class LeaveRequest(models.Model):

    class Status(models.TextChoices):
        PENDING = "PENDING", "Pending"
        APPROVED = "APPROVED", "Approved"
        REJECTED = "REJECTED", "Rejected"
        CANCELLED = "CANCELLED", "Cancelled"

    class DurationType(models.TextChoices):
        FULL_DAY = "FULL_DAY", "Full Day"
        HALF_DAY = "HALF_DAY", "Half Day"

    class ApprovalStage(models.TextChoices):
        MANAGER = "MANAGER", "Manager"
        HR_ADMIN = "HR_ADMIN", "HR Admin"
        SUPER_ADMIN = "SUPER_ADMIN", "Super Admin"

    employee = models.ForeignKey(
        "employees.Employee",
        on_delete=models.CASCADE,
        related_name="leave_requests",
    )

    leave_type = models.ForeignKey(
        LeaveType,
        on_delete=models.PROTECT,
        related_name="requests",
    )

    start_date = models.DateField()

    end_date = models.DateField()

    duration_type = models.CharField(
        max_length=20,
        choices=DurationType.choices,
        default=DurationType.FULL_DAY,
    )

    reason = models.TextField()

    attachment = models.FileField(
        upload_to="leave/attachments/",
        blank=True,
        null=True,
    )

    status = models.CharField(
        max_length=20,
        choices=Status.choices,
        default=Status.PENDING,
    )

    approval_stage = models.CharField(
        max_length=20,
        choices=ApprovalStage.choices,
        null=True,
        blank=True,
    )

    applied_at = models.DateTimeField(
        auto_now_add=True,
    )

    approved_by = models.ForeignKey(
        "employees.Employee",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="approved_leave_requests",
    )

    approved_at = models.DateTimeField(
        null=True,
        blank=True,
    )

    rejection_reason = models.TextField(
        blank=True,
    )

    balance_deducted = models.BooleanField(
        default=False,
    )

    created_at = models.DateTimeField(
        auto_now_add=True,
    )

    updated_at = models.DateTimeField(
        auto_now=True,
    )

    class Meta:
        ordering = [
            "-created_at"
        ]

    @property
    def total_days(self):

        if not self.start_date or not self.end_date:
            return Decimal("0.0")

        days = (
            self.end_date - self.start_date
        ).days + 1

        if (
            self.duration_type
            == self.DurationType.HALF_DAY
        ):
            return Decimal("0.5")

        return Decimal(str(days))

    @property
    def is_finalized(self):
        return self.status in [
            self.Status.APPROVED,
            self.Status.REJECTED,
            self.Status.CANCELLED,
        ]

    def clean(self):

        if (
            self.start_date
            and self.end_date
            and self.end_date < self.start_date
        ):
            raise ValidationError(
                "End date cannot be before start date."
            )

        if not self.employee_id:
            return

        if not self.start_date or not self.end_date:
            return

        overlapping = (
            LeaveRequest.objects
            .filter(
                employee=self.employee,
                status__in=[
                    self.Status.PENDING,
                    self.Status.APPROVED,
                ],
                start_date__lte=self.end_date,
                end_date__gte=self.start_date,
            )
        )

        if self.pk:
            overlapping = overlapping.exclude(
                pk=self.pk
            )

        if overlapping.exists():
            raise ValidationError(
                "You already have a pending or approved "
                "leave request for the selected dates."
            )

    def save(self, *args, **kwargs):
        """
        Automatically create a LeaveBalance for the employee,
        leave type, and leave year when a leave request is saved.

        Existing LeaveBalance records are never overwritten.
        """

        super().save(*args, **kwargs)

        if (
            self.employee_id
            and self.leave_type_id
            and self.start_date
        ):
            LeaveBalance.objects.get_or_create(
                employee_id=self.employee_id,
                leave_type_id=self.leave_type_id,
                year=self.start_date.year,
                defaults={
                    "allocated_days": self.leave_type.days_per_year,
                    "used_days": Decimal("0.0"),
                    "carried_forward_days": Decimal("0.0"),
                },
            )

    def __str__(self):
        return (
            f"{self.employee} - "
            f"{self.leave_type} - "
            f"{self.start_date}"
        )


class LeaveApproval(models.Model):

    class Stage(models.TextChoices):
        MANAGER = "MANAGER", "Manager"
        HR_ADMIN = "HR_ADMIN", "HR Admin"
        SUPER_ADMIN = "SUPER_ADMIN", "Super Admin"

    class Action(models.TextChoices):
        APPROVED = "APPROVED", "Approved"
        REJECTED = "REJECTED", "Rejected"
        CANCELLED = "CANCELLED", "Cancelled"

    leave_request = models.ForeignKey(
        LeaveRequest,
        on_delete=models.CASCADE,
        related_name="approval_history",
    )

    stage = models.CharField(
        max_length=20,
        choices=Stage.choices,
    )

    action = models.CharField(
        max_length=20,
        choices=Action.choices,
    )

    acted_by = models.ForeignKey(
        "employees.Employee",
        on_delete=models.PROTECT,
        related_name="leave_actions",
    )

    reason = models.TextField(
        blank=True,
    )

    created_at = models.DateTimeField(
        auto_now_add=True,
    )

    class Meta:
        ordering = [
            "created_at"
        ]

    def __str__(self):
        return (
            f"{self.leave_request} - "
            f"{self.stage} - "
            f"{self.action}"
        )