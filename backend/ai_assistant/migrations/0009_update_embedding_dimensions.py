# Generated manually to update embedding dimensions

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('ai_assistant', '0008_create_documentchunk'),
    ]

    operations = [
        migrations.RunSQL(
            sql="ALTER TABLE ai_assistant_documentchunk ALTER COLUMN embedding TYPE vector(1024);",
            reverse_sql="ALTER TABLE ai_assistant_documentchunk ALTER COLUMN embedding TYPE vector(384);",
        ),
    ]
