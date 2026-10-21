from django.urls import path

from . import views


urlpatterns = [

    path(
        "",
        views.leave_dashboard,
        name="leave_dashboard",
    ),

    path(
        "list/",
        views.leave_list,
        name="leave_list",
    ),

    path(
        "create/",
        views.leave_create,
        name="leave_create",
    ),

    path(
        "<int:pk>/",
        views.leave_detail,
        name="leave_detail",
    ),

    path(
        "<int:pk>/approval/",
        views.leave_approval,
        name="leave_approval",
    ),

    path(
        "<int:pk>/cancel/",
        views.leave_cancel,
        name="leave_cancel",
    ),

    path(
        "balance/",
        views.leave_balance,
        name="leave_balance",
    ),

    path(
        "balance/create/",
        views.leave_balance_create,
        name="leave_balance_create",
    ),

    path(
        "calendar/",
        views.leave_calendar,
        name="leave_calendar",
    ),

    path(
        "types/",
        views.leave_types,
        name="leave_types",
    ),

    path(
        "types/create/",
        views.leave_type_create,
        name="leave_type_create",
    ),

    path(
        "types/<int:pk>/edit/",
        views.leave_type_update,
        name="leave_type_update",
    ),

    path(
        "report/",
        views.leave_report,
        name="leave_report",
    ),
    
    path(
    "month/<int:year>/<int:month>/",
    views.leave_month_detail,
    name="leave_month_detail",
),
]