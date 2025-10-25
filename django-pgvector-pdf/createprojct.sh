\#!/bin/bash

BASE_DIR="/Users/pinggenchen/django-pgvector-pdf"

mkdir -p "$BASE_DIR/myproject"
mkdir -p "$BASE_DIR/pdfimport/templates/pdfimport"

touch "$BASE_DIR/myproject/__init__.py"
touch "$BASE_DIR/myproject/asgi.py"
touch "$BASE_DIR/myproject/settings.py"
touch "$BASE_DIR/myproject/urls.py"
touch "$BASE_DIR/myproject/wsgi.py"

touch "$BASE_DIR/pdfimport/__init__.py"
touch "$BASE_DIR/pdfimport/admin.py"
touch "$BASE_DIR/pdfimport/apps.py"
touch "$BASE_DIR/pdfimport/models.py"
touch "$BASE_DIR/pdfimport/urls.py"
touch "$BASE_DIR/pdfimport/utils.py"
touch "$BASE_DIR/pdfimport/views.py"

touch "$BASE_DIR/pdfimport/templates/pdfimport/upload.html"
touch "$BASE_DIR/pdfimport/templates/pdfimport/query.html"

touch "$BASE_DIR/Dockerfile"
touch "$BASE_DIR/docker-compose.yml"
touch "$BASE_DIR/manage.py"
touch "$BASE_DIR/requirements.txt"

echo "项目文件和目录已创建在 $BASE_DIR"


