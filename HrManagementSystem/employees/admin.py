from django.contrib import admin

from .models import Employee


@admin.register(Employee)
class EmployeeAdmin(admin.ModelAdmin):

    search_fields = (
        "employee_id",
        "first_name",
        "middle_name",
        "last_name",
        "email",
        "phone",
    )

    list_display = (
        "employee_id",
        "first_name",
        "last_name",
        "role",
        "employment_status",
        "company",
        "department",
        "employment_type",
    )

    list_filter = (
        "role",
        "employment_status",
        "employment_type",
        "company",
        "department",
    )