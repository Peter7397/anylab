"""
User Behavior Tracking

This module provides comprehensive user behavior tracking and analytics,
including user interactions, navigation patterns, content preferences, and engagement metrics.
"""

import logging
import json
import hashlib
from typing import Dict, Any, List, Optional, Tuple, Union
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from enum import Enum
from django.utils import timezone as django_timezone
from django.core.cache import cache
from django.contrib.auth.models import User

logger = logging.getLogger(__name__)


class BehaviorEventType(Enum):
    """Behavior event type enumeration"""
    PAGE_VIEW = "page_view"
    CLICK = "click"
    SEARCH = "search"
    DOWNLOAD = "download"
    UPLOAD = "upload"
    NAVIGATION = "navigation"
    SESSION_START = "session_start"
    SESSION_END = "session_end"
    CONTENT_INTERACTION = "content_interaction"
    FEATURE_USAGE = "feature_usage"


class UserSegment(Enum):
    """User segment enumeration"""
    NEW_USER = "new_user"
    REGULAR_USER = "regular_user"
    POWER_USER = "power_user"
    EXPERT_USER = "expert_user"
    INACTIVE_USER = "inactive_user"


class EngagementLevel(Enum):
    """Engagement level enumeration"""
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    VERY_HIGH = "very_high"


@dataclass
class BehaviorEvent:
    """Behavior event structure"""
    id: str
    user_id: str
    event_type: BehaviorEventType
    timestamp: datetime
    page_url: str
    element_id: Optional[str] = None
    element_type: Optional[str] = None
    content_id: Optional[str] = None
    search_query: Optional[str] = None
    session_id: str = ""
    metadata: Dict[str, Any] = field(default_factory=dict)
    created_at: datetime = field(default_factory=lambda: django_timezone.now())


@dataclass
class UserSession:
    """User session structure"""
    id: str
    user_id: str
    start_time: datetime
    end_time: Optional[datetime] = None
    page_views: int = 0
    clicks: int = 0
    searches: int = 0
    downloads: int = 0
    uploads: int = 0
    duration: int = 0  # seconds
    pages_visited: List[str] = field(default_factory=list)
    features_used: List[str] = field(default_factory=list)
    metadata: Dict[str, Any] = field(default_factory=dict)
    created_at: datetime = field(default_factory=lambda: django_timezone.now())
    updated_at: datetime = field(default_factory=lambda: django_timezone.now())


@dataclass
class UserProfile:
    """User profile structure"""
    user_id: str
    segment: UserSegment
    engagement_level: EngagementLevel
    total_sessions: int = 0
    total_page_views: int = 0
    total_clicks: int = 0
    total_searches: int = 0
    total_downloads: int = 0
    total_uploads: int = 0
    average_session_duration: float = 0.0
    favorite_content_types: List[str] = field(default_factory=list)
    favorite_features: List[str] = field(default_factory=list)
    last_activity: datetime = field(default_factory=lambda: django_timezone.now())
    metadata: Dict[str, Any] = field(default_factory=dict)
    created_at: datetime = field(default_factory=lambda: django_timezone.now())
    updated_at: datetime = field(default_factory=lambda: django_timezone.now())


class UserBehaviorTracking:
    """User Behavior Tracking System"""
    
    def __init__(self, config: Dict[str, Any] = None):
        """Initialize user behavior tracking"""
        self.config = config or {}
        self.tracking_enabled = self.config.get('tracking_enabled', True)
        self.analytics_enabled = self.config.get('analytics_enabled', True)
        self.privacy_enabled = self.config.get('privacy_enabled', True)
        self.cache_enabled = self.config.get('cache_enabled', True)
        self.retention_days = self.config.get('retention_days', 90)
        
        # Initialize components
        self.behavior_events = {}
        self.user_sessions = {}
        self.user_profiles = {}
        self.cache = cache if self.cache_enabled else None
        
        # Initialize tracking system
        self._initialize_tracking_system()
        
        logger.info("User Behavior Tracking initialized")
    
    def _initialize_tracking_system(self):
        """Initialize tracking system components"""
        try:
            # Initialize user profiles for existing users
            self._initialize_user_profiles()
            
            logger.info("Tracking system components initialized")
            
        except Exception as e:
            logger.error(f"Error initializing tracking system: {e}")
            raise
    
    def _initialize_user_profiles(self):
        """Initialize user profiles"""
        try:
            # Mock user profiles
            mock_users = [
                {
                    "user_id": "user_1",
                    "segment": UserSegment.REGULAR_USER,
                    "engagement_level": EngagementLevel.MEDIUM
                },
                {
                    "user_id": "user_2",
                    "segment": UserSegment.POWER_USER,
                    "engagement_level": EngagementLevel.HIGH
                },
                {
                    "user_id": "user_3",
                    "segment": UserSegment.NEW_USER,
                    "engagement_level": EngagementLevel.LOW
                }
            ]
            
            for user_data in mock_users:
                profile = UserProfile(**user_data)
                self.user_profiles[profile.user_id] = profile
            
            logger.info(f"Initialized {len(self.user_profiles)} user profiles")
            
        except Exception as e:
            logger.error(f"Error initializing user profiles: {e}")
            raise
    
    def track_event(self, user_id: str, event_type: BehaviorEventType, page_url: str,
                   element_id: str = None, element_type: str = None, content_id: str = None,
                   search_query: str = None, session_id: str = None, metadata: Dict[str, Any] = None) -> str:
        """Track a user behavior event"""
        try:
            if not self.tracking_enabled:
                return ""
            
            # Generate event ID
            event_id = f"event_{user_id}_{event_type.value}_{django_timezone.now().strftime('%Y%m%d_%H%M%S')}_{hash(str(metadata)) % 10000}"
            
            # Create behavior event
            event = BehaviorEvent(
                id=event_id,
                user_id=user_id,
                event_type=event_type,
                timestamp=django_timezone.now(),
                page_url=page_url,
                element_id=element_id,
                element_type=element_type,
                content_id=content_id,
                search_query=search_query,
                session_id=session_id or self._get_or_create_session(user_id),
                metadata=metadata or {}
            )
            
            # Store event
            self.behavior_events[event_id] = event
            
            # Update user session
            self._update_user_session(event)
            
            # Update user profile
            self._update_user_profile(event)
            
            logger.debug(f"Tracked event: {event_id}")
            return event_id
            
        except Exception as e:
            logger.error(f"Error tracking event: {e}")
            return ""
    
    def _get_or_create_session(self, user_id: str) -> str:
        """Get or create user session"""
        try:
            # Check for active session
            for session in self.user_sessions.values():
                if session.user_id == user_id and session.end_time is None:
                    return session.id
            
            # Create new session
            session_id = f"session_{user_id}_{django_timezone.now().strftime('%Y%m%d_%H%M%S')}"
            session = UserSession(
                id=session_id,
                user_id=user_id,
                start_time=django_timezone.now()
            )
            
            self.user_sessions[session_id] = session
            return session_id
            
        except Exception as e:
            logger.error(f"Error getting or creating session: {e}")
            return f"session_{user_id}_{django_timezone.now().strftime('%Y%m%d_%H%M%S')}"
    
    def _update_user_session(self, event: BehaviorEvent):
        """Update user session with event"""
        try:
            session = self.user_sessions.get(event.session_id)
            if not session:
                return
            
            # Update session metrics
            if event.event_type == BehaviorEventType.PAGE_VIEW:
                session.page_views += 1
                if event.page_url not in session.pages_visited:
                    session.pages_visited.append(event.page_url)
            elif event.event_type == BehaviorEventType.CLICK:
                session.clicks += 1
            elif event.event_type == BehaviorEventType.SEARCH:
                session.searches += 1
            elif event.event_type == BehaviorEventType.DOWNLOAD:
                session.downloads += 1
            elif event.event_type == BehaviorEventType.UPLOAD:
                session.uploads += 1
            
            # Update features used
            if event.element_type and event.element_type not in session.features_used:
                session.features_used.append(event.element_type)
            
            # Update session
            session.updated_at = django_timezone.now()
            
        except Exception as e:
            logger.error(f"Error updating user session: {e}")
    
    def _update_user_profile(self, event: BehaviorEvent):
        """Update user profile with event"""
        try:
            profile = self.user_profiles.get(event.user_id)
            if not profile:
                # Create new profile
                profile = UserProfile(
                    user_id=event.user_id,
                    segment=UserSegment.NEW_USER,
                    engagement_level=EngagementLevel.LOW
                )
                self.user_profiles[event.user_id] = profile
            
            # Update profile metrics
            if event.event_type == BehaviorEventType.PAGE_VIEW:
                profile.total_page_views += 1
            elif event.event_type == BehaviorEventType.CLICK:
                profile.total_clicks += 1
            elif event.event_type == BehaviorEventType.SEARCH:
                profile.total_searches += 1
            elif event.event_type == BehaviorEventType.DOWNLOAD:
                profile.total_downloads += 1
            elif event.event_type == BehaviorEventType.UPLOAD:
                profile.total_uploads += 1
            
            # Update last activity
            profile.last_activity = event.timestamp
            
            # Update engagement level
            profile.engagement_level = self._calculate_engagement_level(profile)
            
            # Update segment
            profile.segment = self._calculate_user_segment(profile)
            
            # Update profile
            profile.updated_at = django_timezone.now()
            
        except Exception as e:
            logger.error(f"Error updating user profile: {e}")
    
    def _calculate_engagement_level(self, profile: UserProfile) -> EngagementLevel:
        """Calculate user engagement level"""
        try:
            # Calculate engagement score
            score = 0
            
            # Page views score
            if profile.total_page_views > 100:
                score += 3
            elif profile.total_page_views > 50:
                score += 2
            elif profile.total_page_views > 10:
                score += 1
            
            # Clicks score
            if profile.total_clicks > 200:
                score += 3
            elif profile.total_clicks > 100:
                score += 2
            elif profile.total_clicks > 20:
                score += 1
            
            # Searches score
            if profile.total_searches > 50:
                score += 3
            elif profile.total_searches > 20:
                score += 2
            elif profile.total_searches > 5:
                score += 1
            
            # Downloads score
            if profile.total_downloads > 20:
                score += 2
            elif profile.total_downloads > 5:
                score += 1
            
            # Uploads score
            if profile.total_uploads > 10:
                score += 2
            elif profile.total_uploads > 2:
                score += 1
            
            # Determine engagement level
            if score >= 10:
                return EngagementLevel.VERY_HIGH
            elif score >= 7:
                return EngagementLevel.HIGH
            elif score >= 4:
                return EngagementLevel.MEDIUM
            else:
                return EngagementLevel.LOW
                
        except Exception as e:
            logger.error(f"Error calculating engagement level: {e}")
            return EngagementLevel.LOW
    
    def _calculate_user_segment(self, profile: UserProfile) -> UserSegment:
        """Calculate user segment"""
        try:
            # Check if user is inactive
            days_since_activity = (django_timezone.now() - profile.last_activity).days
            if days_since_activity > 30:
                return UserSegment.INACTIVE_USER
            
            # Calculate segment based on activity
            total_activity = (profile.total_page_views + profile.total_clicks + 
                           profile.total_searches + profile.total_downloads + profile.total_uploads)
            
            if total_activity > 500:
                return UserSegment.EXPERT_USER
            elif total_activity > 200:
                return UserSegment.POWER_USER
            elif total_activity > 50:
                return UserSegment.REGULAR_USER
            else:
                return UserSegment.NEW_USER
                
        except Exception as e:
            logger.error(f"Error calculating user segment: {e}")
            return UserSegment.NEW_USER
    
    def end_session(self, session_id: str):
        """End a user session"""
        try:
            session = self.user_sessions.get(session_id)
            if not session:
                return
            
            # Calculate session duration
            session.end_time = django_timezone.now()
            session.duration = int((session.end_time - session.start_time).total_seconds())
            
            # Update user profile
            profile = self.user_profiles.get(session.user_id)
            if profile:
                profile.total_sessions += 1
                
                # Update average session duration
                if profile.total_sessions > 0:
                    total_duration = profile.average_session_duration * (profile.total_sessions - 1) + session.duration
                    profile.average_session_duration = total_duration / profile.total_sessions
                
                profile.updated_at = django_timezone.now()
            
            logger.info(f"Ended session: {session_id}, duration: {session.duration}s")
            
        except Exception as e:
            logger.error(f"Error ending session: {e}")
    
    def get_user_profile(self, user_id: str) -> Optional[UserProfile]:
        """Get user profile by ID"""
        return self.user_profiles.get(user_id)
    
    def get_user_session(self, session_id: str) -> Optional[UserSession]:
        """Get user session by ID"""
        return self.user_sessions.get(session_id)
    
    def get_user_events(self, user_id: str, event_type: BehaviorEventType = None, 
                       start_date: datetime = None, end_date: datetime = None) -> List[BehaviorEvent]:
        """Get user events"""
        try:
            events = []
            
            for event in self.behavior_events.values():
                if event.user_id != user_id:
                    continue
                
                # Filter by event type
                if event_type and event.event_type != event_type:
                    continue
                
                # Filter by date range
                if start_date and event.timestamp < start_date:
                    continue
                if end_date and event.timestamp > end_date:
                    continue
                
                events.append(event)
            
            # Sort by timestamp
            events.sort(key=lambda x: x.timestamp, reverse=True)
            
            return events
            
        except Exception as e:
            logger.error(f"Error getting user events: {e}")
            return []
    
    def get_user_analytics(self, user_id: str) -> Dict[str, Any]:
        """Get user analytics"""
        try:
            profile = self.user_profiles.get(user_id)
            if not profile:
                return {}
            
            # Get recent events
            recent_events = self.get_user_events(user_id, start_date=django_timezone.now() - timedelta(days=7))
            
            # Calculate analytics
            analytics = {
                "user_id": user_id,
                "segment": profile.segment.value,
                "engagement_level": profile.engagement_level.value,
                "total_sessions": profile.total_sessions,
                "total_page_views": profile.total_page_views,
                "total_clicks": profile.total_clicks,
                "total_searches": profile.total_searches,
                "total_downloads": profile.total_downloads,
                "total_uploads": profile.total_uploads,
                "average_session_duration": profile.average_session_duration,
                "last_activity": profile.last_activity.isoformat(),
                "recent_activity": {
                    "events_last_7_days": len(recent_events),
                    "page_views_last_7_days": len([e for e in recent_events if e.event_type == BehaviorEventType.PAGE_VIEW]),
                    "clicks_last_7_days": len([e for e in recent_events if e.event_type == BehaviorEventType.CLICK]),
                    "searches_last_7_days": len([e for e in recent_events if e.event_type == BehaviorEventType.SEARCH])
                },
                "favorite_content_types": profile.favorite_content_types,
                "favorite_features": profile.favorite_features
            }
            
            return analytics
            
        except Exception as e:
            logger.error(f"Error getting user analytics: {e}")
            return {}
    
    def get_behavior_statistics(self) -> Dict[str, Any]:
        """Get behavior tracking statistics"""
        try:
            stats = {
                "total_events": len(self.behavior_events),
                "total_sessions": len(self.user_sessions),
                "total_users": len(self.user_profiles),
                "events_by_type": {},
                "users_by_segment": {},
                "users_by_engagement": {},
                "active_sessions": 0,
                "tracking_enabled": self.tracking_enabled,
                "analytics_enabled": self.analytics_enabled,
                "privacy_enabled": self.privacy_enabled
            }
            
            # Count events by type
            for event in self.behavior_events.values():
                event_type = event.event_type.value
                stats["events_by_type"][event_type] = stats["events_by_type"].get(event_type, 0) + 1
            
            # Count users by segment
            for profile in self.user_profiles.values():
                segment = profile.segment.value
                stats["users_by_segment"][segment] = stats["users_by_segment"].get(segment, 0) + 1
                
                engagement = profile.engagement_level.value
                stats["users_by_engagement"][engagement] = stats["users_by_engagement"].get(engagement, 0) + 1
            
            # Count active sessions
            for session in self.user_sessions.values():
                if session.end_time is None:
                    stats["active_sessions"] += 1
            
            return stats
            
        except Exception as e:
            logger.error(f"Error getting behavior statistics: {e}")
            return {}
    
    def export_behavior_data(self) -> Dict[str, Any]:
        """Export behavior tracking data"""
        try:
            return {
                "events": [
                    {
                        "id": event.id,
                        "user_id": event.user_id,
                        "event_type": event.event_type.value,
                        "timestamp": event.timestamp.isoformat(),
                        "page_url": event.page_url,
                        "element_id": event.element_id,
                        "element_type": event.element_type,
                        "content_id": event.content_id,
                        "search_query": event.search_query,
                        "session_id": event.session_id,
                        "metadata": event.metadata,
                        "created_at": event.created_at.isoformat()
                    }
                    for event in self.behavior_events.values()
                ],
                "sessions": [
                    {
                        "id": session.id,
                        "user_id": session.user_id,
                        "start_time": session.start_time.isoformat(),
                        "end_time": session.end_time.isoformat() if session.end_time else None,
                        "page_views": session.page_views,
                        "clicks": session.clicks,
                        "searches": session.searches,
                        "downloads": session.downloads,
                        "uploads": session.uploads,
                        "duration": session.duration,
                        "pages_visited": session.pages_visited,
                        "features_used": session.features_used,
                        "metadata": session.metadata,
                        "created_at": session.created_at.isoformat(),
                        "updated_at": session.updated_at.isoformat()
                    }
                    for session in self.user_sessions.values()
                ],
                "profiles": [
                    {
                        "user_id": profile.user_id,
                        "segment": profile.segment.value,
                        "engagement_level": profile.engagement_level.value,
                        "total_sessions": profile.total_sessions,
                        "total_page_views": profile.total_page_views,
                        "total_clicks": profile.total_clicks,
                        "total_searches": profile.total_searches,
                        "total_downloads": profile.total_downloads,
                        "total_uploads": profile.total_uploads,
                        "average_session_duration": profile.average_session_duration,
                        "favorite_content_types": profile.favorite_content_types,
                        "favorite_features": profile.favorite_features,
                        "last_activity": profile.last_activity.isoformat(),
                        "metadata": profile.metadata,
                        "created_at": profile.created_at.isoformat(),
                        "updated_at": profile.updated_at.isoformat()
                    }
                    for profile in self.user_profiles.values()
                ]
            }
            
        except Exception as e:
            logger.error(f"Error exporting behavior data: {e}")
            return {}
    
    def import_behavior_data(self, data: Dict[str, Any]):
        """Import behavior tracking data"""
        try:
            # Import events
            if "events" in data:
                for event_data in data["events"]:
                    event = BehaviorEvent(
                        id=event_data["id"],
                        user_id=event_data["user_id"],
                        event_type=BehaviorEventType(event_data["event_type"]),
                        timestamp=datetime.fromisoformat(event_data["timestamp"]),
                        page_url=event_data["page_url"],
                        element_id=event_data.get("element_id"),
                        element_type=event_data.get("element_type"),
                        content_id=event_data.get("content_id"),
                        search_query=event_data.get("search_query"),
                        session_id=event_data.get("session_id", ""),
                        metadata=event_data.get("metadata", {}),
                        created_at=datetime.fromisoformat(event_data["created_at"])
                    )
                    self.behavior_events[event.id] = event
            
            # Import sessions
            if "sessions" in data:
                for session_data in data["sessions"]:
                    session = UserSession(
                        id=session_data["id"],
                        user_id=session_data["user_id"],
                        start_time=datetime.fromisoformat(session_data["start_time"]),
                        end_time=datetime.fromisoformat(session_data["end_time"]) if session_data.get("end_time") else None,
                        page_views=session_data.get("page_views", 0),
                        clicks=session_data.get("clicks", 0),
                        searches=session_data.get("searches", 0),
                        downloads=session_data.get("downloads", 0),
                        uploads=session_data.get("uploads", 0),
                        duration=session_data.get("duration", 0),
                        pages_visited=session_data.get("pages_visited", []),
                        features_used=session_data.get("features_used", []),
                        metadata=session_data.get("metadata", {}),
                        created_at=datetime.fromisoformat(session_data["created_at"]),
                        updated_at=datetime.fromisoformat(session_data["updated_at"])
                    )
                    self.user_sessions[session.id] = session
            
            # Import profiles
            if "profiles" in data:
                for profile_data in data["profiles"]:
                    profile = UserProfile(
                        user_id=profile_data["user_id"],
                        segment=UserSegment(profile_data["segment"]),
                        engagement_level=EngagementLevel(profile_data["engagement_level"]),
                        total_sessions=profile_data.get("total_sessions", 0),
                        total_page_views=profile_data.get("total_page_views", 0),
                        total_clicks=profile_data.get("total_clicks", 0),
                        total_searches=profile_data.get("total_searches", 0),
                        total_downloads=profile_data.get("total_downloads", 0),
                        total_uploads=profile_data.get("total_uploads", 0),
                        average_session_duration=profile_data.get("average_session_duration", 0.0),
                        favorite_content_types=profile_data.get("favorite_content_types", []),
                        favorite_features=profile_data.get("favorite_features", []),
                        last_activity=datetime.fromisoformat(profile_data["last_activity"]),
                        metadata=profile_data.get("metadata", {}),
                        created_at=datetime.fromisoformat(profile_data["created_at"]),
                        updated_at=datetime.fromisoformat(profile_data["updated_at"])
                    )
                    self.user_profiles[profile.user_id] = profile
            
            logger.info("Behavior tracking data imported successfully")
            
        except Exception as e:
            logger.error(f"Error importing behavior data: {e}")
            raise
