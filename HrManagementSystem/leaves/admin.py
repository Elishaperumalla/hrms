from django.contrib import admin

from .models import (
    LeaveApproval,
    LeaveBalance,
    LeaveRequest,
    LeaveType,
)






@admin.register(LeaveType)
class LeaveTypeAdmin(admin.ModelAdmin):

    list_display = (
        "name",
        "code",
        "days_per_year",
        "is_paid",
        "requires_approval",
        "is_active",
    )

    list_filter = (
        "is_paid",
        "requires_approval",
        "is_active",
    )

    search_fields = (
        "name",
        "code",
    )


@admin.register(LeaveBalance)
class LeaveBalanceAdmin(admin.ModelAdmin):

    list_display = (
        "employee",
        "leave_type",
        "year",
        "allocated_days",
        "carried_forward_days",
        "used_days",
    )

    list_filter = (
        "year",
        "leave_type",
    )

    search_fields = (
        "employee__employee_id",
        "employee__first_name",
        "employee__last_name",
    )


@admin.register(LeaveRequest)
class LeaveRequestAdmin(admin.ModelAdmin):

    list_display = (
        "employee",
        "leave_type",
        "start_date",
        "end_date",
        "total_days",
        "status",
        "approval_stage",
        "balance_deducted",
    )

    list_filter = (
        "status",
        "approval_stage",
        "leave_type",
        "duration_type",
    )

    search_fields = (
        "employee__employee_id",
        "employee__first_name",
        "employee__last_name",
    )

    readonly_fields = (
        "applied_at",
        "approved_at",
        "created_at",
        "updated_at",
        "balance_deducted",
    )


@admin.register(LeaveApproval)
class LeaveApprovalAdmin(admin.ModelAdmin):

    list_display = (
        "leave_request",
        "stage",
        "action",
        "acted_by",
        "created_at",
    )

    list_filter = (
        "stage",
        "action",
    )

    search_fields = (
        "leave_request__employee__employee_id",
        "leave_request__employee__first_name",
        "leave_request__employee__last_name",
        "acted_by__username",
    )

    readonly_fields = (
        "leave_request",
        "stage",
        "action",
        "acted_by",
        "reason",
        "created_at",
    )