from django import template
from pdfimport.models import UploadedFile

register = template.Library()

@register.filter
def get_uploaded_filename(uploaded_file_id):
    try:
        return UploadedFile.objects.get(id=uploaded_file_id).filename
    except UploadedFile.DoesNotExist:
        return "Unknown" 