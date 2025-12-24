"""
Community Forum Integration for AnyLab

This module provides integration with community forums and discussion platforms
to automatically collect troubleshooting solutions and best practices from
the Agilent user community.
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

from .metadata_schema import OrganizationMode, DocumentType, SeverityLevel, DualModeMetadata
from .models import DocumentFile, DocumentChunk, UploadedFile

logger = logging.getLogger(__name__)


@dataclass
class ForumPost:
    """Forum post data structure"""
    post_id: str
    title: str
    content: str
    author: str
    author_reputation: int
    post_date: datetime
    last_updated: datetime
    views: int
    replies: int
    likes: int
    tags: List[str]
    category: str
    thread_url: str
    is_solution: bool
    solution_rating: float
    related_software: List[str]
    related_issues: List[str]
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class ForumConfig:
    """Configuration for forum integration"""
    forum_urls: List[str] = field(default_factory=lambda: [
        "https://community.agilent.com",
        "https://forums.agilent.com",
        "https://www.linkedin.com/groups/agilent-technologies",
        "https://www.reddit.com/r/AgilentTechnologies"
    ])
    max_posts_per_forum: int = 1000
    delay_between_requests: float = 2.0
    timeout: int = 30
    retry_attempts: int = 3
    user_agent: str = "AnyLab-Forum-Integration/1.0"
    cache_duration: int = 7200  # 2 hours
    min_content_length: int = 100
    min_author_reputation: int = 10


class ForumScraper:
    """Main forum scraper class"""
    
    def __init__(self, config: Optional[ForumConfig] = None):
        self.config = config or ForumConfig()
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': self.config.user_agent,
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
            'Accept-Language': 'en-US,en;q=0.5',
            'Accept-Encoding': 'gzip, deflate',
            'Connection': 'keep-alive',
        })
        self.scraped_urls = set()
        self.processed_posts = set()
        
    def scrape_all_forums(self) -> List[ForumPost]:
        """Scrape all configured forums"""
        logger.info("Starting forum scraping process")
        
        all_posts = []
        
        for forum_url in self.config.forum_urls:
            try:
                logger.info(f"Scraping forum: {forum_url}")
                forum_posts = self._scrape_forum(forum_url)
                all_posts.extend(forum_posts)
                
                # Rate limiting between forums
                time.sleep(self.config.delay_between_requests * 2)
                
            except Exception as e:
                logger.error(f"Error scraping forum {forum_url}: {e}")
                continue
        
        logger.info(f"Successfully scraped {len(all_posts)} forum posts")
        return all_posts
    
    def _scrape_forum(self, forum_url: str) -> List[ForumPost]:
        """Scrape a specific forum"""
        posts = []
        
        try:
            # Get forum main page
            main_content = self._fetch_page(forum_url)
            if not main_content:
                logger.error(f"Failed to fetch forum main page: {forum_url}")
                return posts
            
            # Extract forum structure and post links
            post_links = self._extract_post_links(main_content, forum_url)
            logger.info(f"Found {len(post_links)} post links in {forum_url}")
            
            # Scrape each post
            for i, post_link in enumerate(post_links[:self.config.max_posts_per_forum]):
                try:
                    logger.info(f"Scraping post {i+1}/{min(len(post_links), self.config.max_posts_per_forum)}: {post_link}")
                    
                    # Check cache first
                    cache_key = f"forum_post_{hashlib.md5(post_link.encode()).hexdigest()}"
                    cached_post = cache.get(cache_key)
                    
                    if cached_post:
                        logger.info(f"Using cached forum post: {post_link}")
                        posts.append(ForumPost(**cached_post))
                        continue
                    
                    # Fetch and parse post
                    post_content = self._fetch_page(post_link)
                    if post_content:
                        forum_post = self._parse_forum_post(post_content, post_link, forum_url)
                        if forum_post and self._is_valid_post(forum_post):
                            posts.append(forum_post)
                            
                            # Cache the post
                            cache.set(cache_key, forum_post.__dict__, self.config.cache_duration)
                    
                    # Rate limiting
                    time.sleep(self.config.delay_between_requests)
                    
                except Exception as e:
                    logger.error(f"Error scraping post {post_link}: {e}")
                    continue
            
        except Exception as e:
            logger.error(f"Error scraping forum {forum_url}: {e}")
        
        return posts
    
    def _extract_post_links(self, html_content: str, base_url: str) -> List[str]:
        """Extract post links from forum page"""
        soup = BeautifulSoup(html_content, 'html.parser')
        links = []
        
        # Common selectors for forum post links
        post_selectors = [
            'a[href*="/topic/"]',
            'a[href*="/thread/"]',
            'a[href*="/post/"]',
            'a[href*="/discussion/"]',
            '.topic-title a',
            '.thread-title a',
            '.post-title a',
            '.discussion-title a'
        ]
        
        for selector in post_selectors:
            elements = soup.select(selector)
            for elem in elements:
                href = elem.get('href')
                if href:
                    # Convert relative URLs to absolute
                    if href.startswith('/'):
                        href = urljoin(base_url, href)
                    elif not href.startswith('http'):
                        href = urljoin(base_url, href)
                    
                    # Filter out non-post links
                    if self._is_post_link(href):
                        links.append(href)
        
        # Remove duplicates and sort
        links = list(set(links))
        links.sort()
        
        return links
    
    def _is_post_link(self, url: str) -> bool:
        """Check if URL looks like a forum post"""
        post_patterns = [
            r'/topic/',
            r'/thread/',
            r'/post/',
            r'/discussion/',
            r'/forum/.*?/\d+',
            r'/t/\d+',
            r'/p/\d+'
        ]
        
        return any(re.search(pattern, url.lower()) for pattern in post_patterns)
    
    def _parse_forum_post(self, html_content: str, post_url: str, forum_url: str) -> Optional[ForumPost]:
        """Parse a forum post"""
        try:
            soup = BeautifulSoup(html_content, 'html.parser')
            
            # Extract post ID from URL
            post_id = self._extract_post_id(post_url)
            if not post_id:
                return None
            
            # Extract title
            title = self._extract_post_title(soup)
            
            # Extract content
            content = self._extract_post_content(soup)
            if len(content) < self.config.min_content_length:
                return None
            
            # Extract author information
            author, author_reputation = self._extract_author_info(soup)
            
            # Extract dates
            post_date, last_updated = self._extract_post_dates(soup)
            
            # Extract engagement metrics
            views, replies, likes = self._extract_engagement_metrics(soup)
            
            # Extract tags
            tags = self._extract_post_tags(soup)
            
            # Extract category
            category = self._extract_post_category(soup)
            
            # Determine if this is a solution
            is_solution, solution_rating = self._analyze_solution_status(soup, content)
            
            # Extract related software and issues
            related_software = self._extract_related_software(content)
            related_issues = self._extract_related_issues(content)
            
            # Build metadata
            metadata = {
                'source_url': post_url,
                'forum_url': forum_url,
                'scraped_at': timezone.now().isoformat(),
                'scraper_version': '1.0',
                'content_length': len(content),
                'is_solution': is_solution,
                'solution_rating': solution_rating,
                'engagement_score': self._calculate_engagement_score(views, replies, likes),
                'quality_score': self._calculate_quality_score(content, author_reputation, is_solution)
            }
            
            return ForumPost(
                post_id=post_id,
                title=title,
                content=content,
                author=author,
                author_reputation=author_reputation,
                post_date=post_date,
                last_updated=last_updated,
                views=views,
                replies=replies,
                likes=likes,
                tags=tags,
                category=category,
                thread_url=post_url,
                is_solution=is_solution,
                solution_rating=solution_rating,
                related_software=related_software,
                related_issues=related_issues,
                metadata=metadata
            )
            
        except Exception as e:
            logger.error(f"Error parsing forum post {post_url}: {e}")
            return None
    
    def _extract_post_id(self, url: str) -> Optional[str]:
        """Extract post ID from URL"""
        id_patterns = [
            r'/topic/(\d+)',
            r'/thread/(\d+)',
            r'/post/(\d+)',
            r'/discussion/(\d+)',
            r'/t/(\d+)',
            r'/p/(\d+)',
            r'/(\d+)$'
        ]
        
        for pattern in id_patterns:
            match = re.search(pattern, url)
            if match:
                return match.group(1)
        
        # Fallback to URL hash
        return hashlib.md5(url.encode()).hexdigest()[:8]
    
    def _extract_post_title(self, soup: BeautifulSoup) -> str:
        """Extract post title"""
        title_selectors = [
            'h1',
            '.topic-title',
            '.thread-title',
            '.post-title',
            '.discussion-title',
            'title'
        ]
        
        for selector in title_selectors:
            title_elem = soup.select_one(selector)
            if title_elem:
                title = title_elem.get_text().strip()
                if title and len(title) > 5:
                    return title
        
        return "Untitled Forum Post"
    
    def _extract_post_content(self, soup: BeautifulSoup) -> str:
        """Extract post content"""
        content_selectors = [
            '.post-content',
            '.topic-content',
            '.thread-content',
            '.discussion-content',
            '.message-content',
            '.content',
            'article',
            '.post-body'
        ]
        
        for selector in content_selectors:
            content_elem = soup.select_one(selector)
            if content_elem:
                # Remove script and style elements
                for script in content_elem(["script", "style"]):
                    script.decompose()
                
                content = content_elem.get_text().strip()
                if content and len(content) > 50:
                    return content
        
        return ""
    
    def _extract_author_info(self, soup: BeautifulSoup) -> Tuple[str, int]:
        """Extract author information"""
        author = "Unknown"
        reputation = 0
        
        # Author selectors
        author_selectors = [
            '.author',
            '.username',
            '.user-name',
            '.post-author',
            '.topic-author'
        ]
        
        for selector in author_selectors:
            author_elem = soup.select_one(selector)
            if author_elem:
                author = author_elem.get_text().strip()
                break
        
        # Reputation selectors
        reputation_selectors = [
            '.reputation',
            '.user-reputation',
            '.karma',
            '.points'
        ]
        
        for selector in reputation_selectors:
            rep_elem = soup.select_one(selector)
            if rep_elem:
                try:
                    reputation = int(re.search(r'\d+', rep_elem.get_text()).group())
                    break
                except (ValueError, AttributeError):
                    continue
        
        return author, reputation
    
    def _extract_post_dates(self, soup: BeautifulSoup) -> Tuple[datetime, datetime]:
        """Extract post dates"""
        page_text = soup.get_text()
        
        # Date patterns
        date_patterns = [
            r'(\d{1,2}/\d{1,2}/\d{4})',
            r'(\d{4}-\d{2}-\d{2})',
            r'(\d{1,2}-\d{1,2}-\d{4})',
            r'(\d{1,2}\s+\w+\s+\d{4})'
        ]
        
        dates = []
        for pattern in date_patterns:
            matches = re.findall(pattern, page_text)
            dates.extend(matches)
        
        # Try to parse dates
        post_date = timezone.now()
        last_updated = timezone.now()
        
        if dates:
            try:
                # Use the first date as post date, last as updated
                post_date = datetime.strptime(dates[0], '%m/%d/%Y')
                if len(dates) > 1:
                    last_updated = datetime.strptime(dates[-1], '%m/%d/%Y')
                else:
                    last_updated = post_date
            except ValueError:
                pass
        
        return post_date, last_updated
    
    def _extract_engagement_metrics(self, soup: BeautifulSoup) -> Tuple[int, int, int]:
        """Extract engagement metrics"""
        views = 0
        replies = 0
        likes = 0
        
        # Views selectors
        views_selectors = [
            '.views',
            '.view-count',
            '.post-views'
        ]
        
        for selector in views_selectors:
            views_elem = soup.select_one(selector)
            if views_elem:
                try:
                    views = int(re.search(r'\d+', views_elem.get_text()).group())
                    break
                except (ValueError, AttributeError):
                    continue
        
        # Replies selectors
        replies_selectors = [
            '.replies',
            '.reply-count',
            '.post-replies'
        ]
        
        for selector in replies_selectors:
            replies_elem = soup.select_one(selector)
            if replies_elem:
                try:
                    replies = int(re.search(r'\d+', replies_elem.get_text()).group())
                    break
                except (ValueError, AttributeError):
                    continue
        
        # Likes selectors
        likes_selectors = [
            '.likes',
            '.like-count',
            '.post-likes',
            '.upvotes'
        ]
        
        for selector in likes_selectors:
            likes_elem = soup.select_one(selector)
            if likes_elem:
                try:
                    likes = int(re.search(r'\d+', likes_elem.get_text()).group())
                    break
                except (ValueError, AttributeError):
                    continue
        
        return views, replies, likes
    
    def _extract_post_tags(self, soup: BeautifulSoup) -> List[str]:
        """Extract post tags"""
        tags = []
        
        # Tag selectors
        tag_selectors = [
            '.tags a',
            '.tag',
            '.topic-tags a',
            '.post-tags a'
        ]
        
        for selector in tag_selectors:
            tag_elements = soup.select(selector)
            for elem in tag_elements:
                tag = elem.get_text().strip()
                if tag and len(tag) < 50:  # Reasonable tag length
                    tags.append(tag)
        
        return list(set(tags))  # Remove duplicates
    
    def _extract_post_category(self, soup: BeautifulSoup) -> str:
        """Extract post category"""
        category_selectors = [
            '.category',
            '.forum-category',
            '.topic-category',
            '.breadcrumb a'
        ]
        
        for selector in category_selectors:
            category_elem = soup.select_one(selector)
            if category_elem:
                category = category_elem.get_text().strip()
                if category and len(category) < 100:
                    return category
        
        return "General"
    
    def _analyze_solution_status(self, soup: BeautifulSoup, content: str) -> Tuple[bool, float]:
        """Analyze if post contains a solution and rate it"""
        is_solution = False
        solution_rating = 0.0
        
        # Solution indicators
        solution_keywords = [
            'solution', 'fix', 'resolved', 'solved', 'answer', 'workaround',
            'troubleshooting', 'step by step', 'instructions', 'guide'
        ]
        
        content_lower = content.lower()
        solution_count = sum(1 for keyword in solution_keywords if keyword in content_lower)
        
        if solution_count > 0:
            is_solution = True
            solution_rating = min(solution_count / len(solution_keywords), 1.0)
        
        # Check for solution markers in HTML
        solution_markers = [
            '.solution',
            '.accepted-answer',
            '.best-answer',
            '.marked-solution'
        ]
        
        for marker in solution_markers:
            if soup.select_one(marker):
                is_solution = True
                solution_rating = max(solution_rating, 0.8)
                break
        
        return is_solution, solution_rating
    
    def _extract_related_software(self, content: str) -> List[str]:
        """Extract related software from content"""
        software_list = []
        
        # Common Agilent software
        agilent_software = [
            'OpenLab CDS', 'OpenLab ECM', 'OpenLab ELN', 'OpenLab Server',
            'MassHunter', 'VNMRJ', 'VNMR', 'ChemStation', 'OpenLAB',
            'Agilent 1290', 'Agilent 1260', 'Agilent 1100', 'Agilent 7890',
            'Agilent 5977', 'Agilent 7000', 'Agilent 7200'
        ]
        
        content_lower = content.lower()
        for software in agilent_software:
            if software.lower() in content_lower:
                software_list.append(software)
        
        return list(set(software_list))
    
    def _extract_related_issues(self, content: str) -> List[str]:
        """Extract related issues from content"""
        issues = []
        
        # Common issue patterns
        issue_patterns = [
            r'error\s+(\w+)',
            r'problem\s+with\s+(\w+)',
            r'issue\s+with\s+(\w+)',
            r'failing\s+(\w+)',
            r'not\s+working\s+(\w+)'
        ]
        
        for pattern in issue_patterns:
            matches = re.findall(pattern, content.lower())
            issues.extend(matches)
        
        return list(set(issues))
    
    def _calculate_engagement_score(self, views: int, replies: int, likes: int) -> float:
        """Calculate engagement score"""
        # Weighted scoring
        score = (views * 0.1) + (replies * 2) + (likes * 3)
        return min(score / 100, 1.0)  # Normalize to 0-1
    
    def _calculate_quality_score(self, content: str, author_reputation: int, is_solution: bool) -> float:
        """Calculate quality score"""
        score = 0.0
        
        # Content length score
        if len(content) > 200:
            score += 0.2
        elif len(content) > 100:
            score += 0.1
        
        # Author reputation score
        if author_reputation > 100:
            score += 0.3
        elif author_reputation > 50:
            score += 0.2
        elif author_reputation > 10:
            score += 0.1
        
        # Solution status score
        if is_solution:
            score += 0.3
        
        # Content quality indicators
        quality_indicators = ['step', 'solution', 'fix', 'workaround', 'troubleshooting']
        indicator_count = sum(1 for indicator in quality_indicators if indicator in content.lower())
        score += min(indicator_count * 0.1, 0.2)
        
        return min(score, 1.0)
    
    def _is_valid_post(self, post: ForumPost) -> bool:
        """Check if post meets quality criteria"""
        # Minimum content length
        if len(post.content) < self.config.min_content_length:
            return False
        
        # Minimum author reputation
        if post.author_reputation < self.config.min_author_reputation:
            return False
        
        # Must have some engagement
        if post.views == 0 and post.replies == 0:
            return False
        
        return True
    
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


class ForumProcessor:
    """Process scraped forum data and integrate with document management system"""
    
    def __init__(self):
        self.rag_service = None  # Will be initialized when needed
    
    def process_forum_posts(self, forum_posts: List[ForumPost]) -> Dict[str, Any]:
        """Process forum posts and create document entries"""
        logger.info(f"Processing {len(forum_posts)} forum posts")
        
        results = {
            'processed': 0,
            'created': 0,
            'updated': 0,
            'errors': 0,
            'skipped': 0
        }
        
        for forum_post in forum_posts:
            try:
                # Check if this post already exists
                existing_doc = self._find_existing_document(forum_post.post_id)
                
                if existing_doc:
                    # Update existing document
                    self._update_document(existing_doc, forum_post)
                    results['updated'] += 1
                else:
                    # Create new document
                    self._create_document(forum_post)
                    results['created'] += 1
                
                results['processed'] += 1
                
            except Exception as e:
                logger.error(f"Error processing forum post {forum_post.post_id}: {e}")
                results['errors'] += 1
        
        logger.info(f"Forum processing completed: {results}")
        return results
    
    def _find_existing_document(self, post_id: str) -> Optional[DocumentFile]:
        """Find existing document by post ID"""
        try:
            # Look for documents with this post ID in metadata
            documents = DocumentFile.objects.filter(
                metadata__icontains=f'"post_id": "{post_id}"'
            )
            return documents.first()
        except Exception as e:
            logger.error(f"Error finding existing document for post {post_id}: {e}")
            return None
    
    def _create_document(self, forum_post: ForumPost) -> DocumentFile:
        """Create a new document from forum post"""
        try:
            # Create metadata
            metadata = {
                'post_id': forum_post.post_id,
                'author': forum_post.author,
                'author_reputation': forum_post.author_reputation,
                'views': forum_post.views,
                'replies': forum_post.replies,
                'likes': forum_post.likes,
                'tags': forum_post.tags,
                'category': forum_post.category,
                'is_solution': forum_post.is_solution,
                'solution_rating': forum_post.solution_rating,
                'related_software': forum_post.related_software,
                'related_issues': forum_post.related_issues,
                'thread_url': forum_post.thread_url,
                'scraped_at': forum_post.metadata.get('scraped_at'),
                'document_type': 'COMMUNITY_SOLUTION',
                'organization_mode': 'lab-informatics',
                'content_category': 'troubleshooting',
                'quality_score': forum_post.metadata.get('quality_score', 0.5),
                'engagement_score': forum_post.metadata.get('engagement_score', 0.0),
                'search_tags': self._generate_search_tags(forum_post),
                'keywords': self._extract_keywords(forum_post)
            }
            
            # Create document file
            document = DocumentFile.objects.create(
                title=f"Forum: {forum_post.title}",
                filename=f"Forum_{forum_post.post_id}.html",
                file_type="HTML",
                file_size=len(forum_post.content),
                description=forum_post.content[:200],
                document_type="COMMUNITY_SOLUTION",
                metadata=json.dumps(metadata),
                uploaded_by=None,  # System upload
                page_count=1,
                created_at=forum_post.post_date,
                updated_at=forum_post.last_updated
            )
            
            # Create content chunks for RAG
            self._create_content_chunks(document, forum_post)
            
            logger.info(f"Created document for forum post {forum_post.post_id}")
            return document
            
        except Exception as e:
            logger.error(f"Error creating document for forum post {forum_post.post_id}: {e}")
            raise
    
    def _update_document(self, document: DocumentFile, forum_post: ForumPost):
        """Update existing document with new forum post data"""
        try:
            # Update document fields
            document.title = f"Forum: {forum_post.title}"
            document.description = forum_post.content[:200]
            document.updated_at = forum_post.last_updated
            
            # Update metadata
            metadata = json.loads(document.metadata) if document.metadata else {}
            metadata.update({
                'post_id': forum_post.post_id,
                'views': forum_post.views,
                'replies': forum_post.replies,
                'likes': forum_post.likes,
                'is_solution': forum_post.is_solution,
                'solution_rating': forum_post.solution_rating,
                'updated_at': forum_post.last_updated.isoformat(),
                'quality_score': forum_post.metadata.get('quality_score', 0.5),
                'engagement_score': forum_post.metadata.get('engagement_score', 0.0),
            })
            
            document.metadata = json.dumps(metadata)
            document.save()
            
            # Update content chunks
            self._update_content_chunks(document, forum_post)
            
            logger.info(f"Updated document for forum post {forum_post.post_id}")
            
        except Exception as e:
            logger.error(f"Error updating document for forum post {forum_post.post_id}: {e}")
            raise
    
    def _create_content_chunks(self, document: DocumentFile, forum_post: ForumPost):
        """Create content chunks for RAG indexing"""
        try:
            # Create chunks for different sections
            chunks_data = [
                {
                    'content': f"Title: {forum_post.title}\nAuthor: {forum_post.author}\nContent: {forum_post.content}",
                    'section': 'main_content'
                },
                {
                    'content': f"Related Software: {'; '.join(forum_post.related_software)}",
                    'section': 'related_software'
                },
                {
                    'content': f"Related Issues: {'; '.join(forum_post.related_issues)}",
                    'section': 'related_issues'
                },
                {
                    'content': f"Tags: {'; '.join(forum_post.tags)}",
                    'section': 'tags'
                }
            ]
            
            for chunk_data in chunks_data:
                if chunk_data['content'].strip():
                    # Create uploaded file entry
                    uploaded_file = UploadedFile.objects.create(
                        filename=f"Forum_{forum_post.post_id}_{chunk_data['section']}.txt",
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
                            'post_id': forum_post.post_id,
                            'author': forum_post.author,
                            'is_solution': forum_post.is_solution,
                            'solution_rating': forum_post.solution_rating
                        })
                    )
            
            logger.info(f"Created content chunks for forum post {forum_post.post_id}")
            
        except Exception as e:
            logger.error(f"Error creating content chunks for forum post {forum_post.post_id}: {e}")
            raise
    
    def _update_content_chunks(self, document: DocumentFile, forum_post: ForumPost):
        """Update existing content chunks"""
        try:
            # Delete existing chunks
            DocumentChunk.objects.filter(
                uploaded_file__filename__startswith=f"Forum_{forum_post.post_id}_"
            ).delete()
            
            # Recreate chunks
            self._create_content_chunks(document, forum_post)
            
        except Exception as e:
            logger.error(f"Error updating content chunks for forum post {forum_post.post_id}: {e}")
            raise
    
    def _generate_search_tags(self, forum_post: ForumPost) -> List[str]:
        """Generate search tags for forum post"""
        tags = []
        
        # Add category tags
        if forum_post.category:
            tags.append(forum_post.category.lower().replace(' ', '_'))
        
        # Add software tags
        for software in forum_post.related_software:
            tags.append(software.lower().replace(' ', '_'))
        
        # Add issue tags
        for issue in forum_post.related_issues:
            tags.append(issue.lower().replace(' ', '_'))
        
        # Add solution tags
        if forum_post.is_solution:
            tags.append('solution')
            tags.append('resolved')
        
        # Add engagement tags
        if forum_post.engagement_score > 0.7:
            tags.append('popular')
        if forum_post.solution_rating > 0.8:
            tags.append('high_quality')
        
        return list(set(tags))
    
    def _extract_keywords(self, forum_post: ForumPost) -> List[str]:
        """Extract keywords from forum post"""
        keywords = []
        
        # Extract from title
        if forum_post.title:
            keywords.extend(forum_post.title.lower().split())
        
        # Extract from content
        if forum_post.content:
            keywords.extend(forum_post.content.lower().split())
        
        # Extract from tags
        for tag in forum_post.tags:
            keywords.extend(tag.lower().split())
        
        # Filter and clean keywords
        keywords = [word.strip('.,!?;:') for word in keywords if len(word) > 3]
        keywords = list(set(keywords))  # Remove duplicates
        
        return keywords[:20]  # Limit to 20 keywords


# Example usage and testing
if __name__ == "__main__":
    # Create forum scraper
    scraper = ForumScraper()
    
    # Scrape forum posts
    forum_posts = scraper.scrape_all_forums()
    print(f"Scraped {len(forum_posts)} forum posts")
    
    # Process posts
    processor = ForumProcessor()
    results = processor.process_forum_posts(forum_posts)
    print(f"Processing results: {results}")
