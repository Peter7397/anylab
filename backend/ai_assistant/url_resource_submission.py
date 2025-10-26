"""
URL-Based Resource Submission System

This module provides URL-based resource submission functionality
including URL validation, content extraction, and automatic processing.
"""

import logging
import re
import requests
from typing import Dict, Any, List, Optional, Tuple, Union
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from enum import Enum
from urllib.parse import urlparse, urljoin
from django.utils import timezone as django_timezone
from django.core.validators import URLValidator
from django.core.exceptions import ValidationError

logger = logging.getLogger(__name__)


class ResourceType(Enum):
    """Resource type enumeration"""
    DOCUMENT = "document"
    WEBPAGE = "webpage"
    PDF = "pdf"
    VIDEO = "video"
    IMAGE = "image"
    AUDIO = "audio"
    PRESENTATION = "presentation"
    SPREADSHEET = "spreadsheet"
    CODE_REPOSITORY = "code_repository"
    FORUM_POST = "forum_post"
    BLOG_POST = "blog_post"
    NEWS_ARTICLE = "news_article"
    TECHNICAL_DOCUMENT = "technical_document"
    USER_MANUAL = "user_manual"
    TROUBLESHOOTING_GUIDE = "troubleshooting_guide"
    API_DOCUMENTATION = "api_documentation"
    WHITE_PAPER = "white_paper"
    CASE_STUDY = "case_study"
    WEBINAR = "webinar"
    TUTORIAL = "tutorial"


class SubmissionStatus(Enum):
    """Submission status enumeration"""
    PENDING = "pending"
    PROCESSING = "processing"
    COMPLETED = "completed"
    FAILED = "failed"
    REJECTED = "rejected"
    DUPLICATE = "duplicate"
    INVALID_URL = "invalid_url"
    CONTENT_UNAVAILABLE = "content_unavailable"
    PROCESSING_ERROR = "processing_error"


class URLValidationResult(Enum):
    """URL validation result enumeration"""
    VALID = "valid"
    INVALID_FORMAT = "invalid_format"
    UNREACHABLE = "unreachable"
    REDIRECT = "redirect"
    BLOCKED = "blocked"
    TIMEOUT = "timeout"
    SSL_ERROR = "ssl_error"
    CONTENT_TYPE_UNSUPPORTED = "content_type_unsupported"


@dataclass
class URLSubmission:
    """URL submission structure"""
    id: str
    url: str
    title: Optional[str] = None
    description: Optional[str] = None
    resource_type: Optional[ResourceType] = None
    category: Optional[str] = None
    tags: List[str] = field(default_factory=list)
    submitted_by: Optional[str] = None
    submitted_at: datetime = field(default_factory=lambda: django_timezone.now())
    status: SubmissionStatus = SubmissionStatus.PENDING
    validation_result: Optional[URLValidationResult] = None
    content_preview: Optional[str] = None
    metadata: Dict[str, Any] = field(default_factory=dict)
    processing_log: List[str] = field(default_factory=list)
    error_message: Optional[str] = None
    retry_count: int = 0
    max_retries: int = 3
    priority: int = 0  # Higher number = higher priority
    auto_process: bool = True
    requires_review: bool = False
    review_status: Optional[str] = None
    reviewed_by: Optional[str] = None
    reviewed_at: Optional[datetime] = None
    processing_started_at: Optional[datetime] = None
    processing_completed_at: Optional[datetime] = None


@dataclass
class URLValidationConfig:
    """URL validation configuration"""
    timeout: int = 30
    max_redirects: int = 5
    user_agent: str = "AnyLab-Resource-Submission/1.0"
    allowed_content_types: List[str] = field(default_factory=lambda: [
        "text/html",
        "text/plain",
        "application/pdf",
        "application/msword",
        "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
        "application/vnd.ms-excel",
        "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        "application/vnd.ms-powerpoint",
        "application/vnd.openxmlformats-officedocument.presentationml.presentation",
        "image/jpeg",
        "image/png",
        "image/gif",
        "video/mp4",
        "video/webm",
        "audio/mpeg",
        "audio/wav"
    ])
    blocked_domains: List[str] = field(default_factory=lambda: [
        "localhost",
        "127.0.0.1",
        "0.0.0.0"
    ])
    blocked_extensions: List[str] = field(default_factory=lambda: [
        ".exe",
        ".bat",
        ".cmd",
        ".scr",
        ".pif",
        ".com"
    ])
    require_https: bool = False
    max_content_size: int = 100 * 1024 * 1024  # 100MB


@dataclass
class ContentExtractionResult:
    """Content extraction result structure"""
    success: bool
    title: Optional[str] = None
    content: Optional[str] = None
    metadata: Dict[str, Any] = field(default_factory=dict)
    images: List[str] = field(default_factory=list)
    links: List[str] = field(default_factory=list)
    language: Optional[str] = None
    word_count: int = 0
    reading_time: int = 0
    error_message: Optional[str] = None
    extraction_method: Optional[str] = None


class URLResourceSubmissionManager:
    """URL-Based Resource Submission Manager"""
    
    def __init__(self, config: Dict[str, Any] = None):
        """Initialize URL resource submission manager"""
        self.config = config or {}
        self.submission_enabled = self.config.get('submission_enabled', True)
        self.auto_processing_enabled = self.config.get('auto_processing_enabled', True)
        self.validation_enabled = self.config.get('validation_enabled', True)
        self.extraction_enabled = self.config.get('extraction_enabled', True)
        
        # Initialize components
        self.url_validator = URLValidator()
        self.validation_config = URLValidationConfig()
        self.submissions = {}
        self.processing_queue = []
        self.failed_submissions = []
        
        # Initialize processing
        self._initialize_processing()
        
        logger.info("URL Resource Submission Manager initialized")
    
    def _initialize_processing(self):
        """Initialize URL processing components"""
        try:
            # Initialize content extractors
            self.content_extractors = {
                ResourceType.WEBPAGE: self._extract_webpage_content,
                ResourceType.PDF: self._extract_pdf_content,
                ResourceType.DOCUMENT: self._extract_document_content,
                ResourceType.VIDEO: self._extract_video_content,
                ResourceType.IMAGE: self._extract_image_content,
                ResourceType.AUDIO: self._extract_audio_content,
                ResourceType.PRESENTATION: self._extract_presentation_content,
                ResourceType.SPREADSHEET: self._extract_spreadsheet_content,
                ResourceType.CODE_REPOSITORY: self._extract_code_repository_content,
                ResourceType.FORUM_POST: self._extract_forum_post_content,
                ResourceType.BLOG_POST: self._extract_blog_post_content,
                ResourceType.NEWS_ARTICLE: self._extract_news_article_content,
                ResourceType.TECHNICAL_DOCUMENT: self._extract_technical_document_content,
                ResourceType.USER_MANUAL: self._extract_user_manual_content,
                ResourceType.TROUBLESHOOTING_GUIDE: self._extract_troubleshooting_guide_content,
                ResourceType.API_DOCUMENTATION: self._extract_api_documentation_content,
                ResourceType.WHITE_PAPER: self._extract_white_paper_content,
                ResourceType.CASE_STUDY: self._extract_case_study_content,
                ResourceType.WEBINAR: self._extract_webinar_content,
                ResourceType.TUTORIAL: self._extract_tutorial_content
            }
            
            # Initialize URL patterns for resource type detection
            self.url_patterns = {
                ResourceType.CODE_REPOSITORY: [
                    r'github\.com',
                    r'gitlab\.com',
                    r'bitbucket\.org',
                    r'sourceforge\.net'
                ],
                ResourceType.FORUM_POST: [
                    r'forum\.',
                    r'community\.',
                    r'discussion\.',
                    r'stackoverflow\.com',
                    r'reddit\.com'
                ],
                ResourceType.BLOG_POST: [
                    r'blog\.',
                    r'medium\.com',
                    r'wordpress\.com',
                    r'blogspot\.com'
                ],
                ResourceType.NEWS_ARTICLE: [
                    r'news\.',
                    r'article\.',
                    r'cnn\.com',
                    r'bbc\.com',
                    r'reuters\.com'
                ],
                ResourceType.TECHNICAL_DOCUMENT: [
                    r'docs\.',
                    r'documentation\.',
                    r'manual\.',
                    r'guide\.',
                    r'wiki\.'
                ],
                ResourceType.API_DOCUMENTATION: [
                    r'api\.',
                    r'developer\.',
                    r'dev\.',
                    r'reference\.'
                ],
                ResourceType.WHITE_PAPER: [
                    r'whitepaper\.',
                    r'white-paper\.',
                    r'research\.',
                    r'study\.'
                ],
                ResourceType.CASE_STUDY: [
                    r'case-study\.',
                    r'casestudy\.',
                    r'example\.',
                    r'success-story\.'
                ],
                ResourceType.WEBINAR: [
                    r'webinar\.',
                    r'event\.',
                    r'conference\.',
                    r'seminar\.'
                ],
                ResourceType.TUTORIAL: [
                    r'tutorial\.',
                    r'how-to\.',
                    r'guide\.',
                    r'learn\.'
                ]
            }
            
            logger.info("URL processing components initialized")
            
        except Exception as e:
            logger.error(f"Error initializing processing components: {e}")
            raise
    
    def submit_url(self, url: str, **kwargs) -> URLSubmission:
        """Submit a URL for processing"""
        try:
            # Generate submission ID
            submission_id = f"url_submission_{django_timezone.now().strftime('%Y%m%d_%H%M%S')}_{hash(url) % 10000}"
            
            # Create submission
            submission = URLSubmission(
                id=submission_id,
                url=url,
                title=kwargs.get('title'),
                description=kwargs.get('description'),
                resource_type=kwargs.get('resource_type'),
                category=kwargs.get('category'),
                tags=kwargs.get('tags', []),
                submitted_by=kwargs.get('submitted_by'),
                priority=kwargs.get('priority', 0),
                auto_process=kwargs.get('auto_process', True),
                requires_review=kwargs.get('requires_review', False)
            )
            
            # Store submission
            self.submissions[submission_id] = submission
            
            # Add to processing queue if auto-processing is enabled
            if submission.auto_process and self.auto_processing_enabled:
                self.processing_queue.append(submission_id)
                self._process_submission(submission_id)
            
            logger.info(f"URL submitted: {url} (ID: {submission_id})")
            return submission
            
        except Exception as e:
            logger.error(f"Error submitting URL: {e}")
            raise
    
    def validate_url(self, url: str) -> Tuple[URLValidationResult, Dict[str, Any]]:
        """Validate a URL"""
        try:
            validation_info = {
                'url': url,
                'is_valid_format': False,
                'is_reachable': False,
                'content_type': None,
                'content_size': 0,
                'redirect_count': 0,
                'response_time': 0,
                'final_url': url,
                'error_message': None
            }
            
            # Basic URL format validation
            try:
                self.url_validator(url)
                validation_info['is_valid_format'] = True
            except ValidationError as e:
                return URLValidationResult.INVALID_FORMAT, validation_info
            
            # Check for blocked domains
            parsed_url = urlparse(url)
            if any(blocked_domain in parsed_url.netloc.lower() for blocked_domain in self.validation_config.blocked_domains):
                validation_info['error_message'] = "Domain is blocked"
                return URLValidationResult.BLOCKED, validation_info
            
            # Check for blocked extensions
            if any(url.lower().endswith(ext) for ext in self.validation_config.blocked_extensions):
                validation_info['error_message'] = "File extension is blocked"
                return URLValidationResult.BLOCKED, validation_info
            
            # Check HTTPS requirement
            if self.validation_config.require_https and parsed_url.scheme != 'https':
                validation_info['error_message'] = "HTTPS is required"
                return URLValidationResult.BLOCKED, validation_info
            
            # Test URL reachability
            try:
                start_time = datetime.now()
                response = requests.head(
                    url,
                    timeout=self.validation_config.timeout,
                    allow_redirects=True,
                    headers={'User-Agent': self.validation_config.user_agent}
                )
                end_time = datetime.now()
                
                validation_info['response_time'] = (end_time - start_time).total_seconds()
                validation_info['is_reachable'] = True
                validation_info['content_type'] = response.headers.get('content-type', '').split(';')[0]
                validation_info['content_size'] = int(response.headers.get('content-length', 0))
                validation_info['final_url'] = response.url
                
                # Check content type
                if validation_info['content_type'] not in self.validation_config.allowed_content_types:
                    validation_info['error_message'] = f"Content type {validation_info['content_type']} not supported"
                    return URLValidationResult.CONTENT_TYPE_UNSUPPORTED, validation_info
                
                # Check content size
                if validation_info['content_size'] > self.validation_config.max_content_size:
                    validation_info['error_message'] = f"Content size {validation_info['content_size']} exceeds limit"
                    return URLValidationResult.CONTENT_TYPE_UNSUPPORTED, validation_info
                
                # Check for redirects
                if response.url != url:
                    validation_info['redirect_count'] = len(response.history)
                    return URLValidationResult.REDIRECT, validation_info
                
                return URLValidationResult.VALID, validation_info
                
            except requests.exceptions.Timeout:
                validation_info['error_message'] = "Request timeout"
                return URLValidationResult.TIMEOUT, validation_info
            except requests.exceptions.SSLError:
                validation_info['error_message'] = "SSL error"
                return URLValidationResult.SSL_ERROR, validation_info
            except requests.exceptions.ConnectionError:
                validation_info['error_message'] = "Connection error"
                return URLValidationResult.UNREACHABLE, validation_info
            except Exception as e:
                validation_info['error_message'] = str(e)
                return URLValidationResult.UNREACHABLE, validation_info
            
        except Exception as e:
            logger.error(f"Error validating URL: {e}")
            return URLValidationResult.INVALID_FORMAT, {'error_message': str(e)}
    
    def detect_resource_type(self, url: str, content_type: str = None) -> ResourceType:
        """Detect resource type from URL and content type"""
        try:
            # Check content type first
            if content_type:
                if 'pdf' in content_type.lower():
                    return ResourceType.PDF
                elif 'image' in content_type.lower():
                    return ResourceType.IMAGE
                elif 'video' in content_type.lower():
                    return ResourceType.VIDEO
                elif 'audio' in content_type.lower():
                    return ResourceType.AUDIO
                elif 'text/html' in content_type.lower():
                    return ResourceType.WEBPAGE
                elif 'application/msword' in content_type.lower() or 'application/vnd.openxmlformats-officedocument.wordprocessingml.document' in content_type.lower():
                    return ResourceType.DOCUMENT
                elif 'application/vnd.ms-powerpoint' in content_type.lower() or 'application/vnd.openxmlformats-officedocument.presentationml.presentation' in content_type.lower():
                    return ResourceType.PRESENTATION
                elif 'application/vnd.ms-excel' in content_type.lower() or 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet' in content_type.lower():
                    return ResourceType.SPREADSHEET
            
            # Check URL patterns
            url_lower = url.lower()
            for resource_type, patterns in self.url_patterns.items():
                for pattern in patterns:
                    if re.search(pattern, url_lower):
                        return resource_type
            
            # Check file extensions
            if url_lower.endswith('.pdf'):
                return ResourceType.PDF
            elif any(url_lower.endswith(ext) for ext in ['.jpg', '.jpeg', '.png', '.gif', '.bmp', '.svg']):
                return ResourceType.IMAGE
            elif any(url_lower.endswith(ext) for ext in ['.mp4', '.avi', '.mov', '.wmv', '.flv', '.webm']):
                return ResourceType.VIDEO
            elif any(url_lower.endswith(ext) for ext in ['.mp3', '.wav', '.flac', '.aac', '.ogg']):
                return ResourceType.AUDIO
            elif any(url_lower.endswith(ext) for ext in ['.doc', '.docx', '.rtf', '.txt']):
                return ResourceType.DOCUMENT
            elif any(url_lower.endswith(ext) for ext in ['.ppt', '.pptx']):
                return ResourceType.PRESENTATION
            elif any(url_lower.endswith(ext) for ext in ['.xls', '.xlsx', '.csv']):
                return ResourceType.SPREADSHEET
            
            # Default to webpage
            return ResourceType.WEBPAGE
            
        except Exception as e:
            logger.error(f"Error detecting resource type: {e}")
            return ResourceType.WEBPAGE
    
    def extract_content(self, submission: URLSubmission) -> ContentExtractionResult:
        """Extract content from URL submission"""
        try:
            # Determine resource type if not specified
            if not submission.resource_type:
                submission.resource_type = self.detect_resource_type(submission.url)
            
            # Get content extractor
            extractor = self.content_extractors.get(submission.resource_type)
            if not extractor:
                return ContentExtractionResult(
                    success=False,
                    error_message=f"No extractor available for resource type: {submission.resource_type.value}"
                )
            
            # Extract content
            result = extractor(submission.url)
            
            # Update submission with extracted content
            if result.success:
                submission.content_preview = result.content[:500] if result.content else None
                submission.metadata.update(result.metadata)
                submission.processing_log.append(f"Content extracted successfully using {result.extraction_method}")
            else:
                submission.processing_log.append(f"Content extraction failed: {result.error_message}")
            
            return result
            
        except Exception as e:
            logger.error(f"Error extracting content: {e}")
            return ContentExtractionResult(
                success=False,
                error_message=str(e)
            )
    
    def _extract_webpage_content(self, url: str) -> ContentExtractionResult:
        """Extract content from webpage"""
        try:
            response = requests.get(url, timeout=30, headers={'User-Agent': self.validation_config.user_agent})
            response.raise_for_status()
            
            # Simple HTML parsing (in production, use BeautifulSoup or similar)
            content = response.text
            
            # Extract title
            title_match = re.search(r'<title>(.*?)</title>', content, re.IGNORECASE | re.DOTALL)
            title = title_match.group(1).strip() if title_match else None
            
            # Extract text content (remove HTML tags)
            text_content = re.sub(r'<[^>]+>', ' ', content)
            text_content = re.sub(r'\s+', ' ', text_content).strip()
            
            # Extract images
            image_matches = re.findall(r'<img[^>]+src=["\']([^"\']+)["\']', content, re.IGNORECASE)
            images = [urljoin(url, img_url) for img_url in image_matches]
            
            # Extract links
            link_matches = re.findall(r'<a[^>]+href=["\']([^"\']+)["\']', content, re.IGNORECASE)
            links = [urljoin(url, link_url) for link_url in link_matches]
            
            # Calculate word count and reading time
            word_count = len(text_content.split())
            reading_time = max(1, word_count // 200)  # Assume 200 words per minute
            
            return ContentExtractionResult(
                success=True,
                title=title,
                content=text_content,
                metadata={
                    'url': url,
                    'content_type': response.headers.get('content-type', ''),
                    'content_length': len(content),
                    'status_code': response.status_code
                },
                images=images,
                links=links,
                word_count=word_count,
                reading_time=reading_time,
                extraction_method='webpage_extractor'
            )
            
        except Exception as e:
            return ContentExtractionResult(
                success=False,
                error_message=str(e)
            )
    
    def _extract_pdf_content(self, url: str) -> ContentExtractionResult:
        """Extract content from PDF"""
        try:
            # In production, use PyMuPDF or similar
            response = requests.get(url, timeout=30)
            response.raise_for_status()
            
            # For now, return basic info
            return ContentExtractionResult(
                success=True,
                title="PDF Document",
                content="PDF content extraction not implemented",
                metadata={
                    'url': url,
                    'content_type': 'application/pdf',
                    'content_length': len(response.content)
                },
                extraction_method='pdf_extractor'
            )
            
        except Exception as e:
            return ContentExtractionResult(
                success=False,
                error_message=str(e)
            )
    
    def _extract_document_content(self, url: str) -> ContentExtractionResult:
        """Extract content from document"""
        try:
            # In production, use python-docx or similar
            response = requests.get(url, timeout=30)
            response.raise_for_status()
            
            return ContentExtractionResult(
                success=True,
                title="Document",
                content="Document content extraction not implemented",
                metadata={
                    'url': url,
                    'content_type': response.headers.get('content-type', ''),
                    'content_length': len(response.content)
                },
                extraction_method='document_extractor'
            )
            
        except Exception as e:
            return ContentExtractionResult(
                success=False,
                error_message=str(e)
            )
    
    def _extract_video_content(self, url: str) -> ContentExtractionResult:
        """Extract content from video"""
        try:
            # In production, use video processing libraries
            return ContentExtractionResult(
                success=True,
                title="Video Content",
                content="Video content extraction not implemented",
                metadata={
                    'url': url,
                    'content_type': 'video'
                },
                extraction_method='video_extractor'
            )
            
        except Exception as e:
            return ContentExtractionResult(
                success=False,
                error_message=str(e)
            )
    
    def _extract_image_content(self, url: str) -> ContentExtractionResult:
        """Extract content from image"""
        try:
            # In production, use OCR libraries
            return ContentExtractionResult(
                success=True,
                title="Image Content",
                content="Image content extraction not implemented",
                metadata={
                    'url': url,
                    'content_type': 'image'
                },
                extraction_method='image_extractor'
            )
            
        except Exception as e:
            return ContentExtractionResult(
                success=False,
                error_message=str(e)
            )
    
    def _extract_audio_content(self, url: str) -> ContentExtractionResult:
        """Extract content from audio"""
        try:
            # In production, use audio processing libraries
            return ContentExtractionResult(
                success=True,
                title="Audio Content",
                content="Audio content extraction not implemented",
                metadata={
                    'url': url,
                    'content_type': 'audio'
                },
                extraction_method='audio_extractor'
            )
            
        except Exception as e:
            return ContentExtractionResult(
                success=False,
                error_message=str(e)
            )
    
    def _extract_presentation_content(self, url: str) -> ContentExtractionResult:
        """Extract content from presentation"""
        try:
            # In production, use presentation processing libraries
            return ContentExtractionResult(
                success=True,
                title="Presentation",
                content="Presentation content extraction not implemented",
                metadata={
                    'url': url,
                    'content_type': 'presentation'
                },
                extraction_method='presentation_extractor'
            )
            
        except Exception as e:
            return ContentExtractionResult(
                success=False,
                error_message=str(e)
            )
    
    def _extract_spreadsheet_content(self, url: str) -> ContentExtractionResult:
        """Extract content from spreadsheet"""
        try:
            # In production, use spreadsheet processing libraries
            return ContentExtractionResult(
                success=True,
                title="Spreadsheet",
                content="Spreadsheet content extraction not implemented",
                metadata={
                    'url': url,
                    'content_type': 'spreadsheet'
                },
                extraction_method='spreadsheet_extractor'
            )
            
        except Exception as e:
            return ContentExtractionResult(
                success=False,
                error_message=str(e)
            )
    
    def _extract_code_repository_content(self, url: str) -> ContentExtractionResult:
        """Extract content from code repository"""
        try:
            # In production, use Git APIs
            return ContentExtractionResult(
                success=True,
                title="Code Repository",
                content="Code repository content extraction not implemented",
                metadata={
                    'url': url,
                    'content_type': 'code_repository'
                },
                extraction_method='code_repository_extractor'
            )
            
        except Exception as e:
            return ContentExtractionResult(
                success=False,
                error_message=str(e)
            )
    
    def _extract_forum_post_content(self, url: str) -> ContentExtractionResult:
        """Extract content from forum post"""
        try:
            # Use webpage extractor for forum posts
            return self._extract_webpage_content(url)
            
        except Exception as e:
            return ContentExtractionResult(
                success=False,
                error_message=str(e)
            )
    
    def _extract_blog_post_content(self, url: str) -> ContentExtractionResult:
        """Extract content from blog post"""
        try:
            # Use webpage extractor for blog posts
            return self._extract_webpage_content(url)
            
        except Exception as e:
            return ContentExtractionResult(
                success=False,
                error_message=str(e)
            )
    
    def _extract_news_article_content(self, url: str) -> ContentExtractionResult:
        """Extract content from news article"""
        try:
            # Use webpage extractor for news articles
            return self._extract_webpage_content(url)
            
        except Exception as e:
            return ContentExtractionResult(
                success=False,
                error_message=str(e)
            )
    
    def _extract_technical_document_content(self, url: str) -> ContentExtractionResult:
        """Extract content from technical document"""
        try:
            # Use webpage extractor for technical documents
            return self._extract_webpage_content(url)
            
        except Exception as e:
            return ContentExtractionResult(
                success=False,
                error_message=str(e)
            )
    
    def _extract_user_manual_content(self, url: str) -> ContentExtractionResult:
        """Extract content from user manual"""
        try:
            # Use webpage extractor for user manuals
            return self._extract_webpage_content(url)
            
        except Exception as e:
            return ContentExtractionResult(
                success=False,
                error_message=str(e)
            )
    
    def _extract_troubleshooting_guide_content(self, url: str) -> ContentExtractionResult:
        """Extract content from troubleshooting guide"""
        try:
            # Use webpage extractor for troubleshooting guides
            return self._extract_webpage_content(url)
            
        except Exception as e:
            return ContentExtractionResult(
                success=False,
                error_message=str(e)
            )
    
    def _extract_api_documentation_content(self, url: str) -> ContentExtractionResult:
        """Extract content from API documentation"""
        try:
            # Use webpage extractor for API documentation
            return self._extract_webpage_content(url)
            
        except Exception as e:
            return ContentExtractionResult(
                success=False,
                error_message=str(e)
            )
    
    def _extract_white_paper_content(self, url: str) -> ContentExtractionResult:
        """Extract content from white paper"""
        try:
            # Use webpage extractor for white papers
            return self._extract_webpage_content(url)
            
        except Exception as e:
            return ContentExtractionResult(
                success=False,
                error_message=str(e)
            )
    
    def _extract_case_study_content(self, url: str) -> ContentExtractionResult:
        """Extract content from case study"""
        try:
            # Use webpage extractor for case studies
            return self._extract_webpage_content(url)
            
        except Exception as e:
            return ContentExtractionResult(
                success=False,
                error_message=str(e)
            )
    
    def _extract_webinar_content(self, url: str) -> ContentExtractionResult:
        """Extract content from webinar"""
        try:
            # Use webpage extractor for webinars
            return self._extract_webpage_content(url)
            
        except Exception as e:
            return ContentExtractionResult(
                success=False,
                error_message=str(e)
            )
    
    def _extract_tutorial_content(self, url: str) -> ContentExtractionResult:
        """Extract content from tutorial"""
        try:
            # Use webpage extractor for tutorials
            return self._extract_webpage_content(url)
            
        except Exception as e:
            return ContentExtractionResult(
                success=False,
                error_message=str(e)
            )
    
    def _process_submission(self, submission_id: str):
        """Process a URL submission"""
        try:
            submission = self.submissions.get(submission_id)
            if not submission:
                return
            
            # Update status
            submission.status = SubmissionStatus.PROCESSING
            submission.processing_started_at = django_timezone.now()
            
            # Validate URL
            if self.validation_enabled:
                validation_result, validation_info = self.validate_url(submission.url)
                submission.validation_result = validation_result
                submission.metadata.update(validation_info)
                
                if validation_result != URLValidationResult.VALID:
                    submission.status = SubmissionStatus.FAILED
                    submission.error_message = validation_info.get('error_message', 'URL validation failed')
                    submission.processing_completed_at = django_timezone.now()
                    return
            
            # Extract content
            if self.extraction_enabled:
                extraction_result = self.extract_content(submission)
                
                if extraction_result.success:
                    submission.status = SubmissionStatus.COMPLETED
                    submission.processing_log.append("Content extraction completed successfully")
                else:
                    submission.status = SubmissionStatus.FAILED
                    submission.error_message = extraction_result.error_message
                    submission.processing_log.append(f"Content extraction failed: {extraction_result.error_message}")
            
            submission.processing_completed_at = django_timezone.now()
            
            logger.info(f"Processed URL submission: {submission_id}")
            
        except Exception as e:
            logger.error(f"Error processing submission {submission_id}: {e}")
            submission = self.submissions.get(submission_id)
            if submission:
                submission.status = SubmissionStatus.PROCESSING_ERROR
                submission.error_message = str(e)
                submission.processing_completed_at = django_timezone.now()
    
    def get_submission(self, submission_id: str) -> Optional[URLSubmission]:
        """Get a submission by ID"""
        return self.submissions.get(submission_id)
    
    def get_submissions(self, status: SubmissionStatus = None, submitted_by: str = None) -> List[URLSubmission]:
        """Get submissions filtered by status and user"""
        try:
            submissions = list(self.submissions.values())
            
            if status:
                submissions = [s for s in submissions if s.status == status]
            
            if submitted_by:
                submissions = [s for s in submissions if s.submitted_by == submitted_by]
            
            return sorted(submissions, key=lambda x: x.submitted_at, reverse=True)
            
        except Exception as e:
            logger.error(f"Error getting submissions: {e}")
            return []
    
    def retry_submission(self, submission_id: str):
        """Retry a failed submission"""
        try:
            submission = self.get_submission(submission_id)
            if not submission:
                return
            
            if submission.retry_count >= submission.max_retries:
                submission.status = SubmissionStatus.FAILED
                submission.error_message = "Maximum retry attempts exceeded"
                return
            
            submission.retry_count += 1
            submission.status = SubmissionStatus.PENDING
            submission.error_message = None
            submission.processing_log.append(f"Retry attempt {submission.retry_count}")
            
            # Add to processing queue
            self.processing_queue.append(submission_id)
            self._process_submission(submission_id)
            
            logger.info(f"Retrying submission: {submission_id}")
            
        except Exception as e:
            logger.error(f"Error retrying submission: {e}")
    
    def delete_submission(self, submission_id: str):
        """Delete a submission"""
        try:
            if submission_id in self.submissions:
                del self.submissions[submission_id]
                logger.info(f"Deleted submission: {submission_id}")
            
        except Exception as e:
            logger.error(f"Error deleting submission: {e}")
    
    def get_submission_statistics(self) -> Dict[str, Any]:
        """Get submission statistics"""
        try:
            stats = {
                'total_submissions': len(self.submissions),
                'submissions_by_status': {},
                'submissions_by_type': {},
                'submissions_by_user': {},
                'processing_queue_size': len(self.processing_queue),
                'failed_submissions_count': len(self.failed_submissions),
                'average_processing_time': 0,
                'success_rate': 0
            }
            
            # Count by status
            for submission in self.submissions.values():
                status = submission.status.value
                stats['submissions_by_status'][status] = stats['submissions_by_status'].get(status, 0) + 1
                
                # Count by type
                if submission.resource_type:
                    resource_type = submission.resource_type.value
                    stats['submissions_by_type'][resource_type] = stats['submissions_by_type'].get(resource_type, 0) + 1
                
                # Count by user
                if submission.submitted_by:
                    stats['submissions_by_user'][submission.submitted_by] = stats['submissions_by_user'].get(submission.submitted_by, 0) + 1
            
            # Calculate success rate
            completed_count = stats['submissions_by_status'].get(SubmissionStatus.COMPLETED.value, 0)
            if stats['total_submissions'] > 0:
                stats['success_rate'] = (completed_count / stats['total_submissions']) * 100
            
            return stats
            
        except Exception as e:
            logger.error(f"Error getting submission statistics: {e}")
            return {}
    
    def bulk_submit_urls(self, urls: List[str], **kwargs) -> List[URLSubmission]:
        """Bulk submit multiple URLs"""
        try:
            submissions = []
            
            for url in urls:
                submission = self.submit_url(url, **kwargs)
                submissions.append(submission)
            
            logger.info(f"Bulk submitted {len(urls)} URLs")
            return submissions
            
        except Exception as e:
            logger.error(f"Error bulk submitting URLs: {e}")
            return []
    
    def export_submissions(self, submission_ids: List[str] = None) -> List[Dict[str, Any]]:
        """Export submissions data"""
        try:
            if submission_ids:
                submissions = [self.submissions.get(sid) for sid in submission_ids if sid in self.submissions]
            else:
                submissions = list(self.submissions.values())
            
            export_data = []
            for submission in submissions:
                if submission:
                    export_data.append({
                        'id': submission.id,
                        'url': submission.url,
                        'title': submission.title,
                        'description': submission.description,
                        'resource_type': submission.resource_type.value if submission.resource_type else None,
                        'category': submission.category,
                        'tags': submission.tags,
                        'submitted_by': submission.submitted_by,
                        'submitted_at': submission.submitted_at.isoformat(),
                        'status': submission.status.value,
                        'validation_result': submission.validation_result.value if submission.validation_result else None,
                        'content_preview': submission.content_preview,
                        'metadata': submission.metadata,
                        'processing_log': submission.processing_log,
                        'error_message': submission.error_message,
                        'retry_count': submission.retry_count,
                        'priority': submission.priority,
                        'auto_process': submission.auto_process,
                        'requires_review': submission.requires_review,
                        'review_status': submission.review_status,
                        'reviewed_by': submission.reviewed_by,
                        'reviewed_at': submission.reviewed_at.isoformat() if submission.reviewed_at else None,
                        'processing_started_at': submission.processing_started_at.isoformat() if submission.processing_started_at else None,
                        'processing_completed_at': submission.processing_completed_at.isoformat() if submission.processing_completed_at else None
                    })
            
            return export_data
            
        except Exception as e:
            logger.error(f"Error exporting submissions: {e}")
            return []
    
    def import_submissions(self, submissions_data: List[Dict[str, Any]]):
        """Import submissions data"""
        try:
            for submission_data in submissions_data:
                submission = URLSubmission(
                    id=submission_data['id'],
                    url=submission_data['url'],
                    title=submission_data.get('title'),
                    description=submission_data.get('description'),
                    resource_type=ResourceType(submission_data['resource_type']) if submission_data.get('resource_type') else None,
                    category=submission_data.get('category'),
                    tags=submission_data.get('tags', []),
                    submitted_by=submission_data.get('submitted_by'),
                    submitted_at=datetime.fromisoformat(submission_data['submitted_at']),
                    status=SubmissionStatus(submission_data['status']),
                    validation_result=URLValidationResult(submission_data['validation_result']) if submission_data.get('validation_result') else None,
                    content_preview=submission_data.get('content_preview'),
                    metadata=submission_data.get('metadata', {}),
                    processing_log=submission_data.get('processing_log', []),
                    error_message=submission_data.get('error_message'),
                    retry_count=submission_data.get('retry_count', 0),
                    priority=submission_data.get('priority', 0),
                    auto_process=submission_data.get('auto_process', True),
                    requires_review=submission_data.get('requires_review', False),
                    review_status=submission_data.get('review_status'),
                    reviewed_by=submission_data.get('reviewed_by'),
                    reviewed_at=datetime.fromisoformat(submission_data['reviewed_at']) if submission_data.get('reviewed_at') else None,
                    processing_started_at=datetime.fromisoformat(submission_data['processing_started_at']) if submission_data.get('processing_started_at') else None,
                    processing_completed_at=datetime.fromisoformat(submission_data['processing_completed_at']) if submission_data.get('processing_completed_at') else None
                )
                
                self.submissions[submission.id] = submission
            
            logger.info(f"Imported {len(submissions_data)} submissions")
            
        except Exception as e:
            logger.error(f"Error importing submissions: {e}")
            raise
    
    def cleanup_old_submissions(self, days_old: int = 30):
        """Clean up old submissions"""
        try:
            cutoff_date = django_timezone.now() - timedelta(days=days_old)
            old_submissions = [
                sid for sid, submission in self.submissions.items()
                if submission.submitted_at < cutoff_date
            ]
            
            for submission_id in old_submissions:
                del self.submissions[submission_id]
            
            logger.info(f"Cleaned up {len(old_submissions)} old submissions")
            
        except Exception as e:
            logger.error(f"Error cleaning up old submissions: {e}")
    
    def get_processing_queue_status(self) -> Dict[str, Any]:
        """Get processing queue status"""
        try:
            return {
                'queue_size': len(self.processing_queue),
                'failed_count': len(self.failed_submissions),
                'processing_count': len([
                    s for s in self.submissions.values()
                    if s.status == SubmissionStatus.PROCESSING
                ]),
                'pending_count': len([
                    s for s in self.submissions.values()
                    if s.status == SubmissionStatus.PENDING
                ]),
                'completed_count': len([
                    s for s in self.submissions.values()
                    if s.status == SubmissionStatus.COMPLETED
                ])
            }
            
        except Exception as e:
            logger.error(f"Error getting processing queue status: {e}")
            return {}
    
    def pause_processing(self):
        """Pause URL processing"""
        self.auto_processing_enabled = False
        logger.info("URL processing paused")
    
    def resume_processing(self):
        """Resume URL processing"""
        self.auto_processing_enabled = True
        logger.info("URL processing resumed")
    
    def update_validation_config(self, config: Dict[str, Any]):
        """Update URL validation configuration"""
        try:
            for key, value in config.items():
                if hasattr(self.validation_config, key):
                    setattr(self.validation_config, key, value)
            
            logger.info("URL validation configuration updated")
            
        except Exception as e:
            logger.error(f"Error updating validation configuration: {e}")
    
    def get_validation_config(self) -> Dict[str, Any]:
        """Get URL validation configuration"""
        try:
            return {
                'timeout': self.validation_config.timeout,
                'max_redirects': self.validation_config.max_redirects,
                'user_agent': self.validation_config.user_agent,
                'allowed_content_types': self.validation_config.allowed_content_types,
                'blocked_domains': self.validation_config.blocked_domains,
                'blocked_extensions': self.validation_config.blocked_extensions,
                'require_https': self.validation_config.require_https,
                'max_content_size': self.validation_config.max_content_size
            }
            
        except Exception as e:
            logger.error(f"Error getting validation configuration: {e}")
            return {}
