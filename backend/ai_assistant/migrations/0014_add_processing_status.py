# Generated manually to add processing status tracking

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('ai_assistant', '0013_add_help_portal_document'),
    ]

    operations = [
        # Add processing status field
        migrations.AddField(
            model_name='uploadedfile',
            name='processing_status',
            field=models.CharField(
                choices=[
                    ('pending', 'Pending'),
                    ('metadata_extracting', 'Extracting Metadata'),
                    ('chunking', 'Generating Chunks'),
                    ('embedding', 'Creating Embeddings'),
                    ('ready', 'Ready for Search'),
                    ('failed', 'Processing Failed'),
                ],
                db_index=True,
                default='pending',
                max_length=20
            ),
        ),
        
        # Add processing completion tracking
        migrations.AddField(
            model_name='uploadedfile',
            name='metadata_extracted',
            field=models.BooleanField(default=False),
        ),
        
        migrations.AddField(
            model_name='uploadedfile',
            name='chunks_created',
            field=models.BooleanField(default=False),
        ),
        
        migrations.AddField(
            model_name='uploadedfile',
            name='embeddings_created',
            field=models.BooleanField(default=False),
        ),
        
        # Add error tracking
        migrations.AddField(
            model_name='uploadedfile',
            name='processing_error',
            field=models.TextField(blank=True, null=True),
        ),
        
        migrations.AddField(
            model_name='uploadedfile',
            name='processing_started_at',
            field=models.DateTimeField(blank=True, null=True),
        ),
        
        migrations.AddField(
            model_name='uploadedfile',
            name='processing_completed_at',
            field=models.DateTimeField(blank=True, null=True),
        ),
        
        # Add quality metrics
        migrations.AddField(
            model_name='uploadedfile',
            name='chunk_count',
            field=models.IntegerField(default=0),
        ),
        
        migrations.AddField(
            model_name='uploadedfile',
            name='embedding_count',
            field=models.IntegerField(default=0),
        ),
        
        # Add indexes for performance
        migrations.AddIndex(
            model_name='uploadedfile',
            index=models.Index(fields=['processing_status'], name='ai_uploadedfile_processing_status_idx'),
        ),
        migrations.AddIndex(
            model_name='uploadedfile',
            index=models.Index(fields=['metadata_extracted', 'chunks_created', 'embeddings_created'], name='ai_uploadedfile_completion_idx'),
        ),
    ]

