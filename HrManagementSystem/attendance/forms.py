from django import forms
from django.db.models import Q

from employees.models import Employee

from .models import Attendance


class AttendanceForm(forms.ModelForm):

    class Meta:

        model = Attendance

        fields = [
            "employee",
            "date",
            "status",
            "check_in",
            "check_out",
            "break_duration",
            "overtime_hours",
            "remarks",
        ]

        widgets = {

            "employee": forms.Select(
                attrs={
                    "class": "form-select",
                }
            ),

            "date": forms.DateInput(
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

            "check_in": forms.TimeInput(
                attrs={
                    "class": "form-control",
                    "type": "time",
                }
            ),

            "check_out": forms.TimeInput(
                attrs={
                    "class": "form-control",
                    "type": "time",
                }
            ),

            "break_duration": forms.NumberInput(
                attrs={
                    "class": "form-control",
                    "placeholder": "Minutes",
                    "min": "0",
                }
            ),

            "overtime_hours": forms.NumberInput(
                attrs={
                    "class": "form-control",
                    "placeholder": "0.00",
                    "step": "0.01",
                    "min": "0",
                }
            ),

            "remarks": forms.Textarea(
                attrs={
                    "class": "form-control",
                    "placeholder": "Attendance remarks",
                    "rows": 4,
                }
            ),
        }

    # =========================================================
    # INITIALIZATION
    # =========================================================

    def __init__(
        self,
        *args,
        request_user=None,
        **kwargs,
    ):

        super().__init__(
            *args,
            **kwargs,
        )

        self.request_user = request_user

        # -----------------------------------------------------
        # OPTIONAL FIELDS
        # -----------------------------------------------------

        for field_name in [
            "check_in",
            "check_out",
            "break_duration",
            "overtime_hours",
            "remarks",
        ]:
            self.fields[field_name].required = False

        # -----------------------------------------------------
        # BASE EMPLOYEE QUERYSET
        # -----------------------------------------------------

        employees = (
            Employee.objects
            .select_related(
                "company",
                "department",
                "designation",
            )
            .filter(
                employment_status=Employee.EmploymentStatus.ACTIVE
            )
            .order_by(
                "first_name",
                "last_name",
            )
        )

        # -----------------------------------------------------
        # NO USER
        # -----------------------------------------------------

        if not request_user:

            employees = employees.none()

        # -----------------------------------------------------
        # SUPER ADMIN
        # -----------------------------------------------------

        elif getattr(
            request_user,
            "role",
            None,
        ) == "SUPER_ADMIN":

            pass

        # -----------------------------------------------------
        # HR ADMIN
        # -----------------------------------------------------

        elif getattr(
            request_user,
            "role",
            None,
        ) == "HR_ADMIN":

            try:

                current_employee = (
                    request_user.employee_profile
                )

                if current_employee.company_id:

                    employees = employees.filter(
                        company_id=current_employee.company_id
                    )

                else:

                    employees = employees.none()

            except Employee.DoesNotExist:

                employees = employees.none()

        # -----------------------------------------------------
        # MANAGER
        # -----------------------------------------------------

        elif getattr(
            request_user,
            "role",
            None,
        ) == "MANAGER":

            try:

                current_employee = (
                    request_user.employee_profile
                )

                employees = employees.filter(
                    Q(pk=current_employee.pk)
                    |
                    Q(
                        reporting_manager=current_employee
                    )
                )

            except Employee.DoesNotExist:

                employees = employees.none()

        # -----------------------------------------------------
        # EMPLOYEE
        # -----------------------------------------------------

        else:

            try:

                current_employee = (
                    request_user.employee_profile
                )

                employees = employees.filter(
                    pk=current_employee.pk
                )

            except Employee.DoesNotExist:

                employees = employees.none()

        self.fields[
            "employee"
        ].queryset = employees

        # -----------------------------------------------------
        # EMPLOYEE FIELD BEHAVIOUR
        # -----------------------------------------------------

        if (
            request_user
            and getattr(
                request_user,
                "role",
                None,
            ) == "EMPLOYEE"
        ):

            try:

                current_employee = (
                    request_user.employee_profile
                )

                self.fields[
                    "employee"
                ].initial = current_employee.pk

                self.fields[
                    "employee"
                ].disabled = True

            except Employee.DoesNotExist:

                pass

    # =========================================================
    # VALIDATION
    # =========================================================

    def clean(self):

        cleaned_data = super().clean()

        employee = cleaned_data.get(
            "employee"
        )

        status = cleaned_data.get(
            "status"
        )

        check_in = cleaned_data.get(
            "check_in"
        )

        check_out = cleaned_data.get(
            "check_out"
        )

        if not employee:
            return cleaned_data

        if not self.request_user:

            raise forms.ValidationError(
                "You are not authorized to manage attendance."
            )

        role = getattr(
            self.request_user,
            "role",
            None,
        )

        # -----------------------------------------------------
        # SUPER ADMIN
        # -----------------------------------------------------

        if role == "SUPER_ADMIN":
            pass

        # -----------------------------------------------------
        # HR ADMIN
        # -----------------------------------------------------

        elif role == "HR_ADMIN":

            try:

                current_employee = (
                    self.request_user.employee_profile
                )

                if (
                    employee.company_id
                    != current_employee.company_id
                ):

                    raise forms.ValidationError(
                        "You can only manage attendance "
                        "within your company."
                    )

            except Employee.DoesNotExist:

                raise forms.ValidationError(
                    "Employee profile not found."
                )

        # -----------------------------------------------------
        # MANAGER
        # -----------------------------------------------------

        elif role == "MANAGER":

            try:

                current_employee = (
                    self.request_user.employee_profile
                )

                if (
                    employee.pk
                    != current_employee.pk
                    and employee.reporting_manager_id
                    != current_employee.pk
                ):

                    raise forms.ValidationError(
                        "You can only manage your own "
                        "attendance or your direct team."
                    )

            except Employee.DoesNotExist:

                raise forms.ValidationError(
                    "Employee profile not found."
                )

        # -----------------------------------------------------
        # EMPLOYEE
        # -----------------------------------------------------

        else:

            try:

                current_employee = (
                    self.request_user.employee_profile
                )

                if employee.pk != current_employee.pk:

                    raise forms.ValidationError(
                        "You can only access your own attendance."
                    )

            except Employee.DoesNotExist:

                raise forms.ValidationError(
                    "Employee profile not found."
                )

        # -----------------------------------------------------
        # SPECIAL STATUS
        # -----------------------------------------------------

        special_statuses = {
            Attendance.Status.ABSENT,
            Attendance.Status.ON_LEAVE,
            Attendance.Status.HOLIDAY,
            Attendance.Status.WEEK_OFF,
        }

        if status in special_statuses:

            if check_in or check_out:

                raise forms.ValidationError(
                    "Check-in and check-out are not allowed "
                    "for this attendance status."
                )

        return cleaned_data