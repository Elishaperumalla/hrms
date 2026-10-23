from django import forms
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.core.exceptions import ValidationError
from django.db import transaction
from django.shortcuts import redirect, render
from django.utils import timezone

from .models import User
from employees.models import Employee


MAX_PHOTO_SIZE = 5 * 1024 * 1024


class UserProfileForm(forms.ModelForm):
    class Meta:
        model = User
        fields = ["first_name", "last_name", "email", "phone"]
        widgets = {
            "first_name": forms.TextInput(attrs={"class": "form-control"}),
            "last_name": forms.TextInput(attrs={"class": "form-control"}),
            "email": forms.EmailInput(attrs={"class": "form-control"}),
            "phone": forms.TextInput(attrs={"class": "form-control"}),
        }


class StandaloneUserProfileForm(UserProfileForm):
    class Meta(UserProfileForm.Meta):
        fields = ["first_name", "last_name", "email", "phone",
                  "profile_picture"]
        widgets = {
            **UserProfileForm.Meta.widgets,
            "profile_picture": forms.ClearableFileInput(
                attrs={"class": "form-control", "accept": "image/*"}
            ),
        }

    def clean_profile_picture(self):
        photo = self.cleaned_data.get("profile_picture")
        if photo and photo.size > MAX_PHOTO_SIZE:
            raise ValidationError("Profile photo must be 5 MB or smaller.")
        return photo


class EmployeePersonalForm(forms.ModelForm):
    class Meta:
        model = Employee
        fields = [
            "middle_name",
            "date_of_birth",
            "gender",
            "alternate_phone",
            "address",
            "city",
            "state",
            "country",
            "profile_photo",
        ]
        widgets = {
            "middle_name": forms.TextInput(attrs={"class": "form-control"}),
            "date_of_birth": forms.DateInput(
                attrs={"class": "form-control", "type": "date"}
            ),
            "gender": forms.Select(attrs={"class": "form-select"}),
            "alternate_phone": forms.TextInput(attrs={"class": "form-control"}),
            "address": forms.Textarea(
                attrs={"class": "form-control", "rows": 3}
            ),
            "city": forms.TextInput(attrs={"class": "form-control"}),
            "state": forms.TextInput(attrs={"class": "form-control"}),
            "country": forms.TextInput(attrs={"class": "form-control"}),
            "profile_photo": forms.ClearableFileInput(
                attrs={"class": "form-control", "accept": "image/*"}
            ),
        }

    def clean_profile_photo(self):
        photo = self.cleaned_data.get("profile_photo")
        if photo and photo.size > MAX_PHOTO_SIZE:
            raise ValidationError("Profile photo must be 5 MB or smaller.")
        return photo


@login_required
def edit_profile_view(request):
    employee = getattr(request.user, "employee_profile", None)

    if employee:
        user_form_class = UserProfileForm
    else:
        user_form_class = StandaloneUserProfileForm

    if request.method == "POST":
        user_form = user_form_class(
            request.POST, request.FILES, instance=request.user
        )

        employee_form = (
            EmployeePersonalForm(
                request.POST, request.FILES, instance=employee
            )
            if employee else None
        )

        valid = user_form.is_valid()
        if employee_form:
            valid = employee_form.is_valid() and valid

        if valid:
            with transaction.atomic():
                user = user_form.save()

                if employee and employee_form:
                    employee = employee_form.save(commit=False)

                    # Keep shared personal details consistent.
                    employee.first_name = user.first_name
                    employee.last_name = user.last_name
                    employee.email = user.email
                    employee.phone = user.phone or ""

                    employee.save()

            messages.success(
                request, "Your profile has been updated successfully."
            )
            return redirect("profile")
    else:
        user_form = user_form_class(instance=request.user)
        employee_form = (
            EmployeePersonalForm(instance=employee) if employee else None
        )

    return render(
        request,
        "account/edit_profile.html",
        {
            "user_form": user_form,
            "employee_form": employee_form,
            "employee": employee,
        },
    )
