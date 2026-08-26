from django.contrib import messages
from django.contrib.auth.mixins import LoginRequiredMixin
from django.urls import reverse_lazy
from django.views.generic import (
    ListView,
    CreateView,
    UpdateView,
    DeleteView,
)

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
# COMPANY
# =========================================================

class CompanyListView(LoginRequiredMixin, ListView):

    model = Company
    template_name = "organization/company_list.html"
    context_object_name = "companies"

    def get_queryset(self):
        return Company.objects.all().order_by("name")


class CompanyCreateView(LoginRequiredMixin, CreateView):

    model = Company
    form_class = CompanyForm
    template_name = "organization/company_form.html"
    success_url = reverse_lazy("company_list")

    def form_valid(self, form):
        messages.success(
            self.request,
            "Company created successfully."
        )
        return super().form_valid(form)


class CompanyUpdateView(LoginRequiredMixin, UpdateView):

    model = Company
    form_class = CompanyForm
    template_name = "organization/company_form.html"
    success_url = reverse_lazy("company_list")

    def form_valid(self, form):
        messages.success(
            self.request,
            "Company updated successfully."
        )
        return super().form_valid(form)


class CompanyDeleteView(LoginRequiredMixin, DeleteView):

    model = Company
    template_name = "organization/company_confirm_delete.html"
    success_url = reverse_lazy("company_list")

    def form_valid(self, form):
        messages.success(
            self.request,
            "Company deleted successfully."
        )
        return super().form_valid(form)


# =========================================================
# DEPARTMENT
# =========================================================

class DepartmentListView(LoginRequiredMixin, ListView):

    model = Department
    template_name = "organization/department_list.html"
    context_object_name = "departments"

    def get_queryset(self):
        return Department.objects.select_related(
            "company"
        ).order_by("name")


class DepartmentCreateView(LoginRequiredMixin, CreateView):

    model = Department
    form_class = DepartmentForm
    template_name = "organization/department_form.html"
    success_url = reverse_lazy("department_list")

    def form_valid(self, form):
        messages.success(
            self.request,
            "Department created successfully."
        )
        return super().form_valid(form)


class DepartmentUpdateView(LoginRequiredMixin, UpdateView):

    model = Department
    form_class = DepartmentForm
    template_name = "organization/department_form.html"
    success_url = reverse_lazy("department_list")

    def form_valid(self, form):
        messages.success(
            self.request,
            "Department updated successfully."
        )
        return super().form_valid(form)


class DepartmentDeleteView(LoginRequiredMixin, DeleteView):

    model = Department
    template_name = "organization/department_confirm_delete.html"
    success_url = reverse_lazy("department_list")

    def form_valid(self, form):
        messages.success(
            self.request,
            "Department deleted successfully."
        )
        return super().form_valid(form)


# =========================================================
# DESIGNATION
# =========================================================

class DesignationListView(LoginRequiredMixin, ListView):

    model = Designation
    template_name = "organization/designation_list.html"
    context_object_name = "designations"

    def get_queryset(self):
        return Designation.objects.select_related(
            "company"
        ).order_by("level", "name")


class DesignationCreateView(LoginRequiredMixin, CreateView):

    model = Designation
    form_class = DesignationForm
    template_name = "organization/designation_form.html"
    success_url = reverse_lazy("designation_list")

    def form_valid(self, form):
        messages.success(
            self.request,
            "Designation created successfully."
        )
        return super().form_valid(form)


class DesignationUpdateView(LoginRequiredMixin, UpdateView):

    model = Designation
    form_class = DesignationForm
    template_name = "organization/designation_form.html"
    success_url = reverse_lazy("designation_list")

    def form_valid(self, form):
        messages.success(
            self.request,
            "Designation updated successfully."
        )
        return super().form_valid(form)


class DesignationDeleteView(LoginRequiredMixin, DeleteView):

    model = Designation
    template_name = "organization/designation_confirm_delete.html"
    success_url = reverse_lazy("designation_list")

    def form_valid(self, form):
        messages.success(
            self.request,
            "Designation deleted successfully."
        )
        return super().form_valid(form)


# =========================================================
# BRANCH
# =========================================================

class BranchListView(LoginRequiredMixin, ListView):

    model = Branch
    template_name = "organization/branch_list.html"
    context_object_name = "branches"

    def get_queryset(self):
        return Branch.objects.select_related(
            "company"
        ).order_by("name")


class BranchCreateView(LoginRequiredMixin, CreateView):

    model = Branch
    form_class = BranchForm
    template_name = "organization/branch_form.html"
    success_url = reverse_lazy("branch_list")

    def form_valid(self, form):
        messages.success(
            self.request,
            "Branch created successfully."
        )
        return super().form_valid(form)


class BranchUpdateView(LoginRequiredMixin, UpdateView):

    model = Branch
    form_class = BranchForm
    template_name = "organization/branch_form.html"
    success_url = reverse_lazy("branch_list")

    def form_valid(self, form):
        messages.success(
            self.request,
            "Branch updated successfully."
        )
        return super().form_valid(form)


class BranchDeleteView(LoginRequiredMixin, DeleteView):

    model = Branch
    template_name = "organization/branch_confirm_delete.html"
    success_url = reverse_lazy("branch_list")

    def form_valid(self, form):
        messages.success(
            self.request,
            "Branch deleted successfully."
        )
        return super().form_valid(form)


# =========================================================
# WORK LOCATION
# =========================================================

class WorkLocationListView(LoginRequiredMixin, ListView):

    model = WorkLocation
    template_name = "organization/work_location_list.html"
    context_object_name = "work_locations"

    def get_queryset(self):
        return WorkLocation.objects.select_related(
            "company"
        ).order_by("name")


class WorkLocationCreateView(LoginRequiredMixin, CreateView):

    model = WorkLocation
    form_class = WorkLocationForm
    template_name = "organization/work_location_form.html"
    success_url = reverse_lazy("work_location_list")

    def form_valid(self, form):
        messages.success(
            self.request,
            "Work location created successfully."
        )
        return super().form_valid(form)


class WorkLocationUpdateView(LoginRequiredMixin, UpdateView):

    model = WorkLocation
    form_class = WorkLocationForm
    template_name = "organization/work_location_form.html"
    success_url = reverse_lazy("work_location_list")

    def form_valid(self, form):
        messages.success(
            self.request,
            "Work location updated successfully."
        )
        return super().form_valid(form)


class WorkLocationDeleteView(LoginRequiredMixin, DeleteView):

    model = WorkLocation
    template_name = "organization/work_location_confirm_delete.html"
    success_url = reverse_lazy("work_location_list")

    def form_valid(self, form):
        messages.success(
            self.request,
            "Work location deleted successfully."
        )
        return super().form_valid(form)