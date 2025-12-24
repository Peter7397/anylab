"""
GitHub Views Module

This module contains all GitHub scanner related views including
repository scanning, file processing, and analytics.
"""

import logging
import json
from django.core.cache import cache
from django.utils import timezone
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework import status

from ..models import DocumentFile
from ..github_scanner import GitHubScanner, GitHubProcessor, GitHubConfig
from .base_views import (
    BaseViewMixin, success_response, error_response, bad_request_response,
    internal_error_response
)

logger = logging.getLogger(__name__)

# Initialize GitHub scanner and processor
github_scanner = GitHubScanner()
github_processor = GitHubProcessor()


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def scan_github_repositories(request):
    """Scan GitHub repositories and process them"""
    try:
        BaseViewMixin.log_request(request, 'scan_github_repositories')
        
        # Get scanning configuration from request
        config_data = request.data.get('config', {})
        config = GitHubConfig(
            github_token=config_data.get('github_token'),
            search_queries=config_data.get('search_queries', [
                "agilent", "openlab", "masshunter", "chemstation", "vnmrj"
            ]),
            max_repos_per_query=config_data.get('max_repos_per_query', 100),
            max_files_per_repo=config_data.get('max_files_per_repo', 500),
            delay_between_requests=config_data.get('delay_between_requests', 1.0),
            timeout=config_data.get('timeout', 30),
            retry_attempts=config_data.get('retry_attempts', 3),
            min_stars=config_data.get('min_stars', 5),
            min_size=config_data.get('min_size', 1000),
            max_size=config_data.get('max_size', 100 * 1024 * 1024)
        )
        
        # Create scanner with custom config
        scanner = GitHubScanner(config)
        
        # Scan repositories
        logger.info("Starting GitHub repository scanning")
        repositories = scanner.scan_all_repositories()
        
        if not repositories:
            return success_response("No repositories found", {
                'scraped_count': 0,
                'processed_count': 0
            })
        
        # Process repositories
        logger.info(f"Processing {len(repositories)} repositories")
        processing_results = github_processor.process_repositories(repositories)
        
        result = {
            'scraped_count': len(repositories),
            'processing_results': processing_results,
            'scraped_at': timezone.now().isoformat()
        }
        
        BaseViewMixin.log_response(result, 'scan_github_repositories')
        return success_response("GitHub scanning completed successfully", result)
        
    except Exception as e:
        return BaseViewMixin.handle_error(e, 'scan_github_repositories')


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def scan_repository_files(request):
    """Scan files in a specific repository"""
    try:
        BaseViewMixin.log_request(request, 'scan_repository_files')
        
        repository_url = request.data.get('repository_url')
        if not repository_url:
            return bad_request_response('Repository URL is required')
        
        # Extract repository name from URL
        repo_name = repository_url.replace('https://github.com/', '').replace('https://github.com/', '')
        if not repo_name:
            return bad_request_response('Invalid repository URL')
        
        # Get scanning configuration from request
        config_data = request.data.get('config', {})
        config = GitHubConfig(
            github_token=config_data.get('github_token'),
            max_files_per_repo=config_data.get('max_files_per_repo', 500),
            delay_between_requests=config_data.get('delay_between_requests', 1.0)
        )
        
        # Create scanner with custom config
        scanner = GitHubScanner(config)
        
        # Create a mock repository object for scanning
        from ..github_scanner import GitHubRepository
        mock_repo = GitHubRepository(
            repo_id="temp",
            name=repo_name.split('/')[-1],
            full_name=repo_name,
            description="",
            url=repository_url,
            clone_url="",
            language="",
            languages=[],
            topics=[],
            stars=0,
            forks=0,
            watchers=0,
            size=0,
            created_at=timezone.now(),
            updated_at=timezone.now(),
            pushed_at=timezone.now(),
            owner=repo_name.split('/')[0],
            owner_type="",
            is_fork=False,
            has_issues=False,
            has_wiki=False,
            has_pages=False,
            license=None,
            default_branch="main",
            readme_content="",
            files_count=0,
            commits_count=0,
            releases_count=0,
            issues_count=0,
            pull_requests_count=0
        )
        
        # Scan repository files
        logger.info(f"Scanning files in repository: {repo_name}")
        files = scanner.scan_repository_files(mock_repo)
        
        if not files:
            return success_response("No files found in repository", {
                'scraped_count': 0,
                'processed_count': 0
            })
        
        # Process files
        logger.info(f"Processing {len(files)} files")
        processing_results = github_processor.process_files(files)
        
        result = {
            'scraped_count': len(files),
            'processing_results': processing_results,
            'scraped_at': timezone.now().isoformat()
        }
        
        BaseViewMixin.log_response(result, 'scan_repository_files')
        return success_response("Repository file scanning completed successfully", result)
        
    except Exception as e:
        return BaseViewMixin.handle_error(e, 'scan_repository_files')


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def get_github_scanning_status(request):
    """Get current GitHub scanning status and statistics"""
    try:
        BaseViewMixin.log_request(request, 'get_github_scanning_status')
        
        # Get GitHub documents count
        github_documents = DocumentFile.objects.filter(document_type__in=['GITHUB_REPOSITORY', 'GITHUB_FILE'])
        total_github_count = github_documents.count()
        
        # Get repository documents count
        repo_documents = DocumentFile.objects.filter(document_type='GITHUB_REPOSITORY')
        total_repo_count = repo_documents.count()
        
        # Get file documents count
        file_documents = DocumentFile.objects.filter(document_type='GITHUB_FILE')
        total_file_count = file_documents.count()
        
        # Get recent GitHub documents
        recent_github = github_documents.order_by('-created_at')[:10]
        recent_github_data = [
            {
                'id': doc.id,
                'title': doc.title,
                'created_at': doc.created_at.isoformat() if doc.created_at else None,
                'metadata': json.loads(doc.metadata) if doc.metadata else {}
            }
            for doc in recent_github
        ]
        
        # Get GitHub statistics
        github_stats = {
            'total_github_documents': total_github_count,
            'total_repositories': total_repo_count,
            'total_files': total_file_count,
            'recent_github_documents': recent_github_data,
            'last_scanning_run': cache.get('last_github_scanning_run'),
            'scanning_in_progress': cache.get('github_scanning_in_progress', False)
        }
        
        BaseViewMixin.log_response(github_stats, 'get_github_scanning_status')
        return success_response("GitHub scanning status retrieved successfully", github_stats)
        
    except Exception as e:
        return BaseViewMixin.handle_error(e, 'get_github_scanning_status')


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def schedule_github_scanning(request):
    """Schedule automatic GitHub scanning"""
    try:
        BaseViewMixin.log_request(request, 'schedule_github_scanning')
        
        schedule_config = request.data.get('schedule', {})
        
        # Schedule configuration
        schedule_data = {
            'enabled': schedule_config.get('enabled', True),
            'frequency': schedule_config.get('frequency', 'weekly'),  # daily, weekly, monthly
            'time': schedule_config.get('time', '04:00'),  # HH:MM format
            'max_repos_per_query': schedule_config.get('max_repos_per_query', 100),
            'max_files_per_repo': schedule_config.get('max_files_per_repo', 500),
            'notify_on_completion': schedule_config.get('notify_on_completion', True)
        }
        
        # Store schedule in cache
        cache.set('github_scanning_schedule', schedule_data, 86400 * 30)  # 30 days
        
        BaseViewMixin.log_response(schedule_data, 'schedule_github_scanning')
        return success_response("GitHub scanning schedule updated successfully", {'schedule': schedule_data})
        
    except Exception as e:
        return BaseViewMixin.handle_error(e, 'schedule_github_scanning')


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def get_github_scanning_schedule(request):
    """Get current GitHub scanning schedule"""
    try:
        BaseViewMixin.log_request(request, 'get_github_scanning_schedule')
        
        schedule = cache.get('github_scanning_schedule', {
            'enabled': False,
            'frequency': 'weekly',
            'time': '04:00',
            'max_repos_per_query': 100,
            'max_files_per_repo': 500,
            'notify_on_completion': True
        })
        
        BaseViewMixin.log_response(schedule, 'get_github_scanning_schedule')
        return success_response("GitHub scanning schedule retrieved successfully", {'schedule': schedule})
        
    except Exception as e:
        return BaseViewMixin.handle_error(e, 'get_github_scanning_schedule')


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def test_github_scanning(request):
    """Test GitHub scanning with a single repository"""
    try:
        BaseViewMixin.log_request(request, 'test_github_scanning')
        
        test_url = request.data.get('test_url')
        if not test_url:
            return bad_request_response('Test URL is required')
        
        # Extract repository name from URL
        repo_name = test_url.replace('https://github.com/', '').replace('https://github.com/', '')
        if not repo_name:
            return bad_request_response('Invalid repository URL')
        
        # Create scanner
        scanner = GitHubScanner()
        
        # Test scanning single repository
        url = f"{scanner.config.base_url}/repos/{repo_name}"
        response = scanner._make_request(url)
        if not response:
            return bad_request_response('Failed to fetch repository')
        
        # Parse the repository
        repo_data = response.json()
        repository = scanner._parse_repository(repo_data)
        if not repository:
            return bad_request_response('Failed to parse repository')
        
        result = {
            'repository': {
                'repo_id': repository.repo_id,
                'name': repository.name,
                'full_name': repository.full_name,
                'description': repository.description,
                'language': repository.language,
                'languages': repository.languages,
                'topics': repository.topics,
                'stars': repository.stars,
                'forks': repository.forks,
                'watchers': repository.watchers,
                'size': repository.size,
                'owner': repository.owner,
                'owner_type': repository.owner_type,
                'is_fork': repository.is_fork,
                'has_issues': repository.has_issues,
                'has_wiki': repository.has_wiki,
                'has_pages': repository.has_pages,
                'license': repository.license,
                'default_branch': repository.default_branch,
                'files_count': repository.files_count,
                'commits_count': repository.commits_count,
                'releases_count': repository.releases_count,
                'issues_count': repository.issues_count,
                'pull_requests_count': repository.pull_requests_count,
                'metadata': repository.metadata
            }
        }
        
        BaseViewMixin.log_response(result, 'test_github_scanning')
        return success_response("GitHub scanning test successful", result)
        
    except Exception as e:
        return BaseViewMixin.handle_error(e, 'test_github_scanning')


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def get_github_analytics(request):
    """Get analytics for GitHub content"""
    try:
        BaseViewMixin.log_request(request, 'get_github_analytics')
        
        # Get GitHub documents count
        github_documents = DocumentFile.objects.filter(document_type__in=['GITHUB_REPOSITORY', 'GITHUB_FILE'])
        total_github_count = github_documents.count()
        
        # Get repository documents count
        repo_documents = DocumentFile.objects.filter(document_type='GITHUB_REPOSITORY')
        total_repo_count = repo_documents.count()
        
        # Get file documents count
        file_documents = DocumentFile.objects.filter(document_type='GITHUB_FILE')
        total_file_count = file_documents.count()
        
        # Get language distribution
        language_stats = {}
        for doc in repo_documents:
            if doc.metadata:
                try:
                    metadata = json.loads(doc.metadata)
                    language = metadata.get('language', 'Unknown')
                    language_stats[language] = language_stats.get(language, 0) + 1
                except (json.JSONDecodeError, TypeError):
                    continue
        
        # Get recent GitHub documents
        recent_github = github_documents.order_by('-created_at')[:10]
        recent_github_data = [
            {
                'id': doc.id,
                'title': doc.title,
                'created_at': doc.created_at.isoformat() if doc.created_at else None,
                'metadata': json.loads(doc.metadata) if doc.metadata else {}
            }
            for doc in recent_github
        ]
        
        # Get GitHub statistics
        github_stats = {
            'total_github_documents': total_github_count,
            'total_repositories': total_repo_count,
            'total_files': total_file_count,
            'language_distribution': language_stats,
            'recent_github_documents': recent_github_data,
            'last_scanning_run': cache.get('last_github_scanning_run'),
            'scanning_in_progress': cache.get('github_scanning_in_progress', False)
        }
        
        BaseViewMixin.log_response(github_stats, 'get_github_analytics')
        return success_response("GitHub analytics retrieved successfully", github_stats)
        
    except Exception as e:
        return BaseViewMixin.handle_error(e, 'get_github_analytics')
