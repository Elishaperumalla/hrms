from django.urls import path

from .views import (
    CompanyListView,
    CompanyCreateView,
    CompanyUpdateView,
    CompanyDeleteView,

    DepartmentListView,
    DepartmentCreateView,
    DepartmentUpdateView,
    DepartmentDeleteView,

    DesignationListView,
    DesignationCreateView,
    DesignationUpdateView,
    DesignationDeleteView,

    BranchListView,
    BranchCreateView,
    BranchUpdateView,
    BranchDeleteView,

    WorkLocationListView,
    WorkLocationCreateView,
    WorkLocationUpdateView,
    WorkLocationDeleteView,
    office_attendance_settings,
)


urlpatterns = [
    path("office-attendance-settings/", office_attendance_settings, name="office_attendance_settings"),

    # =====================================================
    # COMPANY
    # =====================================================

    path(
        "companies/",
        CompanyListView.as_view(),
        name="company_list",
    ),

    path(
        "companies/add/",
        CompanyCreateView.as_view(),
        name="company_create",
    ),

    path(
        "companies/<int:pk>/edit/",
        CompanyUpdateView.as_view(),
        name="company_update",
    ),

    path(
        "companies/<int:pk>/delete/",
        CompanyDeleteView.as_view(),
        name="company_delete",
    ),


    # =====================================================
    # DEPARTMENT
    # =====================================================

    path(
        "departments/",
        DepartmentListView.as_view(),
        name="department_list",
    ),

    path(
        "departments/add/",
        DepartmentCreateView.as_view(),
        name="department_create",
    ),

    path(
        "departments/<int:pk>/edit/",
        DepartmentUpdateView.as_view(),
        name="department_update",
    ),

    path(
        "departments/<int:pk>/delete/",
        DepartmentDeleteView.as_view(),
        name="department_delete",
    ),


    # =====================================================
    # DESIGNATION
    # =====================================================

    path(
        "designations/",
        DesignationListView.as_view(),
        name="designation_list",
    ),

    path(
        "designations/add/",
        DesignationCreateView.as_view(),
        name="designation_create",
    ),

    path(
        "designations/<int:pk>/edit/",
        DesignationUpdateView.as_view(),
        name="designation_update",
    ),

    path(
        "designations/<int:pk>/delete/",
        DesignationDeleteView.as_view(),
        name="designation_delete",
    ),


    # =====================================================
    # BRANCH
    # =====================================================

    path(
        "branches/",
        BranchListView.as_view(),
        name="branch_list",
    ),

    path(
        "branches/add/",
        BranchCreateView.as_view(),
        name="branch_create",
    ),

    path(
        "branches/<int:pk>/edit/",
        BranchUpdateView.as_view(),
        name="branch_update",
    ),

    path(
        "branches/<int:pk>/delete/",
        BranchDeleteView.as_view(),
        name="branch_delete",
    ),


    # =====================================================
    # WORK LOCATION
    # =====================================================

    path(
        "work-locations/",
        WorkLocationListView.as_view(),
        name="work_location_list",
    ),

    path(
        "work-locations/add/",
        WorkLocationCreateView.as_view(),
        name="work_location_create",
    ),

    path(
        "work-locations/<int:pk>/edit/",
        WorkLocationUpdateView.as_view(),
        name="work_location_update",
    ),

    path(
        "work-locations/<int:pk>/delete/",
        WorkLocationDeleteView.as_view(),
        name="work_location_delete",
    ),
]