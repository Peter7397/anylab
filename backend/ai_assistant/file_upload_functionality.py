"""
File Upload Functionality System

This module provides comprehensive file upload functionality
including file validation, processing, storage, and management.
"""

import logging
import os
import hashlib
import mimetypes
from typing import Dict, Any, List, Optional, Tuple, Union, BinaryIO
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from enum import Enum
from pathlib import Path
from django.core.files.storage import default_storage
from django.core.files.uploadedfile import InMemoryUploadedFile, TemporaryUploadedFile
from django.utils import timezone as django_timezone
from django.conf import settings

logger = logging.getLogger(__name__)


class FileType(Enum):
    """File type enumeration"""
    PDF = "pdf"
    DOCUMENT = "document"
    IMAGE = "image"
    VIDEO = "video"
    AUDIO = "audio"
    PRESENTATION = "presentation"
    SPREADSHEET = "spreadsheet"
    ARCHIVE = "archive"
    CODE = "code"
    TEXT = "text"
    DATA = "data"
    UNKNOWN = "unknown"


class UploadStatus(Enum):
    """Upload status enumeration"""
    PENDING = "pending"
    UPLOADING = "uploading"
    PROCESSING = "processing"
    COMPLETED = "completed"
    FAILED = "failed"
    REJECTED = "rejected"
    DUPLICATE = "duplicate"
    QUARANTINED = "quarantined"
    SCANNING = "scanning"
    SCAN_FAILED = "scan_failed"


class FileValidationResult(Enum):
    """File validation result enumeration"""
    VALID = "valid"
    INVALID_SIZE = "invalid_size"
    INVALID_TYPE = "invalid_type"
    INVALID_NAME = "invalid_name"
    MALICIOUS = "malicious"
    CORRUPTED = "corrupted"
    ENCRYPTED = "encrypted"
    PASSWORD_PROTECTED = "password_protected"
    UNSUPPORTED_FORMAT = "unsupported_format"


@dataclass
class FileUploadConfig:
    """File upload configuration"""
    max_file_size: int = 100 * 1024 * 1024  # 100MB
    max_total_size: int = 1024 * 1024 * 1024  # 1GB
    allowed_extensions: List[str] = field(default_factory=lambda: [
        '.pdf', '.doc', '.docx', '.txt', '.rtf',
        '.jpg', '.jpeg', '.png', '.gif', '.bmp', '.svg',
        '.mp4', '.avi', '.mov', '.wmv', '.flv', '.webm',
        '.mp3', '.wav', '.flac', '.aac', '.ogg',
        '.ppt', '.pptx',
        '.xls', '.xlsx', '.csv',
        '.zip', '.rar', '.7z', '.tar', '.gz',
        '.py', '.js', '.html', '.css', '.json', '.xml',
        '.csv', '.tsv', '.dat'
    ])
    blocked_extensions: List[str] = field(default_factory=lambda: [
        '.exe', '.bat', '.cmd', '.scr', '.pif', '.com',
        '.dll', '.sys', '.msi', '.app', '.deb', '.rpm'
    ])
    allowed_mime_types: List[str] = field(default_factory=lambda: [
        'application/pdf',
        'application/msword',
        'application/vnd.openxmlformats-officedocument.wordprocessingml.document',
        'text/plain',
        'text/rtf',
        'image/jpeg',
        'image/png',
        'image/gif',
        'image/bmp',
        'image/svg+xml',
        'video/mp4',
        'video/avi',
        'video/quicktime',
        'video/x-msvideo',
        'video/x-flv',
        'video/webm',
        'audio/mpeg',
        'audio/wav',
        'audio/flac',
        'audio/aac',
        'audio/ogg',
        'application/vnd.ms-powerpoint',
        'application/vnd.openxmlformats-officedocument.presentationml.presentation',
        'application/vnd.ms-excel',
        'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
        'text/csv',
        'application/zip',
        'application/x-rar-compressed',
        'application/x-7z-compressed',
        'application/x-tar',
        'application/gzip',
        'text/python',
        'application/javascript',
        'text/html',
        'text/css',
        'application/json',
        'application/xml',
        'text/xml'
    ])
    scan_for_viruses: bool = True
    extract_metadata: bool = True
    generate_thumbnails: bool = True
    auto_categorize: bool = True
    duplicate_detection: bool = True
    storage_backend: str = "default"
    temp_storage_path: str = "temp_uploads"
    permanent_storage_path: str = "uploads"
    thumbnail_storage_path: str = "thumbnails"
    metadata_storage_path: str = "metadata"


@dataclass
class FileUpload:
    """File upload structure"""
    id: str
    filename: str
    original_filename: str
    file_path: str
    file_size: int
    file_type: FileType
    mime_type: str
    file_hash: str
    uploaded_by: Optional[str] = None
    uploaded_at: datetime = field(default_factory=lambda: django_timezone.now())
    status: UploadStatus = UploadStatus.PENDING
    validation_result: Optional[FileValidationResult] = None
    metadata: Dict[str, Any] = field(default_factory=dict)
    thumbnail_path: Optional[str] = None
    processing_log: List[str] = field(default_factory=list)
    error_message: Optional[str] = None
    retry_count: int = 0
    max_retries: int = 3
    priority: int = 0
    auto_process: bool = True
    requires_review: bool = False
    review_status: Optional[str] = None
    reviewed_by: Optional[str] = None
    reviewed_at: Optional[datetime] = None
    processing_started_at: Optional[datetime] = None
    processing_completed_at: Optional[datetime] = None
    tags: List[str] = field(default_factory=list)
    category: Optional[str] = None
    description: Optional[str] = None
    is_public: bool = False
    access_level: str = "private"
    download_count: int = 0
    last_accessed_at: Optional[datetime] = None


@dataclass
class UploadProgress:
    """Upload progress structure"""
    upload_id: str
    filename: str
    total_size: int
    uploaded_size: int
    progress_percentage: float
    upload_speed: float  # bytes per second
    estimated_time_remaining: int  # seconds
    status: str
    error_message: Optional[str] = None


class FileUploadManager:
    """File Upload Manager"""
    
    def __init__(self, config: Dict[str, Any] = None):
        """Initialize file upload manager"""
        self.config = config or {}
        self.upload_enabled = self.config.get('upload_enabled', True)
        self.auto_processing_enabled = self.config.get('auto_processing_enabled', True)
        self.validation_enabled = self.config.get('validation_enabled', True)
        self.scanning_enabled = self.config.get('scanning_enabled', True)
        
        # Initialize components
        self.upload_config = FileUploadConfig()
        self.uploads = {}
        self.processing_queue = []
        self.failed_uploads = []
        self.upload_progress = {}
        
        # Initialize storage
        self._initialize_storage()
        
        # Initialize processing
        self._initialize_processing()
        
        logger.info("File Upload Manager initialized")
    
    def _initialize_storage(self):
        """Initialize storage components"""
        try:
            # Create storage directories
            self.temp_storage_path = os.path.join(settings.MEDIA_ROOT, self.upload_config.temp_storage_path)
            self.permanent_storage_path = os.path.join(settings.MEDIA_ROOT, self.upload_config.permanent_storage_path)
            self.thumbnail_storage_path = os.path.join(settings.MEDIA_ROOT, self.upload_config.thumbnail_storage_path)
            self.metadata_storage_path = os.path.join(settings.MEDIA_ROOT, self.upload_config.metadata_storage_path)
            
            # Create directories if they don't exist
            for path in [self.temp_storage_path, self.permanent_storage_path, 
                        self.thumbnail_storage_path, self.metadata_storage_path]:
                os.makedirs(path, exist_ok=True)
            
            logger.info("Storage components initialized")
            
        except Exception as e:
            logger.error(f"Error initializing storage: {e}")
            raise
    
    def _initialize_processing(self):
        """Initialize file processing components"""
        try:
            # Initialize file processors
            self.file_processors = {
                FileType.PDF: self._process_pdf_file,
                FileType.DOCUMENT: self._process_document_file,
                FileType.IMAGE: self._process_image_file,
                FileType.VIDEO: self._process_video_file,
                FileType.AUDIO: self._process_audio_file,
                FileType.PRESENTATION: self._process_presentation_file,
                FileType.SPREADSHEET: self._process_spreadsheet_file,
                FileType.ARCHIVE: self._process_archive_file,
                FileType.CODE: self._process_code_file,
                FileType.TEXT: self._process_text_file,
                FileType.DATA: self._process_data_file,
                FileType.UNKNOWN: self._process_unknown_file
            }
            
            # Initialize metadata extractors
            self.metadata_extractors = {
                FileType.PDF: self._extract_pdf_metadata,
                FileType.DOCUMENT: self._extract_document_metadata,
                FileType.IMAGE: self._extract_image_metadata,
                FileType.VIDEO: self._extract_video_metadata,
                FileType.AUDIO: self._extract_audio_metadata,
                FileType.PRESENTATION: self._extract_presentation_metadata,
                FileType.SPREADSHEET: self._extract_spreadsheet_metadata,
                FileType.ARCHIVE: self._extract_archive_metadata,
                FileType.CODE: self._extract_code_metadata,
                FileType.TEXT: self._extract_text_metadata,
                FileType.DATA: self._extract_data_metadata,
                FileType.UNKNOWN: self._extract_unknown_metadata
            }
            
            # Initialize thumbnail generators
            self.thumbnail_generators = {
                FileType.PDF: self._generate_pdf_thumbnail,
                FileType.IMAGE: self._generate_image_thumbnail,
                FileType.VIDEO: self._generate_video_thumbnail,
                FileType.PRESENTATION: self._generate_presentation_thumbnail,
                FileType.DOCUMENT: self._generate_document_thumbnail,
                FileType.SPREADSHEET: self._generate_spreadsheet_thumbnail
            }
            
            logger.info("File processing components initialized")
            
        except Exception as e:
            logger.error(f"Error initializing processing components: {e}")
            raise
    
    def upload_file(self, file: Union[InMemoryUploadedFile, TemporaryUploadedFile], **kwargs) -> FileUpload:
        """Upload a file"""
        try:
            # Generate upload ID
            upload_id = f"file_upload_{django_timezone.now().strftime('%Y%m%d_%H%M%S')}_{hash(file.name) % 10000}"
            
            # Validate file
            if self.validation_enabled:
                validation_result, validation_info = self.validate_file(file)
                if validation_result != FileValidationResult.VALID:
                    raise ValueError(f"File validation failed: {validation_info.get('error_message', 'Unknown error')}")
            
            # Generate file hash
            file_hash = self._generate_file_hash(file)
            
            # Check for duplicates
            if self.upload_config.duplicate_detection:
                existing_upload = self._find_duplicate_file(file_hash)
                if existing_upload:
                    existing_upload.status = UploadStatus.DUPLICATE
                    existing_upload.processing_log.append(f"Duplicate detected: {upload_id}")
                    return existing_upload
            
            # Determine file type
            file_type = self._detect_file_type(file)
            
            # Generate file path
            file_path = self._generate_file_path(upload_id, file.name, file_type)
            
            # Save file
            self._save_file(file, file_path)
            
            # Create upload record
            upload = FileUpload(
                id=upload_id,
                filename=file.name,
                original_filename=file.name,
                file_path=file_path,
                file_size=file.size,
                file_type=file_type,
                mime_type=file.content_type or mimetypes.guess_type(file.name)[0] or 'application/octet-stream',
                file_hash=file_hash,
                uploaded_by=kwargs.get('uploaded_by'),
                priority=kwargs.get('priority', 0),
                auto_process=kwargs.get('auto_process', True),
                requires_review=kwargs.get('requires_review', False),
                tags=kwargs.get('tags', []),
                category=kwargs.get('category'),
                description=kwargs.get('description'),
                is_public=kwargs.get('is_public', False),
                access_level=kwargs.get('access_level', 'private')
            )
            
            # Store upload
            self.uploads[upload_id] = upload
            
            # Add to processing queue if auto-processing is enabled
            if upload.auto_process and self.auto_processing_enabled:
                self.processing_queue.append(upload_id)
                self._process_upload(upload_id)
            
            logger.info(f"File uploaded: {file.name} (ID: {upload_id})")
            return upload
            
        except Exception as e:
            logger.error(f"Error uploading file: {e}")
            raise
    
    def validate_file(self, file: Union[InMemoryUploadedFile, TemporaryUploadedFile]) -> Tuple[FileValidationResult, Dict[str, Any]]:
        """Validate a file"""
        try:
            validation_info = {
                'filename': file.name,
                'file_size': file.size,
                'mime_type': file.content_type,
                'is_valid_size': False,
                'is_valid_type': False,
                'is_valid_name': False,
                'error_message': None
            }
            
            # Check file size
            if file.size > self.upload_config.max_file_size:
                validation_info['error_message'] = f"File size {file.size} exceeds limit {self.upload_config.max_file_size}"
                return FileValidationResult.INVALID_SIZE, validation_info
            
            validation_info['is_valid_size'] = True
            
            # Check file extension
            file_ext = Path(file.name).suffix.lower()
            if file_ext in self.upload_config.blocked_extensions:
                validation_info['error_message'] = f"File extension {file_ext} is blocked"
                return FileValidationResult.INVALID_TYPE, validation_info
            
            if file_ext not in self.upload_config.allowed_extensions:
                validation_info['error_message'] = f"File extension {file_ext} is not allowed"
                return FileValidationResult.INVALID_TYPE, validation_info
            
            validation_info['is_valid_type'] = True
            
            # Check MIME type
            if file.content_type and file.content_type not in self.upload_config.allowed_mime_types:
                validation_info['error_message'] = f"MIME type {file.content_type} is not allowed"
                return FileValidationResult.INVALID_TYPE, validation_info
            
            # Check filename
            if not self._is_valid_filename(file.name):
                validation_info['error_message'] = f"Invalid filename: {file.name}"
                return FileValidationResult.INVALID_NAME, validation_info
            
            validation_info['is_valid_name'] = True
            
            # Additional security checks
            if self._is_malicious_file(file):
                validation_info['error_message'] = "File appears to be malicious"
                return FileValidationResult.MALICIOUS, validation_info
            
            return FileValidationResult.VALID, validation_info
            
        except Exception as e:
            logger.error(f"Error validating file: {e}")
            return FileValidationResult.CORRUPTED, {'error_message': str(e)}
    
    def _is_valid_filename(self, filename: str) -> bool:
        """Check if filename is valid"""
        try:
            # Check for invalid characters
            invalid_chars = ['<', '>', ':', '"', '|', '?', '*', '\\', '/']
            if any(char in filename for char in invalid_chars):
                return False
            
            # Check for reserved names
            reserved_names = ['CON', 'PRN', 'AUX', 'NUL', 'COM1', 'COM2', 'COM3', 'COM4', 'COM5', 'COM6', 'COM7', 'COM8', 'COM9', 'LPT1', 'LPT2', 'LPT3', 'LPT4', 'LPT5', 'LPT6', 'LPT7', 'LPT8', 'LPT9']
            if filename.upper() in reserved_names:
                return False
            
            # Check filename length
            if len(filename) > 255:
                return False
            
            return True
            
        except Exception as e:
            logger.error(f"Error checking filename validity: {e}")
            return False
    
    def _is_malicious_file(self, file: Union[InMemoryUploadedFile, TemporaryUploadedFile]) -> bool:
        """Check if file appears to be malicious"""
        try:
            # Check file signature/magic bytes
            file.seek(0)
            header = file.read(1024)
            file.seek(0)
            
            # Check for executable signatures
            executable_signatures = [
                b'MZ',  # PE executable
                b'\x7fELF',  # ELF executable
                b'\xfe\xed\xfa',  # Mach-O executable
                b'#!/bin/',  # Shell script
                b'#!/usr/bin/',  # Shell script
            ]
            
            for signature in executable_signatures:
                if header.startswith(signature):
                    return True
            
            # Check for suspicious content
            suspicious_patterns = [
                b'eval(',
                b'exec(',
                b'system(',
                b'shell_exec(',
                b'passthru(',
                b'<script',
                b'javascript:',
                b'vbscript:',
                b'data:text/html',
            ]
            
            for pattern in suspicious_patterns:
                if pattern in header.lower():
                    return True
            
            return False
            
        except Exception as e:
            logger.error(f"Error checking file for malicious content: {e}")
            return True  # Err on the side of caution
    
    def _generate_file_hash(self, file: Union[InMemoryUploadedFile, TemporaryUploadedFile]) -> str:
        """Generate file hash"""
        try:
            file.seek(0)
            hasher = hashlib.sha256()
            
            # Read file in chunks to handle large files
            chunk_size = 8192
            while True:
                chunk = file.read(chunk_size)
                if not chunk:
                    break
                hasher.update(chunk)
            
            file.seek(0)
            return hasher.hexdigest()
            
        except Exception as e:
            logger.error(f"Error generating file hash: {e}")
            return ""
    
    def _detect_file_type(self, file: Union[InMemoryUploadedFile, TemporaryUploadedFile]) -> FileType:
        """Detect file type"""
        try:
            file_ext = Path(file.name).suffix.lower()
            mime_type = file.content_type or mimetypes.guess_type(file.name)[0] or ''
            
            # Check by extension
            if file_ext in ['.pdf']:
                return FileType.PDF
            elif file_ext in ['.doc', '.docx', '.txt', '.rtf']:
                return FileType.DOCUMENT
            elif file_ext in ['.jpg', '.jpeg', '.png', '.gif', '.bmp', '.svg']:
                return FileType.IMAGE
            elif file_ext in ['.mp4', '.avi', '.mov', '.wmv', '.flv', '.webm']:
                return FileType.VIDEO
            elif file_ext in ['.mp3', '.wav', '.flac', '.aac', '.ogg']:
                return FileType.AUDIO
            elif file_ext in ['.ppt', '.pptx']:
                return FileType.PRESENTATION
            elif file_ext in ['.xls', '.xlsx', '.csv']:
                return FileType.SPREADSHEET
            elif file_ext in ['.zip', '.rar', '.7z', '.tar', '.gz']:
                return FileType.ARCHIVE
            elif file_ext in ['.py', '.js', '.html', '.css', '.json', '.xml']:
                return FileType.CODE
            elif file_ext in ['.txt', '.md', '.log']:
                return FileType.TEXT
            elif file_ext in ['.csv', '.tsv', '.dat', '.json']:
                return FileType.DATA
            
            # Check by MIME type
            if 'pdf' in mime_type:
                return FileType.PDF
            elif 'image' in mime_type:
                return FileType.IMAGE
            elif 'video' in mime_type:
                return FileType.VIDEO
            elif 'audio' in mime_type:
                return FileType.AUDIO
            elif 'text' in mime_type:
                return FileType.TEXT
            
            return FileType.UNKNOWN
            
        except Exception as e:
            logger.error(f"Error detecting file type: {e}")
            return FileType.UNKNOWN
    
    def _generate_file_path(self, upload_id: str, filename: str, file_type: FileType) -> str:
        """Generate file path"""
        try:
            # Create directory structure: uploads/year/month/day/type/
            now = django_timezone.now()
            year = now.strftime('%Y')
            month = now.strftime('%m')
            day = now.strftime('%d')
            
            # Create directory path
            dir_path = os.path.join(
                self.permanent_storage_path,
                year,
                month,
                day,
                file_type.value
            )
            
            # Create directory if it doesn't exist
            os.makedirs(dir_path, exist_ok=True)
            
            # Generate filename with upload ID
            file_ext = Path(filename).suffix
            new_filename = f"{upload_id}{file_ext}"
            
            return os.path.join(dir_path, new_filename)
            
        except Exception as e:
            logger.error(f"Error generating file path: {e}")
            return os.path.join(self.permanent_storage_path, f"{upload_id}_{filename}")
    
    def _save_file(self, file: Union[InMemoryUploadedFile, TemporaryUploadedFile], file_path: str):
        """Save file to storage"""
        try:
            # Use Django's default storage
            with default_storage.open(file_path, 'wb') as destination:
                for chunk in file.chunks():
                    destination.write(chunk)
            
            logger.info(f"File saved to: {file_path}")
            
        except Exception as e:
            logger.error(f"Error saving file: {e}")
            raise
    
    def _find_duplicate_file(self, file_hash: str) -> Optional[FileUpload]:
        """Find duplicate file by hash"""
        try:
            for upload in self.uploads.values():
                if upload.file_hash == file_hash:
                    return upload
            return None
            
        except Exception as e:
            logger.error(f"Error finding duplicate file: {e}")
            return None
    
    def _process_upload(self, upload_id: str):
        """Process a file upload"""
        try:
            upload = self.uploads.get(upload_id)
            if not upload:
                return
            
            # Update status
            upload.status = UploadStatus.PROCESSING
            upload.processing_started_at = django_timezone.now()
            
            # Extract metadata
            if self.upload_config.extract_metadata:
                metadata_result = self._extract_metadata(upload)
                if metadata_result:
                    upload.metadata.update(metadata_result)
                    upload.processing_log.append("Metadata extracted successfully")
            
            # Generate thumbnail
            if self.upload_config.generate_thumbnails:
                thumbnail_result = self._generate_thumbnail(upload)
                if thumbnail_result:
                    upload.thumbnail_path = thumbnail_result
                    upload.processing_log.append("Thumbnail generated successfully")
            
            # Process file
            processor = self.file_processors.get(upload.file_type)
            if processor:
                processing_result = processor(upload)
                if processing_result:
                    upload.metadata.update(processing_result)
                    upload.processing_log.append(f"File processed successfully using {upload.file_type.value} processor")
            
            # Auto-categorize
            if self.upload_config.auto_categorize:
                category = self._auto_categorize_file(upload)
                if category:
                    upload.category = category
                    upload.processing_log.append(f"File auto-categorized as: {category}")
            
            # Scan for viruses
            if self.upload_config.scan_for_viruses and self.scanning_enabled:
                scan_result = self._scan_file(upload)
                if scan_result:
                    upload.metadata['virus_scan'] = scan_result
                    upload.processing_log.append("Virus scan completed")
            
            upload.status = UploadStatus.COMPLETED
            upload.processing_completed_at = django_timezone.now()
            
            logger.info(f"Processed file upload: {upload_id}")
            
        except Exception as e:
            logger.error(f"Error processing upload {upload_id}: {e}")
            upload = self.uploads.get(upload_id)
            if upload:
                upload.status = UploadStatus.FAILED
                upload.error_message = str(e)
                upload.processing_completed_at = django_timezone.now()
    
    def _extract_metadata(self, upload: FileUpload) -> Optional[Dict[str, Any]]:
        """Extract metadata from file"""
        try:
            extractor = self.metadata_extractors.get(upload.file_type)
            if extractor:
                return extractor(upload)
            return None
            
        except Exception as e:
            logger.error(f"Error extracting metadata: {e}")
            return None
    
    def _generate_thumbnail(self, upload: FileUpload) -> Optional[str]:
        """Generate thumbnail for file"""
        try:
            generator = self.thumbnail_generators.get(upload.file_type)
            if generator:
                return generator(upload)
            return None
            
        except Exception as e:
            logger.error(f"Error generating thumbnail: {e}")
            return None
    
    def _auto_categorize_file(self, upload: FileUpload) -> Optional[str]:
        """Auto-categorize file"""
        try:
            # Simple categorization based on file type and content
            if upload.file_type == FileType.PDF:
                if 'manual' in upload.filename.lower() or 'guide' in upload.filename.lower():
                    return 'user_manual'
                elif 'troubleshooting' in upload.filename.lower() or 'troubleshoot' in upload.filename.lower():
                    return 'troubleshooting'
                elif 'specification' in upload.filename.lower() or 'spec' in upload.filename.lower():
                    return 'specification'
                else:
                    return 'documentation'
            
            elif upload.file_type == FileType.IMAGE:
                return 'image'
            
            elif upload.file_type == FileType.VIDEO:
                return 'video'
            
            elif upload.file_type == FileType.AUDIO:
                return 'audio'
            
            elif upload.file_type == FileType.CODE:
                return 'code'
            
            elif upload.file_type == FileType.DATA:
                return 'data'
            
            return 'other'
            
        except Exception as e:
            logger.error(f"Error auto-categorizing file: {e}")
            return None
    
    def _scan_file(self, upload: FileUpload) -> Optional[Dict[str, Any]]:
        """Scan file for viruses"""
        try:
            # In production, integrate with antivirus software
            # For now, return a mock scan result
            return {
                'scanned_at': django_timezone.now().isoformat(),
                'scan_result': 'clean',
                'scan_engine': 'mock_antivirus',
                'threats_found': 0,
                'scan_duration': 1.5
            }
            
        except Exception as e:
            logger.error(f"Error scanning file: {e}")
            return None
    
    # File processor methods
    def _process_pdf_file(self, upload: FileUpload) -> Optional[Dict[str, Any]]:
        """Process PDF file"""
        try:
            # In production, use PyMuPDF or similar
            return {
                'page_count': 1,
                'text_extracted': True,
                'images_extracted': False,
                'processing_method': 'pdf_processor'
            }
            
        except Exception as e:
            logger.error(f"Error processing PDF file: {e}")
            return None
    
    def _process_document_file(self, upload: FileUpload) -> Optional[Dict[str, Any]]:
        """Process document file"""
        try:
            # In production, use python-docx or similar
            return {
                'word_count': 0,
                'paragraph_count': 0,
                'processing_method': 'document_processor'
            }
            
        except Exception as e:
            logger.error(f"Error processing document file: {e}")
            return None
    
    def _process_image_file(self, upload: FileUpload) -> Optional[Dict[str, Any]]:
        """Process image file"""
        try:
            # In production, use PIL or similar
            return {
                'width': 0,
                'height': 0,
                'color_mode': 'RGB',
                'processing_method': 'image_processor'
            }
            
        except Exception as e:
            logger.error(f"Error processing image file: {e}")
            return None
    
    def _process_video_file(self, upload: FileUpload) -> Optional[Dict[str, Any]]:
        """Process video file"""
        try:
            # In production, use OpenCV or similar
            return {
                'duration': 0,
                'width': 0,
                'height': 0,
                'fps': 0,
                'processing_method': 'video_processor'
            }
            
        except Exception as e:
            logger.error(f"Error processing video file: {e}")
            return None
    
    def _process_audio_file(self, upload: FileUpload) -> Optional[Dict[str, Any]]:
        """Process audio file"""
        try:
            # In production, use librosa or similar
            return {
                'duration': 0,
                'sample_rate': 0,
                'channels': 0,
                'processing_method': 'audio_processor'
            }
            
        except Exception as e:
            logger.error(f"Error processing audio file: {e}")
            return None
    
    def _process_presentation_file(self, upload: FileUpload) -> Optional[Dict[str, Any]]:
        """Process presentation file"""
        try:
            # In production, use python-pptx or similar
            return {
                'slide_count': 0,
                'processing_method': 'presentation_processor'
            }
            
        except Exception as e:
            logger.error(f"Error processing presentation file: {e}")
            return None
    
    def _process_spreadsheet_file(self, upload: FileUpload) -> Optional[Dict[str, Any]]:
        """Process spreadsheet file"""
        try:
            # In production, use openpyxl or similar
            return {
                'sheet_count': 0,
                'row_count': 0,
                'column_count': 0,
                'processing_method': 'spreadsheet_processor'
            }
            
        except Exception as e:
            logger.error(f"Error processing spreadsheet file: {e}")
            return None
    
    def _process_archive_file(self, upload: FileUpload) -> Optional[Dict[str, Any]]:
        """Process archive file"""
        try:
            # In production, use zipfile or similar
            return {
                'file_count': 0,
                'compression_ratio': 0,
                'processing_method': 'archive_processor'
            }
            
        except Exception as e:
            logger.error(f"Error processing archive file: {e}")
            return None
    
    def _process_code_file(self, upload: FileUpload) -> Optional[Dict[str, Any]]:
        """Process code file"""
        try:
            # In production, use AST parsing or similar
            return {
                'line_count': 0,
                'function_count': 0,
                'class_count': 0,
                'processing_method': 'code_processor'
            }
            
        except Exception as e:
            logger.error(f"Error processing code file: {e}")
            return None
    
    def _process_text_file(self, upload: FileUpload) -> Optional[Dict[str, Any]]:
        """Process text file"""
        try:
            # In production, use text processing libraries
            return {
                'line_count': 0,
                'word_count': 0,
                'character_count': 0,
                'processing_method': 'text_processor'
            }
            
        except Exception as e:
            logger.error(f"Error processing text file: {e}")
            return None
    
    def _process_data_file(self, upload: FileUpload) -> Optional[Dict[str, Any]]:
        """Process data file"""
        try:
            # In production, use pandas or similar
            return {
                'row_count': 0,
                'column_count': 0,
                'data_types': [],
                'processing_method': 'data_processor'
            }
            
        except Exception as e:
            logger.error(f"Error processing data file: {e}")
            return None
    
    def _process_unknown_file(self, upload: FileUpload) -> Optional[Dict[str, Any]]:
        """Process unknown file type"""
        try:
            return {
                'processing_method': 'unknown_processor',
                'note': 'File type not recognized'
            }
            
        except Exception as e:
            logger.error(f"Error processing unknown file: {e}")
            return None
    
    # Metadata extractor methods
    def _extract_pdf_metadata(self, upload: FileUpload) -> Optional[Dict[str, Any]]:
        """Extract PDF metadata"""
        try:
            # In production, use PyMuPDF or similar
            return {
                'title': None,
                'author': None,
                'subject': None,
                'creator': None,
                'producer': None,
                'creation_date': None,
                'modification_date': None,
                'page_count': 0,
                'extraction_method': 'pdf_metadata_extractor'
            }
            
        except Exception as e:
            logger.error(f"Error extracting PDF metadata: {e}")
            return None
    
    def _extract_document_metadata(self, upload: FileUpload) -> Optional[Dict[str, Any]]:
        """Extract document metadata"""
        try:
            # In production, use python-docx or similar
            return {
                'title': None,
                'author': None,
                'subject': None,
                'keywords': None,
                'creation_date': None,
                'modification_date': None,
                'word_count': 0,
                'extraction_method': 'document_metadata_extractor'
            }
            
        except Exception as e:
            logger.error(f"Error extracting document metadata: {e}")
            return None
    
    def _extract_image_metadata(self, upload: FileUpload) -> Optional[Dict[str, Any]]:
        """Extract image metadata"""
        try:
            # In production, use PIL or similar
            return {
                'width': 0,
                'height': 0,
                'color_mode': 'RGB',
                'dpi': 0,
                'exif_data': {},
                'extraction_method': 'image_metadata_extractor'
            }
            
        except Exception as e:
            logger.error(f"Error extracting image metadata: {e}")
            return None
    
    def _extract_video_metadata(self, upload: FileUpload) -> Optional[Dict[str, Any]]:
        """Extract video metadata"""
        try:
            # In production, use OpenCV or similar
            return {
                'duration': 0,
                'width': 0,
                'height': 0,
                'fps': 0,
                'codec': None,
                'bitrate': 0,
                'extraction_method': 'video_metadata_extractor'
            }
            
        except Exception as e:
            logger.error(f"Error extracting video metadata: {e}")
            return None
    
    def _extract_audio_metadata(self, upload: FileUpload) -> Optional[Dict[str, Any]]:
        """Extract audio metadata"""
        try:
            # In production, use librosa or similar
            return {
                'duration': 0,
                'sample_rate': 0,
                'channels': 0,
                'bitrate': 0,
                'codec': None,
                'extraction_method': 'audio_metadata_extractor'
            }
            
        except Exception as e:
            logger.error(f"Error extracting audio metadata: {e}")
            return None
    
    def _extract_presentation_metadata(self, upload: FileUpload) -> Optional[Dict[str, Any]]:
        """Extract presentation metadata"""
        try:
            # In production, use python-pptx or similar
            return {
                'title': None,
                'author': None,
                'subject': None,
                'slide_count': 0,
                'creation_date': None,
                'modification_date': None,
                'extraction_method': 'presentation_metadata_extractor'
            }
            
        except Exception as e:
            logger.error(f"Error extracting presentation metadata: {e}")
            return None
    
    def _extract_spreadsheet_metadata(self, upload: FileUpload) -> Optional[Dict[str, Any]]:
        """Extract spreadsheet metadata"""
        try:
            # In production, use openpyxl or similar
            return {
                'title': None,
                'author': None,
                'subject': None,
                'sheet_count': 0,
                'creation_date': None,
                'modification_date': None,
                'extraction_method': 'spreadsheet_metadata_extractor'
            }
            
        except Exception as e:
            logger.error(f"Error extracting spreadsheet metadata: {e}")
            return None
    
    def _extract_archive_metadata(self, upload: FileUpload) -> Optional[Dict[str, Any]]:
        """Extract archive metadata"""
        try:
            # In production, use zipfile or similar
            return {
                'file_count': 0,
                'compression_ratio': 0,
                'extraction_method': 'archive_metadata_extractor'
            }
            
        except Exception as e:
            logger.error(f"Error extracting archive metadata: {e}")
            return None
    
    def _extract_code_metadata(self, upload: FileUpload) -> Optional[Dict[str, Any]]:
        """Extract code metadata"""
        try:
            # In production, use AST parsing or similar
            return {
                'line_count': 0,
                'function_count': 0,
                'class_count': 0,
                'import_count': 0,
                'extraction_method': 'code_metadata_extractor'
            }
            
        except Exception as e:
            logger.error(f"Error extracting code metadata: {e}")
            return None
    
    def _extract_text_metadata(self, upload: FileUpload) -> Optional[Dict[str, Any]]:
        """Extract text metadata"""
        try:
            # In production, use text processing libraries
            return {
                'line_count': 0,
                'word_count': 0,
                'character_count': 0,
                'language': None,
                'extraction_method': 'text_metadata_extractor'
            }
            
        except Exception as e:
            logger.error(f"Error extracting text metadata: {e}")
            return None
    
    def _extract_data_metadata(self, upload: FileUpload) -> Optional[Dict[str, Any]]:
        """Extract data metadata"""
        try:
            # In production, use pandas or similar
            return {
                'row_count': 0,
                'column_count': 0,
                'data_types': [],
                'extraction_method': 'data_metadata_extractor'
            }
            
        except Exception as e:
            logger.error(f"Error extracting data metadata: {e}")
            return None
    
    def _extract_unknown_metadata(self, upload: FileUpload) -> Optional[Dict[str, Any]]:
        """Extract unknown file metadata"""
        try:
            return {
                'extraction_method': 'unknown_metadata_extractor',
                'note': 'File type not recognized'
            }
            
        except Exception as e:
            logger.error(f"Error extracting unknown metadata: {e}")
            return None
    
    # Thumbnail generator methods
    def _generate_pdf_thumbnail(self, upload: FileUpload) -> Optional[str]:
        """Generate PDF thumbnail"""
        try:
            # In production, use PyMuPDF or similar
            thumbnail_filename = f"{upload.id}_thumb.png"
            thumbnail_path = os.path.join(self.thumbnail_storage_path, thumbnail_filename)
            
            # Mock thumbnail generation
            with open(thumbnail_path, 'w') as f:
                f.write("Mock PDF thumbnail")
            
            return thumbnail_path
            
        except Exception as e:
            logger.error(f"Error generating PDF thumbnail: {e}")
            return None
    
    def _generate_image_thumbnail(self, upload: FileUpload) -> Optional[str]:
        """Generate image thumbnail"""
        try:
            # In production, use PIL or similar
            thumbnail_filename = f"{upload.id}_thumb.png"
            thumbnail_path = os.path.join(self.thumbnail_storage_path, thumbnail_filename)
            
            # Mock thumbnail generation
            with open(thumbnail_path, 'w') as f:
                f.write("Mock image thumbnail")
            
            return thumbnail_path
            
        except Exception as e:
            logger.error(f"Error generating image thumbnail: {e}")
            return None
    
    def _generate_video_thumbnail(self, upload: FileUpload) -> Optional[str]:
        """Generate video thumbnail"""
        try:
            # In production, use OpenCV or similar
            thumbnail_filename = f"{upload.id}_thumb.png"
            thumbnail_path = os.path.join(self.thumbnail_storage_path, thumbnail_filename)
            
            # Mock thumbnail generation
            with open(thumbnail_path, 'w') as f:
                f.write("Mock video thumbnail")
            
            return thumbnail_path
            
        except Exception as e:
            logger.error(f"Error generating video thumbnail: {e}")
            return None
    
    def _generate_presentation_thumbnail(self, upload: FileUpload) -> Optional[str]:
        """Generate presentation thumbnail"""
        try:
            # In production, use python-pptx or similar
            thumbnail_filename = f"{upload.id}_thumb.png"
            thumbnail_path = os.path.join(self.thumbnail_storage_path, thumbnail_filename)
            
            # Mock thumbnail generation
            with open(thumbnail_path, 'w') as f:
                f.write("Mock presentation thumbnail")
            
            return thumbnail_path
            
        except Exception as e:
            logger.error(f"Error generating presentation thumbnail: {e}")
            return None
    
    def _generate_document_thumbnail(self, upload: FileUpload) -> Optional[str]:
        """Generate document thumbnail"""
        try:
            # In production, use python-docx or similar
            thumbnail_filename = f"{upload.id}_thumb.png"
            thumbnail_path = os.path.join(self.thumbnail_storage_path, thumbnail_filename)
            
            # Mock thumbnail generation
            with open(thumbnail_path, 'w') as f:
                f.write("Mock document thumbnail")
            
            return thumbnail_path
            
        except Exception as e:
            logger.error(f"Error generating document thumbnail: {e}")
            return None
    
    def _generate_spreadsheet_thumbnail(self, upload: FileUpload) -> Optional[str]:
        """Generate spreadsheet thumbnail"""
        try:
            # In production, use openpyxl or similar
            thumbnail_filename = f"{upload.id}_thumb.png"
            thumbnail_path = os.path.join(self.thumbnail_storage_path, thumbnail_filename)
            
            # Mock thumbnail generation
            with open(thumbnail_path, 'w') as f:
                f.write("Mock spreadsheet thumbnail")
            
            return thumbnail_path
            
        except Exception as e:
            logger.error(f"Error generating spreadsheet thumbnail: {e}")
            return None
    
    def get_upload(self, upload_id: str) -> Optional[FileUpload]:
        """Get an upload by ID"""
        return self.uploads.get(upload_id)
    
    def get_uploads(self, status: UploadStatus = None, uploaded_by: str = None) -> List[FileUpload]:
        """Get uploads filtered by status and user"""
        try:
            uploads = list(self.uploads.values())
            
            if status:
                uploads = [u for u in uploads if u.status == status]
            
            if uploaded_by:
                uploads = [u for u in uploads if u.uploaded_by == uploaded_by]
            
            return sorted(uploads, key=lambda x: x.uploaded_at, reverse=True)
            
        except Exception as e:
            logger.error(f"Error getting uploads: {e}")
            return []
    
    def delete_upload(self, upload_id: str):
        """Delete an upload"""
        try:
            upload = self.get_upload(upload_id)
            if upload:
                # Delete file
                if default_storage.exists(upload.file_path):
                    default_storage.delete(upload.file_path)
                
                # Delete thumbnail
                if upload.thumbnail_path and default_storage.exists(upload.thumbnail_path):
                    default_storage.delete(upload.thumbnail_path)
                
                # Delete metadata file
                metadata_path = os.path.join(self.metadata_storage_path, f"{upload_id}.json")
                if os.path.exists(metadata_path):
                    os.remove(metadata_path)
                
                # Remove from uploads
                del self.uploads[upload_id]
                
                logger.info(f"Deleted upload: {upload_id}")
            
        except Exception as e:
            logger.error(f"Error deleting upload: {e}")
    
    def get_upload_statistics(self) -> Dict[str, Any]:
        """Get upload statistics"""
        try:
            stats = {
                'total_uploads': len(self.uploads),
                'uploads_by_status': {},
                'uploads_by_type': {},
                'uploads_by_user': {},
                'total_file_size': 0,
                'average_file_size': 0,
                'processing_queue_size': len(self.processing_queue),
                'failed_uploads_count': len(self.failed_uploads),
                'success_rate': 0
            }
            
            # Count by status and type
            for upload in self.uploads.values():
                status = upload.status.value
                stats['uploads_by_status'][status] = stats['uploads_by_status'].get(status, 0) + 1
                
                file_type = upload.file_type.value
                stats['uploads_by_type'][file_type] = stats['uploads_by_type'].get(file_type, 0) + 1
                
                # Count by user
                if upload.uploaded_by:
                    stats['uploads_by_user'][upload.uploaded_by] = stats['uploads_by_user'].get(upload.uploaded_by, 0) + 1
                
                # Calculate total file size
                stats['total_file_size'] += upload.file_size
            
            # Calculate averages
            if stats['total_uploads'] > 0:
                stats['average_file_size'] = stats['total_file_size'] / stats['total_uploads']
                
                # Calculate success rate
                completed_count = stats['uploads_by_status'].get(UploadStatus.COMPLETED.value, 0)
                stats['success_rate'] = (completed_count / stats['total_uploads']) * 100
            
            return stats
            
        except Exception as e:
            logger.error(f"Error getting upload statistics: {e}")
            return {}
    
    def bulk_upload_files(self, files: List[Union[InMemoryUploadedFile, TemporaryUploadedFile]], **kwargs) -> List[FileUpload]:
        """Bulk upload multiple files"""
        try:
            uploads = []
            
            for file in files:
                upload = self.upload_file(file, **kwargs)
                uploads.append(upload)
            
            logger.info(f"Bulk uploaded {len(files)} files")
            return uploads
            
        except Exception as e:
            logger.error(f"Error bulk uploading files: {e}")
            return []
    
    def export_uploads(self, upload_ids: List[str] = None) -> List[Dict[str, Any]]:
        """Export uploads data"""
        try:
            if upload_ids:
                uploads = [self.uploads.get(uid) for uid in upload_ids if uid in self.uploads]
            else:
                uploads = list(self.uploads.values())
            
            export_data = []
            for upload in uploads:
                if upload:
                    export_data.append({
                        'id': upload.id,
                        'filename': upload.filename,
                        'original_filename': upload.original_filename,
                        'file_path': upload.file_path,
                        'file_size': upload.file_size,
                        'file_type': upload.file_type.value,
                        'mime_type': upload.mime_type,
                        'file_hash': upload.file_hash,
                        'uploaded_by': upload.uploaded_by,
                        'uploaded_at': upload.uploaded_at.isoformat(),
                        'status': upload.status.value,
                        'validation_result': upload.validation_result.value if upload.validation_result else None,
                        'metadata': upload.metadata,
                        'thumbnail_path': upload.thumbnail_path,
                        'processing_log': upload.processing_log,
                        'error_message': upload.error_message,
                        'retry_count': upload.retry_count,
                        'priority': upload.priority,
                        'auto_process': upload.auto_process,
                        'requires_review': upload.requires_review,
                        'review_status': upload.review_status,
                        'reviewed_by': upload.reviewed_by,
                        'reviewed_at': upload.reviewed_at.isoformat() if upload.reviewed_at else None,
                        'processing_started_at': upload.processing_started_at.isoformat() if upload.processing_started_at else None,
                        'processing_completed_at': upload.processing_completed_at.isoformat() if upload.processing_completed_at else None,
                        'tags': upload.tags,
                        'category': upload.category,
                        'description': upload.description,
                        'is_public': upload.is_public,
                        'access_level': upload.access_level,
                        'download_count': upload.download_count,
                        'last_accessed_at': upload.last_accessed_at.isoformat() if upload.last_accessed_at else None
                    })
            
            return export_data
            
        except Exception as e:
            logger.error(f"Error exporting uploads: {e}")
            return []
    
    def import_uploads(self, uploads_data: List[Dict[str, Any]]):
        """Import uploads data"""
        try:
            for upload_data in uploads_data:
                upload = FileUpload(
                    id=upload_data['id'],
                    filename=upload_data['filename'],
                    original_filename=upload_data['original_filename'],
                    file_path=upload_data['file_path'],
                    file_size=upload_data['file_size'],
                    file_type=FileType(upload_data['file_type']),
                    mime_type=upload_data['mime_type'],
                    file_hash=upload_data['file_hash'],
                    uploaded_by=upload_data.get('uploaded_by'),
                    uploaded_at=datetime.fromisoformat(upload_data['uploaded_at']),
                    status=UploadStatus(upload_data['status']),
                    validation_result=FileValidationResult(upload_data['validation_result']) if upload_data.get('validation_result') else None,
                    metadata=upload_data.get('metadata', {}),
                    thumbnail_path=upload_data.get('thumbnail_path'),
                    processing_log=upload_data.get('processing_log', []),
                    error_message=upload_data.get('error_message'),
                    retry_count=upload_data.get('retry_count', 0),
                    priority=upload_data.get('priority', 0),
                    auto_process=upload_data.get('auto_process', True),
                    requires_review=upload_data.get('requires_review', False),
                    review_status=upload_data.get('review_status'),
                    reviewed_by=upload_data.get('reviewed_by'),
                    reviewed_at=datetime.fromisoformat(upload_data['reviewed_at']) if upload_data.get('reviewed_at') else None,
                    processing_started_at=datetime.fromisoformat(upload_data['processing_started_at']) if upload_data.get('processing_started_at') else None,
                    processing_completed_at=datetime.fromisoformat(upload_data['processing_completed_at']) if upload_data.get('processing_completed_at') else None,
                    tags=upload_data.get('tags', []),
                    category=upload_data.get('category'),
                    description=upload_data.get('description'),
                    is_public=upload_data.get('is_public', False),
                    access_level=upload_data.get('access_level', 'private'),
                    download_count=upload_data.get('download_count', 0),
                    last_accessed_at=datetime.fromisoformat(upload_data['last_accessed_at']) if upload_data.get('last_accessed_at') else None
                )
                
                self.uploads[upload.id] = upload
            
            logger.info(f"Imported {len(uploads_data)} uploads")
            
        except Exception as e:
            logger.error(f"Error importing uploads: {e}")
            raise
    
    def cleanup_old_uploads(self, days_old: int = 30):
        """Clean up old uploads"""
        try:
            cutoff_date = django_timezone.now() - timedelta(days=days_old)
            old_uploads = [
                uid for uid, upload in self.uploads.items()
                if upload.uploaded_at < cutoff_date
            ]
            
            for upload_id in old_uploads:
                self.delete_upload(upload_id)
            
            logger.info(f"Cleaned up {len(old_uploads)} old uploads")
            
        except Exception as e:
            logger.error(f"Error cleaning up old uploads: {e}")
    
    def get_processing_queue_status(self) -> Dict[str, Any]:
        """Get processing queue status"""
        try:
            return {
                'queue_size': len(self.processing_queue),
                'failed_count': len(self.failed_uploads),
                'processing_count': len([
                    u for u in self.uploads.values()
                    if u.status == UploadStatus.PROCESSING
                ]),
                'pending_count': len([
                    u for u in self.uploads.values()
                    if u.status == UploadStatus.PENDING
                ]),
                'completed_count': len([
                    u for u in self.uploads.values()
                    if u.status == UploadStatus.COMPLETED
                ])
            }
            
        except Exception as e:
            logger.error(f"Error getting processing queue status: {e}")
            return {}
    
    def pause_processing(self):
        """Pause file processing"""
        self.auto_processing_enabled = False
        logger.info("File processing paused")
    
    def resume_processing(self):
        """Resume file processing"""
        self.auto_processing_enabled = True
        logger.info("File processing resumed")
    
    def update_upload_config(self, config: Dict[str, Any]):
        """Update upload configuration"""
        try:
            for key, value in config.items():
                if hasattr(self.upload_config, key):
                    setattr(self.upload_config, key, value)
            
            logger.info("Upload configuration updated")
            
        except Exception as e:
            logger.error(f"Error updating upload configuration: {e}")
    
    def get_upload_config(self) -> Dict[str, Any]:
        """Get upload configuration"""
        try:
            return {
                'max_file_size': self.upload_config.max_file_size,
                'max_total_size': self.upload_config.max_total_size,
                'allowed_extensions': self.upload_config.allowed_extensions,
                'blocked_extensions': self.upload_config.blocked_extensions,
                'allowed_mime_types': self.upload_config.allowed_mime_types,
                'scan_for_viruses': self.upload_config.scan_for_viruses,
                'extract_metadata': self.upload_config.extract_metadata,
                'generate_thumbnails': self.upload_config.generate_thumbnails,
                'auto_categorize': self.upload_config.auto_categorize,
                'duplicate_detection': self.upload_config.duplicate_detection,
                'storage_backend': self.upload_config.storage_backend,
                'temp_storage_path': self.upload_config.temp_storage_path,
                'permanent_storage_path': self.upload_config.permanent_storage_path,
                'thumbnail_storage_path': self.upload_config.thumbnail_storage_path,
                'metadata_storage_path': self.upload_config.metadata_storage_path
            }
            
        except Exception as e:
            logger.error(f"Error getting upload configuration: {e}")
            return {}
