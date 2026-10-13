from datetime import datetime, time
from decimal import Decimal, ROUND_HALF_UP

from django.core.exceptions import ValidationError
from django.db import models


class Attendance(models.Model):

    # =========================================================
    # STATUS
    # =========================================================

    class Status(models.TextChoices):
        PRESENT = "PRESENT", "Present"
        ABSENT = "ABSENT", "Absent"
        HALF_DAY = "HALF_DAY", "Half Day"
        ON_LEAVE = "ON_LEAVE", "On Leave"
        HOLIDAY = "HOLIDAY", "Holiday"
        WEEK_OFF = "WEEK_OFF", "Week Off"

    # =========================================================
    # TEMPORARY DEFAULT SHIFT
    # =========================================================
    #
    # This will later be replaced by:
    # Shift + Attendance Policy + Employee Shift Assignment
    #

    DEFAULT_SHIFT_START = time(9, 0)
    DEFAULT_SHIFT_END = time(18, 0)
    DEFAULT_GRACE_MINUTES = 15

    # =========================================================
    # EMPLOYEE
    # =========================================================

    employee = models.ForeignKey(
        "employees.Employee",
        on_delete=models.CASCADE,
        related_name="attendance_records",
    )

    # =========================================================
    # DATE / STATUS
    # =========================================================

    date = models.DateField()

    status = models.CharField(
        max_length=20,
        choices=Status.choices,
        default=Status.PRESENT,
    )

    # =========================================================
    # TIME
    # =========================================================

    check_in = models.TimeField(
        null=True,
        blank=True,
    )

    check_out = models.TimeField(
        null=True,
        blank=True,
    )

    # =========================================================
    # BREAK
    # =========================================================

    break_duration = models.PositiveIntegerField(
        default=0,
        help_text="Break duration in minutes.",
    )

    # =========================================================
    # CALCULATED / MANUAL METRICS
    # =========================================================

    work_hours = models.DecimalField(
        max_digits=5,
        decimal_places=2,
        default=Decimal("0.00"),
    )

    overtime_hours = models.DecimalField(
        max_digits=5,
        decimal_places=2,
        default=Decimal("0.00"),
    )

    late_minutes = models.PositiveIntegerField(
        default=0,
    )

    early_leave_minutes = models.PositiveIntegerField(
        default=0,
    )

    # =========================================================
    # REMARKS
    # =========================================================

    remarks = models.TextField(
        blank=True,
        null=True,
    )

    # =========================================================
    # AUDIT
    # =========================================================

    created_at = models.DateTimeField(
        auto_now_add=True,
    )

    updated_at = models.DateTimeField(
        auto_now=True,
    )

    # =========================================================
    # META
    # =========================================================

    class Meta:
        ordering = [
            "-date",
            "-created_at",
        ]

        constraints = [
            models.UniqueConstraint(
                fields=["employee", "date"],
                name="unique_employee_attendance_date",
            )
        ]

    # =========================================================
    # STRING
    # =========================================================

    def __str__(self):
        return (
            f"{self.employee} - "
            f"{self.date} - "
            f"{self.get_status_display()}"
        )

    # =========================================================
    # WORK HOURS
    # =========================================================

    def calculate_work_hours(self):
        if not self.check_in or not self.check_out:
            return Decimal("0.00")

        start = datetime.combine(
            self.date,
            self.check_in,
        )

        end = datetime.combine(
            self.date,
            self.check_out,
        )

        if end < start:
            return Decimal("0.00")

        total_seconds = (
            end - start
        ).total_seconds()

        break_seconds = (
            self.break_duration or 0
        ) * 60

        total_seconds = max(
            0,
            total_seconds - break_seconds,
        )

        hours = Decimal(
            str(total_seconds / 3600)
        )

        return hours.quantize(
            Decimal("0.01"),
            rounding=ROUND_HALF_UP,
        )

    # =========================================================
    # LATE MINUTES
    # =========================================================

    def calculate_late_minutes(self):
        if not self.check_in:
            return 0

        scheduled_start = datetime.combine(
            self.date,
            self.DEFAULT_SHIFT_START,
        )

        actual_start = datetime.combine(
            self.date,
            self.check_in,
        )

        difference = (
            actual_start - scheduled_start
        ).total_seconds()

        grace_seconds = (
            self.DEFAULT_GRACE_MINUTES * 60
        )

        if difference <= grace_seconds:
            return 0

        return int(
            (difference - grace_seconds) // 60
        )

    # =========================================================
    # EARLY LEAVE
    # =========================================================

    def calculate_early_leave_minutes(self):
        if not self.check_out:
            return 0

        scheduled_end = datetime.combine(
            self.date,
            self.DEFAULT_SHIFT_END,
        )

        actual_end = datetime.combine(
            self.date,
            self.check_out,
        )

        difference = (
            scheduled_end - actual_end
        ).total_seconds()

        if difference <= 0:
            return 0

        return int(
            difference // 60
        )

    # =========================================================
    # VALIDATION
    # =========================================================

    def clean(self):

        # -----------------------------------------------------
        # SPECIAL STATUSES CANNOT HAVE CHECK-IN / CHECK-OUT
        # -----------------------------------------------------

        special_statuses = {
            self.Status.ABSENT,
            self.Status.ON_LEAVE,
            self.Status.HOLIDAY,
            self.Status.WEEK_OFF,
        }

        if self.status in special_statuses:

            if self.check_in or self.check_out:
                raise ValidationError(
                    {
                        "status": (
                            "Check-in and check-out are not "
                            "allowed for this attendance status."
                        )
                    }
                )

        # -----------------------------------------------------
        # CHECK-IN / CHECK-OUT
        # -----------------------------------------------------

        if self.check_in and self.check_out:

            start = datetime.combine(
                self.date,
                self.check_in,
            )

            end = datetime.combine(
                self.date,
                self.check_out,
            )

            if end < start:
                raise ValidationError(
                    {
                        "check_out": (
                            "Check-out time cannot be earlier "
                            "than check-in time."
                        )
                    }
                )

        # -----------------------------------------------------
        # BREAK
        # -----------------------------------------------------

        if self.break_duration is not None:
            if self.break_duration < 0:
                raise ValidationError(
                    {
                        "break_duration": (
                            "Break duration cannot be negative."
                        )
                    }
                )

        # -----------------------------------------------------
        # OVERTIME
        # -----------------------------------------------------

        if self.overtime_hours is not None:
            if self.overtime_hours < 0:
                raise ValidationError(
                    {
                        "overtime_hours": (
                            "Overtime cannot be negative."
                        )
                    }
                )

    # =========================================================
    # SAVE
    # =========================================================

    def save(self, *args, **kwargs):

        # -----------------------------------------------------
        # NORMALIZE SPECIAL STATUSES
        # -----------------------------------------------------

        if self.status in {
            self.Status.ABSENT,
            self.Status.ON_LEAVE,
            self.Status.HOLIDAY,
            self.Status.WEEK_OFF,
        }:
            self.check_in = None
            self.check_out = None
            self.break_duration = 0
            self.work_hours = Decimal("0.00")
            self.late_minutes = 0
            self.early_leave_minutes = 0

        else:

            self.work_hours = (
                self.calculate_work_hours()
            )

            self.late_minutes = (
                self.calculate_late_minutes()
            )

            self.early_leave_minutes = (
                self.calculate_early_leave_minutes()
            )

        self.full_clean()

        super().save(*args, **kwargs)

    # =========================================================
    # PROPERTIES
    # =========================================================

    @property
    def is_checked_in(self):
        return bool(
            self.check_in
            and not self.check_out
        )

    @property
    def is_completed(self):
        return bool(
            self.check_in
            and self.check_out
        )

    @property
    def total_break_hours(self):
        return Decimal(
            str(self.break_duration or 0)
        ) / Decimal("60")