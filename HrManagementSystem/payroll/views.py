from decimal import Decimal, ROUND_HALF_UP
from datetime import date
import calendar

from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.db import transaction
from django.db.models import Q, Sum, Count
from django.http import HttpResponseForbidden
from django.shortcuts import get_object_or_404, redirect, render
from django.utils import timezone

from employees.models import Employee

from .forms import (
    EmployeeSalaryForm,
    PayrollPeriodForm,
    SalaryComponentForm,
)
from .models import (
    EmployeeSalary,
    PayrollComponent,
    PayrollPeriod,
    PayrollRecord,
    Payslip,
    SalaryComponent,
)


# ============================================================
# ROLE HELPERS
# ============================================================

def get_current_employee(request):
    """
    Return the currently logged-in Employee profile.
    """

    try:
        employee = request.user.employee_profile
    except Employee.DoesNotExist:
        return None

    if employee.employment_status in [
        Employee.EmploymentStatus.ACTIVE,
        Employee.EmploymentStatus.BENCH,
        Employee.EmploymentStatus.ON_LEAVE,
    ]:
        return employee

    return None


def is_super_admin(request):
    employee = get_current_employee(request)

    return (
        employee is not None
        and employee.role == Employee.Role.SUPER_ADMIN
    )


def is_hr_admin(request):
    employee = get_current_employee(request)

    return (
        employee is not None
        and employee.role == Employee.Role.HR_ADMIN
    )


def is_hr_or_super_admin(request):
    return (
        is_hr_admin(request)
        or is_super_admin(request)
    )


def is_manager(request):
    employee = get_current_employee(request)

    return (
        employee is not None
        and employee.role == Employee.Role.MANAGER
    )


def is_employee(request):
    employee = get_current_employee(request)

    return (
        employee is not None
        and employee.role == Employee.Role.EMPLOYEE
    )


# ============================================================
# ACCESS HELPERS
# ============================================================

def get_accessible_employees(request):
    """
    Payroll employee visibility.

    Super Admin:
        All employees.

    HR Admin:
        Employees from same company + branch.

    Manager:
        Only own employee profile.

    Employee:
        Only own employee profile.
    """

    current_employee = get_current_employee(request)

    if not current_employee:
        return Employee.objects.none()

    base_queryset = Employee.objects.filter(
        employment_status__in=[
            Employee.EmploymentStatus.ACTIVE,
            Employee.EmploymentStatus.BENCH,
            Employee.EmploymentStatus.ON_LEAVE,
        ]
    ).select_related(
        "company",
        "branch",
        "department",
        "designation",
        "reporting_manager",
    )

    if current_employee.role == Employee.Role.SUPER_ADMIN:
        return base_queryset

    if current_employee.role == Employee.Role.HR_ADMIN:
        return base_queryset.filter(
            company=current_employee.company,
            branch=current_employee.branch,
        )

    return base_queryset.filter(
        pk=current_employee.pk
    )


def get_accessible_salary_queryset(request):
    """
    Return salary records visible to current user.
    """

    employees = get_accessible_employees(request)

    return EmployeeSalary.objects.filter(
        employee__in=employees
    ).select_related(
        "employee",
        "employee__company",
        "employee__branch",
        "employee__department",
        "employee__designation",
        "salary_structure",
    )


def get_accessible_payroll_queryset(request):
    """
    Return payroll records visible to current user.
    """

    employees = get_accessible_employees(request)

    return PayrollRecord.objects.filter(
        employee__in=employees
    ).select_related(
        "employee",
        "period",
        "employee_salary",
        "employee__company",
        "employee__branch",
    ).prefetch_related(
        "components__component",
        "payslip",
    )


def require_payroll_access(request):
    """
    Payroll requires an active employee profile.
    """

    employee = get_current_employee(request)

    if not employee:
        return None

    if employee.role not in [
        Employee.Role.SUPER_ADMIN,
        Employee.Role.HR_ADMIN,
        Employee.Role.MANAGER,
        Employee.Role.EMPLOYEE,
    ]:
        return None

    return employee


def require_payroll_management(request):
    """
    Only HR Admin and Super Admin can manage payroll.
    """

    employee = get_current_employee(request)

    if not employee:
        return None

    if employee.role not in [
        Employee.Role.SUPER_ADMIN,
        Employee.Role.HR_ADMIN,
    ]:
        return None

    return employee


# ============================================================
# DASHBOARD
# ============================================================

@login_required
def payroll_dashboard(request):

    current_employee = require_payroll_access(request)

    if not current_employee:
        return HttpResponseForbidden(
            "You do not have permission to access Payroll."
        )

    accessible_employees = get_accessible_employees(request)

    salary_queryset = get_accessible_salary_queryset(request)

    payroll_queryset = get_accessible_payroll_queryset(request)

    current_month = timezone.now().month
    current_year = timezone.now().year

    current_period = PayrollPeriod.objects.filter(
        month=current_month,
        year=current_year,
    ).first()

    current_payroll = payroll_queryset.filter(
        period=current_period
    ) if current_period else PayrollRecord.objects.none()

    context = {
        "current_employee": current_employee,
        "total_employees": accessible_employees.count(),
        "total_salary_records": salary_queryset.count(),
        "current_period": current_period,
        "current_payroll_count": current_payroll.count(),
        "current_payroll_total": current_payroll.aggregate(
            total=Sum("net_salary")
        )["total"] or Decimal("0.00"),
        "recent_periods": PayrollPeriod.objects.all()[:6],
        "recent_payslips": payroll_queryset.filter(
            payslip__isnull=False
        ).order_by(
            "-period__year",
            "-period__month",
        )[:5],
    }

    return render(
        request,
        "payroll/payroll_dashboard.html",
        context,
    )


# ============================================================
# SALARY COMPONENTS
# ============================================================

@login_required
def component_list(request):

    if not require_payroll_management(request):
        return HttpResponseForbidden(
            "Only HR Admin or Super Admin can manage salary components."
        )

    components = SalaryComponent.objects.all()

    search = request.GET.get("search", "").strip()

    if search:
        components = components.filter(
            Q(name__icontains=search)
            | Q(code__icontains=search)
        )

    component_type = request.GET.get("type")

    if component_type:
        components = components.filter(
            component_type=component_type
        )

    context = {
        "components": components,
        "search": search,
        "selected_type": component_type,
        "component_types": SalaryComponent.ComponentType.choices,
    }

    return render(
        request,
        "payroll/component_list.html",
        context,
    )


@login_required
def component_create(request):

    if not require_payroll_management(request):
        return HttpResponseForbidden(
            "Only HR Admin or Super Admin can create salary components."
        )

    if request.method == "POST":

        form = SalaryComponentForm(request.POST)

        if form.is_valid():

            component = form.save()

            messages.success(
                request,
                f"Salary component '{component.name}' created successfully."
            )

            return redirect("payroll:component_list")

    else:
        form = SalaryComponentForm()

    return render(
        request,
        "payroll/component_form.html",
        {
            "form": form,
            "title": "Add Salary Component",
            "button_text": "Create Component",
        },
    )


@login_required
def component_update(request, pk):

    if not require_payroll_management(request):
        return HttpResponseForbidden(
            "Only HR Admin or Super Admin can update salary components."
        )

    component = get_object_or_404(
        SalaryComponent,
        pk=pk,
    )

    if request.method == "POST":

        form = SalaryComponentForm(
            request.POST,
            instance=component,
        )

        if form.is_valid():

            form.save()

            messages.success(
                request,
                "Salary component updated successfully."
            )

            return redirect("payroll:component_list")

    else:
        form = SalaryComponentForm(
            instance=component
        )

    return render(
        request,
        "payroll/component_form.html",
        {
            "form": form,
            "component": component,
            "title": "Edit Salary Component",
            "button_text": "Update Component",
        },
    )


@login_required
def component_delete(request, pk):

    if not require_payroll_management(request):
        return HttpResponseForbidden(
            "Only HR Admin or Super Admin can delete salary components."
        )

    component = get_object_or_404(
        SalaryComponent,
        pk=pk,
    )

    if request.method == "POST":

        try:
            component.delete()

            messages.success(
                request,
                "Salary component deleted successfully."
            )

        except Exception:
            messages.error(
                request,
                "This salary component cannot be deleted because it is already used."
            )

        return redirect("payroll:component_list")

    return render(
        request,
        "payroll/component_confirm_delete.html",
        {
            "component": component,
        },
    )


# ============================================================
# EMPLOYEE SALARY
# ============================================================

@login_required
def salary_list(request):

    current_employee = require_payroll_access(request)

    if not current_employee:
        return HttpResponseForbidden(
            "You do not have permission to view salaries."
        )

    salaries = get_accessible_salary_queryset(request)

    search = request.GET.get("search", "").strip()

    if search:
        salaries = salaries.filter(
            Q(employee__first_name__icontains=search)
            | Q(employee__last_name__icontains=search)
            | Q(employee__employee_id__icontains=search)
        )

    active_filter = request.GET.get("active")

    if active_filter == "active":
        salaries = salaries.filter(
            is_active=True
        )

    elif active_filter == "inactive":
        salaries = salaries.filter(
            is_active=False
        )

    context = {
        "salaries": salaries,
        "search": search,
        "active_filter": active_filter,
        "current_employee": current_employee,
    }

    return render(
        request,
        "payroll/salary_list.html",
        context,
    )


@login_required
def salary_create(request):

    current_employee = require_payroll_management(request)

    if not current_employee:
        return HttpResponseForbidden(
            "Only HR Admin or Super Admin can create salary records."
        )

    if request.method == "POST":

        form = EmployeeSalaryForm(
            request.POST,
            request_user=request.user,
        )

        if form.is_valid():

            employee = form.cleaned_data["employee"]

            accessible_employees = get_accessible_employees(request)

            if not accessible_employees.filter(
                pk=employee.pk
            ).exists():

                return HttpResponseForbidden(
                    "You cannot assign salary to this employee."
                )

            salary = form.save(
                commit=False
            )

            salary.created_by = request.user

            salary.save()

            messages.success(
                request,
                f"Salary assigned successfully to {employee.get_full_name()}."
            )

            return redirect(
                "payroll:salary_detail",
                pk=salary.pk,
            )

    else:

        form = EmployeeSalaryForm(
            request_user=request.user,
        )

        form.fields["employee"].queryset = (
            get_accessible_employees(request)
        )

    return render(
        request,
        "payroll/salary_form.html",
        {
            "form": form,
            "title": "Assign Employee Salary",
            "button_text": "Save Salary",
        },
    )


@login_required
def salary_detail(request, pk):

    current_employee = require_payroll_access(request)

    if not current_employee:
        return HttpResponseForbidden(
            "You do not have permission to view this salary."
        )

    salary = get_object_or_404(
        get_accessible_salary_queryset(request),
        pk=pk,
    )

    structure_components = (
        salary.salary_structure
        .structure_components
        .filter(is_active=True)
        .select_related("component")
    )

    return render(
        request,
        "payroll/salary_detail.html",
        {
            "salary": salary,
            "structure_components": structure_components,
            "current_employee": current_employee,
        },
    )


@login_required
def salary_update(request, pk):

    current_employee = require_payroll_management(request)

    if not current_employee:
        return HttpResponseForbidden(
            "Only HR Admin or Super Admin can update salaries."
        )

    salary = get_object_or_404(
        get_accessible_salary_queryset(request),
        pk=pk,
    )

    if request.method == "POST":

        form = EmployeeSalaryForm(
            request.POST,
            instance=salary,
            request_user=request.user,
        )

        form.fields["employee"].queryset = (
            get_accessible_employees(request)
        )

        if form.is_valid():

            updated_salary = form.save(
                commit=False
            )

            updated_salary.created_by = (
                salary.created_by
                or request.user
            )

            updated_salary.save()

            messages.success(
                request,
                "Employee salary updated successfully."
            )

            return redirect(
                "payroll:salary_detail",
                pk=salary.pk,
            )

    else:

        form = EmployeeSalaryForm(
            instance=salary,
            request_user=request.user,
        )

        form.fields["employee"].queryset = (
            get_accessible_employees(request)
        )

    return render(
        request,
        "payroll/salary_form.html",
        {
            "form": form,
            "salary": salary,
            "title": "Edit Employee Salary",
            "button_text": "Update Salary",
        },
    )


# ============================================================
# PAYROLL PERIOD
# ============================================================

@login_required
def period_list(request):

    current_employee = require_payroll_access(request)

    if not current_employee:
        return HttpResponseForbidden(
            "You do not have permission to view payroll periods."
        )

    periods = PayrollPeriod.objects.all()

    context = {
        "periods": periods,
        "current_employee": current_employee,
    }

    return render(
        request,
        "payroll/period_list.html",
        context,
    )


@login_required
def period_create(request):

    if not require_payroll_management(request):
        return HttpResponseForbidden(
            "Only HR Admin or Super Admin can create payroll periods."
        )

    if request.method == "POST":

        form = PayrollPeriodForm(request.POST)

        if form.is_valid():

            period = form.save()

            messages.success(
                request,
                f"Payroll period {period.display_name} created successfully."
            )

            return redirect(
                "payroll:period_detail",
                pk=period.pk,
            )

    else:

        today = timezone.localdate()

        first_day = today.replace(day=1)

        last_day = today.replace(
            day=calendar.monthrange(
                today.year,
                today.month,
            )[1]
        )

        form = PayrollPeriodForm(
            initial={
                "month": today.month,
                "year": today.year,
                "start_date": first_day,
                "end_date": last_day,
            }
        )

    return render(
        request,
        "payroll/period_form.html",
        {
            "form": form,
            "title": "Create Payroll Period",
            "button_text": "Create Period",
        },
    )


@login_required
def period_detail(request, pk):

    current_employee = require_payroll_access(request)

    if not current_employee:
        return HttpResponseForbidden(
            "You do not have permission to view payroll."
        )

    period = get_object_or_404(
        PayrollPeriod,
        pk=pk,
    )

    records = get_accessible_payroll_queryset(
        request
    ).filter(
        period=period
    )

    summary = records.aggregate(
        total_gross=Sum("gross_salary"),
        total_deductions=Sum("total_deductions"),
        total_net=Sum("net_salary"),
        total_lop=Sum("lop_amount"),
        total_overtime=Sum("overtime_amount"),
    )

    context = {
        "period": period,
        "records": records,
        "summary": summary,
        "current_employee": current_employee,
    }

    return render(
        request,
        "payroll/period_detail.html",
        context,
    )


# ============================================================
# PAYROLL CALCULATION HELPERS
# ============================================================

MONEY_PLACES = Decimal("0.01")


def money(value):
    """
    Convert a value to currency precision.
    """

    if value is None:
        value = Decimal("0.00")

    return Decimal(value).quantize(
        MONEY_PLACES,
        rounding=ROUND_HALF_UP,
    )


def get_days_in_period(period):
    return (
        period.end_date - period.start_date
    ).days + 1


def calculate_component_amount(
    structure_component,
    monthly_ctc,
    basic_amount,
):
    """
    Calculate individual salary component.

    FIXED:
        Uses configured amount.

    PERCENTAGE:
        Calculates percentage against the selected base.

    If percentage_of is not configured,
    monthly CTC is used.
    """

    component = structure_component.component

    if component.calculation_type == (
        SalaryComponent.CalculationType.FIXED
    ):
        return money(
            structure_component.amount
        )

    percentage = (
        structure_component.percentage
        or Decimal("0.00")
    )

    base_amount = monthly_ctc

    if component.percentage_of:

        if component.percentage_of.code == "BASIC":
            base_amount = basic_amount

    return money(
        base_amount
        * percentage
        / Decimal("100")
    )


def get_attendance_data(employee, period):
    """
    Read attendance information.

    The attendance application is treated as an optional
    source here so Payroll remains usable even before
    attendance records exist for a new employee.
    """

    try:

        from attendance.models import Attendance

    except ImportError:

        return {
            "working_days": Decimal(
                get_days_in_period(period)
            ),
            "present_days": Decimal("0.00"),
            "leave_days": Decimal("0.00"),
            "lop_days": Decimal("0.00"),
            "payable_days": Decimal("0.00"),
            "overtime_hours": Decimal("0.00"),
        }

    attendance_qs = Attendance.objects.filter(
        employee=employee,
        date__range=[
            period.start_date,
            period.end_date,
        ],
    )

    working_days = Decimal(
        get_days_in_period(period)
    )

    present_days = Decimal("0.00")
    leave_days = Decimal("0.00")
    lop_days = Decimal("0.00")
    overtime_hours = Decimal("0.00")

    for attendance in attendance_qs:

        status = str(
            getattr(
                attendance,
                "status",
                ""
            )
        ).upper()

        if status.endswith("PRESENT"):
            present_days += Decimal("1.00")

        elif status.endswith("HALF_DAY"):
            present_days += Decimal("0.50")

        elif status.endswith("ON_LEAVE"):
            leave_days += Decimal("1.00")

        elif status.endswith("ABSENT"):
            lop_days += Decimal("1.00")

        overtime = getattr(
            attendance,
            "overtime",
            None,
        )

        if overtime is None:
            overtime = getattr(
                attendance,
                "overtime_hours",
                Decimal("0.00"),
            )

        try:
            overtime_hours += Decimal(
                str(overtime or 0)
            )
        except Exception:
            pass

    payable_days = (
        present_days
        + leave_days
    )

    return {
        "working_days": working_days,
        "present_days": present_days,
        "leave_days": leave_days,
        "lop_days": lop_days,
        "payable_days": payable_days,
        "overtime_hours": overtime_hours,
    }


def calculate_payroll_record(
    employee_salary,
    period,
):
    """
    Calculate one employee's payroll.

    Salary structure:
        Earnings
        Deductions
        Employer Contributions

    Payroll:
        Gross
        LOP
        Overtime
        Deductions
        Net
    """

    employee = employee_salary.employee

    attendance = get_attendance_data(
        employee,
        period,
    )

    monthly_ctc = money(
        employee_salary.annual_ctc
        / Decimal("12")
    )

    structure_components = (
        employee_salary.salary_structure
        .structure_components
        .filter(
            is_active=True
        )
        .select_related("component")
        .order_by(
            "calculation_order",
            "id",
        )
    )

    component_values = []

    basic_amount = Decimal("0.00")

    # --------------------------------------------------------
    # First calculate BASIC
    # --------------------------------------------------------

    for structure_component in structure_components:

        component = structure_component.component

        if component.code.upper() == "BASIC":

            basic_amount = calculate_component_amount(
                structure_component,
                monthly_ctc,
                monthly_ctc,
            )

            break

    # --------------------------------------------------------
    # Calculate components
    # --------------------------------------------------------

    total_earnings = Decimal("0.00")
    total_deductions = Decimal("0.00")
    employer_contribution = Decimal("0.00")

    for structure_component in structure_components:

        component = structure_component.component

        amount = calculate_component_amount(
            structure_component,
            monthly_ctc,
            basic_amount,
        )

        component_values.append(
            {
                "component": component,
                "amount": amount,
                "calculated_from": monthly_ctc,
                "percentage": structure_component.percentage,
            }
        )

        if component.component_type == (
            SalaryComponent.ComponentType.EARNING
        ):
            total_earnings += amount

        elif component.component_type == (
            SalaryComponent.ComponentType.DEDUCTION
        ):
            total_deductions += amount

        elif component.component_type == (
            SalaryComponent.ComponentType.EMPLOYER_CONTRIBUTION
        ):
            employer_contribution += amount

    total_earnings = money(total_earnings)

    total_deductions = money(total_deductions)

    employer_contribution = money(
        employer_contribution
    )

    # --------------------------------------------------------
    # Gross salary
    # --------------------------------------------------------

    gross_salary = total_earnings

    # --------------------------------------------------------
    # LOP calculation
    # --------------------------------------------------------

    working_days = (
        attendance["working_days"]
        or Decimal("1.00")
    )

    lop_days = attendance["lop_days"]

    daily_salary = (
        gross_salary
        / working_days
    )

    lop_amount = money(
        daily_salary
        * lop_days
    )

    # --------------------------------------------------------
    # Overtime
    # --------------------------------------------------------

    overtime_hours = attendance[
        "overtime_hours"
    ]

    overtime_amount = Decimal("0.00")

    if overtime_hours > 0:

        hourly_rate = (
            daily_salary
            / Decimal("8")
        )

        overtime_amount = money(
            hourly_rate
            * overtime_hours
        )

    # --------------------------------------------------------
    # Net salary
    # --------------------------------------------------------

    net_salary = money(
        gross_salary
        + overtime_amount
        - total_deductions
        - lop_amount
    )

    if net_salary < Decimal("0.00"):
        net_salary = Decimal("0.00")

    return {
        "working_days": attendance[
            "working_days"
        ],

        "present_days": attendance[
            "present_days"
        ],

        "leave_days": attendance[
            "leave_days"
        ],

        "lop_days": lop_days,

        "payable_days": attendance[
            "payable_days"
        ],

        "overtime_hours": overtime_hours,

        "gross_salary": money(
            gross_salary
        ),

        "total_earnings": total_earnings,

        "total_deductions": total_deductions,

        "employer_contribution": employer_contribution,

        "lop_amount": lop_amount,

        "overtime_amount": overtime_amount,

        "net_salary": net_salary,

        "components": component_values,
    }


# ============================================================
# PROCESS PAYROLL
# ============================================================

@login_required
@transaction.atomic
def process_payroll(request, pk):

    current_employee = require_payroll_management(request)

    if not current_employee:
        return HttpResponseForbidden(
            "Only HR Admin or Super Admin can process payroll."
        )

    period = get_object_or_404(
        PayrollPeriod,
        pk=pk,
    )

    if period.status in [
        PayrollPeriod.Status.PAID,
        PayrollPeriod.Status.CANCELLED,
    ]:

        messages.error(
            request,
            "This payroll period cannot be processed."
        )

        return redirect(
            "payroll:period_detail",
            pk=period.pk,
        )

    if request.method != "POST":

        accessible_employees = (
            get_accessible_employees(request)
            .filter(
                employment_status__in=[
                    Employee.EmploymentStatus.ACTIVE,
                    Employee.EmploymentStatus.BENCH,
                    Employee.EmploymentStatus.ON_LEAVE,
                ]
            )
        )

        salary_records = (
            EmployeeSalary.objects.filter(
                employee__in=accessible_employees,
                is_active=True,
                effective_from__lte=period.end_date,
            )
            .filter(
                Q(effective_to__isnull=True)
                | Q(effective_to__gte=period.start_date)
            )
            .select_related(
                "employee",
                "salary_structure",
            )
        )

        context = {
            "period": period,
            "salary_records": salary_records,
            "employee_count": salary_records.count(),
        }

        return render(
            request,
            "payroll/payroll_process.html",
            context,
        )

    # --------------------------------------------------------
    # Process
    # --------------------------------------------------------

    period.status = PayrollPeriod.Status.PROCESSING
    period.save(
        update_fields=[
            "status",
            "updated_at",
        ]
    )

    accessible_employees = (
        get_accessible_employees(request)
    )

    salary_records = (
        EmployeeSalary.objects.filter(
            employee__in=accessible_employees,
            is_active=True,
            effective_from__lte=period.end_date,
        )
        .filter(
            Q(effective_to__isnull=True)
            | Q(effective_to__gte=period.start_date)
        )
        .select_related(
            "employee",
            "salary_structure",
        )
    )

    processed_count = 0

    for employee_salary in salary_records:

        calculation = calculate_payroll_record(
            employee_salary,
            period,
        )

        payroll_record, created = (
            PayrollRecord.objects.update_or_create(
                period=period,
                employee=employee_salary.employee,
                defaults={
                    "employee_salary": employee_salary,
                    "working_days": calculation[
                        "working_days"
                    ],
                    "payable_days": calculation[
                        "payable_days"
                    ],
                    "present_days": calculation[
                        "present_days"
                    ],
                    "leave_days": calculation[
                        "leave_days"
                    ],
                    "lop_days": calculation[
                        "lop_days"
                    ],
                    "overtime_hours": calculation[
                        "overtime_hours"
                    ],
                    "gross_salary": calculation[
                        "gross_salary"
                    ],
                    "total_earnings": calculation[
                        "total_earnings"
                    ],
                    "total_deductions": calculation[
                        "total_deductions"
                    ],
                    "employer_contribution": calculation[
                        "employer_contribution"
                    ],
                    "lop_amount": calculation[
                        "lop_amount"
                    ],
                    "overtime_amount": calculation[
                        "overtime_amount"
                    ],
                    "net_salary": calculation[
                        "net_salary"
                    ],
                    "status": PayrollRecord.Status.PROCESSED,
                },
            )
        )

        # Remove old component values when recalculating.
        payroll_record.components.all().delete()

        PayrollComponent.objects.bulk_create(
            [
                PayrollComponent(
                    payroll_record=payroll_record,
                    component=item["component"],
                    amount=item["amount"],
                    calculated_from=item[
                        "calculated_from"
                    ],
                    percentage=item[
                        "percentage"
                    ],
                )
                for item in calculation["components"]
            ]
        )

        # ----------------------------------------------------
        # Payslip
        # ----------------------------------------------------

        payslip_number = (
            f"PS-{period.year}"
            f"{period.month:02d}-"
            f"{employee_salary.employee.employee_id}"
        )

        Payslip.objects.update_or_create(
            payroll_record=payroll_record,
            defaults={
                "payslip_number": payslip_number,
                "generated_by": request.user,
            },
        )

        processed_count += 1

    period.status = PayrollPeriod.Status.PROCESSED

    period.processed_at = timezone.now()

    period.processed_by = request.user

    period.save(
        update_fields=[
            "status",
            "processed_at",
            "processed_by",
            "updated_at",
        ]
    )

    messages.success(
        request,
        f"Payroll processed successfully for "
        f"{processed_count} employees."
    )

    return redirect(
        "payroll:period_detail",
        pk=period.pk,
    )


# ============================================================
# MARK PAYROLL AS PAID
# ============================================================

@login_required
@transaction.atomic
def mark_payroll_paid(request, pk):

    current_employee = require_payroll_management(request)

    if not current_employee:
        return HttpResponseForbidden(
            "Only HR Admin or Super Admin can mark payroll as paid."
        )

    period = get_object_or_404(
        PayrollPeriod,
        pk=pk,
    )

    if request.method != "POST":

        return redirect(
            "payroll:period_detail",
            pk=period.pk,
        )

    if period.status != PayrollPeriod.Status.PROCESSED:

        messages.error(
            request,
            "Only processed payroll can be marked as paid."
        )

        return redirect(
            "payroll:period_detail",
            pk=period.pk,
        )

    payroll_records = get_accessible_payroll_queryset(
        request
    ).filter(
        period=period
    )

    payment_date = timezone.localdate()

    payroll_records.update(
        status=PayrollRecord.Status.PAID,
        payment_date=payment_date,
    )

    period.status = PayrollPeriod.Status.PAID

    period.save(
        update_fields=[
            "status",
            "updated_at",
        ]
    )

    messages.success(
        request,
        f"Payroll for {period.display_name} marked as paid."
    )

    return redirect(
        "payroll:period_detail",
        pk=period.pk,
    )


# ============================================================
# PAYSLIPS
# ============================================================

@login_required
def payslip_list(request):

    current_employee = require_payroll_access(request)

    if not current_employee:
        return HttpResponseForbidden(
            "You do not have permission to view payslips."
        )

    payroll_records = (
        get_accessible_payroll_queryset(request)
        .filter(
            payslip__isnull=False
        )
        .order_by(
            "-period__year",
            "-period__month",
            "employee__first_name",
        )
    )

    search = request.GET.get(
        "search",
        ""
    ).strip()

    if search:

        payroll_records = payroll_records.filter(
            Q(
                employee__first_name__icontains=search
            )
            | Q(
                employee__last_name__icontains=search
            )
            | Q(
                employee__employee_id__icontains=search
            )
            | Q(
                payslip__payslip_number__icontains=search
            )
        )

    context = {
        "payroll_records": payroll_records,
        "search": search,
        "current_employee": current_employee,
    }

    return render(
        request,
        "payroll/payslip_list.html",
        context,
    )


@login_required
def payslip_detail(request, pk):

    current_employee = require_payroll_access(request)

    if not current_employee:
        return HttpResponseForbidden(
            "You do not have permission to view this payslip."
        )

    payroll_record = get_object_or_404(
        get_accessible_payroll_queryset(request),
        pk=pk,
    )

    payslip = get_object_or_404(
        Payslip.objects.select_related(
            "payroll_record",
            "payroll_record__employee",
            "payroll_record__period",
        ),
        payroll_record=payroll_record,
    )

    components = (
        payroll_record.components
        .select_related("component")
        .order_by(
            "component__component_type",
            "component__name",
        )
    )

    earnings = components.filter(
        component__component_type=(
            SalaryComponent.ComponentType.EARNING
        )
    )

    deductions = components.filter(
        component__component_type=(
            SalaryComponent.ComponentType.DEDUCTION
        )
    )

    employer_contributions = components.filter(
        component__component_type=(
            SalaryComponent.ComponentType.EMPLOYER_CONTRIBUTION
        )
    )

    context = {
        "payslip": payslip,
        "payroll_record": payroll_record,
        "earnings": earnings,
        "deductions": deductions,
        "employer_contributions": employer_contributions,
        "current_employee": current_employee,
    }

    return render(
        request,
        "payroll/payslip_detail.html",
        context,
    )


@login_required
def payslip_print(request, pk):

    current_employee = require_payroll_access(request)

    if not current_employee:
        return HttpResponseForbidden(
            "You do not have permission to view this payslip."
        )

    payroll_record = get_object_or_404(
        get_accessible_payroll_queryset(request),
        pk=pk,
    )

    payslip = get_object_or_404(
        Payslip.objects.select_related(
            "payroll_record",
            "payroll_record__employee",
            "payroll_record__employee__company",
            "payroll_record__employee__branch",
            "payroll_record__employee__department",
            "payroll_record__employee__designation",
            "payroll_record__period",
        ),
        payroll_record=payroll_record,
    )

    components = (
        payroll_record.components
        .select_related("component")
        .order_by(
            "component__component_type",
            "component__name",
        )
    )

    earnings = components.filter(
        component__component_type=(
            SalaryComponent.ComponentType.EARNING
        )
    )

    deductions = components.filter(
        component__component_type=(
            SalaryComponent.ComponentType.DEDUCTION
        )
    )

    employer_contributions = components.filter(
        component__component_type=(
            SalaryComponent.ComponentType.EMPLOYER_CONTRIBUTION
        )
    )

    context = {
        "payslip": payslip,
        "payroll_record": payroll_record,
        "earnings": earnings,
        "deductions": deductions,
        "employer_contributions": employer_contributions,
    }

    return render(
        request,
        "payroll/payslip_print.html",
        context,
    )