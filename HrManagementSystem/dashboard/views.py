# # from django.contrib.auth.decorators import login_required
# # from django.db.models import Count, Q
# # from django.shortcuts import render
# # from django.utils import timezone

# # from employees.models import Employee

# # from organization.models import (
# #     Company,
# #     Department,
# #     Branch,
# #     WorkLocation,
# # )


# # # =========================================================
# # # DASHBOARD
# # # =========================================================

# # @login_required
# # def dashboard(request):

# #     user = request.user

# #     current_employee = getattr(
# #         user,
# #         "employee_profile",
# #         None,
# #     )

# #     # =====================================================
# #     # SUPER ADMIN
# #     # =====================================================

# #     if (
# #         user.is_superuser
# #         or (
# #             current_employee
# #             and current_employee.role
# #             == Employee.Role.SUPER_ADMIN
# #         )
# #     ):

# #         today = timezone.localdate()

# #         employees = Employee.objects.exclude(
# #             role=Employee.Role.SUPER_ADMIN
# #         )

# #         active_statuses = [
# #             Employee.EmploymentStatus.ACTIVE,
# #             Employee.EmploymentStatus.ON_LEAVE,
# #             Employee.EmploymentStatus.BENCH,
# #         ]

# #         workforce = employees.filter(
# #             employment_status__in=active_statuses
# #         )

# #         total_employees = workforce.count()

# #         active_employees = workforce.filter(
# #             employment_status=(
# #                 Employee.EmploymentStatus.ACTIVE
# #             )
# #         ).count()

# #         on_leave_employees = workforce.filter(
# #             employment_status=(
# #                 Employee.EmploymentStatus.ON_LEAVE
# #             )
# #         ).count()

# #         bench_employees = workforce.filter(
# #             employment_status=(
# #                 Employee.EmploymentStatus.BENCH
# #             )
# #         ).count()

# #         total_hr = workforce.filter(
# #             role=Employee.Role.HR_ADMIN
# #         ).count()

# #         active_hr = workforce.filter(
# #             role=Employee.Role.HR_ADMIN,
# #             employment_status=(
# #                 Employee.EmploymentStatus.ACTIVE
# #             ),
# #         ).count()

# #         total_managers = workforce.filter(
# #             role=Employee.Role.MANAGER
# #         ).count()

# #         active_managers = workforce.filter(
# #             role=Employee.Role.MANAGER,
# #             employment_status=(
# #                 Employee.EmploymentStatus.ACTIVE
# #             ),
# #         ).count()

# #         departments = (
# #             Department.objects
# #             .select_related("company")
# #             .annotate(
# #                 employee_count=Count(
# #                     "employees",
# #                     filter=Q(
# #                         employees__employment_status__in=(
# #                             active_statuses
# #                         )
# #                     ),
# #                     distinct=True,
# #                 ),
# #                 manager_count=Count(
# #                     "employees",
# #                     filter=Q(
# #                         employees__role=(
# #                             Employee.Role.MANAGER
# #                         ),
# #                         employees__employment_status__in=(
# #                             active_statuses
# #                         ),
# #                     ),
# #                     distinct=True,
# #                 ),
# #                 hr_count=Count(
# #                     "employees",
# #                     filter=Q(
# #                         employees__role=(
# #                             Employee.Role.HR_ADMIN
# #                         ),
# #                         employees__employment_status__in=(
# #                             active_statuses
# #                         ),
# #                     ),
# #                     distinct=True,
# #                 ),
# #             )
# #             .order_by("name")
# #         )

# #         companies = Company.objects.all().order_by(
# #             "name"
# #         )

# #         branches = (
# #             Branch.objects
# #             .select_related("company")
# #             .order_by("name")
# #         )

# #         for branch in branches:

# #             branch.employee_count = workforce.filter(
# #                 branch=branch
# #             ).count()

# #         work_locations = (
# #             WorkLocation.objects
# #             .select_related("company")
# #             .order_by("name")
# #         )

# #         for location in work_locations:

# #             location.employee_count = workforce.filter(
# #                 work_location=location
# #             ).count()

# #         active_departments = departments.filter(
# #             is_active=True
# #         ).count()

# #         active_branches = Branch.objects.filter(
# #             is_active=True
# #         ).count()

# #         active_locations = WorkLocation.objects.filter(
# #             is_active=True
# #         ).count()

# #         department_data = []

# #         for department in departments:

# #             department_employees = workforce.filter(
# #                 department=department
# #             )

# #             department_data.append(
# #                 {
# #                     "department": department,

# #                     "employee_count":
# #                         department_employees.count(),

# #                     "active_count":
# #                         department_employees.filter(
# #                             employment_status=(
# #                                 Employee.EmploymentStatus.ACTIVE
# #                             )
# #                         ).count(),

# #                     "manager_count":
# #                         department_employees.filter(
# #                             role=Employee.Role.MANAGER
# #                         ).count(),

# #                     "hr_count":
# #                         department_employees.filter(
# #                             role=Employee.Role.HR_ADMIN
# #                         ).count(),
# #                 }
# #             )

# #         context = {

# #             "user": user,
# #             "current_employee": current_employee,
# #             "today": today,

# #             "total_employees": total_employees,
# #             "active_employees": active_employees,
# #             "on_leave_employees": on_leave_employees,
# #             "bench_employees": bench_employees,

# #             "total_hr": total_hr,
# #             "active_hr": active_hr,

# #             "total_managers": total_managers,
# #             "active_managers": active_managers,

# #             "total_departments":
# #                 departments.count(),

# #             "active_departments":
# #                 active_departments,

# #             "total_branches":
# #                 branches.count(),

# #             "active_branches":
# #                 active_branches,

# #             "total_locations":
# #                 work_locations.count(),

# #             "active_locations":
# #                 active_locations,

# #             "total_companies":
# #                 companies.count(),

# #             "companies": companies,
# #             "departments": departments,
# #             "department_data": department_data,
# #             "branches": branches,
# #             "work_locations": work_locations,
# #         }

# #         return render(
# #             request,
# #             "dashboard/admin_dashboard.html",
# #             context,
# #         )

# #     # =====================================================
# #     # HR ADMIN
# #     # =====================================================

# #     if (
# #         current_employee
# #         and current_employee.role
# #         == Employee.Role.HR_ADMIN
# #     ):

# #         company_employees = Employee.objects.filter(
# #             company=current_employee.company,
# #             employment_status__in=[
# #                 Employee.EmploymentStatus.ACTIVE,
# #                 Employee.EmploymentStatus.ON_LEAVE,
# #                 Employee.EmploymentStatus.BENCH,
# #             ],
# #         )

# #         context = {

# #             "user": user,
# #             "current_employee": current_employee,

# #             "total_employees":
# #                 company_employees.count(),

# #             "active_employees":
# #                 company_employees.filter(
# #                     employment_status=(
# #                         Employee.EmploymentStatus.ACTIVE
# #                     )
# #                 ).count(),

# #             "on_leave_employees":
# #                 company_employees.filter(
# #                     employment_status=(
# #                         Employee.EmploymentStatus.ON_LEAVE
# #                     )
# #                 ).count(),

# #             "bench_employees":
# #                 company_employees.filter(
# #                     employment_status=(
# #                         Employee.EmploymentStatus.BENCH
# #                     )
# #                 ).count(),

# #             "total_managers":
# #                 company_employees.filter(
# #                     role=Employee.Role.MANAGER
# #                 ).count(),

# #             "total_hr":
# #                 company_employees.filter(
# #                     role=Employee.Role.HR_ADMIN
# #                 ).count(),
# #         }

# #         return render(
# #             request,
# #             "dashboard/hr_dashboard.html",
# #             context,
# #         )

# #     # =====================================================
# #     # MANAGER
# #     # =====================================================

# #     if (
# #         current_employee
# #         and current_employee.role
# #         == Employee.Role.MANAGER
# #     ):

# #         team = Employee.objects.filter(
# #             reporting_manager=current_employee,
# #             employment_status__in=[
# #                 Employee.EmploymentStatus.ACTIVE,
# #                 Employee.EmploymentStatus.ON_LEAVE,
# #                 Employee.EmploymentStatus.BENCH,
# #             ],
# #         )

# #         context = {

# #             "user": user,
# #             "current_employee": current_employee,

# #             "team_count":
# #                 team.count(),

# #             "active_team_count":
# #                 team.filter(
# #                     employment_status=(
# #                         Employee.EmploymentStatus.ACTIVE
# #                     )
# #                 ).count(),

# #             "on_leave_team_count":
# #                 team.filter(
# #                     employment_status=(
# #                         Employee.EmploymentStatus.ON_LEAVE
# #                     )
# #                 ).count(),

# #             "bench_team_count":
# #                 team.filter(
# #                     employment_status=(
# #                         Employee.EmploymentStatus.BENCH
# #                     )
# #                 ).count(),

# #             "team_members":
# #                 team.select_related(
# #                     "department",
# #                     "designation",
# #                 ),
# #         }

# #         return render(
# #             request,
# #             "dashboard/manager_dashboard.html",
# #             context,
# #         )

# #     # =====================================================
# #     # RECRUITER
# #     # =====================================================

# #     if getattr(user, "role", None) == "RECRUITER":

# #         return render(
# #             request,
# #             "dashboard/recruiter_dashboard.html",
# #             {
# #                 "user": user,
# #                 "current_employee": current_employee,
# #             },
# #         )

# #     # =====================================================
# #     # PAYROLL ADMIN
# #     # =====================================================

# #     if getattr(user, "role", None) == "PAYROLL_ADMIN":

# #         return render(
# #             request,
# #             "dashboard/payroll_dashboard.html",
# #             {
# #                 "user": user,
# #                 "current_employee": current_employee,
# #             },
# #         )

# #     # =====================================================
# #     # EMPLOYEE
# #     # =====================================================

# #     return render(
# #         request,
# #         "dashboard/employee_dashboard.html",
# #         {
# #             "user": user,
# #             "current_employee": current_employee,
# #         },
# #     )





# from django.contrib.auth.decorators import login_required
# from django.db.models import Count, Q
# from django.shortcuts import render
# from django.utils import timezone

# from employees.models import Employee
# from leaves.models import LeaveRequest

# from organization.models import (
#     Company,
#     Department,
#     Branch,
#     WorkLocation,
# )


# # =========================================================
# # HELPER — CURRENT APPROVED LEAVE EMPLOYEES
# # =========================================================

# def get_current_on_leave_employee_ids(
#     employees,
#     today=None,
# ):
#     """
#     Return employee IDs who are currently on APPROVED leave.

#     Current leave means:

#         APPROVED
#         start_date <= today
#         end_date >= today
#     """

#     if today is None:
#         today = timezone.localdate()

#     employee_ids = employees.values_list(
#         "pk",
#         flat=True,
#     )

#     return set(
#         LeaveRequest.objects.filter(
#             employee_id__in=employee_ids,
#             status=LeaveRequest.Status.APPROVED,
#             start_date__lte=today,
#             end_date__gte=today,
#         )
#         .values_list(
#             "employee_id",
#             flat=True,
#         )
#         .distinct()
#     )


# # =========================================================
# # HELPER — MARK CURRENT LEAVE
# # =========================================================

# def mark_current_leave_status(
#     employees,
#     on_leave_employee_ids,
# ):
#     """
#     Add is_currently_on_leave attribute to Employee objects.
#     """

#     for employee in employees:

#         employee.is_currently_on_leave = (
#             employee.pk in on_leave_employee_ids
#         )

#     return employees


# # =========================================================
# # DASHBOARD
# # =========================================================

# @login_required
# def dashboard(request):

#     user = request.user

#     current_employee = getattr(
#         user,
#         "employee_profile",
#         None,
#     )

#     today = timezone.localdate()

#     # =====================================================
#     # SUPER ADMIN
#     # =====================================================

#     if (
#         user.is_superuser
#         or (
#             current_employee
#             and current_employee.role
#             == Employee.Role.SUPER_ADMIN
#         )
#     ):

#         # -------------------------------------------------
#         # WORKFORCE
#         # -------------------------------------------------

#         employees = (
#             Employee.objects
#             .exclude(
#                 role=Employee.Role.SUPER_ADMIN
#             )
#         )

#         active_statuses = [
#             Employee.EmploymentStatus.ACTIVE,
#             Employee.EmploymentStatus.ON_LEAVE,
#             Employee.EmploymentStatus.BENCH,
#         ]

#         workforce = employees.filter(
#             employment_status__in=active_statuses
#         )

#         # -------------------------------------------------
#         # CURRENT APPROVED LEAVE
#         # -------------------------------------------------

#         on_leave_employee_ids = (
#             get_current_on_leave_employee_ids(
#                 workforce,
#                 today,
#             )
#         )

#         # -------------------------------------------------
#         # COUNTS
#         # -------------------------------------------------

#         total_employees = workforce.count()

#         bench_employees = workforce.filter(
#             employment_status=(
#                 Employee.EmploymentStatus.BENCH
#             )
#         ).count()

#         on_leave_employees = len(
#             on_leave_employee_ids
#         )

#         active_employees = (
#             workforce
#             .filter(
#                 employment_status=(
#                     Employee.EmploymentStatus.ACTIVE
#                 )
#             )
#             .exclude(
#                 pk__in=on_leave_employee_ids
#             )
#             .count()
#         )

#         # -------------------------------------------------
#         # HR
#         # -------------------------------------------------

#         total_hr = workforce.filter(
#             role=Employee.Role.HR_ADMIN
#         ).count()

#         active_hr = (
#             workforce
#             .filter(
#                 role=Employee.Role.HR_ADMIN,
#                 employment_status=(
#                     Employee.EmploymentStatus.ACTIVE
#                 ),
#             )
#             .exclude(
#                 pk__in=on_leave_employee_ids
#             )
#             .count()
#         )

#         # -------------------------------------------------
#         # MANAGERS
#         # -------------------------------------------------

#         total_managers = workforce.filter(
#             role=Employee.Role.MANAGER
#         ).count()

#         active_managers = (
#             workforce
#             .filter(
#                 role=Employee.Role.MANAGER,
#                 employment_status=(
#                     Employee.EmploymentStatus.ACTIVE
#                 ),
#             )
#             .exclude(
#                 pk__in=on_leave_employee_ids
#             )
#             .count()
#         )

#         # -------------------------------------------------
#         # DEPARTMENTS
#         # -------------------------------------------------

#         departments = (
#             Department.objects
#             .select_related("company")
#             .annotate(
#                 employee_count=Count(
#                     "employees",
#                     filter=Q(
#                         employees__employment_status__in=(
#                             active_statuses
#                         )
#                     ),
#                     distinct=True,
#                 ),
#                 manager_count=Count(
#                     "employees",
#                     filter=Q(
#                         employees__role=(
#                             Employee.Role.MANAGER
#                         ),
#                         employees__employment_status__in=(
#                             active_statuses
#                         ),
#                     ),
#                     distinct=True,
#                 ),
#                 hr_count=Count(
#                     "employees",
#                     filter=Q(
#                         employees__role=(
#                             Employee.Role.HR_ADMIN
#                         ),
#                         employees__employment_status__in=(
#                             active_statuses
#                         ),
#                     ),
#                     distinct=True,
#                 ),
#             )
#             .order_by("name")
#         )

#         # -------------------------------------------------
#         # COMPANIES
#         # -------------------------------------------------

#         companies = (
#             Company.objects
#             .all()
#             .order_by("name")
#         )

#         # -------------------------------------------------
#         # BRANCHES
#         # -------------------------------------------------

#         branches = (
#             Branch.objects
#             .select_related("company")
#             .order_by("name")
#         )

#         for branch in branches:

#             branch.employee_count = (
#                 workforce
#                 .filter(
#                     branch=branch
#                 )
#                 .count()
#             )

#         # -------------------------------------------------
#         # WORK LOCATIONS
#         # -------------------------------------------------

#         work_locations = (
#             WorkLocation.objects
#             .select_related("company")
#             .order_by("name")
#         )

#         for location in work_locations:

#             location.employee_count = (
#                 workforce
#                 .filter(
#                     work_location=location
#                 )
#                 .count()
#             )

#         # -------------------------------------------------
#         # ACTIVE ORGANIZATION COUNTS
#         # -------------------------------------------------

#         active_departments = (
#             departments
#             .filter(
#                 is_active=True
#             )
#             .count()
#         )

#         active_branches = (
#             Branch.objects
#             .filter(
#                 is_active=True
#             )
#             .count()
#         )

#         active_locations = (
#             WorkLocation.objects
#             .filter(
#                 is_active=True
#             )
#             .count()
#         )

#         # -------------------------------------------------
#         # DEPARTMENT DATA
#         # -------------------------------------------------

#         department_data = []

#         for department in departments:

#             department_employees = (
#                 workforce
#                 .filter(
#                     department=department
#                 )
#             )

#             department_employee_ids = set(
#                 department_employees.values_list(
#                     "pk",
#                     flat=True,
#                 )
#             )

#             department_on_leave_ids = (
#                 on_leave_employee_ids
#                 & department_employee_ids
#             )

#             department_data.append(
#                 {
#                     "department":
#                         department,

#                     "employee_count":
#                         department_employees.count(),

#                     "active_count":
#                         department_employees
#                         .filter(
#                             employment_status=(
#                                 Employee.EmploymentStatus.ACTIVE
#                             )
#                         )
#                         .exclude(
#                             pk__in=department_on_leave_ids
#                         )
#                         .count(),

#                     "on_leave_count":
#                         len(
#                             department_on_leave_ids
#                         ),

#                     "manager_count":
#                         department_employees
#                         .filter(
#                             role=(
#                                 Employee.Role.MANAGER
#                             )
#                         )
#                         .count(),

#                     "hr_count":
#                         department_employees
#                         .filter(
#                             role=(
#                                 Employee.Role.HR_ADMIN
#                             )
#                         )
#                         .count(),
#                 }
#             )

#         # -------------------------------------------------
#         # CONTEXT
#         # -------------------------------------------------

#         context = {

#             "user":
#                 user,

#             "current_employee":
#                 current_employee,

#             "today":
#                 today,

#             "total_employees":
#                 total_employees,

#             "active_employees":
#                 active_employees,

#             "on_leave_employees":
#                 on_leave_employees,

#             "bench_employees":
#                 bench_employees,

#             "total_hr":
#                 total_hr,

#             "active_hr":
#                 active_hr,

#             "total_managers":
#                 total_managers,

#             "active_managers":
#                 active_managers,

#             "total_departments":
#                 departments.count(),

#             "active_departments":
#                 active_departments,

#             "total_branches":
#                 branches.count(),

#             "active_branches":
#                 active_branches,

#             "total_locations":
#                 work_locations.count(),

#             "active_locations":
#                 active_locations,

#             "total_companies":
#                 companies.count(),

#             "companies":
#                 companies,

#             "departments":
#                 departments,

#             "department_data":
#                 department_data,

#             "branches":
#                 branches,

#             "work_locations":
#                 work_locations,
#         }

#         return render(
#             request,
#             "dashboard/admin_dashboard.html",
#             context,
#         )

#     # =====================================================
#     # HR ADMIN
#     # =====================================================

#     if (
#         current_employee
#         and current_employee.role
#         == Employee.Role.HR_ADMIN
#     ):

#         # -------------------------------------------------
#         # COMPANY EMPLOYEES
#         # -------------------------------------------------

#         company_employees = (
#             Employee.objects
#             .filter(
#                 company=current_employee.company,
#                 employment_status__in=[
#                     Employee.EmploymentStatus.ACTIVE,
#                     Employee.EmploymentStatus.ON_LEAVE,
#                     Employee.EmploymentStatus.BENCH,
#                 ],
#             )
#             .select_related(
#                 "company",
#                 "department",
#                 "designation",
#                 "reporting_manager",
#             )
#             .order_by(
#                 "first_name",
#                 "last_name",
#             )
#         )

#         # -------------------------------------------------
#         # CURRENT APPROVED LEAVE
#         # -------------------------------------------------

#         on_leave_employee_ids = (
#             get_current_on_leave_employee_ids(
#                 company_employees,
#                 today,
#             )
#         )

#         # -------------------------------------------------
#         # COUNTS
#         # -------------------------------------------------

#         total_employees = (
#             company_employees.count()
#         )

#         bench_employees = (
#             company_employees
#             .filter(
#                 employment_status=(
#                     Employee.EmploymentStatus.BENCH
#                 )
#             )
#             .count()
#         )

#         on_leave_employees = len(
#             on_leave_employee_ids
#         )

#         active_employees = (
#             company_employees
#             .filter(
#                 employment_status=(
#                     Employee.EmploymentStatus.ACTIVE
#                 )
#             )
#             .exclude(
#                 pk__in=on_leave_employee_ids
#             )
#             .count()
#         )

#         total_managers = (
#             company_employees
#             .filter(
#                 role=Employee.Role.MANAGER
#             )
#             .count()
#         )

#         active_managers = (
#             company_employees
#             .filter(
#                 role=Employee.Role.MANAGER,
#                 employment_status=(
#                     Employee.EmploymentStatus.ACTIVE
#                 ),
#             )
#             .exclude(
#                 pk__in=on_leave_employee_ids
#             )
#             .count()
#         )

#         total_hr = (
#             company_employees
#             .filter(
#                 role=Employee.Role.HR_ADMIN
#             )
#             .count()
#         )

#         active_hr = (
#             company_employees
#             .filter(
#                 role=Employee.Role.HR_ADMIN,
#                 employment_status=(
#                     Employee.EmploymentStatus.ACTIVE
#                 ),
#             )
#             .exclude(
#                 pk__in=on_leave_employee_ids
#             )
#             .count()
#         )

#         # -------------------------------------------------
#         # MARK CURRENT LEAVE
#         # -------------------------------------------------

#         company_employees = list(
#             company_employees
#         )

#         mark_current_leave_status(
#             company_employees,
#             on_leave_employee_ids,
#         )

#         # -------------------------------------------------
#         # CONTEXT
#         # -------------------------------------------------

#         context = {

#             "user":
#                 user,

#             "current_employee":
#                 current_employee,

#             "today":
#                 today,

#             "total_employees":
#                 total_employees,

#             "active_employees":
#                 active_employees,

#             "on_leave_employees":
#                 on_leave_employees,

#             "bench_employees":
#                 bench_employees,

#             "total_managers":
#                 total_managers,

#             "active_managers":
#                 active_managers,

#             "total_hr":
#                 total_hr,

#             "active_hr":
#                 active_hr,

#             "company_employees":
#                 company_employees,
#         }

#         return render(
#             request,
#             "dashboard/hr_dashboard.html",
#             context,
#         )

#     # =====================================================
#     # MANAGER
#     # =====================================================

#     if (
#         current_employee
#         and current_employee.role
#         == Employee.Role.MANAGER
#     ):

#         # -------------------------------------------------
#         # DIRECT TEAM
#         # -------------------------------------------------

#         team_queryset = (
#             Employee.objects
#             .filter(
#                 reporting_manager=current_employee,
#                 employment_status__in=[
#                     Employee.EmploymentStatus.ACTIVE,
#                     Employee.EmploymentStatus.ON_LEAVE,
#                     Employee.EmploymentStatus.BENCH,
#                 ],
#             )
#             .select_related(
#                 "department",
#                 "designation",
#                 "company",
#             )
#             .order_by(
#                 "first_name",
#                 "last_name",
#             )
#         )

#         # -------------------------------------------------
#         # CURRENT APPROVED LEAVE
#         # -------------------------------------------------

#         on_leave_employee_ids = (
#             get_current_on_leave_employee_ids(
#                 team_queryset,
#                 today,
#             )
#         )

#         # -------------------------------------------------
#         # COUNTS
#         # -------------------------------------------------

#         team_count = (
#             team_queryset.count()
#         )

#         bench_team_count = (
#             team_queryset
#             .filter(
#                 employment_status=(
#                     Employee.EmploymentStatus.BENCH
#                 )
#             )
#             .count()
#         )

#         on_leave_team_count = len(
#             on_leave_employee_ids
#         )

#         active_team_count = (
#             team_queryset
#             .filter(
#                 employment_status=(
#                     Employee.EmploymentStatus.ACTIVE
#                 )
#             )
#             .exclude(
#                 pk__in=on_leave_employee_ids
#             )
#             .count()
#         )

#         # -------------------------------------------------
#         # MARK TEAM MEMBERS
#         # -------------------------------------------------

#         team_members = list(
#             team_queryset
#         )

#         mark_current_leave_status(
#             team_members,
#             on_leave_employee_ids,
#         )

#         # -------------------------------------------------
#         # CONTEXT
#         # -------------------------------------------------

#         context = {

#             "user":
#                 user,

#             "current_employee":
#                 current_employee,

#             "today":
#                 today,

#             "team_count":
#                 team_count,

#             "active_team_count":
#                 active_team_count,

#             "on_leave_team_count":
#                 on_leave_team_count,

#             "bench_team_count":
#                 bench_team_count,

#             "team_members":
#                 team_members,
#         }

#         return render(
#             request,
#             "dashboard/manager_dashboard.html",
#             context,
#         )

#     # =====================================================
#     # RECRUITER
#     # =====================================================

#     if (
#         getattr(
#             user,
#             "role",
#             None,
#         )
#         == "RECRUITER"
#     ):

#         return render(
#             request,
#             "dashboard/recruiter_dashboard.html",
#             {
#                 "user":
#                     user,

#                 "current_employee":
#                     current_employee,
#             },
#         )

#     # =====================================================
#     # PAYROLL ADMIN
#     # =====================================================

#     if (
#         getattr(
#             user,
#             "role",
#             None,
#         )
#         == "PAYROLL_ADMIN"
#     ):

#         return render(
#             request,
#             "dashboard/payroll_dashboard.html",
#             {
#                 "user":
#                     user,

#                 "current_employee":
#                     current_employee,
#             },
#         )

#     # =====================================================
#     # EMPLOYEE
#     # =====================================================

#     return render(
#         request,
#         "dashboard/employee_dashboard.html",
#         {
#             "user":
#                 user,

#             "current_employee":
#                 current_employee,

#             "today":
#                 today,
#         },
#     )



# from django.contrib.auth.decorators import login_required
# from django.db.models import Count, Q
# from django.shortcuts import render
# from django.utils import timezone

# from employees.models import Employee

# from organization.models import (
#     Company,
#     Department,
#     Branch,
#     WorkLocation,
# )


# # =========================================================
# # DASHBOARD
# # =========================================================

# @login_required
# def dashboard(request):

#     user = request.user

#     current_employee = getattr(
#         user,
#         "employee_profile",
#         None,
#     )

#     # =====================================================
#     # SUPER ADMIN
#     # =====================================================

#     if (
#         user.is_superuser
#         or (
#             current_employee
#             and current_employee.role
#             == Employee.Role.SUPER_ADMIN
#         )
#     ):

#         today = timezone.localdate()

#         employees = Employee.objects.exclude(
#             role=Employee.Role.SUPER_ADMIN
#         )

#         active_statuses = [
#             Employee.EmploymentStatus.ACTIVE,
#             Employee.EmploymentStatus.ON_LEAVE,
#             Employee.EmploymentStatus.BENCH,
#         ]

#         workforce = employees.filter(
#             employment_status__in=active_statuses
#         )

#         total_employees = workforce.count()

#         active_employees = workforce.filter(
#             employment_status=(
#                 Employee.EmploymentStatus.ACTIVE
#             )
#         ).count()

#         on_leave_employees = workforce.filter(
#             employment_status=(
#                 Employee.EmploymentStatus.ON_LEAVE
#             )
#         ).count()

#         bench_employees = workforce.filter(
#             employment_status=(
#                 Employee.EmploymentStatus.BENCH
#             )
#         ).count()

#         total_hr = workforce.filter(
#             role=Employee.Role.HR_ADMIN
#         ).count()

#         active_hr = workforce.filter(
#             role=Employee.Role.HR_ADMIN,
#             employment_status=(
#                 Employee.EmploymentStatus.ACTIVE
#             ),
#         ).count()

#         total_managers = workforce.filter(
#             role=Employee.Role.MANAGER
#         ).count()

#         active_managers = workforce.filter(
#             role=Employee.Role.MANAGER,
#             employment_status=(
#                 Employee.EmploymentStatus.ACTIVE
#             ),
#         ).count()

#         departments = (
#             Department.objects
#             .select_related("company")
#             .annotate(
#                 employee_count=Count(
#                     "employees",
#                     filter=Q(
#                         employees__employment_status__in=(
#                             active_statuses
#                         )
#                     ),
#                     distinct=True,
#                 ),
#                 manager_count=Count(
#                     "employees",
#                     filter=Q(
#                         employees__role=(
#                             Employee.Role.MANAGER
#                         ),
#                         employees__employment_status__in=(
#                             active_statuses
#                         ),
#                     ),
#                     distinct=True,
#                 ),
#                 hr_count=Count(
#                     "employees",
#                     filter=Q(
#                         employees__role=(
#                             Employee.Role.HR_ADMIN
#                         ),
#                         employees__employment_status__in=(
#                             active_statuses
#                         ),
#                     ),
#                     distinct=True,
#                 ),
#             )
#             .order_by("name")
#         )

#         companies = Company.objects.all().order_by(
#             "name"
#         )

#         branches = (
#             Branch.objects
#             .select_related("company")
#             .order_by("name")
#         )

#         for branch in branches:

#             branch.employee_count = workforce.filter(
#                 branch=branch
#             ).count()

#         work_locations = (
#             WorkLocation.objects
#             .select_related("company")
#             .order_by("name")
#         )

#         for location in work_locations:

#             location.employee_count = workforce.filter(
#                 work_location=location
#             ).count()

#         active_departments = departments.filter(
#             is_active=True
#         ).count()

#         active_branches = Branch.objects.filter(
#             is_active=True
#         ).count()

#         active_locations = WorkLocation.objects.filter(
#             is_active=True
#         ).count()

#         department_data = []

#         for department in departments:

#             department_employees = workforce.filter(
#                 department=department
#             )

#             department_data.append(
#                 {
#                     "department": department,

#                     "employee_count":
#                         department_employees.count(),

#                     "active_count":
#                         department_employees.filter(
#                             employment_status=(
#                                 Employee.EmploymentStatus.ACTIVE
#                             )
#                         ).count(),

#                     "manager_count":
#                         department_employees.filter(
#                             role=Employee.Role.MANAGER
#                         ).count(),

#                     "hr_count":
#                         department_employees.filter(
#                             role=Employee.Role.HR_ADMIN
#                         ).count(),
#                 }
#             )

#         context = {

#             "user": user,
#             "current_employee": current_employee,
#             "today": today,

#             "total_employees": total_employees,
#             "active_employees": active_employees,
#             "on_leave_employees": on_leave_employees,
#             "bench_employees": bench_employees,

#             "total_hr": total_hr,
#             "active_hr": active_hr,

#             "total_managers": total_managers,
#             "active_managers": active_managers,

#             "total_departments":
#                 departments.count(),

#             "active_departments":
#                 active_departments,

#             "total_branches":
#                 branches.count(),

#             "active_branches":
#                 active_branches,

#             "total_locations":
#                 work_locations.count(),

#             "active_locations":
#                 active_locations,

#             "total_companies":
#                 companies.count(),

#             "companies": companies,
#             "departments": departments,
#             "department_data": department_data,
#             "branches": branches,
#             "work_locations": work_locations,
#         }

#         return render(
#             request,
#             "dashboard/admin_dashboard.html",
#             context,
#         )

#     # =====================================================
#     # HR ADMIN
#     # =====================================================

#     if (
#         current_employee
#         and current_employee.role
#         == Employee.Role.HR_ADMIN
#     ):

#         company_employees = Employee.objects.filter(
#             company=current_employee.company,
#             employment_status__in=[
#                 Employee.EmploymentStatus.ACTIVE,
#                 Employee.EmploymentStatus.ON_LEAVE,
#                 Employee.EmploymentStatus.BENCH,
#             ],
#         )

#         context = {

#             "user": user,
#             "current_employee": current_employee,

#             "total_employees":
#                 company_employees.count(),

#             "active_employees":
#                 company_employees.filter(
#                     employment_status=(
#                         Employee.EmploymentStatus.ACTIVE
#                     )
#                 ).count(),

#             "on_leave_employees":
#                 company_employees.filter(
#                     employment_status=(
#                         Employee.EmploymentStatus.ON_LEAVE
#                     )
#                 ).count(),

#             "bench_employees":
#                 company_employees.filter(
#                     employment_status=(
#                         Employee.EmploymentStatus.BENCH
#                     )
#                 ).count(),

#             "total_managers":
#                 company_employees.filter(
#                     role=Employee.Role.MANAGER
#                 ).count(),

#             "total_hr":
#                 company_employees.filter(
#                     role=Employee.Role.HR_ADMIN
#                 ).count(),
#         }

#         return render(
#             request,
#             "dashboard/hr_dashboard.html",
#             context,
#         )

#     # =====================================================
#     # MANAGER
#     # =====================================================

#     if (
#         current_employee
#         and current_employee.role
#         == Employee.Role.MANAGER
#     ):

#         team = Employee.objects.filter(
#             reporting_manager=current_employee,
#             employment_status__in=[
#                 Employee.EmploymentStatus.ACTIVE,
#                 Employee.EmploymentStatus.ON_LEAVE,
#                 Employee.EmploymentStatus.BENCH,
#             ],
#         )

#         context = {

#             "user": user,
#             "current_employee": current_employee,

#             "team_count":
#                 team.count(),

#             "active_team_count":
#                 team.filter(
#                     employment_status=(
#                         Employee.EmploymentStatus.ACTIVE
#                     )
#                 ).count(),

#             "on_leave_team_count":
#                 team.filter(
#                     employment_status=(
#                         Employee.EmploymentStatus.ON_LEAVE
#                     )
#                 ).count(),

#             "bench_team_count":
#                 team.filter(
#                     employment_status=(
#                         Employee.EmploymentStatus.BENCH
#                     )
#                 ).count(),

#             "team_members":
#                 team.select_related(
#                     "department",
#                     "designation",
#                 ),
#         }

#         return render(
#             request,
#             "dashboard/manager_dashboard.html",
#             context,
#         )

#     # =====================================================
#     # RECRUITER
#     # =====================================================

#     if getattr(user, "role", None) == "RECRUITER":

#         return render(
#             request,
#             "dashboard/recruiter_dashboard.html",
#             {
#                 "user": user,
#                 "current_employee": current_employee,
#             },
#         )

#     # =====================================================
#     # PAYROLL ADMIN
#     # =====================================================

#     if getattr(user, "role", None) == "PAYROLL_ADMIN":

#         return render(
#             request,
#             "dashboard/payroll_dashboard.html",
#             {
#                 "user": user,
#                 "current_employee": current_employee,
#             },
#         )

#     # =====================================================
#     # EMPLOYEE
#     # =====================================================

#     return render(
#         request,
#         "dashboard/employee_dashboard.html",
#         {
#             "user": user,
#             "current_employee": current_employee,
#         },
#     )





from django.contrib.auth.decorators import login_required
from django.db.models import Count, Q
from django.shortcuts import render
from django.utils import timezone

from employees.models import Employee
from leaves.models import LeaveRequest

from organization.models import (
    Company,
    Department,
    Branch,
    WorkLocation,
)


# HELPER — CURRENT APPROVED LEAVE EMPLOYEES

def get_current_on_leave_employee_ids(
    employees,
    today=None,
):
    """
    Return employee IDs who are currently on APPROVED leave.

    Current leave means:

        APPROVED
        start_date <= today
        end_date >= today
    """

    if today is None:
        today = timezone.localdate()

    employee_ids = employees.values_list(
        "pk",
        flat=True,
    )

    return set(
        LeaveRequest.objects.filter(
            employee_id__in=employee_ids,
            status=LeaveRequest.Status.APPROVED,
            start_date__lte=today,
            end_date__gte=today,
        )
        .values_list(
            "employee_id",
            flat=True,
        )
        .distinct()
    )


# HELPER — MARK CURRENT LEAVE

def mark_current_leave_status(
    employees,
    on_leave_employee_ids,
):
    """
    Add is_currently_on_leave attribute to Employee objects.
    """

    for employee in employees:

        employee.is_currently_on_leave = (
            employee.pk in on_leave_employee_ids
        )

    return employees


# DASHBOARD

@login_required
def dashboard(request):

    user = request.user

    current_employee = getattr(
        user,
        "employee_profile",
        None,
    )

    today = timezone.localdate()

    # SUPER ADMIN

    if (
        user.is_superuser
        or (
            current_employee
            and current_employee.role
            == Employee.Role.SUPER_ADMIN
        )
    ):

        # WORKFORCE

        employees = (
            Employee.objects
            .exclude(
                role=Employee.Role.SUPER_ADMIN
            )
        )

        active_statuses = [
            Employee.EmploymentStatus.ACTIVE,
            Employee.EmploymentStatus.ON_LEAVE,
            Employee.EmploymentStatus.BENCH,
        ]

        workforce = employees.filter(
            employment_status__in=active_statuses
        )

        # CURRENT APPROVED LEAVE

        on_leave_employee_ids = (
            get_current_on_leave_employee_ids(
                workforce,
                today,
            )
        )

        # COUNTS

        total_employees = workforce.count()

        bench_employees = workforce.filter(
            employment_status=(
                Employee.EmploymentStatus.BENCH
            )
        ).count()

        on_leave_employees = len(
            on_leave_employee_ids
        )

        active_employees = (
            workforce
            .filter(
                employment_status=(
                    Employee.EmploymentStatus.ACTIVE
                )
            )
            .exclude(
                pk__in=on_leave_employee_ids
            )
            .count()
        )

        # HR

        total_hr = workforce.filter(
            role=Employee.Role.HR_ADMIN
        ).count()

        active_hr = (
            workforce
            .filter(
                role=Employee.Role.HR_ADMIN,
                employment_status=(
                    Employee.EmploymentStatus.ACTIVE
                ),
            )
            .exclude(
                pk__in=on_leave_employee_ids
            )
            .count()
        )

        # MANAGERS

        total_managers = workforce.filter(
            role=Employee.Role.MANAGER
        ).count()

        active_managers = (
            workforce
            .filter(
                role=Employee.Role.MANAGER,
                employment_status=(
                    Employee.EmploymentStatus.ACTIVE
                ),
            )
            .exclude(
                pk__in=on_leave_employee_ids
            )
            .count()
        )

        # DEPARTMENTS

        departments = (
            Department.objects
            .select_related("company")
            .annotate(
                employee_count=Count(
                    "employees",
                    filter=Q(
                        employees__employment_status__in=(
                            active_statuses
                        )
                    ),
                    distinct=True,
                ),
                manager_count=Count(
                    "employees",
                    filter=Q(
                        employees__role=(
                            Employee.Role.MANAGER
                        ),
                        employees__employment_status__in=(
                            active_statuses
                        ),
                    ),
                    distinct=True,
                ),
                hr_count=Count(
                    "employees",
                    filter=Q(
                        employees__role=(
                            Employee.Role.HR_ADMIN
                        ),
                        employees__employment_status__in=(
                            active_statuses
                        ),
                    ),
                    distinct=True,
                ),
            )
            .order_by("name")
        )

        # COMPANIES

        companies = (
            Company.objects
            .all()
            .order_by("name")
        )

        # BRANCHES

        branches = (
            Branch.objects
            .select_related("company")
            .order_by("name")
        )

        for branch in branches:

            branch.employee_count = (
                workforce
                .filter(
                    branch=branch
                )
                .count()
            )

        # WORK LOCATIONS

        work_locations = (
            WorkLocation.objects
            .select_related("company")
            .order_by("name")
        )

        for location in work_locations:

            location.employee_count = (
                workforce
                .filter(
                    work_location=location
                )
                .count()
            )

        # ACTIVE ORGANIZATION COUNTS

        active_departments = (
            departments
            .filter(
                is_active=True
            )
            .count()
        )

        active_branches = (
            Branch.objects
            .filter(
                is_active=True
            )
            .count()
        )

        active_locations = (
            WorkLocation.objects
            .filter(
                is_active=True
            )
            .count()
        )

        # DEPARTMENT DATA

        department_data = []

        for department in departments:

            department_employees = (
                workforce
                .filter(
                    department=department
                )
            )

            department_employee_ids = set(
                department_employees.values_list(
                    "pk",
                    flat=True,
                )
            )

            department_on_leave_ids = (
                on_leave_employee_ids
                & department_employee_ids
            )

            department_data.append(
                {
                    "department":
                        department,

                    "employee_count":
                        department_employees.count(),

                    "active_count":
                        department_employees
                        .filter(
                            employment_status=(
                                Employee.EmploymentStatus.ACTIVE
                            )
                        )
                        .exclude(
                            pk__in=department_on_leave_ids
                        )
                        .count(),

                    "on_leave_count":
                        len(
                            department_on_leave_ids
                        ),

                    "manager_count":
                        department_employees
                        .filter(
                            role=(
                                Employee.Role.MANAGER
                            )
                        )
                        .count(),

                    "hr_count":
                        department_employees
                        .filter(
                            role=(
                                Employee.Role.HR_ADMIN
                            )
                        )
                        .count(),
                }
            )

        # CONTEXT

        context = {

            "user":
                user,

            "current_employee":
                current_employee,

            "today":
                today,

            "total_employees":
                total_employees,

            "active_employees":
                active_employees,

            "on_leave_employees":
                on_leave_employees,

            "bench_employees":
                bench_employees,

            "total_hr":
                total_hr,

            "active_hr":
                active_hr,

            "total_managers":
                total_managers,

            "active_managers":
                active_managers,

            "total_departments":
                departments.count(),

            "active_departments":
                active_departments,

            "total_branches":
                branches.count(),

            "active_branches":
                active_branches,

            "total_locations":
                work_locations.count(),

            "active_locations":
                active_locations,

            "total_companies":
                companies.count(),

            "companies":
                companies,

            "departments":
                departments,

            "department_data":
                department_data,

            "branches":
                branches,

            "work_locations":
                work_locations,
        }

        return render(
            request,
            "dashboard/admin_dashboard.html",
            context,
        )

    # HR ADMIN

    if (
        current_employee
        and current_employee.role
        == Employee.Role.HR_ADMIN
    ):

        # -------------------------------------------------
        # HR BRANCH EMPLOYEES
        # -------------------------------------------------
        #
        # HR access is restricted to the HR's own company AND
        # own branch.  Do not fall back to company-wide data when
        # branch is missing, because that would expose employees
        # from other branches.
        # -------------------------------------------------

        if current_employee.company_id and current_employee.branch_id:
            company_employees = (
                Employee.objects
                .filter(
                    company_id=current_employee.company_id,
                    branch_id=current_employee.branch_id,
                    employment_status__in=[
                        Employee.EmploymentStatus.ACTIVE,
                        Employee.EmploymentStatus.ON_LEAVE,
                        Employee.EmploymentStatus.BENCH,
                    ],
                )
                .select_related(
                    "company",
                    "department",
                    "designation",
                    "branch",
                    "reporting_manager",
                )
                .order_by(
                    "first_name",
                    "last_name",
                )
            )
        else:
            # An HR account without a company or branch must not
            # receive company-wide employee data.
            company_employees = Employee.objects.none()

        # CURRENT APPROVED LEAVE

        on_leave_employee_ids = (
            get_current_on_leave_employee_ids(
                company_employees,
                today,
            )
        )

        # COUNTS

        total_employees = (
            company_employees.count()
        )

        bench_employees = (
            company_employees
            .filter(
                employment_status=(
                    Employee.EmploymentStatus.BENCH
                )
            )
            .count()
        )

        on_leave_employees = len(
            on_leave_employee_ids
        )

        active_employees = (
            company_employees
            .filter(
                employment_status=(
                    Employee.EmploymentStatus.ACTIVE
                )
            )
            .exclude(
                pk__in=on_leave_employee_ids
            )
            .count()
        )

        total_managers = (
            company_employees
            .filter(
                role=Employee.Role.MANAGER
            )
            .count()
        )

        active_managers = (
            company_employees
            .filter(
                role=Employee.Role.MANAGER,
                employment_status=(
                    Employee.EmploymentStatus.ACTIVE
                ),
            )
            .exclude(
                pk__in=on_leave_employee_ids
            )
            .count()
        )

        total_hr = (
            company_employees
            .filter(
                role=Employee.Role.HR_ADMIN
            )
            .count()
        )

        active_hr = (
            company_employees
            .filter(
                role=Employee.Role.HR_ADMIN,
                employment_status=(
                    Employee.EmploymentStatus.ACTIVE
                ),
            )
            .exclude(
                pk__in=on_leave_employee_ids
            )
            .count()
        )

        # -------------------------------------------------
        # MARK CURRENT LEAVE
        # -------------------------------------------------

        company_employees = list(
            company_employees
        )

        mark_current_leave_status(
            company_employees,
            on_leave_employee_ids,
        )

        # CONTEXT

        context = {

            "user":
                user,

            "current_employee":
                current_employee,

            "today":
                today,

            "total_employees":
                total_employees,

            "active_employees":
                active_employees,

            "on_leave_employees":
                on_leave_employees,

            "bench_employees":
                bench_employees,

            "total_managers":
                total_managers,

            "active_managers":
                active_managers,

            "total_hr":
                total_hr,

            "active_hr":
                active_hr,

            "company_employees":
                company_employees,
        }

        return render(
            request,
            "dashboard/hr_dashboard.html",
            context,
        )

    # MANAGER

    if (
        current_employee
        and current_employee.role
        == Employee.Role.MANAGER
    ):

        # DIRECT TEAM

        team_queryset = (
            Employee.objects
            .filter(
                reporting_manager=current_employee,
                employment_status__in=[
                    Employee.EmploymentStatus.ACTIVE,
                    Employee.EmploymentStatus.ON_LEAVE,
                    Employee.EmploymentStatus.BENCH,
                ],
            )
            .select_related(
                "department",
                "designation",
                "company",
            )
            .order_by(
                "first_name",
                "last_name",
            )
        )

        # CURRENT APPROVED LEAVE

        on_leave_employee_ids = (
            get_current_on_leave_employee_ids(
                team_queryset,
                today,
            )
        )

        # COUNTS

        team_count = (
            team_queryset.count()
        )

        bench_team_count = (
            team_queryset
            .filter(
                employment_status=(
                    Employee.EmploymentStatus.BENCH
                )
            )
            .count()
        )

        on_leave_team_count = len(
            on_leave_employee_ids
        )

        active_team_count = (
            team_queryset
            .filter(
                employment_status=(
                    Employee.EmploymentStatus.ACTIVE
                )
            )
            .exclude(
                pk__in=on_leave_employee_ids
            )
            .count()
        )

        # MARK TEAM MEMBERS

        team_members = list(
            team_queryset
        )

        mark_current_leave_status(
            team_members,
            on_leave_employee_ids,
        )

        # CONTEXT

        context = {

            "user":
                user,

            "current_employee":
                current_employee,

            "today":
                today,

            "team_count":
                team_count,

            "active_team_count":
                active_team_count,

            "on_leave_team_count":
                on_leave_team_count,

            "bench_team_count":
                bench_team_count,

            "team_members":
                team_members,
        }

        return render(
            request,
            "dashboard/manager_dashboard.html",
            context,
        )

    # RECRUITER

    if (
        getattr(
            user,
            "role",
            None,
        )
        == "RECRUITER"
    ):

        return render(
            request,
            "dashboard/recruiter_dashboard.html",
            {
                "user":
                    user,

                "current_employee":
                    current_employee,
            },
        )

    # PAYROLL ADMIN

    if (
        getattr(
            user,
            "role",
            None,
        )
        == "PAYROLL_ADMIN"
    ):

        return render(
            request,
            "dashboard/payroll_dashboard.html",
            {
                "user":
                    user,

                "current_employee":
                    current_employee,
            },
        )

    # EMPLOYEE

    return render(
        request,
        "dashboard/employee_dashboard.html",
        {
            "user":
                user,

            "current_employee":
                current_employee,

            "today":
                today,
        },
    )


@login_required
def settings_view(request):
    return render(request, "settings/settings.html")


@login_required
def company_settings(request):
    return render(request, "settings/company_settings.html")


@login_required
def system_settings(request):
    return render(request, "settings/system_settings.html")