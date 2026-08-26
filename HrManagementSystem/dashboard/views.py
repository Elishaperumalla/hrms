from django.shortcuts import render

# Create your views here.
from django.contrib.auth.decorators import login_required


@login_required
def dashboard(request):

    user = request.user

    if user.is_superuser or user.role == "SUPER_ADMIN":
        template = "dashboard/admin_dashboard.html"

    elif user.role == "HR_ADMIN":
        template = "dashboard/hr_dashboard.html"

    elif user.role == "MANAGER":
        template = "dashboard/manager_dashboard.html"

    elif user.role == "RECRUITER":
        template = "dashboard/recruiter_dashboard.html"

    elif user.role == "PAYROLL_ADMIN":
        template = "dashboard/payroll_dashboard.html"

    else:
        template = "dashboard/employee_dashboard.html"

    context = {
        "user": user,
    }

    return render(request, template, context)