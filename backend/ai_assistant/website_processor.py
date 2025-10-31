"""
Website Processing System

This module provides website processing capabilities that mirror the AutomaticFileProcessor
to ensure websites go through the same proven processing pipeline:
1. Fetch HTML content
2. Convert to UploadedFile format
3. Use existing AutomaticFileProcessor for metadata, chunking, and embeddings
4. Track processing status

QUALITY RULES:
- Use BGE-M3 ONLY - NO FALLBACKS EVER
- Same chunking strategy as file uploads (600 chars, 120 overlap)
- Same embedding batch processing (50 chunks per API call)
- Same status tracking and error handling
"""

import logging
import os
import hashlib
import requests
import tempfile
from pathlib import Path
from urllib.parse import urlparse
from django.conf import settings
from django.utils import timezone
from django.core.files.base import ContentFile
from bs4 import BeautifulSoup
from .models import WebsiteSource, UploadedFile, DocumentChunk
from .automatic_file_processor import automatic_file_processor
from .html_parser import HTMLParser, HTMLParsingConfig

logger = logging.getLogger(__name__)


class WebsiteProcessor:
    """
    Process websites using the same proven file upload flow
    
    WORKFLOW:
    1. Fetch HTML content from URL
    2. Parse and clean HTML
    3. Convert to UploadedFile format
    4. Link WebsiteSource to UploadedFile
    5. Use AutomaticFileProcessor for the rest (metadata, chunking, embeddings)
    6. Update WebsiteSource status
    """
    
    def __init__(self):
        self.rag_service = automatic_file_processor.rag_service
        self.ollama_url = getattr(settings, 'OLLAMA_API_URL', 'http://localhost:11434')
        
        # HTML parsing configuration
        self.html_config = HTMLParsingConfig(
            timeout=30,
            retry_attempts=3,
            min_content_length=100,
            max_content_length=1000000,  # 1MB max
            extract_images=True,
            extract_tables=True,
            extract_forms=True,
            extract_code=True,
            extract_links=True,
            clean_html=True,
            remove_scripts=True,
            remove_styles=True,
            remove_comments=True,
            preserve_structure=True,
            language_detection=True,
            content_classification=True
        )
        
    def process_website_fully(self, website_source_id: int, max_retries: int = 3):
        """
        Complete website processing workflow with retry logic:
        URL → Fetch HTML → Parse → Convert to UploadedFile → Process via AutomaticFileProcessor → Ready
        
        RETRY MECHANISM: Up to 3 attempts for quality assurance
        """
        website_source = WebsiteSource.objects.get(id=website_source_id)
        
        for attempt in range(1, max_retries + 1):
            try:
                logger.info(f"Starting website processing for: {website_source.url} (attempt {attempt}/{max_retries})")
                
                # Step 1: Update status - fetching content
                website_source.processing_status = 'fetching'
                website_source.processing_started_at = timezone.now()
                website_source.processing_error = None
                website_source.save()
                
                # Step 2: Fetch and parse HTML content
                html_content = self._fetch_and_parse_html(website_source.url)
                if not html_content:
                    raise Exception("Failed to fetch or parse HTML content")
                
                # Step 3: Convert HTML to UploadedFile format
                uploaded_file = self._create_uploaded_file_from_html(html_content, website_source)
                if not uploaded_file:
                    raise Exception("Failed to create UploadedFile from HTML content")
                
                # Step 4: Link WebsiteSource to UploadedFile
                website_source.uploaded_file = uploaded_file
                website_source.save()
                
                # Step 5: Use existing AutomaticFileProcessor for the rest!
                # This ensures SAME proven processing pipeline:
                # - Metadata extraction
                # - Chunking (600 chars, 120 overlap)
                # - Embedding (BGE-M3, batches of 50)
                # - Status tracking
                logger.info(f"Processing HTML content via AutomaticFileProcessor for UploadedFile {uploaded_file.id}")
                result = automatic_file_processor.process_file_fully(uploaded_file.id)
                
                # Step 6: Update WebsiteSource status based on UploadedFile
                uploaded_file.refresh_from_db()
                website_source.processing_status = uploaded_file.processing_status
                website_source.metadata_extracted = uploaded_file.metadata_extracted
                website_source.chunks_created = uploaded_file.chunks_created
                website_source.embeddings_created = uploaded_file.embeddings_created
                website_source.chunk_count = uploaded_file.chunk_count
                website_source.embedding_count = uploaded_file.embedding_count
                website_source.processing_error = uploaded_file.processing_error
                website_source.processing_completed_at = uploaded_file.processing_completed_at
                website_source.page_count = 1  # Single page for now
                
                # Update refresh schedule
                if website_source.auto_refresh:
                    from datetime import timedelta
                    website_source.next_refresh_at = timezone.now() + timedelta(days=website_source.refresh_interval_days)
                
                website_source.save()
                
                logger.info(f"Website processing completed successfully: {website_source.url}")
                return {
                    'status': 'success',
                    'website_source_id': website_source_id,
                    'uploaded_file_id': uploaded_file.id,
                    'chunk_count': uploaded_file.chunk_count,
                    'embedding_count': uploaded_file.embedding_count,
                    'result': result
                }
                
            except Exception as e:
                logger.error(f"Website processing attempt {attempt} failed for {website_source.url}: {e}", exc_info=True)
                
                # Update error status
                website_source.processing_status = 'failed'
                website_source.processing_error = f"Attempt {attempt} failed: {str(e)}"
                website_source.save()
                
                if attempt >= max_retries:
                    logger.error(f"All website processing attempts failed for {website_source.url}")
                    return {
                        'status': 'failed',
                        'website_source_id': website_source_id,
                        'error': str(e),
                        'attempts': attempt
                    }
                
                # Wait before retry
                import time
                time.sleep(2 ** attempt)  # Exponential backoff
        
        return {
            'status': 'failed',
            'website_source_id': website_source_id,
            'error': 'All processing attempts failed',
            'attempts': max_retries
        }
    
    def _fetch_and_parse_html(self, url: str):
        """Fetch and parse HTML content from URL"""
        try:
            logger.info(f"Fetching HTML content from: {url}")
            
            # Use existing HTMLParser
            parser = HTMLParser(self.html_config)
            html_content = parser.parse_url(url)
            
            if not html_content:
                logger.error(f"Failed to parse HTML content from {url}")
                return None
            
            logger.info(f"Successfully parsed HTML content from {url}: {len(html_content.clean_content)} characters")
            return html_content
            
        except Exception as e:
            logger.error(f"Error fetching HTML from {url}: {e}", exc_info=True)
            return None
    
    def _create_uploaded_file_from_html(self, html_content, website_source):
        """Convert HTML content to UploadedFile format"""
        try:
            logger.info(f"Converting HTML content to UploadedFile format")
            
            # Create content for UploadedFile
            # We'll store the clean HTML content as a text file
            content_text = html_content.clean_content
            
            # Create a temporary file-like object
            content_file = ContentFile(
                content_text.encode('utf-8'),
                name=f"website_{website_source.id}_{hashlib.md5(html_content.url.encode()).hexdigest()[:8]}.html"
            )
            
            # Calculate file hash
            file_hash = hashlib.sha256(content_text.encode('utf-8')).hexdigest()
            
            # Check for duplicates
            existing_file = UploadedFile.objects.filter(file_hash=file_hash).first()
            if existing_file:
                logger.info(f"Found existing UploadedFile with same content hash: {existing_file.id}")
                return existing_file
            
            # Create UploadedFile record
            uploaded_file = UploadedFile.objects.create(
                filename=f"website_{website_source.id}_{hashlib.md5(html_content.url.encode()).hexdigest()[:8]}.html",
                file_hash=file_hash,
                file_size=len(content_text),
                page_count=1,
                intro=content_text[:200] if content_text else None,
                uploaded_by=website_source.created_by,
                processing_status='pending'  # Will be processed by AutomaticFileProcessor
            )
            
            # Store the content in metadata for AutomaticFileProcessor to use
            uploaded_file.metadata = {
                'content_type': 'website',
                'source_url': html_content.url,
                'title': html_content.title,
                'description': html_content.description,
                'domain': html_content.metadata.get('domain', ''),
                'language': html_content.language,
                'encoding': html_content.encoding,
                'content_type_detected': html_content.content_type,
                'quality_score': html_content.quality_score,
                'relevance_score': html_content.relevance_score,
                'extracted_elements': {
                    'links_count': len(html_content.links),
                    'images_count': len(html_content.images),
                    'tables_count': len(html_content.tables),
                    'headings_count': len(html_content.headings),
                    'paragraphs_count': len(html_content.paragraphs),
                    'lists_count': len(html_content.lists),
                    'code_blocks_count': len(html_content.code_blocks),
                    'forms_count': len(html_content.forms)
                },
                'html_content': content_text,  # Store the actual content
                'processing_metadata': html_content.processing_metadata
            }
            uploaded_file.save()
            
            logger.info(f"Created UploadedFile {uploaded_file.id} from HTML content")
            return uploaded_file
            
        except Exception as e:
            logger.error(f"Error creating UploadedFile from HTML content: {e}", exc_info=True)
            return None
    
    def refresh_website(self, website_source_id: int):
        """Refresh website content by re-processing"""
        try:
            website_source = WebsiteSource.objects.get(id=website_source_id)
            logger.info(f"Refreshing website content for: {website_source.url}")
            
            # Reset processing status
            website_source.processing_status = 'pending'
            website_source.processing_error = None
            website_source.processing_started_at = None
            website_source.processing_completed_at = None
            website_source.metadata_extracted = False
            website_source.chunks_created = False
            website_source.embeddings_created = False
            website_source.chunk_count = 0
            website_source.embedding_count = 0
            website_source.save()
            
            # Delete existing chunks if any
            if website_source.uploaded_file:
                DocumentChunk.objects.filter(uploaded_file=website_source.uploaded_file).delete()
                logger.info(f"Deleted existing chunks for UploadedFile {website_source.uploaded_file.id}")
            
            # Re-process the website
            result = self.process_website_fully(website_source_id)
            
            # Update last refreshed timestamp
            website_source.last_refreshed_at = timezone.now()
            website_source.save()
            
            logger.info(f"Website refresh completed for: {website_source.url}")
            return result
            
        except Exception as e:
            logger.error(f"Error refreshing website {website_source_id}: {e}", exc_info=True)
            return {
                'status': 'failed',
                'website_source_id': website_source_id,
                'error': str(e)
            }


# Global instance
website_processor = WebsiteProcessor()
