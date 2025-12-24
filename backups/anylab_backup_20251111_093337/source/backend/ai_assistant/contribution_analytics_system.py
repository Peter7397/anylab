"""
Contribution Analytics System

This module provides comprehensive analytics for user contributions,
including contribution patterns, quality metrics, user engagement, and community insights.
"""

import logging
import statistics
from typing import Dict, Any, List, Optional, Tuple, Union
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from enum import Enum
from django.utils import timezone as django_timezone
from django.core.cache import cache

logger = logging.getLogger(__name__)


class ContributionType(Enum):
    """Contribution type enumeration"""
    DOCUMENT_UPLOAD = "document_upload"
    URL_SUBMISSION = "url_submission"
    CONTENT_EDIT = "content_edit"
    COMMENT = "comment"
    RATING = "rating"
    REVIEW = "review"
    SUGGESTION = "suggestion"
    BUG_REPORT = "bug_report"
    FEATURE_REQUEST = "feature_request"


class ContributionStatus(Enum):
    """Contribution status enumeration"""
    PENDING = "pending"
    APPROVED = "approved"
    REJECTED = "rejected"
    UNDER_REVIEW = "under_review"
    PUBLISHED = "published"
    ARCHIVED = "archived"


class ContributorLevel(Enum):
    """Contributor level enumeration"""
    NEWBIE = "newbie"
    CONTRIBUTOR = "contributor"
    REGULAR = "regular"
    EXPERT = "expert"
    MODERATOR = "moderator"
    ADMIN = "admin"


class QualityRating(Enum):
    """Quality rating enumeration"""
    EXCELLENT = "excellent"
    GOOD = "good"
    AVERAGE = "average"
    POOR = "poor"
    CRITICAL = "critical"


@dataclass
class Contribution:
    """Contribution structure"""
    id: str
    user_id: str
    contribution_type: ContributionType
    title: str
    description: str
    content: str
    status: ContributionStatus
    quality_rating: QualityRating
    views: int = 0
    likes: int = 0
    comments: int = 0
    shares: int = 0
    metadata: Dict[str, Any] = field(default_factory=dict)
    created_at: datetime = field(default_factory=lambda: django_timezone.now())
    updated_at: datetime = field(default_factory=lambda: django_timezone.now())
    published_at: Optional[datetime] = None


@dataclass
class ContributorProfile:
    """Contributor profile structure"""
    user_id: str
    contributor_level: ContributorLevel
    total_contributions: int = 0
    approved_contributions: int = 0
    rejected_contributions: int = 0
    pending_contributions: int = 0
    total_views: int = 0
    total_likes: int = 0
    total_comments: int = 0
    average_quality_rating: float = 0.0
    contribution_score: float = 0.0
    last_contribution: datetime = field(default_factory=lambda: django_timezone.now())
    metadata: Dict[str, Any] = field(default_factory=dict)
    created_at: datetime = field(default_factory=lambda: django_timezone.now())
    updated_at: datetime = field(default_factory=lambda: django_timezone.now())


@dataclass
class ContributionAnalytics:
    """Contribution analytics structure"""
    id: str
    period: str  # "daily", "weekly", "monthly"
    start_date: datetime
    end_date: datetime
    total_contributions: int = 0
    approved_contributions: int = 0
    rejected_contributions: int = 0
    pending_contributions: int = 0
    total_views: int = 0
    total_likes: int = 0
    total_comments: int = 0
    average_quality_rating: float = 0.0
    top_contributors: List[str] = field(default_factory=list)
    top_contributions: List[str] = field(default_factory=list)
    contribution_trends: Dict[str, Any] = field(default_factory=dict)
    created_at: datetime = field(default_factory=lambda: django_timezone.now())


class ContributionAnalyticsSystem:
    """Contribution Analytics System"""
    
    def __init__(self, config: Dict[str, Any] = None):
        """Initialize contribution analytics system"""
        self.config = config or {}
        self.analytics_enabled = self.config.get('analytics_enabled', True)
        self.quality_monitoring = self.config.get('quality_monitoring', True)
        self.trend_analysis = self.config.get('trend_analysis', True)
        self.cache_enabled = self.config.get('cache_enabled', True)
        self.analytics_interval = self.config.get('analytics_interval', 3600)  # seconds
        
        # Initialize components
        self.contributions = {}
        self.contributor_profiles = {}
        self.contribution_analytics = {}
        self.cache = cache if self.cache_enabled else None
        
        # Initialize analytics system
        self._initialize_analytics_system()
        
        logger.info("Contribution Analytics System initialized")
    
    def _initialize_analytics_system(self):
        """Initialize analytics system components"""
        try:
            # Initialize sample contributions
            self._initialize_sample_contributions()
            
            # Initialize contributor profiles
            self._initialize_contributor_profiles()
            
            logger.info("Analytics system components initialized")
            
        except Exception as e:
            logger.error(f"Error initializing analytics system: {e}")
            raise
    
    def _initialize_sample_contributions(self):
        """Initialize sample contributions"""
        try:
            sample_contributions = [
                {
                    "id": "contrib_1",
                    "user_id": "user_1",
                    "contribution_type": ContributionType.DOCUMENT_UPLOAD,
                    "title": "OpenLab Troubleshooting Guide",
                    "description": "Comprehensive troubleshooting guide for OpenLab issues",
                    "content": "This guide covers common OpenLab issues and solutions...",
                    "status": ContributionStatus.APPROVED,
                    "quality_rating": QualityRating.EXCELLENT,
                    "views": 450,
                    "likes": 25,
                    "comments": 8,
                    "shares": 12
                },
                {
                    "id": "contrib_2",
                    "user_id": "user_2",
                    "contribution_type": ContributionType.URL_SUBMISSION,
                    "title": "Agilent Support Portal",
                    "description": "Link to Agilent's official support portal",
                    "content": "https://support.agilent.com",
                    "status": ContributionStatus.APPROVED,
                    "quality_rating": QualityRating.GOOD,
                    "views": 320,
                    "likes": 15,
                    "comments": 3,
                    "shares": 5
                },
                {
                    "id": "contrib_3",
                    "user_id": "user_3",
                    "contribution_type": ContributionType.CONTENT_EDIT,
                    "title": "Updated ChemStation Manual",
                    "description": "Updated ChemStation manual with latest features",
                    "content": "Updated manual content...",
                    "status": ContributionStatus.PENDING,
                    "quality_rating": QualityRating.AVERAGE,
                    "views": 180,
                    "likes": 8,
                    "comments": 2,
                    "shares": 1
                },
                {
                    "id": "contrib_4",
                    "user_id": "user_1",
                    "contribution_type": ContributionType.COMMENT,
                    "title": "Comment on MassHunter Tutorial",
                    "description": "Helpful comment on MassHunter tutorial",
                    "content": "This tutorial was very helpful. I found the section on...",
                    "status": ContributionStatus.APPROVED,
                    "quality_rating": QualityRating.GOOD,
                    "views": 95,
                    "likes": 12,
                    "comments": 1,
                    "shares": 0
                }
            ]
            
            for contrib_data in sample_contributions:
                contribution = Contribution(**contrib_data)
                self.contributions[contribution.id] = contribution
            
            logger.info(f"Initialized {len(self.contributions)} sample contributions")
            
        except Exception as e:
            logger.error(f"Error initializing sample contributions: {e}")
            raise
    
    def _initialize_contributor_profiles(self):
        """Initialize contributor profiles"""
        try:
            sample_profiles = [
                {
                    "user_id": "user_1",
                    "contributor_level": ContributorLevel.EXPERT,
                    "total_contributions": 15,
                    "approved_contributions": 12,
                    "rejected_contributions": 1,
                    "pending_contributions": 2,
                    "total_views": 2500,
                    "total_likes": 150,
                    "total_comments": 45,
                    "average_quality_rating": 4.2
                },
                {
                    "user_id": "user_2",
                    "contributor_level": ContributorLevel.REGULAR,
                    "total_contributions": 8,
                    "approved_contributions": 6,
                    "rejected_contributions": 1,
                    "pending_contributions": 1,
                    "total_views": 1200,
                    "total_likes": 80,
                    "total_comments": 20,
                    "average_quality_rating": 3.8
                },
                {
                    "user_id": "user_3",
                    "contributor_level": ContributorLevel.CONTRIBUTOR,
                    "total_contributions": 3,
                    "approved_contributions": 1,
                    "rejected_contributions": 0,
                    "pending_contributions": 2,
                    "total_views": 400,
                    "total_likes": 25,
                    "total_comments": 8,
                    "average_quality_rating": 3.5
                }
            ]
            
            for profile_data in sample_profiles:
                profile = ContributorProfile(**profile_data)
                profile.contribution_score = self._calculate_contribution_score(profile)
                self.contributor_profiles[profile.user_id] = profile
            
            logger.info(f"Initialized {len(self.contributor_profiles)} contributor profiles")
            
        except Exception as e:
            logger.error(f"Error initializing contributor profiles: {e}")
            raise
    
    def _calculate_contribution_score(self, profile: ContributorProfile) -> float:
        """Calculate contributor score"""
        try:
            score = 0.0
            
            # Base score from total contributions
            score += profile.total_contributions * 2
            
            # Bonus for approved contributions
            score += profile.approved_contributions * 5
            
            # Penalty for rejected contributions
            score -= profile.rejected_contributions * 3
            
            # Engagement score
            score += profile.total_views * 0.1
            score += profile.total_likes * 0.5
            score += profile.total_comments * 0.3
            
            # Quality bonus
            score += profile.average_quality_rating * 10
            
            return max(score, 0.0)
            
        except Exception as e:
            logger.error(f"Error calculating contribution score: {e}")
            return 0.0
    
    def add_contribution(self, user_id: str, contribution_type: ContributionType, title: str,
                        description: str, content: str, metadata: Dict[str, Any] = None) -> str:
        """Add a new contribution"""
        try:
            # Generate contribution ID
            contrib_id = f"contrib_{user_id}_{django_timezone.now().strftime('%Y%m%d_%H%M%S')}_{hash(content) % 10000}"
            
            # Create contribution
            contribution = Contribution(
                id=contrib_id,
                user_id=user_id,
                contribution_type=contribution_type,
                title=title,
                description=description,
                content=content,
                status=ContributionStatus.PENDING,
                quality_rating=QualityRating.AVERAGE,
                metadata=metadata or {}
            )
            
            # Store contribution
            self.contributions[contrib_id] = contribution
            
            # Update contributor profile
            self._update_contributor_profile(user_id, contribution)
            
            logger.info(f"Added contribution: {contrib_id}")
            return contrib_id
            
        except Exception as e:
            logger.error(f"Error adding contribution: {e}")
            return ""
    
    def _update_contributor_profile(self, user_id: str, contribution: Contribution):
        """Update contributor profile with new contribution"""
        try:
            profile = self.contributor_profiles.get(user_id)
            if not profile:
                # Create new profile
                profile = ContributorProfile(
                    user_id=user_id,
                    contributor_level=ContributorLevel.NEWBIE
                )
                self.contributor_profiles[user_id] = profile
            
            # Update profile metrics
            profile.total_contributions += 1
            
            if contribution.status == ContributionStatus.APPROVED:
                profile.approved_contributions += 1
            elif contribution.status == ContributionStatus.REJECTED:
                profile.rejected_contributions += 1
            elif contribution.status == ContributionStatus.PENDING:
                profile.pending_contributions += 1
            
            profile.total_views += contribution.views
            profile.total_likes += contribution.likes
            profile.total_comments += contribution.comments
            
            # Update average quality rating
            if profile.total_contributions > 0:
                total_rating = profile.average_quality_rating * (profile.total_contributions - 1)
                total_rating += self._get_quality_rating_value(contribution.quality_rating)
                profile.average_quality_rating = total_rating / profile.total_contributions
            
            # Update last contribution
            profile.last_contribution = contribution.created_at
            
            # Recalculate contribution score
            profile.contribution_score = self._calculate_contribution_score(profile)
            
            # Update contributor level
            profile.contributor_level = self._determine_contributor_level(profile)
            
            profile.updated_at = django_timezone.now()
            
        except Exception as e:
            logger.error(f"Error updating contributor profile: {e}")
    
    def _get_quality_rating_value(self, rating: QualityRating) -> float:
        """Get numeric value for quality rating"""
        try:
            rating_values = {
                QualityRating.EXCELLENT: 5.0,
                QualityRating.GOOD: 4.0,
                QualityRating.AVERAGE: 3.0,
                QualityRating.POOR: 2.0,
                QualityRating.CRITICAL: 1.0
            }
            return rating_values.get(rating, 3.0)
            
        except Exception as e:
            logger.error(f"Error getting quality rating value: {e}")
            return 3.0
    
    def _determine_contributor_level(self, profile: ContributorProfile) -> ContributorLevel:
        """Determine contributor level based on profile"""
        try:
            if profile.contribution_score >= 500:
                return ContributorLevel.ADMIN
            elif profile.contribution_score >= 300:
                return ContributorLevel.MODERATOR
            elif profile.contribution_score >= 150:
                return ContributorLevel.EXPERT
            elif profile.contribution_score >= 50:
                return ContributorLevel.REGULAR
            elif profile.contribution_score >= 10:
                return ContributorLevel.CONTRIBUTOR
            else:
                return ContributorLevel.NEWBIE
                
        except Exception as e:
            logger.error(f"Error determining contributor level: {e}")
            return ContributorLevel.NEWBIE
    
    def get_contribution(self, contrib_id: str) -> Optional[Contribution]:
        """Get a contribution by ID"""
        return self.contributions.get(contrib_id)
    
    def get_contributor_profile(self, user_id: str) -> Optional[ContributorProfile]:
        """Get a contributor profile by user ID"""
        return self.contributor_profiles.get(user_id)
    
    def get_contributions_by_user(self, user_id: str, status: ContributionStatus = None) -> List[Contribution]:
        """Get contributions by user"""
        try:
            contributions = []
            
            for contrib in self.contributions.values():
                if contrib.user_id != user_id:
                    continue
                
                if status and contrib.status != status:
                    continue
                
                contributions.append(contrib)
            
            # Sort by created date
            contributions.sort(key=lambda x: x.created_at, reverse=True)
            
            return contributions
            
        except Exception as e:
            logger.error(f"Error getting contributions by user: {e}")
            return []
    
    def get_top_contributors(self, limit: int = 10) -> List[ContributorProfile]:
        """Get top contributors by score"""
        try:
            profiles = list(self.contributor_profiles.values())
            profiles.sort(key=lambda x: x.contribution_score, reverse=True)
            return profiles[:limit]
            
        except Exception as e:
            logger.error(f"Error getting top contributors: {e}")
            return []
    
    def get_top_contributions(self, limit: int = 10, contribution_type: ContributionType = None) -> List[Contribution]:
        """Get top contributions by engagement"""
        try:
            contributions = list(self.contributions.values())
            
            # Filter by type if specified
            if contribution_type:
                contributions = [c for c in contributions if c.contribution_type == contribution_type]
            
            # Sort by engagement score (views + likes + comments + shares)
            contributions.sort(key=lambda x: x.views + x.likes + x.comments + x.shares, reverse=True)
            
            return contributions[:limit]
            
        except Exception as e:
            logger.error(f"Error getting top contributions: {e}")
            return []
    
    def generate_analytics(self, period: str = "monthly", start_date: datetime = None, end_date: datetime = None) -> ContributionAnalytics:
        """Generate contribution analytics for a period"""
        try:
            if not start_date:
                start_date = django_timezone.now() - timedelta(days=30)
            if not end_date:
                end_date = django_timezone.now()
            
            # Filter contributions by date range
            period_contributions = []
            for contrib in self.contributions.values():
                if start_date <= contrib.created_at <= end_date:
                    period_contributions.append(contrib)
            
            # Calculate analytics
            total_contributions = len(period_contributions)
            approved_contributions = len([c for c in period_contributions if c.status == ContributionStatus.APPROVED])
            rejected_contributions = len([c for c in period_contributions if c.status == ContributionStatus.REJECTED])
            pending_contributions = len([c for c in period_contributions if c.status == ContributionStatus.PENDING])
            
            total_views = sum(c.views for c in period_contributions)
            total_likes = sum(c.likes for c in period_contributions)
            total_comments = sum(c.comments for c in period_contributions)
            
            # Calculate average quality rating
            quality_ratings = [self._get_quality_rating_value(c.quality_rating) for c in period_contributions]
            average_quality_rating = statistics.mean(quality_ratings) if quality_ratings else 0.0
            
            # Get top contributors for the period
            contributor_scores = {}
            for contrib in period_contributions:
                if contrib.user_id not in contributor_scores:
                    contributor_scores[contrib.user_id] = 0
                contributor_scores[contrib.user_id] += contrib.views + contrib.likes + contrib.comments
            
            top_contributors = sorted(contributor_scores.items(), key=lambda x: x[1], reverse=True)[:5]
            top_contributor_ids = [user_id for user_id, _ in top_contributors]
            
            # Get top contributions for the period
            top_contributions = sorted(period_contributions, key=lambda x: x.views + x.likes + x.comments + x.shares, reverse=True)[:5]
            top_contribution_ids = [c.id for c in top_contributions]
            
            # Create analytics
            analytics = ContributionAnalytics(
                id=f"analytics_{period}_{start_date.strftime('%Y%m%d')}_{end_date.strftime('%Y%m%d')}",
                period=period,
                start_date=start_date,
                end_date=end_date,
                total_contributions=total_contributions,
                approved_contributions=approved_contributions,
                rejected_contributions=rejected_contributions,
                pending_contributions=pending_contributions,
                total_views=total_views,
                total_likes=total_likes,
                total_comments=total_comments,
                average_quality_rating=average_quality_rating,
                top_contributors=top_contributor_ids,
                top_contributions=top_contribution_ids,
                contribution_trends={
                    "daily_contributions": self._calculate_daily_trends(period_contributions, start_date, end_date),
                    "contribution_types": self._calculate_type_trends(period_contributions),
                    "quality_trends": self._calculate_quality_trends(period_contributions)
                }
            )
            
            self.contribution_analytics[analytics.id] = analytics
            
            logger.info(f"Generated analytics for period: {period}")
            return analytics
            
        except Exception as e:
            logger.error(f"Error generating analytics: {e}")
            return None
    
    def _calculate_daily_trends(self, contributions: List[Contribution], start_date: datetime, end_date: datetime) -> Dict[str, int]:
        """Calculate daily contribution trends"""
        try:
            daily_trends = {}
            current_date = start_date.date()
            end_date_only = end_date.date()
            
            while current_date <= end_date_only:
                daily_contributions = [c for c in contributions if c.created_at.date() == current_date]
                daily_trends[current_date.isoformat()] = len(daily_contributions)
                current_date += timedelta(days=1)
            
            return daily_trends
            
        except Exception as e:
            logger.error(f"Error calculating daily trends: {e}")
            return {}
    
    def _calculate_type_trends(self, contributions: List[Contribution]) -> Dict[str, int]:
        """Calculate contribution type trends"""
        try:
            type_trends = {}
            for contrib in contributions:
                contrib_type = contrib.contribution_type.value
                type_trends[contrib_type] = type_trends.get(contrib_type, 0) + 1
            
            return type_trends
            
        except Exception as e:
            logger.error(f"Error calculating type trends: {e}")
            return {}
    
    def _calculate_quality_trends(self, contributions: List[Contribution]) -> Dict[str, int]:
        """Calculate quality trends"""
        try:
            quality_trends = {}
            for contrib in contributions:
                quality = contrib.quality_rating.value
                quality_trends[quality] = quality_trends.get(quality, 0) + 1
            
            return quality_trends
            
        except Exception as e:
            logger.error(f"Error calculating quality trends: {e}")
            return {}
    
    def get_analytics_statistics(self) -> Dict[str, Any]:
        """Get analytics statistics"""
        try:
            stats = {
                "total_contributions": len(self.contributions),
                "total_contributors": len(self.contributor_profiles),
                "total_analytics": len(self.contribution_analytics),
                "contributions_by_type": {},
                "contributions_by_status": {},
                "contributors_by_level": {},
                "quality_distribution": {},
                "analytics_enabled": self.analytics_enabled,
                "quality_monitoring": self.quality_monitoring,
                "trend_analysis": self.trend_analysis
            }
            
            # Count contributions by type and status
            for contrib in self.contributions.values():
                contrib_type = contrib.contribution_type.value
                stats["contributions_by_type"][contrib_type] = stats["contributions_by_type"].get(contrib_type, 0) + 1
                
                status = contrib.status.value
                stats["contributions_by_status"][status] = stats["contributions_by_status"].get(status, 0) + 1
                
                quality = contrib.quality_rating.value
                stats["quality_distribution"][quality] = stats["quality_distribution"].get(quality, 0) + 1
            
            # Count contributors by level
            for profile in self.contributor_profiles.values():
                level = profile.contributor_level.value
                stats["contributors_by_level"][level] = stats["contributors_by_level"].get(level, 0) + 1
            
            return stats
            
        except Exception as e:
            logger.error(f"Error getting analytics statistics: {e}")
            return {}
    
    def export_analytics_data(self) -> Dict[str, Any]:
        """Export analytics data"""
        try:
            return {
                "contributions": [
                    {
                        "id": contrib.id,
                        "user_id": contrib.user_id,
                        "contribution_type": contrib.contribution_type.value,
                        "title": contrib.title,
                        "description": contrib.description,
                        "content": contrib.content[:100] + "..." if len(contrib.content) > 100 else contrib.content,
                        "status": contrib.status.value,
                        "quality_rating": contrib.quality_rating.value,
                        "views": contrib.views,
                        "likes": contrib.likes,
                        "comments": contrib.comments,
                        "shares": contrib.shares,
                        "metadata": contrib.metadata,
                        "created_at": contrib.created_at.isoformat(),
                        "updated_at": contrib.updated_at.isoformat(),
                        "published_at": contrib.published_at.isoformat() if contrib.published_at else None
                    }
                    for contrib in self.contributions.values()
                ],
                "contributor_profiles": [
                    {
                        "user_id": profile.user_id,
                        "contributor_level": profile.contributor_level.value,
                        "total_contributions": profile.total_contributions,
                        "approved_contributions": profile.approved_contributions,
                        "rejected_contributions": profile.rejected_contributions,
                        "pending_contributions": profile.pending_contributions,
                        "total_views": profile.total_views,
                        "total_likes": profile.total_likes,
                        "total_comments": profile.total_comments,
                        "average_quality_rating": profile.average_quality_rating,
                        "contribution_score": profile.contribution_score,
                        "last_contribution": profile.last_contribution.isoformat(),
                        "metadata": profile.metadata,
                        "created_at": profile.created_at.isoformat(),
                        "updated_at": profile.updated_at.isoformat()
                    }
                    for profile in self.contributor_profiles.values()
                ],
                "analytics": [
                    {
                        "id": analytics.id,
                        "period": analytics.period,
                        "start_date": analytics.start_date.isoformat(),
                        "end_date": analytics.end_date.isoformat(),
                        "total_contributions": analytics.total_contributions,
                        "approved_contributions": analytics.approved_contributions,
                        "rejected_contributions": analytics.rejected_contributions,
                        "pending_contributions": analytics.pending_contributions,
                        "total_views": analytics.total_views,
                        "total_likes": analytics.total_likes,
                        "total_comments": analytics.total_comments,
                        "average_quality_rating": analytics.average_quality_rating,
                        "top_contributors": analytics.top_contributors,
                        "top_contributions": analytics.top_contributions,
                        "contribution_trends": analytics.contribution_trends,
                        "created_at": analytics.created_at.isoformat()
                    }
                    for analytics in self.contribution_analytics.values()
                ]
            }
            
        except Exception as e:
            logger.error(f"Error exporting analytics data: {e}")
            return {}
    
    def import_analytics_data(self, data: Dict[str, Any]):
        """Import analytics data"""
        try:
            # Import contributions
            if "contributions" in data:
                for contrib_data in data["contributions"]:
                    contribution = Contribution(
                        id=contrib_data["id"],
                        user_id=contrib_data["user_id"],
                        contribution_type=ContributionType(contrib_data["contribution_type"]),
                        title=contrib_data["title"],
                        description=contrib_data["description"],
                        content=contrib_data["content"],
                        status=ContributionStatus(contrib_data["status"]),
                        quality_rating=QualityRating(contrib_data["quality_rating"]),
                        views=contrib_data.get("views", 0),
                        likes=contrib_data.get("likes", 0),
                        comments=contrib_data.get("comments", 0),
                        shares=contrib_data.get("shares", 0),
                        metadata=contrib_data.get("metadata", {}),
                        created_at=datetime.fromisoformat(contrib_data["created_at"]),
                        updated_at=datetime.fromisoformat(contrib_data["updated_at"]),
                        published_at=datetime.fromisoformat(contrib_data["published_at"]) if contrib_data.get("published_at") else None
                    )
                    self.contributions[contribution.id] = contribution
            
            # Import contributor profiles
            if "contributor_profiles" in data:
                for profile_data in data["contributor_profiles"]:
                    profile = ContributorProfile(
                        user_id=profile_data["user_id"],
                        contributor_level=ContributorLevel(profile_data["contributor_level"]),
                        total_contributions=profile_data.get("total_contributions", 0),
                        approved_contributions=profile_data.get("approved_contributions", 0),
                        rejected_contributions=profile_data.get("rejected_contributions", 0),
                        pending_contributions=profile_data.get("pending_contributions", 0),
                        total_views=profile_data.get("total_views", 0),
                        total_likes=profile_data.get("total_likes", 0),
                        total_comments=profile_data.get("total_comments", 0),
                        average_quality_rating=profile_data.get("average_quality_rating", 0.0),
                        contribution_score=profile_data.get("contribution_score", 0.0),
                        last_contribution=datetime.fromisoformat(profile_data["last_contribution"]),
                        metadata=profile_data.get("metadata", {}),
                        created_at=datetime.fromisoformat(profile_data["created_at"]),
                        updated_at=datetime.fromisoformat(profile_data["updated_at"])
                    )
                    self.contributor_profiles[profile.user_id] = profile
            
            # Import analytics
            if "analytics" in data:
                for analytics_data in data["analytics"]:
                    analytics = ContributionAnalytics(
                        id=analytics_data["id"],
                        period=analytics_data["period"],
                        start_date=datetime.fromisoformat(analytics_data["start_date"]),
                        end_date=datetime.fromisoformat(analytics_data["end_date"]),
                        total_contributions=analytics_data.get("total_contributions", 0),
                        approved_contributions=analytics_data.get("approved_contributions", 0),
                        rejected_contributions=analytics_data.get("rejected_contributions", 0),
                        pending_contributions=analytics_data.get("pending_contributions", 0),
                        total_views=analytics_data.get("total_views", 0),
                        total_likes=analytics_data.get("total_likes", 0),
                        total_comments=analytics_data.get("total_comments", 0),
                        average_quality_rating=analytics_data.get("average_quality_rating", 0.0),
                        top_contributors=analytics_data.get("top_contributors", []),
                        top_contributions=analytics_data.get("top_contributions", []),
                        contribution_trends=analytics_data.get("contribution_trends", {}),
                        created_at=datetime.fromisoformat(analytics_data["created_at"])
                    )
                    self.contribution_analytics[analytics.id] = analytics
            
            logger.info("Analytics data imported successfully")
            
        except Exception as e:
            logger.error(f"Error importing analytics data: {e}")
            raise
