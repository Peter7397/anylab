# Generated migration to add indexes for enhanced duplicate detection

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('ai_assistant', '0014_add_processing_status'),
    ]

    operations = [
        # Add index to filename and file_size for duplicate detection
        migrations.AddIndex(
            model_name='uploadedfile',
            index=models.Index(fields=['filename', 'file_size'], name='ai_uploadedfile_filename_size_idx'),
        ),
    ]

