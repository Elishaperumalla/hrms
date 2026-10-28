from django import forms

from .models import (
    Company,
    Department,
    Designation,
    Branch,
    WorkLocation,
    OfficeAttendanceSettings,
)


class GPSConfigFormMixin:
    """Shared styling and validation for company/branch GPS settings."""

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        for name in ("latitude", "longitude", "radius_meters"):
            self.fields[name].widget.attrs.setdefault("class", "form-control")

        self.fields["latitude"].widget.attrs.update({
            "step": "any",
            "placeholder": "Latitude",
        })
        self.fields["longitude"].widget.attrs.update({
            "step": "any",
            "placeholder": "Longitude",
        })
        self.fields["radius_meters"].widget.attrs.update({
            "min": "1",
            "max": "50000",
        })

    def clean_latitude(self):
        value = self.cleaned_data.get("latitude")
        if value is not None and not -90 <= value <= 90:
            raise forms.ValidationError("Latitude must be between -90 and 90.")
        return value

    def clean_longitude(self):
        value = self.cleaned_data.get("longitude")
        if value is not None and not -180 <= value <= 180:
            raise forms.ValidationError("Longitude must be between -180 and 180.")
        return value

    def clean_radius_meters(self):
        value = self.cleaned_data.get("radius_meters")
        if value is None or not 1 <= value <= 50000:
            raise forms.ValidationError("Radius must be between 1 and 50000 meters.")
        return value

    def clean(self):
        cleaned = super().clean()
        latitude = cleaned.get("latitude")
        longitude = cleaned.get("longitude")

        if (latitude is None) != (longitude is None):
            raise forms.ValidationError(
                "Enter both latitude and longitude, or leave both empty."
            )
        return cleaned


# =========================================================
# COMPANY FORM
# =========================================================

class CompanyForm(GPSConfigFormMixin, forms.ModelForm):

    class Meta:

        model = Company

        fields = [
            "name",
            "legal_name",
            "email",
            "phone",
            "website",
            "address",
            "city",
            "state",
            "country",
            "postal_code",
            "latitude",
            "longitude",
            "radius_meters",
            "logo",
            "established_date",
            "is_active",
        ]

        widgets = {

            "name": forms.TextInput(
                attrs={
                    "class": "form-control",
                    "placeholder": "Company name",
                }
            ),

            "legal_name": forms.TextInput(
                attrs={
                    "class": "form-control",
                    "placeholder": "Legal company name",
                }
            ),

            "email": forms.EmailInput(
                attrs={
                    "class": "form-control",
                    "placeholder": "company@example.com",
                }
            ),

            "phone": forms.TextInput(
                attrs={
                    "class": "form-control",
                    "placeholder": "Phone number",
                }
            ),

            "website": forms.URLInput(
                attrs={
                    "class": "form-control",
                    "placeholder": "https://example.com",
                }
            ),

            "address": forms.Textarea(
                attrs={
                    "class": "form-control",
                    "placeholder": "Company address",
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

            "logo": forms.ClearableFileInput(
                attrs={
                    "class": "form-control",
                }
            ),

            "established_date": forms.DateInput(
                attrs={
                    "class": "form-control",
                    "type": "date",
                }
            ),

            "is_active": forms.CheckboxInput(
                attrs={
                    "class": "form-check-input",
                }
            ),
        }


# =========================================================
# DEPARTMENT FORM
# =========================================================

class DepartmentForm(forms.ModelForm):

    class Meta:

        model = Department

        fields = [
            "company",
            "name",
            "code",
            "description",
            "is_active",
        ]

        widgets = {

            "company": forms.Select(
                attrs={
                    "class": "form-select",
                }
            ),

            "name": forms.TextInput(
                attrs={
                    "class": "form-control",
                    "placeholder": "Department name",
                }
            ),

            "code": forms.TextInput(
                attrs={
                    "class": "form-control",
                    "placeholder": "Department code",
                }
            ),

            "description": forms.Textarea(
                attrs={
                    "class": "form-control",
                    "placeholder": "Department description",
                    "rows": 3,
                }
            ),

            "is_active": forms.CheckboxInput(
                attrs={
                    "class": "form-check-input",
                }
            ),
        }


# =========================================================
# DESIGNATION FORM
# =========================================================

class DesignationForm(forms.ModelForm):

    class Meta:

        model = Designation

        fields = [
            "company",
            "name",
            "code",
            "description",
            "level",
            "is_active",
        ]

        widgets = {

            "company": forms.Select(
                attrs={
                    "class": "form-select",
                }
            ),

            "name": forms.TextInput(
                attrs={
                    "class": "form-control",
                    "placeholder": "Designation name",
                }
            ),

            "code": forms.TextInput(
                attrs={
                    "class": "form-control",
                    "placeholder": "Designation code",
                }
            ),

            "description": forms.Textarea(
                attrs={
                    "class": "form-control",
                    "placeholder": "Designation description",
                    "rows": 3,
                }
            ),

            "level": forms.NumberInput(
                attrs={
                    "class": "form-control",
                    "min": 1,
                    "placeholder": "Hierarchy level",
                }
            ),

            "is_active": forms.CheckboxInput(
                attrs={
                    "class": "form-check-input",
                }
            ),
        }


# =========================================================
# BRANCH FORM
# =========================================================

class BranchForm(GPSConfigFormMixin, forms.ModelForm):

    class Meta:

        model = Branch

        fields = [
            "company",
            "name",
            "code",
            "address",
            "city",
            "state",
            "country",
            "postal_code",
            "latitude",
            "longitude",
            "radius_meters",
            "phone",
            "email",
            "is_head_office",
            "is_active",
        ]

        widgets = {

            "company": forms.Select(
                attrs={
                    "class": "form-select",
                }
            ),

            "name": forms.TextInput(
                attrs={
                    "class": "form-control",
                    "placeholder": "Branch name",
                }
            ),

            "code": forms.TextInput(
                attrs={
                    "class": "form-control",
                    "placeholder": "Branch code",
                }
            ),

            "address": forms.Textarea(
                attrs={
                    "class": "form-control",
                    "placeholder": "Branch address",
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

            "phone": forms.TextInput(
                attrs={
                    "class": "form-control",
                    "placeholder": "Phone number",
                }
            ),

            "email": forms.EmailInput(
                attrs={
                    "class": "form-control",
                    "placeholder": "branch@example.com",
                }
            ),

            "is_head_office": forms.CheckboxInput(
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


# =========================================================
# WORK LOCATION FORM
# =========================================================

class WorkLocationForm(forms.ModelForm):

    class Meta:

        model = WorkLocation

        fields = [
            "company",
            "name",
            "address",
            "city",
            "state",
            "country",
            "postal_code",
            "latitude",
            "longitude",
            "location_type",
            "is_active",
        ]

        widgets = {

            "company": forms.Select(
                attrs={
                    "class": "form-select",
                }
            ),

            "name": forms.TextInput(
                attrs={
                    "class": "form-control",
                    "placeholder": "Work location name",
                }
            ),

            "address": forms.Textarea(
                attrs={
                    "class": "form-control",
                    "placeholder": "Work location address",
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

            "latitude": forms.NumberInput(attrs={
                "class": "form-control",
                "step": "any",
                "placeholder": "Latitude",
            }),

            "longitude": forms.NumberInput(attrs={
                "class": "form-control",
                "step": "any",
                "placeholder": "Longitude",
            }),

            "location_type": forms.Select(
                attrs={
                    "class": "form-select",
                }
            ),

            "is_active": forms.CheckboxInput(
                attrs={
                    "class": "form-check-input",
                }
            ),
        }

class OfficeAttendanceSettingsForm(forms.ModelForm):
    class Meta:
        model = OfficeAttendanceSettings
        fields = [
            "name",
            "latitude",
            "longitude",
            "radius_meters",
            "is_active",
        ]
        widgets = {
            "name": forms.TextInput(attrs={
                "class": "form-control",
                "placeholder": "Main Office",
            }),
            "latitude": forms.NumberInput(attrs={
                "class": "form-control",
                "step": "any",
                "placeholder": "e.g. 17.3850",
            }),
            "longitude": forms.NumberInput(attrs={
                "class": "form-control",
                "step": "any",
                "placeholder": "e.g. 78.4867",
            }),
            "radius_meters": forms.NumberInput(attrs={
                "class": "form-control",
                "min": "1",
                "max": "50000",
            }),
            "is_active": forms.CheckboxInput(attrs={
                "class": "form-check-input",
            }),
        }

    def clean_latitude(self):
        value = self.cleaned_data.get("latitude")
        if value is not None and not -90 <= value <= 90:
            raise forms.ValidationError("Latitude must be between -90 and 90.")
        return value

    def clean_longitude(self):
        value = self.cleaned_data.get("longitude")
        if value is not None and not -180 <= value <= 180:
            raise forms.ValidationError("Longitude must be between -180 and 180.")
        return value

    def clean_radius_meters(self):
        value = self.cleaned_data.get("radius_meters")
        if value is None or not 1 <= value <= 50000:
            raise forms.ValidationError("Radius must be between 1 and 50000 meters.")
        return value

    def clean(self):
        cleaned = super().clean()
        latitude = cleaned.get("latitude")
        longitude = cleaned.get("longitude")

        if (latitude is None) != (longitude is None):
            raise forms.ValidationError(
                "Enter both latitude and longitude, or leave both empty."
            )
        return cleaned
