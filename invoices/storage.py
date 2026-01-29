import os
from django.conf import settings
from django.utils.text import slugify


def get_client_invoice_path(client_name, project_name, invoice_number):
    """
    Generate file path for invoice PDF storage
    Format: media/invoices/{client-slug}/{project-slug}/{invoice-number}.pdf
    """
    client_slug = slugify(client_name)
    project_slug = slugify(project_name)
    filename = f"{invoice_number}.pdf"
    return os.path.join(settings.MEDIA_ROOT, 'invoices', client_slug, project_slug, filename)


def ensure_project_folder(client_name, project_name):
    """
    Ensure the client/project folder exists
    Returns the folder path
    """
    client_slug = slugify(client_name)
    project_slug = slugify(project_name)
    folder_path = os.path.join(settings.MEDIA_ROOT, 'invoices', client_slug, project_slug)
    os.makedirs(folder_path, exist_ok=True)
    return folder_path
