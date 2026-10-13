from django import forms

from .models import (
    Employee,
    EmployeeDocument,
    EmployeeAsset,
)


# ============================================================
# EMPLOYEE FORM
# ============================================================

class EmployeeForm(forms.ModelForm):

    class Meta:
        model = Employee

        fields = [
            # Personal
            "employee_id",
            "first_name",
            "middle_name",
            "last_name",
            "date_of_birth",
            "gender",

            # Contact
            "email",
            "phone",
            "alternate_phone",

            # Address
            "address",
            "city",
            "state",
            "country",
            "postal_code",

            # Organization
            "company",
            "department",
            "designation",
            "branch",
            "work_location",

            # Role
            "role",

            # Employment
            "employment_type",
            "employment_status",
            "joining_date",
            "confirmation_date",
            "resignation_date",
            "termination_date",

            # Reporting
            "reporting_manager",

            # Profile
            "profile_photo",
        ]

        widgets = {
            "employee_id": forms.TextInput(
                attrs={
                    "class": "form-control",
                    "placeholder": "Employee ID",
                }
            ),

            "first_name": forms.TextInput(
                attrs={
                    "class": "form-control",
                    "placeholder": "First name",
                }
            ),

            "middle_name": forms.TextInput(
                attrs={
                    "class": "form-control",
                    "placeholder": "Middle name",
                }
            ),

            "last_name": forms.TextInput(
                attrs={
                    "class": "form-control",
                    "placeholder": "Last name",
                }
            ),

            "date_of_birth": forms.DateInput(
                attrs={
                    "class": "form-control",
                    "type": "date",
                }
            ),

            "gender": forms.Select(
                attrs={
                    "class": "form-select",
                }
            ),

            "email": forms.EmailInput(
                attrs={
                    "class": "form-control",
                    "placeholder": "employee@example.com",
                }
            ),

            "phone": forms.TextInput(
                attrs={
                    "class": "form-control",
                    "placeholder": "Phone number",
                }
            ),

            "alternate_phone": forms.TextInput(
                attrs={
                    "class": "form-control",
                    "placeholder": "Alternate phone number",
                }
            ),

            "address": forms.Textarea(
                attrs={
                    "class": "form-control",
                    "placeholder": "Full address",
                    "rows": 3,
                }
            ),

            "city": forms.TextInput(
                attrs={
                    "class": "form-control",
                    "placeholder": "City",
                }
            ),

            "state": forms.TextInput(
                attrs={
                    "class": "form-control",
                    "placeholder": "State",
                }
            ),

            "country": forms.TextInput(
                attrs={
                    "class": "form-control",
                    "placeholder": "Country",
                }
            ),

            "postal_code": forms.TextInput(
                attrs={
                    "class": "form-control",
                    "placeholder": "Postal code",
                }
            ),

            "company": forms.Select(
                attrs={
                    "class": "form-select",
                }
            ),

            "department": forms.Select(
                attrs={
                    "class": "form-select",
                }
            ),

            "designation": forms.Select(
                attrs={
                    "class": "form-select",
                }
            ),

            "branch": forms.Select(
                attrs={
                    "class": "form-select",
                }
            ),

            "work_location": forms.Select(
                attrs={
                    "class": "form-select",
                }
            ),

            "role": forms.Select(
                attrs={
                    "class": "form-select",
                }
            ),

            "employment_type": forms.Select(
                attrs={
                    "class": "form-select",
                }
            ),

            "employment_status": forms.Select(
                attrs={
                    "class": "form-select",
                }
            ),

            "joining_date": forms.DateInput(
                attrs={
                    "class": "form-control",
                    "type": "date",
                }
            ),

            "confirmation_date": forms.DateInput(
                attrs={
                    "class": "form-control",
                    "type": "date",
                }
            ),

            "resignation_date": forms.DateInput(
                attrs={
                    "class": "form-control",
                    "type": "date",
                }
            ),

            "termination_date": forms.DateInput(
                attrs={
                    "class": "form-control",
                    "type": "date",
                }
            ),

            "reporting_manager": forms.Select(
                attrs={
                    "class": "form-select",
                }
            ),

            "profile_photo": forms.ClearableFileInput(
                attrs={
                    "class": "form-control",
                    "accept": "image/*",
                }
            ),
        }

    # ========================================================
    # INITIALIZE
    # ========================================================

    def __init__(self, *args, **kwargs):

        request_user = kwargs.pop(
            "request_user",
            None,
        )

        super().__init__(
            *args,
            **kwargs,
        )

        self.request_user = request_user

        # ----------------------------------------------------
        # OPTIONAL FIELDS
        # ----------------------------------------------------

        optional_fields = [
            "department",
            "designation",
            "branch",
            "work_location",
            "reporting_manager",
            "date_of_birth",
            "confirmation_date",
            "resignation_date",
            "termination_date",
            "email",
            "phone",
            "alternate_phone",
            "address",
            "city",
            "state",
            "postal_code",
            "profile_photo",
        ]

        for field_name in optional_fields:
            self.fields[field_name].required = False

        # ----------------------------------------------------
        # CURRENT EMPLOYEE
        # ----------------------------------------------------

        self.current_employee = None

        if request_user and request_user.is_authenticated:

            self.current_employee = getattr(
                request_user,
                "employee_profile",
                None,
            )

        # ----------------------------------------------------
        # ROLE PERMISSIONS
        # ----------------------------------------------------

        if self.current_employee:

            # ================================================
            # HR ADMIN
            # ================================================

            if (
                self.current_employee.role
                == Employee.Role.HR_ADMIN
            ):

                self.fields["role"].choices = [
                    (
                        Employee.Role.EMPLOYEE,
                        "Employee",
                    ),
                    (
                        Employee.Role.MANAGER,
                        "Manager",
                    ),
                ]

                # HR can only work inside own company.

                self.fields["company"].queryset = (
                    self.fields["company"]
                    .queryset
                    .filter(
                        pk=self.current_employee.company_id
                    )
                )

                self.fields["company"].initial = (
                    self.current_employee.company
                )

                self.fields["company"].disabled = True

            # ================================================
            # SUPER ADMIN
            # ================================================

            elif (
                self.current_employee.role
                == Employee.Role.SUPER_ADMIN
            ):

                self.fields["role"].choices = [
                    (
                        Employee.Role.EMPLOYEE,
                        "Employee",
                    ),
                    (
                        Employee.Role.MANAGER,
                        "Manager",
                    ),
                    (
                        Employee.Role.HR_ADMIN,
                        "HR Admin",
                    ),
                ]

        # ----------------------------------------------------
        # MANAGER QUERYSET
        # ----------------------------------------------------

        manager_queryset = (
            Employee.objects
            .filter(
                role=Employee.Role.MANAGER,
                employment_status__in=[
                    Employee.EmploymentStatus.ACTIVE,
                    Employee.EmploymentStatus.ON_LEAVE,
                ],
            )
            .select_related(
                "company",
                "department",
                "designation",
            )
            .order_by(
                "first_name",
                "last_name",
            )
        )

        # Don't allow self as manager.

        if self.instance and self.instance.pk:

            manager_queryset = (
                manager_queryset.exclude(
                    pk=self.instance.pk
                )
            )

        # HR sees only managers in own company.

        if (
            self.current_employee
            and self.current_employee.role
            == Employee.Role.HR_ADMIN
        ):

            manager_queryset = (
                manager_queryset.filter(
                    company_id=(
                        self.current_employee.company_id
                    )
                )
            )

        self.fields[
            "reporting_manager"
        ].queryset = manager_queryset

    # ========================================================
    # VALIDATION
    # ========================================================

    def clean(self):

        cleaned_data = super().clean()

        role = cleaned_data.get("role")
        company = cleaned_data.get("company")
        department = cleaned_data.get("department")
        manager = cleaned_data.get(
            "reporting_manager"
        )

        current_employee = self.current_employee

        # ----------------------------------------------------
        # HR COMPANY SECURITY
        # ----------------------------------------------------

        if (
            current_employee
            and current_employee.role
            == Employee.Role.HR_ADMIN
        ):

            company = current_employee.company

            cleaned_data["company"] = company

            if role not in [
                Employee.Role.EMPLOYEE,
                Employee.Role.MANAGER,
            ]:

                self.add_error(
                    "role",
                    "HR Admin can create only Employees and Managers.",
                )

        # ----------------------------------------------------
        # REPORTING MANAGER
        # ----------------------------------------------------

        if manager:

            # Manager must belong to same company.

            if company and manager.company_id != company.id:

                self.add_error(
                    "reporting_manager",
                    "Reporting manager must belong to the same company.",
                )

            # Employee must report to a Manager.

            if role == Employee.Role.EMPLOYEE:

                if manager.role != Employee.Role.MANAGER:

                    self.add_error(
                        "reporting_manager",
                        "Employee must report to a Manager.",
                    )

                if (
                    department
                    and manager.department_id
                    != department.id
                ):

                    self.add_error(
                        "reporting_manager",
                        "Employee and Manager must belong to the same department.",
                    )

        # ----------------------------------------------------
        # EMPLOYEE MUST HAVE MANAGER
        # ----------------------------------------------------

        if (
            role == Employee.Role.EMPLOYEE
            and not manager
        ):

            self.add_error(
                "reporting_manager",
                "Please select a reporting manager for the employee.",
            )

        # ----------------------------------------------------
        # MANAGER CREATED BY HR
        # ----------------------------------------------------

        if (
            role == Employee.Role.MANAGER
            and current_employee
            and current_employee.role
            == Employee.Role.HR_ADMIN
        ):

            cleaned_data[
                "reporting_manager"
            ] = current_employee

        return cleaned_data


# ============================================================
# EMPLOYEE DOCUMENT FORM
# ============================================================

class EmployeeDocumentForm(forms.ModelForm):

    class Meta:
        model = EmployeeDocument

        fields = [
            "document_type",
            "title",
            "description",
            "document",
            "issue_date",
            "expiry_date",
        ]

        widgets = {
            "document_type": forms.Select(
                attrs={
                    "class": "form-select",
                }
            ),

            "title": forms.TextInput(
                attrs={
                    "class": "form-control",
                    "placeholder": "Document title",
                }
            ),

            "description": forms.Textarea(
                attrs={
                    "class": "form-control",
                    "placeholder": "Description",
                    "rows": 3,
                }
            ),

            "document": forms.ClearableFileInput(
                attrs={
                    "class": "form-control",
                }
            ),

            "issue_date": forms.DateInput(
                attrs={
                    "class": "form-control",
                    "type": "date",
                }
            ),

            "expiry_date": forms.DateInput(
                attrs={
                    "class": "form-control",
                    "type": "date",
                }
            ),
        }

    def __init__(self, *args, **kwargs):

        super().__init__(
            *args,
            **kwargs,
        )

        self.fields[
            "description"
        ].required = False

        self.fields[
            "issue_date"
        ].required = False

        self.fields[
            "expiry_date"
        ].required = False


# ============================================================
# EMPLOYEE ASSET FORM
# ============================================================

class EmployeeAssetForm(forms.ModelForm):

    class Meta:
        model = EmployeeAsset

        fields = [
            "asset_type",
            "asset_name",
            "asset_code",
            "serial_number",
            "assigned_date",
            "return_date",
            "status",
            "notes",
        ]

        widgets = {
            "asset_type": forms.Select(
                attrs={
                    "class": "form-select",
                }
            ),

            "asset_name": forms.TextInput(
                attrs={
                    "class": "form-control",
                    "placeholder": "Asset name",
                }
            ),

            "asset_code": forms.TextInput(
                attrs={
                    "class": "form-control",
                    "placeholder": "Asset code",
                }
            ),

            "serial_number": forms.TextInput(
                attrs={
                    "class": "form-control",
                    "placeholder": "Serial number",
                }
            ),

            "assigned_date": forms.DateInput(
                attrs={
                    "class": "form-control",
                    "type": "date",
                }
            ),

            "return_date": forms.DateInput(
                attrs={
                    "class": "form-control",
                    "type": "date",
                }
            ),

            "status": forms.Select(
                attrs={
                    "class": "form-select",
                }
            ),

            "notes": forms.Textarea(
                attrs={
                    "class": "form-control",
                    "placeholder": "Asset notes",
                    "rows": 3,
                }
            ),
        }

    def __init__(self, *args, **kwargs):

        super().__init__(
            *args,
            **kwargs,
        )

        self.fields[
            "serial_number"
        ].required = False

        self.fields[
            "return_date"
        ].required = False

        self.fields[
            "notes"
        ].required = False