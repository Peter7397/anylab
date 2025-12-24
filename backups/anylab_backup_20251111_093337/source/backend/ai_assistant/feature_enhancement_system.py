"""
Feature Enhancement System for AnyLab AI Assistant

This module provides comprehensive feature enhancement capabilities including
feature request management, enhancement planning, A/B testing, user feedback
analysis, and feature rollout strategies.
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


class FeatureStatus(Enum):
    """Feature enhancement status levels"""
    REQUESTED = "requested"
    UNDER_REVIEW = "under_review"
    APPROVED = "approved"
    IN_DEVELOPMENT = "in_development"
    TESTING = "testing"
    READY_FOR_RELEASE = "ready_for_release"
    RELEASED = "released"
    DEPRECATED = "deprecated"
    REJECTED = "rejected"


class FeaturePriority(Enum):
    """Feature priority levels"""
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"
    STRATEGIC = "strategic"


class FeatureCategory(Enum):
    """Feature categories"""
    USER_INTERFACE = "user_interface"
    FUNCTIONALITY = "functionality"
    PERFORMANCE = "performance"
    SECURITY = "security"
    INTEGRATION = "integration"
    ANALYTICS = "analytics"
    MOBILE = "mobile"
    API = "api"
    AI_ML = "ai_ml"
    AUTOMATION = "automation"


class EnhancementType(Enum):
    """Types of enhancements"""
    NEW_FEATURE = "new_feature"
    IMPROVEMENT = "improvement"
    BUG_FIX = "bug_fix"
    OPTIMIZATION = "optimization"
    REFACTORING = "refactoring"
    INTEGRATION = "integration"
    UI_UX = "ui_ux"


class TestingMethod(Enum):
    """Testing methods for features"""
    UNIT_TESTING = "unit_testing"
    INTEGRATION_TESTING = "integration_testing"
    USER_ACCEPTANCE_TESTING = "user_acceptance_testing"
    A_B_TESTING = "a_b_testing"
    BETA_TESTING = "beta_testing"
    PERFORMANCE_TESTING = "performance_testing"
    SECURITY_TESTING = "security_testing"


@dataclass
class FeatureRequest:
    """Feature request data structure"""
    id: str
    title: str
    description: str
    category: FeatureCategory
    priority: FeaturePriority
    status: FeatureStatus
    enhancement_type: EnhancementType
    requested_by: str
    assigned_to: Optional[str]
    created_at: datetime
    updated_at: datetime
    target_release: Optional[str]
    estimated_effort: Optional[int]  # in hours
    actual_effort: Optional[int]  # in hours
    business_value: Optional[str]
    technical_complexity: Optional[str]
    user_impact: Optional[str]
    dependencies: List[str]
    related_features: List[str]
    feedback_count: int
    votes: int
    tags: List[str]


@dataclass
class EnhancementPlan:
    """Enhancement plan data structure"""
    id: str
    feature_request_id: str
    title: str
    description: str
    implementation_approach: str
    technical_requirements: List[str]
    testing_strategy: List[TestingMethod]
    rollout_strategy: str
    success_metrics: List[str]
    risk_assessment: str
    timeline: Dict[str, datetime]
    resources_required: List[str]
    created_at: datetime
    updated_at: datetime
    status: FeatureStatus


@dataclass
class UserFeedback:
    """User feedback data structure"""
    id: str
    feature_id: str
    user_id: str
    feedback_type: str  # positive, negative, suggestion, bug_report
    content: str
    rating: Optional[int]  # 1-5 scale
    created_at: datetime
    processed: bool
    response: Optional[str]
    tags: List[str]


@dataclass
class ABTest:
    """A/B test data structure"""
    id: str
    name: str
    feature_id: str
    description: str
    variant_a: Dict[str, Any]
    variant_b: Dict[str, Any]
    traffic_split: float  # percentage to variant B
    start_date: datetime
    end_date: Optional[datetime]
    status: str
    success_metric: str
    results: Dict[str, Any]
    statistical_significance: Optional[float]


class FeatureRequestManager:
    """Manages feature requests and their lifecycle"""
    
    def __init__(self):
        self.feature_requests = {}
        self.request_counter = 0
        self.voting_system = {}
    
    def create_feature_request(self, title: str, description: str, 
                             category: FeatureCategory, requested_by: str,
                             enhancement_type: EnhancementType = EnhancementType.NEW_FEATURE,
                             priority: FeaturePriority = FeaturePriority.MEDIUM) -> FeatureRequest:
        """Create a new feature request"""
        self.request_counter += 1
        request_id = f"FR-{self.request_counter:06d}"
        
        feature_request = FeatureRequest(
            id=request_id,
            title=title,
            description=description,
            category=category,
            priority=priority,
            status=FeatureStatus.REQUESTED,
            enhancement_type=enhancement_type,
            requested_by=requested_by,
            assigned_to=None,
            created_at=timezone.now(),
            updated_at=timezone.now(),
            target_release=None,
            estimated_effort=None,
            actual_effort=None,
            business_value=None,
            technical_complexity=None,
            user_impact=None,
            dependencies=[],
            related_features=[],
            feedback_count=0,
            votes=0,
            tags=[]
        )
        
        self.feature_requests[request_id] = feature_request
        logger.info(f"Created feature request: {request_id}")
        return feature_request
    
    def update_feature_request(self, request_id: str, updates: Dict[str, Any]) -> bool:
        """Update feature request"""
        if request_id not in self.feature_requests:
            return False
        
        feature_request = self.feature_requests[request_id]
        
        # Update fields
        for key, value in updates.items():
            if hasattr(feature_request, key):
                setattr(feature_request, key, value)
        
        feature_request.updated_at = timezone.now()
        logger.info(f"Updated feature request: {request_id}")
        return True
    
    def vote_feature_request(self, request_id: str, user_id: str, vote: int) -> bool:
        """Vote on feature request (1-5 scale)"""
        if request_id not in self.feature_requests:
            return False
        
        feature_request = self.feature_requests[request_id]
        
        # Initialize voting system for this request
        if request_id not in self.voting_system:
            self.voting_system[request_id] = {}
        
        # Record vote
        self.voting_system[request_id][user_id] = vote
        
        # Update vote count
        feature_request.votes = len(self.voting_system[request_id])
        
        logger.info(f"User {user_id} voted {vote} on feature request {request_id}")
        return True
    
    def get_feature_request(self, request_id: str) -> Optional[FeatureRequest]:
        """Get feature request by ID"""
        return self.feature_requests.get(request_id)
    
    def search_feature_requests(self, query: str, filters: Dict[str, Any] = None) -> List[FeatureRequest]:
        """Search feature requests"""
        results = []
        
        for request in self.feature_requests.values():
            # Text search
            if query.lower() in request.title.lower() or query.lower() in request.description.lower():
                # Apply filters
                if filters:
                    if "status" in filters and request.status != filters["status"]:
                        continue
                    if "category" in filters and request.category != filters["category"]:
                        continue
                    if "priority" in filters and request.priority != filters["priority"]:
                        continue
                
                results.append(request)
        
        # Sort by votes (most popular first)
        results.sort(key=lambda x: x.votes, reverse=True)
        return results
    
    def get_feature_requests_by_status(self, status: FeatureStatus) -> List[FeatureRequest]:
        """Get feature requests by status"""
        return [req for req in self.feature_requests.values() if req.status == status]
    
    def get_feature_requests_by_user(self, user_id: str) -> List[FeatureRequest]:
        """Get feature requests created by a user"""
        return [req for req in self.feature_requests.values() if req.requested_by == user_id]


class EnhancementPlanner:
    """Plans and manages feature enhancements"""
    
    def __init__(self):
        self.enhancement_plans = {}
        self.plan_counter = 0
    
    def create_enhancement_plan(self, feature_request_id: str, title: str, 
                              description: str, implementation_approach: str) -> EnhancementPlan:
        """Create an enhancement plan for a feature request"""
        self.plan_counter += 1
        plan_id = f"EP-{self.plan_counter:06d}"
        
        plan = EnhancementPlan(
            id=plan_id,
            feature_request_id=feature_request_id,
            title=title,
            description=description,
            implementation_approach=implementation_approach,
            technical_requirements=[],
            testing_strategy=[],
            rollout_strategy="",
            success_metrics=[],
            risk_assessment="",
            timeline={},
            resources_required=[],
            created_at=timezone.now(),
            updated_at=timezone.now(),
            status=FeatureStatus.UNDER_REVIEW
        )
        
        self.enhancement_plans[plan_id] = plan
        logger.info(f"Created enhancement plan: {plan_id}")
        return plan
    
    def update_enhancement_plan(self, plan_id: str, updates: Dict[str, Any]) -> bool:
        """Update enhancement plan"""
        if plan_id not in self.enhancement_plans:
            return False
        
        plan = self.enhancement_plans[plan_id]
        
        for key, value in updates.items():
            if hasattr(plan, key):
                setattr(plan, key, value)
        
        plan.updated_at = timezone.now()
        logger.info(f"Updated enhancement plan: {plan_id}")
        return True
    
    def add_technical_requirement(self, plan_id: str, requirement: str) -> bool:
        """Add technical requirement to enhancement plan"""
        if plan_id not in self.enhancement_plans:
            return False
        
        plan = self.enhancement_plans[plan_id]
        plan.technical_requirements.append(requirement)
        plan.updated_at = timezone.now()
        
        logger.info(f"Added technical requirement to plan {plan_id}")
        return True
    
    def add_testing_method(self, plan_id: str, method: TestingMethod) -> bool:
        """Add testing method to enhancement plan"""
        if plan_id not in self.enhancement_plans:
            return False
        
        plan = self.enhancement_plans[plan_id]
        plan.testing_strategy.append(method)
        plan.updated_at = timezone.now()
        
        logger.info(f"Added testing method to plan {plan_id}")
        return True
    
    def set_timeline(self, plan_id: str, timeline: Dict[str, datetime]) -> bool:
        """Set timeline for enhancement plan"""
        if plan_id not in self.enhancement_plans:
            return False
        
        plan = self.enhancement_plans[plan_id]
        plan.timeline = timeline
        plan.updated_at = timezone.now()
        
        logger.info(f"Set timeline for plan {plan_id}")
        return True
    
    def get_enhancement_plan(self, plan_id: str) -> Optional[EnhancementPlan]:
        """Get enhancement plan by ID"""
        return self.enhancement_plans.get(plan_id)
    
    def get_plans_by_status(self, status: FeatureStatus) -> List[EnhancementPlan]:
        """Get enhancement plans by status"""
        return [plan for plan in self.enhancement_plans.values() if plan.status == status]


class UserFeedbackManager:
    """Manages user feedback for features"""
    
    def __init__(self):
        self.feedback_entries = {}
        self.feedback_counter = 0
    
    def submit_feedback(self, feature_id: str, user_id: str, feedback_type: str,
                       content: str, rating: Optional[int] = None) -> UserFeedback:
        """Submit user feedback for a feature"""
        self.feedback_counter += 1
        feedback_id = f"FB-{self.feedback_counter:06d}"
        
        feedback = UserFeedback(
            id=feedback_id,
            feature_id=feature_id,
            user_id=user_id,
            feedback_type=feedback_type,
            content=content,
            rating=rating,
            created_at=timezone.now(),
            processed=False,
            response=None,
            tags=[]
        )
        
        self.feedback_entries[feedback_id] = feedback
        logger.info(f"Submitted feedback: {feedback_id}")
        return feedback
    
    def process_feedback(self, feedback_id: str, response: str) -> bool:
        """Process user feedback with a response"""
        if feedback_id not in self.feedback_entries:
            return False
        
        feedback = self.feedback_entries[feedback_id]
        feedback.processed = True
        feedback.response = response
        
        logger.info(f"Processed feedback: {feedback_id}")
        return True
    
    def get_feedback_for_feature(self, feature_id: str) -> List[UserFeedback]:
        """Get all feedback for a specific feature"""
        return [fb for fb in self.feedback_entries.values() if fb.feature_id == feature_id]
    
    def analyze_feedback_sentiment(self, feature_id: str) -> Dict[str, Any]:
        """Analyze feedback sentiment for a feature"""
        feedback_list = self.get_feedback_for_feature(feature_id)
        
        if not feedback_list:
            return {"sentiment": "neutral", "confidence": 0.0, "sample_size": 0}
        
        # Simple sentiment analysis based on feedback type and rating
        positive_count = 0
        negative_count = 0
        neutral_count = 0
        
        for feedback in feedback_list:
            if feedback.feedback_type == "positive" or (feedback.rating and feedback.rating >= 4):
                positive_count += 1
            elif feedback.feedback_type == "negative" or (feedback.rating and feedback.rating <= 2):
                negative_count += 1
            else:
                neutral_count += 1
        
        total = len(feedback_list)
        
        if positive_count > negative_count:
            sentiment = "positive"
            confidence = positive_count / total
        elif negative_count > positive_count:
            sentiment = "negative"
            confidence = negative_count / total
        else:
            sentiment = "neutral"
            confidence = neutral_count / total
        
        return {
            "sentiment": sentiment,
            "confidence": confidence,
            "sample_size": total,
            "positive_count": positive_count,
            "negative_count": negative_count,
            "neutral_count": neutral_count
        }


class ABTestingManager:
    """Manages A/B testing for features"""
    
    def __init__(self):
        self.ab_tests = {}
        self.test_counter = 0
        self.test_results = {}
    
    def create_ab_test(self, name: str, feature_id: str, description: str,
                      variant_a: Dict[str, Any], variant_b: Dict[str, Any],
                      traffic_split: float = 0.5, success_metric: str = "conversion_rate") -> ABTest:
        """Create a new A/B test"""
        self.test_counter += 1
        test_id = f"AB-{self.test_counter:06d}"
        
        ab_test = ABTest(
            id=test_id,
            name=name,
            feature_id=feature_id,
            description=description,
            variant_a=variant_a,
            variant_b=variant_b,
            traffic_split=traffic_split,
            start_date=timezone.now(),
            end_date=None,
            status="active",
            success_metric=success_metric,
            results={},
            statistical_significance=None
        )
        
        self.ab_tests[test_id] = ab_test
        logger.info(f"Created A/B test: {test_id}")
        return ab_test
    
    def assign_user_to_variant(self, test_id: str, user_id: str) -> str:
        """Assign user to a test variant"""
        if test_id not in self.ab_tests:
            return "control"
        
        ab_test = self.ab_tests[test_id]
        
        # Simple hash-based assignment
        user_hash = hash(user_id) % 100
        if user_hash < (ab_test.traffic_split * 100):
            return "variant_b"
        else:
            return "variant_a"
    
    def record_test_result(self, test_id: str, user_id: str, variant: str, 
                          metric_value: float) -> bool:
        """Record result for A/B test"""
        if test_id not in self.ab_tests:
            return False
        
        if test_id not in self.test_results:
            self.test_results[test_id] = {"variant_a": [], "variant_b": []}
        
        self.test_results[test_id][variant].append({
            "user_id": user_id,
            "metric_value": metric_value,
            "timestamp": timezone.now()
        })
        
        logger.info(f"Recorded test result for {test_id}, variant {variant}")
        return True
    
    def analyze_test_results(self, test_id: str) -> Dict[str, Any]:
        """Analyze A/B test results"""
        if test_id not in self.ab_tests or test_id not in self.test_results:
            return {"error": "Test not found"}
        
        ab_test = self.ab_tests[test_id]
        results = self.test_results[test_id]
        
        variant_a_results = results["variant_a"]
        variant_b_results = results["variant_b"]
        
        if not variant_a_results or not variant_b_results:
            return {"error": "Insufficient data"}
        
        # Calculate basic statistics
        variant_a_mean = sum(r["metric_value"] for r in variant_a_results) / len(variant_a_results)
        variant_b_mean = sum(r["metric_value"] for r in variant_b_results) / len(variant_b_results)
        
        # Calculate improvement
        improvement = ((variant_b_mean - variant_a_mean) / variant_a_mean) * 100 if variant_a_mean > 0 else 0
        
        # Simple statistical significance test (t-test simulation)
        # In a real implementation, this would use proper statistical methods
        statistical_significance = 0.95 if abs(improvement) > 5 else 0.75
        
        analysis = {
            "test_id": test_id,
            "variant_a": {
                "sample_size": len(variant_a_results),
                "mean": variant_a_mean,
                "results": variant_a_results
            },
            "variant_b": {
                "sample_size": len(variant_b_results),
                "mean": variant_b_mean,
                "results": variant_b_results
            },
            "improvement_percentage": improvement,
            "statistical_significance": statistical_significance,
            "recommendation": "implement_variant_b" if improvement > 0 and statistical_significance > 0.9 else "continue_testing"
        }
        
        # Update test with results
        ab_test.results = analysis
        ab_test.statistical_significance = statistical_significance
        
        logger.info(f"Analyzed A/B test results for {test_id}")
        return analysis
    
    def end_ab_test(self, test_id: str) -> bool:
        """End an A/B test"""
        if test_id not in self.ab_tests:
            return False
        
        ab_test = self.ab_tests[test_id]
        ab_test.end_date = timezone.now()
        ab_test.status = "completed"
        
        logger.info(f"Ended A/B test: {test_id}")
        return True


class FeatureEnhancementAnalytics:
    """Provides analytics for feature enhancement process"""
    
    def __init__(self, request_manager: FeatureRequestManager, 
                 feedback_manager: UserFeedbackManager,
                 ab_testing_manager: ABTestingManager):
        self.request_manager = request_manager
        self.feedback_manager = feedback_manager
        self.ab_testing_manager = ab_testing_manager
    
    def get_feature_request_analytics(self, start_date: datetime, end_date: datetime) -> Dict[str, Any]:
        """Get analytics for feature requests"""
        requests_in_range = [
            req for req in self.request_manager.feature_requests.values()
            if start_date <= req.created_at <= end_date
        ]
        
        analytics = {
            "total_requests": len(requests_in_range),
            "by_status": {},
            "by_category": {},
            "by_priority": {},
            "avg_votes": 0.0,
            "most_requested_features": [],
            "trends": {}
        }
        
        # Count by status
        for request in requests_in_range:
            status = request.status.value
            analytics["by_status"][status] = analytics["by_status"].get(status, 0) + 1
        
        # Count by category
        for request in requests_in_range:
            category = request.category.value
            analytics["by_category"][category] = analytics["by_category"].get(category, 0) + 1
        
        # Count by priority
        for request in requests_in_range:
            priority = request.priority.value
            analytics["by_priority"][priority] = analytics["by_priority"].get(priority, 0) + 1
        
        # Calculate average votes
        if requests_in_range:
            total_votes = sum(req.votes for req in requests_in_range)
            analytics["avg_votes"] = total_votes / len(requests_in_range)
        
        # Most requested features (by votes)
        sorted_requests = sorted(requests_in_range, key=lambda x: x.votes, reverse=True)
        analytics["most_requested_features"] = [
            {"title": req.title, "votes": req.votes, "status": req.status.value}
            for req in sorted_requests[:5]
        ]
        
        return analytics
    
    def get_user_feedback_analytics(self, start_date: datetime, end_date: datetime) -> Dict[str, Any]:
        """Get analytics for user feedback"""
        feedback_in_range = [
            fb for fb in self.feedback_manager.feedback_entries.values()
            if start_date <= fb.created_at <= end_date
        ]
        
        analytics = {
            "total_feedback": len(feedback_in_range),
            "by_type": {},
            "avg_rating": 0.0,
            "sentiment_distribution": {},
            "processed_rate": 0.0
        }
        
        # Count by type
        for feedback in feedback_in_range:
            fb_type = feedback.feedback_type
            analytics["by_type"][fb_type] = analytics["by_type"].get(fb_type, 0) + 1
        
        # Calculate average rating
        rated_feedback = [fb for fb in feedback_in_range if fb.rating is not None]
        if rated_feedback:
            analytics["avg_rating"] = sum(fb.rating for fb in rated_feedback) / len(rated_feedback)
        
        # Sentiment distribution
        for feedback in feedback_in_range:
            sentiment = self.feedback_manager.analyze_feedback_sentiment(feedback.feature_id)["sentiment"]
            analytics["sentiment_distribution"][sentiment] = analytics["sentiment_distribution"].get(sentiment, 0) + 1
        
        # Processed rate
        processed_feedback = [fb for fb in feedback_in_range if fb.processed]
        if feedback_in_range:
            analytics["processed_rate"] = len(processed_feedback) / len(feedback_in_range)
        
        return analytics
    
    def get_ab_test_analytics(self, start_date: datetime, end_date: datetime) -> Dict[str, Any]:
        """Get analytics for A/B tests"""
        tests_in_range = [
            test for test in self.ab_testing_manager.ab_tests.values()
            if start_date <= test.start_date <= end_date
        ]
        
        analytics = {
            "total_tests": len(tests_in_range),
            "active_tests": len([t for t in tests_in_range if t.status == "active"]),
            "completed_tests": len([t for t in tests_in_range if t.status == "completed"]),
            "avg_improvement": 0.0,
            "successful_tests": 0,
            "test_results": []
        }
        
        improvements = []
        for test in tests_in_range:
            if test.results and "improvement_percentage" in test.results:
                improvement = test.results["improvement_percentage"]
                improvements.append(improvement)
                
                analytics["test_results"].append({
                    "test_id": test.id,
                    "name": test.name,
                    "improvement": improvement,
                    "statistical_significance": test.statistical_significance
                })
                
                if improvement > 0 and test.statistical_significance and test.statistical_significance > 0.9:
                    analytics["successful_tests"] += 1
        
        if improvements:
            analytics["avg_improvement"] = sum(improvements) / len(improvements)
        
        return analytics
    
    def generate_enhancement_report(self, start_date: datetime, end_date: datetime) -> Dict[str, Any]:
        """Generate comprehensive enhancement report"""
        report = {
            "period": {
                "start": start_date,
                "end": end_date
            },
            "feature_requests": self.get_feature_request_analytics(start_date, end_date),
            "user_feedback": self.get_user_feedback_analytics(start_date, end_date),
            "ab_testing": self.get_ab_test_analytics(start_date, end_date),
            "recommendations": []
        }
        
        # Generate recommendations
        if report["feature_requests"]["total_requests"] > 50:
            report["recommendations"].append("High volume of feature requests - consider prioritization framework")
        
        if report["user_feedback"]["avg_rating"] < 3.5:
            report["recommendations"].append("Low user satisfaction - focus on addressing user concerns")
        
        if report["ab_testing"]["successful_tests"] / max(report["ab_testing"]["completed_tests"], 1) < 0.3:
            report["recommendations"].append("Low A/B test success rate - review testing methodology")
        
        return report


# Example usage and testing
if __name__ == "__main__":
    # Initialize feature enhancement system
    request_manager = FeatureRequestManager()
    planner = EnhancementPlanner()
    feedback_manager = UserFeedbackManager()
    ab_testing_manager = ABTestingManager()
    analytics = FeatureEnhancementAnalytics(request_manager, feedback_manager, ab_testing_manager)
    
    # Create a feature request
    feature_request = request_manager.create_feature_request(
        "Dark Mode Support",
        "Add dark mode theme option for better user experience",
        FeatureCategory.USER_INTERFACE,
        "user_123",
        EnhancementType.NEW_FEATURE,
        FeaturePriority.HIGH
    )
    
    print(f"Created feature request: {feature_request.id}")
    
    # Vote on the feature request
    request_manager.vote_feature_request(feature_request.id, "user_456", 5)
    request_manager.vote_feature_request(feature_request.id, "user_789", 4)
    
    print(f"Feature request votes: {feature_request.votes}")
    
    # Create enhancement plan
    enhancement_plan = planner.create_enhancement_plan(
        feature_request.id,
        "Dark Mode Implementation Plan",
        "Implement dark mode using CSS variables and theme switching",
        "CSS-based theme system with JavaScript toggle"
    )
    
    # Add technical requirements
    planner.add_technical_requirement(enhancement_plan.id, "CSS custom properties for colors")
    planner.add_technical_requirement(enhancement_plan.id, "JavaScript theme switcher")
    planner.add_technical_requirement(enhancement_plan.id, "User preference storage")
    
    # Add testing methods
    planner.add_testing_method(enhancement_plan.id, TestingMethod.USER_ACCEPTANCE_TESTING)
    planner.add_testing_method(enhancement_plan.id, TestingMethod.A_B_TESTING)
    
    print(f"Created enhancement plan: {enhancement_plan.id}")
    print(f"Technical requirements: {len(enhancement_plan.technical_requirements)}")
    print(f"Testing methods: {len(enhancement_plan.testing_strategy)}")
    
    # Submit user feedback
    feedback = feedback_manager.submit_feedback(
        feature_request.id,
        "user_999",
        "positive",
        "Dark mode would be great for working in low light conditions!",
        5
    )
    
    print(f"Submitted feedback: {feedback.id}")
    
    # Create A/B test
    ab_test = ab_testing_manager.create_ab_test(
        "Dark Mode Adoption Test",
        feature_request.id,
        "Test user adoption of dark mode feature",
        {"theme": "light", "description": "Default light theme"},
        {"theme": "dark", "description": "New dark theme"},
        0.5,
        "user_engagement"
    )
    
    print(f"Created A/B test: {ab_test.id}")
    
    # Generate analytics report
    end_date = timezone.now()
    start_date = end_date - timedelta(days=30)
    
    report = analytics.generate_enhancement_report(start_date, end_date)
    print(f"Generated enhancement report with {len(report['recommendations'])} recommendations")
    
    print("\nFeature Enhancement System initialized successfully!")
