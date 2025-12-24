"""
Automated Content Update Detection

This module provides automated detection of content updates from various sources,
including websites, RSS feeds, APIs, and file systems.
"""

import logging
import hashlib
import requests
import feedparser
from typing import Dict, Any, List, Optional, Tuple, Union
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from enum import Enum
from django.utils import timezone as django_timezone
from django.core.cache import cache
import schedule
import time
import threading

logger = logging.getLogger(__name__)


class UpdateSource(Enum):
    """Update source enumeration"""
    WEBSITE = "website"
    RSS_FEED = "rss_feed"
    API = "api"
    FILE_SYSTEM = "file_system"
    GIT_REPOSITORY = "git_repository"
    DATABASE = "database"
    EMAIL = "email"
    SOCIAL_MEDIA = "social_media"


class UpdateType(Enum):
    """Update type enumeration"""
    CONTENT_ADDED = "content_added"
    CONTENT_MODIFIED = "content_modified"
    CONTENT_DELETED = "content_deleted"
    CONTENT_MOVED = "content_moved"
    METADATA_CHANGED = "metadata_changed"
    STRUCTURE_CHANGED = "structure_changed"


class UpdatePriority(Enum):
    """Update priority enumeration"""
    CRITICAL = "critical"
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"
    INFORMATIONAL = "informational"


@dataclass
class UpdateSource:
    """Update source structure"""
    id: str
    name: str
    source_type: UpdateSource
    url: str
    config: Dict[str, Any] = field(default_factory=dict)
    enabled: bool = True
    last_check: Optional[datetime] = None
    last_update: Optional[datetime] = None
    check_interval: int = 3600  # seconds
    metadata: Dict[str, Any] = field(default_factory=dict)
    created_at: datetime = field(default_factory=lambda: django_timezone.now())
    updated_at: datetime = field(default_factory=lambda: django_timezone.now())


@dataclass
class ContentUpdate:
    """Content update structure"""
    id: str
    source_id: str
    update_type: UpdateType
    priority: UpdatePriority
    title: str
    description: str
    content_hash: str
    old_content: Optional[str] = None
    new_content: Optional[str] = None
    metadata: Dict[str, Any] = field(default_factory=dict)
    detected_at: datetime = field(default_factory=lambda: django_timezone.now())
    processed_at: Optional[datetime] = None
    status: str = "pending"


class AutomatedContentUpdateDetection:
    """Automated Content Update Detection System"""
    
    def __init__(self, config: Dict[str, Any] = None):
        """Initialize update detection system"""
        self.config = config or {}
        self.detection_enabled = self.config.get('detection_enabled', True)
        self.auto_processing = self.config.get('auto_processing', True)
        self.notification_enabled = self.config.get('notification_enabled', True)
        self.cache_enabled = self.config.get('cache_enabled', True)
        self.max_concurrent_checks = self.config.get('max_concurrent_checks', 5)
        
        # Initialize components
        self.update_sources = {}
        self.content_updates = {}
        self.content_hashes = {}
        self.cache = cache if self.cache_enabled else None
        self.scheduler = schedule
        self.running = False
        self.worker_thread = None
        
        # Initialize detection system
        self._initialize_detection_system()
        
        logger.info("Automated Content Update Detection initialized")
    
    def _initialize_detection_system(self):
        """Initialize detection system components"""
        try:
            # Initialize detectors
            self.detectors = {
                UpdateSource.WEBSITE: self._detect_website_updates,
                UpdateSource.RSS_FEED: self._detect_rss_updates,
                UpdateSource.API: self._detect_api_updates,
                UpdateSource.FILE_SYSTEM: self._detect_filesystem_updates,
                UpdateSource.GIT_REPOSITORY: self._detect_git_updates,
                UpdateSource.DATABASE: self._detect_database_updates,
                UpdateSource.EMAIL: self._detect_email_updates,
                UpdateSource.SOCIAL_MEDIA: self._detect_social_media_updates
            }
            
            # Initialize processors
            self.processors = {
                UpdateType.CONTENT_ADDED: self._process_content_added,
                UpdateType.CONTENT_MODIFIED: self._process_content_modified,
                UpdateType.CONTENT_DELETED: self._process_content_deleted,
                UpdateType.CONTENT_MOVED: self._process_content_moved,
                UpdateType.METADATA_CHANGED: self._process_metadata_changed,
                UpdateType.STRUCTURE_CHANGED: self._process_structure_changed
            }
            
            # Initialize default sources
            self._create_default_sources()
            
            logger.info("Detection system components initialized")
            
        except Exception as e:
            logger.error(f"Error initializing detection system: {e}")
            raise
    
    def _create_default_sources(self):
        """Create default update sources"""
        try:
            default_sources = [
                {
                    "id": "agilent_website",
                    "name": "Agilent Website",
                    "source_type": UpdateSource.WEBSITE,
                    "url": "https://www.agilent.com",
                    "config": {"check_pages": ["/news", "/products", "/support"]},
                    "check_interval": 3600
                },
                {
                    "id": "agilent_rss",
                    "name": "Agilent RSS Feed",
                    "source_type": UpdateSource.RSS_FEED,
                    "url": "https://www.agilent.com/rss",
                    "config": {"max_items": 50},
                    "check_interval": 1800
                },
                {
                    "id": "openlab_help",
                    "name": "OpenLab Help Portal",
                    "source_type": UpdateSource.WEBSITE,
                    "url": "https://help.openlab.agilent.com",
                    "config": {"check_pages": ["/troubleshooting", "/faq"]},
                    "check_interval": 7200
                }
            ]
            
            for source_data in default_sources:
                source = UpdateSource(**source_data)
                self.update_sources[source.id] = source
            
            logger.info(f"Created {len(default_sources)} default sources")
            
        except Exception as e:
            logger.error(f"Error creating default sources: {e}")
            raise
    
    def add_update_source(self, source_id: str, name: str, source_type: UpdateSource,
                         url: str, config: Dict[str, Any] = None,
                         check_interval: int = 3600) -> UpdateSource:
        """Add an update source"""
        try:
            source = UpdateSource(
                id=source_id,
                name=name,
                source_type=source_type,
                url=url,
                config=config or {},
                check_interval=check_interval
            )
            
            self.update_sources[source_id] = source
            
            logger.info(f"Added update source: {source_id}")
            return source
            
        except Exception as e:
            logger.error(f"Error adding update source: {e}")
            raise
    
    def remove_update_source(self, source_id: str):
        """Remove an update source"""
        try:
            if source_id in self.update_sources:
                del self.update_sources[source_id]
                logger.info(f"Removed update source: {source_id}")
            
        except Exception as e:
            logger.error(f"Error removing update source: {e}")
    
    def start_detection(self):
        """Start automated detection"""
        try:
            if self.running:
                logger.warning("Detection already running")
                return
            
            self.running = True
            
            # Start worker thread
            self.worker_thread = threading.Thread(target=self._detection_worker)
            self.worker_thread.daemon = True
            self.worker_thread.start()
            
            logger.info("Automated detection started")
            
        except Exception as e:
            logger.error(f"Error starting detection: {e}")
            raise
    
    def stop_detection(self):
        """Stop automated detection"""
        try:
            self.running = False
            
            if self.worker_thread:
                self.worker_thread.join(timeout=5)
            
            logger.info("Automated detection stopped")
            
        except Exception as e:
            logger.error(f"Error stopping detection: {e}")
    
    def _detection_worker(self):
        """Detection worker thread"""
        try:
            while self.running:
                # Check all sources
                for source in self.update_sources.values():
                    if not source.enabled:
                        continue
                    
                    # Check if it's time to check this source
                    if self._should_check_source(source):
                        try:
                            self._check_source_for_updates(source)
                        except Exception as e:
                            logger.error(f"Error checking source {source.id}: {e}")
                
                # Sleep for a short time
                time.sleep(60)
                
        except Exception as e:
            logger.error(f"Error in detection worker: {e}")
    
    def _should_check_source(self, source: UpdateSource) -> bool:
        """Check if source should be checked"""
        try:
            if not source.last_check:
                return True
            
            time_since_last_check = django_timezone.now() - source.last_check
            return time_since_last_check.total_seconds() >= source.check_interval
            
        except Exception as e:
            logger.error(f"Error checking if source should be checked: {e}")
            return False
    
    def _check_source_for_updates(self, source: UpdateSource):
        """Check a source for updates"""
        try:
            # Get detector for source type
            detector = self.detectors.get(source.source_type)
            if not detector:
                logger.warning(f"No detector for source type: {source.source_type}")
                return
            
            # Detect updates
            updates = detector(source)
            
            # Process updates
            for update in updates:
                self._process_update(update)
            
            # Update source last check time
            source.last_check = django_timezone.now()
            
            logger.info(f"Checked source {source.id}, found {len(updates)} updates")
            
        except Exception as e:
            logger.error(f"Error checking source for updates: {e}")
    
    def _detect_website_updates(self, source: UpdateSource) -> List[ContentUpdate]:
        """Detect website updates"""
        try:
            updates = []
            
            # Mock website update detection
            # In production, use actual web scraping
            for i in range(3):  # Mock 3 updates
                update = ContentUpdate(
                    id=f"website_update_{source.id}_{i}",
                    source_id=source.id,
                    update_type=UpdateType.CONTENT_ADDED,
                    priority=UpdatePriority.MEDIUM,
                    title=f"Website Update {i}",
                    description=f"New content detected on {source.name}",
                    content_hash=hashlib.md5(f"content_{i}".encode()).hexdigest(),
                    new_content=f"New website content {i}",
                    metadata={"page": f"/page_{i}"}
                )
                updates.append(update)
            
            return updates
            
        except Exception as e:
            logger.error(f"Error detecting website updates: {e}")
            return []
    
    def _detect_rss_updates(self, source: UpdateSource) -> List[ContentUpdate]:
        """Detect RSS feed updates"""
        try:
            updates = []
            
            # Mock RSS update detection
            # In production, use feedparser
            for i in range(5):  # Mock 5 updates
                update = ContentUpdate(
                    id=f"rss_update_{source.id}_{i}",
                    source_id=source.id,
                    update_type=UpdateType.CONTENT_ADDED,
                    priority=UpdatePriority.HIGH,
                    title=f"RSS Update {i}",
                    description=f"New RSS item from {source.name}",
                    content_hash=hashlib.md5(f"rss_content_{i}".encode()).hexdigest(),
                    new_content=f"New RSS content {i}",
                    metadata={"feed_item": f"item_{i}"}
                )
                updates.append(update)
            
            return updates
            
        except Exception as e:
            logger.error(f"Error detecting RSS updates: {e}")
            return []
    
    def _detect_api_updates(self, source: UpdateSource) -> List[ContentUpdate]:
        """Detect API updates"""
        try:
            updates = []
            
            # Mock API update detection
            # In production, use actual API calls
            for i in range(2):  # Mock 2 updates
                update = ContentUpdate(
                    id=f"api_update_{source.id}_{i}",
                    source_id=source.id,
                    update_type=UpdateType.CONTENT_MODIFIED,
                    priority=UpdatePriority.MEDIUM,
                    title=f"API Update {i}",
                    description=f"API data changed on {source.name}",
                    content_hash=hashlib.md5(f"api_content_{i}".encode()).hexdigest(),
                    new_content=f"Updated API content {i}",
                    metadata={"endpoint": f"/api/endpoint_{i}"}
                )
                updates.append(update)
            
            return updates
            
        except Exception as e:
            logger.error(f"Error detecting API updates: {e}")
            return []
    
    def _detect_filesystem_updates(self, source: UpdateSource) -> List[ContentUpdate]:
        """Detect filesystem updates"""
        try:
            updates = []
            
            # Mock filesystem update detection
            # In production, use file system monitoring
            for i in range(4):  # Mock 4 updates
                update = ContentUpdate(
                    id=f"filesystem_update_{source.id}_{i}",
                    source_id=source.id,
                    update_type=UpdateType.CONTENT_MODIFIED,
                    priority=UpdatePriority.LOW,
                    title=f"File Update {i}",
                    description=f"File changed in {source.name}",
                    content_hash=hashlib.md5(f"file_content_{i}".encode()).hexdigest(),
                    new_content=f"Updated file content {i}",
                    metadata={"file_path": f"/path/file_{i}.txt"}
                )
                updates.append(update)
            
            return updates
            
        except Exception as e:
            logger.error(f"Error detecting filesystem updates: {e}")
            return []
    
    def _detect_git_updates(self, source: UpdateSource) -> List[ContentUpdate]:
        """Detect Git repository updates"""
        try:
            updates = []
            
            # Mock Git update detection
            # In production, use Git API or webhooks
            for i in range(3):  # Mock 3 updates
                update = ContentUpdate(
                    id=f"git_update_{source.id}_{i}",
                    source_id=source.id,
                    update_type=UpdateType.CONTENT_ADDED,
                    priority=UpdatePriority.HIGH,
                    title=f"Git Update {i}",
                    description=f"New commit in {source.name}",
                    content_hash=hashlib.md5(f"git_content_{i}".encode()).hexdigest(),
                    new_content=f"New Git content {i}",
                    metadata={"commit": f"commit_{i}"}
                )
                updates.append(update)
            
            return updates
            
        except Exception as e:
            logger.error(f"Error detecting Git updates: {e}")
            return []
    
    def _detect_database_updates(self, source: UpdateSource) -> List[ContentUpdate]:
        """Detect database updates"""
        try:
            updates = []
            
            # Mock database update detection
            # In production, use database triggers or polling
            for i in range(2):  # Mock 2 updates
                update = ContentUpdate(
                    id=f"database_update_{source.id}_{i}",
                    source_id=source.id,
                    update_type=UpdateType.CONTENT_MODIFIED,
                    priority=UpdatePriority.MEDIUM,
                    title=f"Database Update {i}",
                    description=f"Database record changed in {source.name}",
                    content_hash=hashlib.md5(f"db_content_{i}".encode()).hexdigest(),
                    new_content=f"Updated database content {i}",
                    metadata={"table": f"table_{i}"}
                )
                updates.append(update)
            
            return updates
            
        except Exception as e:
            logger.error(f"Error detecting database updates: {e}")
            return []
    
    def _detect_email_updates(self, source: UpdateSource) -> List[ContentUpdate]:
        """Detect email updates"""
        try:
            updates = []
            
            # Mock email update detection
            # In production, use email API or IMAP
            for i in range(1):  # Mock 1 update
                update = ContentUpdate(
                    id=f"email_update_{source.id}_{i}",
                    source_id=source.id,
                    update_type=UpdateType.CONTENT_ADDED,
                    priority=UpdatePriority.HIGH,
                    title=f"Email Update {i}",
                    description=f"New email in {source.name}",
                    content_hash=hashlib.md5(f"email_content_{i}".encode()).hexdigest(),
                    new_content=f"New email content {i}",
                    metadata={"email_id": f"email_{i}"}
                )
                updates.append(update)
            
            return updates
            
        except Exception as e:
            logger.error(f"Error detecting email updates: {e}")
            return []
    
    def _detect_social_media_updates(self, source: UpdateSource) -> List[ContentUpdate]:
        """Detect social media updates"""
        try:
            updates = []
            
            # Mock social media update detection
            # In production, use social media APIs
            for i in range(3):  # Mock 3 updates
                update = ContentUpdate(
                    id=f"social_update_{source.id}_{i}",
                    source_id=source.id,
                    update_type=UpdateType.CONTENT_ADDED,
                    priority=UpdatePriority.LOW,
                    title=f"Social Media Update {i}",
                    description=f"New post in {source.name}",
                    content_hash=hashlib.md5(f"social_content_{i}".encode()).hexdigest(),
                    new_content=f"New social media content {i}",
                    metadata={"post_id": f"post_{i}"}
                )
                updates.append(update)
            
            return updates
            
        except Exception as e:
            logger.error(f"Error detecting social media updates: {e}")
            return []
    
    def _process_update(self, update: ContentUpdate):
        """Process a content update"""
        try:
            # Store update
            self.content_updates[update.id] = update
            
            # Get processor for update type
            processor = self.processors.get(update.update_type)
            if not processor:
                logger.warning(f"No processor for update type: {update.update_type}")
                return
            
            # Process update
            processor(update)
            
            # Mark as processed
            update.processed_at = django_timezone.now()
            update.status = "processed"
            
            logger.info(f"Processed update: {update.id}")
            
        except Exception as e:
            logger.error(f"Error processing update: {e}")
            update.status = "error"
    
    def _process_content_added(self, update: ContentUpdate):
        """Process content added update"""
        try:
            # Store content hash
            self.content_hashes[update.content_hash] = {
                "content": update.new_content,
                "source_id": update.source_id,
                "detected_at": update.detected_at
            }
            
            # Notify if enabled
            if self.notification_enabled:
                self._notify_content_added(update)
            
            logger.info(f"Processed content added: {update.id}")
            
        except Exception as e:
            logger.error(f"Error processing content added: {e}")
    
    def _process_content_modified(self, update: ContentUpdate):
        """Process content modified update"""
        try:
            # Update content hash
            self.content_hashes[update.content_hash] = {
                "content": update.new_content,
                "source_id": update.source_id,
                "detected_at": update.detected_at
            }
            
            # Notify if enabled
            if self.notification_enabled:
                self._notify_content_modified(update)
            
            logger.info(f"Processed content modified: {update.id}")
            
        except Exception as e:
            logger.error(f"Error processing content modified: {e}")
    
    def _process_content_deleted(self, update: ContentUpdate):
        """Process content deleted update"""
        try:
            # Remove content hash
            if update.content_hash in self.content_hashes:
                del self.content_hashes[update.content_hash]
            
            # Notify if enabled
            if self.notification_enabled:
                self._notify_content_deleted(update)
            
            logger.info(f"Processed content deleted: {update.id}")
            
        except Exception as e:
            logger.error(f"Error processing content deleted: {e}")
    
    def _process_content_moved(self, update: ContentUpdate):
        """Process content moved update"""
        try:
            # Update content hash location
            if update.content_hash in self.content_hashes:
                self.content_hashes[update.content_hash]["source_id"] = update.source_id
            
            # Notify if enabled
            if self.notification_enabled:
                self._notify_content_moved(update)
            
            logger.info(f"Processed content moved: {update.id}")
            
        except Exception as e:
            logger.error(f"Error processing content moved: {e}")
    
    def _process_metadata_changed(self, update: ContentUpdate):
        """Process metadata changed update"""
        try:
            # Update metadata
            if update.content_hash in self.content_hashes:
                self.content_hashes[update.content_hash]["metadata"] = update.metadata
            
            # Notify if enabled
            if self.notification_enabled:
                self._notify_metadata_changed(update)
            
            logger.info(f"Processed metadata changed: {update.id}")
            
        except Exception as e:
            logger.error(f"Error processing metadata changed: {e}")
    
    def _process_structure_changed(self, update: ContentUpdate):
        """Process structure changed update"""
        try:
            # Update structure
            if update.content_hash in self.content_hashes:
                self.content_hashes[update.content_hash]["structure"] = update.metadata.get("structure")
            
            # Notify if enabled
            if self.notification_enabled:
                self._notify_structure_changed(update)
            
            logger.info(f"Processed structure changed: {update.id}")
            
        except Exception as e:
            logger.error(f"Error processing structure changed: {e}")
    
    def _notify_content_added(self, update: ContentUpdate):
        """Notify about content added"""
        try:
            # Mock notification
            logger.info(f"NOTIFICATION: Content added - {update.title}")
            
        except Exception as e:
            logger.error(f"Error notifying content added: {e}")
    
    def _notify_content_modified(self, update: ContentUpdate):
        """Notify about content modified"""
        try:
            # Mock notification
            logger.info(f"NOTIFICATION: Content modified - {update.title}")
            
        except Exception as e:
            logger.error(f"Error notifying content modified: {e}")
    
    def _notify_content_deleted(self, update: ContentUpdate):
        """Notify about content deleted"""
        try:
            # Mock notification
            logger.info(f"NOTIFICATION: Content deleted - {update.title}")
            
        except Exception as e:
            logger.error(f"Error notifying content deleted: {e}")
    
    def _notify_content_moved(self, update: ContentUpdate):
        """Notify about content moved"""
        try:
            # Mock notification
            logger.info(f"NOTIFICATION: Content moved - {update.title}")
            
        except Exception as e:
            logger.error(f"Error notifying content moved: {e}")
    
    def _notify_metadata_changed(self, update: ContentUpdate):
        """Notify about metadata changed"""
        try:
            # Mock notification
            logger.info(f"NOTIFICATION: Metadata changed - {update.title}")
            
        except Exception as e:
            logger.error(f"Error notifying metadata changed: {e}")
    
    def _notify_structure_changed(self, update: ContentUpdate):
        """Notify about structure changed"""
        try:
            # Mock notification
            logger.info(f"NOTIFICATION: Structure changed - {update.title}")
            
        except Exception as e:
            logger.error(f"Error notifying structure changed: {e}")
    
    def get_update_source(self, source_id: str) -> Optional[UpdateSource]:
        """Get an update source by ID"""
        return self.update_sources.get(source_id)
    
    def get_content_update(self, update_id: str) -> Optional[ContentUpdate]:
        """Get a content update by ID"""
        return self.content_updates.get(update_id)
    
    def get_updates_by_source(self, source_id: str) -> List[ContentUpdate]:
        """Get updates for a source"""
        try:
            return [update for update in self.content_updates.values() if update.source_id == source_id]
        except Exception as e:
            logger.error(f"Error getting updates by source: {e}")
            return []
    
    def get_recent_updates(self, hours: int = 24) -> List[ContentUpdate]:
        """Get recent updates"""
        try:
            cutoff_time = django_timezone.now() - timedelta(hours=hours)
            return [update for update in self.content_updates.values() if update.detected_at >= cutoff_time]
        except Exception as e:
            logger.error(f"Error getting recent updates: {e}")
            return []
    
    def get_detection_statistics(self) -> Dict[str, Any]:
        """Get detection statistics"""
        try:
            stats = {
                "total_sources": len(self.update_sources),
                "enabled_sources": len([s for s in self.update_sources.values() if s.enabled]),
                "total_updates": len(self.content_updates),
                "updates_by_type": {},
                "updates_by_priority": {},
                "updates_by_source": {},
                "recent_updates_24h": len(self.get_recent_updates(24)),
                "recent_updates_7d": len(self.get_recent_updates(168)),
                "detection_enabled": self.detection_enabled,
                "auto_processing": self.auto_processing,
                "notification_enabled": self.notification_enabled,
                "running": self.running
            }
            
            # Count updates by type
            for update in self.content_updates.values():
                update_type = update.update_type.value
                stats["updates_by_type"][update_type] = stats["updates_by_type"].get(update_type, 0) + 1
                
                priority = update.priority.value
                stats["updates_by_priority"][priority] = stats["updates_by_priority"].get(priority, 0) + 1
                
                source_id = update.source_id
                stats["updates_by_source"][source_id] = stats["updates_by_source"].get(source_id, 0) + 1
            
            return stats
            
        except Exception as e:
            logger.error(f"Error getting detection statistics: {e}")
            return {}
    
    def export_detection_data(self) -> Dict[str, Any]:
        """Export detection data"""
        try:
            return {
                "sources": [
                    {
                        "id": source.id,
                        "name": source.name,
                        "source_type": source.source_type.value,
                        "url": source.url,
                        "config": source.config,
                        "enabled": source.enabled,
                        "last_check": source.last_check.isoformat() if source.last_check else None,
                        "last_update": source.last_update.isoformat() if source.last_update else None,
                        "check_interval": source.check_interval,
                        "metadata": source.metadata,
                        "created_at": source.created_at.isoformat(),
                        "updated_at": source.updated_at.isoformat()
                    }
                    for source in self.update_sources.values()
                ],
                "updates": [
                    {
                        "id": update.id,
                        "source_id": update.source_id,
                        "update_type": update.update_type.value,
                        "priority": update.priority.value,
                        "title": update.title,
                        "description": update.description,
                        "content_hash": update.content_hash,
                        "old_content": update.old_content,
                        "new_content": update.new_content,
                        "metadata": update.metadata,
                        "detected_at": update.detected_at.isoformat(),
                        "processed_at": update.processed_at.isoformat() if update.processed_at else None,
                        "status": update.status
                    }
                    for update in self.content_updates.values()
                ]
            }
            
        except Exception as e:
            logger.error(f"Error exporting detection data: {e}")
            return {}
    
    def import_detection_data(self, data: Dict[str, Any]):
        """Import detection data"""
        try:
            # Import sources
            if "sources" in data:
                for source_data in data["sources"]:
                    source = UpdateSource(
                        id=source_data["id"],
                        name=source_data["name"],
                        source_type=UpdateSource(source_data["source_type"]),
                        url=source_data["url"],
                        config=source_data.get("config", {}),
                        enabled=source_data.get("enabled", True),
                        last_check=datetime.fromisoformat(source_data["last_check"]) if source_data.get("last_check") else None,
                        last_update=datetime.fromisoformat(source_data["last_update"]) if source_data.get("last_update") else None,
                        check_interval=source_data.get("check_interval", 3600),
                        metadata=source_data.get("metadata", {}),
                        created_at=datetime.fromisoformat(source_data["created_at"]),
                        updated_at=datetime.fromisoformat(source_data["updated_at"])
                    )
                    self.update_sources[source.id] = source
            
            # Import updates
            if "updates" in data:
                for update_data in data["updates"]:
                    update = ContentUpdate(
                        id=update_data["id"],
                        source_id=update_data["source_id"],
                        update_type=UpdateType(update_data["update_type"]),
                        priority=UpdatePriority(update_data["priority"]),
                        title=update_data["title"],
                        description=update_data["description"],
                        content_hash=update_data["content_hash"],
                        old_content=update_data.get("old_content"),
                        new_content=update_data.get("new_content"),
                        metadata=update_data.get("metadata", {}),
                        detected_at=datetime.fromisoformat(update_data["detected_at"]),
                        processed_at=datetime.fromisoformat(update_data["processed_at"]) if update_data.get("processed_at") else None,
                        status=update_data.get("status", "pending")
                    )
                    self.content_updates[update.id] = update
            
            logger.info("Detection data imported successfully")
            
        except Exception as e:
            logger.error(f"Error importing detection data: {e}")
            raise
