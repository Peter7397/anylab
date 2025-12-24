"""
Peer Review System

This module provides a comprehensive peer review system for user contributions
including review workflows, quality assessment, and community feedback.
"""

import logging
from typing import Dict, Any, List, Optional, Tuple, Union
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from enum import Enum
from django.utils import timezone as django_timezone
from django.core.cache import cache
from django.contrib.auth.models import User

logger = logging.getLogger(__name__)


class ReviewType(Enum):
    """Review type enumeration"""
    CONTENT_REVIEW = "content_review"
    QUALITY_REVIEW = "quality_review"
    TECHNICAL_REVIEW = "technical_review"
    ACCURACY_REVIEW = "accuracy_review"
    COMPLETENESS_REVIEW = "completeness_review"
    RELEVANCE_REVIEW = "relevance_review"
    LANGUAGE_REVIEW = "language_review"
    FORMAT_REVIEW = "format_review"
    METADATA_REVIEW = "metadata_review"
    CATEGORIZATION_REVIEW = "categorization_review"
    DUPLICATE_REVIEW = "duplicate_review"
    COPYRIGHT_REVIEW = "copyright_review"
    SECURITY_REVIEW = "security_review"
    ACCESSIBILITY_REVIEW = "accessibility_review"
    EXPERT_REVIEW = "expert_review"


class ReviewStatus(Enum):
    """Review status enumeration"""
    PENDING = "pending"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    REJECTED = "rejected"
    APPROVED = "approved"
    NEEDS_REVISION = "needs_revision"
    CANCELLED = "cancelled"
    EXPIRED = "expired"
    DISPUTED = "disputed"
    ESCALATED = "escalated"


class ReviewPriority(Enum):
    """Review priority enumeration"""
    LOW = 1
    NORMAL = 2
    HIGH = 3
    URGENT = 4
    CRITICAL = 5


class ReviewOutcome(Enum):
    """Review outcome enumeration"""
    APPROVE = "approve"
    REJECT = "reject"
    REVISE = "revise"
    NEEDS_MORE_INFO = "needs_more_info"
    ESCALATE = "escalate"
    DUPLICATE = "duplicate"
    SPAM = "spam"
    COPYRIGHT_VIOLATION = "copyright_violation"
    SECURITY_RISK = "security_risk"
    QUALITY_ISSUE = "quality_issue"
    TECHNICAL_ISSUE = "technical_issue"
    ACCURACY_ISSUE = "accuracy_issue"
    COMPLETENESS_ISSUE = "completeness_issue"
    RELEVANCE_ISSUE = "relevance_issue"
    LANGUAGE_ISSUE = "language_issue"
    FORMAT_ISSUE = "format_issue"
    METADATA_ISSUE = "metadata_issue"
    CATEGORIZATION_ISSUE = "categorization_issue"
    ACCESSIBILITY_ISSUE = "accessibility_issue"


class ReviewerRole(Enum):
    """Reviewer role enumeration"""
    CONTENT_REVIEWER = "content_reviewer"
    TECHNICAL_REVIEWER = "technical_reviewer"
    QUALITY_REVIEWER = "quality_reviewer"
    EXPERT_REVIEWER = "expert_reviewer"
    MODERATOR = "moderator"
    ADMIN = "admin"
    COMMUNITY_REVIEWER = "community_reviewer"
    PEER_REVIEWER = "peer_reviewer"
    TRANSLATION_REVIEWER = "translation_reviewer"
    ACCESSIBILITY_REVIEWER = "accessibility_reviewer"


@dataclass
class ReviewCriteria:
    """Review criteria structure"""
    id: str
    name: str
    description: str
    review_type: ReviewType
    weight: float  # 0.0 to 1.0
    required: bool = True
    scoring_type: str = "scale"  # scale, binary, multiple_choice
    scale_min: int = 1
    scale_max: int = 5
    options: List[str] = field(default_factory=list)
    guidelines: str = ""
    examples: List[str] = field(default_factory=list)


@dataclass
class ReviewAssignment:
    """Review assignment structure"""
    id: str
    contribution_id: str
    reviewer_id: str
    review_type: ReviewType
    priority: ReviewPriority
    status: ReviewStatus
    assigned_at: datetime = field(default_factory=lambda: django_timezone.now())
    due_date: Optional[datetime] = None
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    estimated_duration: int = 30  # minutes
    actual_duration: Optional[int] = None
    reviewer_role: ReviewerRole = ReviewerRole.CONTENT_REVIEWER
    auto_assigned: bool = False
    assignment_reason: str = ""
    notes: str = ""
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class Review:
    """Review structure"""
    id: str
    assignment_id: str
    contribution_id: str
    reviewer_id: str
    review_type: ReviewType
    status: ReviewStatus
    outcome: Optional[ReviewOutcome] = None
    overall_score: float = 0.0
    criteria_scores: Dict[str, float] = field(default_factory=dict)
    comments: str = ""
    suggestions: List[str] = field(default_factory=list)
    issues_found: List[str] = field(default_factory=list)
    strengths: List[str] = field(default_factory=list)
    recommendations: List[str] = field(default_factory=list)
    confidence_level: float = 0.0  # 0.0 to 1.0
    review_duration: int = 0  # minutes
    created_at: datetime = field(default_factory=lambda: django_timezone.now())
    updated_at: datetime = field(default_factory=lambda: django_timezone.now())
    submitted_at: Optional[datetime] = None
    approved_at: Optional[datetime] = None
    rejected_at: Optional[datetime] = None
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class ReviewWorkflow:
    """Review workflow structure"""
    id: str
    name: str
    description: str
    contribution_types: List[str]
    review_stages: List[Dict[str, Any]]
    auto_assign: bool = True
    parallel_reviews: bool = False
    min_reviewers: int = 1
    max_reviewers: int = 3
    consensus_required: bool = False
    escalation_threshold: float = 0.5
    timeout_hours: int = 72
    enabled: bool = True
    created_at: datetime = field(default_factory=lambda: django_timezone.now())
    updated_at: datetime = field(default_factory=lambda: django_timezone.now())


@dataclass
class ReviewerProfile:
    """Reviewer profile structure"""
    user_id: str
    username: str
    email: str
    reviewer_roles: List[ReviewerRole]
    expertise_areas: List[str]
    languages: List[str]
    review_count: int = 0
    average_rating: float = 0.0
    reliability_score: float = 0.0
    quality_score: float = 0.0
    speed_score: float = 0.0
    availability: Dict[str, Any] = field(default_factory=dict)
    preferences: Dict[str, Any] = field(default_factory=dict)
    max_reviews_per_day: int = 5
    max_reviews_per_week: int = 20
    current_reviews: int = 0
    is_active: bool = True
    joined_at: datetime = field(default_factory=lambda: django_timezone.now())
    last_review_at: Optional[datetime] = None
    profile_updated_at: datetime = field(default_factory=lambda: django_timezone.now())


@dataclass
class ReviewStatistics:
    """Review statistics structure"""
    total_reviews: int = 0
    completed_reviews: int = 0
    pending_reviews: int = 0
    rejected_reviews: int = 0
    approved_reviews: int = 0
    average_review_time: float = 0.0
    average_quality_score: float = 0.0
    reviewer_satisfaction: float = 0.0
    contributor_satisfaction: float = 0.0
    review_accuracy: float = 0.0
    consensus_rate: float = 0.0
    escalation_rate: float = 0.0
    timeout_rate: float = 0.0


class PeerReviewSystemManager:
    """Peer Review System Manager"""
    
    def __init__(self, config: Dict[str, Any] = None):
        """Initialize peer review system manager"""
        self.config = config or {}
        self.review_enabled = self.config.get('review_enabled', True)
        self.auto_assignment_enabled = self.config.get('auto_assignment_enabled', True)
        self.consensus_required = self.config.get('consensus_required', False)
        self.quality_threshold = self.config.get('quality_threshold', 0.7)
        self.review_timeout_hours = self.config.get('review_timeout_hours', 72)
        
        # Initialize components
        self.review_criteria = {}
        self.review_assignments = {}
        self.reviews = {}
        self.workflows = {}
        self.reviewer_profiles = {}
        self.statistics = ReviewStatistics()
        
        # Initialize review system
        self._initialize_review_system()
        
        logger.info("Peer Review System Manager initialized")
    
    def _initialize_review_system(self):
        """Initialize review system components"""
        try:
            # Initialize review criteria
            self._create_default_criteria()
            
            # Initialize review workflows
            self._create_default_workflows()
            
            # Initialize reviewer profiles
            self._initialize_reviewer_profiles()
            
            logger.info("Review system components initialized")
            
        except Exception as e:
            logger.error(f"Error initializing review system: {e}")
            raise
    
    def _create_default_criteria(self):
        """Create default review criteria"""
        try:
            criteria_list = [
                ReviewCriteria(
                    id="content_quality",
                    name="Content Quality",
                    description="Overall quality of the content",
                    review_type=ReviewType.CONTENT_REVIEW,
                    weight=0.3,
                    required=True,
                    scoring_type="scale",
                    scale_min=1,
                    scale_max=5,
                    guidelines="Evaluate the overall quality, clarity, and usefulness of the content",
                    examples=["Well-written and informative", "Clear and easy to understand", "Provides valuable information"]
                ),
                ReviewCriteria(
                    id="technical_accuracy",
                    name="Technical Accuracy",
                    description="Technical accuracy and correctness",
                    review_type=ReviewType.TECHNICAL_REVIEW,
                    weight=0.25,
                    required=True,
                    scoring_type="scale",
                    scale_min=1,
                    scale_max=5,
                    guidelines="Verify technical accuracy, correctness of information, and proper implementation",
                    examples=["Technically accurate", "Correct implementation", "Proper methodology"]
                ),
                ReviewCriteria(
                    id="completeness",
                    name="Completeness",
                    description="Completeness of the content",
                    review_type=ReviewType.COMPLETENESS_REVIEW,
                    weight=0.2,
                    required=True,
                    scoring_type="scale",
                    scale_min=1,
                    scale_max=5,
                    guidelines="Assess if the content is complete and covers all necessary aspects",
                    examples=["Complete coverage", "All necessary information included", "Comprehensive"]
                ),
                ReviewCriteria(
                    id="relevance",
                    name="Relevance",
                    description="Relevance to the target audience",
                    review_type=ReviewType.RELEVANCE_REVIEW,
                    weight=0.15,
                    required=True,
                    scoring_type="scale",
                    scale_min=1,
                    scale_max=5,
                    guidelines="Evaluate relevance to the target audience and use case",
                    examples=["Highly relevant", "Appropriate for audience", "Useful for intended purpose"]
                ),
                ReviewCriteria(
                    id="language_quality",
                    name="Language Quality",
                    description="Language and writing quality",
                    review_type=ReviewType.LANGUAGE_REVIEW,
                    weight=0.1,
                    required=True,
                    scoring_type="scale",
                    scale_min=1,
                    scale_max=5,
                    guidelines="Assess grammar, spelling, clarity, and professional writing",
                    examples=["Well-written", "Clear language", "Professional tone"]
                )
            ]
            
            for criteria in criteria_list:
                self.review_criteria[criteria.id] = criteria
            
            logger.info("Default review criteria created")
            
        except Exception as e:
            logger.error(f"Error creating default criteria: {e}")
    
    def _create_default_workflows(self):
        """Create default review workflows"""
        try:
            # Standard workflow
            standard_workflow = ReviewWorkflow(
                id="standard_workflow",
                name="Standard Review Workflow",
                description="Standard review workflow for most content types",
                contribution_types=["file_upload", "url_submission", "content_edit"],
                review_stages=[
                    {
                        "stage": 1,
                        "name": "Initial Review",
                        "review_types": [ReviewType.CONTENT_REVIEW, ReviewType.QUALITY_REVIEW],
                        "min_reviewers": 1,
                        "max_reviewers": 2,
                        "timeout_hours": 48,
                        "auto_assign": True
                    },
                    {
                        "stage": 2,
                        "name": "Technical Review",
                        "review_types": [ReviewType.TECHNICAL_REVIEW, ReviewType.ACCURACY_REVIEW],
                        "min_reviewers": 1,
                        "max_reviewers": 1,
                        "timeout_hours": 24,
                        "auto_assign": True,
                        "conditional": "if_technical_content"
                    },
                    {
                        "stage": 3,
                        "name": "Final Review",
                        "review_types": [ReviewType.EXPERT_REVIEW],
                        "min_reviewers": 1,
                        "max_reviewers": 1,
                        "timeout_hours": 24,
                        "auto_assign": True,
                        "conditional": "if_high_priority"
                    }
                ],
                auto_assign=True,
                parallel_reviews=False,
                min_reviewers=1,
                max_reviewers=2,
                consensus_required=False,
                escalation_threshold=0.5,
                timeout_hours=72
            )
            
            self.workflows["standard_workflow"] = standard_workflow
            
            # Expert workflow
            expert_workflow = ReviewWorkflow(
                id="expert_workflow",
                name="Expert Review Workflow",
                description="Expert review workflow for technical content",
                contribution_types=["technical_document", "api_documentation", "tutorial"],
                review_stages=[
                    {
                        "stage": 1,
                        "name": "Expert Review",
                        "review_types": [ReviewType.EXPERT_REVIEW, ReviewType.TECHNICAL_REVIEW],
                        "min_reviewers": 2,
                        "max_reviewers": 3,
                        "timeout_hours": 72,
                        "auto_assign": True
                    },
                    {
                        "stage": 2,
                        "name": "Quality Review",
                        "review_types": [ReviewType.QUALITY_REVIEW, ReviewType.COMPLETENESS_REVIEW],
                        "min_reviewers": 1,
                        "max_reviewers": 2,
                        "timeout_hours": 48,
                        "auto_assign": True
                    }
                ],
                auto_assign=True,
                parallel_reviews=True,
                min_reviewers=2,
                max_reviewers=3,
                consensus_required=True,
                escalation_threshold=0.3,
                timeout_hours=120
            )
            
            self.workflows["expert_workflow"] = expert_workflow
            
            # Quick workflow
            quick_workflow = ReviewWorkflow(
                id="quick_workflow",
                name="Quick Review Workflow",
                description="Quick review workflow for simple content",
                contribution_types=["comment", "rating", "simple_edit"],
                review_stages=[
                    {
                        "stage": 1,
                        "name": "Quick Review",
                        "review_types": [ReviewType.CONTENT_REVIEW],
                        "min_reviewers": 1,
                        "max_reviewers": 1,
                        "timeout_hours": 24,
                        "auto_assign": True
                    }
                ],
                auto_assign=True,
                parallel_reviews=False,
                min_reviewers=1,
                max_reviewers=1,
                consensus_required=False,
                escalation_threshold=0.7,
                timeout_hours=24
            )
            
            self.workflows["quick_workflow"] = quick_workflow
            
            logger.info("Default review workflows created")
            
        except Exception as e:
            logger.error(f"Error creating default workflows: {e}")
    
    def _initialize_reviewer_profiles(self):
        """Initialize reviewer profiles"""
        try:
            # This would typically load from database
            # For now, create empty profiles
            self.reviewer_profiles = {}
            
            logger.info("Reviewer profiles initialized")
            
        except Exception as e:
            logger.error(f"Error initializing reviewer profiles: {e}")
    
    def create_review_assignment(self, contribution_id: str, review_type: ReviewType, 
                                priority: ReviewPriority = ReviewPriority.NORMAL) -> ReviewAssignment:
        """Create a review assignment"""
        try:
            # Generate assignment ID
            assignment_id = f"review_assignment_{django_timezone.now().strftime('%Y%m%d_%H%M%S')}_{hash(contribution_id) % 10000}"
            
            # Determine workflow
            workflow = self._determine_workflow(contribution_id, review_type)
            
            # Auto-assign reviewer if enabled
            reviewer_id = None
            if self.auto_assignment_enabled:
                reviewer_id = self._auto_assign_reviewer(contribution_id, review_type, workflow)
            
            # Calculate due date
            due_date = django_timezone.now() + timedelta(hours=workflow.timeout_hours)
            
            # Create assignment
            assignment = ReviewAssignment(
                id=assignment_id,
                contribution_id=contribution_id,
                reviewer_id=reviewer_id,
                review_type=review_type,
                priority=priority,
                status=ReviewStatus.PENDING,
                due_date=due_date,
                auto_assigned=reviewer_id is not None,
                assignment_reason=f"Auto-assigned for {review_type.value} review"
            )
            
            # Store assignment
            self.review_assignments[assignment_id] = assignment
            
            logger.info(f"Created review assignment: {assignment_id}")
            return assignment
            
        except Exception as e:
            logger.error(f"Error creating review assignment: {e}")
            raise
    
    def _determine_workflow(self, contribution_id: str, review_type: ReviewType) -> ReviewWorkflow:
        """Determine the appropriate workflow for a contribution"""
        try:
            # Simple workflow selection based on review type
            if review_type in [ReviewType.EXPERT_REVIEW, ReviewType.TECHNICAL_REVIEW]:
                return self.workflows.get("expert_workflow", self.workflows["standard_workflow"])
            elif review_type == ReviewType.CONTENT_REVIEW:
                return self.workflows.get("quick_workflow", self.workflows["standard_workflow"])
            else:
                return self.workflows.get("standard_workflow", self.workflows["standard_workflow"])
            
        except Exception as e:
            logger.error(f"Error determining workflow: {e}")
            return self.workflows["standard_workflow"]
    
    def _auto_assign_reviewer(self, contribution_id: str, review_type: ReviewType, 
                             workflow: ReviewWorkflow) -> Optional[str]:
        """Auto-assign a reviewer for the contribution"""
        try:
            # Get available reviewers
            available_reviewers = self._get_available_reviewers(review_type, workflow)
            
            if not available_reviewers:
                return None
            
            # Select best reviewer based on criteria
            best_reviewer = self._select_best_reviewer(available_reviewers, contribution_id, review_type)
            
            return best_reviewer
            
        except Exception as e:
            logger.error(f"Error auto-assigning reviewer: {e}")
            return None
    
    def _get_available_reviewers(self, review_type: ReviewType, workflow: ReviewWorkflow) -> List[str]:
        """Get available reviewers for a review type"""
        try:
            available_reviewers = []
            
            for reviewer_id, profile in self.reviewer_profiles.items():
                # Check if reviewer is active
                if not profile.is_active:
                    continue
                
                # Check if reviewer has the required role
                required_role = self._get_required_role(review_type)
                if required_role not in profile.reviewer_roles:
                    continue
                
                # Check if reviewer has capacity
                if profile.current_reviews >= profile.max_reviews_per_day:
                    continue
                
                # Check availability
                if not self._is_reviewer_available(reviewer_id):
                    continue
                
                available_reviewers.append(reviewer_id)
            
            return available_reviewers
            
        except Exception as e:
            logger.error(f"Error getting available reviewers: {e}")
            return []
    
    def _get_required_role(self, review_type: ReviewType) -> ReviewerRole:
        """Get required reviewer role for a review type"""
        try:
            role_mapping = {
                ReviewType.CONTENT_REVIEW: ReviewerRole.CONTENT_REVIEWER,
                ReviewType.TECHNICAL_REVIEW: ReviewerRole.TECHNICAL_REVIEWER,
                ReviewType.QUALITY_REVIEW: ReviewerRole.QUALITY_REVIEWER,
                ReviewType.EXPERT_REVIEW: ReviewerRole.EXPERT_REVIEWER,
                ReviewType.LANGUAGE_REVIEW: ReviewerRole.CONTENT_REVIEWER,
                ReviewType.TRANSLATION_REVIEW: ReviewerRole.TRANSLATION_REVIEWER,
                ReviewType.ACCESSIBILITY_REVIEW: ReviewerRole.ACCESSIBILITY_REVIEWER
            }
            
            return role_mapping.get(review_type, ReviewerRole.CONTENT_REVIEWER)
            
        except Exception as e:
            logger.error(f"Error getting required role: {e}")
            return ReviewerRole.CONTENT_REVIEWER
    
    def _is_reviewer_available(self, reviewer_id: str) -> bool:
        """Check if reviewer is available"""
        try:
            profile = self.reviewer_profiles.get(reviewer_id)
            if not profile:
                return False
            
            # Check current workload
            if profile.current_reviews >= profile.max_reviews_per_day:
                return False
            
            # Check availability schedule
            now = django_timezone.now()
            current_hour = now.hour
            current_day = now.strftime('%A').lower()
            
            availability = profile.availability.get(current_day, {})
            if not availability.get('available', True):
                return False
            
            work_hours = availability.get('work_hours', {'start': 9, 'end': 17})
            if not (work_hours['start'] <= current_hour <= work_hours['end']):
                return False
            
            return True
            
        except Exception as e:
            logger.error(f"Error checking reviewer availability: {e}")
            return False
    
    def _select_best_reviewer(self, available_reviewers: List[str], contribution_id: str, 
                             review_type: ReviewType) -> str:
        """Select the best reviewer from available reviewers"""
        try:
            if not available_reviewers:
                return None
            
            # Score reviewers based on various criteria
            reviewer_scores = {}
            
            for reviewer_id in available_reviewers:
                profile = self.reviewer_profiles.get(reviewer_id)
                if not profile:
                    continue
                
                score = 0
                
                # Quality score (40%)
                score += profile.quality_score * 0.4
                
                # Reliability score (30%)
                score += profile.reliability_score * 0.3
                
                # Speed score (20%)
                score += profile.speed_score * 0.2
                
                # Availability bonus (10%)
                availability_bonus = 1.0 - (profile.current_reviews / profile.max_reviews_per_day)
                score += availability_bonus * 0.1
                
                reviewer_scores[reviewer_id] = score
            
            # Select reviewer with highest score
            best_reviewer = max(reviewer_scores.items(), key=lambda x: x[1])[0]
            
            return best_reviewer
            
        except Exception as e:
            logger.error(f"Error selecting best reviewer: {e}")
            return available_reviewers[0] if available_reviewers else None
    
    def start_review(self, assignment_id: str, reviewer_id: str) -> Review:
        """Start a review"""
        try:
            assignment = self.review_assignments.get(assignment_id)
            if not assignment:
                raise ValueError(f"Assignment {assignment_id} not found")
            
            if assignment.status != ReviewStatus.PENDING:
                raise ValueError(f"Assignment {assignment_id} is not pending")
            
            if assignment.reviewer_id != reviewer_id:
                raise ValueError(f"Reviewer {reviewer_id} is not assigned to assignment {assignment_id}")
            
            # Generate review ID
            review_id = f"review_{django_timezone.now().strftime('%Y%m%d_%H%M%S')}_{hash(assignment_id) % 10000}"
            
            # Create review
            review = Review(
                id=review_id,
                assignment_id=assignment_id,
                contribution_id=assignment.contribution_id,
                reviewer_id=reviewer_id,
                review_type=assignment.review_type,
                status=ReviewStatus.IN_PROGRESS
            )
            
            # Store review
            self.reviews[review_id] = review
            
            # Update assignment
            assignment.status = ReviewStatus.IN_PROGRESS
            assignment.started_at = django_timezone.now()
            
            # Update reviewer profile
            profile = self.reviewer_profiles.get(reviewer_id)
            if profile:
                profile.current_reviews += 1
            
            logger.info(f"Started review: {review_id}")
            return review
            
        except Exception as e:
            logger.error(f"Error starting review: {e}")
            raise
    
    def submit_review(self, review_id: str, review_data: Dict[str, Any]) -> Review:
        """Submit a review"""
        try:
            review = self.reviews.get(review_id)
            if not review:
                raise ValueError(f"Review {review_id} not found")
            
            if review.status != ReviewStatus.IN_PROGRESS:
                raise ValueError(f"Review {review_id} is not in progress")
            
            # Update review
            review.outcome = ReviewOutcome(review_data['outcome'])
            review.overall_score = review_data.get('overall_score', 0.0)
            review.criteria_scores = review_data.get('criteria_scores', {})
            review.comments = review_data.get('comments', '')
            review.suggestions = review_data.get('suggestions', [])
            review.issues_found = review_data.get('issues_found', [])
            review.strengths = review_data.get('strengths', [])
            review.recommendations = review_data.get('recommendations', [])
            review.confidence_level = review_data.get('confidence_level', 0.0)
            review.review_duration = review_data.get('review_duration', 0)
            review.status = ReviewStatus.COMPLETED
            review.submitted_at = django_timezone.now()
            review.updated_at = django_timezone.now()
            
            # Update assignment
            assignment = self.review_assignments.get(review.assignment_id)
            if assignment:
                assignment.status = ReviewStatus.COMPLETED
                assignment.completed_at = django_timezone.now()
                assignment.actual_duration = review.review_duration
            
            # Update reviewer profile
            profile = self.reviewer_profiles.get(review.reviewer_id)
            if profile:
                profile.current_reviews = max(0, profile.current_reviews - 1)
                profile.last_review_at = django_timezone.now()
                
                # Update reviewer statistics
                self._update_reviewer_statistics(review.reviewer_id, review)
            
            # Update overall statistics
            self._update_statistics(review)
            
            logger.info(f"Submitted review: {review_id}")
            return review
            
        except Exception as e:
            logger.error(f"Error submitting review: {e}")
            raise
    
    def _update_reviewer_statistics(self, reviewer_id: str, review: Review):
        """Update reviewer statistics"""
        try:
            profile = self.reviewer_profiles.get(reviewer_id)
            if not profile:
                return
            
            # Update review count
            profile.review_count += 1
            
            # Update average rating (simplified)
            if profile.review_count == 1:
                profile.average_rating = review.overall_score
            else:
                profile.average_rating = (profile.average_rating * (profile.review_count - 1) + review.overall_score) / profile.review_count
            
            # Update quality score
            profile.quality_score = profile.average_rating
            
            # Update reliability score (based on completion rate)
            completed_reviews = len([r for r in self.reviews.values() if r.reviewer_id == reviewer_id and r.status == ReviewStatus.COMPLETED])
            total_assignments = len([a for a in self.review_assignments.values() if a.reviewer_id == reviewer_id])
            
            if total_assignments > 0:
                profile.reliability_score = completed_reviews / total_assignments
            
            # Update speed score (based on average review time)
            reviewer_reviews = [r for r in self.reviews.values() if r.reviewer_id == reviewer_id and r.review_duration > 0]
            if reviewer_reviews:
                avg_duration = sum(r.review_duration for r in reviewer_reviews) / len(reviewer_reviews)
                # Convert to score (lower duration = higher score)
                profile.speed_score = max(0, 1.0 - (avg_duration / 120))  # 120 minutes as baseline
            
        except Exception as e:
            logger.error(f"Error updating reviewer statistics: {e}")
    
    def _update_statistics(self, review: Review):
        """Update overall statistics"""
        try:
            self.statistics.total_reviews += 1
            
            if review.status == ReviewStatus.COMPLETED:
                self.statistics.completed_reviews += 1
                
                # Update average review time
                if review.review_duration > 0:
                    if self.statistics.completed_reviews == 1:
                        self.statistics.average_review_time = review.review_duration
                    else:
                        self.statistics.average_review_time = (
                            self.statistics.average_review_time * (self.statistics.completed_reviews - 1) + 
                            review.review_duration
                        ) / self.statistics.completed_reviews
                
                # Update average quality score
                if self.statistics.completed_reviews == 1:
                    self.statistics.average_quality_score = review.overall_score
                else:
                    self.statistics.average_quality_score = (
                        self.statistics.average_quality_score * (self.statistics.completed_reviews - 1) + 
                        review.overall_score
                    ) / self.statistics.completed_reviews
            
            elif review.status == ReviewStatus.REJECTED:
                self.statistics.rejected_reviews += 1
            
            elif review.status == ReviewStatus.APPROVED:
                self.statistics.approved_reviews += 1
            
            elif review.status == ReviewStatus.PENDING:
                self.statistics.pending_reviews += 1
            
        except Exception as e:
            logger.error(f"Error updating statistics: {e}")
    
    def get_review(self, review_id: str) -> Optional[Review]:
        """Get a review by ID"""
        return self.reviews.get(review_id)
    
    def get_reviews(self, reviewer_id: str = None, status: ReviewStatus = None, 
                   review_type: ReviewType = None) -> List[Review]:
        """Get reviews filtered by reviewer, status, and type"""
        try:
            reviews = list(self.reviews.values())
            
            if reviewer_id:
                reviews = [r for r in reviews if r.reviewer_id == reviewer_id]
            
            if status:
                reviews = [r for r in reviews if r.status == status]
            
            if review_type:
                reviews = [r for r in reviews if r.review_type == review_type]
            
            return sorted(reviews, key=lambda x: x.created_at, reverse=True)
            
        except Exception as e:
            logger.error(f"Error getting reviews: {e}")
            return []
    
    def get_review_assignment(self, assignment_id: str) -> Optional[ReviewAssignment]:
        """Get a review assignment by ID"""
        return self.review_assignments.get(assignment_id)
    
    def get_review_assignments(self, reviewer_id: str = None, status: ReviewStatus = None) -> List[ReviewAssignment]:
        """Get review assignments filtered by reviewer and status"""
        try:
            assignments = list(self.review_assignments.values())
            
            if reviewer_id:
                assignments = [a for a in assignments if a.reviewer_id == reviewer_id]
            
            if status:
                assignments = [a for a in assignments if a.status == status]
            
            return sorted(assignments, key=lambda x: x.assigned_at, reverse=True)
            
        except Exception as e:
            logger.error(f"Error getting review assignments: {e}")
            return []
    
    def create_reviewer_profile(self, user_id: str, profile_data: Dict[str, Any]) -> ReviewerProfile:
        """Create a reviewer profile"""
        try:
            profile = ReviewerProfile(
                user_id=user_id,
                username=profile_data.get('username', ''),
                email=profile_data.get('email', ''),
                reviewer_roles=[ReviewerRole(role) for role in profile_data.get('reviewer_roles', [])],
                expertise_areas=profile_data.get('expertise_areas', []),
                languages=profile_data.get('languages', []),
                max_reviews_per_day=profile_data.get('max_reviews_per_day', 5),
                max_reviews_per_week=profile_data.get('max_reviews_per_week', 20),
                availability=profile_data.get('availability', {}),
                preferences=profile_data.get('preferences', {})
            )
            
            self.reviewer_profiles[user_id] = profile
            
            logger.info(f"Created reviewer profile: {user_id}")
            return profile
            
        except Exception as e:
            logger.error(f"Error creating reviewer profile: {e}")
            raise
    
    def update_reviewer_profile(self, user_id: str, updates: Dict[str, Any]):
        """Update a reviewer profile"""
        try:
            profile = self.reviewer_profiles.get(user_id)
            if profile:
                for key, value in updates.items():
                    if hasattr(profile, key):
                        setattr(profile, key, value)
                
                profile.profile_updated_at = django_timezone.now()
                
                logger.info(f"Updated reviewer profile: {user_id}")
            
        except Exception as e:
            logger.error(f"Error updating reviewer profile: {e}")
    
    def get_reviewer_profile(self, user_id: str) -> Optional[ReviewerProfile]:
        """Get a reviewer profile by user ID"""
        return self.reviewer_profiles.get(user_id)
    
    def get_reviewer_profiles(self, role: ReviewerRole = None, active_only: bool = True) -> List[ReviewerProfile]:
        """Get reviewer profiles filtered by role and activity"""
        try:
            profiles = list(self.reviewer_profiles.values())
            
            if active_only:
                profiles = [p for p in profiles if p.is_active]
            
            if role:
                profiles = [p for p in profiles if role in p.reviewer_roles]
            
            return sorted(profiles, key=lambda x: x.review_count, reverse=True)
            
        except Exception as e:
            logger.error(f"Error getting reviewer profiles: {e}")
            return []
    
    def get_review_statistics(self) -> ReviewStatistics:
        """Get review statistics"""
        return self.statistics
    
    def get_reviewer_statistics(self, reviewer_id: str) -> Dict[str, Any]:
        """Get statistics for a specific reviewer"""
        try:
            profile = self.reviewer_profiles.get(reviewer_id)
            if not profile:
                return {}
            
            # Get reviewer's reviews
            reviewer_reviews = [r for r in self.reviews.values() if r.reviewer_id == reviewer_id]
            
            stats = {
                'reviewer_id': reviewer_id,
                'username': profile.username,
                'review_count': profile.review_count,
                'average_rating': profile.average_rating,
                'reliability_score': profile.reliability_score,
                'quality_score': profile.quality_score,
                'speed_score': profile.speed_score,
                'current_reviews': profile.current_reviews,
                'max_reviews_per_day': profile.max_reviews_per_day,
                'max_reviews_per_week': profile.max_reviews_per_week,
                'is_active': profile.is_active,
                'expertise_areas': profile.expertise_areas,
                'languages': profile.languages,
                'reviewer_roles': [role.value for role in profile.reviewer_roles],
                'total_reviews': len(reviewer_reviews),
                'completed_reviews': len([r for r in reviewer_reviews if r.status == ReviewStatus.COMPLETED]),
                'pending_reviews': len([r for r in reviewer_reviews if r.status == ReviewStatus.IN_PROGRESS]),
                'average_review_time': 0,
                'average_quality_score': 0,
                'review_outcomes': {},
                'review_types': {}
            }
            
            # Calculate averages
            completed_reviews = [r for r in reviewer_reviews if r.status == ReviewStatus.COMPLETED]
            if completed_reviews:
                stats['average_review_time'] = sum(r.review_duration for r in completed_reviews) / len(completed_reviews)
                stats['average_quality_score'] = sum(r.overall_score for r in completed_reviews) / len(completed_reviews)
            
            # Count outcomes
            for review in completed_reviews:
                outcome = review.outcome.value if review.outcome else 'unknown'
                stats['review_outcomes'][outcome] = stats['review_outcomes'].get(outcome, 0) + 1
            
            # Count review types
            for review in reviewer_reviews:
                review_type = review.review_type.value
                stats['review_types'][review_type] = stats['review_types'].get(review_type, 0) + 1
            
            return stats
            
        except Exception as e:
            logger.error(f"Error getting reviewer statistics: {e}")
            return {}
    
    def get_contribution_reviews(self, contribution_id: str) -> List[Review]:
        """Get all reviews for a contribution"""
        try:
            reviews = [r for r in self.reviews.values() if r.contribution_id == contribution_id]
            return sorted(reviews, key=lambda x: x.created_at, reverse=True)
            
        except Exception as e:
            logger.error(f"Error getting contribution reviews: {e}")
            return []
    
    def get_review_consensus(self, contribution_id: str) -> Dict[str, Any]:
        """Get review consensus for a contribution"""
        try:
            reviews = self.get_contribution_reviews(contribution_id)
            completed_reviews = [r for r in reviews if r.status == ReviewStatus.COMPLETED]
            
            if not completed_reviews:
                return {
                    'consensus_reached': False,
                    'total_reviews': 0,
                    'average_score': 0.0,
                    'outcomes': {},
                    'consensus_outcome': None
                }
            
            # Calculate average score
            average_score = sum(r.overall_score for r in completed_reviews) / len(completed_reviews)
            
            # Count outcomes
            outcomes = {}
            for review in completed_reviews:
                outcome = review.outcome.value if review.outcome else 'unknown'
                outcomes[outcome] = outcomes.get(outcome, 0) + 1
            
            # Determine consensus outcome
            consensus_outcome = max(outcomes.items(), key=lambda x: x[1])[0] if outcomes else None
            
            # Check if consensus is reached
            consensus_reached = len(completed_reviews) >= 2 and max(outcomes.values()) > len(completed_reviews) / 2
            
            return {
                'consensus_reached': consensus_reached,
                'total_reviews': len(completed_reviews),
                'average_score': average_score,
                'outcomes': outcomes,
                'consensus_outcome': consensus_outcome,
                'reviews': [
                    {
                        'id': r.id,
                        'reviewer_id': r.reviewer_id,
                        'review_type': r.review_type.value,
                        'outcome': r.outcome.value if r.outcome else None,
                        'overall_score': r.overall_score,
                        'confidence_level': r.confidence_level,
                        'submitted_at': r.submitted_at.isoformat() if r.submitted_at else None
                    }
                    for r in completed_reviews
                ]
            }
            
        except Exception as e:
            logger.error(f"Error getting review consensus: {e}")
            return {}
    
    def escalate_review(self, review_id: str, reason: str):
        """Escalate a review"""
        try:
            review = self.reviews.get(review_id)
            if not review:
                raise ValueError(f"Review {review_id} not found")
            
            review.status = ReviewStatus.ESCALATED
            review.metadata['escalation_reason'] = reason
            review.metadata['escalated_at'] = django_timezone.now().isoformat()
            review.updated_at = django_timezone.now()
            
            # Update assignment
            assignment = self.review_assignments.get(review.assignment_id)
            if assignment:
                assignment.status = ReviewStatus.ESCALATED
                assignment.notes = f"Escalated: {reason}"
            
            logger.info(f"Escalated review: {review_id}")
            
        except Exception as e:
            logger.error(f"Error escalating review: {e}")
    
    def cancel_review(self, review_id: str, reason: str):
        """Cancel a review"""
        try:
            review = self.reviews.get(review_id)
            if not review:
                raise ValueError(f"Review {review_id} not found")
            
            review.status = ReviewStatus.CANCELLED
            review.metadata['cancellation_reason'] = reason
            review.metadata['cancelled_at'] = django_timezone.now().isoformat()
            review.updated_at = django_timezone.now()
            
            # Update assignment
            assignment = self.review_assignments.get(review.assignment_id)
            if assignment:
                assignment.status = ReviewStatus.CANCELLED
                assignment.notes = f"Cancelled: {reason}"
            
            # Update reviewer profile
            profile = self.reviewer_profiles.get(review.reviewer_id)
            if profile:
                profile.current_reviews = max(0, profile.current_reviews - 1)
            
            logger.info(f"Cancelled review: {review_id}")
            
        except Exception as e:
            logger.error(f"Error cancelling review: {e}")
    
    def get_review_workflow(self, workflow_id: str) -> Optional[ReviewWorkflow]:
        """Get a review workflow by ID"""
        return self.workflows.get(workflow_id)
    
    def get_review_workflows(self) -> List[ReviewWorkflow]:
        """Get all review workflows"""
        return list(self.workflows.values())
    
    def create_review_workflow(self, workflow_data: Dict[str, Any]) -> ReviewWorkflow:
        """Create a new review workflow"""
        try:
            workflow = ReviewWorkflow(
                id=workflow_data['id'],
                name=workflow_data['name'],
                description=workflow_data.get('description', ''),
                contribution_types=workflow_data.get('contribution_types', []),
                review_stages=workflow_data.get('review_stages', []),
                auto_assign=workflow_data.get('auto_assign', True),
                parallel_reviews=workflow_data.get('parallel_reviews', False),
                min_reviewers=workflow_data.get('min_reviewers', 1),
                max_reviewers=workflow_data.get('max_reviewers', 3),
                consensus_required=workflow_data.get('consensus_required', False),
                escalation_threshold=workflow_data.get('escalation_threshold', 0.5),
                timeout_hours=workflow_data.get('timeout_hours', 72),
                enabled=workflow_data.get('enabled', True)
            )
            
            self.workflows[workflow.id] = workflow
            
            logger.info(f"Created review workflow: {workflow.id}")
            return workflow
            
        except Exception as e:
            logger.error(f"Error creating review workflow: {e}")
            raise
    
    def update_review_workflow(self, workflow_id: str, updates: Dict[str, Any]):
        """Update a review workflow"""
        try:
            workflow = self.workflows.get(workflow_id)
            if workflow:
                for key, value in updates.items():
                    if hasattr(workflow, key):
                        setattr(workflow, key, value)
                
                workflow.updated_at = django_timezone.now()
                
                logger.info(f"Updated review workflow: {workflow_id}")
            
        except Exception as e:
            logger.error(f"Error updating review workflow: {e}")
    
    def delete_review_workflow(self, workflow_id: str):
        """Delete a review workflow"""
        try:
            if workflow_id in self.workflows:
                del self.workflows[workflow_id]
                logger.info(f"Deleted review workflow: {workflow_id}")
            
        except Exception as e:
            logger.error(f"Error deleting review workflow: {e}")
    
    def get_review_criteria(self, criteria_id: str) -> Optional[ReviewCriteria]:
        """Get review criteria by ID"""
        return self.review_criteria.get(criteria_id)
    
    def get_review_criteria_list(self, review_type: ReviewType = None) -> List[ReviewCriteria]:
        """Get review criteria filtered by type"""
        try:
            criteria = list(self.review_criteria.values())
            
            if review_type:
                criteria = [c for c in criteria if c.review_type == review_type]
            
            return sorted(criteria, key=lambda x: x.weight, reverse=True)
            
        except Exception as e:
            logger.error(f"Error getting review criteria: {e}")
            return []
    
    def create_review_criteria(self, criteria_data: Dict[str, Any]) -> ReviewCriteria:
        """Create new review criteria"""
        try:
            criteria = ReviewCriteria(
                id=criteria_data['id'],
                name=criteria_data['name'],
                description=criteria_data['description'],
                review_type=ReviewType(criteria_data['review_type']),
                weight=criteria_data.get('weight', 0.1),
                required=criteria_data.get('required', True),
                scoring_type=criteria_data.get('scoring_type', 'scale'),
                scale_min=criteria_data.get('scale_min', 1),
                scale_max=criteria_data.get('scale_max', 5),
                options=criteria_data.get('options', []),
                guidelines=criteria_data.get('guidelines', ''),
                examples=criteria_data.get('examples', [])
            )
            
            self.review_criteria[criteria.id] = criteria
            
            logger.info(f"Created review criteria: {criteria.id}")
            return criteria
            
        except Exception as e:
            logger.error(f"Error creating review criteria: {e}")
            raise
    
    def update_review_criteria(self, criteria_id: str, updates: Dict[str, Any]):
        """Update review criteria"""
        try:
            criteria = self.review_criteria.get(criteria_id)
            if criteria:
                for key, value in updates.items():
                    if hasattr(criteria, key):
                        setattr(criteria, key, value)
                
                logger.info(f"Updated review criteria: {criteria_id}")
            
        except Exception as e:
            logger.error(f"Error updating review criteria: {e}")
    
    def delete_review_criteria(self, criteria_id: str):
        """Delete review criteria"""
        try:
            if criteria_id in self.review_criteria:
                del self.review_criteria[criteria_id]
                logger.info(f"Deleted review criteria: {criteria_id}")
            
        except Exception as e:
            logger.error(f"Error deleting review criteria: {e}")
    
    def cleanup_expired_reviews(self):
        """Clean up expired reviews"""
        try:
            expired_assignments = []
            current_time = django_timezone.now()
            
            for assignment_id, assignment in self.review_assignments.items():
                if (assignment.status == ReviewStatus.PENDING and 
                    assignment.due_date and 
                    current_time > assignment.due_date):
                    
                    assignment.status = ReviewStatus.EXPIRED
                    assignment.notes = "Review expired due to timeout"
                    expired_assignments.append(assignment_id)
            
            logger.info(f"Cleaned up {len(expired_assignments)} expired reviews")
            
        except Exception as e:
            logger.error(f"Error cleaning up expired reviews: {e}")
    
    def get_review_analytics(self, period: str = "30_days") -> Dict[str, Any]:
        """Get review analytics"""
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
            
            # Get reviews in period
            period_reviews = [
                r for r in self.reviews.values()
                if start_date <= r.created_at <= end_date
            ]
            
            analytics = {
                'period': period,
                'start_date': start_date.isoformat(),
                'end_date': end_date.isoformat(),
                'total_reviews': len(period_reviews),
                'completed_reviews': len([r for r in period_reviews if r.status == ReviewStatus.COMPLETED]),
                'pending_reviews': len([r for r in period_reviews if r.status == ReviewStatus.IN_PROGRESS]),
                'rejected_reviews': len([r for r in period_reviews if r.status == ReviewStatus.REJECTED]),
                'approved_reviews': len([r for r in period_reviews if r.status == ReviewStatus.APPROVED]),
                'average_review_time': 0,
                'average_quality_score': 0,
                'review_outcomes': {},
                'review_types': {},
                'reviewer_performance': {},
                'consensus_rate': 0,
                'escalation_rate': 0,
                'timeout_rate': 0
            }
            
            # Calculate averages
            completed_reviews = [r for r in period_reviews if r.status == ReviewStatus.COMPLETED]
            if completed_reviews:
                analytics['average_review_time'] = sum(r.review_duration for r in completed_reviews) / len(completed_reviews)
                analytics['average_quality_score'] = sum(r.overall_score for r in completed_reviews) / len(completed_reviews)
            
            # Count outcomes
            for review in completed_reviews:
                outcome = review.outcome.value if review.outcome else 'unknown'
                analytics['review_outcomes'][outcome] = analytics['review_outcomes'].get(outcome, 0) + 1
            
            # Count review types
            for review in period_reviews:
                review_type = review.review_type.value
                analytics['review_types'][review_type] = analytics['review_types'].get(review_type, 0) + 1
            
            # Calculate consensus rate
            contributions = set(r.contribution_id for r in period_reviews)
            consensus_count = 0
            for contribution_id in contributions:
                consensus = self.get_review_consensus(contribution_id)
                if consensus['consensus_reached']:
                    consensus_count += 1
            
            if contributions:
                analytics['consensus_rate'] = consensus_count / len(contributions)
            
            # Calculate escalation rate
            escalated_reviews = len([r for r in period_reviews if r.status == ReviewStatus.ESCALATED])
            if period_reviews:
                analytics['escalation_rate'] = escalated_reviews / len(period_reviews)
            
            # Calculate timeout rate
            expired_assignments = len([a for a in self.review_assignments.values() if a.status == ReviewStatus.EXPIRED])
            total_assignments = len(self.review_assignments)
            if total_assignments:
                analytics['timeout_rate'] = expired_assignments / total_assignments
            
            return analytics
            
        except Exception as e:
            logger.error(f"Error getting review analytics: {e}")
            return {}
    
    def export_review_data(self, review_ids: List[str] = None) -> List[Dict[str, Any]]:
        """Export review data"""
        try:
            if review_ids:
                reviews = [self.reviews.get(rid) for rid in review_ids if rid in self.reviews]
            else:
                reviews = list(self.reviews.values())
            
            export_data = []
            for review in reviews:
                if review:
                    export_data.append({
                        'id': review.id,
                        'assignment_id': review.assignment_id,
                        'contribution_id': review.contribution_id,
                        'reviewer_id': review.reviewer_id,
                        'review_type': review.review_type.value,
                        'status': review.status.value,
                        'outcome': review.outcome.value if review.outcome else None,
                        'overall_score': review.overall_score,
                        'criteria_scores': review.criteria_scores,
                        'comments': review.comments,
                        'suggestions': review.suggestions,
                        'issues_found': review.issues_found,
                        'strengths': review.strengths,
                        'recommendations': review.recommendations,
                        'confidence_level': review.confidence_level,
                        'review_duration': review.review_duration,
                        'created_at': review.created_at.isoformat(),
                        'updated_at': review.updated_at.isoformat(),
                        'submitted_at': review.submitted_at.isoformat() if review.submitted_at else None,
                        'approved_at': review.approved_at.isoformat() if review.approved_at else None,
                        'rejected_at': review.rejected_at.isoformat() if review.rejected_at else None,
                        'metadata': review.metadata
                    })
            
            return export_data
            
        except Exception as e:
            logger.error(f"Error exporting review data: {e}")
            return []
    
    def import_review_data(self, reviews_data: List[Dict[str, Any]]):
        """Import review data"""
        try:
            for review_data in reviews_data:
                review = Review(
                    id=review_data['id'],
                    assignment_id=review_data['assignment_id'],
                    contribution_id=review_data['contribution_id'],
                    reviewer_id=review_data['reviewer_id'],
                    review_type=ReviewType(review_data['review_type']),
                    status=ReviewStatus(review_data['status']),
                    outcome=ReviewOutcome(review_data['outcome']) if review_data.get('outcome') else None,
                    overall_score=review_data.get('overall_score', 0.0),
                    criteria_scores=review_data.get('criteria_scores', {}),
                    comments=review_data.get('comments', ''),
                    suggestions=review_data.get('suggestions', []),
                    issues_found=review_data.get('issues_found', []),
                    strengths=review_data.get('strengths', []),
                    recommendations=review_data.get('recommendations', []),
                    confidence_level=review_data.get('confidence_level', 0.0),
                    review_duration=review_data.get('review_duration', 0),
                    created_at=datetime.fromisoformat(review_data['created_at']),
                    updated_at=datetime.fromisoformat(review_data['updated_at']),
                    submitted_at=datetime.fromisoformat(review_data['submitted_at']) if review_data.get('submitted_at') else None,
                    approved_at=datetime.fromisoformat(review_data['approved_at']) if review_data.get('approved_at') else None,
                    rejected_at=datetime.fromisoformat(review_data['rejected_at']) if review_data.get('rejected_at') else None,
                    metadata=review_data.get('metadata', {})
                )
                
                self.reviews[review.id] = review
            
            logger.info(f"Imported {len(reviews_data)} reviews")
            
        except Exception as e:
            logger.error(f"Error importing review data: {e}")
            raise
