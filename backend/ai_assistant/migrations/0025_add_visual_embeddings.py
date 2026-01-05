"""
Migration: Add visual embeddings support to DocumentChunk
Adds visual_embedding field for storing CLIP/vision model embeddings
"""
from django.db import migrations, models
import pgvector.django


class Migration(migrations.Migration):
    dependencies = [
        ('ai_assistant', '0024_add_performance_indexes'),
    ]

    operations = [
        migrations.AddField(
            model_name='documentchunk',
            name='visual_embedding',
            field=pgvector.django.VectorField(
                dimensions=512,  # CLIP ViT-B/32 dimensions
                null=True,
                blank=True,
                help_text='Visual embedding for image content (CLIP/vision model)'
            ),
        ),
        migrations.AddField(
            model_name='documentchunk',
            name='has_visual_content',
            field=models.BooleanField(
                default=False,
                help_text='Whether this chunk contains visual content (image)'
            ),
        ),
    ]

