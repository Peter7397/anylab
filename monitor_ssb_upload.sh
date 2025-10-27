#!/bin/bash
# SSB Upload Monitoring Script

echo "🔍 SSB Upload Monitor - Press Ctrl+C to stop"
echo "============================================"
echo ""

while true; do
    clear
    echo "SSB Upload/Embedding Status - $(date +"%H:%M:%S")"
    echo "============================================"
    echo ""
    
    cd /Volumes/Orico/OnLab0812/backend
    source venv/bin/activate
    
    python3 << 'EOF'
import os
import django
import sys

# Setup Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'anylab.settings')
sys.path.insert(0, '/Volumes/Orico/OnLab0812/backend')
django.setup()

from ai_assistant.models import DocumentChunk, UploadedFile, DocumentFile
from django.utils import timezone
from datetime import timedelta

# Find most recent processing
recent_time = timezone.now() - timedelta(minutes=60)

# Check all recent UploadedFiles
all_ufs = UploadedFile.objects.all().order_by('-uploaded_at')

for uf in all_ufs[:5]:
    chunks = DocumentChunk.objects.filter(uploaded_file=uf)
    total_chunks = chunks.count()
    
    if total_chunks > 0:
        chunks_with_emb = [c for c in chunks if c.embedding is not None]
        total_with_emb = len(chunks_with_emb)
        
        print(f"📦 {uf.filename}")
        print(f"   Chunks: {total_chunks} | With emb: {total_with_emb}")
        
        if total_chunks > 0:
            pct = (total_with_emb / total_chunks) * 100
            print(f"   Progress: {pct:.1f}%")
            
            sample = chunks.first()
            print(f"   Size: {len(sample.content)} chars per chunk")
            
            if total_with_emb < total_chunks:
                remaining = total_chunks - total_with_emb
                eta_minutes = remaining / 60
                print(f"   ⏱️  ETA: ~{eta_minutes:.0f} min")
            
            if total_chunks >= 15000:
                print(f"   ✅ EXCELLENT! Using 100-char chunking")
            print()

# Check DocumentFile
docs = DocumentFile.objects.filter(uploaded_at__gte=recent_time)
if docs.exists():
    print(f"📄 Recent uploads: {docs.count()}")
    for doc in docs:
        print(f"   - {doc.title} ({doc.document_type})")

EOF
    
    sleep 3
done
