"""
Community Engagement Programs for AnyLab AI Assistant

This module provides comprehensive community engagement capabilities including
user engagement tracking, community programs, gamification, social features,
and community-driven content development for the AnyLab platform.
"""

import os
import json
import logging
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional, Tuple
from dataclasses import dataclass, asdict
from enum import Enum
from django.conf import settings
from django.core.cache import cache
from django.utils import timezone
from django.contrib.auth.models import User

logger = logging.getLogger(__name__)


class EngagementLevel(Enum):
    """User engagement levels"""
    INACTIVE = "inactive"
    CASUAL = "casual"
    REGULAR = "regular"
    ACTIVE = "active"
    POWER_USER = "power_user"
    EXPERT = "expert"


class ProgramType(Enum):
    """Types of community programs"""
    CONTRIBUTION_CHALLENGE = "contribution_challenge"
    KNOWLEDGE_SHARING = "knowledge_sharing"
    PEER_REVIEW = "peer_review"
    MENTORSHIP = "mentorship"
    BETA_TESTING = "beta_testing"
    FEEDBACK_COLLECTION = "feedback_collection"
    COMMUNITY_EVENTS = "community_events"
    RECOGNITION_PROGRAM = "recognition_program"


class AchievementType(Enum):
    """Types of achievements"""
    CONTRIBUTION = "contribution"
    QUALITY = "quality"
    COLLABORATION = "collaboration"
    LEARNING = "learning"
    LEADERSHIP = "leadership"
    INNOVATION = "innovation"
    COMMUNITY = "community"


class SocialInteractionType(Enum):
    """Types of social interactions"""
    LIKE = "like"
    COMMENT = "comment"
    SHARE = "share"
    FOLLOW = "follow"
    MENTION = "mention"
    TAG = "tag"
    BOOKMARK = "bookmark"
    RATE = "rate"


@dataclass
class UserEngagementProfile:
    """User engagement profile"""
    user_id: str
    engagement_level: EngagementLevel
    total_points: int
    contribution_score: int
    quality_score: int
    collaboration_score: int
    learning_score: int
    last_active: datetime
    streak_days: int
    achievements: List[str]
    badges: List[str]
    social_connections: List[str]
    preferences: Dict[str, Any]


@dataclass
class CommunityProgram:
    """Community program data structure"""
    id: str
    name: str
    description: str
    program_type: ProgramType
    start_date: datetime
    end_date: Optional[datetime]
    status: str  # active, inactive, completed
    participants: List[str]
    goals: List[str]
    rewards: List[str]
    requirements: Dict[str, Any]
    progress_tracking: Dict[str, Any]
    created_by: str
    created_at: datetime


@dataclass
class Achievement:
    """Achievement data structure"""
    id: str
    name: str
    description: str
    achievement_type: AchievementType
    requirements: Dict[str, Any]
    points: int
    badge_icon: str
    rarity: str  # common, uncommon, rare, epic, legendary
    unlocked_by: List[str]
    created_at: datetime


@dataclass
class SocialInteraction:
    """Social interaction data structure"""
    id: str
    user_id: str
    target_id: str  # content, user, etc.
    interaction_type: SocialInteractionType
    content: Optional[str]
    created_at: datetime
    metadata: Dict[str, Any]


@dataclass
class CommunityEvent:
    """Community event data structure"""
    id: str
    title: str
    description: str
    event_type: str
    start_date: datetime
    end_date: datetime
    location: str  # virtual, physical, hybrid
    max_participants: Optional[int]
    participants: List[str]
    agenda: List[str]
    resources: List[str]
    organizer: str
    status: str  # planned, active, completed, cancelled


class EngagementTracker:
    """Tracks user engagement and activity"""
    
    def __init__(self):
        self.user_profiles = {}
        self.activity_log = []
        self.engagement_metrics = self._initialize_engagement_metrics()
    
    def _initialize_engagement_metrics(self) -> Dict[str, Any]:
        """Initialize engagement metrics configuration"""
        return {
            "engagement_levels": {
                EngagementLevel.INACTIVE: {"min_points": 0, "max_points": 10},
                EngagementLevel.CASUAL: {"min_points": 11, "max_points": 50},
                EngagementLevel.REGULAR: {"min_points": 51, "max_points": 150},
                EngagementLevel.ACTIVE: {"min_points": 151, "max_points": 300},
                EngagementLevel.POWER_USER: {"min_points": 301, "max_points": 600},
                EngagementLevel.EXPERT: {"min_points": 601, "max_points": 1000}
            },
            "point_values": {
                "content_upload": 10,
                "content_review": 5,
                "comment": 2,
                "like": 1,
                "share": 3,
                "helpful_answer": 15,
                "peer_review": 8,
                "mentorship": 20,
                "event_participation": 12
            }
        }
    
    def create_user_profile(self, user_id: str) -> UserEngagementProfile:
        """Create engagement profile for new user"""
        profile = UserEngagementProfile(
            user_id=user_id,
            engagement_level=EngagementLevel.CASUAL,
            total_points=0,
            contribution_score=0,
            quality_score=0,
            collaboration_score=0,
            learning_score=0,
            last_active=timezone.now(),
            streak_days=0,
            achievements=[],
            badges=[],
            social_connections=[],
            preferences={}
        )
        
        self.user_profiles[user_id] = profile
        logger.info(f"Created engagement profile for user: {user_id}")
        return profile
    
    def record_activity(self, user_id: str, activity_type: str, points: int = 0,
                       metadata: Dict[str, Any] = None) -> bool:
        """Record user activity and update engagement"""
        if user_id not in self.user_profiles:
            self.create_user_profile(user_id)
        
        profile = self.user_profiles[user_id]
        
        # Update points
        profile.total_points += points
        
        # Update specific scores based on activity type
        if activity_type in ["content_upload", "content_review", "helpful_answer"]:
            profile.contribution_score += points
        elif activity_type in ["peer_review", "quality_feedback"]:
            profile.quality_score += points
        elif activity_type in ["comment", "share", "mentorship"]:
            profile.collaboration_score += points
        elif activity_type in ["learning_completed", "training_finished"]:
            profile.learning_score += points
        
        # Update last active
        profile.last_active = timezone.now()
        
        # Update streak
        self._update_streak(profile)
        
        # Update engagement level
        self._update_engagement_level(profile)
        
        # Log activity
        activity_record = {
            "user_id": user_id,
            "activity_type": activity_type,
            "points": points,
            "timestamp": timezone.now(),
            "metadata": metadata or {}
        }
        self.activity_log.append(activity_record)
        
        logger.info(f"Recorded activity for user {user_id}: {activity_type} (+{points} points)")
        return True
    
    def _update_streak(self, profile: UserEngagementProfile):
        """Update user's activity streak"""
        current_time = timezone.now()
        time_diff = current_time - profile.last_active
        
        if time_diff.days <= 1:
            profile.streak_days += 1
        else:
            profile.streak_days = 1
    
    def _update_engagement_level(self, profile: UserEngagementProfile):
        """Update user's engagement level based on points"""
        for level, thresholds in self.engagement_metrics["engagement_levels"].items():
            if thresholds["min_points"] <= profile.total_points <= thresholds["max_points"]:
                profile.engagement_level = level
                break
    
    def get_user_profile(self, user_id: str) -> Optional[UserEngagementProfile]:
        """Get user engagement profile"""
        return self.user_profiles.get(user_id)
    
    def get_engagement_leaderboard(self, limit: int = 10) -> List[Dict[str, Any]]:
        """Get engagement leaderboard"""
        sorted_users = sorted(
            self.user_profiles.values(),
            key=lambda x: x.total_points,
            reverse=True
        )
        
        leaderboard = []
        for i, profile in enumerate(sorted_users[:limit]):
            leaderboard.append({
                "rank": i + 1,
                "user_id": profile.user_id,
                "total_points": profile.total_points,
                "engagement_level": profile.engagement_level.value,
                "streak_days": profile.streak_days
            })
        
        return leaderboard
    
    def get_engagement_analytics(self, start_date: datetime, end_date: datetime) -> Dict[str, Any]:
        """Get engagement analytics for a period"""
        activities_in_range = [
            activity for activity in self.activity_log
            if start_date <= activity["timestamp"] <= end_date
        ]
        
        analytics = {
            "total_activities": len(activities_in_range),
            "unique_users": len(set(activity["user_id"] for activity in activities_in_range)),
            "activity_types": {},
            "points_distributed": sum(activity["points"] for activity in activities_in_range),
            "engagement_levels": {},
            "top_contributors": []
        }
        
        # Count activity types
        for activity in activities_in_range:
            activity_type = activity["activity_type"]
            analytics["activity_types"][activity_type] = analytics["activity_types"].get(activity_type, 0) + 1
        
        # Count engagement levels
        for profile in self.user_profiles.values():
            level = profile.engagement_level.value
            analytics["engagement_levels"][level] = analytics["engagement_levels"].get(level, 0) + 1
        
        # Top contributors
        user_points = {}
        for activity in activities_in_range:
            user_id = activity["user_id"]
            user_points[user_id] = user_points.get(user_id, 0) + activity["points"]
        
        top_contributors = sorted(user_points.items(), key=lambda x: x[1], reverse=True)[:5]
        analytics["top_contributors"] = [
            {"user_id": user_id, "points": points} for user_id, points in top_contributors
        ]
        
        return analytics


class CommunityProgramManager:
    """Manages community programs and initiatives"""
    
    def __init__(self):
        self.programs = {}
        self.program_counter = 0
    
    def create_program(self, name: str, description: str, program_type: ProgramType,
                      start_date: datetime, end_date: Optional[datetime],
                      created_by: str, goals: List[str] = None,
                      rewards: List[str] = None) -> CommunityProgram:
        """Create a new community program"""
        self.program_counter += 1
        program_id = f"CP-{self.program_counter:06d}"
        
        program = CommunityProgram(
            id=program_id,
            name=name,
            description=description,
            program_type=program_type,
            start_date=start_date,
            end_date=end_date,
            status="active" if start_date <= timezone.now() else "planned",
            participants=[],
            goals=goals or [],
            rewards=rewards or [],
            requirements={},
            progress_tracking={},
            created_by=created_by,
            created_at=timezone.now()
        )
        
        self.programs[program_id] = program
        logger.info(f"Created community program: {program_id}")
        return program
    
    def join_program(self, program_id: str, user_id: str) -> bool:
        """Join a community program"""
        if program_id not in self.programs:
            return False
        
        program = self.programs[program_id]
        
        if user_id not in program.participants:
            program.participants.append(user_id)
            logger.info(f"User {user_id} joined program {program_id}")
            return True
        
        return False
    
    def leave_program(self, program_id: str, user_id: str) -> bool:
        """Leave a community program"""
        if program_id not in self.programs:
            return False
        
        program = self.programs[program_id]
        
        if user_id in program.participants:
            program.participants.remove(user_id)
            logger.info(f"User {user_id} left program {program_id}")
            return True
        
        return False
    
    def update_program_progress(self, program_id: str, user_id: str, 
                              progress_data: Dict[str, Any]) -> bool:
        """Update program progress for a user"""
        if program_id not in self.programs:
            return False
        
        program = self.programs[program_id]
        
        if user_id not in program.participants:
            return False
        
        # Initialize progress tracking for user if not exists
        if user_id not in program.progress_tracking:
            program.progress_tracking[user_id] = {}
        
        # Update progress
        program.progress_tracking[user_id].update(progress_data)
        program.progress_tracking[user_id]["last_updated"] = timezone.now()
        
        logger.info(f"Updated progress for user {user_id} in program {program_id}")
        return True
    
    def get_program(self, program_id: str) -> Optional[CommunityProgram]:
        """Get program by ID"""
        return self.programs.get(program_id)
    
    def get_active_programs(self) -> List[CommunityProgram]:
        """Get all active programs"""
        return [program for program in self.programs.values() if program.status == "active"]
    
    def get_user_programs(self, user_id: str) -> List[CommunityProgram]:
        """Get programs user is participating in"""
        return [program for program in self.programs.values() if user_id in program.participants]


class AchievementSystem:
    """Manages achievements and badges"""
    
    def __init__(self):
        self.achievements = {}
        self.user_achievements = {}
        self.initialize_default_achievements()
    
    def initialize_default_achievements(self):
        """Initialize default achievements"""
        default_achievements = [
            {
                "id": "first_contribution",
                "name": "First Contribution",
                "description": "Make your first content contribution",
                "type": AchievementType.CONTRIBUTION,
                "requirements": {"contributions": 1},
                "points": 10,
                "rarity": "common"
            },
            {
                "id": "quality_reviewer",
                "name": "Quality Reviewer",
                "description": "Complete 10 peer reviews",
                "type": AchievementType.QUALITY,
                "requirements": {"reviews": 10},
                "points": 50,
                "rarity": "uncommon"
            },
            {
                "id": "community_helper",
                "name": "Community Helper",
                "description": "Provide 25 helpful answers",
                "type": AchievementType.COLLABORATION,
                "requirements": {"helpful_answers": 25},
                "points": 100,
                "rarity": "rare"
            },
            {
                "id": "knowledge_expert",
                "name": "Knowledge Expert",
                "description": "Achieve expert engagement level",
                "type": AchievementType.LEADERSHIP,
                "requirements": {"engagement_level": "expert"},
                "points": 200,
                "rarity": "epic"
            },
            {
                "id": "streak_master",
                "name": "Streak Master",
                "description": "Maintain 30-day activity streak",
                "type": AchievementType.COMMUNITY,
                "requirements": {"streak_days": 30},
                "points": 150,
                "rarity": "rare"
            }
        ]
        
        for achievement_data in default_achievements:
            achievement = Achievement(
                id=achievement_data["id"],
                name=achievement_data["name"],
                description=achievement_data["description"],
                achievement_type=achievement_data["type"],
                requirements=achievement_data["requirements"],
                points=achievement_data["points"],
                badge_icon=f"badge_{achievement_data['id']}.png",
                rarity=achievement_data["rarity"],
                unlocked_by=[],
                created_at=timezone.now()
            )
            self.achievements[achievement.id] = achievement
    
    def check_achievements(self, user_id: str, user_profile: UserEngagementProfile) -> List[str]:
        """Check if user has unlocked any new achievements"""
        unlocked_achievements = []
        
        for achievement_id, achievement in self.achievements.items():
            if achievement_id in user_profile.achievements:
                continue  # Already unlocked
            
            if self._check_achievement_requirements(achievement, user_profile):
                unlocked_achievements.append(achievement_id)
                user_profile.achievements.append(achievement_id)
                achievement.unlocked_by.append(user_id)
                
                logger.info(f"User {user_id} unlocked achievement: {achievement.name}")
        
        return unlocked_achievements
    
    def _check_achievement_requirements(self, achievement: Achievement, 
                                      user_profile: UserEngagementProfile) -> bool:
        """Check if user meets achievement requirements"""
        requirements = achievement.requirements
        
        if "contributions" in requirements:
            if user_profile.contribution_score < requirements["contributions"] * 10:
                return False
        
        if "reviews" in requirements:
            # This would need to be tracked separately in a real implementation
            pass
        
        if "helpful_answers" in requirements:
            # This would need to be tracked separately in a real implementation
            pass
        
        if "engagement_level" in requirements:
            if user_profile.engagement_level.value != requirements["engagement_level"]:
                return False
        
        if "streak_days" in requirements:
            if user_profile.streak_days < requirements["streak_days"]:
                return False
        
        return True
    
    def get_user_achievements(self, user_id: str) -> List[Achievement]:
        """Get achievements unlocked by user"""
        if user_id not in self.user_achievements:
            return []
        
        achievement_ids = self.user_achievements[user_id]
        return [self.achievements[aid] for aid in achievement_ids if aid in self.achievements]
    
    def get_achievement(self, achievement_id: str) -> Optional[Achievement]:
        """Get achievement by ID"""
        return self.achievements.get(achievement_id)


class SocialFeaturesManager:
    """Manages social features and interactions"""
    
    def __init__(self):
        self.interactions = {}
        self.interaction_counter = 0
        self.user_connections = {}
    
    def record_interaction(self, user_id: str, target_id: str, 
                          interaction_type: SocialInteractionType,
                          content: Optional[str] = None,
                          metadata: Dict[str, Any] = None) -> SocialInteraction:
        """Record a social interaction"""
        self.interaction_counter += 1
        interaction_id = f"SI-{self.interaction_counter:06d}"
        
        interaction = SocialInteraction(
            id=interaction_id,
            user_id=user_id,
            target_id=target_id,
            interaction_type=interaction_type,
            content=content,
            created_at=timezone.now(),
            metadata=metadata or {}
        )
        
        self.interactions[interaction_id] = interaction
        
        # Update user connections for follow interactions
        if interaction_type == SocialInteractionType.FOLLOW:
            if user_id not in self.user_connections:
                self.user_connections[user_id] = {"following": [], "followers": []}
            if target_id not in self.user_connections:
                self.user_connections[target_id] = {"following": [], "followers": []}
            
            self.user_connections[user_id]["following"].append(target_id)
            self.user_connections[target_id]["followers"].append(user_id)
        
        logger.info(f"Recorded interaction: {interaction_type.value} from {user_id} to {target_id}")
        return interaction
    
    def get_interactions_for_target(self, target_id: str, 
                                   interaction_type: Optional[SocialInteractionType] = None) -> List[SocialInteraction]:
        """Get interactions for a specific target"""
        interactions = [
            interaction for interaction in self.interactions.values()
            if interaction.target_id == target_id
        ]
        
        if interaction_type:
            interactions = [i for i in interactions if i.interaction_type == interaction_type]
        
        return sorted(interactions, key=lambda x: x.created_at, reverse=True)
    
    def get_user_feed(self, user_id: str, limit: int = 20) -> List[Dict[str, Any]]:
        """Get user's social feed"""
        # Get users that the current user follows
        following = self.user_connections.get(user_id, {}).get("following", [])
        
        # Get recent interactions from followed users
        feed_items = []
        for interaction in self.interactions.values():
            if interaction.user_id in following:
                feed_items.append({
                    "type": "interaction",
                    "interaction": interaction,
                    "timestamp": interaction.created_at
                })
        
        # Sort by timestamp and limit
        feed_items.sort(key=lambda x: x["timestamp"], reverse=True)
        return feed_items[:limit]
    
    def get_user_connections(self, user_id: str) -> Dict[str, List[str]]:
        """Get user's social connections"""
        return self.user_connections.get(user_id, {"following": [], "followers": []})


class CommunityEventManager:
    """Manages community events and gatherings"""
    
    def __init__(self):
        self.events = {}
        self.event_counter = 0
    
    def create_event(self, title: str, description: str, event_type: str,
                    start_date: datetime, end_date: datetime,
                    location: str, organizer: str,
                    max_participants: Optional[int] = None,
                    agenda: List[str] = None) -> CommunityEvent:
        """Create a new community event"""
        self.event_counter += 1
        event_id = f"CE-{self.event_counter:06d}"
        
        event = CommunityEvent(
            id=event_id,
            title=title,
            description=description,
            event_type=event_type,
            start_date=start_date,
            end_date=end_date,
            location=location,
            max_participants=max_participants,
            participants=[],
            agenda=agenda or [],
            resources=[],
            organizer=organizer,
            status="planned"
        )
        
        self.events[event_id] = event
        logger.info(f"Created community event: {event_id}")
        return event
    
    def register_for_event(self, event_id: str, user_id: str) -> bool:
        """Register user for an event"""
        if event_id not in self.events:
            return False
        
        event = self.events[event_id]
        
        # Check if event is full
        if event.max_participants and len(event.participants) >= event.max_participants:
            return False
        
        if user_id not in event.participants:
            event.participants.append(user_id)
            logger.info(f"User {user_id} registered for event {event_id}")
            return True
        
        return False
    
    def cancel_event_registration(self, event_id: str, user_id: str) -> bool:
        """Cancel user's event registration"""
        if event_id not in self.events:
            return False
        
        event = self.events[event_id]
        
        if user_id in event.participants:
            event.participants.remove(user_id)
            logger.info(f"User {user_id} cancelled registration for event {event_id}")
            return True
        
        return False
    
    def get_upcoming_events(self, limit: int = 10) -> List[CommunityEvent]:
        """Get upcoming community events"""
        current_time = timezone.now()
        upcoming_events = [
            event for event in self.events.values()
            if event.start_date > current_time and event.status == "planned"
        ]
        
        return sorted(upcoming_events, key=lambda x: x.start_date)[:limit]
    
    def get_event(self, event_id: str) -> Optional[CommunityEvent]:
        """Get event by ID"""
        return self.events.get(event_id)


class CommunityEngagementAnalytics:
    """Provides analytics for community engagement"""
    
    def __init__(self, engagement_tracker: EngagementTracker,
                 program_manager: CommunityProgramManager,
                 achievement_system: AchievementSystem,
                 social_manager: SocialFeaturesManager):
        self.engagement_tracker = engagement_tracker
        self.program_manager = program_manager
        self.achievement_system = achievement_system
        self.social_manager = social_manager
    
    def get_community_health_metrics(self) -> Dict[str, Any]:
        """Get overall community health metrics"""
        total_users = len(self.engagement_tracker.user_profiles)
        active_users = len([
            profile for profile in self.engagement_tracker.user_profiles.values()
            if (timezone.now() - profile.last_active).days <= 7
        ])
        
        total_programs = len(self.program_manager.programs)
        active_programs = len(self.program_manager.get_active_programs())
        
        total_events = len(self.social_manager.interactions)
        
        return {
            "total_users": total_users,
            "active_users": active_users,
            "user_activity_rate": active_users / max(total_users, 1),
            "total_programs": total_programs,
            "active_programs": active_programs,
            "total_interactions": total_events,
            "engagement_levels": self._get_engagement_level_distribution(),
            "top_achievements": self._get_top_achievements()
        }
    
    def _get_engagement_level_distribution(self) -> Dict[str, int]:
        """Get distribution of user engagement levels"""
        distribution = {}
        for profile in self.engagement_tracker.user_profiles.values():
            level = profile.engagement_level.value
            distribution[level] = distribution.get(level, 0) + 1
        return distribution
    
    def _get_top_achievements(self) -> List[Dict[str, Any]]:
        """Get most unlocked achievements"""
        achievement_counts = {}
        for achievement in self.achievement_system.achievements.values():
            achievement_counts[achievement.name] = len(achievement.unlocked_by)
        
        sorted_achievements = sorted(
            achievement_counts.items(),
            key=lambda x: x[1],
            reverse=True
        )
        
        return [
            {"name": name, "unlocked_count": count}
            for name, count in sorted_achievements[:5]
        ]
    
    def get_program_analytics(self, program_id: str) -> Dict[str, Any]:
        """Get analytics for a specific program"""
        program = self.program_manager.get_program(program_id)
        if not program:
            return {"error": "Program not found"}
        
        analytics = {
            "program_id": program_id,
            "name": program.name,
            "total_participants": len(program.participants),
            "completion_rate": 0.0,
            "average_progress": 0.0,
            "top_participants": []
        }
        
        # Calculate completion rate and average progress
        if program.progress_tracking:
            completed_participants = len([
                user_id for user_id, progress in program.progress_tracking.items()
                if progress.get("completed", False)
            ])
            analytics["completion_rate"] = completed_participants / len(program.participants)
            
            # Calculate average progress
            total_progress = sum(
                progress.get("progress", 0) for progress in program.progress_tracking.values()
            )
            analytics["average_progress"] = total_progress / len(program.progress_tracking)
        
        return analytics
    
    def generate_engagement_report(self, start_date: datetime, end_date: datetime) -> Dict[str, Any]:
        """Generate comprehensive engagement report"""
        report = {
            "period": {
                "start": start_date,
                "end": end_date
            },
            "engagement_analytics": self.engagement_tracker.get_engagement_analytics(start_date, end_date),
            "community_health": self.get_community_health_metrics(),
            "program_performance": self._get_program_performance_analytics(),
            "social_activity": self._get_social_activity_analytics(start_date, end_date),
            "recommendations": []
        }
        
        # Generate recommendations
        if report["community_health"]["user_activity_rate"] < 0.3:
            report["recommendations"].append("Low user activity - consider engagement campaigns")
        
        if report["community_health"]["active_programs"] == 0:
            report["recommendations"].append("No active programs - launch new community initiatives")
        
        return report
    
    def _get_program_performance_analytics(self) -> Dict[str, Any]:
        """Get program performance analytics"""
        programs = self.program_manager.programs.values()
        
        return {
            "total_programs": len(programs),
            "active_programs": len([p for p in programs if p.status == "active"]),
            "average_participants": sum(len(p.participants) for p in programs) / max(len(programs), 1),
            "most_popular_program": max(programs, key=lambda p: len(p.participants)).name if programs else None
        }
    
    def _get_social_activity_analytics(self, start_date: datetime, end_date: datetime) -> Dict[str, Any]:
        """Get social activity analytics"""
        interactions_in_range = [
            interaction for interaction in self.social_manager.interactions.values()
            if start_date <= interaction.created_at <= end_date
        ]
        
        return {
            "total_interactions": len(interactions_in_range),
            "interaction_types": {
                interaction_type.value: len([
                    i for i in interactions_in_range if i.interaction_type == interaction_type
                ])
                for interaction_type in SocialInteractionType
            },
            "most_active_users": self._get_most_active_users(interactions_in_range)
        }
    
    def _get_most_active_users(self, interactions: List[SocialInteraction]) -> List[Dict[str, Any]]:
        """Get most active users from interactions"""
        user_activity = {}
        for interaction in interactions:
            user_id = interaction.user_id
            user_activity[user_id] = user_activity.get(user_id, 0) + 1
        
        sorted_users = sorted(user_activity.items(), key=lambda x: x[1], reverse=True)
        return [
            {"user_id": user_id, "interaction_count": count}
            for user_id, count in sorted_users[:5]
        ]


# Example usage and testing
if __name__ == "__main__":
    # Initialize community engagement system
    engagement_tracker = EngagementTracker()
    program_manager = CommunityProgramManager()
    achievement_system = AchievementSystem()
    social_manager = SocialFeaturesManager()
    event_manager = CommunityEventManager()
    analytics = CommunityEngagementAnalytics(
        engagement_tracker, program_manager, achievement_system, social_manager
    )
    
    # Create user profiles
    user1_profile = engagement_tracker.create_user_profile("user_001")
    user2_profile = engagement_tracker.create_user_profile("user_002")
    
    # Record activities
    engagement_tracker.record_activity("user_001", "content_upload", 10)
    engagement_tracker.record_activity("user_001", "comment", 2)
    engagement_tracker.record_activity("user_002", "content_review", 5)
    engagement_tracker.record_activity("user_002", "like", 1)
    
    print(f"User 1 total points: {user1_profile.total_points}")
    print(f"User 1 engagement level: {user1_profile.engagement_level.value}")
    
    # Create community program
    program = program_manager.create_program(
        "Knowledge Sharing Challenge",
        "Share your expertise and help the community",
        ProgramType.KNOWLEDGE_SHARING,
        timezone.now(),
        timezone.now() + timedelta(days=30),
        "admin",
        ["Share 5 helpful articles", "Get 10 positive reviews"],
        ["Expert badge", "100 points bonus"]
    )
    
    # Join program
    program_manager.join_program(program.id, "user_001")
    program_manager.join_program(program.id, "user_002")
    
    print(f"Program participants: {len(program.participants)}")
    
    # Check achievements
    unlocked = achievement_system.check_achievements("user_001", user1_profile)
    print(f"User 1 unlocked achievements: {len(unlocked)}")
    
    # Record social interactions
    social_manager.record_interaction("user_001", "user_002", SocialInteractionType.FOLLOW)
    social_manager.record_interaction("user_001", "content_123", SocialInteractionType.LIKE)
    
    # Create community event
    event = event_manager.create_event(
        "Monthly Knowledge Share",
        "Monthly community knowledge sharing session",
        "virtual_meeting",
        timezone.now() + timedelta(days=7),
        timezone.now() + timedelta(days=7, hours=2),
        "virtual",
        "admin",
        max_participants=50,
        agenda=["Welcome", "Presentations", "Q&A", "Networking"]
    )
    
    # Register for event
    event_manager.register_for_event(event.id, "user_001")
    event_manager.register_for_event(event.id, "user_002")
    
    print(f"Event participants: {len(event.participants)}")
    
    # Get analytics
    health_metrics = analytics.get_community_health_metrics()
    print(f"Community health metrics: {health_metrics}")
    
    print("\nCommunity Engagement Programs initialized successfully!")
