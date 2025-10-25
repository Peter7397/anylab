import os
import fitz  # PyMuPDF
from django.shortcuts import render
from django.core.files.storage import default_storage
from .models import Document
from .utils import embed_and_store
from django.contrib.auth.decorators import login_required
from .rag_service import QwenRAGService
from .lightweight_rag import LightweightRAGService
from sentence_transformers import SentenceTransformer
import numpy as np
from django.core.paginator import Paginator
from django.conf import settings
from django.core.files.storage import FileSystemStorage
from django.db import connection
import json

# Initialize RAG services (will be loaded on first use)
rag_service = None
lightweight_rag_service = None

@login_required
def upload_pdf(request):
    message = None
    uploaded = []
    skipped = []
    if request.method == 'POST':
        pdfs = request.FILES.getlist('pdfs') or request.FILES.getlist('pdf')
        if not pdfs:
            message = 'No file(s) uploaded.'
        else:
            from .utils import compute_file_hash, embed_and_store
            from .models import UploadedFile
            pdf_storage = FileSystemStorage(location=os.path.join(settings.MEDIA_ROOT, 'uploaded_pdfs'), base_url='/media/uploaded_pdfs/')
            if not os.path.exists(pdf_storage.location):
                os.makedirs(pdf_storage.location, exist_ok=True)
            for pdf in pdfs:
                filename = pdf_storage.save(pdf.name, pdf)
                file_path = pdf_storage.path(filename)
                file_hash = compute_file_hash(file_path)
                if UploadedFile.objects.filter(file_hash=file_hash).exists():
                    skipped.append(f"{pdf.name} (already uploaded)")
                    pdf_storage.delete(filename)
                else:
                    try:
                        intro = None
                        import fitz
                        doc = fitz.open(file_path)
                        if doc.page_count > 0:
                            first_page_text = doc[0].get_text()
                            intro = first_page_text[:200] if first_page_text else None
                        uploaded_file = UploadedFile.objects.create(
                            filename=pdf.name,
                            file_hash=file_hash,
                            intro=intro
                        )
                        embed_and_store(file_path, uploaded_file)
                        uploaded.append(pdf.name)
                    except Exception as e:
                        skipped.append(f"{pdf.name} (error: {e})")
                    # Do NOT delete the file after successful upload
            msg_parts = []
            if uploaded:
                msg_parts.append("<strong>Uploaded:</strong><br>" + "<br>".join(uploaded))
            if skipped:
                msg_parts.append("<strong>Skipped:</strong><br>" + "<br>".join(skipped))
            message = '<br><br>'.join(msg_parts)
        return render(request, 'pdfimport/upload.html', {'message': message})
    return render(request, 'pdfimport/upload.html', {'message': message})

@login_required
def query_vector(request):
    results = []
    message = None
    query_history = request.session.get('vector_query_history', [])
    if request.method == 'POST':
        q = request.POST.get('query', '').strip()
        if not q:
            message = 'Please enter a query.'
        else:
            try:
                model = SentenceTransformer('/model/all-MiniLM-L6-v2')
                query_embedding = model.encode([q])[0].tolist()
                with connection.cursor() as cursor:
                    cursor.execute("""
                        SELECT id, content FROM pdfimport_document
                        ORDER BY embedding <#> %s::vector
                        LIMIT 5;
                    """, [query_embedding])
                    results = cursor.fetchall()
                # Save to history
                query_history.insert(0, {
                    'query': q,
                    'results': [{'id': r[0], 'content': r[1]} for r in results],
                })
                query_history = query_history[:10]
                request.session['vector_query_history'] = query_history
            except Exception as e:
                message = f'Error processing query: {e}'
    return render(request, 'pdfimport/query.html', {
        'results': results,
        'message': message,
        'query_history': query_history,
        'query_history_json': json.dumps(query_history),
    })

@login_required
def rag_query(request):
    global rag_service
    response_data = None
    message = None
    is_loading = False
    query_history = request.session.get('rag_query_history', [])
    if request.method == 'POST':
        query = request.POST.get('query', '').strip()
        if not query:
            message = 'Please enter a query.'
        else:
            try:
                if rag_service is None:
                    rag_service = QwenRAGService()
                is_loading = True
                response_data = rag_service.query_with_rag(query, top_k=10)
                is_loading = False
                # Save to history
                query_history.insert(0, {
                    'query': query,
                    'response': response_data['response'] if isinstance(response_data, dict) else response_data,
                    'sources': response_data['sources'] if isinstance(response_data, dict) and 'sources' in response_data else [],
                })
                query_history = query_history[:10]
                request.session['rag_query_history'] = query_history
            except Exception as e:
                message = f'Error processing RAG query: {e}'
                rag_service = None
    return render(request, 'pdfimport/rag_query.html', {
        'response_data': response_data,
        'message': message,
        'is_loading': is_loading,
        'query_history': query_history,
        'query_history_json': json.dumps(query_history),
    })

@login_required
def lightweight_rag_query(request):
    global lightweight_rag_service
    response_data = None
    message = None
    query_history = request.session.get('lightweight_rag_query_history', [])
    if request.method == 'POST':
        query = request.POST.get('query', '').strip()
        if not query:
            message = 'Please enter a query.'
        else:
            try:
                if lightweight_rag_service is None:
                    lightweight_rag_service = LightweightRAGService()
                response_data = lightweight_rag_service.query_with_lightweight_rag(query, top_k=10)
                # Save to history
                query_history.insert(0, {
                    'query': query,
                    'response': response_data['response'] if isinstance(response_data, dict) else response_data,
                    'sources': response_data['sources'] if isinstance(response_data, dict) and 'sources' in response_data else [],
                })
                query_history = query_history[:10]
                request.session['lightweight_rag_query_history'] = query_history
            except Exception as e:
                message = f'Error processing lightweight RAG query: {e}'
                lightweight_rag_service = None
    return render(request, 'pdfimport/lightweight_rag_query.html', {
        'response_data': response_data,
        'message': message,
        'query_history': query_history,
        'query_history_json': json.dumps(query_history),
    })

@login_required
def document_list(request):
    from .models import UploadedFile
    files = UploadedFile.objects.order_by('-uploaded_at')
    paginator = Paginator(files, 20)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    return render(request, 'pdfimport/document_list.html', {'page_obj': page_obj})

@login_required
def pdf_view(request, uploaded_file_id):
    from .models import UploadedFile
    from django.shortcuts import get_object_or_404
    uploaded_file = get_object_or_404(UploadedFile, id=uploaded_file_id)
    page = request.GET.get('page', 1)
    
    # Build the PDF file URL using the same host and port as the request
    # This ensures the PDF is accessed through the same server that served the page
    host = request.get_host()
    scheme = request.scheme
    pdf_url = f"{scheme}://{host}/media/uploaded_pdfs/{uploaded_file.filename}"
    
    # For debugging
    print(f"Generated PDF URL: {pdf_url}")
    print(f"PDF file exists: {os.path.exists(os.path.join(settings.MEDIA_ROOT, 'uploaded_pdfs', uploaded_file.filename))}")
    print(f"Full PDF path: {os.path.join(settings.MEDIA_ROOT, 'uploaded_pdfs', uploaded_file.filename)}")
    
    return render(request, 'pdfimport/pdf_view.html', {
        'uploaded_file': uploaded_file,
        'pdf_url': pdf_url,
        'page': page
    })
