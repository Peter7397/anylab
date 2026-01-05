# Generated manually to create DocumentChunk model
# NOTE: DocumentChunk may already exist from migration 0006, so this migration
# only creates it if it doesn't exist

import django.db.models.deletion
from django.conf import settings
from django.db import migrations, models
import pgvector.django


def create_documentchunk_if_not_exists(apps, schema_editor):
    """Create DocumentChunk model only if it doesn't already exist"""
    db_alias = schema_editor.connection.alias
    connection = schema_editor.connection
    
    with connection.cursor() as cursor:
        # Check if table already exists
        cursor.execute("""
            SELECT EXISTS (
                SELECT FROM information_schema.tables 
                WHERE table_schema = 'public' 
                AND table_name = 'ai_assistant_documentchunk'
            );
        """)
        table_exists = cursor.fetchone()[0]
        
        if not table_exists:
            # Table doesn't exist, create it using RunSQL
            cursor.execute("""
                CREATE TABLE ai_assistant_documentchunk (
                    id BIGSERIAL NOT NULL PRIMARY KEY,
                    content TEXT NOT NULL,
                    embedding vector(384),
                    page_number INTEGER NOT NULL DEFAULT 1,
                    chunk_index INTEGER NOT NULL DEFAULT 0,
                    created_at TIMESTAMP WITH TIME ZONE,
                    uploaded_file_id BIGINT REFERENCES ai_assistant_uploadedfile(id) ON DELETE CASCADE
                );
                CREATE INDEX ai_assistant_documentchunk_uploaded_file_id_idx 
                    ON ai_assistant_documentchunk(uploaded_file_id);
            """)


def reverse_create_documentchunk(apps, schema_editor):
    """Reverse migration - drop table if it exists"""
    connection = schema_editor.connection
    with connection.cursor() as cursor:
        cursor.execute("DROP TABLE IF EXISTS ai_assistant_documentchunk;")


class Migration(migrations.Migration):

    dependencies = [
        ('ai_assistant', '0007_create_documentfile'),
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.RunPython(
            create_documentchunk_if_not_exists,
            reverse_create_documentchunk,
        ),
    ]
