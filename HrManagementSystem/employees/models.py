from django.conf import settings
from django.db import models


class Employee(models.Model):

    class Role(models.TextChoices):
        EMPLOYEE = "EMPLOYEE", "Employee"
        MANAGER = "MANAGER", "Manager"
        HR_ADMIN = "HR_ADMIN", "HR Admin"
        SUPER_ADMIN = "SUPER_ADMIN", "Super Admin"

    class Gender(models.TextChoices):
        MALE = "MALE", "Male"
        FEMALE = "FEMALE", "Female"
        OTHER = "OTHER", "Other"

    class EmploymentType(models.TextChoices):
        FULL_TIME = "FULL_TIME", "Full Time"
        PART_TIME = "PART_TIME", "Part Time"
        CONTRACT = "CONTRACT", "Contract"
        INTERN = "INTERN", "Intern"

    class EmploymentStatus(models.TextChoices):
        ACTIVE = "ACTIVE", "Active"
        BENCH = "BENCH", "Bench"
        ON_LEAVE = "ON_LEAVE", "On Leave"
        RESIGNED = "RESIGNED", "Resigned"
        TERMINATED = "TERMINATED", "Terminated"
        RETIRED = "RETIRED", "Retired"

    class WorkArrangement(models.TextChoices):
        ONSITE = "ONSITE", "Onsite"
        REMOTE = "REMOTE", "Remote"
        HYBRID = "HYBRID", "Hybrid"
        CLIENT_SITE = "CLIENT_SITE", "Client Site"

    # ============================================================
    # USER ACCOUNT
    # ============================================================

    user = models.OneToOneField(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="employee_profile",
    )

    role = models.CharField(
        max_length=20,
        choices=Role.choices,
        default=Role.EMPLOYEE,
    )

    work_arrangement = models.CharField(
        max_length=20,
        choices=WorkArrangement.choices,
        default=WorkArrangement.ONSITE,
    )

    # ============================================================
    # EMPLOYEE ID
    # ============================================================

    employee_id = models.CharField(
        max_length=20,
        unique=True,
    )

    # ============================================================
    # PERSONAL INFORMATION
    # ============================================================

    first_name = models.CharField(
        max_length=100,
    )

    middle_name = models.CharField(
        max_length=100,
        blank=True,
    )

    last_name = models.CharField(
        max_length=100,
    )

    date_of_birth = models.DateField(
        null=True,
        blank=True,
    )

    gender = models.CharField(
        max_length=20,
        choices=Gender.choices,
        blank=True,
    )

    # ============================================================
    # CONTACT INFORMATION
    # ============================================================

    email = models.EmailField(
        blank=True,
    )

    phone = models.CharField(
        max_length=20,
        blank=True,
    )

    alternate_phone = models.CharField(
        max_length=20,
        blank=True,
    )

    # ============================================================
    # ADDRESS
    # ============================================================

    address = models.TextField(
        blank=True,
    )

    city = models.CharField(
        max_length=100,
        blank=True,
    )

    state = models.CharField(
        max_length=100,
        blank=True,
    )

    country = models.CharField(
        max_length=100,
        default="India",
    )

    postal_code = models.CharField(
        max_length=20,
        blank=True,
    )

    # ============================================================
    # ORGANIZATION
    # ============================================================

    company = models.ForeignKey(
        "organization.Company",
        on_delete=models.PROTECT,
        related_name="employees",
        null=True,
        blank=True
    )

    department = models.ForeignKey(
        "organization.Department",
        on_delete=models.PROTECT,
        related_name="employees",
        null=True,
        blank=True,
    )

    designation = models.ForeignKey(
        "organization.Designation",
        on_delete=models.PROTECT,
        related_name="employees",
        null=True,
        blank=True,
    )

    branch = models.ForeignKey(
        "organization.Branch",
        on_delete=models.PROTECT,
        related_name="employees",
        null=True,
        blank=True,
    )

    work_location = models.ForeignKey(
        "organization.WorkLocation",
        on_delete=models.PROTECT,
        related_name="employees",
        null=True,
        blank=True,
    )

    # ============================================================
    # EMPLOYMENT INFORMATION
    # ============================================================

    employment_type = models.CharField(
        max_length=20,
        choices=EmploymentType.choices,
        default=EmploymentType.FULL_TIME,
    )

    employment_status = models.CharField(
        max_length=20,
        choices=EmploymentStatus.choices,
        default=EmploymentStatus.ACTIVE,
    )

    joining_date = models.DateField()

    confirmation_date = models.DateField(
        null=True,
        blank=True,
    )

    resignation_date = models.DateField(
        null=True,
        blank=True,
    )

    termination_date = models.DateField(
        null=True,
        blank=True,
    )

    # ============================================================
    # REPORTING MANAGER
    # ============================================================

    reporting_manager = models.ForeignKey(
        "self",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="team_members",
    )

    # ============================================================
    # PROFILE
    # ============================================================

    profile_photo = models.ImageField(
        upload_to="employees/profile/",
        blank=True,
        null=True,
    )

    # ============================================================
    # SYSTEM
    # ============================================================

    created_at = models.DateTimeField(
        auto_now_add=True,
    )

    updated_at = models.DateTimeField(
        auto_now=True,
    )

    class Meta:
        ordering = ["first_name", "last_name"]

    def __str__(self):
        return f"{self.employee_id} - {self.get_full_name()}"

    def get_full_name(self):
        return " ".join(
            filter(
                None,
                [
                    self.first_name,
                    self.middle_name,
                    self.last_name,
                ],
            )
        )


class EmployeeDocument(models.Model):

    class DocumentType(models.TextChoices):
        AADHAAR = "AADHAAR", "Aadhaar Card"
        PAN = "PAN", "PAN Card"
        PASSPORT = "PASSPORT", "Passport"
        DRIVING_LICENSE = "DRIVING_LICENSE", "Driving License"
        EDUCATION = "EDUCATION", "Education Certificate"
        EXPERIENCE = "EXPERIENCE", "Experience Certificate"
        OFFER_LETTER = "OFFER_LETTER", "Offer Letter"
        APPOINTMENT_LETTER = "APPOINTMENT_LETTER", "Appointment Letter"
        RELIEVING_LETTER = "RELIEVING_LETTER", "Relieving Letter"
        OTHER = "OTHER", "Other"

    employee = models.ForeignKey(
        Employee,
        on_delete=models.CASCADE,
        related_name="documents",
    )

    document_type = models.CharField(
        max_length=30,
        choices=DocumentType.choices,
    )

    title = models.CharField(
        max_length=200,
    )

    description = models.TextField(
        blank=True,
    )

    document = models.FileField(
        upload_to="employees/documents/",
    )

    issue_date = models.DateField(
        null=True,
        blank=True,
    )

    expiry_date = models.DateField(
        null=True,
        blank=True,
    )

    created_at = models.DateTimeField(
        auto_now_add=True,
    )

    updated_at = models.DateTimeField(
        auto_now=True,
    )

    class Meta:
        ordering = ["-created_at"]

    def __str__(self):
        return f"{self.employee.employee_id} - {self.title}"


class EmployeeAsset(models.Model):

    class AssetType(models.TextChoices):
        LAPTOP = "LAPTOP", "Laptop"
        DESKTOP = "DESKTOP", "Desktop"
        MOBILE = "MOBILE", "Mobile"
        TABLET = "TABLET", "Tablet"
        MONITOR = "MONITOR", "Monitor"
        KEYBOARD = "KEYBOARD", "Keyboard"
        MOUSE = "MOUSE", "Mouse"
        HEADSET = "HEADSET", "Headset"
        ACCESS_CARD = "ACCESS_CARD", "Access Card"
        OTHER = "OTHER", "Other"

    class AssetStatus(models.TextChoices):
        ASSIGNED = "ASSIGNED", "Assigned"
        RETURNED = "RETURNED", "Returned"
        DAMAGED = "DAMAGED", "Damaged"
        LOST = "LOST", "Lost"

    employee = models.ForeignKey(
        Employee,
        on_delete=models.CASCADE,
        related_name="assets",
    )

    asset_type = models.CharField(
        max_length=30,
        choices=AssetType.choices,
    )

    asset_name = models.CharField(
        max_length=200,
    )

    asset_code = models.CharField(
        max_length=100,
        unique=True,
    )

    serial_number = models.CharField(
        max_length=150,
        blank=True,
    )

    assigned_date = models.DateField()

    return_date = models.DateField(
        null=True,
        blank=True,
    )

    status = models.CharField(
        max_length=20,
        choices=AssetStatus.choices,
        default=AssetStatus.ASSIGNED,
    )

    notes = models.TextField(
        blank=True,
    )

    created_at = models.DateTimeField(
        auto_now_add=True,
    )

    updated_at = models.DateTimeField(
        auto_now=True,
    )

    class Meta:
        ordering = ["-created_at"]

    def __str__(self):
        return f"{self.asset_code} - {self.asset_name}"