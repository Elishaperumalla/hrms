from django import forms

from .models import (
    LeaveType,
    LeaveBalance,
    LeaveRequest,
)


# ============================================================
# LEAVE TYPE FORM
# ============================================================

class LeaveTypeForm(forms.ModelForm):

    class Meta:
        model = LeaveType

        fields = [
            "name",
            "code",
            "description",
            "days_per_year",
            "is_paid",
            "requires_approval",
            "is_active",
        ]

        widgets = {
            "name": forms.TextInput(
                attrs={
                    "class": "form-control",
                    "placeholder": "Leave type name",
                }
            ),

            "code": forms.TextInput(
                attrs={
                    "class": "form-control",
                    "placeholder": "Example: CL",
                }
            ),

            "description": forms.Textarea(
                attrs={
                    "class": "form-control",
                    "rows": 3,
                    "placeholder": "Description",
                }
            ),

            "days_per_year": forms.NumberInput(
                attrs={
                    "class": "form-control",
                    "step": "0.5",
                    "min": "0",
                }
            ),

            "is_paid": forms.CheckboxInput(
                attrs={
                    "class": "form-check-input",
                }
            ),

            "requires_approval": forms.CheckboxInput(
                attrs={
                    "class": "form-check-input",
                }
            ),

            "is_active": forms.CheckboxInput(
                attrs={
                    "class": "form-check-input",
                }
            ),
        }


# ============================================================
# LEAVE REQUEST FORM
# ============================================================

class LeaveRequestForm(forms.ModelForm):

    class Meta:
        model = LeaveRequest

        fields = [
            "leave_type",
            "start_date",
            "end_date",
            "duration_type",
            "reason",
            "attachment",
        ]

        widgets = {
            "leave_type": forms.Select(
                attrs={
                    "class": "form-select",
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

            "duration_type": forms.Select(
                attrs={
                    "class": "form-select",
                }
            ),

            "reason": forms.Textarea(
                attrs={
                    "class": "form-control",
                    "rows": 4,
                    "placeholder": "Reason for leave",
                }
            ),

            "attachment": forms.ClearableFileInput(
                attrs={
                    "class": "form-control",
                }
            ),
        }

    def clean(self):

        cleaned_data = super().clean()

        start_date = cleaned_data.get("start_date")
        end_date = cleaned_data.get("end_date")

        if start_date and end_date:

            if end_date < start_date:
                raise forms.ValidationError(
                    "End date cannot be before start date."
                )

        return cleaned_data


# ============================================================
# LEAVE APPROVAL FORM
# ============================================================

class LeaveApprovalForm(forms.Form):

    ACTION_CHOICES = [
        (
            "APPROVE",
            "Approve",
        ),
        (
            "REJECT",
            "Reject",
        ),
        (
            "CANCEL",
            "Cancel",
        ),
    ]

    action = forms.ChoiceField(
        choices=ACTION_CHOICES,
        widget=forms.Select(
            attrs={
                "class": "form-select",
            }
        ),
    )

    reason = forms.CharField(
        required=False,
        widget=forms.Textarea(
            attrs={
                "class": "form-control",
                "rows": 4,
                "placeholder": "Enter reason",
            }
        ),
    )

    def clean(self):

        cleaned_data = super().clean()

        action = cleaned_data.get("action")
        reason = cleaned_data.get("reason")

        if action in [
            "REJECT",
            "CANCEL",
        ] and not reason:

            raise forms.ValidationError(
                "A reason is required for rejection or cancellation."
            )

        return cleaned_data


# ============================================================
# LEAVE BALANCE FORM
# ============================================================

class LeaveBalanceForm(forms.ModelForm):

    class Meta:
        model = LeaveBalance

        fields = [
            "employee",
            "leave_type",
            "year",
            "allocated_days",
            "carried_forward_days",
        ]

        widgets = {
            "employee": forms.Select(
                attrs={
                    "class": "form-select",
                }
            ),

            "leave_type": forms.Select(
                attrs={
                    "class": "form-select",
                }
            ),

            "year": forms.NumberInput(
                attrs={
                    "class": "form-control",
                    "min": "2000",
                }
            ),

            "allocated_days": forms.NumberInput(
                attrs={
                    "class": "form-control",
                    "step": "0.5",
                    "min": "0",
                }
            ),

            "carried_forward_days": forms.NumberInput(
                attrs={
                    "class": "form-control",
                    "step": "0.5",
                    "min": "0",
                }
            ),
        }

    def clean(self):

        cleaned_data = super().clean()

        allocated_days = cleaned_data.get(
            "allocated_days"
        )

        carried_forward_days = cleaned_data.get(
            "carried_forward_days"
        )

        if (
            allocated_days is not None
            and allocated_days < 0
        ):
            raise forms.ValidationError(
                "Allocated days cannot be negative."
            )

        if (
            carried_forward_days is not None
            and carried_forward_days < 0
        ):
            raise forms.ValidationError(
                "Carried forward days cannot be negative."
            )

        return cleaned_data