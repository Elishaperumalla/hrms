from django.urls import path

from . import views


urlpatterns = [

    # =====================================================
    # EMPLOYEES
    # =====================================================

    path(
        "",
        views.employee_list,
        name="employee_list",
    ),

    path(
        "add/",
        views.employee_create,
        name="employee_create",
    ),

    path(
        "<int:pk>/",
        views.employee_detail,
        name="employee_detail",
    ),

    path(
        "<int:pk>/edit/",
        views.employee_update,
        name="employee_update",
    ),

    path(
        "<int:pk>/delete/",
        views.employee_delete,
        name="employee_delete",
    ),


    # =====================================================
    # DOCUMENTS
    # =====================================================

    path(
        "<int:pk>/documents/",
        views.employee_documents,
        name="employee_documents",
    ),

    path(
        "<int:pk>/documents/add/",
        views.employee_document_create,
        name="employee_document_create",
    ),

    path(
        "<int:pk>/documents/<int:document_pk>/delete/",
        views.employee_document_delete,
        name="employee_document_delete",
    ),


    # =====================================================
    # ASSETS
    # =====================================================

        path(
            "<int:pk>/assets/",
            views.employee_assets,
            name="employee_assets",
        ),

        path(
            "<int:pk>/assets/add/",
            views.employee_asset_create,
            name="employee_asset_create",
        ),

        path(
            "<int:pk>/assets/<int:asset_pk>/delete/",
            views.employee_asset_delete,
            name="employee_asset_delete",
        ),
        path(
        "<int:pk>/bench/",
        views.employee_bench,
        name="employee_bench",
    ),

    path(
        "<int:pk>/activate/",
        views.employee_activate,
        name="employee_activate",
    ),

    path(
        "<int:pk>/terminate/",
        views.employee_terminate,
        name="employee_terminate",
    ),
]