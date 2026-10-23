
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.db import transaction
from django.http import HttpResponseForbidden
from django.shortcuts import get_object_or_404, redirect, render
from django.utils import timezone
from django.views.decorators.clickjacking import xframe_options_sameorigin
from django.views.decorators.http import require_POST
from employees.models import Employee
from organization.models import Branch, Department

from .models import Conversation, ConversationMember, MessageReceipt


def get_employee(user):
    try:
        return user.employee_profile
    except Employee.DoesNotExist:
        return None


def active_company_employees(company):
    return Employee.objects.filter(
        company=company,
        employment_status=Employee.EmploymentStatus.ACTIVE,
        user__isnull=False,
        user__is_active=True,
    ).select_related("user")


def user_can_chat_with(user, other_user):
    if user == other_user:
        return False

    employee = get_employee(user)
    other_employee = get_employee(other_user)

    if not employee or not other_employee:
        return False

    return (
        employee.company_id is not None
        and employee.company_id == other_employee.company_id
        and employee.employment_status == Employee.EmploymentStatus.ACTIVE
        and other_employee.employment_status == Employee.EmploymentStatus.ACTIVE
        and other_user.is_active
    )


@login_required
def chat_home(request):
    employee = get_employee(request.user)

    if not employee or not employee.company_id:
        return render(request, "chat/chat_home.html", {
            "employee": employee,
            "conversations": [],
            "employees": [],
            "error": "Your account must be linked to an active company employee.",
        })

    memberships = (
        ConversationMember.objects
        .filter(user=request.user)
        .select_related(
            "conversation",
            "conversation__company",
            "conversation__department",
            "conversation__branch",
        )
    )

    conversations = [membership.conversation for membership in memberships]

    for conversation in conversations:

        # INDIVIDUAL CHAT: show the other employee's name
        if conversation.chat_type == Conversation.ChatType.INDIVIDUAL:
            other_member = (
                conversation.memberships
                .exclude(user=request.user)
                .select_related("user")
                .first()
            )

            if other_member:
                other_user = other_member.user

                conversation.display_name = (
                    other_user.get_full_name().strip()
                    or other_user.username
                    or other_user.email
                )
            else:
                conversation.display_name = "Individual Chat"

        # GROUP / DEPARTMENT / BRANCH / COMPANY CHAT
        else:
            conversation.display_name = (
                conversation.name
                or (
                    f"{conversation.department.name} Department"
                    if conversation.department_id
                    else None
                )
                or (
                    f"{conversation.branch.name} Branch"
                    if conversation.branch_id
                    else None
                )
                or f"{conversation.get_chat_type_display()} Chat"
            )

        # Latest message preview
        conversation.last_message = (
            conversation.messages
            .select_related("sender")
            .order_by("-created_at")
            .first()
        )

    # Latest active conversations first
    conversations.sort(
        key=lambda conversation: (
            conversation.last_message.created_at
            if conversation.last_message
            else conversation.created_at
        ),
        reverse=True,
    )

    employees = (
        active_company_employees(employee.company)
        .exclude(user=request.user)
        .order_by("first_name", "last_name")
    )

    return render(request, "chat/chat_home.html", {
        "employee": employee,
        "conversations": conversations,
        "employees": employees,
    })



@login_required
def create_conversation_page(request):
    employee = get_employee(request.user)

    if (
        not employee
        or not employee.company_id
        or employee.employment_status != Employee.EmploymentStatus.ACTIVE
    ):
        return HttpResponseForbidden(
            "Active company employee access required."
        )

    employees = active_company_employees(
        employee.company
    ).exclude(
        user=request.user
    ).order_by("first_name", "last_name")

    departments = Department.objects.filter(
        company=employee.company,
        is_active=True,
    ).order_by("name")

    branches = Branch.objects.filter(
        company=employee.company,
        is_active=True,
    ).order_by("name")

    return render(request, "chat/chat_create.html", {
        "employee": employee,
        "employees": employees,
        "departments": departments,
        "branches": branches,
    })


@login_required
@require_POST
@transaction.atomic
def create_conversation(request):
    employee = get_employee(request.user)

    if (
        not employee
        or not employee.company_id
        or employee.employment_status != Employee.EmploymentStatus.ACTIVE
    ):
        return HttpResponseForbidden(
            "Active company employee access required."
        )

    chat_type = request.POST.get("chat_type", "").upper()
    company = employee.company
    conversation = None

    if chat_type == Conversation.ChatType.INDIVIDUAL:
        try:
            other_user_id = int(request.POST.get("user_id", ""))
        except (ValueError, TypeError):
            messages.error(request, "Please select an employee.")
            return redirect("chat:create")

        other_employee = get_object_or_404(
            active_company_employees(company),
            user_id=other_user_id,
        )

        if not user_can_chat_with(request.user, other_employee.user):
            return HttpResponseForbidden(
                "You cannot chat with this employee."
            )

        conversation = (
            Conversation.objects.filter(
                chat_type=Conversation.ChatType.INDIVIDUAL,
                company=company,
                memberships__user=request.user,
            )
            .filter(memberships__user=other_employee.user)
            .distinct()
            .first()
        )

        if not conversation:
            conversation = Conversation.objects.create(
                chat_type=chat_type,
                company=company,
                created_by=request.user,
            )

            ConversationMember.objects.bulk_create([
                ConversationMember(
                    conversation=conversation,
                    user=request.user,
                ),
                ConversationMember(
                    conversation=conversation,
                    user=other_employee.user,
                ),
            ])

    elif chat_type == Conversation.ChatType.TEAM:
        selected_ids = list(set(request.POST.getlist("user_ids")))

        selected_employees = list(
            active_company_employees(company).filter(
                user_id__in=selected_ids
            )
        )

        if not selected_employees:
            messages.error(
                request,
                "Select at least one employee for the team chat.",
            )
            return redirect("chat:create")

        name = request.POST.get("name", "").strip()[:150]

        if not name:
            messages.error(request, "Enter a team chat name.")
            return redirect("chat:create")

        conversation = Conversation.objects.create(
            chat_type=chat_type,
            name=name,
            company=company,
            created_by=request.user,
        )

        member_ids = {request.user.pk}
        member_ids.update(emp.user_id for emp in selected_employees)

        ConversationMember.objects.bulk_create([
            ConversationMember(
                conversation=conversation,
                user_id=user_id,
            )
            for user_id in member_ids
        ])

    elif chat_type == Conversation.ChatType.DEPARTMENT:
        if not employee.department_id:
            messages.error(
                request,
                "Your employee profile has no department assigned.",
            )
            return redirect("chat:create")

        department = get_object_or_404(
            Department,
            pk=employee.department_id,
            company=company,
            is_active=True,
        )

        conversation = Conversation.objects.filter(
            chat_type=chat_type,
            company=company,
            department=department,
        ).first()

        if not conversation:
            conversation = Conversation.objects.create(
                chat_type=chat_type,
                name=f"{department.name} Department",
                company=company,
                department=department,
                created_by=request.user,
            )

            member_ids = active_company_employees(company).filter(
                department=department
            ).values_list("user_id", flat=True)

            ConversationMember.objects.bulk_create([
                ConversationMember(
                    conversation=conversation,
                    user_id=user_id,
                )
                for user_id in member_ids
            ], ignore_conflicts=True)

    elif chat_type == Conversation.ChatType.BRANCH:
        if not employee.branch_id:
            messages.error(
                request,
                "Your employee profile has no branch assigned.",
            )
            return redirect("chat:create")

        branch = get_object_or_404(
            Branch,
            pk=employee.branch_id,
            company=company,
            is_active=True,
        )

        conversation = Conversation.objects.filter(
            chat_type=chat_type,
            company=company,
            branch=branch,
        ).first()

        if not conversation:
            conversation = Conversation.objects.create(
                chat_type=chat_type,
                name=f"{branch.name} Branch",
                company=company,
                branch=branch,
                created_by=request.user,
            )

            member_ids = active_company_employees(company).filter(
                branch=branch
            ).values_list("user_id", flat=True)

            ConversationMember.objects.bulk_create([
                ConversationMember(
                    conversation=conversation,
                    user_id=user_id,
                )
                for user_id in member_ids
            ], ignore_conflicts=True)

    elif chat_type == Conversation.ChatType.COMPANY:
        conversation = Conversation.objects.filter(
            chat_type=chat_type,
            company=company,
        ).first()

        if not conversation:
            conversation = Conversation.objects.create(
                chat_type=chat_type,
                name=f"{company.name} Company Chat",
                company=company,
                created_by=request.user,
            )

            member_ids = active_company_employees(
                company
            ).values_list("user_id", flat=True)

            ConversationMember.objects.bulk_create([
                ConversationMember(
                    conversation=conversation,
                    user_id=user_id,
                )
                for user_id in member_ids
            ], ignore_conflicts=True)

    else:
        messages.error(request, "Please select a valid chat type.")
        return redirect("chat:create")

    if conversation:
        ConversationMember.objects.get_or_create(
            conversation=conversation,
            user=request.user,
        )

        return redirect(
            "chat:room",
            conversation_id=conversation.pk,
        )

    messages.error(request, "Could not create the conversation.")
    return redirect("chat:create")

@login_required
@xframe_options_sameorigin
def chat_room(request, conversation_id):
    membership = ConversationMember.objects.filter(
        conversation_id=conversation_id,
        user=request.user,
    ).select_related("conversation").first()

    if not membership:
        return HttpResponseForbidden(
            "You are not a member of this conversation."
        )

    conversation = membership.conversation

    membership.last_read_at = timezone.now()
    membership.save(update_fields=["last_read_at"])

    other_members = conversation.memberships.exclude(
        user=request.user
    ).select_related("user")

    if conversation.chat_type == Conversation.ChatType.INDIVIDUAL:
        other = other_members.first()
        title = (
            other.user.get_full_name() or other.user.username
        ) if other else "Individual chat"
    else:
        title = (
            conversation.name
            or conversation.get_chat_type_display()
        )

    chat_messages = list(
        conversation.messages.select_related("sender","reply_to__sender","forwarded_from__sender",)
        .order_by("-created_at")[:100]
    )
    chat_messages.reverse()
        # Load delivery/read status for messages sent by the current user.
    own_message_ids = [
        message.id
        for message in chat_messages
        if message.sender_id == request.user.id
    ]

    receipts = MessageReceipt.objects.filter(
        message_id__in=own_message_ids
    ).values(
        "message_id",
        "delivered_at",
        "read_at",
    )

    status_by_message = {}

    for receipt in receipts:
        message_id = receipt["message_id"]

        if receipt["read_at"]:
            status_by_message[message_id] = "read"
        elif receipt["delivered_at"]:
            status_by_message.setdefault(message_id, "delivered")
        else:
            status_by_message.setdefault(message_id, "sent")

    for message in chat_messages:
        message.receipt_status = status_by_message.get(
            message.id, "sent"
        )

    
    # Prepare other conversations available for forwarding.
    forward_conversations = []

    employee = get_employee(request.user)

    if employee and employee.company_id:
        memberships = (
            ConversationMember.objects
            .filter(
                user=request.user,
                conversation__company_id=employee.company_id,
            )
            .exclude(conversation_id=conversation.pk)
            .select_related(
                "conversation",
                "conversation__department",
                "conversation__branch",
            )
            .prefetch_related(
                "conversation__memberships__user",
            )
        )

        for membership in memberships:
            target = membership.conversation

            if target.chat_type == Conversation.ChatType.INDIVIDUAL:
                other_members = target.memberships.exclude(
                    user=request.user
                ).select_related("user")

                other_member = other_members.first()

                if other_member:
                    target_title = (
                        other_member.user.get_full_name()
                        or other_member.user.username
                    )
                else:
                    target_title = target.name or "Individual chat"

            elif target.name:
                target_title = target.name

            elif (
                target.chat_type == Conversation.ChatType.DEPARTMENT
                and target.department
            ):
                target_title = target.department.name

            elif (
                target.chat_type == Conversation.ChatType.BRANCH
                and target.branch
            ):
                target_title = target.branch.name

            else:
                target_title = target.get_chat_type_display()

            forward_conversations.append({
                "id": target.pk,
                "title": target_title,
            })


    context = {
        "conversation": conversation,
        "chat_title": title,
        "chat_messages": chat_messages,
        "other_members": other_members,
        "forward_conversations": forward_conversations,
    }


    return render(request, "chat/chat_room.html", context)