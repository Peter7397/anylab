from django.contrib import admin
from .models import Document, UploadedFile

@admin.register(Document)
class DocumentAdmin(admin.ModelAdmin):
    list_display = ("id", "uploaded_file", "page_number", "content")
    search_fields = ("content",)

@admin.register(UploadedFile)
class UploadedFileAdmin(admin.ModelAdmin):
    list_display = ("id", "filename", "file_hash", "uploaded_at", "intro")
    search_fields = ("filename", "file_hash", "intro")
