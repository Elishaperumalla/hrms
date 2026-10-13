from django import forms

from .models import (
    EmployeeSalary,
    PayrollPeriod,
    SalaryComponent,
    SalaryStructure,
    SalaryStructureComponent,
)


class SalaryComponentForm(forms.ModelForm):

    class Meta:
        model = SalaryComponent

        fields = [
            "name",
            "code",
            "component_type",
            "calculation_type",
            "percentage_of",
            "default_amount",
            "is_statutory",
            "description",
            "is_active",
        ]

        widgets = {
            "name": forms.TextInput(
                attrs={"class": "form-control"}
            ),
            "code": forms.TextInput(
                attrs={
                    "class": "form-control",
                    "placeholder": "BASIC, HRA, PF..."
                }
            ),
            "component_type": forms.Select(
                attrs={"class": "form-select"}
            ),
            "calculation_type": forms.Select(
                attrs={"class": "form-select"}
            ),
            "percentage_of": forms.Select(
                attrs={"class": "form-select"}
            ),
            "default_amount": forms.NumberInput(
                attrs={
                    "class": "form-control",
                    "step": "0.01",
                    "min": "0",
                }
            ),
            "is_statutory": forms.CheckboxInput(
                attrs={"class": "form-check-input"}
            ),
            "description": forms.Textarea(
                attrs={
                    "class": "form-control",
                    "rows": 3,
                }
            ),
            "is_active": forms.CheckboxInput(
                attrs={"class": "form-check-input"}
            ),
        }

    def clean_code(self):
        return self.cleaned_data["code"].strip().upper()


class SalaryStructureForm(forms.ModelForm):

    class Meta:
        model = SalaryStructure

        fields = [
            "name",
            "code",
            "description",
            "is_active",
        ]

        widgets = {
            "name": forms.TextInput(
                attrs={"class": "form-control"}
            ),
            "code": forms.TextInput(
                attrs={"class": "form-control"}
            ),
            "description": forms.Textarea(
                attrs={
                    "class": "form-control",
                    "rows": 3,
                }
            ),
            "is_active": forms.CheckboxInput(
                attrs={"class": "form-check-input"}
            ),
        }

    def clean_code(self):
        return self.cleaned_data["code"].strip().upper()


class SalaryStructureComponentForm(forms.ModelForm):

    class Meta:
        model = SalaryStructureComponent

        fields = [
            "component",
            "amount",
            "percentage",
            "calculation_order",
            "is_active",
        ]

        widgets = {
            "component": forms.Select(
                attrs={"class": "form-select"}
            ),
            "amount": forms.NumberInput(
                attrs={
                    "class": "form-control",
                    "step": "0.01",
                    "min": "0",
                }
            ),
            "percentage": forms.NumberInput(
                attrs={
                    "class": "form-control",
                    "step": "0.01",
                    "min": "0",
                }
            ),
            "calculation_order": forms.NumberInput(
                attrs={
                    "class": "form-control",
                    "min": "1",
                }
            ),
            "is_active": forms.CheckboxInput(
                attrs={"class": "form-check-input"}
            ),
        }


class EmployeeSalaryForm(forms.ModelForm):

    class Meta:
        model = EmployeeSalary

        fields = [
            "employee",
            "salary_structure",
            "annual_ctc",
            "effective_from",
            "effective_to",
            "notes",
            "is_active",
        ]

        widgets = {
            "employee": forms.Select(
                attrs={"class": "form-select"}
            ),
            "salary_structure": forms.Select(
                attrs={"class": "form-select"}
            ),
            "annual_ctc": forms.NumberInput(
                attrs={
                    "class": "form-control",
                    "step": "0.01",
                    "min": "0",
                }
            ),
            "effective_from": forms.DateInput(
                attrs={
                    "class": "form-control",
                    "type": "date",
                }
            ),
            "effective_to": forms.DateInput(
                attrs={
                    "class": "form-control",
                    "type": "date",
                }
            ),
            "notes": forms.Textarea(
                attrs={
                    "class": "form-control",
                    "rows": 3,
                }
            ),
            "is_active": forms.CheckboxInput(
                attrs={"class": "form-check-input"}
            ),
        }

    def __init__(self, *args, request_user=None, **kwargs):
        super().__init__(*args, **kwargs)

        self.request_user = request_user

        self.fields["employee"].queryset = Employee.objects.filter(
            employment_status__in=[
                Employee.EmploymentStatus.ACTIVE,
                Employee.EmploymentStatus.BENCH,
                Employee.EmploymentStatus.ON_LEAVE,
            ]
        ).select_related(
            "company",
            "branch",
        )

        self.fields["salary_structure"].queryset = (
            SalaryStructure.objects.filter(
                is_active=True
            )
        )


class PayrollPeriodForm(forms.ModelForm):

    class Meta:
        model = PayrollPeriod

        fields = [
            "month",
            "year",
            "start_date",
            "end_date",
            "notes",
        ]

        widgets = {
            "month": forms.Select(
                choices=[
                    (1, "January"),
                    (2, "February"),
                    (3, "March"),
                    (4, "April"),
                    (5, "May"),
                    (6, "June"),
                    (7, "July"),
                    (8, "August"),
                    (9, "September"),
                    (10, "October"),
                    (11, "November"),
                    (12, "December"),
                ],
                attrs={"class": "form-select"},
            ),
            "year": forms.NumberInput(
                attrs={
                    "class": "form-control",
                    "min": "2000",
                    "max": "2100",
                }
            ),
            "start_date": forms.DateInput(
                attrs={
                    "class": "form-control",
                    "type": "date",
                }
            ),
            "end_date": forms.DateInput(
                attrs={
                    "class": "form-control",
                    "type": "date",
                }
            ),
            "notes": forms.Textarea(
                attrs={
                    "class": "form-control",
                    "rows": 3,
                }
            ),
        }

    def clean(self):
        cleaned_data = super().clean()

        start_date = cleaned_data.get("start_date")
        end_date = cleaned_data.get("end_date")
        month = cleaned_data.get("month")
        year = cleaned_data.get("year")

        if start_date and end_date and start_date > end_date:
            raise forms.ValidationError(
                "End date must be after start date."
            )

        if start_date and month and start_date.month != month:
            raise forms.ValidationError(
                "Start date month must match payroll month."
            )

        if start_date and year and start_date.year != year:
            raise forms.ValidationError(
                "Start date year must match payroll year."
            )

        return cleaned_data