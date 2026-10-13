from django.db import models


# =========================================================
# COMPANY
# =========================================================

class Company(models.Model):

    name = models.CharField(
        max_length=200
    )

    legal_name = models.CharField(
        max_length=250,
        blank=True
    )

    email = models.EmailField(
        blank=True
    )

    phone = models.CharField(
        max_length=20,
        blank=True
    )

    website = models.URLField(
        blank=True
    )

    address = models.TextField(
        blank=True
    )

    city = models.CharField(
        max_length=100,
        blank=True
    )

    state = models.CharField(
        max_length=100,
        blank=True
    )

    country = models.CharField(
        max_length=100,
        default="India"
    )

    postal_code = models.CharField(
        max_length=20,
        blank=True
    )

    logo = models.ImageField(
        upload_to="company/",
        blank=True,
        null=True
    )

    established_date = models.DateField(
        blank=True,
        null=True
    )

    is_active = models.BooleanField(
        default=True
    )

    created_at = models.DateTimeField(
        auto_now_add=True
    )

    updated_at = models.DateTimeField(
        auto_now=True
    )

    class Meta:
        ordering = ["name"]

    def __str__(self):
        return self.name


# =========================================================
# DEPARTMENT
# =========================================================

class Department(models.Model):

    company = models.ForeignKey(
        Company,
        on_delete=models.CASCADE,
        related_name="departments"
    )

    name = models.CharField(
        max_length=150
    )

    code = models.CharField(
        max_length=20
    )

    description = models.TextField(
        blank=True
    )

    # -----------------------------------------------------
    # DEPARTMENT HEAD
    # -----------------------------------------------------
    #
    # Employee model already points to Department.
    # Using a string reference avoids circular import issues.
    #
    # This field can be assigned to a Manager / HR Admin
    # through the form/view.
    #

    head = models.ForeignKey(
        "employees.Employee",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="headed_departments"
    )

    is_active = models.BooleanField(
        default=True
    )

    created_at = models.DateTimeField(
        auto_now_add=True
    )

    updated_at = models.DateTimeField(
        auto_now=True
    )

    class Meta:
        ordering = ["name"]

        constraints = [
            models.UniqueConstraint(
                fields=["company", "name"],
                name="unique_department_per_company"
            ),

            models.UniqueConstraint(
                fields=["company", "code"],
                name="unique_department_code_per_company"
            ),
        ]

    def __str__(self):
        return f"{self.name} ({self.code})"


# =========================================================
# DESIGNATION
# =========================================================

class Designation(models.Model):

    company = models.ForeignKey(
        Company,
        on_delete=models.CASCADE,
        related_name="designations"
    )

    name = models.CharField(
        max_length=150
    )

    code = models.CharField(
        max_length=20
    )

    description = models.TextField(
        blank=True
    )

    level = models.PositiveIntegerField(
        default=1
    )

    is_active = models.BooleanField(
        default=True
    )

    created_at = models.DateTimeField(
        auto_now_add=True
    )

    updated_at = models.DateTimeField(
        auto_now=True
    )

    class Meta:
        ordering = ["level", "name"]

        constraints = [
            models.UniqueConstraint(
                fields=["company", "name"],
                name="unique_designation_per_company"
            ),

            models.UniqueConstraint(
                fields=["company", "code"],
                name="unique_designation_code_per_company"
            ),
        ]

    def __str__(self):
        return f"{self.name} ({self.code})"


# =========================================================
# BRANCH
# =========================================================

class Branch(models.Model):

    company = models.ForeignKey(
        Company,
        on_delete=models.CASCADE,
        related_name="branches"
    )

    name = models.CharField(
        max_length=150
    )

    code = models.CharField(
        max_length=20
    )

    address = models.TextField(
        blank=True
    )

    city = models.CharField(
        max_length=100,
        blank=True
    )

    state = models.CharField(
        max_length=100,
        blank=True
    )

    country = models.CharField(
        max_length=100,
        default="India"
    )

    postal_code = models.CharField(
        max_length=20,
        blank=True
    )

    phone = models.CharField(
        max_length=20,
        blank=True
    )

    email = models.EmailField(
        blank=True
    )

    is_head_office = models.BooleanField(
        default=False
    )

    is_active = models.BooleanField(
        default=True
    )

    created_at = models.DateTimeField(
        auto_now_add=True
    )

    updated_at = models.DateTimeField(
        auto_now=True
    )

    class Meta:
        ordering = ["name"]

        constraints = [
            models.UniqueConstraint(
                fields=["company", "name"],
                name="unique_branch_per_company"
            ),

            models.UniqueConstraint(
                fields=["company", "code"],
                name="unique_branch_code_per_company"
            ),
        ]

    def __str__(self):
        return f"{self.name} ({self.code})"


# =========================================================
# WORK LOCATION
# =========================================================

class WorkLocation(models.Model):

    class LocationType(models.TextChoices):

        OFFICE = "OFFICE", "Office"

        REMOTE = "REMOTE", "Remote"

        HYBRID = "HYBRID", "Hybrid"

        CLIENT = "CLIENT", "Client Site"

    company = models.ForeignKey(
        Company,
        on_delete=models.CASCADE,
        related_name="work_locations"
    )

    name = models.CharField(
        max_length=150
    )

    address = models.TextField(
        blank=True
    )

    city = models.CharField(
        max_length=100,
        blank=True
    )

    state = models.CharField(
        max_length=100,
        blank=True
    )

    country = models.CharField(
        max_length=100,
        default="India"
    )

    postal_code = models.CharField(
        max_length=20,
        blank=True
    )

    location_type = models.CharField(
        max_length=20,
        choices=LocationType.choices,
        default=LocationType.OFFICE
    )

    is_active = models.BooleanField(
        default=True
    )

    created_at = models.DateTimeField(
        auto_now_add=True
    )

    updated_at = models.DateTimeField(
        auto_now=True
    )

    class Meta:
        ordering = ["name"]

    def __str__(self):
        return self.name