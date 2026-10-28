from django.urls import path

from . import views


urlpatterns = [

    # =====================================================
    # DASHBOARD
    # =====================================================

    path(
        "",
        views.attendance_dashboard,
        name="attendance_dashboard",
    ),

    path(
        "dashboard/",
        views.attendance_dashboard,
        name="attendance_dashboard_page",
    ),

    # =====================================================
    # LIST
    # =====================================================

    path(
        "list/",
        views.attendance_list,
        name="attendance_list",
    ),

    # =====================================================
    # CREATE
    # =====================================================

    path(
        "create/",
        views.attendance_create,
        name="attendance_create",
    ),

    # =====================================================
    # DETAIL
    # =====================================================

    path(
        "<int:pk>/",
        views.attendance_detail,
        name="attendance_detail",
    ),

    # =====================================================
    # UPDATE
    # =====================================================

    path(
        "<int:pk>/edit/",
        views.attendance_update,
        name="attendance_update",
    ),

    # =====================================================
    # DELETE
    # =====================================================

    path(
        "<int:pk>/delete/",
        views.attendance_delete,
        name="attendance_delete",
    ),

    # =====================================================
    # CALENDAR
    # =====================================================

    path(
        "calendar/",
        views.attendance_calendar,
        name="attendance_calendar",
    ),

    # =====================================================
    # REPORT
    # =====================================================

    path(
        "report/",
        views.attendance_report,
        name="attendance_report",
    ),

    # =====================================================
    # REAL-TIME CLOCK
    # =====================================================

    path(
        "face-verify/",
        views.attendance_face_verify,
        name="attendance_face_verify",
    ),

    path(
        "clock-in/",
        views.attendance_clock_in,
        name="attendance_clock_in",
    ),

    path(
        "clock-out/",
        views.attendance_clock_out,
        name="attendance_clock_out",
    ),

    # =====================================================
    # PRIVATE ATTENDANCE PHOTO GALLERY
    # =====================================================

    path(
        "photos/",
        views.attendance_photo_gallery,
        name="attendance_photo_gallery",
    ),
    path(
        "photos/<int:pk>/<str:photo_type>/",
        views.attendance_private_photo,
        name="attendance_private_photo",
    ),
]
