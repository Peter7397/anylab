# Generated manually to create DocumentChunk model

import django.db.models.deletion
from django.conf import settings
from django.db import migrations, models
import pgvector.django


class Migration(migrations.Migration):

    dependencies = [
        ('ai_assistant', '0007_create_documentfile'),
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.CreateModel(
            name='DocumentChunk',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('content', models.TextField()),
                ('embedding', pgvector.django.VectorField(dimensions=384, null=True, blank=True)),
                ('page_number', models.IntegerField(default=1)),
                ('chunk_index', models.IntegerField(default=0)),
                ('created_at', models.DateTimeField(auto_now_add=True, null=True, blank=True)),
                ('uploaded_file', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE, related_name='pages', to='ai_assistant.uploadedfile')),
            ],
            options={
                'ordering': ['uploaded_file', 'page_number', 'chunk_index'],
            },
        ),
    ]
