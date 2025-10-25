# Generated manually for PDFDocument model

import django.db.models.deletion
from django.conf import settings
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('ai_assistant', '0002_initial'),
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.CreateModel(
            name='PDFDocument',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('title', models.CharField(max_length=255)),
                ('filename', models.CharField(max_length=255)),
                ('file', models.FileField(upload_to='pdfs/%Y/%m/%d/')),
                ('description', models.TextField(blank=True, null=True)),
                ('uploaded_at', models.DateTimeField(auto_now_add=True)),
                ('page_count', models.IntegerField(blank=True, null=True)),
                ('file_size', models.BigIntegerField(blank=True, null=True)),
                ('is_processed', models.BooleanField(default=False)),
                ('processed_at', models.DateTimeField(blank=True, null=True)),
                ('uploaded_by', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to=settings.AUTH_USER_MODEL)),
            ],
            options={
                'verbose_name': 'PDF Document',
                'verbose_name_plural': 'PDF Documents',
                'ordering': ['-uploaded_at'],
            },
        ),
    ]
