import fitz
from .models import Document
from sentence_transformers import SentenceTransformer
import numpy as np
import psycopg2
import hashlib

model = SentenceTransformer('/model/all-MiniLM-L6-v2')

def compute_file_hash(file_path):
    sha256 = hashlib.sha256()
    with open(file_path, 'rb') as f:
        for chunk in iter(lambda: f.read(8192), b''):
            sha256.update(chunk)
    return sha256.hexdigest()

def embed_and_store(pdf_path, uploaded_file):
    try:
        doc = fitz.open(pdf_path)
        for i, page in enumerate(doc, start=1):
            text = page.get_text()
            if text.strip():
                embedding = model.encode([text])[0].tolist()
                Document.objects.create(
                    uploaded_file=uploaded_file,
                    content=text,
                    embedding=embedding,
                    page_number=i
                )
        return doc.page_count
    except Exception as e:
        raise RuntimeError(f'Failed to process PDF: {e}')
