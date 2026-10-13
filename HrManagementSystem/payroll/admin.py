from django.contrib import admin

from .models import (
    EmployeeSalary,
    PayrollComponent,
    PayrollPeriod,
    PayrollRecord,
    Payslip,
    SalaryComponent,
    SalaryStructure,
    SalaryStructureComponent,
)


@admin.register(SalaryComponent)
class SalaryComponentAdmin(admin.ModelAdmin):

    list_display = (
        "name",
        "code",
        "component_type",
        "calculation_type",
        "default_amount",
        "is_statutory",
        "is_active",
    )

    list_filter = (
        "component_type",
        "calculation_type",
        "is_statutory",
        "is_active",
    )

    search_fields = (
        "name",
        "code",
    )


class SalaryStructureComponentInline(admin.TabularInline):

    model = SalaryStructureComponent

    extra = 1


@admin.register(SalaryStructure)
class SalaryStructureAdmin(admin.ModelAdmin):

    list_display = (
        "name",
        "code",
        "is_active",
        "created_at",
    )

    list_filter = ("is_active",)

    search_fields = (
        "name",
        "code",
    )

    inlines = [
        SalaryStructureComponentInline
    ]


@admin.register(SalaryStructureComponent)
class SalaryStructureComponentAdmin(admin.ModelAdmin):

    list_display = (
        "structure",
        "component",
        "amount",
        "percentage",
        "calculation_order",
        "is_active",
    )

    list_filter = (
        "is_active",
    )


@admin.register(EmployeeSalary)
class EmployeeSalaryAdmin(admin.ModelAdmin):

    list_display = (
        "employee",
        "salary_structure",
        "annual_ctc",
        "effective_from",
        "effective_to",
        "is_active",
    )

    list_filter = (
        "is_active",
        "salary_structure",
    )

    search_fields = (
        "employee__first_name",
        "employee__last_name",
        "employee__employee_id",
    )

    autocomplete_fields = (
        "employee",
        "salary_structure",
    )


@admin.register(PayrollPeriod)
class PayrollPeriodAdmin(admin.ModelAdmin):

    list_display = (
        "display_name",
        "status",
        "start_date",
        "end_date",
        "processed_at",
    )

    list_filter = (
        "status",
        "year",
        "month",
    )


class PayrollComponentInline(admin.TabularInline):

    model = PayrollComponent

    extra = 0


@admin.register(PayrollRecord)
class PayrollRecordAdmin(admin.ModelAdmin):

    list_display = (
        "employee",
        "period",
        "gross_salary",
        "total_deductions",
        "net_salary",
        "status",
    )

    list_filter = (
        "status",
        "period",
    )

    search_fields = (
        "employee__first_name",
        "employee__last_name",
        "employee__employee_id",
    )

    inlines = [
        PayrollComponentInline
    ]


@admin.register(PayrollComponent)
class PayrollComponentAdmin(admin.ModelAdmin):

    list_display = (
        "payroll_record",
        "component",
        "amount",
    )


@admin.register(Payslip)
class PayslipAdmin(admin.ModelAdmin):

    list_display = (
        "payslip_number",
        "payroll_record",
        "generated_at",
        "is_published",
    )

    list_filter = (
        "is_published",
    )

    search_fields = (
        "payslip_number",
        "payroll_record__employee__first_name",
        "payroll_record__employee__last_name",
    )