"""
User Contribution Dashboard System

This module provides a comprehensive dashboard for users to track and manage
their contributions including uploads, submissions, reviews, and analytics.
"""

import logging
from typing import Dict, Any, List, Optional, Tuple, Union
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from enum import Enum
from django.utils import timezone as django_timezone
from django.core.cache import cache
from django.db.models import Count, Sum, Avg, Q
from django.contrib.auth.models import User

logger = logging.getLogger(__name__)


class ContributionType(Enum):
    """Contribution type enumeration"""
    FILE_UPLOAD = "file_upload"
    URL_SUBMISSION = "url_submission"
    CONTENT_REVIEW = "content_review"
    METADATA_EDIT = "metadata_edit"
    CATEGORIZATION = "categorization"
    TRANSLATION = "translation"
    ANNOTATION = "annotation"
    COMMENT = "comment"
    RATING = "rating"
    SHARE = "share"
    DOWNLOAD = "download"
    VIEW = "view"
    SEARCH = "search"
    FEEDBACK = "feedback"
    BUG_REPORT = "bug_report"
    FEATURE_REQUEST = "feature_request"
    COMMUNITY_POST = "community_post"
    EXPERT_ANSWER = "expert_answer"
    TUTORIAL_CREATION = "tutorial_creation"
    DOCUMENTATION_UPDATE = "documentation_update"


class ContributionStatus(Enum):
    """Contribution status enumeration"""
    PENDING = "pending"
    APPROVED = "approved"
    REJECTED = "rejected"
    UNDER_REVIEW = "under_review"
    PUBLISHED = "published"
    ARCHIVED = "archived"
    DELETED = "deleted"
    DRAFT = "draft"
    SUBMITTED = "submitted"
    PROCESSING = "processing"
    COMPLETED = "completed"
    FAILED = "failed"


class UserRole(Enum):
    """User role enumeration"""
    VIEWER = "viewer"
    CONTRIBUTOR = "contributor"
    REVIEWER = "reviewer"
    MODERATOR = "moderator"
    ADMIN = "admin"
    EXPERT = "expert"
    TRANSLATOR = "translator"
    CURATOR = "curator"


class AchievementType(Enum):
    """Achievement type enumeration"""
    FIRST_CONTRIBUTION = "first_contribution"
    CONTRIBUTION_MILESTONE = "contribution_milestone"
    QUALITY_CONTRIBUTOR = "quality_contributor"
    EXPERT_REVIEWER = "expert_reviewer"
    COMMUNITY_HELPER = "community_helper"
    TRANSLATION_EXPERT = "translation_expert"
    DOCUMENTATION_MASTER = "documentation_master"
    TUTORIAL_CREATOR = "tutorial_creator"
    BUG_HUNTER = "bug_hunter"
    FEATURE_ADVOCATE = "feature_advocate"


@dataclass
class UserContribution:
    """User contribution structure"""
    id: str
    user_id: str
    contribution_type: ContributionType
    title: str
    description: Optional[str] = None
    content_id: Optional[str] = None
    file_path: Optional[str] = None
    url: Optional[str] = None
    status: ContributionStatus = ContributionStatus.PENDING
    points_earned: int = 0
    quality_score: float = 0.0
    review_count: int = 0
    approval_count: int = 0
    rejection_count: int = 0
    view_count: int = 0
    download_count: int = 0
    share_count: int = 0
    comment_count: int = 0
    rating_average: float = 0.0
    rating_count: int = 0
    tags: List[str] = field(default_factory=list)
    category: Optional[str] = None
    metadata: Dict[str, Any] = field(default_factory=dict)
    created_at: datetime = field(default_factory=lambda: django_timezone.now())
    updated_at: datetime = field(default_factory=lambda: django_timezone.now())
    reviewed_at: Optional[datetime] = None
    published_at: Optional[datetime] = None
    archived_at: Optional[datetime] = None


@dataclass
class UserProfile:
    """User profile structure"""
    user_id: str
    username: str
    email: str
    first_name: str
    last_name: str
    role: UserRole = UserRole.CONTRIBUTOR
    total_points: int = 0
    contribution_count: int = 0
    approved_contributions: int = 0
    rejected_contributions: int = 0
    pending_contributions: int = 0
    review_count: int = 0
    quality_score: float = 0.0
    reputation_score: float = 0.0
    expertise_areas: List[str] = field(default_factory=list)
    languages: List[str] = field(default_factory=list)
    timezone: str = "UTC"
    preferences: Dict[str, Any] = field(default_factory=dict)
    achievements: List[str] = field(default_factory=list)
    badges: List[str] = field(default_factory=list)
    joined_at: datetime = field(default_factory=lambda: django_timezone.now())
    last_active_at: datetime = field(default_factory=lambda: django_timezone.now())
    profile_updated_at: datetime = field(default_factory=lambda: django_timezone.now())


@dataclass
class ContributionAnalytics:
    """Contribution analytics structure"""
    user_id: str
    period: str  # daily, weekly, monthly, yearly
    start_date: datetime
    end_date: datetime
    total_contributions: int = 0
    contributions_by_type: Dict[str, int] = field(default_factory=dict)
    contributions_by_status: Dict[str, int] = field(default_factory=dict)
    total_points_earned: int = 0
    average_quality_score: float = 0.0
    total_views: int = 0
    total_downloads: int = 0
    total_shares: int = 0
    total_comments: int = 0
    average_rating: float = 0.0
    top_categories: List[str] = field(default_factory=list)
    top_tags: List[str] = field(default_factory=list)
    contribution_trend: List[Dict[str, Any]] = field(default_factory=list)
    quality_trend: List[Dict[str, Any]] = field(default_factory=list)
    engagement_trend: List[Dict[str, Any]] = field(default_factory=list)


@dataclass
class DashboardWidget:
    """Dashboard widget structure"""
    id: str
    name: str
    type: str  # chart, table, metric, list, progress
    title: str
    description: str
    data_source: str
    config: Dict[str, Any]
    position: Tuple[int, int]  # row, column
    size: Tuple[int, int]  # width, height
    refresh_interval: int = 300  # seconds
    enabled: bool = True
    user_specific: bool = True
    created_at: datetime = field(default_factory=lambda: django_timezone.now())
    updated_at: datetime = field(default_factory=lambda: django_timezone.now())


@dataclass
class UserAchievement:
    """User achievement structure"""
    id: str
    user_id: str
    achievement_type: AchievementType
    title: str
    description: str
    points_awarded: int
    badge_icon: str
    unlocked_at: datetime = field(default_factory=lambda: django_timezone.now())
    metadata: Dict[str, Any] = field(default_factory=dict)


class UserContributionDashboardManager:
    """User Contribution Dashboard Manager"""
    
    def __init__(self, config: Dict[str, Any] = None):
        """Initialize user contribution dashboard manager"""
        self.config = config or {}
        self.dashboard_enabled = self.config.get('dashboard_enabled', True)
        self.analytics_enabled = self.config.get('analytics_enabled', True)
        self.achievements_enabled = self.config.get('achievements_enabled', True)
        self.real_time_updates = self.config.get('real_time_updates', True)
        
        # Initialize components
        self.contributions = {}
        self.user_profiles = {}
        self.analytics = {}
        self.widgets = {}
        self.achievements = {}
        
        # Initialize dashboard
        self._initialize_dashboard()
        
        # Initialize analytics
        self._initialize_analytics()
        
        # Initialize achievements
        self._initialize_achievements()
        
        logger.info("User Contribution Dashboard Manager initialized")
    
    def _initialize_dashboard(self):
        """Initialize dashboard components"""
        try:
            # Initialize default widgets
            self._create_default_widgets()
            
            # Initialize dashboard layouts
            self._create_dashboard_layouts()
            
            logger.info("Dashboard components initialized")
            
        except Exception as e:
            logger.error(f"Error initializing dashboard: {e}")
            raise
    
    def _create_default_widgets(self):
        """Create default dashboard widgets"""
        try:
            widgets = [
                DashboardWidget(
                    id="contribution_summary",
                    name="Contribution Summary",
                    type="metric",
                    title="My Contributions",
                    description="Overview of your contributions",
                    data_source="user_contributions",
                    config={
                        "metrics": ["total_contributions", "approved_contributions", "pending_contributions", "total_points"]
                    },
                    position=(0, 0),
                    size=(2, 1)
                ),
                DashboardWidget(
                    id="contribution_trend",
                    name="Contribution Trend",
                    type="chart",
                    title="Contribution Trend",
                    description="Your contribution activity over time",
                    data_source="contribution_analytics",
                    config={
                        "chart_type": "line",
                        "x_axis": "date",
                        "y_axis": "count",
                        "period": "30_days"
                    },
                    position=(0, 2),
                    size=(3, 2)
                ),
                DashboardWidget(
                    id="quality_score",
                    name="Quality Score",
                    type="progress",
                    title="Quality Score",
                    description="Your content quality rating",
                    data_source="user_quality",
                    config={
                        "max_value": 100,
                        "color": "green"
                    },
                    position=(0, 5),
                    size=(1, 1)
                ),
                DashboardWidget(
                    id="recent_contributions",
                    name="Recent Contributions",
                    type="list",
                    title="Recent Contributions",
                    description="Your latest contributions",
                    data_source="recent_contributions",
                    config={
                        "limit": 10,
                        "show_status": True
                    },
                    position=(1, 0),
                    size=(2, 2)
                ),
                DashboardWidget(
                    id="contribution_types",
                    name="Contribution Types",
                    type="chart",
                    title="Contribution Types",
                    description="Breakdown by contribution type",
                    data_source="contribution_types",
                    config={
                        "chart_type": "pie",
                        "show_percentages": True
                    },
                    position=(1, 2),
                    size=(2, 2)
                ),
                DashboardWidget(
                    id="achievements",
                    name="Achievements",
                    type="list",
                    title="Achievements",
                    description="Your unlocked achievements",
                    data_source="user_achievements",
                    config={
                        "show_badges": True,
                        "limit": 5
                    },
                    position=(1, 4),
                    size=(2, 2)
                ),
                DashboardWidget(
                    id="engagement_metrics",
                    name="Engagement Metrics",
                    type="metric",
                    title="Engagement",
                    description="How your content is performing",
                    data_source="engagement_metrics",
                    config={
                        "metrics": ["total_views", "total_downloads", "total_shares", "average_rating"]
                    },
                    position=(2, 0),
                    size=(2, 1)
                ),
                DashboardWidget(
                    id="top_categories",
                    name="Top Categories",
                    type="list",
                    title="Top Categories",
                    description="Your most active categories",
                    data_source="top_categories",
                    config={
                        "limit": 5,
                        "show_counts": True
                    },
                    position=(2, 2),
                    size=(2, 1)
                ),
                DashboardWidget(
                    id="reputation_score",
                    name="Reputation Score",
                    type="metric",
                    title="Reputation",
                    description="Your community reputation",
                    data_source="reputation_score",
                    config={
                        "show_trend": True
                    },
                    position=(2, 4),
                    size=(2, 1)
                )
            ]
            
            for widget in widgets:
                self.widgets[widget.id] = widget
            
            logger.info("Default widgets created")
            
        except Exception as e:
            logger.error(f"Error creating default widgets: {e}")
    
    def _create_dashboard_layouts(self):
        """Create dashboard layouts"""
        try:
            self.dashboard_layouts = {
                "default": {
                    "name": "Default Layout",
                    "description": "Standard dashboard layout",
                    "widgets": [
                        "contribution_summary",
                        "contribution_trend",
                        "quality_score",
                        "recent_contributions",
                        "contribution_types",
                        "achievements",
                        "engagement_metrics",
                        "top_categories",
                        "reputation_score"
                    ],
                    "grid_size": (3, 6),
                    "responsive": True
                },
                "minimal": {
                    "name": "Minimal Layout",
                    "description": "Minimal dashboard layout",
                    "widgets": [
                        "contribution_summary",
                        "recent_contributions",
                        "quality_score"
                    ],
                    "grid_size": (2, 3),
                    "responsive": True
                },
                "detailed": {
                    "name": "Detailed Layout",
                    "description": "Detailed dashboard layout",
                    "widgets": [
                        "contribution_summary",
                        "contribution_trend",
                        "quality_score",
                        "recent_contributions",
                        "contribution_types",
                        "achievements",
                        "engagement_metrics",
                        "top_categories",
                        "reputation_score"
                    ],
                    "grid_size": (4, 6),
                    "responsive": True
                }
            }
            
            logger.info("Dashboard layouts created")
            
        except Exception as e:
            logger.error(f"Error creating dashboard layouts: {e}")
    
    def _initialize_analytics(self):
        """Initialize analytics components"""
        try:
            # Initialize analytics processors
            self.analytics_processors = {
                'contribution_analytics': self._process_contribution_analytics,
                'engagement_analytics': self._process_engagement_analytics,
                'quality_analytics': self._process_quality_analytics,
                'trend_analytics': self._process_trend_analytics,
                'comparison_analytics': self._process_comparison_analytics
            }
            
            logger.info("Analytics components initialized")
            
        except Exception as e:
            logger.error(f"Error initializing analytics: {e}")
            raise
    
    def _initialize_achievements(self):
        """Initialize achievements system"""
        try:
            # Initialize achievement definitions
            self.achievement_definitions = {
                AchievementType.FIRST_CONTRIBUTION: {
                    'title': 'First Contribution',
                    'description': 'Made your first contribution',
                    'points': 10,
                    'badge_icon': 'first_contribution.png',
                    'condition': {'min_contributions': 1}
                },
                AchievementType.CONTRIBUTION_MILESTONE: {
                    'title': 'Contribution Milestone',
                    'description': 'Reached a contribution milestone',
                    'points': 50,
                    'badge_icon': 'milestone.png',
                    'condition': {'min_contributions': 10}
                },
                AchievementType.QUALITY_CONTRIBUTOR: {
                    'title': 'Quality Contributor',
                    'description': 'Maintained high quality contributions',
                    'points': 100,
                    'badge_icon': 'quality.png',
                    'condition': {'min_quality_score': 80, 'min_contributions': 5}
                },
                AchievementType.EXPERT_REVIEWER: {
                    'title': 'Expert Reviewer',
                    'description': 'Completed many reviews',
                    'points': 75,
                    'badge_icon': 'reviewer.png',
                    'condition': {'min_reviews': 20}
                },
                AchievementType.COMMUNITY_HELPER: {
                    'title': 'Community Helper',
                    'description': 'Helped the community',
                    'points': 60,
                    'badge_icon': 'helper.png',
                    'condition': {'min_comments': 50, 'min_shares': 10}
                },
                AchievementType.TRANSLATION_EXPERT: {
                    'title': 'Translation Expert',
                    'description': 'Expert in translations',
                    'points': 80,
                    'badge_icon': 'translator.png',
                    'condition': {'min_translations': 10}
                },
                AchievementType.DOCUMENTATION_MASTER: {
                    'title': 'Documentation Master',
                    'description': 'Master of documentation',
                    'points': 90,
                    'badge_icon': 'documentation.png',
                    'condition': {'min_documentation_updates': 15}
                },
                AchievementType.TUTORIAL_CREATOR: {
                    'title': 'Tutorial Creator',
                    'description': 'Created helpful tutorials',
                    'points': 70,
                    'badge_icon': 'tutorial.png',
                    'condition': {'min_tutorials': 5}
                },
                AchievementType.BUG_HUNTER: {
                    'title': 'Bug Hunter',
                    'description': 'Found and reported bugs',
                    'points': 40,
                    'badge_icon': 'bug_hunter.png',
                    'condition': {'min_bug_reports': 10}
                },
                AchievementType.FEATURE_ADVOCATE: {
                    'title': 'Feature Advocate',
                    'description': 'Advocated for new features',
                    'points': 30,
                    'badge_icon': 'feature.png',
                    'condition': {'min_feature_requests': 5}
                }
            }
            
            logger.info("Achievements system initialized")
            
        except Exception as e:
            logger.error(f"Error initializing achievements: {e}")
            raise
    
    def create_contribution(self, user_id: str, contribution_data: Dict[str, Any]) -> UserContribution:
        """Create a new user contribution"""
        try:
            # Generate contribution ID
            contribution_id = f"contribution_{django_timezone.now().strftime('%Y%m%d_%H%M%S')}_{hash(user_id) % 10000}"
            
            # Create contribution
            contribution = UserContribution(
                id=contribution_id,
                user_id=user_id,
                contribution_type=ContributionType(contribution_data['contribution_type']),
                title=contribution_data['title'],
                description=contribution_data.get('description'),
                content_id=contribution_data.get('content_id'),
                file_path=contribution_data.get('file_path'),
                url=contribution_data.get('url'),
                status=ContributionStatus(contribution_data.get('status', ContributionStatus.PENDING.value)),
                points_earned=contribution_data.get('points_earned', 0),
                quality_score=contribution_data.get('quality_score', 0.0),
                tags=contribution_data.get('tags', []),
                category=contribution_data.get('category'),
                metadata=contribution_data.get('metadata', {})
            )
            
            # Store contribution
            self.contributions[contribution_id] = contribution
            
            # Update user profile
            self._update_user_profile(user_id)
            
            # Check for achievements
            self._check_achievements(user_id)
            
            logger.info(f"Created contribution: {contribution_id}")
            return contribution
            
        except Exception as e:
            logger.error(f"Error creating contribution: {e}")
            raise
    
    def update_contribution(self, contribution_id: str, updates: Dict[str, Any]):
        """Update a user contribution"""
        try:
            contribution = self.contributions.get(contribution_id)
            if contribution:
                for key, value in updates.items():
                    if hasattr(contribution, key):
                        setattr(contribution, key, value)
                
                contribution.updated_at = django_timezone.now()
                
                # Update user profile
                self._update_user_profile(contribution.user_id)
                
                logger.info(f"Updated contribution: {contribution_id}")
            
        except Exception as e:
            logger.error(f"Error updating contribution: {e}")
    
    def delete_contribution(self, contribution_id: str):
        """Delete a user contribution"""
        try:
            contribution = self.contributions.get(contribution_id)
            if contribution:
                user_id = contribution.user_id
                del self.contributions[contribution_id]
                
                # Update user profile
                self._update_user_profile(user_id)
                
                logger.info(f"Deleted contribution: {contribution_id}")
            
        except Exception as e:
            logger.error(f"Error deleting contribution: {e}")
    
    def get_contribution(self, contribution_id: str) -> Optional[UserContribution]:
        """Get a contribution by ID"""
        return self.contributions.get(contribution_id)
    
    def get_user_contributions(self, user_id: str, status: ContributionStatus = None, 
                              contribution_type: ContributionType = None) -> List[UserContribution]:
        """Get user contributions filtered by status and type"""
        try:
            contributions = [c for c in self.contributions.values() if c.user_id == user_id]
            
            if status:
                contributions = [c for c in contributions if c.status == status]
            
            if contribution_type:
                contributions = [c for c in contributions if c.contribution_type == contribution_type]
            
            return sorted(contributions, key=lambda x: x.created_at, reverse=True)
            
        except Exception as e:
            logger.error(f"Error getting user contributions: {e}")
            return []
    
    def get_user_profile(self, user_id: str) -> Optional[UserProfile]:
        """Get user profile"""
        return self.user_profiles.get(user_id)
    
    def create_user_profile(self, user_id: str, profile_data: Dict[str, Any]) -> UserProfile:
        """Create user profile"""
        try:
            profile = UserProfile(
                user_id=user_id,
                username=profile_data.get('username', ''),
                email=profile_data.get('email', ''),
                first_name=profile_data.get('first_name', ''),
                last_name=profile_data.get('last_name', ''),
                role=UserRole(profile_data.get('role', UserRole.CONTRIBUTOR.value)),
                expertise_areas=profile_data.get('expertise_areas', []),
                languages=profile_data.get('languages', []),
                timezone=profile_data.get('timezone', 'UTC'),
                preferences=profile_data.get('preferences', {})
            )
            
            self.user_profiles[user_id] = profile
            
            logger.info(f"Created user profile: {user_id}")
            return profile
            
        except Exception as e:
            logger.error(f"Error creating user profile: {e}")
            raise
    
    def update_user_profile(self, user_id: str, updates: Dict[str, Any]):
        """Update user profile"""
        try:
            profile = self.user_profiles.get(user_id)
            if profile:
                for key, value in updates.items():
                    if hasattr(profile, key):
                        setattr(profile, key, value)
                
                profile.profile_updated_at = django_timezone.now()
                
                logger.info(f"Updated user profile: {user_id}")
            
        except Exception as e:
            logger.error(f"Error updating user profile: {e}")
    
    def _update_user_profile(self, user_id: str):
        """Update user profile statistics"""
        try:
            profile = self.user_profiles.get(user_id)
            if not profile:
                return
            
            # Get user contributions
            user_contributions = [c for c in self.contributions.values() if c.user_id == user_id]
            
            # Update statistics
            profile.contribution_count = len(user_contributions)
            profile.approved_contributions = len([c for c in user_contributions if c.status == ContributionStatus.APPROVED])
            profile.rejected_contributions = len([c for c in user_contributions if c.status == ContributionStatus.REJECTED])
            profile.pending_contributions = len([c for c in user_contributions if c.status == ContributionStatus.PENDING])
            profile.total_points = sum(c.points_earned for c in user_contributions)
            
            # Calculate quality score
            if user_contributions:
                profile.quality_score = sum(c.quality_score for c in user_contributions) / len(user_contributions)
            
            # Calculate reputation score
            profile.reputation_score = self._calculate_reputation_score(user_id)
            
            profile.last_active_at = django_timezone.now()
            
        except Exception as e:
            logger.error(f"Error updating user profile: {e}")
    
    def _calculate_reputation_score(self, user_id: str) -> float:
        """Calculate user reputation score"""
        try:
            profile = self.user_profiles.get(user_id)
            if not profile:
                return 0.0
            
            # Base score from points
            base_score = profile.total_points * 0.1
            
            # Quality bonus
            quality_bonus = profile.quality_score * 0.2
            
            # Activity bonus
            activity_bonus = min(profile.contribution_count * 0.5, 50)
            
            # Approval rate bonus
            if profile.contribution_count > 0:
                approval_rate = profile.approved_contributions / profile.contribution_count
                approval_bonus = approval_rate * 100
            else:
                approval_bonus = 0
            
            # Achievement bonus
            achievement_bonus = len(profile.achievements) * 10
            
            total_score = base_score + quality_bonus + activity_bonus + approval_bonus + achievement_bonus
            
            return min(total_score, 1000)  # Cap at 1000
            
        except Exception as e:
            logger.error(f"Error calculating reputation score: {e}")
            return 0.0
    
    def _check_achievements(self, user_id: str):
        """Check and unlock achievements for user"""
        try:
            profile = self.user_profiles.get(user_id)
            if not profile:
                return
            
            user_contributions = [c for c in self.contributions.values() if c.user_id == user_id]
            
            for achievement_type, definition in self.achievement_definitions.items():
                # Check if user already has this achievement
                if achievement_type.value in profile.achievements:
                    continue
                
                # Check achievement conditions
                if self._check_achievement_conditions(user_id, achievement_type, definition['condition']):
                    # Unlock achievement
                    achievement = UserAchievement(
                        id=f"achievement_{user_id}_{achievement_type.value}",
                        user_id=user_id,
                        achievement_type=achievement_type,
                        title=definition['title'],
                        description=definition['description'],
                        points_awarded=definition['points'],
                        badge_icon=definition['badge_icon']
                    )
                    
                    self.achievements[achievement.id] = achievement
                    profile.achievements.append(achievement_type.value)
                    profile.total_points += definition['points']
                    
                    logger.info(f"Unlocked achievement {achievement_type.value} for user {user_id}")
            
        except Exception as e:
            logger.error(f"Error checking achievements: {e}")
    
    def _check_achievement_conditions(self, user_id: str, achievement_type: AchievementType, conditions: Dict[str, Any]) -> bool:
        """Check if achievement conditions are met"""
        try:
            profile = self.user_profiles.get(user_id)
            if not profile:
                return False
            
            user_contributions = [c for c in self.contributions.values() if c.user_id == user_id]
            
            # Check specific conditions
            if 'min_contributions' in conditions:
                if len(user_contributions) < conditions['min_contributions']:
                    return False
            
            if 'min_quality_score' in conditions:
                if profile.quality_score < conditions['min_quality_score']:
                    return False
            
            if 'min_reviews' in conditions:
                if profile.review_count < conditions['min_reviews']:
                    return False
            
            if 'min_comments' in conditions:
                total_comments = sum(c.comment_count for c in user_contributions)
                if total_comments < conditions['min_comments']:
                    return False
            
            if 'min_shares' in conditions:
                total_shares = sum(c.share_count for c in user_contributions)
                if total_shares < conditions['min_shares']:
                    return False
            
            if 'min_translations' in conditions:
                translations = [c for c in user_contributions if c.contribution_type == ContributionType.TRANSLATION]
                if len(translations) < conditions['min_translations']:
                    return False
            
            if 'min_documentation_updates' in conditions:
                doc_updates = [c for c in user_contributions if c.contribution_type == ContributionType.DOCUMENTATION_UPDATE]
                if len(doc_updates) < conditions['min_documentation_updates']:
                    return False
            
            if 'min_tutorials' in conditions:
                tutorials = [c for c in user_contributions if c.contribution_type == ContributionType.TUTORIAL_CREATION]
                if len(tutorials) < conditions['min_tutorials']:
                    return False
            
            if 'min_bug_reports' in conditions:
                bug_reports = [c for c in user_contributions if c.contribution_type == ContributionType.BUG_REPORT]
                if len(bug_reports) < conditions['min_bug_reports']:
                    return False
            
            if 'min_feature_requests' in conditions:
                feature_requests = [c for c in user_contributions if c.contribution_type == ContributionType.FEATURE_REQUEST]
                if len(feature_requests) < conditions['min_feature_requests']:
                    return False
            
            return True
            
        except Exception as e:
            logger.error(f"Error checking achievement conditions: {e}")
            return False
    
    def get_user_analytics(self, user_id: str, period: str = "30_days") -> ContributionAnalytics:
        """Get user analytics"""
        try:
            # Calculate date range
            end_date = django_timezone.now()
            if period == "7_days":
                start_date = end_date - timedelta(days=7)
            elif period == "30_days":
                start_date = end_date - timedelta(days=30)
            elif period == "90_days":
                start_date = end_date - timedelta(days=90)
            elif period == "1_year":
                start_date = end_date - timedelta(days=365)
            else:
                start_date = end_date - timedelta(days=30)
            
            # Get user contributions in period
            user_contributions = [
                c for c in self.contributions.values()
                if c.user_id == user_id and start_date <= c.created_at <= end_date
            ]
            
            # Create analytics
            analytics = ContributionAnalytics(
                user_id=user_id,
                period=period,
                start_date=start_date,
                end_date=end_date,
                total_contributions=len(user_contributions),
                total_points_earned=sum(c.points_earned for c in user_contributions),
                total_views=sum(c.view_count for c in user_contributions),
                total_downloads=sum(c.download_count for c in user_contributions),
                total_shares=sum(c.share_count for c in user_contributions),
                total_comments=sum(c.comment_count for c in user_contributions)
            )
            
            # Calculate contributions by type
            for contribution in user_contributions:
                contribution_type = contribution.contribution_type.value
                analytics.contributions_by_type[contribution_type] = analytics.contributions_by_type.get(contribution_type, 0) + 1
            
            # Calculate contributions by status
            for contribution in user_contributions:
                status = contribution.status.value
                analytics.contributions_by_status[status] = analytics.contributions_by_status.get(status, 0) + 1
            
            # Calculate average quality score
            if user_contributions:
                analytics.average_quality_score = sum(c.quality_score for c in user_contributions) / len(user_contributions)
            
            # Calculate average rating
            rated_contributions = [c for c in user_contributions if c.rating_count > 0]
            if rated_contributions:
                analytics.average_rating = sum(c.rating_average for c in rated_contributions) / len(rated_contributions)
            
            # Get top categories
            categories = {}
            for contribution in user_contributions:
                if contribution.category:
                    categories[contribution.category] = categories.get(contribution.category, 0) + 1
            
            analytics.top_categories = sorted(categories.items(), key=lambda x: x[1], reverse=True)[:5]
            analytics.top_categories = [cat[0] for cat in analytics.top_categories]
            
            # Get top tags
            tags = {}
            for contribution in user_contributions:
                for tag in contribution.tags:
                    tags[tag] = tags.get(tag, 0) + 1
            
            analytics.top_tags = sorted(tags.items(), key=lambda x: x[1], reverse=True)[:5]
            analytics.top_tags = [tag[0] for tag in analytics.top_tags]
            
            # Generate trends
            analytics.contribution_trend = self._generate_contribution_trend(user_contributions, start_date, end_date)
            analytics.quality_trend = self._generate_quality_trend(user_contributions, start_date, end_date)
            analytics.engagement_trend = self._generate_engagement_trend(user_contributions, start_date, end_date)
            
            return analytics
            
        except Exception as e:
            logger.error(f"Error getting user analytics: {e}")
            return ContributionAnalytics(user_id=user_id, period=period, start_date=start_date, end_date=end_date)
    
    def _generate_contribution_trend(self, contributions: List[UserContribution], start_date: datetime, end_date: datetime) -> List[Dict[str, Any]]:
        """Generate contribution trend data"""
        try:
            trend_data = []
            current_date = start_date
            
            while current_date <= end_date:
                next_date = current_date + timedelta(days=1)
                daily_contributions = [
                    c for c in contributions
                    if current_date <= c.created_at < next_date
                ]
                
                trend_data.append({
                    'date': current_date.strftime('%Y-%m-%d'),
                    'count': len(daily_contributions),
                    'points': sum(c.points_earned for c in daily_contributions)
                })
                
                current_date = next_date
            
            return trend_data
            
        except Exception as e:
            logger.error(f"Error generating contribution trend: {e}")
            return []
    
    def _generate_quality_trend(self, contributions: List[UserContribution], start_date: datetime, end_date: datetime) -> List[Dict[str, Any]]:
        """Generate quality trend data"""
        try:
            trend_data = []
            current_date = start_date
            
            while current_date <= end_date:
                next_date = current_date + timedelta(days=1)
                daily_contributions = [
                    c for c in contributions
                    if current_date <= c.created_at < next_date
                ]
                
                if daily_contributions:
                    avg_quality = sum(c.quality_score for c in daily_contributions) / len(daily_contributions)
                else:
                    avg_quality = 0
                
                trend_data.append({
                    'date': current_date.strftime('%Y-%m-%d'),
                    'quality_score': avg_quality
                })
                
                current_date = next_date
            
            return trend_data
            
        except Exception as e:
            logger.error(f"Error generating quality trend: {e}")
            return []
    
    def _generate_engagement_trend(self, contributions: List[UserContribution], start_date: datetime, end_date: datetime) -> List[Dict[str, Any]]:
        """Generate engagement trend data"""
        try:
            trend_data = []
            current_date = start_date
            
            while current_date <= end_date:
                next_date = current_date + timedelta(days=1)
                daily_contributions = [
                    c for c in contributions
                    if current_date <= c.created_at < next_date
                ]
                
                trend_data.append({
                    'date': current_date.strftime('%Y-%m-%d'),
                    'views': sum(c.view_count for c in daily_contributions),
                    'downloads': sum(c.download_count for c in daily_contributions),
                    'shares': sum(c.share_count for c in daily_contributions),
                    'comments': sum(c.comment_count for c in daily_contributions)
                })
                
                current_date = next_date
            
            return trend_data
            
        except Exception as e:
            logger.error(f"Error generating engagement trend: {e}")
            return []
    
    def get_dashboard_data(self, user_id: str, layout: str = "default") -> Dict[str, Any]:
        """Get dashboard data for user"""
        try:
            # Get user profile
            profile = self.get_user_profile(user_id)
            if not profile:
                return {}
            
            # Get user analytics
            analytics = self.get_user_analytics(user_id)
            
            # Get user contributions
            contributions = self.get_user_contributions(user_id)
            
            # Get user achievements
            user_achievements = [a for a in self.achievements.values() if a.user_id == user_id]
            
            # Get dashboard layout
            dashboard_layout = self.dashboard_layouts.get(layout, self.dashboard_layouts["default"])
            
            # Prepare dashboard data
            dashboard_data = {
                'user_profile': {
                    'user_id': profile.user_id,
                    'username': profile.username,
                    'email': profile.email,
                    'first_name': profile.first_name,
                    'last_name': profile.last_name,
                    'role': profile.role.value,
                    'total_points': profile.total_points,
                    'contribution_count': profile.contribution_count,
                    'approved_contributions': profile.approved_contributions,
                    'rejected_contributions': profile.rejected_contributions,
                    'pending_contributions': profile.pending_contributions,
                    'quality_score': profile.quality_score,
                    'reputation_score': profile.reputation_score,
                    'expertise_areas': profile.expertise_areas,
                    'languages': profile.languages,
                    'achievements': profile.achievements,
                    'badges': profile.badges,
                    'joined_at': profile.joined_at.isoformat(),
                    'last_active_at': profile.last_active_at.isoformat()
                },
                'analytics': {
                    'period': analytics.period,
                    'total_contributions': analytics.total_contributions,
                    'contributions_by_type': analytics.contributions_by_type,
                    'contributions_by_status': analytics.contributions_by_status,
                    'total_points_earned': analytics.total_points_earned,
                    'average_quality_score': analytics.average_quality_score,
                    'total_views': analytics.total_views,
                    'total_downloads': analytics.total_downloads,
                    'total_shares': analytics.total_shares,
                    'total_comments': analytics.total_comments,
                    'average_rating': analytics.average_rating,
                    'top_categories': analytics.top_categories,
                    'top_tags': analytics.top_tags,
                    'contribution_trend': analytics.contribution_trend,
                    'quality_trend': analytics.quality_trend,
                    'engagement_trend': analytics.engagement_trend
                },
                'recent_contributions': [
                    {
                        'id': c.id,
                        'title': c.title,
                        'description': c.description,
                        'contribution_type': c.contribution_type.value,
                        'status': c.status.value,
                        'points_earned': c.points_earned,
                        'quality_score': c.quality_score,
                        'view_count': c.view_count,
                        'download_count': c.download_count,
                        'share_count': c.share_count,
                        'comment_count': c.comment_count,
                        'rating_average': c.rating_average,
                        'rating_count': c.rating_count,
                        'tags': c.tags,
                        'category': c.category,
                        'created_at': c.created_at.isoformat(),
                        'updated_at': c.updated_at.isoformat()
                    }
                    for c in contributions[:10]
                ],
                'achievements': [
                    {
                        'id': a.id,
                        'achievement_type': a.achievement_type.value,
                        'title': a.title,
                        'description': a.description,
                        'points_awarded': a.points_awarded,
                        'badge_icon': a.badge_icon,
                        'unlocked_at': a.unlocked_at.isoformat()
                    }
                    for a in user_achievements
                ],
                'dashboard_layout': dashboard_layout,
                'widgets': [
                    {
                        'id': widget.id,
                        'name': widget.name,
                        'type': widget.type,
                        'title': widget.title,
                        'description': widget.description,
                        'position': widget.position,
                        'size': widget.size,
                        'enabled': widget.enabled
                    }
                    for widget in self.widgets.values()
                    if widget.id in dashboard_layout['widgets']
                ]
            }
            
            return dashboard_data
            
        except Exception as e:
            logger.error(f"Error getting dashboard data: {e}")
            return {}
    
    def get_widget_data(self, widget_id: str, user_id: str) -> Dict[str, Any]:
        """Get data for a specific widget"""
        try:
            widget = self.widgets.get(widget_id)
            if not widget:
                return {}
            
            # Get data based on widget data source
            if widget.data_source == 'user_contributions':
                return self._get_user_contributions_data(user_id)
            elif widget.data_source == 'contribution_analytics':
                return self._get_contribution_analytics_data(user_id)
            elif widget.data_source == 'user_quality':
                return self._get_user_quality_data(user_id)
            elif widget.data_source == 'recent_contributions':
                return self._get_recent_contributions_data(user_id)
            elif widget.data_source == 'contribution_types':
                return self._get_contribution_types_data(user_id)
            elif widget.data_source == 'user_achievements':
                return self._get_user_achievements_data(user_id)
            elif widget.data_source == 'engagement_metrics':
                return self._get_engagement_metrics_data(user_id)
            elif widget.data_source == 'top_categories':
                return self._get_top_categories_data(user_id)
            elif widget.data_source == 'reputation_score':
                return self._get_reputation_score_data(user_id)
            else:
                return {}
            
        except Exception as e:
            logger.error(f"Error getting widget data: {e}")
            return {}
    
    def _get_user_contributions_data(self, user_id: str) -> Dict[str, Any]:
        """Get user contributions data"""
        try:
            profile = self.get_user_profile(user_id)
            if not profile:
                return {}
            
            return {
                'total_contributions': profile.contribution_count,
                'approved_contributions': profile.approved_contributions,
                'pending_contributions': profile.pending_contributions,
                'total_points': profile.total_points
            }
            
        except Exception as e:
            logger.error(f"Error getting user contributions data: {e}")
            return {}
    
    def _get_contribution_analytics_data(self, user_id: str) -> Dict[str, Any]:
        """Get contribution analytics data"""
        try:
            analytics = self.get_user_analytics(user_id)
            return {
                'contribution_trend': analytics.contribution_trend,
                'period': analytics.period
            }
            
        except Exception as e:
            logger.error(f"Error getting contribution analytics data: {e}")
            return {}
    
    def _get_user_quality_data(self, user_id: str) -> Dict[str, Any]:
        """Get user quality data"""
        try:
            profile = self.get_user_profile(user_id)
            if not profile:
                return {}
            
            return {
                'quality_score': profile.quality_score,
                'max_value': 100
            }
            
        except Exception as e:
            logger.error(f"Error getting user quality data: {e}")
            return {}
    
    def _get_recent_contributions_data(self, user_id: str) -> Dict[str, Any]:
        """Get recent contributions data"""
        try:
            contributions = self.get_user_contributions(user_id)
            return {
                'contributions': [
                    {
                        'id': c.id,
                        'title': c.title,
                        'contribution_type': c.contribution_type.value,
                        'status': c.status.value,
                        'created_at': c.created_at.isoformat()
                    }
                    for c in contributions[:10]
                ]
            }
            
        except Exception as e:
            logger.error(f"Error getting recent contributions data: {e}")
            return {}
    
    def _get_contribution_types_data(self, user_id: str) -> Dict[str, Any]:
        """Get contribution types data"""
        try:
            analytics = self.get_user_analytics(user_id)
            return {
                'contribution_types': analytics.contributions_by_type
            }
            
        except Exception as e:
            logger.error(f"Error getting contribution types data: {e}")
            return {}
    
    def _get_user_achievements_data(self, user_id: str) -> Dict[str, Any]:
        """Get user achievements data"""
        try:
            user_achievements = [a for a in self.achievements.values() if a.user_id == user_id]
            return {
                'achievements': [
                    {
                        'id': a.id,
                        'title': a.title,
                        'description': a.description,
                        'badge_icon': a.badge_icon,
                        'unlocked_at': a.unlocked_at.isoformat()
                    }
                    for a in user_achievements[:5]
                ]
            }
            
        except Exception as e:
            logger.error(f"Error getting user achievements data: {e}")
            return {}
    
    def _get_engagement_metrics_data(self, user_id: str) -> Dict[str, Any]:
        """Get engagement metrics data"""
        try:
            analytics = self.get_user_analytics(user_id)
            return {
                'total_views': analytics.total_views,
                'total_downloads': analytics.total_downloads,
                'total_shares': analytics.total_shares,
                'average_rating': analytics.average_rating
            }
            
        except Exception as e:
            logger.error(f"Error getting engagement metrics data: {e}")
            return {}
    
    def _get_top_categories_data(self, user_id: str) -> Dict[str, Any]:
        """Get top categories data"""
        try:
            analytics = self.get_user_analytics(user_id)
            return {
                'top_categories': analytics.top_categories
            }
            
        except Exception as e:
            logger.error(f"Error getting top categories data: {e}")
            return {}
    
    def _get_reputation_score_data(self, user_id: str) -> Dict[str, Any]:
        """Get reputation score data"""
        try:
            profile = self.get_user_profile(user_id)
            if not profile:
                return {}
            
            return {
                'reputation_score': profile.reputation_score,
                'trend': 'up'  # Mock trend
            }
            
        except Exception as e:
            logger.error(f"Error getting reputation score data: {e}")
            return {}
    
    def get_dashboard_statistics(self) -> Dict[str, Any]:
        """Get dashboard statistics"""
        try:
            stats = {
                'total_users': len(self.user_profiles),
                'total_contributions': len(self.contributions),
                'total_achievements': len(self.achievements),
                'contributions_by_type': {},
                'contributions_by_status': {},
                'users_by_role': {},
                'average_quality_score': 0,
                'average_reputation_score': 0,
                'total_points_awarded': 0
            }
            
            # Count contributions by type and status
            for contribution in self.contributions.values():
                contribution_type = contribution.contribution_type.value
                stats['contributions_by_type'][contribution_type] = stats['contributions_by_type'].get(contribution_type, 0) + 1
                
                status = contribution.status.value
                stats['contributions_by_status'][status] = stats['contributions_by_status'].get(status, 0) + 1
            
            # Count users by role
            for profile in self.user_profiles.values():
                role = profile.role.value
                stats['users_by_role'][role] = stats['users_by_role'].get(role, 0) + 1
            
            # Calculate averages
            if self.user_profiles:
                stats['average_quality_score'] = sum(p.quality_score for p in self.user_profiles.values()) / len(self.user_profiles)
                stats['average_reputation_score'] = sum(p.reputation_score for p in self.user_profiles.values()) / len(self.user_profiles)
            
            # Calculate total points
            stats['total_points_awarded'] = sum(c.points_earned for c in self.contributions.values())
            
            return stats
            
        except Exception as e:
            logger.error(f"Error getting dashboard statistics: {e}")
            return {}
    
    def export_user_data(self, user_id: str) -> Dict[str, Any]:
        """Export user data"""
        try:
            profile = self.get_user_profile(user_id)
            if not profile:
                return {}
            
            contributions = self.get_user_contributions(user_id)
            analytics = self.get_user_analytics(user_id)
            user_achievements = [a for a in self.achievements.values() if a.user_id == user_id]
            
            return {
                'user_profile': {
                    'user_id': profile.user_id,
                    'username': profile.username,
                    'email': profile.email,
                    'first_name': profile.first_name,
                    'last_name': profile.last_name,
                    'role': profile.role.value,
                    'total_points': profile.total_points,
                    'contribution_count': profile.contribution_count,
                    'quality_score': profile.quality_score,
                    'reputation_score': profile.reputation_score,
                    'expertise_areas': profile.expertise_areas,
                    'languages': profile.languages,
                    'achievements': profile.achievements,
                    'badges': profile.badges,
                    'joined_at': profile.joined_at.isoformat(),
                    'last_active_at': profile.last_active_at.isoformat()
                },
                'contributions': [
                    {
                        'id': c.id,
                        'title': c.title,
                        'description': c.description,
                        'contribution_type': c.contribution_type.value,
                        'status': c.status.value,
                        'points_earned': c.points_earned,
                        'quality_score': c.quality_score,
                        'tags': c.tags,
                        'category': c.category,
                        'created_at': c.created_at.isoformat(),
                        'updated_at': c.updated_at.isoformat()
                    }
                    for c in contributions
                ],
                'analytics': {
                    'period': analytics.period,
                    'total_contributions': analytics.total_contributions,
                    'total_points_earned': analytics.total_points_earned,
                    'average_quality_score': analytics.average_quality_score,
                    'total_views': analytics.total_views,
                    'total_downloads': analytics.total_downloads,
                    'total_shares': analytics.total_shares,
                    'total_comments': analytics.total_comments,
                    'average_rating': analytics.average_rating
                },
                'achievements': [
                    {
                        'id': a.id,
                        'achievement_type': a.achievement_type.value,
                        'title': a.title,
                        'description': a.description,
                        'points_awarded': a.points_awarded,
                        'badge_icon': a.badge_icon,
                        'unlocked_at': a.unlocked_at.isoformat()
                    }
                    for a in user_achievements
                ]
            }
            
        except Exception as e:
            logger.error(f"Error exporting user data: {e}")
            return {}
    
    def cleanup_old_data(self, days_old: int = 365):
        """Clean up old data"""
        try:
            cutoff_date = django_timezone.now() - timedelta(days=days_old)
            
            # Clean up old contributions
            old_contributions = [
                cid for cid, contribution in self.contributions.items()
                if contribution.created_at < cutoff_date
            ]
            
            for contribution_id in old_contributions:
                del self.contributions[contribution_id]
            
            logger.info(f"Cleaned up {len(old_contributions)} old contributions")
            
        except Exception as e:
            logger.error(f"Error cleaning up old data: {e}")
    
    def get_leaderboard(self, limit: int = 10) -> List[Dict[str, Any]]:
        """Get user leaderboard"""
        try:
            # Sort users by reputation score
            sorted_users = sorted(
                self.user_profiles.values(),
                key=lambda x: x.reputation_score,
                reverse=True
            )
            
            leaderboard = []
            for i, profile in enumerate(sorted_users[:limit]):
                leaderboard.append({
                    'rank': i + 1,
                    'user_id': profile.user_id,
                    'username': profile.username,
                    'total_points': profile.total_points,
                    'contribution_count': profile.contribution_count,
                    'quality_score': profile.quality_score,
                    'reputation_score': profile.reputation_score,
                    'achievements_count': len(profile.achievements)
                })
            
            return leaderboard
            
        except Exception as e:
            logger.error(f"Error getting leaderboard: {e}")
            return []
    
    def get_contribution_statistics(self) -> Dict[str, Any]:
        """Get contribution statistics"""
        try:
            stats = {
                'total_contributions': len(self.contributions),
                'contributions_by_type': {},
                'contributions_by_status': {},
                'contributions_by_user': {},
                'total_points_awarded': 0,
                'average_quality_score': 0,
                'top_contributors': [],
                'recent_contributions': []
            }
            
            # Count by type and status
            for contribution in self.contributions.values():
                contribution_type = contribution.contribution_type.value
                stats['contributions_by_type'][contribution_type] = stats['contributions_by_type'].get(contribution_type, 0) + 1
                
                status = contribution.status.value
                stats['contributions_by_status'][status] = stats['contributions_by_status'].get(status, 0) + 1
                
                # Count by user
                stats['contributions_by_user'][contribution.user_id] = stats['contributions_by_user'].get(contribution.user_id, 0) + 1
                
                # Sum points
                stats['total_points_awarded'] += contribution.points_earned
            
            # Calculate average quality score
            if self.contributions:
                stats['average_quality_score'] = sum(c.quality_score for c in self.contributions.values()) / len(self.contributions)
            
            # Get top contributors
            top_contributors = sorted(
                stats['contributions_by_user'].items(),
                key=lambda x: x[1],
                reverse=True
            )[:10]
            
            stats['top_contributors'] = [
                {
                    'user_id': user_id,
                    'contribution_count': count,
                    'username': self.user_profiles.get(user_id, {}).username if self.user_profiles.get(user_id) else 'Unknown'
                }
                for user_id, count in top_contributors
            ]
            
            # Get recent contributions
            recent_contributions = sorted(
                self.contributions.values(),
                key=lambda x: x.created_at,
                reverse=True
            )[:10]
            
            stats['recent_contributions'] = [
                {
                    'id': c.id,
                    'title': c.title,
                    'contribution_type': c.contribution_type.value,
                    'status': c.status.value,
                    'user_id': c.user_id,
                    'username': self.user_profiles.get(c.user_id, {}).username if self.user_profiles.get(c.user_id) else 'Unknown',
                    'created_at': c.created_at.isoformat()
                }
                for c in recent_contributions
            ]
            
            return stats
            
        except Exception as e:
            logger.error(f"Error getting contribution statistics: {e}")
            return {}
