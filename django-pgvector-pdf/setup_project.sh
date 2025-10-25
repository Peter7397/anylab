#!/bin/bash

BASE_DIR="/Users/pinggenchen/django-pgvector-pdf"
mkdir -p "$BASE_DIR"
cd "$BASE_DIR" || exit

echo "🛠️ 创建 Django 项目..."
# 初始化 Django 项目和 App
django-admin startproject myproject .
python3 manage.py startapp pdfimport

# 添加目录结构
mkdir -p pdfimport/templates/pdfimport
mkdir -p pdfimport/management/commands

echo "📄 写入 manage.py"
cat > manage.py <<EOF
#!/usr/bin/env python
import os
import sys
def main():
    os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'myproject.settings')
    try:
        from django.core.management import execute_from_command_line
    except ImportError as exc:
        raise ImportError("Couldn't import Django") from exc
    execute_from_command_line(sys.argv)
if __name__ == '__main__':
    main()
EOF

echo "📄 写入 myproject/settings.py"
cat > myproject/settings.py <<EOF
import os
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SECRET_KEY = 'dev'
DEBUG = True
ALLOWED_HOSTS = []
INSTALLED_APPS = [
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    'pdfimport',
]
MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
]
ROOT_URLCONF = 'myproject.urls'
TEMPLATES = [{
    'BACKEND': 'django.template.backends.django.DjangoTemplates',
    'DIRS': [os.path.join(BASE_DIR, 'pdfimport/templates')],
    'APP_DIRS': True,
    'OPTIONS': {'context_processors': [
        'django.template.context_processors.debug',
        'django.template.context_processors.request',
        'django.contrib.auth.context_processors.auth',
        'django.contrib.messages.context_processors.messages',
    ]},
}]
WSGI_APPLICATION = 'myproject.wsgi.application'
DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.postgresql',
        'NAME': 'pgvector',
        'USER': 'postgres',
        'PASSWORD': 'yourpassword',
        'HOST': 'localhost',
        'PORT': '5432',
    }
}
STATIC_URL = '/static/'
EOF

echo "📄 写入 myproject/urls.py"
cat > myproject/urls.py <<EOF
from django.contrib import admin
from django.urls import path
from pdfimport import views
urlpatterns = [
    path('admin/', admin.site.urls),
    path('', views.upload_pdf, name='upload'),
    path('query/', views.query_vector, name='query'),
]
EOF

echo "📄 写入 pdfimport/views.py"
cat > pdfimport/views.py <<EOF
import os
import fitz  # PyMuPDF
from django.shortcuts import render
from django.core.files.storage import default_storage
from .models import Document
from .utils import embed_and_store

def upload_pdf(request):
    if request.method == 'POST':
        pdf = request.FILES['pdf']
        filename = default_storage.save(pdf.name, pdf)
        file_path = default_storage.path(filename)
        embed_and_store(file_path)
        return render(request, 'pdfimport/upload.html', {'message': 'PDF uploaded!'})
    return render(request, 'pdfimport/upload.html')

def query_vector(request):
    results = []
    if request.method == 'POST':
        q = request.POST['query']
        from django.db import connection
        with connection.cursor() as cursor:
            cursor.execute("SELECT id, content FROM pdfimport_document ORDER BY embedding <#> (SELECT embedding FROM pdfimport_document ORDER BY id DESC LIMIT 1) LIMIT 5;")
            results = cursor.fetchall()
    return render(request, 'pdfimport/query.html', {'results': results})
EOF

echo "📄 写入 pdfimport/utils.py"
cat > pdfimport/utils.py <<EOF
import fitz
from .models import Document
from sentence_transformers import SentenceTransformer
import numpy as np
import psycopg2

model = SentenceTransformer('all-MiniLM-L6-v2')

def embed_and_store(pdf_path):
    doc = fitz.open(pdf_path)
    text = ""
    for page in doc:
        text += page.get_text()
    embedding = model.encode([text])[0].tolist()
    Document.objects.create(content=text, embedding=embedding)
EOF

echo "📄 写入 pdfimport/models.py"
cat > pdfimport/models.py <<EOF
from django.db import models
from pgvector.django import VectorField

class Document(models.Model):
    content = models.TextField()
    embedding = VectorField(dimensions=384)
EOF

echo "📄 写入 pdfimport/templates/pdfimport/upload.html"
cat > pdfimport/templates/pdfimport/upload.html <<EOF
<h1>Upload PDF</h1>
<form method="post" enctype="multipart/form-data">
  {% csrf_token %}
  <input type="file" name="pdf">
  <button type="submit">Upload</button>
</form>
<p>{{ message }}</p>
EOF

echo "📄 写入 pdfimport/templates/pdfimport/query.html"
cat > pdfimport/templates/pdfimport/query.html <<EOF
<h1>Query Document</h1>
<form method="post">
  {% csrf_token %}
  <input type="text" name="query">
  <button type="submit">Search</button>
</form>
<ul>
{% for id, content in results %}
  <li><strong>{{ id }}</strong>: {{ content|truncatechars:100 }}</li>
{% endfor %}
</ul>
EOF

echo "📄 写入 Dockerfile"
cat > Dockerfile <<EOF
FROM python:3.11-slim
WORKDIR /app
COPY . .
RUN pip install --no-cache-dir -r requirements.txt
CMD ["python", "manage.py", "runserver", "0.0.0.0:8000"]
EOF

echo "📄 写入 docker-compose.yml"
cat > docker-compose.yml <<EOF
version: '3'
services:
  db:
    image: ankane/pgvector
    environment:
      POSTGRES_USER: postgres
      POSTGRES_PASSWORD: yourpassword
      POSTGRES_DB: pgvector
    ports:
      - "5432:5432"
  web:
    build: .
    command: python manage.py runserver 0.0.0.0:8000
    volumes:
      - .:/app
    ports:
      - "8000:8000"
    depends_on:
      - db
EOF

echo "📄 写入 requirements.txt"
cat > requirements.txt <<EOF
Django>=4.0
psycopg2-binary
pgvector
PyMuPDF
sentence-transformers
EOF

echo "✅ 完成！你现在可以运行以下命令启动项目："
echo "cd $BASE_DIR"
echo "docker-compose up --build"

