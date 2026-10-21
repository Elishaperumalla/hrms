
from functools import wraps

from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.core.exceptions import PermissionDenied
from django.db.models import Avg, Count, Q
from django.shortcuts import get_object_or_404, redirect, render
from employees.models import Employee
from .forms import (
    PerformanceReviewForm,
    PerformanceGoalForm,
    PerformanceAppraisalForm,
)
from .models import (
    PerformanceReview,
    PerformanceGoal,
    PerformanceAppraisal,
)


def hr_or_manager_required(view_func):
    @wraps(view_func)
    def wrapper(request, *args, **kwargs):
        user = request.user
        role = getattr(user, "role", "")

        allowed_roles = {
            "SUPER_ADMIN",
            "HR_ADMIN",
            "MANAGER",
        }

        if not user.is_authenticated:
            return redirect("login")

        if not (
            user.is_superuser
            or user.is_staff
            or role in allowed_roles
        ):
            raise PermissionDenied(
                "You do not have permission to manage performance records."
            )

        return view_func(request, *args, **kwargs)

    return wrapper


# --------------------------------------------------
# DASHBOARD
# --------------------------------------------------
@login_required
# @hr_or_manager_required
def dashboard(request):
    reviews = PerformanceReview.objects.select_related(
        "employee", "reviewer"
    )
    
    role =getattr(request.user, "role","")
    if role =="EMPLOYEE":
        try:
            employee = request.user.employee_profile
        except Employee.DoesNotExist:
            raise PermissionDenied("Your account is not linked to employee profile")
        reviews = reviews.filter(employee=employee)    
    stats = reviews.aggregate(
        total=Count("id"),
        completed=Count(
            "id",
            filter=Q(status="COMPLETED"),
        ),
        pending=Count(
            "id",
            filter=Q(status="PENDING"),
        ),
        average_rating=Avg("rating"),
    )

    recent_reviews = reviews[:8]

    status_data = [
        {
            "label": label,
            "count": reviews.filter(status=value).count(),
        }
        for value, label in PerformanceReview.Status.choices
    ]

    role = getattr(request.user, "role", "")

    can_manage = (
        request.user.is_superuser
        or request.user.is_staff
        or role in {"SUPER_ADMIN", "HR_ADMIN", "MANAGER"}
    )

    return render(
        request,
        "performance/dashboard.html",
        {
            "stats": stats,
            "recent_reviews": recent_reviews,
            "status_data": status_data,
            "can_manage": can_manage,
        },
    )

# --------------------------------------------------
# PERFORMANCE REVIEWS
# --------------------------------------------------

@login_required
# @hr_or_manager_required
def review_list(request):
    reviews = PerformanceReview.objects.select_related(
        "employee", "reviewer"
    )

    status = request.GET.get("status", "")
    search = request.GET.get("q", "").strip()

    if status in dict(PerformanceReview.Status.choices):
        reviews = reviews.filter(status=status)

    if search:
        reviews = reviews.filter(
            Q(review_title__icontains=search)
            | Q(goals__icontains=search)
            | Q(achievements__icontains=search)
            | Q(employee__first_name__icontains=search)
            | Q(employee__last_name__icontains=search)
        )

    return render(
        request,
        "performance/review_list.html",
        {
            "reviews": reviews,
            "status_choices": PerformanceReview.Status.choices,
            "selected_status": status,
            "search_query": search,
        },
    )


@login_required
@hr_or_manager_required
def review_create(request):
    form = PerformanceReviewForm(request.POST or None)

    if request.method == "POST" and form.is_valid():
        review = form.save(commit=False)
        review.reviewer = request.user
        review.save()

        messages.success(
            request,
            "Performance review created successfully.",
        )
        return redirect(
            "performance:review_detail",
            pk=review.pk,
        )

    return render(
        request,
        "performance/review_form.html",
        {
            "form": form,
            "page_title": "Create Performance Review",
        },
    )


@login_required
@hr_or_manager_required
def review_update(request, pk):
    review = get_object_or_404(
        PerformanceReview,
        pk=pk,
    )

    form = PerformanceReviewForm(
        request.POST or None,
        instance=review,
    )

    if request.method == "POST" and form.is_valid():
        review = form.save(commit=False)
        review.reviewer = request.user
        review.save()

        messages.success(
            request,
            "Performance review updated successfully.",
        )
        return redirect(
            "performance:review_detail",
            pk=review.pk,
        )

    return render(
        request,
        "performance/review_form.html",
        {
            "form": form,
            "page_title": "Update Performance Review",
        },
    )


@login_required
# @hr_or_manager_required
def review_detail(request, pk):
    review = get_object_or_404(
        PerformanceReview.objects.select_related(
            "employee", "reviewer"
        ),
        pk=pk,
    )

    return render(
        request,
        "performance/review_detail.html",
        {"review": review},
    )


# --------------------------------------------------
# PERFORMANCE GOALS
# --------------------------------------------------

@login_required
@hr_or_manager_required
def goal_list(request):
    goals = PerformanceGoal.objects.select_related("employee")

    status = request.GET.get("status", "")
    search = request.GET.get("q", "").strip()

    if status in dict(PerformanceGoal.Status.choices):
        goals = goals.filter(status=status)

    if search:
        goals = goals.filter(
            Q(title__icontains=search)
            | Q(description__icontains=search)
            | Q(employee__first_name__icontains=search)
            | Q(employee__last_name__icontains=search)
        )

    return render(
        request,
        "performance/goal_list.html",
        {
            "goals": goals,
            "status_choices": PerformanceGoal.Status.choices,
            "selected_status": status,
            "search_query": search,
        },
    )


@login_required
@hr_or_manager_required
def goal_create(request):
    form = PerformanceGoalForm(request.POST or None)

    if request.method == "POST" and form.is_valid():
        form.save()

        messages.success(
            request,
            "Performance goal created successfully.",
        )
        return redirect("performance:goal_list")

    return render(
        request,
        "performance/goal_form.html",
        {
            "form": form,
            "page_title": "Create Performance Goal",
        },
    )


@login_required
@hr_or_manager_required
def goal_update(request, pk):
    goal = get_object_or_404(
        PerformanceGoal,
        pk=pk,
    )

    form = PerformanceGoalForm(
        request.POST or None,
        instance=goal,
    )

    if request.method == "POST" and form.is_valid():
        form.save()

        messages.success(
            request,
            "Performance goal updated successfully.",
        )
        return redirect("performance:goal_list")

    return render(
        request,
        "performance/goal_form.html",
        {
            "form": form,
            "page_title": "Update Performance Goal",
        },
    )


# --------------------------------------------------
# PERFORMANCE APPRAISALS
# --------------------------------------------------

@login_required
@hr_or_manager_required
def appraisal_list(request):
    appraisals = PerformanceAppraisal.objects.select_related(
        "employee", "reviewer"
    )

    status = request.GET.get("status", "")
    search = request.GET.get("q", "").strip()

    if status in dict(PerformanceAppraisal.Status.choices):
        appraisals = appraisals.filter(status=status)

    if search:
        appraisals = appraisals.filter(
            Q(title__icontains=search)
            | Q(strengths__icontains=search)
            | Q(improvement_areas__icontains=search)
            | Q(employee__first_name__icontains=search)
            | Q(employee__last_name__icontains=search)
        )

    return render(
        request,
        "performance/appraisal_list.html",
        {
            "appraisals": appraisals,
            "status_choices": PerformanceAppraisal.Status.choices,
            "selected_status": status,
            "search_query": search,
        },
    )


@login_required
@hr_or_manager_required
def appraisal_create(request):
    form = PerformanceAppraisalForm(request.POST or None)

    if request.method == "POST" and form.is_valid():
        appraisal = form.save(commit=False)
        appraisal.reviewer = request.user
        appraisal.save()

        messages.success(
            request,
            "Performance appraisal created successfully.",
        )
        return redirect("performance:appraisal_list")

    return render(
        request,
        "performance/appraisal_form.html",
        {
            "form": form,
            "page_title": "Create Performance Appraisal",
        },
    )


# --------------------------------------------------
# PERFORMANCE REPORT
# --------------------------------------------------

@login_required
@hr_or_manager_required
def performance_report(request):
    reviews = PerformanceReview.objects.select_related("employee")

    total_reviews = reviews.count()
    completed_reviews = reviews.filter(
        status=PerformanceReview.Status.COMPLETED
    ).count()

    average_rating = reviews.aggregate(
        average=Avg("rating")
    )["average"]

    rating_breakdown = []

    for rating in range(5, 0, -1):
        count = reviews.filter(rating=rating).count()

        percentage = (
            round(count * 100 / total_reviews)
            if total_reviews
            else 0
        )

        rating_breakdown.append(
            {
                "rating": rating,
                "count": count,
                "percentage": percentage,
            }
        )

    status_breakdown = [
        {
            "label": label,
            "count": reviews.filter(status=value).count(),
        }
        for value, label in PerformanceReview.Status.choices
    ]

    return render(
        request,
        "performance/performance_report.html",
        {
            "total_reviews": total_reviews,
            "completed_reviews": completed_reviews,
            "average_rating": average_rating,
            "rating_breakdown": rating_breakdown,
            "status_breakdown": status_breakdown,
        },
    )
