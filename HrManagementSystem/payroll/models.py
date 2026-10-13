from decimal import Decimal

from django.conf import settings
from django.core.validators import MinValueValidator
from django.db import models
from django.utils import timezone

from employees.models import Employee


class SalaryComponent(models.Model):

    class ComponentType(models.TextChoices):
        EARNING = "EARNING", "Earning"
        DEDUCTION = "DEDUCTION", "Deduction"
        EMPLOYER_CONTRIBUTION = (
            "EMPLOYER_CONTRIBUTION",
            "Employer Contribution",
        )

    class CalculationType(models.TextChoices):
        FIXED = "FIXED", "Fixed Amount"
        PERCENTAGE = "PERCENTAGE", "Percentage"

    name = models.CharField(max_length=100)

    code = models.CharField(
        max_length=50,
        unique=True,
    )

    component_type = models.CharField(
        max_length=30,
        choices=ComponentType.choices,
    )

    calculation_type = models.CharField(
        max_length=20,
        choices=CalculationType.choices,
        default=CalculationType.FIXED,
    )

    percentage_of = models.ForeignKey(
        "self",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="percentage_components",
    )

    default_amount = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        default=Decimal("0.00"),
        validators=[MinValueValidator(Decimal("0.00"))],
    )

    is_statutory = models.BooleanField(default=False)

    is_active = models.BooleanField(default=True)

    description = models.TextField(
        blank=True,
        null=True,
    )

    created_at = models.DateTimeField(auto_now_add=True)

    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["component_type", "name"]

    def __str__(self):
        return f"{self.name} ({self.code})"


class SalaryStructure(models.Model):

    name = models.CharField(max_length=150)

    code = models.CharField(
        max_length=50,
        unique=True,
    )

    description = models.TextField(
        blank=True,
        null=True,
    )

    components = models.ManyToManyField(
        SalaryComponent,
        through="SalaryStructureComponent",
        related_name="salary_structures",
        blank=True,
    )

    is_active = models.BooleanField(default=True)

    created_at = models.DateTimeField(auto_now_add=True)

    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["name"]

    def __str__(self):
        return f"{self.name} ({self.code})"


class SalaryStructureComponent(models.Model):

    structure = models.ForeignKey(
        SalaryStructure,
        on_delete=models.CASCADE,
        related_name="structure_components",
    )

    component = models.ForeignKey(
        SalaryComponent,
        on_delete=models.PROTECT,
        related_name="structure_assignments",
    )

    amount = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        default=Decimal("0.00"),
        validators=[MinValueValidator(Decimal("0.00"))],
    )

    percentage = models.DecimalField(
        max_digits=7,
        decimal_places=2,
        null=True,
        blank=True,
        validators=[MinValueValidator(Decimal("0.00"))],
    )

    calculation_order = models.PositiveIntegerField(default=1)

    is_active = models.BooleanField(default=True)

    class Meta:
        ordering = ["calculation_order", "id"]

        constraints = [
            models.UniqueConstraint(
                fields=["structure", "component"],
                name="unique_structure_component",
            )
        ]

    def __str__(self):
        return f"{self.structure.name} - {self.component.name}"


class EmployeeSalary(models.Model):

    employee = models.ForeignKey(
        Employee,
        on_delete=models.CASCADE,
        related_name="salary_records",
    )

    salary_structure = models.ForeignKey(
        SalaryStructure,
        on_delete=models.PROTECT,
        related_name="employee_salaries",
    )

    annual_ctc = models.DecimalField(
        max_digits=14,
        decimal_places=2,
        validators=[MinValueValidator(Decimal("0.00"))],
    )

    effective_from = models.DateField()

    effective_to = models.DateField(
        null=True,
        blank=True,
    )

    is_active = models.BooleanField(default=True)

    notes = models.TextField(
        blank=True,
        null=True,
    )

    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="created_employee_salaries",
    )

    created_at = models.DateTimeField(auto_now_add=True)

    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["-effective_from", "-id"]

    def __str__(self):
        return (
            f"{self.employee.get_full_name()} - "
            f"₹{self.annual_ctc:,.2f}"
        )

    @property
    def monthly_ctc(self):
        return self.annual_ctc / Decimal("12")

    def save(self, *args, **kwargs):
        if self.is_active:
            EmployeeSalary.objects.filter(
                employee=self.employee,
                is_active=True,
            ).exclude(pk=self.pk).update(
                is_active=False,
                effective_to=self.effective_from,
            )

        super().save(*args, **kwargs)


class PayrollPeriod(models.Model):

    class Status(models.TextChoices):
        DRAFT = "DRAFT", "Draft"
        PROCESSING = "PROCESSING", "Processing"
        PROCESSED = "PROCESSED", "Processed"
        PAID = "PAID", "Paid"
        CANCELLED = "CANCELLED", "Cancelled"

    month = models.PositiveSmallIntegerField()

    year = models.PositiveIntegerField()

    start_date = models.DateField()

    end_date = models.DateField()

    status = models.CharField(
        max_length=20,
        choices=Status.choices,
        default=Status.DRAFT,
    )

    processed_at = models.DateTimeField(
        null=True,
        blank=True,
    )

    processed_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="processed_payroll_periods",
    )

    notes = models.TextField(
        blank=True,
        null=True,
    )

    created_at = models.DateTimeField(auto_now_add=True)

    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["-year", "-month"]

        constraints = [
            models.UniqueConstraint(
                fields=["month", "year"],
                name="unique_payroll_period",
            )
        ]

    def __str__(self):
        return f"{self.month:02d}/{self.year}"

    @property
    def display_name(self):
        return self.start_date.strftime("%B %Y")


class PayrollRecord(models.Model):

    class Status(models.TextChoices):
        DRAFT = "DRAFT", "Draft"
        PROCESSED = "PROCESSED", "Processed"
        PAID = "PAID", "Paid"
        HOLD = "HOLD", "On Hold"

    period = models.ForeignKey(
        PayrollPeriod,
        on_delete=models.CASCADE,
        related_name="payroll_records",
    )

    employee = models.ForeignKey(
        Employee,
        on_delete=models.PROTECT,
        related_name="payroll_records",
    )

    employee_salary = models.ForeignKey(
        EmployeeSalary,
        on_delete=models.PROTECT,
        related_name="payroll_records",
    )

    working_days = models.DecimalField(
        max_digits=6,
        decimal_places=2,
        default=Decimal("0.00"),
    )

    payable_days = models.DecimalField(
        max_digits=6,
        decimal_places=2,
        default=Decimal("0.00"),
    )

    present_days = models.DecimalField(
        max_digits=6,
        decimal_places=2,
        default=Decimal("0.00"),
    )

    leave_days = models.DecimalField(
        max_digits=6,
        decimal_places=2,
        default=Decimal("0.00"),
    )

    lop_days = models.DecimalField(
        max_digits=6,
        decimal_places=2,
        default=Decimal("0.00"),
    )

    overtime_hours = models.DecimalField(
        max_digits=8,
        decimal_places=2,
        default=Decimal("0.00"),
    )

    gross_salary = models.DecimalField(
        max_digits=14,
        decimal_places=2,
        default=Decimal("0.00"),
    )

    total_earnings = models.DecimalField(
        max_digits=14,
        decimal_places=2,
        default=Decimal("0.00"),
    )

    total_deductions = models.DecimalField(
        max_digits=14,
        decimal_places=2,
        default=Decimal("0.00"),
    )

    employer_contribution = models.DecimalField(
        max_digits=14,
        decimal_places=2,
        default=Decimal("0.00"),
    )

    lop_amount = models.DecimalField(
        max_digits=14,
        decimal_places=2,
        default=Decimal("0.00"),
    )

    overtime_amount = models.DecimalField(
        max_digits=14,
        decimal_places=2,
        default=Decimal("0.00"),
    )

    net_salary = models.DecimalField(
        max_digits=14,
        decimal_places=2,
        default=Decimal("0.00"),
    )

    status = models.CharField(
        max_length=20,
        choices=Status.choices,
        default=Status.DRAFT,
    )

    payment_date = models.DateField(
        null=True,
        blank=True,
    )

    payment_reference = models.CharField(
        max_length=100,
        blank=True,
        null=True,
    )

    remarks = models.TextField(
        blank=True,
        null=True,
    )

    created_at = models.DateTimeField(auto_now_add=True)

    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["employee__first_name", "employee__last_name"]

        constraints = [
            models.UniqueConstraint(
                fields=["period", "employee"],
                name="unique_employee_payroll_period",
            )
        ]

    def __str__(self):
        return (
            f"{self.employee.get_full_name()} - "
            f"{self.period.display_name}"
        )


class PayrollComponent(models.Model):

    payroll_record = models.ForeignKey(
        PayrollRecord,
        on_delete=models.CASCADE,
        related_name="components",
    )

    component = models.ForeignKey(
        SalaryComponent,
        on_delete=models.PROTECT,
        related_name="payroll_components",
    )

    amount = models.DecimalField(
        max_digits=14,
        decimal_places=2,
        default=Decimal("0.00"),
    )

    calculated_from = models.DecimalField(
        max_digits=14,
        decimal_places=2,
        null=True,
        blank=True,
    )

    percentage = models.DecimalField(
        max_digits=7,
        decimal_places=2,
        null=True,
        blank=True,
    )

    remarks = models.CharField(
        max_length=255,
        blank=True,
        null=True,
    )

    class Meta:
        ordering = ["component__component_type", "component__name"]

    def __str__(self):
        return (
            f"{self.payroll_record.employee.get_full_name()} - "
            f"{self.component.name}"
        )


class Payslip(models.Model):

    payroll_record = models.OneToOneField(
        PayrollRecord,
        on_delete=models.CASCADE,
        related_name="payslip",
    )

    payslip_number = models.CharField(
        max_length=100,
        unique=True,
    )

    generated_at = models.DateTimeField(
        default=timezone.now,
    )

    generated_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="generated_payslips",
    )

    is_published = models.BooleanField(default=False)

    published_at = models.DateTimeField(
        null=True,
        blank=True,
    )

    notes = models.TextField(
        blank=True,
        null=True,
    )

    class Meta:
        ordering = ["-generated_at"]

    def __str__(self):
        return self.payslip_number