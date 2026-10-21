import logging

from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.db import transaction
from django.db.models import Q
from django.shortcuts import get_object_or_404, redirect, render
from django.utils import timezone

from account.models import User
from account.views import create_hrms_user

from .forms import EmployeeForm, EmployeeDocumentForm, EmployeeAssetForm
from .models import Employee, EmployeeDocument, EmployeeAsset


logger = logging.getLogger(__name__)


# =========================================================
# ROLE HELPERS
# =========================================================

def is_hr_admin(employee):
    return bool(
        employee
        and employee.role == Employee.Role.HR_ADMIN
    )


def is_super_admin(employee):
    return bool(
        employee
        and employee.role == Employee.Role.SUPER_ADMIN
    )


def is_hr_or_super_admin(employee):
    return bool(
        employee
        and employee.role in [
            Employee.Role.HR_ADMIN,
            Employee.Role.SUPER_ADMIN,
        ]
    )


# =========================================================
# ORGANIZATION SCOPE HELPERS
# =========================================================

def is_same_company_branch(current_employee, employee):
    """Return True when both employees belong to the same company and branch."""

    if not current_employee or not employee:
        return False

    return (
        current_employee.company_id == employee.company_id
        and current_employee.branch_id == employee.branch_id
    )


def get_hr_branch_queryset(queryset, current_employee):
    """Restrict an employee queryset to the HR Admin's company and branch."""

    return queryset.filter(
        company_id=current_employee.company_id,
        branch_id=current_employee.branch_id,
    )


# =========================================================
# CURRENT EMPLOYEE
# =========================================================

def get_current_employee(request):
    """
    Return the Employee profile linked to the logged-in user.

    ACTIVE, ON_LEAVE and BENCH employees can access the system.
    TERMINATED, RESIGNED and RETIRED employees cannot.
    """

    if not request.user.is_authenticated:
        return None

    return (
        Employee.objects
        .select_related(
            "company",
            "department",
            "designation",
            "branch",
            "work_location",
            "reporting_manager",
            "user",
        )
        .filter(
            user=request.user,
            employment_status__in=[
                Employee.EmploymentStatus.ACTIVE,
                Employee.EmploymentStatus.ON_LEAVE,
                Employee.EmploymentStatus.BENCH,
            ],
        )
        .first()
    )


# =========================================================
# HR / SUPER ADMIN PERMISSION
# =========================================================

def require_hr(request):
    """
    Allow HR Admin and Super Admin for HR management actions.
    """

    employee = get_current_employee(request)

    if not employee:
        messages.error(
            request,
            "Your Employee profile was not found.",
        )
        return None

    if not is_hr_or_super_admin(employee):
        messages.error(
            request,
            "Only HR Admin or Super Admin can perform this action.",
        )
        return None

    return employee


# =========================================================
# HR / SUPER ADMIN EMPLOYEE ACCESS
# =========================================================

def get_hr_accessible_employee(
    current_employee,
    pk,
):
    """
    Super Admin can manage employees globally.

    HR Admin can manage employees only inside
    their own company and branch.
    """

    if not is_hr_or_super_admin(current_employee):
        return None

    queryset = (
        Employee.objects
        .select_related(
            "company",
            "department",
            "designation",
            "branch",
            "work_location",
            "reporting_manager",
            "user",
        )
    )

    # Super Admin → global access
    if is_super_admin(current_employee):
        return get_object_or_404(
            queryset,
            pk=pk,
        )

    # HR → company + branch scoped access
    return get_object_or_404(
        queryset,
        pk=pk,
        company_id=current_employee.company_id,
        branch_id=current_employee.branch_id,
    )


# =========================================================
# FORM PREPARATION
# =========================================================

def prepare_employee_form(
    form,
    current_employee,
    employee=None,
):
    """
    Configure EmployeeForm according to the current authority.

    CREATION:

        Super Admin:
            HR Admin only

        HR Admin:
            Employee + Manager

    EDIT:

        Super Admin:
            HR Admin + Manager + Employee

        HR Admin:
            Employee + Manager

    Reporting manager:

        HR Admin → Super Admin
        Manager  → HR Admin
        Employee → Manager

    Employee manager dropdown is restricted to:
        same company
        same department
        active/on-leave managers
    """

    role_field = form.fields.get("role")
    manager_field = form.fields.get("reporting_manager")
    branch_field = form.fields.get("branch")

    # =====================================================
    # HR → CURRENT BRANCH ONLY
    # =====================================================
    #
    # HR Admins are branch-scoped. Keep the form itself aligned
    # with the same security rule used by the backend.
    # =====================================================

    if branch_field and is_hr_admin(current_employee):
        branch_field.queryset = branch_field.queryset.filter(
            pk=current_employee.branch_id,
        )
        branch_field.initial = current_employee.branch_id

    # =====================================================
    # ROLE CHOICES
    # =====================================================

    if role_field:

        # -------------------------------------------------
        # SUPER ADMIN
        # -------------------------------------------------

        if is_super_admin(current_employee):

            # =================================================
            # CREATE
            # =================================================
            #
            # Super Admin is allowed to CREATE
            # HR Admin accounts only.
            #
            # Manager and Employee creation belongs
            # to HR Admin.
            #
            if employee is None:

                role_field.choices = [
                    (
                        Employee.Role.HR_ADMIN,
                        "HR Admin",
                    ),
                ]

            # =================================================
            # EDIT
            # =================================================
            #
            # Super Admin can still EDIT existing
            # HR / Manager / Employee records.
            #
            else:

                role_field.choices = [
                    (
                        Employee.Role.HR_ADMIN,
                        "HR Admin",
                    ),
                    (
                        Employee.Role.MANAGER,
                        "Manager",
                    ),
                    (
                        Employee.Role.EMPLOYEE,
                        "Employee",
                    ),
                ]

        # -------------------------------------------------
        # HR ADMIN
        # -------------------------------------------------

        else:

            role_field.choices = [
                (
                    Employee.Role.EMPLOYEE,
                    "Employee",
                ),
                (
                    Employee.Role.MANAGER,
                    "Manager",
                ),
            ]

    # =====================================================
    # REPORTING MANAGER QUERYSET
    # =====================================================

    if manager_field:

        selected_role = None

        # -------------------------------------------------
        # POST
        # -------------------------------------------------

        if form.is_bound:

            selected_role = form.data.get("role")

        # -------------------------------------------------
        # EDIT
        # -------------------------------------------------

        elif employee is not None:

            selected_role = employee.role

        # -------------------------------------------------
        # NEW FORM DEFAULT
        # -------------------------------------------------

        else:

            selected_role = Employee.Role.HR_ADMIN

        # =================================================
        # HR ADMIN → SUPER ADMIN
        # =================================================

        if selected_role == Employee.Role.HR_ADMIN:

            manager_qs = Employee.objects.filter(
                role=Employee.Role.SUPER_ADMIN,
                employment_status__in=[
                    Employee.EmploymentStatus.ACTIVE,
                    Employee.EmploymentStatus.ON_LEAVE,
                ],
            )

        # =================================================
        # MANAGER → HR ADMIN
        # =================================================

        elif selected_role == Employee.Role.MANAGER:

            manager_qs = Employee.objects.filter(
                role=Employee.Role.HR_ADMIN,
                employment_status__in=[
                    Employee.EmploymentStatus.ACTIVE,
                    Employee.EmploymentStatus.ON_LEAVE,
                ],
            )

        # =================================================
        # EMPLOYEE → MANAGER
        # =================================================

        else:

            manager_qs = Employee.objects.filter(
                role=Employee.Role.MANAGER,
                employment_status__in=[
                    Employee.EmploymentStatus.ACTIVE,
                    Employee.EmploymentStatus.ON_LEAVE,
                ],
            )

        manager_qs = (
            manager_qs
            .select_related(
                "company",
                "department",
                "designation",
                "user",
            )
            .order_by(
                "first_name",
                "last_name",
            )
        )

        # =================================================
        # HR → SAME COMPANY
        # =================================================

        if is_hr_admin(current_employee):

            manager_qs = manager_qs.filter(
                company_id=current_employee.company_id,
                branch_id=current_employee.branch_id,
            )

        # =================================================
        # DETERMINE DEPARTMENT
        # =================================================

        department_id = None

        if employee is not None:

            department_id = employee.department_id

        if form.is_bound:

            raw_department = form.data.get(
                "department"
            )

            if raw_department:

                try:
                    department_id = int(
                        raw_department
                    )

                except (
                    TypeError,
                    ValueError,
                ):
                    department_id = None

        # =================================================
        # EMPLOYEE → SAME DEPARTMENT MANAGERS
        # =================================================

        if (
            selected_role == Employee.Role.EMPLOYEE
            and department_id
        ):

            manager_qs = manager_qs.filter(
                department_id=department_id,
            )

        # =================================================
        # PREVENT SELF SELECTION
        # =================================================

        if employee is not None:

            manager_qs = manager_qs.exclude(
                pk=employee.pk,
            )

        manager_field.queryset = manager_qs


# =========================================================
# EMPLOYEE FORM RENDER HELPER
# =========================================================

def render_employee_form(
    request,
    form,
    current_employee,
    title,
    button_text,
    employee=None,
):

    return render(
        request,
        "employees/employee_form.html",
        {
            "form": form,
            "employee": employee,
            "title": title,
            "button_text": button_text,
            "current_employee": current_employee,
        },
    )


# =========================================================
# REPORTING HIERARCHY VALIDATION
# =========================================================

def validate_reporting_hierarchy(
    employee,
    current_employee,
    form,
    creating=False,
):
    """
    Enforce:

        Super Admin
             ↓
        HR Admin
             ↓
         Manager
             ↓
         Employee
    """

    role = employee.role

    # =====================================================
    # SUPER ADMIN
    # =====================================================

    if is_super_admin(current_employee):

        # -------------------------------------------------
        # SUPER ADMIN CREATION RESTRICTION
        # -------------------------------------------------
        #
        # Super Admin can CREATE ONLY HR Admin.
        #
        if creating and role != Employee.Role.HR_ADMIN:

            form.add_error(
                "role",
                (
                    "Super Admin can create HR Admin "
                    "accounts only."
                ),
            )

            return False

        # -------------------------------------------------
        # HR REPORTS TO SUPER ADMIN
        # -------------------------------------------------

        if role == Employee.Role.HR_ADMIN:

            employee.reporting_manager = current_employee

            return True

    # =====================================================
    # HR ADMIN
    # =====================================================

    elif is_hr_admin(current_employee):

        if role not in [
            Employee.Role.EMPLOYEE,
            Employee.Role.MANAGER,
        ]:

            form.add_error(
                "role",
                (
                    "HR Admin can create Employees "
                    "and Managers only."
                ),
            )

            return False

    # =====================================================
    # HR ADMIN ROLE
    # =====================================================

    if role == Employee.Role.HR_ADMIN:

        manager = employee.reporting_manager

        if not manager:

            form.add_error(
                "reporting_manager",
                "HR Admin must report to a Super Admin.",
            )

            return False

        if manager.role != Employee.Role.SUPER_ADMIN:

            form.add_error(
                "reporting_manager",
                "HR Admin must report to a Super Admin.",
            )

            return False

        return True

    # =====================================================
    # MANAGER ROLE
    # =====================================================

    if role == Employee.Role.MANAGER:

        # -------------------------------------------------
        # HR-created Manager automatically reports to HR
        # -------------------------------------------------

        if is_hr_admin(current_employee):

            employee.reporting_manager = current_employee

            # HR and Manager must belong to same company.
            if (
                employee.company_id
                != current_employee.company_id
            ):

                form.add_error(
                    "company",
                    "Manager must belong to the HR's company.",
                )

                return False

            if (
                employee.branch_id
                != current_employee.branch_id
            ):

                form.add_error(
                    "branch",
                    "Manager must belong to the HR's branch.",
                )

                return False

            return True

        # -------------------------------------------------
        # Super Admin editing an existing Manager
        # -------------------------------------------------
        #
        # Super Admin is not allowed to CREATE a Manager,
        # but can manage/edit existing Manager records.
        #
        # If the existing Manager already has a valid
        # HR reporting manager, preserve that hierarchy.
        # -------------------------------------------------

        manager = employee.reporting_manager

        if not manager:

            form.add_error(
                "reporting_manager",
                "Manager must report to an HR Admin.",
            )

            return False

        if manager.role != Employee.Role.HR_ADMIN:

            form.add_error(
                "reporting_manager",
                "Manager must report to an HR Admin.",
            )

            return False

        if (
            manager.company_id
            != employee.company_id
        ):

            form.add_error(
                "reporting_manager",
                (
                    "Reporting HR Admin must belong "
                    "to the same company."
                ),
            )

            return False

        if (
            manager.branch_id
            != employee.branch_id
        ):

            form.add_error(
                "reporting_manager",
                (
                    "Reporting HR Admin must belong "
                    "to the same branch."
                ),
            )

            return False

        return True

    # =====================================================
    # EMPLOYEE ROLE
    # =====================================================

    if role == Employee.Role.EMPLOYEE:

        manager = employee.reporting_manager

        if not manager:

            form.add_error(
                "reporting_manager",
                "Employee must have a reporting manager.",
            )

            return False

        if manager.role != Employee.Role.MANAGER:

            form.add_error(
                "reporting_manager",
                "Employee must report to a Manager.",
            )

            return False

        if (
            manager.company_id
            != employee.company_id
        ):

            form.add_error(
                "reporting_manager",
                (
                    "Reporting manager must belong "
                    "to the same company."
                ),
            )

            return False

        if (
            manager.branch_id
            != employee.branch_id
        ):

            form.add_error(
                "reporting_manager",
                (
                    "Employee and Manager must belong "
                    "to the same branch."
                ),
            )

            return False

        if (
            manager.department_id
            != employee.department_id
        ):

            form.add_error(
                "reporting_manager",
                (
                    "Employee and Manager must belong "
                    "to the same department."
                ),
            )

            return False

        return True

    # =====================================================
    # SUPER ADMIN ROLE
    # =====================================================

    if role == Employee.Role.SUPER_ADMIN:

        form.add_error(
            "role",
            (
                "Super Admin accounts are not created "
                "from the Employee workflow."
            ),
        )

        return False

    form.add_error(
        "role",
        "Invalid employee role.",
    )

    return False


# =========================================================
# USER ROLE MAPPING
# =========================================================

def get_user_role_for_employee(employee):

    mapping = {
        Employee.Role.EMPLOYEE:
            User.Role.EMPLOYEE,

        Employee.Role.MANAGER:
            User.Role.MANAGER,

        Employee.Role.HR_ADMIN:
            User.Role.HR_ADMIN,

        Employee.Role.SUPER_ADMIN:
            User.Role.SUPER_ADMIN,
    }

    return mapping.get(
        employee.role
    )


# =========================================================
# EMPLOYEE LIST
# =========================================================

@login_required
def employee_list(request):

    current_employee = get_current_employee(
        request
    )

    if not current_employee:

        messages.error(
            request,
            "Your Employee profile was not found.",
        )

        return redirect("dashboard")

    employees = (
        Employee.objects
        .select_related(
            "company",
            "department",
            "designation",
            "branch",
            "work_location",
            "reporting_manager",
        )
    )

    # =====================================================
    # SUPER ADMIN
    # =====================================================

    if is_super_admin(current_employee):

        employees = employees.all()

    # =====================================================
    # HR ADMIN
    # =====================================================

    elif is_hr_admin(current_employee):

        employees = get_hr_branch_queryset(
            employees,
            current_employee,
        )

    # =====================================================
    # MANAGER
    # =====================================================

    elif (
        current_employee.role
        == Employee.Role.MANAGER
    ):

        employees = employees.filter(
            company_id=current_employee.company_id,
            branch_id=current_employee.branch_id,
        ).filter(
            Q(
                pk=current_employee.pk
            )
            |
            Q(
                reporting_manager=current_employee
            )
        )

    # =====================================================
    # EMPLOYEE
    # =====================================================

    else:

        employees = employees.filter(
            pk=current_employee.pk,
        )

    employees = employees.order_by(
        "first_name",
        "last_name",
    )

    return render(
        request,
        "employees/employee_list.html",
        {
            "employees": employees,
            "current_employee": current_employee,
            "can_manage_employees":
                is_hr_or_super_admin(
                    current_employee
                ),
        },
    )


# =========================================================
# EMPLOYEE DETAIL
# =========================================================

@login_required
def employee_detail(request, pk):

    current_employee = get_current_employee(
        request
    )

    if not current_employee:

        messages.error(
            request,
            "Your Employee profile was not found.",
        )

        return redirect("dashboard")

    employee = get_object_or_404(
        Employee.objects.select_related(
            "company",
            "department",
            "designation",
            "branch",
            "work_location",
            "reporting_manager",
        ),
        pk=pk,
    )

    # =====================================================
    # ACCESS CONTROL
    # =====================================================

    if is_super_admin(current_employee):

        has_access = True

    elif is_hr_admin(current_employee):

        has_access = is_same_company_branch(
            current_employee,
            employee,
        )

    elif (
        current_employee.role
        == Employee.Role.MANAGER
    ):

        has_access = (
            is_same_company_branch(
                current_employee,
                employee,
            )
            and (
                employee.pk
                == current_employee.pk
                or
                employee.reporting_manager_id
                == current_employee.pk
            )
        )

    else:

        has_access = (
            employee.pk
            == current_employee.pk
        )

    if not has_access:

        messages.error(
            request,
            "You are not authorized to view this employee.",
        )

        return redirect(
            "employee_list"
        )

    return render(
        request,
        "employees/employee_detail.html",
        {
            "employee": employee,
            "documents":
                employee.documents.all(),
            "assets":
                employee.assets.all(),
            "current_employee":
                current_employee,
            "can_manage_employee":
                is_hr_or_super_admin(
                    current_employee
                )
                and (
                    is_super_admin(
                        current_employee
                    )
                    or
                    is_same_company_branch(
                        current_employee,
                        employee,
                    )
                ),
        },
    )


# =========================================================
# CREATE EMPLOYEE / MANAGER / HR ADMIN
# =========================================================

@login_required
def employee_create(request):

    current_employee = require_hr(
        request
    )

    if not current_employee:

        return redirect(
            "dashboard"
        )

    if request.method == "POST":

        form = EmployeeForm(
            request.POST,
            request.FILES,
            request_user=request.user,
        )

        prepare_employee_form(
            form,
            current_employee,
        )

        if form.is_valid():

            try:

                with transaction.atomic():

                    employee = form.save(
                        commit=False
                    )

                    # =================================================
                    # COMPANY SECURITY
                    # =================================================

                    if is_hr_admin(
                        current_employee
                    ):

                        employee.company = (
                            current_employee.company
                        )
                        employee.branch = (
                            current_employee.branch
                        )

                    elif is_super_admin(
                        current_employee
                    ):

                        if not employee.company_id:

                            raise ValueError(
                                "Company is required."
                            )

                    # =================================================
                    # DEFAULT STATUS
                    # =================================================

                    employee.employment_status = (
                        Employee.EmploymentStatus.ACTIVE
                    )

                    # =================================================
                    # REPORTING HIERARCHY
                    # =================================================

                    if not validate_reporting_hierarchy(
                        employee,
                        current_employee,
                        form,
                        creating=True,
                    ):

                        raise ValueError(
                            "Please correct the reporting hierarchy."
                        )

                    # =================================================
                    # EMAIL REQUIRED
                    # =================================================

                    if not employee.email:

                        raise ValueError(
                            (
                                "Email address is required "
                                "to create the login account."
                            )
                        )

                    # =================================================
                    # USER ROLE
                    # =================================================

                    user_role = (
                        get_user_role_for_employee(
                            employee
                        )
                    )

                    if not user_role:

                        raise ValueError(
                            "Invalid role for account creation."
                        )

                    # =================================================
                    # CREATE USER
                    # =================================================

                    user = create_hrms_user(
                        email=employee.email,
                        first_name=employee.first_name,
                        last_name=employee.last_name,
                        phone=employee.phone,
                        role=user_role,
                    )

                    # =================================================
                    # LINK USER <-> EMPLOYEE
                    # =================================================

                    employee.user = user

                    employee.save()

                # =====================================================
                # SUCCESS
                # =====================================================

                messages.success(
                    request,
                    (
                        f"{employee.get_full_name()} "
                        f"was created successfully. "
                        f"Login credentials have been sent to "
                        f"{employee.email}."
                    ),
                )

                return redirect(
                    "employee_detail",
                    pk=employee.pk,
                )

            except ValueError as exc:

                logger.warning(
                    "Employee creation validation error: %s",
                    exc,
                )

                messages.error(
                    request,
                    str(exc),
                )

                form.add_error(
                    None,
                    str(exc),
                )

            except Exception as exc:

                logger.exception(
                    "Employee creation failed. "
                    "User=%s EmployeeData=%s Error=%r",
                    request.user.username,
                    {
                        "employee_id":
                            request.POST.get("employee_id"),
                        "email":
                            request.POST.get("email"),
                        "role":
                            request.POST.get("role"),
                        "company":
                            request.POST.get("company"),
                        "department":
                            request.POST.get("department"),
                        "reporting_manager":
                            request.POST.get(
                                "reporting_manager"
                            ),
                    },
                    exc,
                )

                error_message = (
                    "Unable to create the employee. "
                    "Please check the form data and "
                    "the server console for the exact error."
                )

                messages.error(
                    request,
                    error_message,
                )

                form.add_error(
                    None,
                    error_message,
                )

    else:

        form = EmployeeForm(
            request_user=request.user,
        )

        prepare_employee_form(
            form,
            current_employee,
        )

        # =====================================================
        # HR COMPANY DEFAULT
        # =====================================================

        if is_hr_admin(
            current_employee
        ):

            form.fields[
                "company"
            ].initial = (
                current_employee.company_id
            )

        # =====================================================
        # SUPER ADMIN REPORTING MANAGER
        # =====================================================

        elif is_super_admin(
            current_employee
        ):

            form.fields[
                "reporting_manager"
            ].queryset = (
                Employee.objects.filter(
                    role=Employee.Role.SUPER_ADMIN,
                    employment_status__in=[
                        Employee.EmploymentStatus.ACTIVE,
                        Employee.EmploymentStatus.ON_LEAVE,
                    ],
                )
                .select_related(
                    "company",
                    "department",
                    "user",
                )
                .order_by(
                    "first_name",
                    "last_name",
                )
            )

    # =====================================================
    # PAGE TITLE
    # =====================================================

    if is_super_admin(
        current_employee
    ):

        title = "Add HR Admin"
        button_text = "Create HR Admin"

    else:

        title = "Add Employee"
        button_text = "Create Employee"

    return render_employee_form(
        request,
        form,
        current_employee,
        title,
        button_text,
    )


# =========================================================
# UPDATE EMPLOYEE
# =========================================================

@login_required
def employee_update(request, pk):

    current_employee = require_hr(
        request
    )

    if not current_employee:

        return redirect(
            "dashboard"
        )

    employee = get_hr_accessible_employee(
        current_employee,
        pk,
    )

    if not employee:

        messages.error(
            request,
            "You are not authorized to update this employee.",
        )

        return redirect(
            "employee_list"
        )

    # =====================================================
    # TERMINATED EMPLOYEE
    # =====================================================

    if (
        employee.employment_status
        == Employee.EmploymentStatus.TERMINATED
    ):

        messages.error(
            request,
            "A terminated employee cannot be edited.",
        )

        return redirect(
            "employee_detail",
            pk=employee.pk,
        )

    if request.method == "POST":

        form = EmployeeForm(
            request.POST,
            request.FILES,
            instance=employee,
            request_user=request.user,
        )

        prepare_employee_form(
            form,
            current_employee,
            employee,
        )

        if form.is_valid():

            try:

                with transaction.atomic():

                    updated_employee = form.save(
                        commit=False
                    )

                    # =================================================
                    # COMPANY SECURITY
                    # =================================================

                    if is_hr_admin(
                        current_employee
                    ):

                        updated_employee.company = (
                            current_employee.company
                        )
                        updated_employee.branch = (
                            current_employee.branch
                        )

                    # =================================================
                    # REPORTING HIERARCHY
                    # =================================================

                    if not validate_reporting_hierarchy(
                        updated_employee,
                        current_employee,
                        form,
                        creating=False,
                    ):

                        raise ValueError(
                            "Please correct the reporting hierarchy."
                        )

                    # =================================================
                    # EMAIL REQUIRED
                    # =================================================

                    if not updated_employee.email:

                        raise ValueError(
                            (
                                "Email address is required "
                                "for the login account."
                            )
                        )

                    # =================================================
                    # UPDATE LINKED USER
                    # =================================================

                    if updated_employee.user:

                        updated_employee.user.email = (
                            updated_employee.email
                        )

                        updated_employee.user.first_name = (
                            updated_employee.first_name
                        )

                        updated_employee.user.last_name = (
                            updated_employee.last_name
                        )

                        updated_employee.user.phone = (
                            updated_employee.phone
                        )

                        updated_employee.user.save(
                            update_fields=[
                                "email",
                                "first_name",
                                "last_name",
                                "phone",
                            ]
                        )

                    # =================================================
                    # SAVE EMPLOYEE
                    # =================================================

                    updated_employee.save()

                messages.success(
                    request,
                    (
                        f"{updated_employee.get_full_name()} "
                        f"was updated successfully."
                    ),
                )

                return redirect(
                    "employee_detail",
                    pk=updated_employee.pk,
                )

            except ValueError as exc:

                logger.warning(
                    "Employee update validation error: %s",
                    exc,
                )

                messages.error(
                    request,
                    str(exc),
                )

                form.add_error(
                    None,
                    str(exc),
                )

            except Exception as exc:

                logger.exception(
                    "Employee update failed. "
                    "Employee=%s Error=%r",
                    employee.pk,
                    exc,
                )

                error_message = (
                    "Unable to update the employee. "
                    "Please check the form data and "
                    "the server console for the exact error."
                )

                messages.error(
                    request,
                    error_message,
                )

                form.add_error(
                    None,
                    error_message,
                )

    else:

        form = EmployeeForm(
            instance=employee,
            request_user=request.user,
        )

        prepare_employee_form(
            form,
            current_employee,
            employee,
        )

    return render_employee_form(
        request,
        form,
        current_employee,
        "Edit Employee",
        "Update Employee",
        employee=employee,
    )


# =========================================================
# PUT EMPLOYEE ON BENCH
# =========================================================

@login_required
def employee_bench(request, pk):

    current_employee = require_hr(
        request
    )

    if not current_employee:

        return redirect(
            "dashboard"
        )

    employee = get_hr_accessible_employee(
        current_employee,
        pk,
    )

    if not employee:

        messages.error(
            request,
            "You are not authorized to manage this employee.",
        )

        return redirect(
            "employee_list"
        )

    if request.method != "POST":

        return redirect(
            "employee_detail",
            pk=employee.pk,
        )

    if (
        employee.employment_status
        == Employee.EmploymentStatus.TERMINATED
    ):

        messages.error(
            request,
            "A terminated employee cannot be moved to Bench.",
        )

        return redirect(
            "employee_detail",
            pk=employee.pk,
        )

    if (
        employee.employment_status
        == Employee.EmploymentStatus.BENCH
    ):

        messages.warning(
            request,
            "Employee is already on Bench.",
        )

        return redirect(
            "employee_detail",
            pk=employee.pk,
        )

    employee.employment_status = (
        Employee.EmploymentStatus.BENCH
    )

    employee.save(
        update_fields=[
            "employment_status",
            "updated_at",
        ]
    )

    messages.success(
        request,
        (
            f"{employee.get_full_name()} "
            f"has been moved to Bench."
        ),
    )

    return redirect(
        "employee_detail",
        pk=employee.pk,
    )


# =========================================================
# ACTIVATE EMPLOYEE
# =========================================================

@login_required
def employee_activate(request, pk):

    current_employee = require_hr(
        request
    )

    if not current_employee:

        return redirect(
            "dashboard"
        )

    employee = get_hr_accessible_employee(
        current_employee,
        pk,
    )

    if not employee:

        messages.error(
            request,
            "You are not authorized to manage this employee.",
        )

        return redirect(
            "employee_list"
        )

    if request.method != "POST":

        return redirect(
            "employee_detail",
            pk=employee.pk,
        )

    if (
        employee.employment_status
        == Employee.EmploymentStatus.TERMINATED
    ):

        messages.error(
            request,
            "A terminated employee cannot be activated.",
        )

        return redirect(
            "employee_detail",
            pk=employee.pk,
        )

    employee.employment_status = (
        Employee.EmploymentStatus.ACTIVE
    )

    employee.save(
        update_fields=[
            "employment_status",
            "updated_at",
        ]
    )

    if employee.user:

        if not employee.user.is_active:

            employee.user.is_active = True

            employee.user.save(
                update_fields=[
                    "is_active",
                ]
            )

    messages.success(
        request,
        (
            f"{employee.get_full_name()} "
            f"is now Active."
        ),
    )

    return redirect(
        "employee_detail",
        pk=employee.pk,
    )


# =========================================================
# TERMINATE EMPLOYEE
# =========================================================

@login_required
def employee_terminate(request, pk):

    current_employee = require_hr(
        request
    )

    if not current_employee:

        return redirect(
            "dashboard"
        )

    employee = get_hr_accessible_employee(
        current_employee,
        pk,
    )

    if not employee:

        messages.error(
            request,
            "You are not authorized to manage this employee.",
        )

        return redirect(
            "employee_list"
        )

    if request.method != "POST":

        return redirect(
            "employee_detail",
            pk=employee.pk,
        )

    if (
        employee.employment_status
        == Employee.EmploymentStatus.TERMINATED
    ):

        messages.warning(
            request,
            "Employee is already terminated.",
        )

        return redirect(
            "employee_detail",
            pk=employee.pk,
        )

    with transaction.atomic():

        employee.employment_status = (
            Employee.EmploymentStatus.TERMINATED
        )

        employee.termination_date = (
            timezone.localdate()
        )

        employee.save(
            update_fields=[
                "employment_status",
                "termination_date",
                "updated_at",
            ]
        )

        if employee.user:

            employee.user.is_active = False

            employee.user.save(
                update_fields=[
                    "is_active",
                ]
            )

    messages.success(
        request,
        (
            f"{employee.get_full_name()} "
            f"has been terminated successfully. "
            f"Their login account has been disabled."
        ),
    )

    return redirect(
        "employee_detail",
        pk=employee.pk,
    )


# =========================================================
# DELETE EMPLOYEE
# =========================================================

@login_required
def employee_delete(request, pk):

    current_employee = require_hr(
        request
    )

    if not current_employee:

        return redirect(
            "dashboard"
        )

    employee = get_hr_accessible_employee(
        current_employee,
        pk,
    )

    if not employee:

        messages.error(
            request,
            "You are not authorized to delete this employee.",
        )

        return redirect(
            "employee_list"
        )

    messages.error(
        request,
        (
            "Employee records should not be permanently "
            "deleted. Use Terminate instead."
        ),
    )

    return redirect(
        "employee_detail",
        pk=employee.pk,
    )


# =========================================================
# EMPLOYEE DOCUMENTS
# =========================================================

@login_required
def employee_documents(request, pk):

    current_employee = get_current_employee(
        request
    )

    if not current_employee:

        messages.error(
            request,
            "Your Employee profile was not found.",
        )

        return redirect(
            "dashboard"
        )

    employee = get_object_or_404(
        Employee,
        pk=pk,
    )

    # =====================================================
    # ACCESS CONTROL
    # =====================================================

    if is_super_admin(current_employee):

        allowed = True

    elif is_hr_admin(current_employee):

        allowed = is_same_company_branch(
            current_employee,
            employee,
        )

    elif (
        current_employee.role
        == Employee.Role.MANAGER
    ):

        allowed = (
            is_same_company_branch(
                current_employee,
                employee,
            )
            and (
                employee.pk
                == current_employee.pk
                or
                employee.reporting_manager_id
                == current_employee.pk
            )
        )

    else:

        allowed = (
            employee.pk
            == current_employee.pk
        )

    if not allowed:

        messages.error(
            request,
            "You are not authorized to view these documents.",
        )

        return redirect(
            "employee_list"
        )

    return render(
        request,
        "employees/employee_documents.html",
        {
            "employee": employee,
            "documents":
                employee.documents.all(),
            "current_employee":
                current_employee,
            "can_manage_employee":
                is_hr_or_super_admin(
                    current_employee
                )
                and (
                    is_super_admin(
                        current_employee
                    )
                    or
                    is_same_company_branch(
                        current_employee,
                        employee,
                    )
                ),
        },
    )


# =========================================================
# ADD EMPLOYEE DOCUMENT
# =========================================================

@login_required
def employee_document_create(request, pk):

    current_employee = require_hr(
        request
    )

    if not current_employee:

        return redirect(
            "dashboard"
        )

    employee = get_hr_accessible_employee(
        current_employee,
        pk,
    )

    if not employee:

        messages.error(
            request,
            "You are not authorized to add documents.",
        )

        return redirect(
            "employee_list"
        )

    if request.method == "POST":

        form = EmployeeDocumentForm(
            request.POST,
            request.FILES,
        )

        if form.is_valid():

            document = form.save(
                commit=False
            )

            document.employee = employee

            document.save()

            messages.success(
                request,
                "Employee document uploaded successfully.",
            )

            return redirect(
                "employee_documents",
                pk=employee.pk,
            )

    else:

        form = EmployeeDocumentForm()

    return render(
        request,
        "employees/employee_document_form.html",
        {
            "form": form,
            "employee": employee,
            "title": "Add Employee Document",
            "button_text": "Upload Document",
            "current_employee":
                current_employee,
        },
    )


# =========================================================
# DELETE EMPLOYEE DOCUMENT
# =========================================================

@login_required
def employee_document_delete(
    request,
    pk,
    document_pk,
):

    current_employee = require_hr(
        request
    )

    if not current_employee:

        return redirect(
            "dashboard"
        )

    employee = get_hr_accessible_employee(
        current_employee,
        pk,
    )

    if not employee:

        messages.error(
            request,
            "You are not authorized to delete this document.",
        )

        return redirect(
            "employee_list"
        )

    document = get_object_or_404(
        EmployeeDocument,
        pk=document_pk,
        employee=employee,
    )

    if request.method == "POST":

        document.delete()

        messages.success(
            request,
            "Employee document deleted successfully.",
        )

    return redirect(
        "employee_documents",
        pk=employee.pk,
    )


# =========================================================
# EMPLOYEE ASSETS
# =========================================================

@login_required
def employee_assets(request, pk):

    current_employee = get_current_employee(
        request
    )

    if not current_employee:

        messages.error(
            request,
            "Your Employee profile was not found.",
        )

        return redirect(
            "dashboard"
        )

    employee = get_object_or_404(
        Employee,
        pk=pk,
    )

    # =====================================================
    # ACCESS CONTROL
    # =====================================================

    if is_super_admin(current_employee):

        allowed = True

    elif is_hr_admin(current_employee):

        allowed = is_same_company_branch(
            current_employee,
            employee,
        )

    elif (
        current_employee.role
        == Employee.Role.MANAGER
    ):

        allowed = (
            is_same_company_branch(
                current_employee,
                employee,
            )
            and (
                employee.pk
                == current_employee.pk
                or
                employee.reporting_manager_id
                == current_employee.pk
            )
        )

    else:

        allowed = (
            employee.pk
            == current_employee.pk
        )

    if not allowed:

        messages.error(
            request,
            "You are not authorized to view these assets.",
        )

        return redirect(
            "employee_list"
        )

    return render(
        request,
        "employees/employee_assets.html",
        {
            "employee": employee,
            "assets":
                employee.assets.all(),
            "current_employee":
                current_employee,
            "can_manage_employee":
                is_hr_or_super_admin(
                    current_employee
                )
                and (
                    is_super_admin(
                        current_employee
                    )
                    or
                    is_same_company_branch(
                        current_employee,
                        employee,
                    )
                ),
        },
    )


# =========================================================
# ADD EMPLOYEE ASSET
# =========================================================

@login_required
def employee_asset_create(request, pk):

    current_employee = require_hr(
        request
    )

    if not current_employee:

        return redirect(
            "dashboard"
        )

    employee = get_hr_accessible_employee(
        current_employee,
        pk,
    )

    if not employee:

        messages.error(
            request,
            "You are not authorized to assign assets.",
        )

        return redirect(
            "employee_list"
        )

    if request.method == "POST":

        form = EmployeeAssetForm(
            request.POST,
        )

        if form.is_valid():

            asset = form.save(
                commit=False
            )

            asset.employee = employee

            asset.save()

            messages.success(
                request,
                "Employee asset assigned successfully.",
            )

            return redirect(
                "employee_assets",
                pk=employee.pk,
            )

    else:

        form = EmployeeAssetForm()

    return render(
        request,
        "employees/employee_asset_form.html",
        {
            "form": form,
            "employee": employee,
            "title": "Assign Employee Asset",
            "button_text": "Assign Asset",
            "current_employee":
                current_employee,
        },
    )


# =========================================================
# DELETE EMPLOYEE ASSET
# =========================================================

@login_required
def employee_asset_delete(
    request,
    pk,
    asset_pk,
):

    current_employee = require_hr(
        request
    )

    if not current_employee:

        return redirect(
            "dashboard"
        )

    employee = get_hr_accessible_employee(
        current_employee,
        pk,
    )

    if not employee:

        messages.error(
            request,
            "You are not authorized to remove this asset.",
        )

        return redirect(
            "employee_list"
        )

    asset = get_object_or_404(
        EmployeeAsset,
        pk=asset_pk,
        employee=employee,
    )

    if request.method == "POST":

        asset.delete()

        messages.success(
            request,
            "Employee asset removed successfully.",
        )

    return redirect(
        "employee_assets",
        pk=employee.pk,
    )
