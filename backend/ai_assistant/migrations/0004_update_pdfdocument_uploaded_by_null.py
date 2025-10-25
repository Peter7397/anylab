# Generated manually to make uploaded_by field nullable

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('ai_assistant', '0003_pdfdocument'),
    ]

    operations = [
        migrations.AlterField(
            model_name='pdfdocument',
            name='uploaded_by',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE, to='users.user'),
        ),
    ]
