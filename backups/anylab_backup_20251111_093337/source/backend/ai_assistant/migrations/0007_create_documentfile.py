# Generated manually to create DocumentFile model

import django.core.validators
import django.db.models.deletion
from django.conf import settings
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('ai_assistant', '0006_document_queryhistory_uploadedfile_and_more'),
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.CreateModel(
            name='DocumentFile',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('title', models.CharField(max_length=255)),
                ('file', models.FileField(blank=True, null=True, upload_to='documents/', validators=[django.core.validators.FileExtensionValidator(allowed_extensions=['pdf', 'doc', 'docx', 'xls', 'xlsx', 'ppt', 'pptx', 'txt', 'rtf'])])),
                ('filename', models.CharField(blank=True, max_length=255, null=True)),
                ('document_type', models.CharField(choices=[('pdf', 'PDF Document'), ('doc', 'Word Document'), ('docx', 'Word Document'), ('xls', 'Excel Spreadsheet'), ('xlsx', 'Excel Spreadsheet'), ('ppt', 'PowerPoint Presentation'), ('pptx', 'PowerPoint Presentation'), ('txt', 'Text Document'), ('rtf', 'Rich Text Document')], default='pdf', max_length=10)),
                ('description', models.TextField(blank=True, null=True)),
                ('uploaded_at', models.DateTimeField(auto_now_add=True)),
                ('page_count', models.IntegerField(default=0)),
                ('file_size', models.BigIntegerField(default=0)),
                ('uploaded_by', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, to=settings.AUTH_USER_MODEL)),
            ],
            options={
                'ordering': ['-uploaded_at'],
            },
        ),
    ]
