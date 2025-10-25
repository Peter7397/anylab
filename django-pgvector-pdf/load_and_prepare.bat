@echo off
setlocal

REM Load all Docker images

echo Loading Django web image...
docker load -i django_web_image.tar

echo Loading Ollama image...
docker load -i ollama_image.tar

echo Loading Alpine image...
docker load -i alpine_image.tar

REM Create the Ollama data volume (if not already present)
echo Creating Ollama data volume...
docker volume create django-pgvector-pdf_ollama_data

REM Unpack the Qwen2 model data into the volume
echo Unpacking Qwen2 model data into the volume...
docker run --rm -v django-pgvector-pdf_ollama_data:/volume -v "%cd%":/backup alpine sh -c "cd /volume && tar xzf /backup/ollama_data.tar.gz"

echo.
echo All images loaded and data volume prepared. You can now run:
echo   docker compose up

echo Done.
endlocal 