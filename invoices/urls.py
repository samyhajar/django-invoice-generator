from django.urls import path
from . import views

urlpatterns = [
    # Dashboard pages
    path('', views.invoice_list, name='invoice_list'),
    path('invoices/', views.invoice_list, name='invoice_list'),
    path('invoices/new/', views.invoice_form, name='invoice_create'),
    path('invoices/<int:invoice_id>/edit/', views.invoice_update, name='invoice_update'),
    
    path('clients/', views.client_list, name='client_list'),
    path('clients/new/', views.client_form, name='client_create'),
    path('clients/<int:client_id>/edit/', views.client_form, name='client_update'),
    
    path('products/', views.product_list, name='product_list'),
    path('products/new/', views.product_form, name='product_create'),
    path('products/<int:product_id>/edit/', views.product_form, name='product_update'),
    
    path('projects/', views.project_list, name='project_list'),
    path('projects/new/', views.project_form, name='project_create'),
    path('projects/<int:project_id>/edit/', views.project_form, name='project_update'),
    
    path('profile/', views.company_profile, name='company_profile'),
    
    # API and utility endpoints
    path('invoice/<int:invoice_id>/pdf/', views.generate_invoice_pdf, name='invoice_pdf'),
    path('api/product/<int:product_id>/', views.get_product_details, name='product_details'),
    path('project/<int:project_id>/download-zip/', views.download_project_zip, name='download_project_zip'),
    path('tax-overview/', views.tax_overview, name='tax_overview'),
]
