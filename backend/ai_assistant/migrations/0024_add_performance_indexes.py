# Generated migration to add performance indexes

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('ai_assistant', '0023_enable_pgvector_extension'),
    ]

    operations = [
        # Add index on uploaded_at for UploadedFile (for time-based queries)
        migrations.AddIndex(
            model_name='uploadedfile',
            index=models.Index(fields=['uploaded_at'], name='ai_uploadedfile_uploaded_at_idx'),
        ),
        
        # Add composite index for DocumentChunk queries
        migrations.AddIndex(
            model_name='documentchunk',
            index=models.Index(fields=['uploaded_file', 'page_number'], name='ai_documentchunk_file_page_idx'),
        ),
        
        # Add index for DocumentChunk embedding queries (for vector search)
        migrations.AddIndex(
            model_name='documentchunk',
            index=models.Index(fields=['uploaded_file', 'chunk_index'], name='ai_documentchunk_file_chunk_idx'),
        ),
        
        # Add index for DocumentChunk created_at (for time-based queries)
        migrations.AddIndex(
            model_name='documentchunk',
            index=models.Index(fields=['created_at'], name='ai_documentchunk_created_at_idx'),
        ),
    ]
