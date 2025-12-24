"""
GitHub Repository Scanner for AnyLab

This module provides automated scanning and integration of GitHub repositories
containing Agilent-related code, documentation, and troubleshooting resources.
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
import hashlib
from django.conf import settings
from django.core.cache import cache
from django.utils import timezone

from .metadata_schema import OrganizationMode, DocumentType, SeverityLevel, DualModeMetadata
from .models import DocumentFile, DocumentChunk, UploadedFile

logger = logging.getLogger(__name__)


@dataclass
class GitHubRepository:
    """GitHub repository data structure"""
    repo_id: str
    name: str
    full_name: str
    description: str
    url: str
    clone_url: str
    language: str
    languages: List[str]
    topics: List[str]
    stars: int
    forks: int
    watchers: int
    size: int
    created_at: datetime
    updated_at: datetime
    pushed_at: datetime
    owner: str
    owner_type: str
    is_fork: bool
    has_issues: bool
    has_wiki: bool
    has_pages: bool
    license: Optional[str]
    default_branch: str
    readme_content: str
    files_count: int
    commits_count: int
    releases_count: int
    issues_count: int
    pull_requests_count: int
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class GitHubFile:
    """GitHub file data structure"""
    file_id: str
    name: str
    path: str
    content: str
    size: int
    sha: str
    url: str
    download_url: str
    type: str  # file, dir
    language: str
    encoding: str
    content_type: str
    repository: str
    branch: str
    last_modified: datetime
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class GitHubConfig:
    """Configuration for GitHub scanning"""
    github_token: Optional[str] = None
    base_url: str = "https://api.github.com"
    search_queries: List[str] = field(default_factory=lambda: [
        "agilent",
        "openlab",
        "masshunter",
        "chemstation",
        "vnmrj",
        "agilent-technologies",
        "lab-informatics",
        "chromatography",
        "mass-spectrometry"
    ])
    max_repos_per_query: int = 100
    max_files_per_repo: int = 500
    delay_between_requests: float = 1.0
    timeout: int = 30
    retry_attempts: int = 3
    user_agent: str = "AnyLab-GitHub-Scanner/1.0"
    cache_duration: int = 3600  # 1 hour
    min_stars: int = 5
    min_size: int = 1000  # bytes
    max_size: int = 100 * 1024 * 1024  # 100MB
    file_extensions: List[str] = field(default_factory=lambda: [
        '.md', '.txt', '.rst', '.py', '.js', '.ts', '.java', '.cpp', '.c',
        '.h', '.hpp', '.cs', '.php', '.rb', '.go', '.rs', '.swift', '.kt',
        '.scala', '.sh', '.bat', '.ps1', '.yml', '.yaml', '.json', '.xml',
        '.html', '.css', '.scss', '.sass', '.less', '.sql', '.r', '.m',
        '.matlab', '.julia', '.lua', '.perl', '.pl', '.pm'
    ])


class GitHubScanner:
    """Main GitHub scanner class"""
    
    def __init__(self, config: Optional[GitHubConfig] = None):
        self.config = config or GitHubConfig()
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': self.config.user_agent,
            'Accept': 'application/vnd.github.v3+json',
            'Authorization': f'token {self.config.github_token}' if self.config.github_token else None
        })
        self.scanned_repos = set()
        self.processed_files = set()
        
    def scan_all_repositories(self) -> List[GitHubRepository]:
        """Scan all repositories matching search queries"""
        logger.info("Starting GitHub repository scanning")
        
        all_repos = []
        
        for query in self.config.search_queries:
            try:
                logger.info(f"Searching repositories for query: {query}")
                repos = self._search_repositories(query)
                all_repos.extend(repos)
                
                # Rate limiting between queries
                time.sleep(self.config.delay_between_requests * 2)
                
            except Exception as e:
                logger.error(f"Error searching repositories for query '{query}': {e}")
                continue
        
        # Remove duplicates based on repo ID
        unique_repos = {}
        for repo in all_repos:
            if repo.repo_id not in unique_repos:
                unique_repos[repo.repo_id] = repo
        
        final_repos = list(unique_repos.values())
        logger.info(f"Successfully scanned {len(final_repos)} unique repositories")
        return final_repos
    
    def _search_repositories(self, query: str) -> List[GitHubRepository]:
        """Search repositories using GitHub API"""
        repos = []
        page = 1
        per_page = 100
        
        while len(repos) < self.config.max_repos_per_query and page <= 10:  # GitHub API limit
            try:
                # Build search URL
                search_url = f"{self.config.base_url}/search/repositories"
                params = {
                    'q': query,
                    'sort': 'stars',
                    'order': 'desc',
                    'page': page,
                    'per_page': per_page
                }
                
                response = self._make_request(search_url, params=params)
                if not response:
                    break
                
                data = response.json()
                items = data.get('items', [])
                
                if not items:
                    break
                
                # Process each repository
                for item in items:
                    try:
                        repo = self._parse_repository(item)
                        if repo and self._is_valid_repository(repo):
                            repos.append(repo)
                    except Exception as e:
                        logger.error(f"Error parsing repository {item.get('full_name', 'unknown')}: {e}")
                        continue
                
                page += 1
                time.sleep(self.config.delay_between_requests)
                
            except Exception as e:
                logger.error(f"Error searching repositories page {page}: {e}")
                break
        
        return repos
    
    def _parse_repository(self, data: Dict[str, Any]) -> Optional[GitHubRepository]:
        """Parse repository data from GitHub API"""
        try:
            # Extract basic information
            repo_id = str(data.get('id', ''))
            name = data.get('name', '')
            full_name = data.get('full_name', '')
            description = data.get('description', '')
            url = data.get('html_url', '')
            clone_url = data.get('clone_url', '')
            
            # Extract language information
            language = data.get('language', '')
            languages = self._get_repository_languages(full_name)
            
            # Extract topics
            topics = data.get('topics', [])
            
            # Extract statistics
            stars = data.get('stargazers_count', 0)
            forks = data.get('forks_count', 0)
            watchers = data.get('watchers_count', 0)
            size = data.get('size', 0)
            
            # Extract dates
            created_at = self._parse_date(data.get('created_at'))
            updated_at = self._parse_date(data.get('updated_at'))
            pushed_at = self._parse_date(data.get('pushed_at'))
            
            # Extract owner information
            owner_data = data.get('owner', {})
            owner = owner_data.get('login', '')
            owner_type = owner_data.get('type', '')
            
            # Extract repository flags
            is_fork = data.get('fork', False)
            has_issues = data.get('has_issues', False)
            has_wiki = data.get('has_wiki', False)
            has_pages = data.get('has_pages', False)
            
            # Extract license
            license_data = data.get('license')
            license_name = license_data.get('name') if license_data else None
            
            # Extract default branch
            default_branch = data.get('default_branch', 'main')
            
            # Get README content
            readme_content = self._get_readme_content(full_name, default_branch)
            
            # Get additional statistics
            files_count, commits_count, releases_count, issues_count, pull_requests_count = self._get_repository_stats(full_name)
            
            # Build metadata
            metadata = {
                'scraped_at': timezone.now().isoformat(),
                'scanner_version': '1.0',
                'search_query': self._get_search_query_for_repo(full_name),
                'relevance_score': self._calculate_relevance_score(data),
                'quality_score': self._calculate_quality_score(data),
                'maintenance_score': self._calculate_maintenance_score(data),
                'documentation_score': self._calculate_documentation_score(data)
            }
            
            return GitHubRepository(
                repo_id=repo_id,
                name=name,
                full_name=full_name,
                description=description,
                url=url,
                clone_url=clone_url,
                language=language,
                languages=languages,
                topics=topics,
                stars=stars,
                forks=forks,
                watchers=watchers,
                size=size,
                created_at=created_at,
                updated_at=updated_at,
                pushed_at=pushed_at,
                owner=owner,
                owner_type=owner_type,
                is_fork=is_fork,
                has_issues=has_issues,
                has_wiki=has_wiki,
                has_pages=has_pages,
                license=license_name,
                default_branch=default_branch,
                readme_content=readme_content,
                files_count=files_count,
                commits_count=commits_count,
                releases_count=releases_count,
                issues_count=issues_count,
                pull_requests_count=pull_requests_count,
                metadata=metadata
            )
            
        except Exception as e:
            logger.error(f"Error parsing repository data: {e}")
            return None
    
    def _get_repository_languages(self, full_name: str) -> List[str]:
        """Get repository languages from GitHub API"""
        try:
            url = f"{self.config.base_url}/repos/{full_name}/languages"
            response = self._make_request(url)
            if response:
                data = response.json()
                return list(data.keys())
        except Exception as e:
            logger.error(f"Error getting languages for {full_name}: {e}")
        return []
    
    def _get_readme_content(self, full_name: str, branch: str) -> str:
        """Get README content from repository"""
        try:
            url = f"{self.config.base_url}/repos/{full_name}/readme"
            params = {'ref': branch}
            response = self._make_request(url, params=params)
            if response:
                data = response.json()
                content = data.get('content', '')
                encoding = data.get('encoding', 'base64')
                
                if encoding == 'base64':
                    import base64
                    return base64.b64decode(content).decode('utf-8')
                else:
                    return content
        except Exception as e:
            logger.error(f"Error getting README for {full_name}: {e}")
        return ""
    
    def _get_repository_stats(self, full_name: str) -> Tuple[int, int, int, int, int]:
        """Get additional repository statistics"""
        files_count = 0
        commits_count = 0
        releases_count = 0
        issues_count = 0
        pull_requests_count = 0
        
        try:
            # Get commits count
            url = f"{self.config.base_url}/repos/{full_name}/commits"
            response = self._make_request(url, params={'per_page': 1})
            if response:
                commits_count = int(response.headers.get('X-Total-Count', 0))
            
            # Get releases count
            url = f"{self.config.base_url}/repos/{full_name}/releases"
            response = self._make_request(url, params={'per_page': 1})
            if response:
                releases_count = int(response.headers.get('X-Total-Count', 0))
            
            # Get issues count
            url = f"{self.config.base_url}/repos/{full_name}/issues"
            response = self._make_request(url, params={'per_page': 1, 'state': 'all'})
            if response:
                issues_count = int(response.headers.get('X-Total-Count', 0))
            
            # Get pull requests count
            url = f"{self.config.base_url}/repos/{full_name}/pulls"
            response = self._make_request(url, params={'per_page': 1, 'state': 'all'})
            if response:
                pull_requests_count = int(response.headers.get('X-Total-Count', 0))
            
            # Get files count (approximate)
            url = f"{self.config.base_url}/repos/{full_name}/git/trees/{full_name.split('/')[-1]}:HEAD"
            response = self._make_request(url, params={'recursive': '1'})
            if response:
                data = response.json()
                files_count = len(data.get('tree', []))
            
        except Exception as e:
            logger.error(f"Error getting stats for {full_name}: {e}")
        
        return files_count, commits_count, releases_count, issues_count, pull_requests_count
    
    def _parse_date(self, date_str: str) -> datetime:
        """Parse GitHub date string"""
        if not date_str:
            return timezone.now()
        
        try:
            return datetime.fromisoformat(date_str.replace('Z', '+00:00'))
        except ValueError:
            return timezone.now()
    
    def _get_search_query_for_repo(self, full_name: str) -> str:
        """Determine which search query found this repository"""
        for query in self.config.search_queries:
            if query.lower() in full_name.lower():
                return query
        return self.config.search_queries[0]
    
    def _calculate_relevance_score(self, data: Dict[str, Any]) -> float:
        """Calculate relevance score for repository"""
        score = 0.0
        
        # Name relevance
        name = data.get('name', '').lower()
        full_name = data.get('full_name', '').lower()
        
        for query in self.config.search_queries:
            if query.lower() in name or query.lower() in full_name:
                score += 0.3
        
        # Description relevance
        description = data.get('description', '').lower()
        for query in self.config.search_queries:
            if query.lower() in description:
                score += 0.2
        
        # Topics relevance
        topics = data.get('topics', [])
        for topic in topics:
            for query in self.config.search_queries:
                if query.lower() in topic.lower():
                    score += 0.1
        
        return min(score, 1.0)
    
    def _calculate_quality_score(self, data: Dict[str, Any]) -> float:
        """Calculate quality score for repository"""
        score = 0.0
        
        # Stars score
        stars = data.get('stargazers_count', 0)
        if stars > 100:
            score += 0.3
        elif stars > 50:
            score += 0.2
        elif stars > 10:
            score += 0.1
        
        # Forks score
        forks = data.get('forks_count', 0)
        if forks > 50:
            score += 0.2
        elif forks > 10:
            score += 0.1
        
        # Size score (not too small, not too large)
        size = data.get('size', 0)
        if 1000 < size < 100000:  # 1KB to 100MB
            score += 0.1
        
        # Has issues and wiki
        if data.get('has_issues', False):
            score += 0.1
        if data.get('has_wiki', False):
            score += 0.1
        
        # License
        if data.get('license'):
            score += 0.1
        
        return min(score, 1.0)
    
    def _calculate_maintenance_score(self, data: Dict[str, Any]) -> float:
        """Calculate maintenance score for repository"""
        score = 0.0
        
        # Recent activity
        updated_at = self._parse_date(data.get('updated_at'))
        days_since_update = (timezone.now() - updated_at).days
        
        if days_since_update < 30:
            score += 0.4
        elif days_since_update < 90:
            score += 0.3
        elif days_since_update < 365:
            score += 0.2
        
        # Has recent push
        pushed_at = self._parse_date(data.get('pushed_at'))
        days_since_push = (timezone.now() - pushed_at).days
        
        if days_since_push < 7:
            score += 0.3
        elif days_since_push < 30:
            score += 0.2
        elif days_since_push < 90:
            score += 0.1
        
        # Not a fork (original work)
        if not data.get('fork', False):
            score += 0.2
        
        # Has issues enabled (community engagement)
        if data.get('has_issues', False):
            score += 0.1
        
        return min(score, 1.0)
    
    def _calculate_documentation_score(self, data: Dict[str, Any]) -> float:
        """Calculate documentation score for repository"""
        score = 0.0
        
        # Has description
        if data.get('description'):
            score += 0.2
        
        # Has topics
        if data.get('topics'):
            score += 0.2
        
        # Has wiki
        if data.get('has_wiki', False):
            score += 0.3
        
        # Has pages
        if data.get('has_pages', False):
            score += 0.3
        
        return min(score, 1.0)
    
    def _is_valid_repository(self, repo: GitHubRepository) -> bool:
        """Check if repository meets quality criteria"""
        # Minimum stars
        if repo.stars < self.config.min_stars:
            return False
        
        # Size constraints
        if repo.size < self.config.min_size or repo.size > self.config.max_size:
            return False
        
        # Must have some activity
        if repo.commits_count == 0:
            return False
        
        return True
    
    def scan_repository_files(self, repo: GitHubRepository) -> List[GitHubFile]:
        """Scan files in a specific repository"""
        logger.info(f"Scanning files in repository: {repo.full_name}")
        
        files = []
        
        try:
            # Get repository tree
            url = f"{self.config.base_url}/repos/{repo.full_name}/git/trees/{repo.default_branch}"
            params = {'recursive': '1'}
            response = self._make_request(url, params=params)
            
            if not response:
                logger.error(f"Failed to get repository tree for {repo.full_name}")
                return files
            
            data = response.json()
            tree = data.get('tree', [])
            
            # Filter files
            file_items = [item for item in tree if item.get('type') == 'blob']
            
            # Process files
            for i, item in enumerate(file_items[:self.config.max_files_per_repo]):
                try:
                    file_path = item.get('path', '')
                    file_name = item.get('path', '').split('/')[-1]
                    
                    # Check file extension
                    if not any(file_name.endswith(ext) for ext in self.config.file_extensions):
                        continue
                    
                    # Get file content
                    file_content = self._get_file_content(repo.full_name, file_path, repo.default_branch)
                    if not file_content:
                        continue
                    
                    # Create file object
                    github_file = GitHubFile(
                        file_id=f"{repo.repo_id}_{file_path}",
                        name=file_name,
                        path=file_path,
                        content=file_content,
                        size=item.get('size', 0),
                        sha=item.get('sha', ''),
                        url=item.get('url', ''),
                        download_url=item.get('url', ''),
                        type='file',
                        language=self._detect_language(file_name),
                        encoding='utf-8',
                        content_type=self._detect_content_type(file_name),
                        repository=repo.full_name,
                        branch=repo.default_branch,
                        last_modified=repo.updated_at,
                        metadata={
                            'repository_id': repo.repo_id,
                            'repository_name': repo.name,
                            'repository_url': repo.url,
                            'scanned_at': timezone.now().isoformat()
                        }
                    )
                    
                    files.append(github_file)
                    
                    # Rate limiting
                    if i % 10 == 0:
                        time.sleep(self.config.delay_between_requests)
                    
                except Exception as e:
                    logger.error(f"Error processing file {item.get('path', 'unknown')}: {e}")
                    continue
            
            logger.info(f"Scanned {len(files)} files from {repo.full_name}")
            
        except Exception as e:
            logger.error(f"Error scanning files in {repo.full_name}: {e}")
        
        return files
    
    def _get_file_content(self, full_name: str, file_path: str, branch: str) -> str:
        """Get file content from GitHub"""
        try:
            url = f"{self.config.base_url}/repos/{full_name}/contents/{file_path}"
            params = {'ref': branch}
            response = self._make_request(url, params=params)
            
            if not response:
                return ""
            
            data = response.json()
            content = data.get('content', '')
            encoding = data.get('encoding', 'base64')
            
            if encoding == 'base64':
                import base64
                return base64.b64decode(content).decode('utf-8')
            else:
                return content
                
        except Exception as e:
            logger.error(f"Error getting file content for {file_path}: {e}")
            return ""
    
    def _detect_language(self, filename: str) -> str:
        """Detect programming language from filename"""
        language_map = {
            '.py': 'Python',
            '.js': 'JavaScript',
            '.ts': 'TypeScript',
            '.java': 'Java',
            '.cpp': 'C++',
            '.c': 'C',
            '.h': 'C',
            '.hpp': 'C++',
            '.cs': 'C#',
            '.php': 'PHP',
            '.rb': 'Ruby',
            '.go': 'Go',
            '.rs': 'Rust',
            '.swift': 'Swift',
            '.kt': 'Kotlin',
            '.scala': 'Scala',
            '.sh': 'Shell',
            '.bat': 'Batch',
            '.ps1': 'PowerShell',
            '.yml': 'YAML',
            '.yaml': 'YAML',
            '.json': 'JSON',
            '.xml': 'XML',
            '.html': 'HTML',
            '.css': 'CSS',
            '.scss': 'SCSS',
            '.sass': 'Sass',
            '.less': 'Less',
            '.sql': 'SQL',
            '.r': 'R',
            '.m': 'MATLAB',
            '.matlab': 'MATLAB',
            '.julia': 'Julia',
            '.lua': 'Lua',
            '.perl': 'Perl',
            '.pl': 'Perl',
            '.pm': 'Perl',
            '.md': 'Markdown',
            '.txt': 'Text',
            '.rst': 'reStructuredText'
        }
        
        for ext, lang in language_map.items():
            if filename.endswith(ext):
                return lang
        
        return 'Unknown'
    
    def _detect_content_type(self, filename: str) -> str:
        """Detect content type from filename"""
        if filename.endswith(('.md', '.txt', '.rst')):
            return 'text/plain'
        elif filename.endswith(('.py', '.js', '.ts', '.java', '.cpp', '.c', '.h', '.hpp', '.cs', '.php', '.rb', '.go', '.rs', '.swift', '.kt', '.scala', '.sh', '.bat', '.ps1')):
            return 'text/plain'
        elif filename.endswith(('.yml', '.yaml', '.json', '.xml')):
            return 'text/plain'
        elif filename.endswith(('.html', '.css', '.scss', '.sass', '.less')):
            return 'text/plain'
        elif filename.endswith(('.sql', '.r', '.m', '.matlab', '.julia', '.lua', '.perl', '.pl', '.pm')):
            return 'text/plain'
        else:
            return 'text/plain'
    
    def _make_request(self, url: str, params: Optional[Dict[str, Any]] = None) -> Optional[requests.Response]:
        """Make HTTP request with retry logic"""
        for attempt in range(self.config.retry_attempts):
            try:
                response = self.session.get(url, params=params, timeout=self.config.timeout)
                
                # Handle rate limiting
                if response.status_code == 403 and 'rate limit' in response.text.lower():
                    reset_time = int(response.headers.get('X-RateLimit-Reset', 0))
                    wait_time = max(reset_time - time.time(), 0) + 60
                    logger.warning(f"Rate limit exceeded. Waiting {wait_time} seconds...")
                    time.sleep(wait_time)
                    continue
                
                response.raise_for_status()
                return response
                
            except requests.exceptions.RequestException as e:
                logger.warning(f"Attempt {attempt + 1} failed for {url}: {e}")
                if attempt < self.config.retry_attempts - 1:
                    time.sleep(2 ** attempt)  # Exponential backoff
                else:
                    logger.error(f"All attempts failed for {url}")
                    return None
        
        return None


class GitHubProcessor:
    """Process scanned GitHub data and integrate with document management system"""
    
    def __init__(self):
        self.rag_service = None  # Will be initialized when needed
    
    def process_repositories(self, repositories: List[GitHubRepository]) -> Dict[str, Any]:
        """Process repositories and create document entries"""
        logger.info(f"Processing {len(repositories)} repositories")
        
        results = {
            'processed': 0,
            'created': 0,
            'updated': 0,
            'errors': 0,
            'skipped': 0
        }
        
        for repo in repositories:
            try:
                # Check if this repository already exists
                existing_doc = self._find_existing_document(repo.repo_id)
                
                if existing_doc:
                    # Update existing document
                    self._update_document(existing_doc, repo)
                    results['updated'] += 1
                else:
                    # Create new document
                    self._create_document(repo)
                    results['created'] += 1
                
                results['processed'] += 1
                
            except Exception as e:
                logger.error(f"Error processing repository {repo.repo_id}: {e}")
                results['errors'] += 1
        
        logger.info(f"Repository processing completed: {results}")
        return results
    
    def process_files(self, files: List[GitHubFile]) -> Dict[str, Any]:
        """Process files and create document entries"""
        logger.info(f"Processing {len(files)} files")
        
        results = {
            'processed': 0,
            'created': 0,
            'updated': 0,
            'errors': 0,
            'skipped': 0
        }
        
        for file in files:
            try:
                # Check if this file already exists
                existing_doc = self._find_existing_document(file.file_id)
                
                if existing_doc:
                    # Update existing document
                    self._update_document(existing_doc, file)
                    results['updated'] += 1
                else:
                    # Create new document
                    self._create_document(file)
                    results['created'] += 1
                
                results['processed'] += 1
                
            except Exception as e:
                logger.error(f"Error processing file {file.file_id}: {e}")
                results['errors'] += 1
        
        logger.info(f"File processing completed: {results}")
        return results
    
    def _find_existing_document(self, doc_id: str) -> Optional[DocumentFile]:
        """Find existing document by ID"""
        try:
            # Look for documents with this ID in metadata
            documents = DocumentFile.objects.filter(
                metadata__icontains=f'"doc_id": "{doc_id}"'
            )
            return documents.first()
        except Exception as e:
            logger.error(f"Error finding existing document for {doc_id}: {e}")
            return None
    
    def _create_document(self, item: Any) -> DocumentFile:
        """Create a new document from repository or file"""
        try:
            if isinstance(item, GitHubRepository):
                return self._create_repository_document(item)
            elif isinstance(item, GitHubFile):
                return self._create_file_document(item)
            else:
                raise ValueError(f"Unknown item type: {type(item)}")
                
        except Exception as e:
            logger.error(f"Error creating document: {e}")
            raise
    
    def _create_repository_document(self, repo: GitHubRepository) -> DocumentFile:
        """Create a new document from repository"""
        try:
            # Create metadata
            metadata = {
                'doc_id': repo.repo_id,
                'repository_name': repo.name,
                'repository_full_name': repo.full_name,
                'repository_url': repo.url,
                'clone_url': repo.clone_url,
                'language': repo.language,
                'languages': repo.languages,
                'topics': repo.topics,
                'stars': repo.stars,
                'forks': repo.forks,
                'watchers': repo.watchers,
                'size': repo.size,
                'owner': repo.owner,
                'owner_type': repo.owner_type,
                'is_fork': repo.is_fork,
                'has_issues': repo.has_issues,
                'has_wiki': repo.has_wiki,
                'has_pages': repo.has_pages,
                'license': repo.license,
                'default_branch': repo.default_branch,
                'files_count': repo.files_count,
                'commits_count': repo.commits_count,
                'releases_count': repo.releases_count,
                'issues_count': repo.issues_count,
                'pull_requests_count': repo.pull_requests_count,
                'scraped_at': repo.metadata.get('scraped_at'),
                'document_type': 'GITHUB_REPOSITORY',
                'organization_mode': 'lab-informatics',
                'content_category': 'code_repository',
                'quality_score': repo.metadata.get('quality_score', 0.5),
                'relevance_score': repo.metadata.get('relevance_score', 0.5),
                'maintenance_score': repo.metadata.get('maintenance_score', 0.5),
                'documentation_score': repo.metadata.get('documentation_score', 0.5),
                'search_tags': self._generate_repository_search_tags(repo),
                'keywords': self._extract_repository_keywords(repo)
            }
            
            # Create document file
            document = DocumentFile.objects.create(
                title=f"Repository: {repo.name}",
                filename=f"Repo_{repo.repo_id}.json",
                file_type="JSON",
                file_size=len(json.dumps(metadata)),
                description=repo.description,
                document_type="GITHUB_REPOSITORY",
                metadata=json.dumps(metadata),
                uploaded_by=None,  # System upload
                page_count=1,
                created_at=repo.created_at,
                updated_at=repo.updated_at
            )
            
            # Create content chunks for RAG
            self._create_repository_content_chunks(document, repo)
            
            logger.info(f"Created document for repository {repo.repo_id}")
            return document
            
        except Exception as e:
            logger.error(f"Error creating document for repository {repo.repo_id}: {e}")
            raise
    
    def _create_file_document(self, file: GitHubFile) -> DocumentFile:
        """Create a new document from file"""
        try:
            # Create metadata
            metadata = {
                'doc_id': file.file_id,
                'file_name': file.name,
                'file_path': file.path,
                'file_size': file.size,
                'file_sha': file.sha,
                'file_url': file.url,
                'download_url': file.download_url,
                'language': file.language,
                'content_type': file.content_type,
                'repository': file.repository,
                'branch': file.branch,
                'scraped_at': file.metadata.get('scanned_at'),
                'document_type': 'GITHUB_FILE',
                'organization_mode': 'lab-informatics',
                'content_category': 'code_file',
                'quality_score': self._calculate_file_quality_score(file),
                'search_tags': self._generate_file_search_tags(file),
                'keywords': self._extract_file_keywords(file)
            }
            
            # Create document file
            document = DocumentFile.objects.create(
                title=f"File: {file.name}",
                filename=f"File_{file.file_id}.txt",
                file_type="TEXT",
                file_size=file.size,
                description=file.content[:200],
                document_type="GITHUB_FILE",
                metadata=json.dumps(metadata),
                uploaded_by=None,  # System upload
                page_count=1,
                created_at=file.last_modified,
                updated_at=file.last_modified
            )
            
            # Create content chunks for RAG
            self._create_file_content_chunks(document, file)
            
            logger.info(f"Created document for file {file.file_id}")
            return document
            
        except Exception as e:
            logger.error(f"Error creating document for file {file.file_id}: {e}")
            raise
    
    def _update_document(self, document: DocumentFile, item: Any):
        """Update existing document"""
        try:
            if isinstance(item, GitHubRepository):
                self._update_repository_document(document, item)
            elif isinstance(item, GitHubFile):
                self._update_file_document(document, item)
            else:
                raise ValueError(f"Unknown item type: {type(item)}")
                
        except Exception as e:
            logger.error(f"Error updating document: {e}")
            raise
    
    def _update_repository_document(self, document: DocumentFile, repo: GitHubRepository):
        """Update existing repository document"""
        try:
            # Update document fields
            document.title = f"Repository: {repo.name}"
            document.description = repo.description
            document.updated_at = repo.updated_at
            
            # Update metadata
            metadata = json.loads(document.metadata) if document.metadata else {}
            metadata.update({
                'doc_id': repo.repo_id,
                'stars': repo.stars,
                'forks': repo.forks,
                'watchers': repo.watchers,
                'files_count': repo.files_count,
                'commits_count': repo.commits_count,
                'releases_count': repo.releases_count,
                'issues_count': repo.issues_count,
                'pull_requests_count': repo.pull_requests_count,
                'updated_at': repo.updated_at.isoformat(),
                'quality_score': repo.metadata.get('quality_score', 0.5),
                'relevance_score': repo.metadata.get('relevance_score', 0.5),
                'maintenance_score': repo.metadata.get('maintenance_score', 0.5),
                'documentation_score': repo.metadata.get('documentation_score', 0.5),
            })
            
            document.metadata = json.dumps(metadata)
            document.save()
            
            # Update content chunks
            self._update_repository_content_chunks(document, repo)
            
            logger.info(f"Updated document for repository {repo.repo_id}")
            
        except Exception as e:
            logger.error(f"Error updating document for repository {repo.repo_id}: {e}")
            raise
    
    def _update_file_document(self, document: DocumentFile, file: GitHubFile):
        """Update existing file document"""
        try:
            # Update document fields
            document.title = f"File: {file.name}"
            document.description = file.content[:200]
            document.updated_at = file.last_modified
            
            # Update metadata
            metadata = json.loads(document.metadata) if document.metadata else {}
            metadata.update({
                'doc_id': file.file_id,
                'file_size': file.size,
                'file_sha': file.sha,
                'updated_at': file.last_modified.isoformat(),
                'quality_score': self._calculate_file_quality_score(file),
            })
            
            document.metadata = json.dumps(metadata)
            document.save()
            
            # Update content chunks
            self._update_file_content_chunks(document, file)
            
            logger.info(f"Updated document for file {file.file_id}")
            
        except Exception as e:
            logger.error(f"Error updating document for file {file.file_id}: {e}")
            raise
    
    def _create_repository_content_chunks(self, document: DocumentFile, repo: GitHubRepository):
        """Create content chunks for repository"""
        try:
            # Create chunks for different sections
            chunks_data = [
                {
                    'content': f"Repository: {repo.name}\nDescription: {repo.description}\nURL: {repo.url}",
                    'section': 'overview'
                },
                {
                    'content': f"Languages: {'; '.join(repo.languages)}\nTopics: {'; '.join(repo.topics)}",
                    'section': 'technical_info'
                },
                {
                    'content': f"Stars: {repo.stars}\nForks: {repo.forks}\nWatchers: {repo.watchers}",
                    'section': 'statistics'
                },
                {
                    'content': repo.readme_content,
                    'section': 'readme'
                }
            ]
            
            for chunk_data in chunks_data:
                if chunk_data['content'].strip():
                    # Create uploaded file entry
                    uploaded_file = UploadedFile.objects.create(
                        filename=f"Repo_{repo.repo_id}_{chunk_data['section']}.txt",
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
                            'repository_id': repo.repo_id,
                            'repository_name': repo.name,
                            'language': repo.language
                        })
                    )
            
            logger.info(f"Created content chunks for repository {repo.repo_id}")
            
        except Exception as e:
            logger.error(f"Error creating content chunks for repository {repo.repo_id}: {e}")
            raise
    
    def _create_file_content_chunks(self, document: DocumentFile, file: GitHubFile):
        """Create content chunks for file"""
        try:
            # Create chunks for different sections
            chunks_data = [
                {
                    'content': f"File: {file.name}\nPath: {file.path}\nLanguage: {file.language}\nContent:\n{file.content}",
                    'section': 'file_content'
                }
            ]
            
            for chunk_data in chunks_data:
                if chunk_data['content'].strip():
                    # Create uploaded file entry
                    uploaded_file = UploadedFile.objects.create(
                        filename=f"File_{file.file_id}_{chunk_data['section']}.txt",
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
                            'file_id': file.file_id,
                            'file_name': file.name,
                            'language': file.language,
                            'repository': file.repository
                        })
                    )
            
            logger.info(f"Created content chunks for file {file.file_id}")
            
        except Exception as e:
            logger.error(f"Error creating content chunks for file {file.file_id}: {e}")
            raise
    
    def _update_repository_content_chunks(self, document: DocumentFile, repo: GitHubRepository):
        """Update existing repository content chunks"""
        try:
            # Delete existing chunks
            DocumentChunk.objects.filter(
                uploaded_file__filename__startswith=f"Repo_{repo.repo_id}_"
            ).delete()
            
            # Recreate chunks
            self._create_repository_content_chunks(document, repo)
            
        except Exception as e:
            logger.error(f"Error updating content chunks for repository {repo.repo_id}: {e}")
            raise
    
    def _update_file_content_chunks(self, document: DocumentFile, file: GitHubFile):
        """Update existing file content chunks"""
        try:
            # Delete existing chunks
            DocumentChunk.objects.filter(
                uploaded_file__filename__startswith=f"File_{file.file_id}_"
            ).delete()
            
            # Recreate chunks
            self._create_file_content_chunks(document, file)
            
        except Exception as e:
            logger.error(f"Error updating content chunks for file {file.file_id}: {e}")
            raise
    
    def _calculate_file_quality_score(self, file: GitHubFile) -> float:
        """Calculate quality score for file"""
        score = 0.0
        
        # File size score
        if 100 < file.size < 10000:  # 100 bytes to 10KB
            score += 0.2
        elif 1000 < file.size < 100000:  # 1KB to 100KB
            score += 0.3
        
        # Language score
        if file.language in ['Python', 'JavaScript', 'TypeScript', 'Java', 'C++', 'C#']:
            score += 0.2
        elif file.language in ['Markdown', 'Text', 'YAML', 'JSON']:
            score += 0.1
        
        # Content quality
        if file.content and len(file.content) > 50:
            score += 0.3
        
        # File path score (not in hidden directories)
        if not file.path.startswith('.') and not file.path.startswith('node_modules'):
            score += 0.2
        
        return min(score, 1.0)
    
    def _generate_repository_search_tags(self, repo: GitHubRepository) -> List[str]:
        """Generate search tags for repository"""
        tags = []
        
        # Add language tags
        for lang in repo.languages:
            tags.append(lang.lower().replace(' ', '_'))
        
        # Add topic tags
        for topic in repo.topics:
            tags.append(topic.lower().replace(' ', '_'))
        
        # Add quality tags
        if repo.stars > 100:
            tags.append('popular')
        if repo.forks > 50:
            tags.append('well_forked')
        if repo.has_wiki:
            tags.append('documented')
        if repo.has_pages:
            tags.append('has_pages')
        
        # Add maintenance tags
        days_since_update = (timezone.now() - repo.updated_at).days
        if days_since_update < 30:
            tags.append('recently_updated')
        elif days_since_update < 365:
            tags.append('maintained')
        
        return list(set(tags))
    
    def _generate_file_search_tags(self, file: GitHubFile) -> List[str]:
        """Generate search tags for file"""
        tags = []
        
        # Add language tags
        if file.language:
            tags.append(file.language.lower().replace(' ', '_'))
        
        # Add file type tags
        if file.name.endswith('.md'):
            tags.append('documentation')
        elif file.name.endswith(('.py', '.js', '.ts', '.java', '.cpp', '.c')):
            tags.append('source_code')
        elif file.name.endswith(('.yml', '.yaml', '.json')):
            tags.append('configuration')
        elif file.name.endswith(('.txt', '.rst')):
            tags.append('text_file')
        
        # Add path tags
        if 'test' in file.path.lower():
            tags.append('test_file')
        if 'doc' in file.path.lower() or 'docs' in file.path.lower():
            tags.append('documentation')
        if 'example' in file.path.lower() or 'sample' in file.path.lower():
            tags.append('example')
        
        return list(set(tags))
    
    def _extract_repository_keywords(self, repo: GitHubRepository) -> List[str]:
        """Extract keywords from repository"""
        keywords = []
        
        # Extract from name
        if repo.name:
            keywords.extend(repo.name.lower().split())
        
        # Extract from description
        if repo.description:
            keywords.extend(repo.description.lower().split())
        
        # Extract from topics
        for topic in repo.topics:
            keywords.extend(topic.lower().split())
        
        # Filter and clean keywords
        keywords = [word.strip('.,!?;:') for word in keywords if len(word) > 3]
        keywords = list(set(keywords))  # Remove duplicates
        
        return keywords[:20]  # Limit to 20 keywords
    
    def _extract_file_keywords(self, file: GitHubFile) -> List[str]:
        """Extract keywords from file"""
        keywords = []
        
        # Extract from filename
        if file.name:
            keywords.extend(file.name.lower().split())
        
        # Extract from path
        if file.path:
            keywords.extend(file.path.lower().split())
        
        # Extract from content (first 1000 characters)
        if file.content:
            content_words = file.content[:1000].lower().split()
            keywords.extend(content_words)
        
        # Filter and clean keywords
        keywords = [word.strip('.,!?;:') for word in keywords if len(word) > 3]
        keywords = list(set(keywords))  # Remove duplicates
        
        return keywords[:20]  # Limit to 20 keywords


# Example usage and testing
if __name__ == "__main__":
    # Create GitHub scanner
    scanner = GitHubScanner()
    
    # Scan repositories
    repositories = scanner.scan_all_repositories()
    print(f"Scanned {len(repositories)} repositories")
    
    # Process repositories
    processor = GitHubProcessor()
    results = processor.process_repositories(repositories)
    print(f"Processing results: {results}")
    
    # Scan files from first repository
    if repositories:
        files = scanner.scan_repository_files(repositories[0])
        print(f"Scanned {len(files)} files from {repositories[0].name}")
        
        # Process files
        file_results = processor.process_files(files)
        print(f"File processing results: {file_results}")
