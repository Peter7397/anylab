from django.db import models
from pgvector.django import VectorField

class UploadedFile(models.Model):
    filename = models.CharField(max_length=255)
    file_hash = models.CharField(max_length=64, unique=True, db_index=True)
    uploaded_at = models.DateTimeField(auto_now_add=True)
    intro = models.TextField(null=True, blank=True)

class Document(models.Model):
    uploaded_file = models.ForeignKey(UploadedFile, on_delete=models.CASCADE, related_name='pages', null=True, blank=True)
    content = models.TextField()
    embedding = VectorField(dimensions=384)
    page_number = models.IntegerField(default=1)
