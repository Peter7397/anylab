from django.db import migrations, models
import django.db.models.deletion
from django.conf import settings


class Migration(migrations.Migration):

    dependencies = [
        ('ai_assistant', '0004_update_pdfdocument_uploaded_by_null'),
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.CreateModel(
            name='WebLink',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('title', models.CharField(max_length=255)),
                ('url', models.URLField(max_length=1000)),
                ('tags', models.JSONField(blank=True, default=list)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
                ('added_by', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='weblinks', to=settings.AUTH_USER_MODEL)),
            ],
            options={
                'db_table': 'ai_weblinks',
                'verbose_name': 'Web Link',
                'verbose_name_plural': 'Web Links',
            },
        ),
        migrations.CreateModel(
            name='KnowledgeShare',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('enabled', models.BooleanField(default=False)),
                ('share_token', models.CharField(blank=True, max_length=64)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
                ('created_by', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='knowledge_shares', to=settings.AUTH_USER_MODEL)),
            ],
            options={
                'db_table': 'ai_knowledge_share',
                'verbose_name': 'Knowledge Share',
                'verbose_name_plural': 'Knowledge Share',
            },
        ),
        migrations.AddIndex(
            model_name='weblink',
            index=models.Index(fields=['created_at'], name='ai_weblinks_created_at_idx'),
        ),
    ]


