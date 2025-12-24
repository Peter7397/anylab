"""
SSB Scraper for Agilent Official Sources

This module provides automated scraping capabilities for Agilent's Software Status Bulletin (SSB)
and Known Problem Report (KPR) database, focusing on Lab Informatics troubleshooting information.
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
from bs4 import BeautifulSoup
import hashlib
from django.conf import settings
from django.core.cache import cache
from django.utils import timezone
from django.core.files.base import ContentFile

from .metadata_schema import OrganizationMode, DocumentType, SeverityLevel, DualModeMetadata
from .models import DocumentFile, DocumentChunk, UploadedFile

logger = logging.getLogger(__name__)


@dataclass
class SSBEntry:
    """SSB/KPR entry data structure"""
    kpr_number: str
    title: str
    description: str
    severity: SeverityLevel
    software_platform: str
    software_version: str
    affected_components: List[str]
    symptoms: List[str]
    root_cause: Optional[str]
    solution: str
    workaround: Optional[str]
    prerequisites: List[str]
    risks: List[str]
    rollback_procedure: Optional[str]
    related_kprs: List[str]
    created_date: datetime
    updated_date: datetime
    status: str  # open, resolved, closed
    url: str
    html_content: str
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class ScrapingConfig:
    """Configuration for SSB scraping"""
    base_url: str = "https://www.agilent.com/cs/library/support/Patches/SSBs/M84xx.html"
    openlab_help_url: str = "https://openlab.help.agilent.com/en/index.htm"
    max_pages: int = 100
    delay_between_requests: float = 1.0
    timeout: int = 30
    retry_attempts: int = 3
    user_agent: str = "AnyLab-SSB-Scraper/1.0"
    cache_duration: int = 3600  # 1 hour


class SSBScraper:
    """Main SSB scraper class"""
    
    def __init__(self, config: Optional[ScrapingConfig] = None):
        self.config = config or ScrapingConfig()
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': self.config.user_agent,
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
            'Accept-Language': 'en-US,en;q=0.5',
            'Accept-Encoding': 'gzip, deflate',
            'Connection': 'keep-alive',
        })
        self.scraped_urls = set()
        self.processed_kprs = set()
        
    def scrape_all_ssbs(self) -> List[SSBEntry]:
        """Scrape all available SSB entries"""
        logger.info("Starting SSB scraping process")
        
        try:
            # Get main SSB page
            main_page_content = self._fetch_page(self.config.base_url)
            if not main_page_content:
                logger.error("Failed to fetch main SSB page")
                return []
            
            # Parse main page to get SSB links
            ssb_links = self._extract_ssb_links(main_page_content)
            logger.info(f"Found {len(ssb_links)} SSB links")
            
            # Scrape each SSB entry
            ssb_entries = []
            for i, link in enumerate(ssb_links[:self.config.max_pages]):
                try:
                    logger.info(f"Scraping SSB {i+1}/{min(len(ssb_links), self.config.max_pages)}: {link}")
                    
                    # Check cache first
                    cache_key = f"ssb_entry_{hashlib.md5(link.encode()).hexdigest()}"
                    cached_entry = cache.get(cache_key)
                    
                    if cached_entry:
                        logger.info(f"Using cached SSB entry: {link}")
                        ssb_entries.append(SSBEntry(**cached_entry))
                        continue
                    
                    # Fetch and parse SSB page
                    ssb_content = self._fetch_page(link)
                    if ssb_content:
                        ssb_entry = self._parse_ssb_page(ssb_content, link)
                        if ssb_entry:
                            ssb_entries.append(ssb_entry)
                            
                            # Cache the entry
                            cache.set(cache_key, ssb_entry.__dict__, self.config.cache_duration)
                    
                    # Rate limiting
                    time.sleep(self.config.delay_between_requests)
                    
                except Exception as e:
                    logger.error(f"Error scraping SSB {link}: {e}")
                    continue
            
            logger.info(f"Successfully scraped {len(ssb_entries)} SSB entries")
            return ssb_entries
            
        except Exception as e:
            logger.error(f"Error in scrape_all_ssbs: {e}")
            return []
    
    def scrape_openlab_help_portal(self) -> List[Dict[str, Any]]:
        """Scrape OpenLab Help Portal for additional troubleshooting information"""
        logger.info("Starting OpenLab Help Portal scraping")
        
        try:
            # Get main help portal page
            main_content = self._fetch_page(self.config.openlab_help_url)
            if not main_content:
                logger.error("Failed to fetch OpenLab Help Portal")
                return []
            
            # Parse help portal structure
            help_entries = self._extract_help_portal_entries(main_content)
            logger.info(f"Found {len(help_entries)} help portal entries")
            
            return help_entries
            
        except Exception as e:
            logger.error(f"Error scraping OpenLab Help Portal: {e}")
            return []
    
    def _fetch_page(self, url: str) -> Optional[str]:
        """Fetch a web page with retry logic"""
        for attempt in range(self.config.retry_attempts):
            try:
                response = self.session.get(url, timeout=self.config.timeout)
                response.raise_for_status()
                return response.text
                
            except requests.exceptions.RequestException as e:
                logger.warning(f"Attempt {attempt + 1} failed for {url}: {e}")
                if attempt < self.config.retry_attempts - 1:
                    time.sleep(2 ** attempt)  # Exponential backoff
                else:
                    logger.error(f"All attempts failed for {url}")
                    return None
        
        return None
    
    def _extract_ssb_links(self, html_content: str) -> List[str]:
        """Extract SSB links from the main SSB page"""
        soup = BeautifulSoup(html_content, 'html.parser')
        links = []
        
        # Look for SSB/KPR links - these typically have specific patterns
        for link in soup.find_all('a', href=True):
            href = link['href']
            
            # Convert relative URLs to absolute
            if href.startswith('/'):
                href = urljoin(self.config.base_url, href)
            elif not href.startswith('http'):
                href = urljoin(self.config.base_url, href)
            
            # Check if this looks like an SSB/KPR link
            if self._is_ssb_link(href):
                links.append(href)
        
        # Remove duplicates and sort
        links = list(set(links))
        links.sort()
        
        return links
    
    def _is_ssb_link(self, url: str) -> bool:
        """Check if a URL looks like an SSB/KPR link"""
        # Common patterns for SSB/KPR URLs
        ssb_patterns = [
            r'/cs/library/support/Patches/SSBs/',
            r'/support/patches/ssbs/',
            r'/kpr/',
            r'/ssb/',
            r'kpr\d+',
            r'ssb\d+',
            r'M84\d+',  # Agilent M84xx series
        ]
        
        url_lower = url.lower()
        return any(re.search(pattern, url_lower) for pattern in ssb_patterns)
    
    def _parse_ssb_page(self, html_content: str, url: str) -> Optional[SSBEntry]:
        """Parse an individual SSB page"""
        try:
            soup = BeautifulSoup(html_content, 'html.parser')
            
            # Extract KPR number from URL or page content
            kpr_number = self._extract_kpr_number(url, soup)
            if not kpr_number:
                logger.warning(f"Could not extract KPR number from {url}")
                return None
            
            # Extract title
            title = self._extract_title(soup)
            
            # Extract description
            description = self._extract_description(soup)
            
            # Extract severity
            severity = self._extract_severity(soup)
            
            # Extract software information
            software_platform, software_version = self._extract_software_info(soup)
            
            # Extract affected components
            affected_components = self._extract_affected_components(soup)
            
            # Extract symptoms
            symptoms = self._extract_symptoms(soup)
            
            # Extract root cause
            root_cause = self._extract_root_cause(soup)
            
            # Extract solution
            solution = self._extract_solution(soup)
            
            # Extract workaround
            workaround = self._extract_workaround(soup)
            
            # Extract prerequisites
            prerequisites = self._extract_prerequisites(soup)
            
            # Extract risks
            risks = self._extract_risks(soup)
            
            # Extract rollback procedure
            rollback_procedure = self._extract_rollback_procedure(soup)
            
            # Extract related KPRs
            related_kprs = self._extract_related_kprs(soup)
            
            # Extract dates
            created_date, updated_date = self._extract_dates(soup)
            
            # Extract status
            status = self._extract_status(soup)
            
            # Build metadata
            metadata = {
                'source_url': url,
                'scraped_at': timezone.now().isoformat(),
                'scraper_version': '1.0',
                'content_length': len(html_content),
                'has_solution': bool(solution),
                'has_workaround': bool(workaround),
                'severity_level': severity.value if severity else 'unknown',
                'software_platform': software_platform,
                'software_version': software_version,
            }
            
            return SSBEntry(
                kpr_number=kpr_number,
                title=title,
                description=description,
                severity=severity,
                software_platform=software_platform,
                software_version=software_version,
                affected_components=affected_components,
                symptoms=symptoms,
                root_cause=root_cause,
                solution=solution,
                workaround=workaround,
                prerequisites=prerequisites,
                risks=risks,
                rollback_procedure=rollback_procedure,
                related_kprs=related_kprs,
                created_date=created_date,
                updated_date=updated_date,
                status=status,
                url=url,
                html_content=html_content,
                metadata=metadata
            )
            
        except Exception as e:
            logger.error(f"Error parsing SSB page {url}: {e}")
            return None
    
    def _extract_kpr_number(self, url: str, soup: BeautifulSoup) -> Optional[str]:
        """Extract KPR number from URL or page content"""
        # Try to extract from URL first
        url_patterns = [
            r'kpr(\d+)',
            r'ssb(\d+)',
            r'M84(\d+)',
            r'(\d{6,})',  # 6+ digit numbers
        ]
        
        for pattern in url_patterns:
            match = re.search(pattern, url, re.IGNORECASE)
            if match:
                return match.group(1)
        
        # Try to extract from page content
        kpr_patterns = [
            r'KPR\s*#?\s*(\d+)',
            r'SSB\s*#?\s*(\d+)',
            r'Known Problem Report\s*#?\s*(\d+)',
            r'Software Status Bulletin\s*#?\s*(\d+)',
        ]
        
        page_text = soup.get_text()
        for pattern in kpr_patterns:
            match = re.search(pattern, page_text, re.IGNORECASE)
            if match:
                return match.group(1)
        
        return None
    
    def _extract_title(self, soup: BeautifulSoup) -> str:
        """Extract title from SSB page"""
        # Try different title selectors
        title_selectors = [
            'h1',
            '.title',
            '.page-title',
            '.ssb-title',
            '.kpr-title',
            'title'
        ]
        
        for selector in title_selectors:
            title_elem = soup.select_one(selector)
            if title_elem:
                title = title_elem.get_text().strip()
                if title and len(title) > 10:  # Reasonable title length
                    return title
        
        return "Untitled SSB Entry"
    
    def _extract_description(self, soup: BeautifulSoup) -> str:
        """Extract description from SSB page"""
        # Look for description in common sections
        desc_selectors = [
            '.description',
            '.summary',
            '.overview',
            '.problem-description',
            'p'
        ]
        
        for selector in desc_selectors:
            desc_elem = soup.select_one(selector)
            if desc_elem:
                desc = desc_elem.get_text().strip()
                if desc and len(desc) > 20:  # Reasonable description length
                    return desc
        
        return ""
    
    def _extract_severity(self, soup: BeautifulSoup) -> Optional[SeverityLevel]:
        """Extract severity level from SSB page"""
        page_text = soup.get_text().lower()
        
        severity_mapping = {
            'critical': SeverityLevel.CRITICAL,
            'high': SeverityLevel.HIGH,
            'medium': SeverityLevel.MEDIUM,
            'low': SeverityLevel.LOW,
            'informational': SeverityLevel.INFORMATIONAL,
            'info': SeverityLevel.INFORMATIONAL,
        }
        
        for keyword, severity in severity_mapping.items():
            if keyword in page_text:
                return severity
        
        return SeverityLevel.MEDIUM  # Default to medium if not found
    
    def _extract_software_info(self, soup: BeautifulSoup) -> Tuple[str, str]:
        """Extract software platform and version information"""
        page_text = soup.get_text()
        
        # Common Agilent software platforms
        platforms = [
            'OpenLab CDS', 'OpenLab ECM', 'OpenLab ELN', 'OpenLab Server',
            'MassHunter', 'VNMRJ', 'VNMR', 'ChemStation', 'OpenLAB',
            'Agilent 1290', 'Agilent 1260', 'Agilent 1100'
        ]
        
        software_platform = "Unknown"
        software_version = "Unknown"
        
        for platform in platforms:
            if platform.lower() in page_text.lower():
                software_platform = platform
                break
        
        # Try to extract version numbers
        version_patterns = [
            r'version\s+(\d+\.\d+(?:\.\d+)?)',
            r'v(\d+\.\d+(?:\.\d+)?)',
            r'(\d+\.\d+(?:\.\d+)?)',
        ]
        
        for pattern in version_patterns:
            match = re.search(pattern, page_text, re.IGNORECASE)
            if match:
                software_version = match.group(1)
                break
        
        return software_platform, software_version
    
    def _extract_affected_components(self, soup: BeautifulSoup) -> List[str]:
        """Extract affected components"""
        components = []
        
        # Look for component lists
        component_selectors = [
            '.affected-components',
            '.components',
            '.affected-items',
            'ul li',
            'ol li'
        ]
        
        for selector in component_selectors:
            elements = soup.select(selector)
            for elem in elements:
                text = elem.get_text().strip()
                if text and len(text) < 100:  # Reasonable component name length
                    components.append(text)
        
        return list(set(components))  # Remove duplicates
    
    def _extract_symptoms(self, soup: BeautifulSoup) -> List[str]:
        """Extract symptoms from SSB page"""
        symptoms = []
        
        # Look for symptoms sections
        symptom_keywords = ['symptom', 'issue', 'problem', 'error', 'failure']
        
        for keyword in symptom_keywords:
            # Find sections containing symptom keywords
            sections = soup.find_all(text=re.compile(keyword, re.IGNORECASE))
            for section in sections:
                parent = section.parent
                if parent:
                    text = parent.get_text().strip()
                    if text and len(text) > 10:
                        symptoms.append(text)
        
        return list(set(symptoms))
    
    def _extract_root_cause(self, soup: BeautifulSoup) -> Optional[str]:
        """Extract root cause information"""
        root_cause_keywords = ['root cause', 'cause', 'reason', 'underlying']
        
        for keyword in root_cause_keywords:
            sections = soup.find_all(text=re.compile(keyword, re.IGNORECASE))
            for section in sections:
                parent = section.parent
                if parent:
                    text = parent.get_text().strip()
                    if text and len(text) > 20:
                        return text
        
        return None
    
    def _extract_solution(self, soup: BeautifulSoup) -> str:
        """Extract solution information"""
        solution_keywords = ['solution', 'fix', 'resolution', 'corrective action']
        
        for keyword in solution_keywords:
            sections = soup.find_all(text=re.compile(keyword, re.IGNORECASE))
            for section in sections:
                parent = section.parent
                if parent:
                    text = parent.get_text().strip()
                    if text and len(text) > 20:
                        return text
        
        return ""
    
    def _extract_workaround(self, soup: BeautifulSoup) -> Optional[str]:
        """Extract workaround information"""
        workaround_keywords = ['workaround', 'temporary fix', 'interim solution']
        
        for keyword in workaround_keywords:
            sections = soup.find_all(text=re.compile(keyword, re.IGNORECASE))
            for section in sections:
                parent = section.parent
                if parent:
                    text = parent.get_text().strip()
                    if text and len(text) > 20:
                        return text
        
        return None
    
    def _extract_prerequisites(self, soup: BeautifulSoup) -> List[str]:
        """Extract prerequisites"""
        prerequisites = []
        
        prereq_keywords = ['prerequisite', 'requirement', 'before', 'prior to']
        
        for keyword in prereq_keywords:
            sections = soup.find_all(text=re.compile(keyword, re.IGNORECASE))
            for section in sections:
                parent = section.parent
                if parent:
                    text = parent.get_text().strip()
                    if text and len(text) > 10:
                        prerequisites.append(text)
        
        return list(set(prerequisites))
    
    def _extract_risks(self, soup: BeautifulSoup) -> List[str]:
        """Extract risk information"""
        risks = []
        
        risk_keywords = ['risk', 'warning', 'caution', 'important']
        
        for keyword in risk_keywords:
            sections = soup.find_all(text=re.compile(keyword, re.IGNORECASE))
            for section in sections:
                parent = section.parent
                if parent:
                    text = parent.get_text().strip()
                    if text and len(text) > 10:
                        risks.append(text)
        
        return list(set(risks))
    
    def _extract_rollback_procedure(self, soup: BeautifulSoup) -> Optional[str]:
        """Extract rollback procedure"""
        rollback_keywords = ['rollback', 'revert', 'undo', 'restore']
        
        for keyword in rollback_keywords:
            sections = soup.find_all(text=re.compile(keyword, re.IGNORECASE))
            for section in sections:
                parent = section.parent
                if parent:
                    text = parent.get_text().strip()
                    if text and len(text) > 20:
                        return text
        
        return None
    
    def _extract_related_kprs(self, soup: BeautifulSoup) -> List[str]:
        """Extract related KPR numbers"""
        related_kprs = []
        
        # Look for KPR references in the text
        kpr_patterns = [
            r'KPR\s*#?\s*(\d+)',
            r'SSB\s*#?\s*(\d+)',
            r'related.*?(\d{6,})',
        ]
        
        page_text = soup.get_text()
        for pattern in kpr_patterns:
            matches = re.findall(pattern, page_text, re.IGNORECASE)
            related_kprs.extend(matches)
        
        return list(set(related_kprs))
    
    def _extract_dates(self, soup: BeautifulSoup) -> Tuple[datetime, datetime]:
        """Extract creation and update dates"""
        page_text = soup.get_text()
        
        # Date patterns
        date_patterns = [
            r'(\d{1,2}/\d{1,2}/\d{4})',
            r'(\d{4}-\d{2}-\d{2})',
            r'(\d{1,2}-\d{1,2}-\d{4})',
        ]
        
        dates = []
        for pattern in date_patterns:
            matches = re.findall(pattern, page_text)
            dates.extend(matches)
        
        # Try to parse dates
        created_date = timezone.now()
        updated_date = timezone.now()
        
        if dates:
            try:
                # Use the first date as created, last as updated
                created_date = datetime.strptime(dates[0], '%m/%d/%Y')
                if len(dates) > 1:
                    updated_date = datetime.strptime(dates[-1], '%m/%d/%Y')
                else:
                    updated_date = created_date
            except ValueError:
                pass
        
        return created_date, updated_date
    
    def _extract_status(self, soup: BeautifulSoup) -> str:
        """Extract status information"""
        page_text = soup.get_text().lower()
        
        if 'resolved' in page_text or 'fixed' in page_text:
            return 'resolved'
        elif 'closed' in page_text:
            return 'closed'
        else:
            return 'open'
    
    def _extract_help_portal_entries(self, html_content: str) -> List[Dict[str, Any]]:
        """Extract entries from OpenLab Help Portal"""
        soup = BeautifulSoup(html_content, 'html.parser')
        entries = []
        
        # Look for help articles, FAQs, and troubleshooting guides
        article_selectors = [
            'article',
            '.help-article',
            '.faq-item',
            '.troubleshooting-item',
            '.guide-item'
        ]
        
        for selector in article_selectors:
            elements = soup.select(selector)
            for elem in elements:
                entry = {
                    'title': '',
                    'content': '',
                    'url': '',
                    'type': 'help_article',
                    'category': 'troubleshooting'
                }
                
                # Extract title
                title_elem = elem.select_one('h1, h2, h3, .title')
                if title_elem:
                    entry['title'] = title_elem.get_text().strip()
                
                # Extract content
                content_elem = elem.select_one('.content, .description, p')
                if content_elem:
                    entry['content'] = content_elem.get_text().strip()
                
                # Extract URL
                link_elem = elem.select_one('a[href]')
                if link_elem:
                    href = link_elem['href']
                    if href.startswith('/'):
                        href = urljoin(self.config.openlab_help_url, href)
                    entry['url'] = href
                
                if entry['title'] and entry['content']:
                    entries.append(entry)
        
        return entries


class SSBProcessor:
    """Process scraped SSB data and integrate with document management system"""
    
    def __init__(self):
        self.rag_service = None  # Will be initialized when needed
    
    def process_ssb_entries(self, ssb_entries: List[SSBEntry]) -> Dict[str, Any]:
        """Process SSB entries and create document entries"""
        logger.info(f"Processing {len(ssb_entries)} SSB entries")
        
        results = {
            'processed': 0,
            'created': 0,
            'updated': 0,
            'errors': 0,
            'skipped': 0
        }
        
        for ssb_entry in ssb_entries:
            try:
                # Check if this KPR already exists
                existing_doc = self._find_existing_document(ssb_entry.kpr_number)
                
                if existing_doc:
                    # Update existing document
                    self._update_document(existing_doc, ssb_entry)
                    results['updated'] += 1
                else:
                    # Create new document
                    self._create_document(ssb_entry)
                    results['created'] += 1
                
                results['processed'] += 1
                
            except Exception as e:
                logger.error(f"Error processing SSB {ssb_entry.kpr_number}: {e}")
                results['errors'] += 1
        
        logger.info(f"SSB processing completed: {results}")
        return results
    
    def _find_existing_document(self, kpr_number: str) -> Optional[DocumentFile]:
        """Find existing document by KPR number"""
        try:
            # Look for documents with this KPR number in metadata
            documents = DocumentFile.objects.filter(
                metadata__icontains=f'"kpr_number": "{kpr_number}"'
            )
            return documents.first()
        except Exception as e:
            logger.error(f"Error finding existing document for KPR {kpr_number}: {e}")
            return None
    
    def _create_document(self, ssb_entry: SSBEntry) -> DocumentFile:
        """Create a new document from SSB entry"""
        try:
            # Create metadata
            metadata = {
                'kpr_number': ssb_entry.kpr_number,
                'severity_level': ssb_entry.severity.value if ssb_entry.severity else 'medium',
                'software_platform': ssb_entry.software_platform,
                'software_version': ssb_entry.software_version,
                'affected_components': ssb_entry.affected_components,
                'symptoms': ssb_entry.symptoms,
                'root_cause': ssb_entry.root_cause,
                'solution': ssb_entry.solution,
                'workaround': ssb_entry.workaround,
                'prerequisites': ssb_entry.prerequisites,
                'risks': ssb_entry.risks,
                'rollback_procedure': ssb_entry.rollback_procedure,
                'related_kprs': ssb_entry.related_kprs,
                'status': ssb_entry.status,
                'source_url': ssb_entry.url,
                'scraped_at': ssb_entry.metadata.get('scraped_at'),
                'document_type': 'SSB_KPR',
                'organization_mode': 'lab-informatics',
                'content_category': 'troubleshooting',
                'quality_score': self._calculate_quality_score(ssb_entry),
                'search_tags': self._generate_search_tags(ssb_entry),
                'keywords': self._extract_keywords(ssb_entry)
            }
            
            # Create HTML file from HTML content
            html_filename = f"SSB_{ssb_entry.kpr_number}.html"
            try:
                html_bytes = ssb_entry.html_content.encode('utf-8')
                html_file = ContentFile(html_bytes, name=html_filename)
                logger.info(f"Created HTML file for SSB {ssb_entry.kpr_number}, size: {len(html_bytes)} bytes")
            except Exception as e:
                logger.error(f"Error creating HTML file for SSB {ssb_entry.kpr_number}: {e}")
                html_file = None
            
            # Create document file
            document = DocumentFile.objects.create(
                title=f"SSB {ssb_entry.kpr_number}: {ssb_entry.title}",
                filename=html_filename,
                file=html_file,  # Save the HTML file
                document_type="SSB_KPR",
                description=ssb_entry.description,
                metadata=metadata,  # Django JSONField stores dict directly
                uploaded_by=None,  # System upload
                page_count=1,
                file_size=len(html_bytes) if html_file else 0,
                created_at=ssb_entry.created_date,
                updated_at=ssb_entry.updated_date
            )
            
            # Create content chunks for RAG
            self._create_content_chunks(document, ssb_entry)
            
            logger.info(f"Created document for SSB {ssb_entry.kpr_number}")
            return document
            
        except Exception as e:
            logger.error(f"Error creating document for SSB {ssb_entry.kpr_number}: {e}")
            raise
    
    def _update_document(self, document: DocumentFile, ssb_entry: SSBEntry):
        """Update existing document with new SSB data"""
        try:
            # Update document fields
            document.title = f"SSB {ssb_entry.kpr_number}: {ssb_entry.title}"
            document.description = ssb_entry.description
            document.updated_at = ssb_entry.updated_date
            
            # Update HTML file if it exists or create new one
            html_filename = f"SSB_{ssb_entry.kpr_number}.html"
            try:
                html_bytes = ssb_entry.html_content.encode('utf-8')
                html_file = ContentFile(html_bytes, name=html_filename)
                
                # Delete old file if it exists
                if document.file:
                    document.file.delete(save=False)
                
                # Save new file
                document.file = html_file
                document.file_size = len(html_bytes)
                document.filename = html_filename
                logger.info(f"Updated HTML file for SSB {ssb_entry.kpr_number}, size: {len(html_bytes)} bytes")
            except Exception as e:
                logger.error(f"Error updating HTML file for SSB {ssb_entry.kpr_number}: {e}")
            
            # Update metadata
            metadata = json.loads(document.metadata) if isinstance(document.metadata, str) else document.metadata or {}
            metadata.update({
                'kpr_number': ssb_entry.kpr_number,
                'severity_level': ssb_entry.severity.value if ssb_entry.severity else 'medium',
                'software_platform': ssb_entry.software_platform,
                'software_version': ssb_entry.software_version,
                'solution': ssb_entry.solution,
                'workaround': ssb_entry.workaround,
                'status': ssb_entry.status,
                'updated_at': ssb_entry.updated_date.isoformat(),
                'quality_score': self._calculate_quality_score(ssb_entry),
            })
            
            document.metadata = metadata  # Django JSONField stores dict directly
            document.save()
            
            # Update content chunks
            self._update_content_chunks(document, ssb_entry)
            
            logger.info(f"Updated document for SSB {ssb_entry.kpr_number}")
            
        except Exception as e:
            logger.error(f"Error updating document for SSB {ssb_entry.kpr_number}: {e}")
            raise
    
    def _create_content_chunks(self, document: DocumentFile, ssb_entry: SSBEntry):
        """Create content chunks for RAG indexing"""
        try:
            # Create chunks for different sections
            chunks_data = [
                {
                    'content': f"Title: {ssb_entry.title}\nDescription: {ssb_entry.description}",
                    'section': 'overview'
                },
                {
                    'content': f"Symptoms: {'; '.join(ssb_entry.symptoms)}",
                    'section': 'symptoms'
                },
                {
                    'content': f"Root Cause: {ssb_entry.root_cause}" if ssb_entry.root_cause else "",
                    'section': 'root_cause'
                },
                {
                    'content': f"Solution: {ssb_entry.solution}",
                    'section': 'solution'
                },
                {
                    'content': f"Workaround: {ssb_entry.workaround}" if ssb_entry.workaround else "",
                    'section': 'workaround'
                },
                {
                    'content': f"Prerequisites: {'; '.join(ssb_entry.prerequisites)}",
                    'section': 'prerequisites'
                },
                {
                    'content': f"Risks: {'; '.join(ssb_entry.risks)}",
                    'section': 'risks'
                }
            ]
            
            for chunk_data in chunks_data:
                if chunk_data['content'].strip():
                    # Create uploaded file entry
                    uploaded_file = UploadedFile.objects.create(
                        filename=f"SSB_{ssb_entry.kpr_number}_{chunk_data['section']}.txt",
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
                            'kpr_number': ssb_entry.kpr_number,
                            'software_platform': ssb_entry.software_platform,
                            'severity': ssb_entry.severity.value if ssb_entry.severity else 'medium'
                        })
                    )
            
            logger.info(f"Created content chunks for SSB {ssb_entry.kpr_number}")
            
        except Exception as e:
            logger.error(f"Error creating content chunks for SSB {ssb_entry.kpr_number}: {e}")
            raise
    
    def _update_content_chunks(self, document: DocumentFile, ssb_entry: SSBEntry):
        """Update existing content chunks"""
        try:
            # Delete existing chunks
            DocumentChunk.objects.filter(
                uploaded_file__filename__startswith=f"SSB_{ssb_entry.kpr_number}_"
            ).delete()
            
            # Recreate chunks
            self._create_content_chunks(document, ssb_entry)
            
        except Exception as e:
            logger.error(f"Error updating content chunks for SSB {ssb_entry.kpr_number}: {e}")
            raise
    
    def _calculate_quality_score(self, ssb_entry: SSBEntry) -> float:
        """Calculate quality score for SSB entry"""
        score = 0.0
        
        # Base score
        score += 0.2
        
        # Title quality
        if ssb_entry.title and len(ssb_entry.title) > 10:
            score += 0.1
        
        # Description quality
        if ssb_entry.description and len(ssb_entry.description) > 50:
            score += 0.1
        
        # Solution quality
        if ssb_entry.solution and len(ssb_entry.solution) > 20:
            score += 0.2
        
        # Workaround availability
        if ssb_entry.workaround:
            score += 0.1
        
        # Root cause analysis
        if ssb_entry.root_cause:
            score += 0.1
        
        # Prerequisites and risks
        if ssb_entry.prerequisites:
            score += 0.1
        if ssb_entry.risks:
            score += 0.1
        
        # Rollback procedure
        if ssb_entry.rollback_procedure:
            score += 0.1
        
        return min(score, 1.0)
    
    def _generate_search_tags(self, ssb_entry: SSBEntry) -> List[str]:
        """Generate search tags for SSB entry"""
        tags = []
        
        # Add software platform tags
        if ssb_entry.software_platform:
            tags.append(ssb_entry.software_platform.lower().replace(' ', '_'))
        
        # Add severity tags
        if ssb_entry.severity:
            tags.append(f"severity_{ssb_entry.severity.value}")
        
        # Add component tags
        for component in ssb_entry.affected_components:
            tags.append(component.lower().replace(' ', '_'))
        
        # Add symptom tags
        for symptom in ssb_entry.symptoms:
            words = symptom.lower().split()
            tags.extend([word for word in words if len(word) > 3])
        
        return list(set(tags))
    
    def _extract_keywords(self, ssb_entry: SSBEntry) -> List[str]:
        """Extract keywords from SSB entry"""
        keywords = []
        
        # Extract from title
        if ssb_entry.title:
            keywords.extend(ssb_entry.title.lower().split())
        
        # Extract from description
        if ssb_entry.description:
            keywords.extend(ssb_entry.description.lower().split())
        
        # Extract from symptoms
        for symptom in ssb_entry.symptoms:
            keywords.extend(symptom.lower().split())
        
        # Filter and clean keywords
        keywords = [word.strip('.,!?;:') for word in keywords if len(word) > 3]
        keywords = list(set(keywords))  # Remove duplicates
        
        return keywords[:20]  # Limit to 20 keywords


# Example usage and testing
if __name__ == "__main__":
    # Create scraper
    scraper = SSBScraper()
    
    # Scrape SSB entries
    ssb_entries = scraper.scrape_all_ssbs()
    print(f"Scraped {len(ssb_entries)} SSB entries")
    
    # Process entries
    processor = SSBProcessor()
    results = processor.process_ssb_entries(ssb_entries)
    print(f"Processing results: {results}")
    
    # Scrape OpenLab Help Portal
    help_entries = scraper.scrape_openlab_help_portal()
    print(f"Scraped {len(help_entries)} help portal entries")
