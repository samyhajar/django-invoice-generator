from django.urls import path
from . import views

urlpatterns = [
    path('invoice/<int:invoice_id>/pdf/', views.generate_invoice_pdf, name='invoice_pdf'),
    path('api/product/<int:product_id>/', views.get_product_details, name='product_details'),
    path('project/<int:project_id>/download-zip/', views.download_project_zip, name='download_project_zip'),
    path('tax-overview/', views.tax_overview, name='tax_overview'),
]
