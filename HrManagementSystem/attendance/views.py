from decimal import Decimal, InvalidOperation
from calendar import monthrange
from datetime import date

from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.db.models import Count, Q, Sum
from django.http import HttpResponseNotAllowed
from django.shortcuts import get_object_or_404, redirect, render
from django.utils import timezone

from employees.models import Employee
from chat.presence import broadcast_user_presence

from .forms import AttendanceForm
from .models import Attendance

import calendar

from datetime import date
from attendance.holidays import (
    get_public_holidays,
    is_weekend,
)

# =========================================================
# ROLE HELPERS
# =========================================================

def get_user_role(user):
    return getattr(
        user,
        "role",
        None,
    )


def is_super_admin(user):
    return get_user_role(user) == "SUPER_ADMIN"


def is_hr_admin(user):
    return get_user_role(user) == "HR_ADMIN"


def is_manager(user):
    return get_user_role(user) == "MANAGER"


def is_employee(user):
    return get_user_role(user) == "EMPLOYEE"


# =========================================================
# CURRENT EMPLOYEE
# =========================================================

def get_current_employee(user):

    try:
        return user.employee_profile

    except Employee.DoesNotExist:
        return None


# =========================================================
# ATTENDANCE EMPLOYEE SCOPE
# =========================================================

def get_attendance_employee_scope(user):

    employees = Employee.objects.all()

    # -----------------------------------------------------
    # SUPER ADMIN
    # -----------------------------------------------------

    if is_super_admin(user):
        return employees

    current_employee = get_current_employee(user)

    if not current_employee:
        return employees.none()

    # -----------------------------------------------------
    # HR
    # -----------------------------------------------------

    if is_hr_admin(user):

        return employees.filter(
            company_id=current_employee.company_id
        )

    # -----------------------------------------------------
    # MANAGER
    # -----------------------------------------------------

    if is_manager(user):

        return employees.filter(
            Q(pk=current_employee.pk)
            |
            Q(
                reporting_manager=current_employee
            )
        )

    # -----------------------------------------------------
    # EMPLOYEE
    # -----------------------------------------------------

    if is_employee(user):

        return employees.filter(
            pk=current_employee.pk
        )

    return employees.none()


# =========================================================
# ATTENDANCE ACCESS
# =========================================================

def get_accessible_attendance(
    user,
    pk,
):

    employees = get_attendance_employee_scope(
        user
    )

    return get_object_or_404(
        Attendance.objects.select_related(
            "employee",
            "employee__company",
            "employee__department",
            "employee__designation",
            "employee__branch",
            "employee__work_location",
        ),
        pk=pk,
        employee__in=employees,
    )


# =========================================================
# PERMISSIONS
# =========================================================

def can_manage_attendance(user):

    return (
        is_super_admin(user)
        or is_hr_admin(user)
        or is_manager(user)
    )


def can_delete_attendance(user):

    return (
        is_super_admin(user)
        or is_hr_admin(user)
    )


# =========================================================
# DASHBOARD
# =========================================================

@login_required
def attendance_dashboard(request):

    today = timezone.localdate()

    employees = (
        get_attendance_employee_scope(
            request.user
        )
        .filter(
            employment_status=Employee.EmploymentStatus.ACTIVE
        )
    )

    total_employees = employees.count()

    today_records = (
        Attendance.objects
        .filter(
            date=today,
            employee__in=employees,
        )
        .select_related(
            "employee",
        )
    )

    present_today = today_records.filter(
        status=Attendance.Status.PRESENT
    ).count()

    absent_today = today_records.filter(
        status=Attendance.Status.ABSENT
    ).count()

    half_day_today = today_records.filter(
        status=Attendance.Status.HALF_DAY
    ).count()

    on_leave_today = today_records.filter(
        status=Attendance.Status.ON_LEAVE
    ).count()

    holiday_today = today_records.filter(
        status=Attendance.Status.HOLIDAY
    ).count()

    week_off_today = today_records.filter(
        status=Attendance.Status.WEEK_OFF
    ).count()

    late_today = today_records.filter(
        late_minutes__gt=0
    ).count()

    # -----------------------------------------------------
    # ATTENDANCE PERCENTAGE
    # -----------------------------------------------------

    attendance_percentage = 0

    if total_employees > 0:

        attendance_percentage = round(
            (
                present_today
                + (half_day_today * 0.5)
            )
            / total_employees
            * 100,
            2,
        )

    # -----------------------------------------------------
    # CURRENT USER TODAY RECORD
    # -----------------------------------------------------

    current_employee = get_current_employee(
        request.user
    )

    # Face registration reminder; Super Admin is exempt.
    face_registration_required = False
    if not (
        request.user.is_superuser
        or getattr(request.user, "role", "") == "SUPER_ADMIN"
    ):
        from account.models import EmployeeFaceProfile

        face_registration_required = not EmployeeFaceProfile.objects.filter(
            user=request.user,
            is_active=True,
        ).exists()

    today_attendance = None

    if current_employee:

        today_attendance = (
            Attendance.objects
            .filter(
                employee=current_employee,
                date=today,
            )
            .first()
        )

    # -----------------------------------------------------
    # RECENT RECORDS
    # -----------------------------------------------------

    recent_records = (
        Attendance.objects
        .filter(
            employee__in=employees
        )
        .select_related(
            "employee",
            "employee__department",
            "employee__designation",
        )
        .order_by(
            "-date",
            "-created_at",
        )[:10]
    )

    return render(
        request,
        "attendance/attendance_dashboard.html",
        {
            "today": today,
            "total_employees": total_employees,
            "present_today": present_today,
            "absent_today": absent_today,
            "half_day_today": half_day_today,
            "on_leave_today": on_leave_today,
            "holiday_today": holiday_today,
            "week_off_today": week_off_today,
            "late_today": late_today,
            "attendance_percentage": attendance_percentage,
            "today_attendance": today_attendance,
            "face_registration_required": face_registration_required,
            "recent_records": recent_records,
            "can_manage_attendance": can_manage_attendance(
                request.user
            ),
            "can_delete_attendance": can_delete_attendance(
                request.user
            ),
        },
    )


# =========================================================
# ATTENDANCE LIST
# =========================================================

@login_required
def attendance_list(request):

    employees = get_attendance_employee_scope(
        request.user
    )

    records = (
        Attendance.objects
        .filter(
            employee__in=employees
        )
        .select_related(
            "employee",
            "employee__department",
            "employee__designation",
        )
    )

    selected_date = request.GET.get(
        "date",
        ""
    ).strip()

    selected_status = request.GET.get(
        "status",
        ""
    ).strip()

    search = request.GET.get(
        "search",
        ""
    ).strip()

    # -----------------------------------------------------
    # DATE FILTER
    # -----------------------------------------------------

    if selected_date:

        records = records.filter(
            date=selected_date
        )

    # -----------------------------------------------------
    # STATUS FILTER
    # -----------------------------------------------------

    if selected_status:

        records = records.filter(
            status=selected_status
        )

    # -----------------------------------------------------
    # SEARCH
    # -----------------------------------------------------

    if search:

        records = records.filter(
            Q(
                employee__first_name__icontains=search
            )
            |
            Q(
                employee__last_name__icontains=search
            )
            |
            Q(
                employee__employee_id__icontains=search
            )
        )

    records = records.order_by(
        "-date",
        "employee__first_name",
        "employee__last_name",
    )

    return render(
        request,
        "attendance/attendance_list.html",
        {
            "records": records,
            "selected_date": selected_date,
            "selected_status": selected_status,
            "search": search,
            "status_choices": Attendance.Status.choices,
            "can_manage_attendance": can_manage_attendance(
                request.user
            ),
            "can_delete_attendance": can_delete_attendance(
                request.user
            ),
        },
    )


# =========================================================
# CREATE ATTENDANCE
# =========================================================

@login_required
def attendance_create(request):

    if not can_manage_attendance(
        request.user
    ):

        messages.error(
            request,
            "You are not authorized to create attendance records.",
        )

        return redirect(
            "attendance_list"
        )

    # -----------------------------------------------------
    # POST
    # -----------------------------------------------------

    if request.method == "POST":

        form = AttendanceForm(
            request.POST,
            request_user=request.user,
        )

        if form.is_valid():

            attendance = form.save()

            messages.success(
                request,
                "Attendance record created successfully.",
            )

            return redirect(
                "attendance_detail",
                pk=attendance.pk,
            )

    # -----------------------------------------------------
    # GET
    # -----------------------------------------------------

    else:

        initial = {}

        if request.GET.get("employee"):

            employee_id = request.GET.get(
                "employee"
            )

            try:

                employee = (
                    get_attendance_employee_scope(
                        request.user
                    )
                    .get(
                        pk=employee_id
                    )
                )

                initial["employee"] = employee.pk

            except Employee.DoesNotExist:
                pass

        if request.GET.get("date"):

            initial["date"] = request.GET.get(
                "date"
            )

        form = AttendanceForm(
            initial=initial,
            request_user=request.user,
        )

    return render(
        request,
        "attendance/attendance_form.html",
        {
            "form": form,
            "title": "Mark Attendance",
            "button_text": "Save Attendance",
            "is_edit": False,
        },
    )


# =========================================================
# ATTENDANCE DETAIL
# =========================================================

@login_required
def attendance_detail(request, pk):

    attendance = get_accessible_attendance(
        request.user,
        pk,
    )

    return render(
        request,
        "attendance/attendance_detail.html",
        {
            "attendance": attendance,
            "can_manage_attendance": can_manage_attendance(
                request.user
            ),
            "can_delete_attendance": can_delete_attendance(
                request.user
            ),
        },
    )


# =========================================================
# UPDATE ATTENDANCE
# =========================================================

@login_required
def attendance_update(request, pk):

    if not can_manage_attendance(
        request.user
    ):

        messages.error(
            request,
            "You are not authorized to edit attendance records.",
        )

        return redirect(
            "attendance_detail",
            pk=pk,
        )

    attendance = get_accessible_attendance(
        request.user,
        pk,
    )

    if request.method == "POST":

        form = AttendanceForm(
            request.POST,
            instance=attendance,
            request_user=request.user,
        )

        if form.is_valid():

            form.save()

            messages.success(
                request,
                "Attendance record updated successfully.",
            )

            return redirect(
                "attendance_detail",
                pk=attendance.pk,
            )

    else:

        form = AttendanceForm(
            instance=attendance,
            request_user=request.user,
        )

    return render(
        request,
        "attendance/attendance_form.html",
        {
            "form": form,
            "attendance": attendance,
            "title": "Edit Attendance",
            "button_text": "Update Attendance",
            "is_edit": True,
        },
    )


# =========================================================
# DELETE ATTENDANCE
# =========================================================

@login_required
def attendance_delete(request, pk):

    if not can_delete_attendance(
        request.user
    ):

        messages.error(
            request,
            "You are not authorized to delete attendance records.",
        )

        return redirect(
            "attendance_detail",
            pk=pk,
        )

    attendance = get_accessible_attendance(
        request.user,
        pk,
    )

    if request.method != "POST":

        return HttpResponseNotAllowed(
            ["POST"]
        )

    attendance.delete()

    messages.success(
        request,
        "Attendance record deleted successfully.",
    )

    return redirect(
        "attendance_list"
    )


# =========================================================
# CALENDAR
# =========================================================

@login_required
def attendance_calendar(request):

    today = timezone.localdate()

    try:
        year = int(request.GET.get("year", today.year))
        month = int(request.GET.get("month", today.month))
    except (TypeError, ValueError):
        year = today.year
        month = today.month

    if month < 1 or month > 12:
        month = today.month
        year = today.year

    first_day = date(year, month, 1)
    days_in_month = monthrange(year, month)[1]

    employees = (
        get_attendance_employee_scope(request.user)
        .filter(
            employment_status=Employee.EmploymentStatus.ACTIVE
        )
        .select_related("department", "designation")
        .order_by("first_name", "last_name")
    )

    records = (
        Attendance.objects.filter(
            employee__in=employees,
            date__year=year,
            date__month=month,
        )
        .select_related("employee")
    )

    attendance_map = {
        (record.employee_id, record.date.day): record
        for record in records
    }

    public_holidays = get_public_holidays(year)
    calendar_days = []

    for day_number in range(1, days_in_month + 1):
        current_date = date(year, month, day_number)

        holiday_name = public_holidays.get(current_date, "")
        weekend = is_weekend(current_date)

        calendar_days.append({
            "number": day_number,
            "date": current_date,
            "weekday": current_date.strftime("%a"),
            "is_today": current_date == today,
            "is_weekend": weekend,
            "is_holiday": bool(holiday_name),
            "holiday_name": holiday_name,
            "is_non_working_day": weekend or bool(holiday_name),
        })

    employee_rows = []

    for employee in employees:
        row = []

        for day in calendar_days:
            record = attendance_map.get(
                (employee.pk, day["number"])
            )

            row.append({
                "day": day,
                "record": record,
            })

        employee_rows.append({
            "employee": employee,
            "days": row,
        })

    return render(
        request,
        "attendance/attendance_calendar.html",
        {
            "year": year,
            "month": month,
            "month_name": first_day.strftime("%B"),
            "calendar_days": calendar_days,
            "employee_rows": employee_rows,
            "can_manage_attendance": can_manage_attendance(
                request.user
            ),
        },
    )

# =========================================================
# REPORT
# =========================================================

@login_required
def attendance_report(request):

    today = timezone.localdate()

    # -----------------------------------------------------
    # MONTH / YEAR
    # -----------------------------------------------------

    try:

        month = int(
            request.GET.get(
                "month",
                today.month,
            )
        )

        year = int(
            request.GET.get(
                "year",
                today.year,
            )
        )

    except (
        TypeError,
        ValueError,
    ):

        month = today.month
        year = today.year

    if month < 1 or month > 12:

        month = today.month

    # -----------------------------------------------------
    # EMPLOYEE SCOPE
    # -----------------------------------------------------

    employees = get_attendance_employee_scope(
        request.user
    )

    # -----------------------------------------------------
    # RECORDS
    # -----------------------------------------------------

    records = Attendance.objects.filter(
        employee__in=employees,
        date__year=year,
        date__month=month,
    )

    employee_id = request.GET.get(
        "employee"
    )

    # -----------------------------------------------------
    # EMPLOYEE FILTER
    # -----------------------------------------------------

    if employee_id:

        try:

            selected_employee = employees.get(
                pk=employee_id
            )

            records = records.filter(
                employee=selected_employee
            )

        except Employee.DoesNotExist:

            employee_id = ""

    # -----------------------------------------------------
    # SUMMARY
    # -----------------------------------------------------

    summary = (
        records
        .values(
            "employee",
            "employee__employee_id",
            "employee__first_name",
            "employee__last_name",
        )
        .annotate(

            total_days=Count("id"),

            present_days=Count(
                "id",
                filter=Q(
                    status=Attendance.Status.PRESENT
                ),
            ),

            absent_days=Count(
                "id",
                filter=Q(
                    status=Attendance.Status.ABSENT
                ),
            ),

            half_days=Count(
                "id",
                filter=Q(
                    status=Attendance.Status.HALF_DAY
                ),
            ),

            leave_days=Count(
                "id",
                filter=Q(
                    status=Attendance.Status.ON_LEAVE
                ),
            ),

            holiday_days=Count(
                "id",
                filter=Q(
                    status=Attendance.Status.HOLIDAY
                ),
            ),

            week_off_days=Count(
                "id",
                filter=Q(
                    status=Attendance.Status.WEEK_OFF
                ),
            ),

            late_days=Count(
                "id",
                filter=Q(
                    late_minutes__gt=0
                ),
            ),

            total_work_hours=Sum(
                "work_hours"
            ),

            total_overtime=Sum(
                "overtime_hours"
            ),
        )
        .order_by(
            "employee__first_name",
            "employee__last_name",
        )
    )

    # -----------------------------------------------------
    # EMPLOYEE DROPDOWN
    # -----------------------------------------------------

    report_employees = (
        employees
        .filter(
            employment_status=Employee.EmploymentStatus.ACTIVE
        )
        .order_by(
            "first_name",
            "last_name",
        )
    )

    return render(
        request,
        "attendance/attendance_report.html",
        {
            "summary": summary,
            "employees": report_employees,
            "selected_month": month,
            "selected_year": year,
            "selected_employee": employee_id,
            "month_name": date(
                year,
                month,
                1,
            ).strftime("%B"),
        },
    )


# =========================================================
# CLOCK IN
# =========================================================


# =========================================================
# GPS ATTENDANCE VALIDATION
# =========================================================


def _reverse_geocode_attendance(latitude, longitude):
    """Best-effort address lookup using OpenStreetMap Nominatim."""
    import json
    from urllib.parse import urlencode
    from urllib.request import Request, urlopen

    params = urlencode({
        "format": "jsonv2",
        "lat": str(latitude),
        "lon": str(longitude),
        "zoom": 18,
        "addressdetails": 1,
    })
    url = "https://nominatim.openstreetmap.org/reverse?" + params
    request_obj = Request(
        url,
        headers={
            "User-Agent": "VoiceOrbitHRMS/1.0 (attendance location lookup)"
        },
    )

    try:
        with urlopen(request_obj, timeout=3) as response:
            data = json.loads(response.read().decode("utf-8"))
        return (data.get("display_name") or "")[:2000]
    except Exception:
        # Attendance must still work if the free geocoding service is unavailable.
        return ""


def _validate_attendance_gps(request):
    from math import asin, cos, radians, sin, sqrt
    from organization.models import OfficeAttendanceSettings

    mode = (request.POST.get("attendance_mode") or "").strip().upper()
    if mode not in {"OFFICE", "OUTSIDE"}:
        return None, "Please select Office or Outside before continuing."

    try:
        latitude = Decimal(request.POST.get("latitude", ""))
        longitude = Decimal(request.POST.get("longitude", ""))
        accuracy = float(request.POST.get("accuracy", ""))
    except (InvalidOperation, TypeError, ValueError):
        return None, "Please verify your GPS location and try again."

    if not (Decimal("-90") <= latitude <= Decimal("90")):
        return None, "GPS latitude is invalid."
    if not (Decimal("-180") <= longitude <= Decimal("180")):
        return None, "GPS longitude is invalid."
    if accuracy < 0 or accuracy > 100:
        return None, "GPS accuracy is too low. Please retry in an open area."

    address = (request.POST.get("address") or "").strip()[:2000]

    if mode == "OFFICE":
        employee = get_current_employee(request.user)
        fence = None

        # Priority 1: the employee's assigned branch.
        if employee and employee.branch_id:
            branch = employee.branch
            if branch.latitude is not None and branch.longitude is not None:
                fence = (
                    branch.latitude,
                    branch.longitude,
                    branch.radius_meters,
                    f"branch {branch.name}",
                )

        # Priority 2: the employee's assigned company.
        if fence is None and employee and employee.company_id:
            company = employee.company
            if company.latitude is not None and company.longitude is not None:
                fence = (
                    company.latitude,
                    company.longitude,
                    company.radius_meters,
                    f"company {company.name}",
                )

        # Priority 3: legacy office settings for backward compatibility.
        if fence is None:
            settings_obj = OfficeAttendanceSettings.objects.filter(
                is_active=True
            ).first()
            if (
                settings_obj
                and settings_obj.latitude is not None
                and settings_obj.longitude is not None
            ):
                fence = (
                    settings_obj.latitude,
                    settings_obj.longitude,
                    settings_obj.radius_meters,
                    "configured office",
                )

        if fence is None:
            return None, (
                "Office GPS is not configured for your branch or company. "
                "Please contact your Super Admin."
            )

        fence_latitude, fence_longitude, radius_meters, fence_name = fence

        lat1, lon1 = radians(float(latitude)), radians(float(longitude))
        lat2, lon2 = radians(float(fence_latitude)), radians(float(fence_longitude))
        dlat, dlon = lat2 - lat1, lon2 - lon1
        haversine = (
            sin(dlat / 2) ** 2
            + cos(lat1) * cos(lat2) * sin(dlon / 2) ** 2
        )
        distance = 6371000 * 2 * asin(sqrt(min(1, haversine)))

        if distance > radius_meters:
            return None, (
                f"You are {round(distance)} metres from the {fence_name}. "
                f"Office attendance is allowed within {radius_meters} metres."
            )

    if not address:
        address = _reverse_geocode_attendance(latitude, longitude)

    return {
        "mode": mode,
        "latitude": latitude,
        "longitude": longitude,
        "accuracy": accuracy,
        "address": address,
    }, None


@login_required
def attendance_face_verify(request):
    import secrets
    import time
    from io import BytesIO

    from django.http import JsonResponse
    from PIL import Image
    from account.models import EmployeeFaceProfile
    from account.face_service import (
        FaceServiceError,
        extract_embedding,
        decrypt_embedding,
        compare_embeddings,
    )

    if request.method != "POST":
        return HttpResponseNotAllowed(["POST"])

    user = request.user
    action = (request.POST.get("action") or "").strip()
    if action not in {"clock-in", "clock-out"}:
        return JsonResponse({"ok": False, "message": "Invalid attendance action."}, status=400)

    employee = get_current_employee(user)
    if not employee:
        return JsonResponse({"ok": False, "message": "Your employee profile was not found."}, status=403)

    gps, gps_error = _validate_attendance_gps(request)
    if gps_error:
        return JsonResponse({"ok": False, "message": gps_error}, status=400)

    uploaded = request.FILES.get("face_image")
    if not uploaded:
        return JsonResponse({"ok": False, "message": "Capture a photo before continuing."}, status=400)
    if uploaded.size > 5 * 1024 * 1024:
        return JsonResponse({"ok": False, "message": "Photo must be 5 MB or smaller."}, status=400)

    image_bytes = uploaded.read()
    try:
        with Image.open(BytesIO(image_bytes)) as image:
            image.verify()
    except Exception:
        return JsonResponse({"ok": False, "message": "The captured photo is not a valid image."}, status=400)

    is_super_admin = user.is_superuser or getattr(user, "role", "") == "SUPER_ADMIN"

    if not is_super_admin:
        profile = EmployeeFaceProfile.objects.filter(user=user, is_active=True).first()
        if not profile:
            return JsonResponse({
                "ok": False,
                "message": "Face registration is required before attendance.",
                "registration_url": "/account/face-enrollment/",
            }, status=403)

        try:
            live_embedding = extract_embedding(image_bytes)
            registered_embedding = decrypt_embedding(profile.encrypted_template)
            similarity = compare_embeddings(live_embedding, registered_embedding)
        except FaceServiceError as exc:
            return JsonResponse({"ok": False, "message": str(exc)}, status=400)
        except Exception:
            return JsonResponse({
                "ok": False,
                "message": "Face verification is temporarily unavailable. Please retry.",
            }, status=503)

        if similarity < 0.40:
            return JsonResponse({
                "ok": False,
                "message": "Face did not match your registration. Please retry with good lighting.",
            }, status=403)

    verification_id = secrets.token_urlsafe(32)
    try:
        pending_photo = _store_pending_attendance_photo(image_bytes, verification_id)
    except Exception:
        return JsonResponse({
            "ok": False,
            "message": "Could not securely save the attendance photo. Please retry.",
        }, status=503)

    request.session["attendance_face_verification"] = {
        "id": verification_id,
        "user_id": user.pk,
        "action": action,
        "mode": gps["mode"],
        "latitude": str(gps["latitude"]),
        "longitude": str(gps["longitude"]),
        "accuracy": str(gps["accuracy"]),
        "pending_photo": pending_photo,
        "expires_at": int(time.time()) + 120,
    }
    request.session.modified = True

    message = (
        "Photo captured. Super Admin face matching is exempt; complete attendance within 2 minutes."
        if is_super_admin else
        "Face verified and photo secured. Complete attendance within 2 minutes."
    )
    return JsonResponse({"ok": True, "verification_id": verification_id, "message": message})



def _consume_face_verification(request, action, gps):
    """Validate and consume the short-lived face verification for this action."""
    import hmac
    import time

    user = request.user

    proof = request.session.get("attendance_face_verification")
    submitted_id = request.POST.get("face_verification_id", "")

    if not isinstance(proof, dict) or not submitted_id:
        return False, "Please complete face verification before attendance."

    try:
        valid = (
            proof.get("user_id") == user.pk
            and proof.get("action") == action
            and proof.get("mode") == gps["mode"]
            and proof.get("latitude") == str(gps["latitude"])
            and proof.get("longitude") == str(gps["longitude"])
            and proof.get("accuracy") == str(gps["accuracy"])
            and int(proof.get("expires_at", 0)) >= int(time.time())
            and hmac.compare_digest(str(proof.get("id", "")), submitted_id)
        )
    except (TypeError, ValueError):
        valid = False

    if not valid:
        request.session.pop("attendance_face_verification", None)
        request.session.modified = True
        return False, "Face verification expired or does not match this attendance request. Please verify again."

    # One-time token: remove it so it cannot authorize another attendance action.
    request.session.pop("attendance_face_verification", None)
    request.session.modified = True
    return True, None


@login_required
def attendance_clock_in(request):
    if request.method != "POST":
        return HttpResponseNotAllowed(["POST"])

    current_employee = get_current_employee(request.user)
    if not current_employee:
        messages.error(request, "Your employee profile was not found.")
        return redirect("attendance_dashboard")

    gps, error = _validate_attendance_gps(request)
    if error:
        messages.error(request, error)
        return redirect("attendance_dashboard")

    face_proof = request.session.get("attendance_face_verification", {})
    allowed, face_error = _consume_face_verification(request, "clock-in", gps)
    if not allowed:
        messages.error(request, face_error)
        return redirect("attendance_dashboard")
    pending_photo = face_proof.get("pending_photo")
    if not pending_photo:
        messages.error(request, "Attendance photo is missing. Please capture it again.")
        return redirect("attendance_dashboard")

    today = timezone.localdate()
    current_time = timezone.localtime().time().replace(microsecond=0)

    attendance, created = Attendance.objects.get_or_create(
        employee=current_employee,
        date=today,
        defaults={"status": Attendance.Status.PRESENT},
    )

    if not created:
        if attendance.status in {
            Attendance.Status.ABSENT,
            Attendance.Status.ON_LEAVE,
            Attendance.Status.HOLIDAY,
            Attendance.Status.WEEK_OFF,
        }:
            messages.error(
                request,
                "You cannot clock in because today's attendance status is already "
                f"{attendance.get_status_display()}.",
            )
            return redirect("attendance_dashboard")

        if attendance.check_in:
            messages.warning(request, "You have already clocked in today.")
            return redirect("attendance_dashboard")

    attendance.status = Attendance.Status.PRESENT
    attendance.check_in = current_time
    attendance.attendance_mode = gps["mode"]
    attendance.check_in_latitude = gps["latitude"]
    attendance.check_in_longitude = gps["longitude"]
    attendance.check_in_accuracy = gps["accuracy"]
    attendance.check_in_address = gps["address"]
    if not _attach_pending_attendance_photo(attendance, pending_photo, "check_in_photo"):
        messages.error(request, "Could not attach the private Clock In photo. Please retry.")
        return redirect("attendance_dashboard")
    attendance.save()

    broadcast_user_presence(request.user.pk)
    messages.success(
        request,
        f"Clock-in recorded at {current_time.strftime('%I:%M %p')} ({gps['mode'].title()}).",
    )
    return redirect("attendance_dashboard")


@login_required
def attendance_clock_out(request):
    if request.method != "POST":
        return HttpResponseNotAllowed(["POST"])

    current_employee = get_current_employee(request.user)
    if not current_employee:
        messages.error(request, "Your employee profile was not found.")
        return redirect("attendance_dashboard")

    gps, error = _validate_attendance_gps(request)
    if error:
        messages.error(request, error)
        return redirect("attendance_dashboard")

    face_proof = request.session.get("attendance_face_verification", {})
    allowed, face_error = _consume_face_verification(request, "clock-out", gps)
    if not allowed:
        messages.error(request, face_error)
        return redirect("attendance_dashboard")
    pending_photo = face_proof.get("pending_photo")
    if not pending_photo:
        messages.error(request, "Attendance photo is missing. Please capture it again.")
        return redirect("attendance_dashboard")

    today = timezone.localdate()
    attendance = get_object_or_404(Attendance, employee=current_employee, date=today)

    if not attendance.check_in:
        messages.error(request, "You cannot clock out because you have not clocked in.")
        return redirect("attendance_dashboard")

    if attendance.check_out:
        messages.warning(request, "You have already clocked out today.")
        return redirect("attendance_dashboard")

    current_time = timezone.localtime().time().replace(microsecond=0)
    attendance.check_out = current_time
    attendance.status = Attendance.Status.PRESENT
    attendance.check_out_mode = gps["mode"]
    attendance.check_out_latitude = gps["latitude"]
    attendance.check_out_longitude = gps["longitude"]
    attendance.check_out_accuracy = gps["accuracy"]
    attendance.check_out_address = gps["address"]
    if not _attach_pending_attendance_photo(attendance, pending_photo, "check_out_photo"):
        messages.error(request, "Could not attach the private Clock Out photo. Please retry.")
        return redirect("attendance_dashboard")
    attendance.save()

    broadcast_user_presence(request.user.pk, False)
    messages.success(
        request,
        f"Clock-out recorded at {current_time.strftime('%I:%M %p')} ({gps['mode'].title()}).",
    )
    return redirect("attendance_dashboard")


# =========================================================
# PRIVATE ATTENDANCE PHOTO HELPERS
# =========================================================

def _store_pending_attendance_photo(image_bytes, verification_id):
    """Store a verified camera image outside public MEDIA_ROOT."""
    from django.core.files.base import ContentFile
    from attendance.storage_backends.private_attendance import (
        PrivateAttendanceStorage,
    )

    storage = PrivateAttendanceStorage()
    name = f"pending/{verification_id}.jpg"

    # Never overwrite an existing file.
    saved_name = storage.save(name, ContentFile(image_bytes))
    return saved_name


def _attach_pending_attendance_photo(attendance, pending_name, field_name):
    """Move a pending private photo into its final attendance field."""
    from django.core.files.base import ContentFile
    from attendance.storage_backends.private_attendance import (
        PrivateAttendanceStorage,
    )

    if not pending_name:
        return False

    storage = PrivateAttendanceStorage()

    try:
        with storage.open(pending_name, "rb") as photo:
            image_bytes = photo.read()

        field = getattr(attendance, field_name)
        field.save(
            pending_name.rsplit("/", 1)[-1],
            ContentFile(image_bytes),
            save=False,
        )
        storage.delete(pending_name)
        return True
    except (OSError, ValueError):
        return False


# =========================================================
# PRIVATE ATTENDANCE PHOTO GALLERY
# =========================================================

@login_required
def attendance_photo_gallery(request):
    from django.core.exceptions import PermissionDenied

    user = request.user
    if not (is_super_admin(user) or is_hr_admin(user) or is_manager(user)):
        raise PermissionDenied("You do not have permission to view attendance photos.")

    records = Attendance.objects.select_related(
        "employee", "employee__user"
    ).filter(
        employee__isnull=False
    ).order_by("-date", "-check_in")

    if is_super_admin(user):
        pass
    elif is_hr_admin(user):
        current_employee = get_current_employee(user)
        if not current_employee:
            raise PermissionDenied("Your employee profile was not found.")
        records = records.filter(employee__company_id=current_employee.company_id)
    else:
        current_employee = get_current_employee(user)
        if not current_employee:
            raise PermissionDenied("Your employee profile was not found.")
        # Direct reports only; exclude the manager's own attendance.
        records = records.filter(employee__reporting_manager=current_employee)

    return render(
        request,
        "attendance/attendance_photo_gallery.html",
        {"attendance_records": records[:300]},
    )


@login_required
def attendance_private_photo(request, pk, photo_type):
    import mimetypes
    from django.core.exceptions import PermissionDenied
    from django.http import FileResponse, Http404, HttpResponse
    from django.utils.cache import patch_cache_control

    user = request.user
    if not (is_super_admin(user) or is_hr_admin(user) or is_manager(user)):
        raise PermissionDenied("You do not have permission to view attendance photos.")

    if photo_type not in {"in", "out"}:
        raise Http404("Photo not found.")

    records = Attendance.objects.select_related("employee").all()
    if is_super_admin(user):
        pass
    elif is_hr_admin(user):
        current_employee = get_current_employee(user)
        if not current_employee:
            raise PermissionDenied("Your employee profile was not found.")
        records = records.filter(employee__company_id=current_employee.company_id)
    else:
        current_employee = get_current_employee(user)
        if not current_employee:
            raise PermissionDenied("Your employee profile was not found.")
        records = records.filter(employee__reporting_manager=current_employee)

    attendance = records.filter(pk=pk).first()
    if not attendance:
        # Do not reveal whether another team's attendance record exists.
        raise Http404("Photo not found.")

    field = attendance.check_in_photo if photo_type == "in" else attendance.check_out_photo
    if not field:
        raise Http404("Photo not found.")

    try:
        photo_file = field.open("rb")
    except (OSError, ValueError):
        raise Http404("Photo not found.")

    content_type = mimetypes.guess_type(field.name)[0] or "application/octet-stream"
    response = FileResponse(photo_file, content_type=content_type)
    patch_cache_control(response, private=True, no_store=True, max_age=0)
    response["X-Content-Type-Options"] = "nosniff"
    return response
