"""
Webpage Recursive Crawler

Recursively crawls webpages to discover downloadable files with depth control,
file type filtering, and performance optimizations.
"""

import logging
import time
import re
import hashlib
from dataclasses import dataclass, field
from typing import Dict, Any, List, Optional, Set
from urllib.parse import urljoin, urlparse
from urllib.robotparser import RobotFileParser
from concurrent.futures import ThreadPoolExecutor, as_completed
import requests
from bs4 import BeautifulSoup
from django.core.cache import cache
from django.conf import settings

logger = logging.getLogger(__name__)


@dataclass
class WebpageCrawlerConfig:
    """Configuration for webpage crawling"""
    max_depth: int = 2  # Maximum crawl depth (0 = current page only)
    max_pages: int = 50  # Maximum pages to crawl
    max_files: int = 200  # Maximum files to discover
    same_domain_only: bool = True  # Only crawl same domain
    respect_robots_txt: bool = True  # Respect robots.txt
    delay_between_requests: float = 1.0  # Delay between requests (seconds)
    timeout_per_page: int = 30  # Timeout per page request (seconds)
    concurrent_requests: int = 3  # Number of concurrent requests
    file_type_filters: List[str] = field(default_factory=list)  # e.g., ['pdf', 'docx']
    max_file_size_mb: int = 20  # Maximum file size in MB (0 = no limit)
    user_agent: str = 'Mozilla/5.0 (compatible; AnylabWebCrawler/1.0)'


@dataclass
class DiscoveredFile:
    """Represents a discovered file"""
    url: str
    name: str
    type: str  # pdf, doc, xls, ppt, etc.
    discovered_from: str  # URL of page where file was found
    size: Optional[int] = None  # Size in bytes
    size_mb: Optional[float] = None  # Size in MB
    content_type: Optional[str] = None  # Content-Type header if available


class WebpageCrawler:
    """Recursive webpage crawler for discovering downloadable files"""
    
    def __init__(self, config: Optional[WebpageCrawlerConfig] = None):
        self.config = config or WebpageCrawlerConfig()
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': self.config.user_agent,
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
            'Accept-Language': 'en-US,en;q=0.5',
        })
        
        # File extensions to look for
        self.file_extensions = {
            'pdf': ['pdf'],
            'doc': ['doc', 'docx'],
            'xls': ['xls', 'xlsx'],
            'ppt': ['ppt', 'pptx'],
            'txt': ['txt', 'md', 'rtf'],
            'csv': ['csv'],
            'zip': ['zip', 'rar', '7z', 'tar', 'gz'],
            'image': ['jpg', 'jpeg', 'png', 'gif', 'bmp', 'svg', 'webp'],
            'html': ['html', 'htm', 'mhtml'],
        }
        
        # All extensions flattened
        self.all_extensions = []
        for ext_list in self.file_extensions.values():
            self.all_extensions.extend(ext_list)
    
    def crawl_webpage(self, url: str, config: Optional[WebpageCrawlerConfig] = None) -> Dict[str, Any]:
        """
        Main entry point for crawling a webpage
        
        Args:
            url: Starting URL to crawl
            config: Optional configuration override
            
        Returns:
            Dict with 'discovered_files', 'total_pages_crawled', 'total_files_found', 'crawl_time_seconds'
        """
        start_time = time.time()
        crawl_config = config or self.config
        
        # Check cache first
        cache_key = self._get_cache_key(url, crawl_config)
        cached_result = cache.get(cache_key)
        if cached_result:
            logger.info(f"Using cached crawl result for {url}")
            return cached_result
        
        # Validate URL
        parsed_url = urlparse(url)
        if not parsed_url.scheme or not parsed_url.netloc:
            raise ValueError(f"Invalid URL: {url}")
        
        if parsed_url.scheme not in ['http', 'https']:
            raise ValueError(f"URL must use http or https: {url}")
        
        base_domain = f"{parsed_url.scheme}://{parsed_url.netloc}"
        
        # Initialize crawl state
        visited_urls: Set[str] = set()
        discovered_files: List[DiscoveredFile] = []
        robots_parser: Optional[RobotFileParser] = None
        
        # Check robots.txt if enabled
        if crawl_config.respect_robots_txt:
            robots_parser = self._check_robots_txt(base_domain)
        
        # Start recursive crawl
        try:
            self._crawl_recursive(
                url=url,
                depth=0,
                max_depth=crawl_config.max_depth,
                visited=visited_urls,
                discovered_files=discovered_files,
                base_domain=base_domain,
                robots_parser=robots_parser,
                config=crawl_config
            )
        except Exception as e:
            logger.error(f"Error during crawl: {e}", exc_info=True)
            raise
        
        # Filter files by type and size
        filtered_files = self._filter_files(discovered_files, crawl_config)
        
        # Prepare result
        result = {
            'discovered_files': [
                {
                    'url': f.url,
                    'name': f.name,
                    'type': f.type,
                    'size': f.size,
                    'size_mb': f.size_mb,
                    'discovered_from': f.discovered_from,
                    'content_type': f.content_type,
                }
                for f in filtered_files
            ],
            'total_pages_crawled': len(visited_urls),
            'total_files_found': len(discovered_files),
            'total_files_after_filter': len(filtered_files),
            'crawl_time_seconds': round(time.time() - start_time, 2),
        }
        
        # Cache result (1 hour TTL)
        cache.set(cache_key, result, 3600)
        
        logger.info(f"Crawl completed: {len(filtered_files)} files from {len(visited_urls)} pages in {result['crawl_time_seconds']}s")
        
        return result
    
    def _crawl_recursive(
        self,
        url: str,
        depth: int,
        max_depth: int,
        visited: Set[str],
        discovered_files: List[DiscoveredFile],
        base_domain: str,
        robots_parser: Optional[RobotFileParser],
        config: WebpageCrawlerConfig
    ):
        """Recursively crawl webpages"""
        # Check limits
        if len(visited) >= config.max_pages:
            logger.info(f"Reached max pages limit ({config.max_pages})")
            return
        
        if len(discovered_files) >= config.max_files:
            logger.info(f"Reached max files limit ({config.max_files})")
            return
        
        if depth > max_depth:
            return
        
        # Normalize URL
        normalized_url = self._normalize_url(url)
        if normalized_url in visited:
            return
        
        # Check robots.txt
        if robots_parser and not robots_parser.can_fetch(self.config.user_agent, normalized_url):
            logger.debug(f"Robots.txt disallows: {normalized_url}")
            return
        
        # Check domain restriction
        if config.same_domain_only and not self._is_same_domain(normalized_url, base_domain):
            logger.debug(f"Skipping different domain: {normalized_url}")
            return
        
        # Fetch page
        try:
            logger.debug(f"Crawling (depth {depth}): {normalized_url}")
            response = self.session.get(
                normalized_url,
                timeout=config.timeout_per_page,
                allow_redirects=True
            )
            response.raise_for_status()
            
            # Mark as visited
            visited.add(normalized_url)
            
            # Rate limiting
            if config.delay_between_requests > 0:
                time.sleep(config.delay_between_requests)
            
        except requests.exceptions.RequestException as e:
            logger.warning(f"Failed to fetch {normalized_url}: {e}")
            return
        
        # Discover files on this page
        try:
            soup = BeautifulSoup(response.content, 'html.parser')
            page_files = self._discover_files_on_page(soup, response.url, normalized_url)
            
            # Add new files (avoid duplicates)
            existing_urls = {f.url for f in discovered_files}
            for file_info in page_files:
                if file_info.url not in existing_urls:
                    discovered_files.append(file_info)
                    if len(discovered_files) >= config.max_files:
                        return
        except Exception as e:
            logger.warning(f"Error discovering files on {normalized_url}: {e}")
        
        # If not at max depth, crawl linked pages
        if depth < max_depth and len(visited) < config.max_pages:
            # Find all links on the page
            links = soup.find_all('a', href=True)
            urls_to_crawl = []
            
            for link in links:
                href = link.get('href', '')
                if not href:
                    continue
                
                # Resolve relative URLs
                full_url = urljoin(response.url, href)
                normalized = self._normalize_url(full_url)
                
                # Skip if already visited
                if normalized in visited:
                    continue
                
                # Check domain restriction
                if config.same_domain_only and not self._is_same_domain(normalized, base_domain):
                    continue
                
                # Check robots.txt
                if robots_parser and not robots_parser.can_fetch(self.config.user_agent, normalized):
                    continue
                
                # Only crawl HTML pages (not files)
                if not self._is_likely_html_page(normalized):
                    continue
                
                urls_to_crawl.append(normalized)
                
                if len(urls_to_crawl) + len(visited) >= config.max_pages:
                    break
            
            # Crawl linked pages (with concurrency if depth allows)
            if urls_to_crawl:
                if depth == 0 and config.concurrent_requests > 1:
                    # Use concurrent requests for first level
                    self._crawl_concurrent(
                        urls_to_crawl,
                        depth + 1,
                        max_depth,
                        visited,
                        discovered_files,
                        base_domain,
                        robots_parser,
                        config
                    )
                else:
                    # Sequential crawl for deeper levels
                    for next_url in urls_to_crawl:
                        if len(visited) >= config.max_pages or len(discovered_files) >= config.max_files:
                            break
                        self._crawl_recursive(
                            next_url,
                            depth + 1,
                            max_depth,
                            visited,
                            discovered_files,
                            base_domain,
                            robots_parser,
                            config
                        )
    
    def _crawl_concurrent(
        self,
        urls: List[str],
        depth: int,
        max_depth: int,
        visited: Set[str],
        discovered_files: List[DiscoveredFile],
        base_domain: str,
        robots_parser: Optional[RobotFileParser],
        config: WebpageCrawlerConfig
    ):
        """Crawl multiple URLs concurrently"""
        with ThreadPoolExecutor(max_workers=config.concurrent_requests) as executor:
            futures = {}
            for url in urls:
                if len(visited) >= config.max_pages or len(discovered_files) >= config.max_files:
                    break
                future = executor.submit(
                    self._crawl_recursive,
                    url,
                    depth,
                    max_depth,
                    visited,
                    discovered_files,
                    base_domain,
                    robots_parser,
                    config
                )
                futures[future] = url
            
            # Wait for completion
            for future in as_completed(futures):
                try:
                    future.result()
                except Exception as e:
                    logger.warning(f"Error in concurrent crawl for {futures[future]}: {e}")
    
    def _discover_files_on_page(self, soup: BeautifulSoup, base_url: str, page_url: str) -> List[DiscoveredFile]:
        """Discover downloadable files on a webpage using multiple methods"""
        discovered = []
        seen_urls = set()
        
        # Method 1: Find all <a> tags with href
        links = soup.find_all('a', href=True)
        for link in links:
            href = link.get('href', '')
            if not href:
                continue
            
            full_url = urljoin(base_url, href)
            normalized = self._normalize_url(full_url)
            
            if normalized in seen_urls:
                continue
            
            file_info = self._check_if_file_url(normalized, page_url)
            if file_info:
                discovered.append(file_info)
                seen_urls.add(normalized)
        
        # Method 2: Find <iframe>, <embed>, <object> tags
        for tag in soup.find_all(['iframe', 'embed', 'object']):
            src = tag.get('src') or tag.get('data') or tag.get('data-src')
            if src:
                full_url = urljoin(base_url, src)
                normalized = self._normalize_url(full_url)
                
                if normalized in seen_urls:
                    continue
                
                file_info = self._check_if_file_url(normalized, page_url)
                if file_info:
                    discovered.append(file_info)
                    seen_urls.add(normalized)
        
        # Method 3: Find <link> tags (for stylesheets, etc. that might reference files)
        for link in soup.find_all('link', href=True):
            href = link.get('href', '')
            if href:
                full_url = urljoin(base_url, href)
                normalized = self._normalize_url(full_url)
                
                if normalized in seen_urls:
                    continue
                
                file_info = self._check_if_file_url(normalized, page_url)
                if file_info:
                    discovered.append(file_info)
                    seen_urls.add(normalized)
        
        # Method 4: Extract URLs from JavaScript (basic regex)
        scripts = soup.find_all('script')
        for script in scripts:
            if script.string:
                # Find URLs in JavaScript code
                js_urls = re.findall(
                    r'https?://[^\s"\'<>\)]+\.(?:pdf|docx?|xlsx?|pptx?|txt|csv|zip|rar|7z)',
                    script.string,
                    re.IGNORECASE
                )
                for js_url in js_urls:
                    normalized = self._normalize_url(js_url)
                    if normalized in seen_urls:
                        continue
                    
                    file_info = self._check_if_file_url(normalized, page_url)
                    if file_info:
                        discovered.append(file_info)
                        seen_urls.add(normalized)
        
        # Method 5: Check data-* attributes
        for tag in soup.find_all(attrs=lambda x: x and any(k.startswith('data-') for k in x.keys())):
            for attr_name, attr_value in tag.attrs.items():
                if attr_name.startswith('data-') and isinstance(attr_value, str):
                    if attr_value.startswith('http'):
                        normalized = self._normalize_url(attr_value)
                        if normalized in seen_urls:
                            continue
                        
                        file_info = self._check_if_file_url(normalized, page_url)
                        if file_info:
                            discovered.append(file_info)
                            seen_urls.add(normalized)
        
        return discovered
    
    def _check_if_file_url(self, url: str, discovered_from: str) -> Optional[DiscoveredFile]:
        """Check if URL points to a downloadable file and return file info"""
        parsed = urlparse(url)
        path = parsed.path.lower()
        
        # Check file extension
        file_type = None
        extension = None
        
        for ext in self.all_extensions:
            if path.endswith(f'.{ext}'):
                extension = ext
                # Determine file type category
                for type_name, ext_list in self.file_extensions.items():
                    if ext in ext_list:
                        file_type = type_name
                        break
                break
        
        if not file_type:
            return None
        
        # Get filename
        filename = parsed.path.split('/')[-1] or f"file.{extension}"
        
        # Get file info (size, content-type) via HEAD request
        file_info = self._get_file_info(url)
        
        return DiscoveredFile(
            url=url,
            name=filename,
            type=file_type,
            size=file_info.get('size'),
            size_mb=file_info.get('size_mb'),
            discovered_from=discovered_from,
            content_type=file_info.get('content_type'),
        )
    
    def _get_file_info(self, url: str) -> Dict[str, Any]:
        """Get file information via HEAD request"""
        try:
            response = self.session.head(url, timeout=10, allow_redirects=True)
            response.raise_for_status()
            
            # Get size from Content-Length header
            size = None
            size_mb = None
            content_length = response.headers.get('Content-Length')
            if content_length:
                try:
                    size = int(content_length)
                    size_mb = round(size / (1024 * 1024), 2)
                except ValueError:
                    pass
            
            # Get content type
            content_type = response.headers.get('Content-Type', '')
            
            return {
                'size': size,
                'size_mb': size_mb,
                'content_type': content_type,
            }
        except Exception as e:
            logger.debug(f"Could not get file info for {url}: {e}")
            return {'size': None, 'size_mb': None, 'content_type': None}
    
    def _check_robots_txt(self, base_domain: str) -> Optional[RobotFileParser]:
        """Check and parse robots.txt"""
        try:
            robots_url = urljoin(base_domain, '/robots.txt')
            rp = RobotFileParser()
            rp.set_url(robots_url)
            rp.read()
            logger.info(f"Loaded robots.txt from {robots_url}")
            return rp
        except Exception as e:
            logger.debug(f"Could not load robots.txt from {base_domain}: {e}")
            return None
    
    def _is_same_domain(self, url1: str, url2: str) -> bool:
        """Check if two URLs are from the same domain"""
        try:
            parsed1 = urlparse(url1)
            parsed2 = urlparse(url2)
            return parsed1.netloc == parsed2.netloc
        except Exception:
            return False
    
    def _is_likely_html_page(self, url: str) -> bool:
        """Check if URL is likely an HTML page (not a file)"""
        parsed = urlparse(url)
        path = parsed.path.lower()
        
        # If it has a file extension, it's likely a file
        for ext in self.all_extensions:
            if path.endswith(f'.{ext}'):
                return False
        
        # If it ends with / or has no extension, it's likely a page
        return path.endswith('/') or '.' not in path.split('/')[-1]
    
    def _normalize_url(self, url: str) -> str:
        """Normalize URL for comparison"""
        parsed = urlparse(url)
        # Remove fragment, normalize path
        normalized = f"{parsed.scheme}://{parsed.netloc}{parsed.path}"
        if parsed.query:
            normalized += f"?{parsed.query}"
        return normalized.rstrip('/')
    
    def _filter_files(self, files: List[DiscoveredFile], config: WebpageCrawlerConfig) -> List[DiscoveredFile]:
        """Filter files by type and size"""
        filtered = []
        
        for file in files:
            # Filter by file type
            if config.file_type_filters:
                if file.type not in config.file_type_filters:
                    continue
            
            # Filter by size
            if config.max_file_size_mb > 0:
                if file.size_mb and file.size_mb > config.max_file_size_mb:
                    logger.debug(f"Skipping file {file.url}: size {file.size_mb}MB exceeds limit {config.max_file_size_mb}MB")
                    continue
            
            filtered.append(file)
        
        return filtered
    
    def _get_cache_key(self, url: str, config: WebpageCrawlerConfig) -> str:
        """Generate cache key for crawl result"""
        config_str = f"{config.max_depth}_{config.max_pages}_{config.same_domain_only}_{config.file_type_filters}_{config.max_file_size_mb}"
        key = f"webpage_crawl_{hashlib.md5((url + config_str).encode()).hexdigest()}"
        return key

