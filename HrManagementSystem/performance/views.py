
from functools import wraps

from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.core.exceptions import PermissionDenied
from django.db.models import Avg, Count
from django.shortcuts import get_object_or_404, redirect, render

from .forms import PerformanceReviewForm
from .models import PerformanceReview


def hr_or_manager_required(view_func):
    @wraps(view_func)
    def wrapper(request, *args, **kwargs):
        user = request.user
        role = getattr(user, "role", "")
        allowed_roles = {"SUPER_ADMIN", "HR_ADMIN", "MANAGER"}

        if not user.is_authenticated:
            return redirect("login")

        if not (user.is_superuser or user.is_staff or role in allowed_roles):
            raise PermissionDenied("You do not have permission to manage performance reviews.")

        return view_func(request, *args, **kwargs)
    return wrapper


@login_required
@hr_or_manager_required
def dashboard(request):
    reviews = PerformanceReview.objects.select_related("employee", "reviewer")
    stats = reviews.aggregate(
        total=Count("id"),
        completed=Count("id", filter=__import__(
            "django.db.models", fromlist=["Q"]
        ).Q(status="COMPLETED")),
        pending=Count("id", filter=__import__(
            "django.db.models", fromlist=["Q"]
        ).Q(status="PENDING")),
        average_rating=Avg("rating"),
    )

    recent_reviews = reviews[:8]
    status_data = [
        {"label": label, "count": reviews.filter(status=value).count()}
        for value, label in PerformanceReview.Status.choices
    ]

    return render(request, "performance/dashboard.html", {
        "stats": stats,
        "recent_reviews": recent_reviews,
        "status_data": status_data,
    })


@login_required
@hr_or_manager_required
def review_list(request):
    reviews = PerformanceReview.objects.select_related("employee", "reviewer")
    status = request.GET.get("status", "")
    search = request.GET.get("q", "").strip()

    if status in dict(PerformanceReview.Status.choices):
        reviews = reviews.filter(status=status)

    if search:
        reviews = reviews.filter(employee__first_name__icontains=search) if False else reviews
        # Search by review title; employee-name fields differ between projects.
        from django.db.models import Q
        reviews = reviews.filter(
            Q(review_title__icontains=search) |
            Q(goals__icontains=search)
        )

    return render(request, "performance/review_list.html", {
        "reviews": reviews,
        "status_choices": PerformanceReview.Status.choices,
        "selected_status": status,
        "search_query": search,
    })


@login_required
@hr_or_manager_required
def review_create(request):
    form = PerformanceReviewForm(request.POST or None)
    if request.method == "POST" and form.is_valid():
        review = form.save(commit=False)
        review.reviewer = request.user
        review.save()
        messages.success(request, "Performance review created successfully.")
        return redirect("performance:review_detail", pk=review.pk)

    return render(request, "performance/review_form.html", {
        "form": form,
        "page_title": "Create Performance Review",
    })


@login_required
@hr_or_manager_required
def review_update(request, pk):
    review = get_object_or_404(PerformanceReview, pk=pk)
    form = PerformanceReviewForm(request.POST or None, instance=review)

    if request.method == "POST" and form.is_valid():
        review = form.save(commit=False)
        review.reviewer = request.user
        review.save()
        messages.success(request, "Performance review updated successfully.")
        return redirect("performance:review_detail", pk=review.pk)

    return render(request, "performance/review_form.html", {
        "form": form,
        "page_title": "Update Performance Review",
    })


@login_required
@hr_or_manager_required
def review_detail(request, pk):
    review = get_object_or_404(
        PerformanceReview.objects.select_related("employee", "reviewer"),
        pk=pk,
    )
    return render(request, "performance/review_detail.html", {"review": review})
