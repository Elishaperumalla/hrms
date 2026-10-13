
import csv

from django.apps import apps
from django.contrib.auth.decorators import login_required
from django.core.exceptions import PermissionDenied
from django.http import HttpResponse
from django.shortcuts import render


# Candidate model names are checked against the models actually installed.
MODEL_OPTIONS = {
    "employees": ("employees", ("Employee",)),
    "attendance": ("attendance", ("Attendance",)),
    "leaves": ("leaves", ("LeaveRequest", "LeaveApplication", "Leave")),
    "recruitment": (
        "recruitment",
        ("CandidateApplication", "Candidate", "JobOpening"),
    ),
    "payroll": ("payroll", ("Payroll", "Payslip", "SalarySlip")),
}


def _get_model(app_label, possible_names):
    try:
        app_config = apps.get_app_config(app_label)
    except LookupError:
        return None

    installed_models = {model.__name__: model for model in app_config.get_models()}
    for model_name in possible_names:
        if model_name in installed_models:
            return installed_models[model_name]
    return None


def _staff_allowed(user):
    role = getattr(user, "role", "")
    return user.is_superuser or user.is_staff or role in {
        "SUPER_ADMIN", "HR_ADMIN"
    }


def _report_data():
    result = {}
    for key, (app_label, model_names) in MODEL_OPTIONS.items():
        model = _get_model(app_label, model_names)
        result[key] = {
            "model": model,
            "count": model.objects.count() if model else None,
            "available": model is not None,
        }
    return result


@login_required
def dashboard(request):
    if not _staff_allowed(request.user):
        raise PermissionDenied("Only HR and administrators can access reports.")

    data = _report_data()
    chart_labels = []
    chart_values = []

    for key in ("employees", "attendance", "leaves", "recruitment", "payroll"):
        item = data[key]
        if item["available"]:
            chart_labels.append(key.title())
            chart_values.append(item["count"])

    return render(request, "reports/dashboard.html", {
        "report_data": data,
        "chart_labels": chart_labels,
        "chart_values": chart_values,
    })


@login_required
def export_csv(request, report_type):
    if not _staff_allowed(request.user):
        raise PermissionDenied("Only HR and administrators can export reports.")

    if report_type not in MODEL_OPTIONS:
        raise PermissionDenied("Unknown report type.")

    app_label, model_names = MODEL_OPTIONS[report_type]
    model = _get_model(app_label, model_names)

    if model is None:
        raise PermissionDenied(
            "The corresponding model was not found. Update MODEL_OPTIONS "
            "in report/views.py to match your app's model name."
        )

    response = HttpResponse(content_type="text/csv; charset=utf-8")
    response["Content-Disposition"] = (
        f'attachment; filename="{report_type}_report.csv"'
    )
    response.write("\ufeff")
    writer = csv.writer(response)

    fields = list(model._meta.concrete_fields)
    writer.writerow([field.verbose_name for field in fields])

    for obj in model.objects.all().iterator():
        writer.writerow([
            str(getattr(obj, field.attname, "") or "")
            for field in fields
        ])

    return response
