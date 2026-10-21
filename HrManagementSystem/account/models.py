from django.db import models, transaction
from django.conf import settings
from django.utils import timezone
from django.contrib.auth.models import AbstractUser
from django.contrib.auth.models import UserManager


class HRMSUserManager(UserManager):
    @transaction.atomic
    def create_superuser(self, username, email=None, password=None, **extra_fields):
        extra_fields.setdefault("is_staff", True)
        extra_fields.setdefault("is_superuser", True)
        extra_fields.setdefault("is_active", True)
        extra_fields["role"] = self.model.Role.SUPER_ADMIN

        user = super().create_superuser(
            username=username,
            email=email,
            password=password,
            **extra_fields,
        )

        # Create the corresponding Employee profile for the Super Admin.
        # Local import avoids circular-import problems between account and employees.
        from employees.models import Employee

        # Employee ID is generated from the User primary key, making it
        # deterministic and unique for normal createsuperuser usage.
        employee_id = f"SA{user.pk:06d}"

        # Protect against an unlikely employee_id collision.
        counter = 1
        while Employee.objects.filter(employee_id=employee_id).exists():
            employee_id = f"SA{user.pk:06d}{counter}"
            counter += 1

        Employee.objects.get_or_create(
            user=user,
            defaults={
                "role": Employee.Role.SUPER_ADMIN,
                "employee_id": employee_id,
                "first_name": user.first_name or "Super",
                "last_name": user.last_name or "Admin",
                "email": user.email or "",
                "phone": user.phone or "",
                "employment_type": Employee.EmploymentType.FULL_TIME,
                "employment_status": Employee.EmploymentStatus.ACTIVE,
                "joining_date": timezone.localdate(),
            },
        )

        return user


class User(AbstractUser):
    class Role(models.TextChoices):
        SUPER_ADMIN = "SUPER_ADMIN", "Super Admin"
        HR_ADMIN = "HR_ADMIN", "HR Admin"
        MANAGER = "MANAGER", "Manager"
        EMPLOYEE = "EMPLOYEE", "Employee"
        RECRUITER = "RECRUITER", "Recruiter"
        PAYROLL_ADMIN = "PAYROLL_ADMIN", "Payroll Admin"

    objects = HRMSUserManager()

    role = models.CharField(
        max_length=30,
        choices=Role.choices,
        default=Role.EMPLOYEE,
    )

    phone = models.CharField(
        max_length=15,
        blank=True,
        null=True,
    )

    profile_picture = models.ImageField(
        upload_to="profile_pictures/",
        blank=True,
        null=True,
    )

    must_change_password = models.BooleanField(
        default=False,
        help_text="If enabled, the user must change their password after logging in.",
    )

    def __str__(self):
        return f"{self.username} - {self.get_role_display()}"


class PasswordResetOTP(models.Model):
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="password_reset_otps",
    )

    otp = models.CharField(
        max_length=6,
    )

    created_at = models.DateTimeField(
        auto_now_add=True,
    )

    expires_at = models.DateTimeField()

    is_verified = models.BooleanField(
        default=False,
    )

    def is_expired(self):
        return timezone.now() > self.expires_at

    def __str__(self):
        return f"{self.user.username} - Password Reset OTP"