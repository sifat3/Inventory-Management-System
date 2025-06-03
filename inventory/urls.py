from django.urls import path
from . import views
from django.contrib.auth import views as auth_views

urlpatterns = [
    path('', views.login_view, name='login'),
    path('dashboard/', views.dashboard_view, name='dashboard'),
    path('products/', views.product_list_view, name='product_list'),
    path('products/add/', views.product_add_view, name='product_add'),
    path('products/<int:pk>/edit/', views.product_edit_view, name='product_edit'),
    path('products/<int:pk>/delete/', views.product_delete_view, name='product_delete'),
    path('expenses/', views.expense_list_view, name='expense_list'),
    path('expenses/add/', views.expense_add_view, name='expense_add'),
    path('expenses/<int:pk>/edit/', views.expense_edit_view, name='expense_edit'),
    path('expenses/<int:pk>/delete/', views.expense_delete_view, name='expense_delete'),
    path('buy/', views.purchase_list_view, name='purchase_list'),
    path('buy/add/', views.purchase_add_view, name='purchase_add'),
    path('buy/<int:invoice_id>/return/', views.purchase_return_view, name='purchase_return'),
    path('sell/', views.sales_list_view, name='sales_list'),
    path('sell/add/', views.sales_add_view, name='sales_add'),
    path('sell/<int:invoice_id>/return/', views.sales_return_view, name='sales_return'),
    path('sell/invoice/<int:invoice_id>/', views.sales_invoice_view, name='sales_invoice'),
    path('buy/invoice/<int:invoice_id>/', views.purchase_invoice_view, name='purchase_invoice'),
    path('sales/invoice/print/<int:invoice_id>/', views.sales_invoice_print_view, name='sales_invoice_print'),
    path('purchase/invoice/print/<int:invoice_id>/', views.purchase_invoice_print_view, name='purchase_invoice_print'),
    path('logout/', auth_views.LogoutView.as_view(next_page='login'), name='logout'),
    path('purchase/invoice/received/<int:invoice_id>/', views.purchase_invoice_received_view, name='purchase_invoice_received'),
    path('sell/<int:invoice_id>/due_received/', views.sales_due_received_view, name='sales_due_received'),
    path('sell/report/', views.sales_report_view, name='sales_report'),
    path('buy/report/', views.purchase_report_view, name='purchase_report'),
    path('expenses/report/', views.expense_report_view, name='expense_report'),
    path('inventory/report/', views.inventory_report_view, name='inventory_report'),

]
