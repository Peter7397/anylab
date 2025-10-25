from django.apps import AppConfig
from django.db import connection

class PdfimportConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'pdfimport'
    
    def ready(self):
        """Register pgvector types when the app is ready"""
        try:
            from pgvector.psycopg2 import register_vector
            register_vector(connection.connection)
        except Exception as e:
            print(f"Warning: Could not register pgvector types: {e}")
