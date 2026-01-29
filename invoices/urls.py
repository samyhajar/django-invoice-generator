from django.urls import path
from . import views

urlpatterns = [
    path('invoice/<int:invoice_id>/pdf/', views.generate_invoice_pdf, name='invoice_pdf'),
]
