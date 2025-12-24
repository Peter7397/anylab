"""
HTML Parsing System for AnyLab

This module provides comprehensive HTML parsing capabilities for extracting
structured content from web pages, including text, metadata, links, and
semantic information for RAG integration.
"""

import requests
import json
import logging
import time
import re
from typing import Dict, List, Optional, Any, Tuple
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from urllib.parse import urljoin, urlparse, parse_qs
from bs4 import BeautifulSoup, Comment
import hashlib
from django.conf import settings
from django.core.cache import cache
from django.utils import timezone

from .metadata_schema import OrganizationMode, DocumentType, SeverityLevel, DualModeMetadata
from .models import DocumentFile, DocumentChunk, UploadedFile

logger = logging.getLogger(__name__)


@dataclass
class HTMLContent:
    """HTML content data structure"""
    url: str
    title: str
    description: str
    content: str
    clean_content: str
    metadata: Dict[str, Any]
    links: List[Dict[str, str]]
    images: List[Dict[str, str]]
    tables: List[Dict[str, Any]]
    headings: List[Dict[str, str]]
    paragraphs: List[str]
    lists: List[Dict[str, Any]]
    code_blocks: List[str]
    forms: List[Dict[str, Any]]
    scripts: List[str]
    styles: List[str]
    language: str
    encoding: str
    content_type: str
    file_size: int
    last_modified: datetime
    scraped_at: datetime
    quality_score: float
    relevance_score: float
    processing_metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class HTMLParsingConfig:
    """Configuration for HTML parsing"""
    timeout: int = 30
    retry_attempts: int = 3
    user_agent: str = "AnyLab-HTML-Parser/1.0"
    cache_duration: int = 3600  # 1 hour
    min_content_length: int = 100
    max_content_length: int = 1000000  # 1MB
    extract_images: bool = True
    extract_tables: bool = True
    extract_forms: bool = True
    extract_code: bool = True
    extract_links: bool = True
    clean_html: bool = True
    remove_scripts: bool = True
    remove_styles: bool = True
    remove_comments: bool = True
    preserve_structure: bool = True
    language_detection: bool = True
    content_classification: bool = True


class HTMLParser:
    """Main HTML parser class"""
    
    def __init__(self, config: Optional[HTMLParsingConfig] = None):
        self.config = config or HTMLParsingConfig()
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': self.config.user_agent,
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
            'Accept-Language': 'en-US,en;q=0.5',
            'Accept-Encoding': 'gzip, deflate',
            'Connection': 'keep-alive',
        })
        
    def parse_url(self, url: str) -> Optional[HTMLContent]:
        """Parse HTML content from a URL"""
        try:
            # Check cache first
            cache_key = f"html_content_{hashlib.md5(url.encode()).hexdigest()}"
            cached_content = cache.get(cache_key)
            
            if cached_content:
                logger.info(f"Using cached HTML content for {url}")
                return HTMLContent(**cached_content)
            
            # Fetch HTML content
            html_text = self._fetch_html(url)
            if not html_text:
                logger.error(f"Failed to fetch HTML content from {url}")
                return None
            
            # Parse HTML
            html_content = self._parse_html(html_text, url)
            if not html_content:
                logger.error(f"Failed to parse HTML content from {url}")
                return None
            
            # Cache the content
            cache.set(cache_key, html_content.__dict__, self.config.cache_duration)
            
            return html_content
            
        except Exception as e:
            logger.error(f"Error parsing HTML from {url}: {e}")
            return None
    
    def parse_html_text(self, html_text: str, url: str = "") -> Optional[HTMLContent]:
        """Parse HTML content from text"""
        try:
            return self._parse_html(html_text, url)
        except Exception as e:
            logger.error(f"Error parsing HTML text: {e}")
            return None
    
    def _fetch_html(self, url: str) -> Optional[str]:
        """Fetch HTML content from URL"""
        for attempt in range(self.config.retry_attempts):
            try:
                response = self.session.get(url, timeout=self.config.timeout)
                response.raise_for_status()
                
                # Check content type
                content_type = response.headers.get('content-type', '').lower()
                if 'text/html' not in content_type:
                    logger.warning(f"Content type is not HTML: {content_type}")
                    return None
                
                return response.text
                
            except requests.exceptions.RequestException as e:
                logger.warning(f"Attempt {attempt + 1} failed for {url}: {e}")
                if attempt < self.config.retry_attempts - 1:
                    time.sleep(2 ** attempt)  # Exponential backoff
                else:
                    logger.error(f"All attempts failed for {url}")
                    return None
        
        return None
    
    def _parse_html(self, html_text: str, url: str) -> Optional[HTMLContent]:
        """Parse HTML content"""
        try:
            soup = BeautifulSoup(html_text, 'html.parser')
            
            # Extract basic information
            title = self._extract_title(soup)
            description = self._extract_description(soup)
            
            # Clean HTML if requested
            if self.config.clean_html:
                soup = self._clean_html(soup)
            
            # Extract content
            content = self._extract_content(soup)
            clean_content = self._extract_clean_content(soup)
            
            # Check content length
            if len(clean_content) < self.config.min_content_length:
                logger.warning(f"Content too short: {len(clean_content)} characters")
                return None
            
            if len(clean_content) > self.config.max_content_length:
                logger.warning(f"Content too long: {len(clean_content)} characters")
                clean_content = clean_content[:self.config.max_content_length]
            
            # Extract metadata
            metadata = self._extract_metadata(soup, url)
            
            # Extract structured content
            links = self._extract_links(soup, url) if self.config.extract_links else []
            images = self._extract_images(soup, url) if self.config.extract_images else []
            tables = self._extract_tables(soup) if self.config.extract_tables else []
            headings = self._extract_headings(soup)
            paragraphs = self._extract_paragraphs(soup)
            lists = self._extract_lists(soup)
            code_blocks = self._extract_code_blocks(soup) if self.config.extract_code else []
            forms = self._extract_forms(soup) if self.config.extract_forms else []
            scripts = self._extract_scripts(soup) if not self.config.remove_scripts else []
            styles = self._extract_styles(soup) if not self.config.remove_styles else []
            
            # Detect language
            language = self._detect_language(soup, clean_content) if self.config.language_detection else 'en'
            
            # Detect encoding
            encoding = self._detect_encoding(html_text)
            
            # Detect content type
            content_type = self._detect_content_type(soup)
            
            # Calculate quality and relevance scores
            quality_score = self._calculate_quality_score(soup, clean_content)
            relevance_score = self._calculate_relevance_score(clean_content, url)
            
            # Build processing metadata
            processing_metadata = {
                'parser_version': '1.0',
                'parsing_time': timezone.now().isoformat(),
                'content_length': len(clean_content),
                'original_length': len(html_text),
                'compression_ratio': len(clean_content) / len(html_text) if len(html_text) > 0 else 0,
                'structure_preserved': self.config.preserve_structure,
                'elements_extracted': {
                    'links': len(links),
                    'images': len(images),
                    'tables': len(tables),
                    'headings': len(headings),
                    'paragraphs': len(paragraphs),
                    'lists': len(lists),
                    'code_blocks': len(code_blocks),
                    'forms': len(forms)
                }
            }
            
            return HTMLContent(
                url=url,
                title=title,
                description=description,
                content=content,
                clean_content=clean_content,
                metadata=metadata,
                links=links,
                images=images,
                tables=tables,
                headings=headings,
                paragraphs=paragraphs,
                lists=lists,
                code_blocks=code_blocks,
                forms=forms,
                scripts=scripts,
                styles=styles,
                language=language,
                encoding=encoding,
                content_type=content_type,
                file_size=len(html_text),
                last_modified=timezone.now(),
                scraped_at=timezone.now(),
                quality_score=quality_score,
                relevance_score=relevance_score,
                processing_metadata=processing_metadata
            )
            
        except Exception as e:
            logger.error(f"Error parsing HTML: {e}")
            return None
    
    def _extract_title(self, soup: BeautifulSoup) -> str:
        """Extract page title"""
        title_selectors = [
            'title',
            'h1',
            '.title',
            '.page-title',
            '.main-title'
        ]
        
        for selector in title_selectors:
            title_elem = soup.select_one(selector)
            if title_elem:
                title = title_elem.get_text().strip()
                if title and len(title) > 5:
                    return title
        
        return "Untitled Page"
    
    def _extract_description(self, soup: BeautifulSoup) -> str:
        """Extract page description"""
        # Try meta description first
        meta_desc = soup.find('meta', attrs={'name': 'description'})
        if meta_desc and meta_desc.get('content'):
            return meta_desc['content'].strip()
        
        # Try Open Graph description
        og_desc = soup.find('meta', property='og:description')
        if og_desc and og_desc.get('content'):
            return og_desc['content'].strip()
        
        # Try Twitter description
        twitter_desc = soup.find('meta', attrs={'name': 'twitter:description'})
        if twitter_desc and twitter_desc.get('content'):
            return twitter_desc['content'].strip()
        
        # Fallback to first paragraph
        first_p = soup.find('p')
        if first_p:
            desc = first_p.get_text().strip()
            if desc and len(desc) > 20:
                return desc[:200] + "..." if len(desc) > 200 else desc
        
        return ""
    
    def _extract_content(self, soup: BeautifulSoup) -> str:
        """Extract raw content"""
        # Remove script and style elements
        for script in soup(["script", "style"]):
            script.decompose()
        
        return soup.get_text()
    
    def _extract_clean_content(self, soup: BeautifulSoup) -> str:
        """Extract clean, structured content"""
        # Remove unwanted elements
        for element in soup(["script", "style", "nav", "header", "footer", "aside"]):
            element.decompose()
        
        # Extract main content
        main_content = soup.find('main') or soup.find('article') or soup.find('div', class_='content')
        if main_content:
            return main_content.get_text(separator='\n', strip=True)
        
        # Fallback to body content
        body = soup.find('body')
        if body:
            return body.get_text(separator='\n', strip=True)
        
        return soup.get_text(separator='\n', strip=True)
    
    def _extract_metadata(self, soup: BeautifulSoup, url: str) -> Dict[str, Any]:
        """Extract metadata from HTML"""
        metadata = {
            'url': url,
            'domain': urlparse(url).netloc,
            'path': urlparse(url).path,
            'query': urlparse(url).query,
            'fragment': urlparse(url).fragment
        }
        
        # Meta tags
        meta_tags = soup.find_all('meta')
        for meta in meta_tags:
            name = meta.get('name') or meta.get('property')
            content = meta.get('content')
            if name and content:
                metadata[f'meta_{name}'] = content
        
        # Open Graph tags
        og_tags = soup.find_all('meta', property=re.compile(r'^og:'))
        for og in og_tags:
            property_name = og.get('property')
            content = og.get('content')
            if property_name and content:
                metadata[property_name] = content
        
        # Twitter Card tags
        twitter_tags = soup.find_all('meta', attrs={'name': re.compile(r'^twitter:')})
        for twitter in twitter_tags:
            name = twitter.get('name')
            content = twitter.get('content')
            if name and content:
                metadata[name] = content
        
        # Structured data (JSON-LD)
        json_ld_scripts = soup.find_all('script', type='application/ld+json')
        for script in json_ld_scripts:
            try:
                json_data = json.loads(script.string)
                metadata['structured_data'] = json_data
            except (json.JSONDecodeError, TypeError):
                continue
        
        # Microdata
        microdata_items = soup.find_all(attrs={'itemscope': True})
        if microdata_items:
            metadata['has_microdata'] = True
        
        # RDFa
        rdfa_items = soup.find_all(attrs={'typeof': True})
        if rdfa_items:
            metadata['has_rdfa'] = True
        
        return metadata
    
    def _extract_links(self, soup: BeautifulSoup, base_url: str) -> List[Dict[str, str]]:
        """Extract links from HTML"""
        links = []
        
        for link in soup.find_all('a', href=True):
            href = link['href']
            text = link.get_text().strip()
            
            # Convert relative URLs to absolute
            if href.startswith('/'):
                href = urljoin(base_url, href)
            elif not href.startswith('http'):
                href = urljoin(base_url, href)
            
            # Skip invalid URLs
            if not href or href.startswith('javascript:') or href.startswith('mailto:'):
                continue
            
            links.append({
                'url': href,
                'text': text,
                'title': link.get('title', ''),
                'rel': link.get('rel', ''),
                'target': link.get('target', '')
            })
        
        return links
    
    def _extract_images(self, soup: BeautifulSoup, base_url: str) -> List[Dict[str, str]]:
        """Extract images from HTML"""
        images = []
        
        for img in soup.find_all('img', src=True):
            src = img['src']
            alt = img.get('alt', '')
            title = img.get('title', '')
            
            # Convert relative URLs to absolute
            if src.startswith('/'):
                src = urljoin(base_url, src)
            elif not src.startswith('http'):
                src = urljoin(base_url, src)
            
            # Skip invalid URLs
            if not src or src.startswith('data:'):
                continue
            
            images.append({
                'src': src,
                'alt': alt,
                'title': title,
                'width': img.get('width', ''),
                'height': img.get('height', ''),
                'loading': img.get('loading', '')
            })
        
        return images
    
    def _extract_tables(self, soup: BeautifulSoup) -> List[Dict[str, Any]]:
        """Extract tables from HTML"""
        tables = []
        
        for table in soup.find_all('table'):
            table_data = {
                'caption': '',
                'headers': [],
                'rows': [],
                'summary': table.get('summary', '')
            }
            
            # Extract caption
            caption = table.find('caption')
            if caption:
                table_data['caption'] = caption.get_text().strip()
            
            # Extract headers
            headers = table.find_all('th')
            if headers:
                table_data['headers'] = [th.get_text().strip() for th in headers]
            
            # Extract rows
            rows = table.find_all('tr')
            for row in rows:
                cells = row.find_all(['td', 'th'])
                if cells:
                    row_data = [cell.get_text().strip() for cell in cells]
                    table_data['rows'].append(row_data)
            
            if table_data['rows']:
                tables.append(table_data)
        
        return tables
    
    def _extract_headings(self, soup: BeautifulSoup) -> List[Dict[str, str]]:
        """Extract headings from HTML"""
        headings = []
        
        for i in range(1, 7):  # h1 to h6
            for heading in soup.find_all(f'h{i}'):
                text = heading.get_text().strip()
                if text:
                    headings.append({
                        'level': i,
                        'text': text,
                        'id': heading.get('id', ''),
                        'class': ' '.join(heading.get('class', []))
                    })
        
        return headings
    
    def _extract_paragraphs(self, soup: BeautifulSoup) -> List[str]:
        """Extract paragraphs from HTML"""
        paragraphs = []
        
        for p in soup.find_all('p'):
            text = p.get_text().strip()
            if text and len(text) > 10:  # Filter out very short paragraphs
                paragraphs.append(text)
        
        return paragraphs
    
    def _extract_lists(self, soup: BeautifulSoup) -> List[Dict[str, Any]]:
        """Extract lists from HTML"""
        lists = []
        
        for list_elem in soup.find_all(['ul', 'ol']):
            list_type = list_elem.name
            items = []
            
            for li in list_elem.find_all('li'):
                text = li.get_text().strip()
                if text:
                    items.append(text)
            
            if items:
                lists.append({
                    'type': list_type,
                    'items': items,
                    'class': ' '.join(list_elem.get('class', []))
                })
        
        return lists
    
    def _extract_code_blocks(self, soup: BeautifulSoup) -> List[str]:
        """Extract code blocks from HTML"""
        code_blocks = []
        
        # Extract <pre> and <code> elements
        for code_elem in soup.find_all(['pre', 'code']):
            text = code_elem.get_text().strip()
            if text and len(text) > 10:  # Filter out very short code blocks
                code_blocks.append(text)
        
        return code_blocks
    
    def _extract_forms(self, soup: BeautifulSoup) -> List[Dict[str, Any]]:
        """Extract forms from HTML"""
        forms = []
        
        for form in soup.find_all('form'):
            form_data = {
                'action': form.get('action', ''),
                'method': form.get('method', 'get'),
                'fields': []
            }
            
            # Extract form fields
            for field in form.find_all(['input', 'textarea', 'select']):
                field_data = {
                    'type': field.get('type', field.name),
                    'name': field.get('name', ''),
                    'id': field.get('id', ''),
                    'placeholder': field.get('placeholder', ''),
                    'required': field.has_attr('required')
                }
                
                if field.name == 'select':
                    options = []
                    for option in field.find_all('option'):
                        options.append({
                            'value': option.get('value', ''),
                            'text': option.get_text().strip()
                        })
                    field_data['options'] = options
                
                form_data['fields'].append(field_data)
            
            if form_data['fields']:
                forms.append(form_data)
        
        return forms
    
    def _extract_scripts(self, soup: BeautifulSoup) -> List[str]:
        """Extract scripts from HTML"""
        scripts = []
        
        for script in soup.find_all('script'):
            if script.string:
                scripts.append(script.string.strip())
        
        return scripts
    
    def _extract_styles(self, soup: BeautifulSoup) -> List[str]:
        """Extract styles from HTML"""
        styles = []
        
        for style in soup.find_all('style'):
            if style.string:
                styles.append(style.string.strip())
        
        return styles
    
    def _detect_language(self, soup: BeautifulSoup, content: str) -> str:
        """Detect page language"""
        # Try HTML lang attribute
        html_elem = soup.find('html')
        if html_elem and html_elem.get('lang'):
            return html_elem['lang'].split('-')[0]  # Get primary language
        
        # Try meta language
        meta_lang = soup.find('meta', attrs={'http-equiv': 'content-language'})
        if meta_lang and meta_lang.get('content'):
            return meta_lang['content'].split('-')[0]
        
        # Try meta charset
        meta_charset = soup.find('meta', attrs={'charset': True})
        if meta_charset:
            charset = meta_charset.get('charset', '').lower()
            if 'utf-8' in charset:
                return 'en'  # Default to English for UTF-8
        
        # Simple language detection based on content
        # This is a basic implementation - in production, you'd use a proper language detection library
        english_words = ['the', 'and', 'or', 'but', 'in', 'on', 'at', 'to', 'for', 'of', 'with', 'by']
        content_lower = content.lower()
        english_count = sum(1 for word in english_words if word in content_lower)
        
        if english_count > 5:
            return 'en'
        
        return 'en'  # Default to English
    
    def _detect_encoding(self, html_text: str) -> str:
        """Detect HTML encoding"""
        # Try to find charset in meta tag
        charset_match = re.search(r'charset=["\']?([^"\'>\s]+)', html_text, re.IGNORECASE)
        if charset_match:
            return charset_match.group(1).lower()
        
        # Try to find charset in content-type header
        content_type_match = re.search(r'content-type:\s*text/html;\s*charset=([^;\s]+)', html_text, re.IGNORECASE)
        if content_type_match:
            return content_type_match.group(1).lower()
        
        return 'utf-8'  # Default to UTF-8
    
    def _detect_content_type(self, soup: BeautifulSoup) -> str:
        """Detect content type"""
        # Check for specific content indicators
        if soup.find('article'):
            return 'article'
        elif soup.find('main'):
            return 'main_content'
        elif soup.find('form'):
            return 'form'
        elif soup.find('table'):
            return 'data_table'
        elif soup.find('nav'):
            return 'navigation'
        else:
            return 'general'
    
    def _calculate_quality_score(self, soup: BeautifulSoup, content: str) -> float:
        """Calculate content quality score"""
        score = 0.0
        
        # Content length score
        if len(content) > 500:
            score += 0.2
        elif len(content) > 200:
            score += 0.1
        
        # Structure score
        if soup.find('h1'):
            score += 0.1
        if soup.find('h2'):
            score += 0.1
        if soup.find('p'):
            score += 0.1
        
        # Meta information score
        if soup.find('meta', attrs={'name': 'description'}):
            score += 0.1
        if soup.find('meta', attrs={'name': 'keywords'}):
            score += 0.1
        
        # Content quality indicators
        if soup.find('article'):
            score += 0.1
        if soup.find('main'):
            score += 0.1
        
        # Avoid low-quality indicators
        if soup.find('script'):  # Too many scripts might indicate low content quality
            score -= 0.1
        
        return min(max(score, 0.0), 1.0)
    
    def _calculate_relevance_score(self, content: str, url: str) -> float:
        """Calculate content relevance score"""
        score = 0.0
        
        # URL relevance
        url_lower = url.lower()
        if any(keyword in url_lower for keyword in ['agilent', 'openlab', 'masshunter', 'chemstation', 'vnmrj']):
            score += 0.3
        
        # Content relevance
        content_lower = content.lower()
        relevant_keywords = [
            'agilent', 'openlab', 'masshunter', 'chemstation', 'vnmrj',
            'chromatography', 'mass spectrometry', 'nmr', 'spectroscopy',
            'laboratory', 'instrument', 'software', 'troubleshooting',
            'manual', 'guide', 'documentation', 'support'
        ]
        
        keyword_count = sum(1 for keyword in relevant_keywords if keyword in content_lower)
        score += min(keyword_count * 0.05, 0.4)
        
        return min(score, 1.0)
    
    def _clean_html(self, soup: BeautifulSoup) -> BeautifulSoup:
        """Clean HTML content"""
        # Remove comments
        if self.config.remove_comments:
            comments = soup.find_all(string=lambda text: isinstance(text, Comment))
            for comment in comments:
                comment.extract()
        
        # Remove scripts
        if self.config.remove_scripts:
            for script in soup.find_all('script'):
                script.decompose()
        
        # Remove styles
        if self.config.remove_styles:
            for style in soup.find_all('style'):
                style.decompose()
        
        # Remove unwanted elements
        unwanted_tags = ['nav', 'header', 'footer', 'aside', 'advertisement', 'ads']
        for tag in unwanted_tags:
            for element in soup.find_all(tag):
                element.decompose()
        
        return soup


class HTMLProcessor:
    """Process parsed HTML content and integrate with document management system"""
    
    def __init__(self):
        self.rag_service = None  # Will be initialized when needed
    
    def process_html_content(self, html_content: HTMLContent) -> Dict[str, Any]:
        """Process HTML content and create document entries"""
        logger.info(f"Processing HTML content from {html_content.url}")
        
        try:
            # Check if this content already exists
            existing_doc = self._find_existing_document(html_content.url)
            
            if existing_doc:
                # Update existing document
                self._update_document(existing_doc, html_content)
                return {'status': 'updated', 'document_id': existing_doc.id}
            else:
                # Create new document
                document = self._create_document(html_content)
                return {'status': 'created', 'document_id': document.id}
                
        except Exception as e:
            logger.error(f"Error processing HTML content from {html_content.url}: {e}")
            return {'status': 'error', 'error': str(e)}
    
    def _find_existing_document(self, url: str) -> Optional[DocumentFile]:
        """Find existing document by URL"""
        try:
            # Look for documents with this URL in metadata
            documents = DocumentFile.objects.filter(
                metadata__icontains=f'"url": "{url}"'
            )
            return documents.first()
        except Exception as e:
            logger.error(f"Error finding existing document for {url}: {e}")
            return None
    
    def _create_document(self, html_content: HTMLContent) -> DocumentFile:
        """Create a new document from HTML content"""
        try:
            # Create metadata
            metadata = {
                'url': html_content.url,
                'domain': html_content.metadata.get('domain', ''),
                'title': html_content.title,
                'description': html_content.description,
                'language': html_content.language,
                'encoding': html_content.encoding,
                'content_type': html_content.content_type,
                'file_size': html_content.file_size,
                'last_modified': html_content.last_modified.isoformat(),
                'scraped_at': html_content.scraped_at.isoformat(),
                'document_type': 'HTML_PAGE',
                'organization_mode': 'lab-informatics',
                'content_category': 'web_content',
                'quality_score': html_content.quality_score,
                'relevance_score': html_content.relevance_score,
                'processing_metadata': html_content.processing_metadata,
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
                'search_tags': self._generate_search_tags(html_content),
                'keywords': self._extract_keywords(html_content)
            }
            
            # Create document file
            document = DocumentFile.objects.create(
                title=html_content.title,
                filename=f"HTML_{hashlib.md5(html_content.url.encode()).hexdigest()[:8]}.html",
                file_type="HTML",
                file_size=html_content.file_size,
                description=html_content.description,
                document_type="HTML_PAGE",
                metadata=json.dumps(metadata),
                uploaded_by=None,  # System upload
                page_count=1,
                created_at=html_content.scraped_at,
                updated_at=html_content.last_modified
            )
            
            # Create content chunks for RAG
            self._create_content_chunks(document, html_content)
            
            logger.info(f"Created document for HTML content from {html_content.url}")
            return document
            
        except Exception as e:
            logger.error(f"Error creating document for HTML content from {html_content.url}: {e}")
            raise
    
    def _update_document(self, document: DocumentFile, html_content: HTMLContent):
        """Update existing document with new HTML content"""
        try:
            # Update document fields
            document.title = html_content.title
            document.description = html_content.description
            document.updated_at = html_content.last_modified
            
            # Update metadata
            metadata = json.loads(document.metadata) if document.metadata else {}
            metadata.update({
                'url': html_content.url,
                'title': html_content.title,
                'description': html_content.description,
                'last_modified': html_content.last_modified.isoformat(),
                'scraped_at': html_content.scraped_at.isoformat(),
                'quality_score': html_content.quality_score,
                'relevance_score': html_content.relevance_score,
                'processing_metadata': html_content.processing_metadata,
                'extracted_elements': {
                    'links_count': len(html_content.links),
                    'images_count': len(html_content.images),
                    'tables_count': len(html_content.tables),
                    'headings_count': len(html_content.headings),
                    'paragraphs_count': len(html_content.paragraphs),
                    'lists_count': len(html_content.lists),
                    'code_blocks_count': len(html_content.code_blocks),
                    'forms_count': len(html_content.forms)
                }
            })
            
            document.metadata = json.dumps(metadata)
            document.save()
            
            # Update content chunks
            self._update_content_chunks(document, html_content)
            
            logger.info(f"Updated document for HTML content from {html_content.url}")
            
        except Exception as e:
            logger.error(f"Error updating document for HTML content from {html_content.url}: {e}")
            raise
    
    def _create_content_chunks(self, document: DocumentFile, html_content: HTMLContent):
        """Create content chunks for RAG indexing"""
        try:
            # Create chunks for different sections
            chunks_data = [
                {
                    'content': f"Title: {html_content.title}\nDescription: {html_content.description}\nURL: {html_content.url}",
                    'section': 'overview'
                },
                {
                    'content': html_content.clean_content,
                    'section': 'main_content'
                }
            ]
            
            # Add headings as separate chunks
            for heading in html_content.headings:
                chunks_data.append({
                    'content': f"Heading {heading['level']}: {heading['text']}",
                    'section': f'heading_{heading["level"]}'
                })
            
            # Add paragraphs as separate chunks
            for i, paragraph in enumerate(html_content.paragraphs[:10]):  # Limit to first 10 paragraphs
                chunks_data.append({
                    'content': paragraph,
                    'section': f'paragraph_{i+1}'
                })
            
            # Add lists as separate chunks
            for i, list_item in enumerate(html_content.lists[:5]):  # Limit to first 5 lists
                list_content = f"{list_item['type'].upper()} List:\n" + "\n".join(f"- {item}" for item in list_item['items'])
                chunks_data.append({
                    'content': list_content,
                    'section': f'list_{i+1}'
                })
            
            # Add code blocks as separate chunks
            for i, code_block in enumerate(html_content.code_blocks[:3]):  # Limit to first 3 code blocks
                chunks_data.append({
                    'content': f"Code Block:\n{code_block}",
                    'section': f'code_{i+1}'
                })
            
            for chunk_data in chunks_data:
                if chunk_data['content'].strip():
                    # Create uploaded file entry
                    uploaded_file = UploadedFile.objects.create(
                        filename=f"HTML_{document.id}_{chunk_data['section']}.txt",
                        file_hash=hashlib.md5(chunk_data['content'].encode()).hexdigest(),
                        file_size=len(chunk_data['content']),
                        page_count=1,
                        intro=chunk_data['content'][:200],
                        uploaded_by=None
                    )
                    
                    # Create document chunk
                    DocumentChunk.objects.create(
                        uploaded_file=uploaded_file,
                        content=chunk_data['content'],
                        embedding=None,  # Will be generated by RAG service
                        metadata=json.dumps({
                            'section': chunk_data['section'],
                            'url': html_content.url,
                            'title': html_content.title,
                            'language': html_content.language,
                            'content_type': html_content.content_type
                        })
                    )
            
            logger.info(f"Created content chunks for HTML content from {html_content.url}")
            
        except Exception as e:
            logger.error(f"Error creating content chunks for HTML content from {html_content.url}: {e}")
            raise
    
    def _update_content_chunks(self, document: DocumentFile, html_content: HTMLContent):
        """Update existing content chunks"""
        try:
            # Delete existing chunks
            DocumentChunk.objects.filter(
                uploaded_file__filename__startswith=f"HTML_{document.id}_"
            ).delete()
            
            # Recreate chunks
            self._create_content_chunks(document, html_content)
            
        except Exception as e:
            logger.error(f"Error updating content chunks for HTML content from {html_content.url}: {e}")
            raise
    
    def _generate_search_tags(self, html_content: HTMLContent) -> List[str]:
        """Generate search tags for HTML content"""
        tags = []
        
        # Add domain tags
        if html_content.metadata.get('domain'):
            domain = html_content.metadata['domain']
            tags.append(domain.replace('.', '_'))
        
        # Add content type tags
        if html_content.content_type:
            tags.append(html_content.content_type)
        
        # Add language tags
        if html_content.language:
            tags.append(f"lang_{html_content.language}")
        
        # Add quality tags
        if html_content.quality_score > 0.7:
            tags.append('high_quality')
        elif html_content.quality_score > 0.4:
            tags.append('medium_quality')
        else:
            tags.append('low_quality')
        
        # Add relevance tags
        if html_content.relevance_score > 0.7:
            tags.append('high_relevance')
        elif html_content.relevance_score > 0.4:
            tags.append('medium_relevance')
        else:
            tags.append('low_relevance')
        
        # Add structure tags
        if html_content.headings:
            tags.append('has_headings')
        if html_content.tables:
            tags.append('has_tables')
        if html_content.forms:
            tags.append('has_forms')
        if html_content.code_blocks:
            tags.append('has_code')
        
        return list(set(tags))
    
    def _extract_keywords(self, html_content: HTMLContent) -> List[str]:
        """Extract keywords from HTML content"""
        keywords = []
        
        # Extract from title
        if html_content.title:
            keywords.extend(html_content.title.lower().split())
        
        # Extract from description
        if html_content.description:
            keywords.extend(html_content.description.lower().split())
        
        # Extract from headings
        for heading in html_content.headings:
            keywords.extend(heading['text'].lower().split())
        
        # Extract from content (first 1000 characters)
        if html_content.clean_content:
            content_words = html_content.clean_content[:1000].lower().split()
            keywords.extend(content_words)
        
        # Filter and clean keywords
        keywords = [word.strip('.,!?;:') for word in keywords if len(word) > 3]
        keywords = list(set(keywords))  # Remove duplicates
        
        return keywords[:20]  # Limit to 20 keywords


# Example usage and testing
if __name__ == "__main__":
    # Create HTML parser
    parser = HTMLParser()
    
    # Parse HTML from URL
    html_content = parser.parse_url("https://example.com")
    if html_content:
        print(f"Parsed HTML content from {html_content.url}")
        print(f"Title: {html_content.title}")
        print(f"Description: {html_content.description}")
        print(f"Content length: {len(html_content.clean_content)}")
        print(f"Quality score: {html_content.quality_score}")
        print(f"Relevance score: {html_content.relevance_score}")
        
        # Process content
        processor = HTMLProcessor()
        result = processor.process_html_content(html_content)
        print(f"Processing result: {result}")
    
    # Parse HTML from text
    html_text = """
    <html>
    <head>
        <title>Test Page</title>
        <meta name="description" content="This is a test page">
    </head>
    <body>
        <h1>Welcome to Test Page</h1>
        <p>This is a test paragraph with some content.</p>
        <ul>
            <li>Item 1</li>
            <li>Item 2</li>
        </ul>
    </body>
    </html>
    """
    
    html_content = parser.parse_html_text(html_text, "https://test.com")
    if html_content:
        print(f"Parsed HTML text")
        print(f"Title: {html_content.title}")
        print(f"Description: {html_content.description}")
        print(f"Content: {html_content.clean_content}")
        
        # Process content
        processor = HTMLProcessor()
        result = processor.process_html_content(html_content)
        print(f"Processing result: {result}")
