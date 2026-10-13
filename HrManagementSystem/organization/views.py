from django.contrib import messages
from django.contrib.auth.mixins import LoginRequiredMixin
from django.core.exceptions import PermissionDenied
from django.db.models import Count, Q
from django.urls import reverse_lazy
from django.views.generic import (
    ListView,
    CreateView,
    UpdateView,
    DeleteView,
)

from employees.models import Employee

from .models import (
    Company,
    Department,
    Designation,
    Branch,
    WorkLocation,
)

from .forms import (
    CompanyForm,
    DepartmentForm,
    DesignationForm,
    BranchForm,
    WorkLocationForm,
)


# =========================================================
# ROLE / PERMISSION HELPER
# =========================================================

def is_super_admin(user):
    """
    Organization data can be managed only by Super Admin.

    The HRMS Employee role is the primary authority.
    Django's is_superuser is also accepted so the initial
    Django administrator can access the organization module.
    """

    if not user.is_authenticated:
        return False

    try:
        employee = user.employee_profile
    except Employee.DoesNotExist:
        employee = None

    if employee:
        return employee.role == Employee.Role.SUPER_ADMIN

    return user.is_superuser


# =========================================================
# ORGANIZATION PERMISSION MIXIN
# =========================================================

class OrganizationPermissionMixin(LoginRequiredMixin):
    """
    Organization module is strictly Super Admin only.

    Super Admin:
        Full organization management.

    HR Admin:
        No organization-management permission.

    Manager:
        No organization-management permission.

    Employee:
        No organization-management permission.
    """

    def dispatch(self, request, *args, **kwargs):

        if not is_super_admin(request.user):
            raise PermissionDenied(
                "Only Super Admin can manage organization data."
            )

        return super().dispatch(
            request,
            *args,
            **kwargs,
        )


# =========================================================
# COMPANY
# =========================================================

class CompanyListView(
    OrganizationPermissionMixin,
    ListView,
):

    model = Company

    template_name = "organization/company_list.html"

    context_object_name = "companies"

    def get_queryset(self):

        return (
            Company.objects
            .all()
            .order_by("name")
        )


class CompanyCreateView(
    OrganizationPermissionMixin,
    CreateView,
):

    model = Company

    form_class = CompanyForm

    template_name = "organization/company_form.html"

    success_url = reverse_lazy(
        "company_list"
    )

    def form_valid(self, form):

        messages.success(
            self.request,
            "Company created successfully.",
        )

        return super().form_valid(
            form
        )


class CompanyUpdateView(
    OrganizationPermissionMixin,
    UpdateView,
):

    model = Company

    form_class = CompanyForm

    template_name = "organization/company_form.html"

    success_url = reverse_lazy(
        "company_list"
    )

    def form_valid(self, form):

        messages.success(
            self.request,
            "Company updated successfully.",
        )

        return super().form_valid(
            form
        )


class CompanyDeleteView(
    OrganizationPermissionMixin,
    DeleteView,
):

    model = Company

    template_name = (
        "organization/company_confirm_delete.html"
    )

    success_url = reverse_lazy(
        "company_list"
    )

    def form_valid(self, form):

        messages.success(
            self.request,
            "Company deleted successfully.",
        )

        return super().form_valid(
            form
        )


# =========================================================
# DEPARTMENT
# =========================================================

class DepartmentListView(
    OrganizationPermissionMixin,
    ListView,
):

    model = Department

    template_name = (
        "organization/department_list.html"
    )

    context_object_name = "departments"

    def get_queryset(self):

        return (
            Department.objects
            .select_related("company")
            .annotate(
                employee_count=Count(
                    "employees",
                    filter=Q(
                        employees__employment_status__in=[
                            Employee.EmploymentStatus.ACTIVE,
                            Employee.EmploymentStatus.ON_LEAVE,
                            Employee.EmploymentStatus.BENCH,
                        ]
                    ),
                    distinct=True,
                )
            )
            .order_by("name")
        )


class DepartmentCreateView(
    OrganizationPermissionMixin,
    CreateView,
):

    model = Department

    form_class = DepartmentForm

    template_name = (
        "organization/department_form.html"
    )

    success_url = reverse_lazy(
        "department_list"
    )

    def form_valid(self, form):

        messages.success(
            self.request,
            "Department created successfully.",
        )

        return super().form_valid(
            form
        )


class DepartmentUpdateView(
    OrganizationPermissionMixin,
    UpdateView,
):

    model = Department

    form_class = DepartmentForm

    template_name = (
        "organization/department_form.html"
    )

    success_url = reverse_lazy(
        "department_list"
    )

    def form_valid(self, form):

        messages.success(
            self.request,
            "Department updated successfully.",
        )

        return super().form_valid(
            form
        )


class DepartmentDeleteView(
    OrganizationPermissionMixin,
    DeleteView,
):

    model = Department

    template_name = (
        "organization/department_confirm_delete.html"
    )

    success_url = reverse_lazy(
        "department_list"
    )

    def form_valid(self, form):

        messages.success(
            self.request,
            "Department deleted successfully.",
        )

        return super().form_valid(
            form
        )


# =========================================================
# DESIGNATION
# =========================================================

class DesignationListView(
    OrganizationPermissionMixin,
    ListView,
):

    model = Designation

    template_name = (
        "organization/designation_list.html"
    )

    context_object_name = "designations"

    def get_queryset(self):

        return (
            Designation.objects
            .select_related("company")
            .order_by(
                "level",
                "name",
            )
        )


class DesignationCreateView(
    OrganizationPermissionMixin,
    CreateView,
):

    model = Designation

    form_class = DesignationForm

    template_name = (
        "organization/designation_form.html"
    )

    success_url = reverse_lazy(
        "designation_list"
    )

    def form_valid(self, form):

        messages.success(
            self.request,
            "Designation created successfully.",
        )

        return super().form_valid(
            form
        )


class DesignationUpdateView(
    OrganizationPermissionMixin,
    UpdateView,
):

    model = Designation

    form_class = DesignationForm

    template_name = (
        "organization/designation_form.html"
    )

    success_url = reverse_lazy(
        "designation_list"
    )

    def form_valid(self, form):

        messages.success(
            self.request,
            "Designation updated successfully.",
        )

        return super().form_valid(
            form
        )


class DesignationDeleteView(
    OrganizationPermissionMixin,
    DeleteView,
):

    model = Designation

    template_name = (
        "organization/designation_confirm_delete.html"
    )

    success_url = reverse_lazy(
        "designation_list"
    )

    def form_valid(self, form):

        messages.success(
            self.request,
            "Designation deleted successfully.",
        )

        return super().form_valid(
            form
        )


# =========================================================
# BRANCH
# =========================================================

class BranchListView(
    OrganizationPermissionMixin,
    ListView,
):

    model = Branch

    template_name = (
        "organization/branch_list.html"
    )

    context_object_name = "branches"

    def get_queryset(self):

        return (
            Branch.objects
            .select_related("company")
            .order_by("name")
        )


class BranchCreateView(
    OrganizationPermissionMixin,
    CreateView,
):

    model = Branch

    form_class = BranchForm

    template_name = (
        "organization/branch_form.html"
    )

    success_url = reverse_lazy(
        "branch_list"
    )

    def form_valid(self, form):

        messages.success(
            self.request,
            "Branch created successfully.",
        )

        return super().form_valid(
            form
        )


class BranchUpdateView(
    OrganizationPermissionMixin,
    UpdateView,
):

    model = Branch

    form_class = BranchForm

    template_name = (
        "organization/branch_form.html"
    )

    success_url = reverse_lazy(
        "branch_list"
    )

    def form_valid(self, form):

        messages.success(
            self.request,
            "Branch updated successfully.",
        )

        return super().form_valid(
            form
        )


class BranchDeleteView(
    OrganizationPermissionMixin,
    DeleteView,
):

    model = Branch

    template_name = (
        "organization/branch_confirm_delete.html"
    )

    success_url = reverse_lazy(
        "branch_list"
    )

    def form_valid(self, form):

        messages.success(
            self.request,
            "Branch deleted successfully.",
        )

        return super().form_valid(
            form
        )


# =========================================================
# WORK LOCATION
# =========================================================

class WorkLocationListView(
    OrganizationPermissionMixin,
    ListView,
):

    model = WorkLocation

    template_name = (
        "organization/work_location_list.html"
    )

    context_object_name = "work_locations"

    def get_queryset(self):

        return (
            WorkLocation.objects
            .select_related("company")
            .order_by("name")
        )


class WorkLocationCreateView(
    OrganizationPermissionMixin,
    CreateView,
):

    model = WorkLocation

    form_class = WorkLocationForm

    template_name = (
        "organization/work_location_form.html"
    )

    success_url = reverse_lazy(
        "work_location_list"
    )

    def form_valid(self, form):

        messages.success(
            self.request,
            "Work location created successfully.",
        )

        return super().form_valid(
            form
        )


class WorkLocationUpdateView(
    OrganizationPermissionMixin,
    UpdateView,
):

    model = WorkLocation

    form_class = WorkLocationForm

    template_name = (
        "organization/work_location_form.html"
    )

    success_url = reverse_lazy(
        "work_location_list"
    )

    def form_valid(self, form):

        messages.success(
            self.request,
            "Work location updated successfully.",
        )

        return super().form_valid(
            form
        )


class WorkLocationDeleteView(
    OrganizationPermissionMixin,
    DeleteView,
):

    model = WorkLocation

    template_name = (
        "organization/work_location_confirm_delete.html"
    )

    success_url = reverse_lazy(
        "work_location_list"
    )

    def form_valid(self, form):

        messages.success(
            self.request,
            "Work location deleted successfully.",
        )

        return super().form_valid(
            form
        )