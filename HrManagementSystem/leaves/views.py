from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.db import transaction
from django.db.models import Q
from django.shortcuts import (
    get_object_or_404,
    redirect,
    render,
)
from django.views.decorators.http import require_POST
from django.utils import timezone

from employees.models import Employee
from employees.views import get_current_employee

from .forms import (
    LeaveApprovalForm,
    LeaveBalanceForm,
    LeaveRequestForm,
    LeaveTypeForm,
)

from .models import (
    LeaveApproval,
    LeaveBalance,
    LeaveRequest,
    LeaveType,
)


def get_visible_leave_requests(employee):
    """Return leave requests visible to the current employee."""

    requests = LeaveRequest.objects.select_related(
        "employee",
        "employee__company",
        "employee__department",
        "employee__reporting_manager",
        "leave_type",
        "approved_by",
    )

    # ------------------------------------------
    # SUPER ADMIN
    # ------------------------------------------

    if employee.role == Employee.Role.SUPER_ADMIN:
        return requests

    # ------------------------------------------
    # HR ADMIN
    # ------------------------------------------
    #
    # HR can view all leave information within
    # their company.
    #
    # HR approves Manager leave only.
    #

    if employee.role == Employee.Role.HR_ADMIN:
        return requests.filter(
            employee__company_id=employee.company_id,
        )

    # ------------------------------------------
    # MANAGER
    # ------------------------------------------
    #
    # Manager can view:
    # 1. Own leave requests
    # 2. Direct team member leave requests
    #
    # Manager cannot view unrelated employees'
    # or other managers' leave requests.
    #

    if employee.role == Employee.Role.MANAGER:
        return requests.filter(
            Q(employee_id=employee.pk)
            | Q(employee__reporting_manager_id=employee.pk)
        )

    # ------------------------------------------
    # EMPLOYEE
    # ------------------------------------------

    return requests.filter(
        employee_id=employee.pk
    )


@login_required
def leave_dashboard(request):

    employee = get_object_or_404(
        Employee,
        user=request.user,
    )

    today = timezone.localdate()

    context = {
        "employee": employee,
        "today": today,
    }

    # ==========================================
    # EMPLOYEE
    # ==========================================

    if employee.role == Employee.Role.EMPLOYEE:

        my_requests = LeaveRequest.objects.filter(
            employee=employee
        )

        context.update({
            "my_requests": my_requests,

            "pending_count": my_requests.filter(
                status=LeaveRequest.Status.PENDING
            ).count(),

            "approved_count": my_requests.filter(
                status=LeaveRequest.Status.APPROVED
            ).count(),

            "rejected_count": my_requests.filter(
                status=LeaveRequest.Status.REJECTED
            ).count(),

            "balances": LeaveBalance.objects.filter(
                employee=employee,
                year=today.year,
            ).select_related(
                "leave_type"
            ),
        })

    # ==========================================
    # MANAGER
    # ==========================================

    elif employee.role == Employee.Role.MANAGER:

        team = Employee.objects.filter(
            reporting_manager=employee
        )

        # --------------------------------------
        # TEAM REQUESTS
        # --------------------------------------

        team_requests = LeaveRequest.objects.filter(
            employee__in=team
        )

        # --------------------------------------
        # OWN REQUESTS
        # --------------------------------------

        my_requests = LeaveRequest.objects.filter(
            employee=employee
        )

        # --------------------------------------
        # TEAM REQUESTS WAITING FOR MANAGER
        # --------------------------------------

        team_pending_count = team_requests.filter(
            approval_stage=LeaveRequest.ApprovalStage.MANAGER,
            status=LeaveRequest.Status.PENDING,
        ).count()

        # --------------------------------------
        # OWN REQUESTS WAITING FOR HR
        # --------------------------------------

        own_pending_count = my_requests.filter(
            approval_stage=LeaveRequest.ApprovalStage.HR_ADMIN,
            status=LeaveRequest.Status.PENDING,
        ).count()

        # --------------------------------------
        # APPROVED TEAM LEAVES
        # --------------------------------------

        team_approved_count = team_requests.filter(
            status=LeaveRequest.Status.APPROVED
        ).count()

        # --------------------------------------
        # TEAM MEMBERS CURRENTLY ON LEAVE
        # --------------------------------------

        team_on_leave = team_requests.filter(
            status=LeaveRequest.Status.APPROVED,
            start_date__lte=today,
            end_date__gte=today,
        ).count()

        context.update({
            "team": team,

            "team_requests": team_requests,

            "my_requests": my_requests,

            # Total pending items relevant to Manager.
            # This includes:
            # - Team leave waiting for Manager
            # - Manager's own leave waiting for HR
            "pending_count": (
                team_pending_count
                + own_pending_count
            ),

            "team_pending_count": team_pending_count,

            "own_pending_count": own_pending_count,

            "approved_count": team_approved_count,

            "team_on_leave": team_on_leave,
        })

    # ==========================================
    # HR ADMIN
    # ==========================================

    elif employee.role == Employee.Role.HR_ADMIN:

        company_requests = get_visible_leave_requests(
            employee
        )

    
        hr_pending_requests = company_requests.filter(
            employee__role=Employee.Role.MANAGER,
            approval_stage=LeaveRequest.ApprovalStage.HR_ADMIN,
            status=LeaveRequest.Status.PENDING,
        )

        approved_requests = company_requests.filter(
        status=LeaveRequest.Status.APPROVED   )

        rejected_requests = company_requests.filter(
        status=LeaveRequest.Status.REJECTED    )

        active_leave_types = LeaveType.objects.filter(
        is_active=True    )

        company_employees = Employee.objects.filter(
                company_id=employee.company_id,
                employment_status__in=[
                    Employee.EmploymentStatus.ACTIVE,
                    Employee.EmploymentStatus.ON_LEAVE,
                    Employee.EmploymentStatus.BENCH,
                ],
            )

        currently_on_leave = company_requests.filter(
        status=LeaveRequest.Status.APPROVED,
        start_date__lte=today,
        end_date__gte=today,
    )

        
        context.update({
            "company_requests": company_requests,

            "pending_count": hr_pending_requests.count(),

            "approved_count": approved_requests.count(),

            "rejected_count": rejected_requests.count(),

            "active_types": active_leave_types.count(),

        # Existing/extra values
            "employee_count": company_employees.count(),

            "leave_type_count": active_leave_types.count(),

            "currently_on_leave": currently_on_leave,

      })

    # ==========================================
    # SUPER ADMIN
    # ==========================================

    elif employee.role == Employee.Role.SUPER_ADMIN:

        all_requests = get_visible_leave_requests(
            employee
        )

        active_leave_types = LeaveType.objects.filter(
            is_active=True
        )

        employee_count = Employee.objects.filter(
            employment_status__in=[
                Employee.EmploymentStatus.ACTIVE,
                Employee.EmploymentStatus.ON_LEAVE,
                Employee.EmploymentStatus.BENCH,
            ]
        ).count()


        currently_on_leave = all_requests.filter(
            status=LeaveRequest.Status.APPROVED,
            start_date__lte=today,
            end_date__gte=today,
        )

        context.update({
            "all_requests": all_requests,

            # Pending
            "pending_count": all_requests.filter(
                status=LeaveRequest.Status.PENDING
            ).count(),

            # Approved
            "approved_count": all_requests.filter(
                status=LeaveRequest.Status.APPROVED
            ).count(),

            # Rejected
            "rejected_count": all_requests.filter(
                status=LeaveRequest.Status.REJECTED
            ).count(),

            # Active Leave Types
            "active_types": active_leave_types.count(),

            # Existing employee count
            "employee_count": employee_count,

            # Existing name, if used somewhere else
            "leave_type_count": active_leave_types.count(),

            # Current employees on approved leave
            "currently_on_leave": currently_on_leave,
        })

    return render(
        request,
        "leave/leave_dashboard.html",
        context,
    )


@login_required
def leave_list(request):

    employee = get_object_or_404(
        Employee.objects.select_related(
            "company",
            "department",
        ),
        user=request.user,
    )

    requests = get_visible_leave_requests(
        employee
    )

    # --------------------------------------------------
    # SUPER ADMIN
    # --------------------------------------------------

    if employee.role == Employee.Role.SUPER_ADMIN:

        pass

    # --------------------------------------------------
    # HR ADMIN
    # --------------------------------------------------

    elif employee.role == Employee.Role.HR_ADMIN:

        requests = requests.filter(
            employee__company_id=employee.company_id,
        )

    # --------------------------------------------------
    # MANAGER
    # --------------------------------------------------

    elif employee.role == Employee.Role.MANAGER:

        pass

    else:

        requests = requests.filter(
            employee_id=employee.pk
        )

    requests = requests.order_by(
        "-created_at"
    )

    return render(
        request,
        "leave/leave_list.html",
        {
            "leave_requests": requests,
            "current_employee": employee,
        },
    )


@login_required
def leave_detail(request, pk):

    employee = get_object_or_404(
        Employee,
        user=request.user,
    )

    leave_request = get_object_or_404(
        LeaveRequest.objects.select_related(
            "employee",
            "employee__reporting_manager",
            "employee__company",
            "employee__department",
            "leave_type",
            "approved_by",
        ),
        pk=pk,
    )

    allowed = False

    # ------------------------------------------
    # EMPLOYEE → OWN LEAVE
    # ------------------------------------------

    if (
        employee.role == Employee.Role.EMPLOYEE
        and leave_request.employee_id == employee.pk
    ):
        allowed = True

    # ------------------------------------------
    # MANAGER → OWN LEAVE OR DIRECT TEAM MEMBER
    # ------------------------------------------

    elif employee.role == Employee.Role.MANAGER:

        allowed = (
            leave_request.employee_id == employee.pk
            or
            leave_request.employee.reporting_manager_id
            == employee.pk
        )

    # ------------------------------------------
    # HR → SAME COMPANY
    # ------------------------------------------

    elif employee.role == Employee.Role.HR_ADMIN:

        allowed = (
            leave_request.employee.company_id
            == employee.company_id
        )

    # ------------------------------------------
    # SUPER ADMIN → GLOBAL INFORMATION ACCESS
    # ------------------------------------------

    elif employee.role == Employee.Role.SUPER_ADMIN:

        allowed = True

    if not allowed:

        messages.error(
            request,
            "You do not have permission to view this leave request.",
        )

        return redirect(
            "leave_dashboard"
        )

    approval_history = (
        leave_request.approval_history
        .select_related(
            "acted_by",
        )
        .all()
    )

    return render(
        request,
        "leave/leave_detail.html",
        {
            "leave_request": leave_request,
            "approval_history": approval_history,
            "current_employee": employee,
        },
    )


@login_required
def leave_create(request):

    employee = get_object_or_404(
        Employee.objects.select_related(
            "company",
            "department",
            "reporting_manager",
        ),
        user=request.user,
    )

    if employee.employment_status != Employee.EmploymentStatus.ACTIVE:

        messages.error(
            request,
            "Only active employees can apply for leave.",
        )

        return redirect(
            "leave_dashboard"
        )

    # ==========================================
    # SUPER ADMIN
    # ==========================================

    if employee.role == Employee.Role.SUPER_ADMIN:

        messages.info(
            request,
            "Super Admin leave workflow is currently under development.",
        )

        return redirect(
            "leave_dashboard"
        )

    # ==========================================
    # HR ADMIN
    # ==========================================

    if employee.role == Employee.Role.HR_ADMIN:

        messages.info(
            request,
            "HR leave approval workflow is currently under development.",
        )

        return redirect(
            "leave_dashboard"
        )

    if request.method == "POST":

        form = LeaveRequestForm(
            request.POST,
            request.FILES,
        )

        if form.is_valid():

            leave_request = form.save(
                commit=False
            )

            leave_request.employee = employee

            # ==========================================
            # MANAGER → HR → FINAL
            # ==========================================

            if employee.role == Employee.Role.MANAGER:

                leave_request.approval_stage = (
                    LeaveRequest.ApprovalStage.HR_ADMIN
                )

            # ==========================================
            # EMPLOYEE → MANAGER → FINAL
            # ==========================================

            elif employee.role == Employee.Role.EMPLOYEE:

                if not employee.reporting_manager_id:

                    messages.error(
                        request,
                        "You cannot apply for leave because no reporting manager is assigned to you.",
                    )

                    return render(
                        request,
                        "leave/leave_form.html",
                        {
                            "form": form,
                            "employee": employee,
                            "title": "Apply for Leave",
                            "button_text": "Submit Leave Request",
                        },
                    )

                if employee.reporting_manager.role != Employee.Role.MANAGER:

                    messages.error(
                        request,
                        "Your assigned reporting manager is not a valid Manager.",
                    )

                    return render(
                        request,
                        "leave/leave_form.html",
                        {
                            "form": form,
                            "employee": employee,
                            "title": "Apply for Leave",
                            "button_text": "Submit Leave Request",
                        },
                    )

                if (
                    employee.company_id
                    != employee.reporting_manager.company_id
                ):

                    messages.error(
                        request,
                        "Your reporting manager must belong to the same company.",
                    )

                    return render(
                        request,
                        "leave/leave_form.html",
                        {
                            "form": form,
                            "employee": employee,
                            "title": "Apply for Leave",
                            "button_text": "Submit Leave Request",
                        },
                    )

                if (
                    employee.department_id
                    != employee.reporting_manager.department_id
                ):

                    messages.error(
                        request,
                        "Your reporting manager must be in the same department.",
                    )

                    return render(
                        request,
                        "leave/leave_form.html",
                        {
                            "form": form,
                            "employee": employee,
                            "title": "Apply for Leave",
                            "button_text": "Submit Leave Request",
                        },
                    )

                leave_request.approval_stage = (
                    LeaveRequest.ApprovalStage.MANAGER
                )

            else:

                messages.error(
                    request,
                    "Your leave workflow is currently unavailable.",
                )

                return redirect(
                    "leave_dashboard"
                )

            leave_request.status = (
                LeaveRequest.Status.PENDING
            )

            leave_request.save()

            messages.success(
                request,
                "Leave request submitted successfully.",
            )

            return redirect(
                "leave_detail",
                pk=leave_request.pk,
            )

    else:

        form = LeaveRequestForm()

    return render(
        request,
        "leave/leave_form.html",
        {
            "form": form,
            "employee": employee,
            "title": "Apply for Leave",
            "button_text": "Submit Leave Request",
        },
    )


def deduct_leave_balance(leave_request):

    if leave_request.balance_deducted:
        return

    year = leave_request.start_date.year

    balance = (
        LeaveBalance.objects
        .select_for_update()
        .filter(
            employee=leave_request.employee,
            leave_type=leave_request.leave_type,
            year=year,
        )
        .first()
    )

    if not balance:

        raise ValueError(
            "Leave balance does not exist for this employee "
            "and leave type."
        )

    requested_days = leave_request.total_days

    if balance.available_days < requested_days:

        raise ValueError(
            f"Insufficient leave balance. "
            f"Available: {balance.available_days}, "
            f"Requested: {requested_days}."
        )

    balance.used_days += requested_days

    balance.save(
        update_fields=[
            "used_days",
        ]
    )

    leave_request.balance_deducted = True

    leave_request.save(
        update_fields=[
            "balance_deducted",
            "updated_at",
        ]
    )


@login_required
def leave_approval(request, pk):

    employee = get_object_or_404(
        Employee.objects.select_related(
            "company",
            "department",
            "reporting_manager",
        ),
        user=request.user,
    )

    leave_request = get_object_or_404(
        LeaveRequest.objects.select_related(
            "employee",
            "employee__company",
            "employee__department",
            "employee__reporting_manager",
            "leave_type",
        ),
        pk=pk,
    )

    # ==========================================
    # FINALIZED REQUEST
    # ==========================================

    if leave_request.is_finalized:

        messages.error(
            request,
            "This leave request is already finalized and cannot be changed.",
        )

        return redirect(
            "leave_detail",
            pk=pk,
        )

    # ==========================================
    # CANNOT APPROVE OWN LEAVE
    # ==========================================

    if leave_request.employee_id == employee.pk:

        messages.error(
            request,
            "You cannot approve your own leave request.",
        )

        return redirect(
            "leave_detail",
            pk=pk,
        )

    # ==========================================
    # ONLY PENDING REQUESTS
    # ==========================================

    if leave_request.status != LeaveRequest.Status.PENDING:

        messages.error(
            request,
            "Only pending leave requests can be approved or rejected.",
        )

        return redirect(
            "leave_detail",
            pk=pk,
        )

    # ==========================================
    # APPROVAL FORM
    # ==========================================

    if request.method == "POST":

        form = LeaveApprovalForm(
            request.POST
        )

        form.fields["action"].choices = [
            ("APPROVE", "Approve"),
            ("REJECT", "Reject"),
        ]

        if form.is_valid():

            action = form.cleaned_data["action"]
            reason = form.cleaned_data["reason"]

            # ==========================================
            # EMPLOYEE → MANAGER → FINAL
            # ==========================================

            if (
                leave_request.approval_stage
                == LeaveRequest.ApprovalStage.MANAGER
            ):

                # --------------------------------------
                # ONLY MANAGER
                # --------------------------------------

                if employee.role != Employee.Role.MANAGER:

                    messages.error(
                        request,
                        "Only the assigned manager can review this leave.",
                    )

                    return redirect(
                        "leave_detail",
                        pk=pk,
                    )

                # --------------------------------------
                # REQUESTER MUST BE EMPLOYEE
                # --------------------------------------

                if (
                    leave_request.employee.role
                    != Employee.Role.EMPLOYEE
                ):

                    messages.error(
                        request,
                        "Manager approval is only applicable to Employee leave requests.",
                    )

                    return redirect(
                        "leave_detail",
                        pk=pk,
                    )

                # --------------------------------------
                # ONLY REPORTING MANAGER
                # --------------------------------------

                if (
                    leave_request.employee.reporting_manager_id
                    != employee.pk
                ):

                    messages.error(
                        request,
                        "You are not the reporting manager for this employee.",
                    )

                    return redirect(
                        "leave_detail",
                        pk=pk,
                    )

                # --------------------------------------
                # SAME COMPANY
                # --------------------------------------

                if (
                    leave_request.employee.company_id
                    != employee.company_id
                ):

                    messages.error(
                        request,
                        "You are not authorized to review leave from another company.",
                    )

                    return redirect(
                        "leave_detail",
                        pk=pk,
                    )

                # --------------------------------------
                # SAME DEPARTMENT
                # --------------------------------------

                if (
                    leave_request.employee.department_id
                    != employee.department_id
                ):

                    messages.error(
                        request,
                        "You are not authorized to review leave from another department.",
                    )

                    return redirect(
                        "leave_detail",
                        pk=pk,
                    )

                # ======================================
                # MANAGER APPROVE → FINAL
                # ======================================

                if action == "APPROVE":

                    try:

                        with transaction.atomic():

                            locked_request = (
                                LeaveRequest.objects
                                .select_for_update()
                                .select_related(
                                    "employee",
                                    "leave_type",
                                )
                                .get(
                                    pk=pk
                                )
                            )

                            if locked_request.is_finalized:

                                messages.error(
                                    request,
                                    "This leave was already finalized.",
                                )

                                return redirect(
                                    "leave_detail",
                                    pk=pk,
                                )

                            if (
                                locked_request.status
                                != LeaveRequest.Status.PENDING
                            ):

                                messages.error(
                                    request,
                                    "This leave request is no longer pending.",
                                )

                                return redirect(
                                    "leave_detail",
                                    pk=pk,
                                )

                            if (
                                locked_request.approval_stage
                                != LeaveRequest.ApprovalStage.MANAGER
                            ):

                                messages.error(
                                    request,
                                    "This leave is no longer waiting for Manager approval.",
                                )

                                return redirect(
                                    "leave_detail",
                                    pk=pk,
                                )

                            locked_request.status = (
                                LeaveRequest.Status.APPROVED
                            )

                            locked_request.approved_by = employee

                            locked_request.approved_at = (
                                timezone.now()
                            )

                            locked_request.approval_stage = None

                            locked_request.rejection_reason = ""

                            locked_request.save(
                                update_fields=[
                                    "status",
                                    "approved_by",
                                    "approved_at",
                                    "approval_stage",
                                    "rejection_reason",
                                    "updated_at",
                                ]
                            )

                            LeaveApproval.objects.create(
                                leave_request=locked_request,
                                stage=LeaveApproval.Stage.MANAGER,
                                action=LeaveApproval.Action.APPROVED,
                                acted_by=employee,
                                reason=reason,
                            )

                            deduct_leave_balance(
                                locked_request
                            )

                    except ValueError as exc:

                        messages.error(
                            request,
                            str(exc),
                        )

                        return redirect(
                            "leave_detail",
                            pk=pk,
                        )

                    messages.success(
                        request,
                        "Leave finally approved by Manager.",
                    )

                    return redirect(
                        "leave_detail",
                        pk=pk,
                    )

                # ======================================
                # MANAGER REJECT → FINAL
                # ======================================

                if action == "REJECT":

                    with transaction.atomic():

                        locked_request = (
                            LeaveRequest.objects
                            .select_for_update()
                            .get(
                                pk=pk
                            )
                        )

                        if locked_request.is_finalized:

                            messages.error(
                                request,
                                "This leave was already finalized.",
                            )

                            return redirect(
                                "leave_detail",
                                pk=pk,
                            )

                        if (
                            locked_request.status
                            != LeaveRequest.Status.PENDING
                        ):

                            messages.error(
                                request,
                                "This leave request is no longer pending.",
                            )

                            return redirect(
                                "leave_detail",
                                pk=pk,
                            )

                        if (
                            locked_request.approval_stage
                            != LeaveRequest.ApprovalStage.MANAGER
                        ):

                            messages.error(
                                request,
                                "This leave is no longer waiting for Manager approval.",
                            )

                            return redirect(
                                "leave_detail",
                                pk=pk,
                            )

                        locked_request.status = (
                            LeaveRequest.Status.REJECTED
                        )

                        locked_request.approval_stage = None

                        locked_request.rejection_reason = reason

                        locked_request.save(
                            update_fields=[
                                "status",
                                "approval_stage",
                                "rejection_reason",
                                "updated_at",
                            ]
                        )

                        LeaveApproval.objects.create(
                            leave_request=locked_request,
                            stage=LeaveApproval.Stage.MANAGER,
                            action=LeaveApproval.Action.REJECTED,
                            acted_by=employee,
                            reason=reason,
                        )

                    messages.error(
                        request,
                        "Leave rejected by Manager.",
                    )

                    return redirect(
                        "leave_detail",
                        pk=pk,
                    )

            # ==========================================
            # MANAGER → HR → FINAL
            # ==========================================

            if (
                leave_request.approval_stage
                == LeaveRequest.ApprovalStage.HR_ADMIN
            ):

                # --------------------------------------
                # ONLY HR ADMIN
                # --------------------------------------

                if employee.role != Employee.Role.HR_ADMIN:

                    messages.error(
                        request,
                        "Only HR Admin can review this leave.",
                    )

                    return redirect(
                        "leave_detail",
                        pk=pk,
                    )

                # --------------------------------------
                # HR APPROVES ONLY MANAGER LEAVE
                # --------------------------------------

                if (
                    leave_request.employee.role
                    != Employee.Role.MANAGER
                ):

                    messages.error(
                        request,
                        "HR approval is currently applicable only to Manager leave requests.",
                    )

                    return redirect(
                        "leave_detail",
                        pk=pk,
                    )

                # --------------------------------------
                # SAME COMPANY CHECK
                # --------------------------------------

                if (
                    leave_request.employee.company_id
                    != employee.company_id
                ):

                    messages.error(
                        request,
                        "You are not authorized to review leave from another company.",
                    )

                    return redirect(
                        "leave_detail",
                        pk=pk,
                    )

                # ======================================
                # HR APPROVE → FINAL
                # ======================================

                if action == "APPROVE":

                    try:

                        with transaction.atomic():

                            locked_request = (
                                LeaveRequest.objects
                                .select_for_update()
                                .select_related(
                                    "employee",
                                    "leave_type",
                                )
                                .get(
                                    pk=pk
                                )
                            )

                            if locked_request.is_finalized:

                                messages.error(
                                    request,
                                    "This leave was already finalized.",
                                )

                                return redirect(
                                    "leave_detail",
                                    pk=pk,
                                )

                            if (
                                locked_request.status
                                != LeaveRequest.Status.PENDING
                            ):

                                messages.error(
                                    request,
                                    "This leave request is no longer pending.",
                                )

                                return redirect(
                                    "leave_detail",
                                    pk=pk,
                                )

                            if (
                                locked_request.approval_stage
                                != LeaveRequest.ApprovalStage.HR_ADMIN
                            ):

                                messages.error(
                                    request,
                                    "This leave is no longer waiting for HR approval.",
                                )

                                return redirect(
                                    "leave_detail",
                                    pk=pk,
                                )

                            locked_request.status = (
                                LeaveRequest.Status.APPROVED
                            )

                            locked_request.approved_by = employee

                            locked_request.approved_at = (
                                timezone.now()
                            )

                            locked_request.approval_stage = None

                            locked_request.rejection_reason = ""

                            locked_request.save(
                                update_fields=[
                                    "status",
                                    "approved_by",
                                    "approved_at",
                                    "approval_stage",
                                    "rejection_reason",
                                    "updated_at",
                                ]
                            )

                            LeaveApproval.objects.create(
                                leave_request=locked_request,
                                stage=LeaveApproval.Stage.HR_ADMIN,
                                action=LeaveApproval.Action.APPROVED,
                                acted_by=employee,
                                reason=reason,
                            )

                            deduct_leave_balance(
                                locked_request
                            )

                    except ValueError as exc:

                        messages.error(
                            request,
                            str(exc),
                        )

                        return redirect(
                            "leave_detail",
                            pk=pk,
                        )

                    messages.success(
                        request,
                        "Manager leave finally approved by HR Admin.",
                    )

                    return redirect(
                        "leave_detail",
                        pk=pk,
                    )

                # ======================================
                # HR REJECT → FINAL
                # ======================================

                if action == "REJECT":

                    with transaction.atomic():

                        locked_request = (
                            LeaveRequest.objects
                            .select_for_update()
                            .get(
                                pk=pk
                            )
                        )

                        if locked_request.is_finalized:

                            messages.error(
                                request,
                                "This leave was already finalized.",
                            )

                            return redirect(
                                "leave_detail",
                                pk=pk,
                            )

                        if (
                            locked_request.status
                            != LeaveRequest.Status.PENDING
                        ):

                            messages.error(
                                request,
                                "This leave request is no longer pending.",
                            )

                            return redirect(
                                "leave_detail",
                                pk=pk,
                            )

                        if (
                            locked_request.approval_stage
                            != LeaveRequest.ApprovalStage.HR_ADMIN
                        ):

                            messages.error(
                                request,
                                "This leave is no longer waiting for HR approval.",
                            )

                            return redirect(
                                "leave_detail",
                                pk=pk,
                            )

                        locked_request.status = (
                            LeaveRequest.Status.REJECTED
                        )

                        locked_request.approval_stage = None

                        locked_request.rejection_reason = reason

                        locked_request.save(
                            update_fields=[
                                "status",
                                "approval_stage",
                                "rejection_reason",
                                "updated_at",
                            ]
                        )

                        LeaveApproval.objects.create(
                            leave_request=locked_request,
                            stage=LeaveApproval.Stage.HR_ADMIN,
                            action=LeaveApproval.Action.REJECTED,
                            acted_by=employee,
                            reason=reason,
                        )

                    messages.error(
                        request,
                        "Manager leave rejected by HR Admin.",
                    )

                    return redirect(
                        "leave_detail",
                        pk=pk,
                    )

            # ==========================================
            # FUTURE / DISABLED APPROVAL STAGE
            # ==========================================

            messages.error(
                request,
                "This leave approval workflow is currently unavailable.",
            )

            return redirect(
                "leave_detail",
                pk=pk,
            )

    else:

        form = LeaveApprovalForm()

        form.fields["action"].choices = [
            ("APPROVE", "Approve"),
            ("REJECT", "Reject"),
        ]

    return render(
        request,
        "leave/leave_approval.html",
        {
            "form": form,
            "leave_request": leave_request,
        },
    )


@login_required
def leave_balance(request):

    year = int(
        request.GET.get(
            "year",
            timezone.localdate().year,
        )
    )

    balances = LeaveBalance.objects.select_related(
        "employee",
        "leave_type",
    ).filter(
        year=year
    )

    return render(
        request,
        "leave/leave_balance.html",
        {
            "balances": balances,
            "year": year,
        },
    )


@login_required
def leave_balance_create(request):

    if request.method == "POST":

        form = LeaveBalanceForm(
            request.POST
        )

        if form.is_valid():

            form.save()

            messages.success(
                request,
                "Leave balance created successfully.",
            )

            return redirect(
                "leave_balance"
            )

    else:

        form = LeaveBalanceForm(
            initial={
                "year": timezone.localdate().year,
            }
        )

    return render(
        request,
        "leave/leave_form.html",
        {
            "form": form,
            "title": "Add Leave Balance",
            "button_text": "Save Balance",
        },
    )


@login_required
def leave_calendar(request):

    employee = get_object_or_404(
        Employee.objects.select_related(
            "company",
            "department",
        ),
        user=request.user,
    )

    year = int(
        request.GET.get(
            "year",
            timezone.localdate().year,
        )
    )

    month = int(
        request.GET.get(
            "month",
            timezone.localdate().month,
        )
    )

    requests = get_visible_leave_requests(
        employee
    ).filter(
        start_date__year=year,
        start_date__month=month,
    ).exclude(
        status=LeaveRequest.Status.REJECTED
    )

    return render(
        request,
        "leave/leave_calendar.html",
        {
            "leave_requests": requests,
            "year": year,
            "month": month,
        },
    )


@login_required
def leave_types(request):

    types = LeaveType.objects.all()

    return render(
        request,
        "leave/leave_types.html",
        {
            "leave_types": types,
        },
    )


@login_required
def leave_type_create(request):

    if request.method == "POST":

        form = LeaveTypeForm(
            request.POST
        )

        if form.is_valid():

            form.save()

            messages.success(
                request,
                "Leave type created successfully.",
            )

            return redirect(
                "leave_types"
            )

    else:

        form = LeaveTypeForm()

    return render(
        request,
        "leave/leave_type_form.html",
        {
            "form": form,
            "title": "Add Leave Type",
            "button_text": "Create Leave Type",
        },
    )


@login_required
def leave_type_update(request, pk):

    leave_type = get_object_or_404(
        LeaveType,
        pk=pk,
    )

    if request.method == "POST":

        form = LeaveTypeForm(
            request.POST,
            instance=leave_type,
        )

        if form.is_valid():

            form.save()

            messages.success(
                request,
                "Leave type updated successfully.",
            )

            return redirect(
                "leave_types"
            )

    else:

        form = LeaveTypeForm(
            instance=leave_type
        )

    return render(
        request,
        "leave/leave_type_form.html",
        {
            "form": form,
            "leave_type": leave_type,
            "title": "Edit Leave Type",
            "button_text": "Update Leave Type",
        },
    )


@login_required
def leave_report(request):

    employee = get_object_or_404(
        Employee.objects.select_related(
            "company",
            "department",
        ),
        user=request.user,
    )

    requests = get_visible_leave_requests(
        employee
    )

    # ------------------------------------------
    # HR → COMPANY INFORMATION
    # ------------------------------------------

    if employee.role == Employee.Role.HR_ADMIN:

        requests = requests.filter(
            employee__company_id=employee.company_id,
        )

    approved = requests.filter(
        status=LeaveRequest.Status.APPROVED
    )

    pending = requests.filter(
        status=LeaveRequest.Status.PENDING
    )

    rejected = requests.filter(
        status=LeaveRequest.Status.REJECTED
    )

    return render(
        request,
        "leave/leave_report.html",
        {
            "requests": requests,
            "approved": approved,
            "pending": pending,
            "rejected": rejected,
        },
    )


@login_required
@require_POST
def leave_cancel(request, pk):
    """
    Cancel the current user's own pending leave request.
    """

    employee = get_current_employee(
        request.user
    )

    leave_request = get_object_or_404(
        LeaveRequest.objects.select_related(
            "employee",
            "leave_type",
        ),
        pk=pk,
    )

    if not employee:

        messages.error(
            request,
            "Employee profile not found.",
        )

        return redirect(
            "leave_dashboard"
        )

    # ------------------------------------------
    # ONLY OWNER CAN CANCEL
    # ------------------------------------------

    if leave_request.employee_id != employee.pk:

        messages.error(
            request,
            "You can cancel only your own leave requests.",
        )

        return redirect(
            "leave_list"
        )

    # ------------------------------------------
    # ONLY PENDING REQUEST
    # ------------------------------------------

    if leave_request.status != LeaveRequest.Status.PENDING:

        messages.error(
            request,
            "Only pending leave requests can be cancelled.",
        )

        return redirect(
            "leave_detail",
            pk=leave_request.pk,
        )

    if leave_request.is_finalized:

        messages.error(
            request,
            "This leave request has already been finalized.",
        )

        return redirect(
            "leave_detail",
            pk=leave_request.pk,
        )

    # ------------------------------------------
    # APPROVAL HISTORY STAGE
    # ------------------------------------------

    history_stage = leave_request.approval_stage

    if history_stage is None:

        if employee.role == Employee.Role.MANAGER:

            history_stage = (
                LeaveRequest.ApprovalStage.HR_ADMIN
            )

        elif employee.role == Employee.Role.HR_ADMIN:

            history_stage = (
                LeaveRequest.ApprovalStage.HR_ADMIN
            )

        else:

            history_stage = (
                LeaveRequest.ApprovalStage.MANAGER
            )

    # ------------------------------------------
    # CANCEL REQUEST
    # ------------------------------------------

    with transaction.atomic():

        leave_request.status = (
            LeaveRequest.Status.CANCELLED
        )

        leave_request.approval_stage = None

        leave_request.rejection_reason = (
            "Cancelled by employee."
        )

        leave_request.save(
            update_fields=[
                "status",
                "approval_stage",
                "rejection_reason",
                "updated_at",
            ]
        )

        LeaveApproval.objects.create(
            leave_request=leave_request,
            stage=history_stage,
            action=LeaveApproval.Action.CANCELLED,
            acted_by=employee,
            reason="Leave request cancelled by the requester.",
        )

    messages.success(request,
        "Leave request cancelled successfully.",
    )

    return redirect("leave_detail",pk=leave_request.pk,)