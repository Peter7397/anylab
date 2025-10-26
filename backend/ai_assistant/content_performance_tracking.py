"""
Content Performance Tracking

This module provides comprehensive content performance tracking and analytics,
including content popularity, engagement metrics, search performance, and user satisfaction.
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


class PerformanceMetric(Enum):
    """Performance metric enumeration"""
    VIEWS = "views"
    CLICKS = "clicks"
    DOWNLOADS = "downloads"
    SEARCHES = "searches"
    ENGAGEMENT_TIME = "engagement_time"
    BOUNCE_RATE = "bounce_rate"
    CONVERSION_RATE = "conversion_rate"
    USER_SATISFACTION = "user_satisfaction"


class ContentType(Enum):
    """Content type enumeration"""
    DOCUMENT = "document"
    VIDEO = "video"
    IMAGE = "image"
    AUDIO = "audio"
    WEBPAGE = "webpage"
    TUTORIAL = "tutorial"
    FAQ = "faq"
    TROUBLESHOOTING = "troubleshooting"


class PerformanceLevel(Enum):
    """Performance level enumeration"""
    EXCELLENT = "excellent"
    GOOD = "good"
    AVERAGE = "average"
    POOR = "poor"
    CRITICAL = "critical"


@dataclass
class ContentPerformance:
    """Content performance structure"""
    id: str
    content_id: str
    content_type: ContentType
    title: str
    views: int = 0
    clicks: int = 0
    downloads: int = 0
    searches: int = 0
    engagement_time: float = 0.0  # seconds
    bounce_rate: float = 0.0
    conversion_rate: float = 0.0
    user_satisfaction: float = 0.0
    performance_score: float = 0.0
    performance_level: PerformanceLevel = PerformanceLevel.AVERAGE
    metadata: Dict[str, Any] = field(default_factory=dict)
    created_at: datetime = field(default_factory=lambda: django_timezone.now())
    updated_at: datetime = field(default_factory=lambda: django_timezone.now())


@dataclass
class PerformanceEvent:
    """Performance event structure"""
    id: str
    content_id: str
    event_type: PerformanceMetric
    user_id: str
    timestamp: datetime
    value: float
    metadata: Dict[str, Any] = field(default_factory=dict)
    created_at: datetime = field(default_factory=lambda: django_timezone.now())


@dataclass
class PerformanceTrend:
    """Performance trend structure"""
    id: str
    content_id: str
    metric: PerformanceMetric
    period: str  # "daily", "weekly", "monthly"
    start_date: datetime
    end_date: datetime
    values: List[float] = field(default_factory=list)
    trend_direction: str = "stable"  # "up", "down", "stable"
    trend_percentage: float = 0.0
    created_at: datetime = field(default_factory=lambda: django_timezone.now())


class ContentPerformanceTracking:
    """Content Performance Tracking System"""
    
    def __init__(self, config: Dict[str, Any] = None):
        """Initialize content performance tracking"""
        self.config = config or {}
        self.tracking_enabled = self.config.get('tracking_enabled', True)
        self.analytics_enabled = self.config.get('analytics_enabled', True)
        self.trend_analysis = self.config.get('trend_analysis', True)
        self.cache_enabled = self.config.get('cache_enabled', True)
        self.retention_days = self.config.get('retention_days', 365)
        
        # Initialize components
        self.content_performance = {}
        self.performance_events = {}
        self.performance_trends = {}
        self.cache = cache if self.cache_enabled else None
        
        # Initialize tracking system
        self._initialize_tracking_system()
        
        logger.info("Content Performance Tracking initialized")
    
    def _initialize_tracking_system(self):
        """Initialize tracking system components"""
        try:
            # Initialize sample content performance data
            self._initialize_sample_content()
            
            logger.info("Tracking system components initialized")
            
        except Exception as e:
            logger.error(f"Error initializing tracking system: {e}")
            raise
    
    def _initialize_sample_content(self):
        """Initialize sample content performance data"""
        try:
            sample_content = [
                {
                    "id": "content_1",
                    "content_id": "doc_001",
                    "content_type": ContentType.DOCUMENT,
                    "title": "OpenLab User Guide",
                    "views": 1250,
                    "clicks": 890,
                    "downloads": 340,
                    "searches": 45,
                    "engagement_time": 180.5,
                    "bounce_rate": 0.15,
                    "conversion_rate": 0.25,
                    "user_satisfaction": 4.2
                },
                {
                    "id": "content_2",
                    "content_id": "video_001",
                    "content_type": ContentType.VIDEO,
                    "title": "ChemStation Tutorial",
                    "views": 2100,
                    "clicks": 1500,
                    "downloads": 120,
                    "searches": 78,
                    "engagement_time": 420.0,
                    "bounce_rate": 0.08,
                    "conversion_rate": 0.35,
                    "user_satisfaction": 4.5
                },
                {
                    "id": "content_3",
                    "content_id": "faq_001",
                    "content_type": ContentType.FAQ,
                    "title": "Common Troubleshooting Issues",
                    "views": 890,
                    "clicks": 650,
                    "downloads": 45,
                    "searches": 120,
                    "engagement_time": 95.0,
                    "bounce_rate": 0.22,
                    "conversion_rate": 0.18,
                    "user_satisfaction": 3.8
                }
            ]
            
            for content_data in sample_content:
                performance = ContentPerformance(**content_data)
                performance.performance_score = self._calculate_performance_score(performance)
                performance.performance_level = self._determine_performance_level(performance.performance_score)
                self.content_performance[performance.id] = performance
            
            logger.info(f"Initialized {len(self.content_performance)} content performance records")
            
        except Exception as e:
            logger.error(f"Error initializing sample content: {e}")
            raise
    
    def track_performance_event(self, content_id: str, event_type: PerformanceMetric, 
                              user_id: str, value: float = 1.0, metadata: Dict[str, Any] = None) -> str:
        """Track a content performance event"""
        try:
            if not self.tracking_enabled:
                return ""
            
            # Generate event ID
            event_id = f"event_{content_id}_{event_type.value}_{django_timezone.now().strftime('%Y%m%d_%H%M%S')}_{hash(str(metadata)) % 10000}"
            
            # Create performance event
            event = PerformanceEvent(
                id=event_id,
                content_id=content_id,
                event_type=event_type,
                user_id=user_id,
                timestamp=django_timezone.now(),
                value=value,
                metadata=metadata or {}
            )
            
            # Store event
            self.performance_events[event_id] = event
            
            # Update content performance
            self._update_content_performance(event)
            
            logger.debug(f"Tracked performance event: {event_id}")
            return event_id
            
        except Exception as e:
            logger.error(f"Error tracking performance event: {e}")
            return ""
    
    def _update_content_performance(self, event: PerformanceEvent):
        """Update content performance with event"""
        try:
            # Find content performance record
            content_perf = None
            for perf in self.content_performance.values():
                if perf.content_id == event.content_id:
                    content_perf = perf
                    break
            
            if not content_perf:
                # Create new content performance record
                content_perf = ContentPerformance(
                    id=f"perf_{event.content_id}",
                    content_id=event.content_id,
                    content_type=ContentType.DOCUMENT,  # Default type
                    title=f"Content {event.content_id}",
                    metadata={"auto_created": True}
                )
                self.content_performance[content_perf.id] = content_perf
            
            # Update metrics based on event type
            if event.event_type == PerformanceMetric.VIEWS:
                content_perf.views += int(event.value)
            elif event.event_type == PerformanceMetric.CLICKS:
                content_perf.clicks += int(event.value)
            elif event.event_type == PerformanceMetric.DOWNLOADS:
                content_perf.downloads += int(event.value)
            elif event.event_type == PerformanceMetric.SEARCHES:
                content_perf.searches += int(event.value)
            elif event.event_type == PerformanceMetric.ENGAGEMENT_TIME:
                content_perf.engagement_time = (content_perf.engagement_time + event.value) / 2
            elif event.event_type == PerformanceMetric.BOUNCE_RATE:
                content_perf.bounce_rate = event.value
            elif event.event_type == PerformanceMetric.CONVERSION_RATE:
                content_perf.conversion_rate = event.value
            elif event.event_type == PerformanceMetric.USER_SATISFACTION:
                content_perf.user_satisfaction = event.value
            
            # Recalculate performance score and level
            content_perf.performance_score = self._calculate_performance_score(content_perf)
            content_perf.performance_level = self._determine_performance_level(content_perf.performance_score)
            content_perf.updated_at = django_timezone.now()
            
        except Exception as e:
            logger.error(f"Error updating content performance: {e}")
    
    def _calculate_performance_score(self, performance: ContentPerformance) -> float:
        """Calculate content performance score"""
        try:
            score = 0.0
            
            # Views score (0-25 points)
            if performance.views > 1000:
                score += 25
            elif performance.views > 500:
                score += 20
            elif performance.views > 100:
                score += 15
            elif performance.views > 50:
                score += 10
            elif performance.views > 10:
                score += 5
            
            # Clicks score (0-20 points)
            if performance.clicks > 500:
                score += 20
            elif performance.clicks > 200:
                score += 15
            elif performance.clicks > 100:
                score += 10
            elif performance.clicks > 50:
                score += 5
            
            # Downloads score (0-15 points)
            if performance.downloads > 100:
                score += 15
            elif performance.downloads > 50:
                score += 12
            elif performance.downloads > 20:
                score += 8
            elif performance.downloads > 5:
                score += 4
            
            # Engagement time score (0-15 points)
            if performance.engagement_time > 300:
                score += 15
            elif performance.engagement_time > 180:
                score += 12
            elif performance.engagement_time > 60:
                score += 8
            elif performance.engagement_time > 30:
                score += 4
            
            # Bounce rate score (0-10 points, inverted)
            if performance.bounce_rate < 0.1:
                score += 10
            elif performance.bounce_rate < 0.2:
                score += 8
            elif performance.bounce_rate < 0.3:
                score += 5
            elif performance.bounce_rate < 0.5:
                score += 2
            
            # Conversion rate score (0-10 points)
            if performance.conversion_rate > 0.3:
                score += 10
            elif performance.conversion_rate > 0.2:
                score += 8
            elif performance.conversion_rate > 0.1:
                score += 5
            elif performance.conversion_rate > 0.05:
                score += 2
            
            # User satisfaction score (0-5 points)
            if performance.user_satisfaction > 4.5:
                score += 5
            elif performance.user_satisfaction > 4.0:
                score += 4
            elif performance.user_satisfaction > 3.5:
                score += 3
            elif performance.user_satisfaction > 3.0:
                score += 2
            elif performance.user_satisfaction > 2.0:
                score += 1
            
            return min(score, 100.0)  # Cap at 100
            
        except Exception as e:
            logger.error(f"Error calculating performance score: {e}")
            return 0.0
    
    def _determine_performance_level(self, score: float) -> PerformanceLevel:
        """Determine performance level from score"""
        try:
            if score >= 90:
                return PerformanceLevel.EXCELLENT
            elif score >= 75:
                return PerformanceLevel.GOOD
            elif score >= 50:
                return PerformanceLevel.AVERAGE
            elif score >= 25:
                return PerformanceLevel.POOR
            else:
                return PerformanceLevel.CRITICAL
                
        except Exception as e:
            logger.error(f"Error determining performance level: {e}")
            return PerformanceLevel.CRITICAL
    
    def get_content_performance(self, content_id: str) -> Optional[ContentPerformance]:
        """Get content performance by ID"""
        try:
            for performance in self.content_performance.values():
                if performance.content_id == content_id:
                    return performance
            return None
            
        except Exception as e:
            logger.error(f"Error getting content performance: {e}")
            return None
    
    def get_top_performing_content(self, limit: int = 10, content_type: ContentType = None) -> List[ContentPerformance]:
        """Get top performing content"""
        try:
            content_list = list(self.content_performance.values())
            
            # Filter by content type if specified
            if content_type:
                content_list = [c for c in content_list if c.content_type == content_type]
            
            # Sort by performance score
            content_list.sort(key=lambda x: x.performance_score, reverse=True)
            
            return content_list[:limit]
            
        except Exception as e:
            logger.error(f"Error getting top performing content: {e}")
            return []
    
    def get_content_trends(self, content_id: str, metric: PerformanceMetric, 
                          period: str = "weekly", days: int = 30) -> PerformanceTrend:
        """Get content performance trends"""
        try:
            # Get events for content and metric
            events = []
            for event in self.performance_events.values():
                if (event.content_id == content_id and 
                    event.event_type == metric and
                    event.timestamp >= django_timezone.now() - timedelta(days=days)):
                    events.append(event)
            
            # Sort by timestamp
            events.sort(key=lambda x: x.timestamp)
            
            # Calculate trend values
            values = []
            if period == "daily":
                # Group by day
                current_date = django_timezone.now().date()
                for i in range(days):
                    date = current_date - timedelta(days=i)
                    day_events = [e for e in events if e.timestamp.date() == date]
                    values.insert(0, sum(e.value for e in day_events))
            elif period == "weekly":
                # Group by week
                weeks = days // 7
                for i in range(weeks):
                    week_start = django_timezone.now() - timedelta(weeks=i+1)
                    week_end = django_timezone.now() - timedelta(weeks=i)
                    week_events = [e for e in events if week_start <= e.timestamp < week_end]
                    values.insert(0, sum(e.value for e in week_events))
            else:  # monthly
                months = days // 30
                for i in range(months):
                    month_start = django_timezone.now() - timedelta(days=30*(i+1))
                    month_end = django_timezone.now() - timedelta(days=30*i)
                    month_events = [e for e in events if month_start <= e.timestamp < month_end]
                    values.insert(0, sum(e.value for e in month_events))
            
            # Calculate trend direction and percentage
            trend_direction = "stable"
            trend_percentage = 0.0
            
            if len(values) >= 2:
                recent_avg = statistics.mean(values[-3:]) if len(values) >= 3 else values[-1]
                older_avg = statistics.mean(values[:3]) if len(values) >= 3 else values[0]
                
                if older_avg > 0:
                    trend_percentage = ((recent_avg - older_avg) / older_avg) * 100
                    
                    if trend_percentage > 10:
                        trend_direction = "up"
                    elif trend_percentage < -10:
                        trend_direction = "down"
                    else:
                        trend_direction = "stable"
            
            # Create trend
            trend = PerformanceTrend(
                id=f"trend_{content_id}_{metric.value}_{period}_{django_timezone.now().strftime('%Y%m%d_%H%M%S')}",
                content_id=content_id,
                metric=metric,
                period=period,
                start_date=django_timezone.now() - timedelta(days=days),
                end_date=django_timezone.now(),
                values=values,
                trend_direction=trend_direction,
                trend_percentage=trend_percentage
            )
            
            self.performance_trends[trend.id] = trend
            return trend
            
        except Exception as e:
            logger.error(f"Error getting content trends: {e}")
            return None
    
    def get_performance_analytics(self) -> Dict[str, Any]:
        """Get performance analytics"""
        try:
            analytics = {
                "total_content": len(self.content_performance),
                "total_events": len(self.performance_events),
                "total_trends": len(self.performance_trends),
                "content_by_type": {},
                "content_by_performance_level": {},
                "average_performance_score": 0.0,
                "top_performing_content": [],
                "trending_content": [],
                "performance_metrics": {
                    "total_views": 0,
                    "total_clicks": 0,
                    "total_downloads": 0,
                    "total_searches": 0,
                    "average_engagement_time": 0.0,
                    "average_bounce_rate": 0.0,
                    "average_conversion_rate": 0.0,
                    "average_user_satisfaction": 0.0
                }
            }
            
            # Count content by type and performance level
            total_score = 0
            total_views = 0
            total_clicks = 0
            total_downloads = 0
            total_searches = 0
            total_engagement_time = 0
            total_bounce_rate = 0
            total_conversion_rate = 0
            total_satisfaction = 0
            
            for performance in self.content_performance.values():
                # Count by type
                content_type = performance.content_type.value
                analytics["content_by_type"][content_type] = analytics["content_by_type"].get(content_type, 0) + 1
                
                # Count by performance level
                level = performance.performance_level.value
                analytics["content_by_performance_level"][level] = analytics["content_by_performance_level"].get(level, 0) + 1
                
                # Sum metrics
                total_score += performance.performance_score
                total_views += performance.views
                total_clicks += performance.clicks
                total_downloads += performance.downloads
                total_searches += performance.searches
                total_engagement_time += performance.engagement_time
                total_bounce_rate += performance.bounce_rate
                total_conversion_rate += performance.conversion_rate
                total_satisfaction += performance.user_satisfaction
            
            # Calculate averages
            if len(self.content_performance) > 0:
                analytics["average_performance_score"] = total_score / len(self.content_performance)
                analytics["performance_metrics"]["total_views"] = total_views
                analytics["performance_metrics"]["total_clicks"] = total_clicks
                analytics["performance_metrics"]["total_downloads"] = total_downloads
                analytics["performance_metrics"]["total_searches"] = total_searches
                analytics["performance_metrics"]["average_engagement_time"] = total_engagement_time / len(self.content_performance)
                analytics["performance_metrics"]["average_bounce_rate"] = total_bounce_rate / len(self.content_performance)
                analytics["performance_metrics"]["average_conversion_rate"] = total_conversion_rate / len(self.content_performance)
                analytics["performance_metrics"]["average_user_satisfaction"] = total_satisfaction / len(self.content_performance)
            
            # Get top performing content
            analytics["top_performing_content"] = [
                {
                    "content_id": perf.content_id,
                    "title": perf.title,
                    "performance_score": perf.performance_score,
                    "performance_level": perf.performance_level.value
                }
                for perf in self.get_top_performing_content(5)
            ]
            
            return analytics
            
        except Exception as e:
            logger.error(f"Error getting performance analytics: {e}")
            return {}
    
    def get_performance_statistics(self) -> Dict[str, Any]:
        """Get performance tracking statistics"""
        try:
            stats = {
                "total_content": len(self.content_performance),
                "total_events": len(self.performance_events),
                "total_trends": len(self.performance_trends),
                "events_by_type": {},
                "content_by_type": {},
                "content_by_performance_level": {},
                "trends_by_period": {},
                "tracking_enabled": self.tracking_enabled,
                "analytics_enabled": self.analytics_enabled,
                "trend_analysis": self.trend_analysis
            }
            
            # Count events by type
            for event in self.performance_events.values():
                event_type = event.event_type.value
                stats["events_by_type"][event_type] = stats["events_by_type"].get(event_type, 0) + 1
            
            # Count content by type
            for performance in self.content_performance.values():
                content_type = performance.content_type.value
                stats["content_by_type"][content_type] = stats["content_by_type"].get(content_type, 0) + 1
                
                level = performance.performance_level.value
                stats["content_by_performance_level"][level] = stats["content_by_performance_level"].get(level, 0) + 1
            
            # Count trends by period
            for trend in self.performance_trends.values():
                period = trend.period
                stats["trends_by_period"][period] = stats["trends_by_period"].get(period, 0) + 1
            
            return stats
            
        except Exception as e:
            logger.error(f"Error getting performance statistics: {e}")
            return {}
    
    def export_performance_data(self) -> Dict[str, Any]:
        """Export performance tracking data"""
        try:
            return {
                "content_performance": [
                    {
                        "id": perf.id,
                        "content_id": perf.content_id,
                        "content_type": perf.content_type.value,
                        "title": perf.title,
                        "views": perf.views,
                        "clicks": perf.clicks,
                        "downloads": perf.downloads,
                        "searches": perf.searches,
                        "engagement_time": perf.engagement_time,
                        "bounce_rate": perf.bounce_rate,
                        "conversion_rate": perf.conversion_rate,
                        "user_satisfaction": perf.user_satisfaction,
                        "performance_score": perf.performance_score,
                        "performance_level": perf.performance_level.value,
                        "metadata": perf.metadata,
                        "created_at": perf.created_at.isoformat(),
                        "updated_at": perf.updated_at.isoformat()
                    }
                    for perf in self.content_performance.values()
                ],
                "performance_events": [
                    {
                        "id": event.id,
                        "content_id": event.content_id,
                        "event_type": event.event_type.value,
                        "user_id": event.user_id,
                        "timestamp": event.timestamp.isoformat(),
                        "value": event.value,
                        "metadata": event.metadata,
                        "created_at": event.created_at.isoformat()
                    }
                    for event in self.performance_events.values()
                ],
                "performance_trends": [
                    {
                        "id": trend.id,
                        "content_id": trend.content_id,
                        "metric": trend.metric.value,
                        "period": trend.period,
                        "start_date": trend.start_date.isoformat(),
                        "end_date": trend.end_date.isoformat(),
                        "values": trend.values,
                        "trend_direction": trend.trend_direction,
                        "trend_percentage": trend.trend_percentage,
                        "created_at": trend.created_at.isoformat()
                    }
                    for trend in self.performance_trends.values()
                ]
            }
            
        except Exception as e:
            logger.error(f"Error exporting performance data: {e}")
            return {}
    
    def import_performance_data(self, data: Dict[str, Any]):
        """Import performance tracking data"""
        try:
            # Import content performance
            if "content_performance" in data:
                for perf_data in data["content_performance"]:
                    performance = ContentPerformance(
                        id=perf_data["id"],
                        content_id=perf_data["content_id"],
                        content_type=ContentType(perf_data["content_type"]),
                        title=perf_data["title"],
                        views=perf_data.get("views", 0),
                        clicks=perf_data.get("clicks", 0),
                        downloads=perf_data.get("downloads", 0),
                        searches=perf_data.get("searches", 0),
                        engagement_time=perf_data.get("engagement_time", 0.0),
                        bounce_rate=perf_data.get("bounce_rate", 0.0),
                        conversion_rate=perf_data.get("conversion_rate", 0.0),
                        user_satisfaction=perf_data.get("user_satisfaction", 0.0),
                        performance_score=perf_data.get("performance_score", 0.0),
                        performance_level=PerformanceLevel(perf_data["performance_level"]),
                        metadata=perf_data.get("metadata", {}),
                        created_at=datetime.fromisoformat(perf_data["created_at"]),
                        updated_at=datetime.fromisoformat(perf_data["updated_at"])
                    )
                    self.content_performance[performance.id] = performance
            
            # Import performance events
            if "performance_events" in data:
                for event_data in data["performance_events"]:
                    event = PerformanceEvent(
                        id=event_data["id"],
                        content_id=event_data["content_id"],
                        event_type=PerformanceMetric(event_data["event_type"]),
                        user_id=event_data["user_id"],
                        timestamp=datetime.fromisoformat(event_data["timestamp"]),
                        value=event_data["value"],
                        metadata=event_data.get("metadata", {}),
                        created_at=datetime.fromisoformat(event_data["created_at"])
                    )
                    self.performance_events[event.id] = event
            
            # Import performance trends
            if "performance_trends" in data:
                for trend_data in data["performance_trends"]:
                    trend = PerformanceTrend(
                        id=trend_data["id"],
                        content_id=trend_data["content_id"],
                        metric=PerformanceMetric(trend_data["metric"]),
                        period=trend_data["period"],
                        start_date=datetime.fromisoformat(trend_data["start_date"]),
                        end_date=datetime.fromisoformat(trend_data["end_date"]),
                        values=trend_data.get("values", []),
                        trend_direction=trend_data.get("trend_direction", "stable"),
                        trend_percentage=trend_data.get("trend_percentage", 0.0),
                        created_at=datetime.fromisoformat(trend_data["created_at"])
                    )
                    self.performance_trends[trend.id] = trend
            
            logger.info("Performance tracking data imported successfully")
            
        except Exception as e:
            logger.error(f"Error importing performance data: {e}")
            raise
