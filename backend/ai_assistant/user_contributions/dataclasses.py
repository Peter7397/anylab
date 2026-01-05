"""
User Contribution Data Classes

This module contains all dataclasses used in the User Contribution Dashboard.
"""

from typing import Dict, Any, List, Optional, Tuple
from dataclasses import dataclass, field
from datetime import datetime
from django.utils import timezone as django_timezone

from .enums import ContributionType, ContributionStatus, UserRole, AchievementType


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
    first_name: str = ""
    last_name: str = ""
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

