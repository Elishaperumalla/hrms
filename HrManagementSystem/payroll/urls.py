from django.urls import path
from . import views

app_name = "payroll"

urlpatterns = [
    path("", views.payroll_dashboard, name="payroll_dashboard"),

    path("components/", views.component_list, name="component_list"),
    path("components/add/", views.component_create, name="component_create"),
    path("components/<int:pk>/edit/", views.component_update, name="component_update"),
    path("components/<int:pk>/delete/", views.component_delete, name="component_delete"),

    path("salaries/", views.salary_list, name="salary_list"),
    path("salaries/add/", views.salary_create, name="salary_create"),
    path("salaries/<int:pk>/", views.salary_detail, name="salary_detail"),
    path("salaries/<int:pk>/edit/", views.salary_update, name="salary_update"),

    path("periods/", views.period_list, name="period_list"),
    path("periods/add/", views.period_create, name="period_create"),
    path("periods/<int:pk>/", views.period_detail, name="period_detail"),
    path("periods/<int:pk>/process/", views.process_payroll, name="process_payroll"),
    path("periods/<int:pk>/mark-paid/", views.mark_payroll_paid, name="mark_payroll_paid"),

    path("payslips/", views.payslip_list, name="payslip_list"),
    path("payslips/<int:pk>/", views.payslip_detail, name="payslip_detail"),
    path("payslips/<int:pk>/print/", views.payslip_print, name="payslip_print"),
]