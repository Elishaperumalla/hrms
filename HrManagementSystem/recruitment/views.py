
from functools import wraps

from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.core.paginator import Paginator
from django.db.models import Q, Count
from django.shortcuts import get_object_or_404, redirect, render

from .forms import CandidateApplicationForm, JobOpeningForm
from .models import CandidateApplication, JobOpening


def recruitment_staff_required(view_func):
    @wraps(view_func)
    @login_required
    def wrapper(request, *args, **kwargs):
        user = request.user
        role = getattr(user, "role", "")
        role = getattr(role, "value", role)
        role = str(role).upper()

        allowed = (
            user.is_superuser
            or user.is_staff
            or role in {"SUPER_ADMIN", "HR_ADMIN"}
        )

        if not allowed:
            messages.error(
                request,
                "You do not have permission to access Recruitment."
            )
            return redirect("dashboard")

        return view_func(request, *args, **kwargs)

    return wrapper


@recruitment_staff_required
def recruitment_dashboard(request):
    applications = CandidateApplication.objects.select_related("job")

    search = request.GET.get("q", "").strip()
    status = request.GET.get("status", "").strip()
    source = request.GET.get("source", "").strip()

    if search:
        applications = applications.filter(
            Q(candidate_name__icontains=search)
            | Q(email__icontains=search)
            | Q(phone__icontains=search)
            | Q(job__title__icontains=search)
        )

    valid_statuses = CandidateApplication.Status.values
    valid_sources = CandidateApplication.Source.values

    if status in valid_statuses:
        applications = applications.filter(status=status)

    if source in valid_sources:
        applications = applications.filter(source=source)

    paginator = Paginator(applications, 10)
    page_obj = paginator.get_page(request.GET.get("page"))

    context = {
        "page_obj": page_obj,
        "total_applications": CandidateApplication.objects.count(),
        "new_applications": CandidateApplication.objects.filter(
            status="NEW"
        ).count(),
        "shortlisted": CandidateApplication.objects.filter(
            status="SHORTLISTED"
        ).count(),
        "interviews": CandidateApplication.objects.filter(
            status="INTERVIEW"
        ).count(),
        "hired": CandidateApplication.objects.filter(status="HIRED").count(),
        "rejected": CandidateApplication.objects.filter(
            status="REJECTED"
        ).count(),
        "jobs": JobOpening.objects.all(),
        "status_choices": CandidateApplication.Status.choices,
        "source_choices": CandidateApplication.Source.choices,
        "selected_status": status,
        "selected_source": source,
        "search": search,
    }
    return render(request, "recruitment/dashboard.html", context)


@recruitment_staff_required
def application_create(request):
    if request.method == "POST":
        form = CandidateApplicationForm(
            request.POST, request.FILES
        )
        if form.is_valid():
            application = form.save()
            messages.success(
                request,
                f"Application for {application.candidate_name} was saved."
            )
            return redirect(
                "recruitment:application_detail",
                pk=application.pk,
            )
    else:
        form = CandidateApplicationForm()

    return render(
        request,
        "recruitment/application_form.html",
        {"form": form, "page_title": "Add Candidate"},
    )


@recruitment_staff_required
def application_detail(request, pk):
    application = get_object_or_404(
        CandidateApplication.objects.select_related("job"),
        pk=pk,
    )
    return render(
        request,
        "recruitment/application_detail.html",
        {"application": application,
          "status_choices": CandidateApplication.Status.choices,},
    )


@recruitment_staff_required
def application_update_status(request, pk):
    if request.method != "POST":
        return redirect("recruitment:application_detail", pk=pk)

    application = get_object_or_404(CandidateApplication, pk=pk)
    new_status = request.POST.get("status", "")

    if new_status not in CandidateApplication.Status.values:
        messages.error(request, "Please select a valid status.")
    else:
        application.status = new_status
        application.save(update_fields=["status", "updated_at"])
        messages.success(request, "Application status updated.")

    return redirect("recruitment:application_detail", pk=pk)


@recruitment_staff_required
def job_list(request):
    jobs = JobOpening.objects.annotate(
        application_count=Count("applications")
    )
    return render(request, "recruitment/job_list.html", {"jobs": jobs})


@recruitment_staff_required
def job_create(request):
    if request.method == "POST":
        form = JobOpeningForm(request.POST)
        if form.is_valid():
            form.save()
            messages.success(request, "Job opening created.")
            return redirect("recruitment:job_list")
    else:
        form = JobOpeningForm()

    return render(
        request,
        "recruitment/job_form.html",
        {"form": form, "page_title": "Create Job Opening"},
    )
