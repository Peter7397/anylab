"""
Continuous Content Quality Monitoring

This module provides continuous monitoring of content quality,
including accuracy, completeness, relevance, and user satisfaction metrics.
"""

import logging
import re
import statistics
from typing import Dict, Any, List, Optional, Tuple, Union
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from enum import Enum
from django.utils import timezone as django_timezone
from django.core.cache import cache

logger = logging.getLogger(__name__)


class QualityMetric(Enum):
    """Quality metric enumeration"""
    ACCURACY = "accuracy"
    COMPLETENESS = "completeness"
    RELEVANCE = "relevance"
    CLARITY = "clarity"
    CONSISTENCY = "consistency"
    TIMELINESS = "timeliness"
    USABILITY = "usability"
    ACCESSIBILITY = "accessibility"


class QualityLevel(Enum):
    """Quality level enumeration"""
    EXCELLENT = "excellent"
    GOOD = "good"
    FAIR = "fair"
    POOR = "poor"
    CRITICAL = "critical"


class QualityStatus(Enum):
    """Quality status enumeration"""
    PASSING = "passing"
    WARNING = "warning"
    FAILING = "failing"
    UNKNOWN = "unknown"


@dataclass
class QualityCheck:
    """Quality check structure"""
    id: str
    content_id: str
    metric: QualityMetric
    score: float
    level: QualityLevel
    status: QualityStatus
    details: str
    recommendations: List[str] = field(default_factory=list)
    metadata: Dict[str, Any] = field(default_factory=dict)
    checked_at: datetime = field(default_factory=lambda: django_timezone.now())
    checked_by: str = "system"


@dataclass
class QualityReport:
    """Quality report structure"""
    id: str
    content_id: str
    overall_score: float
    overall_level: QualityLevel
    overall_status: QualityStatus
    checks: List[QualityCheck] = field(default_factory=list)
    trends: Dict[str, Any] = field(default_factory=dict)
    recommendations: List[str] = field(default_factory=list)
    generated_at: datetime = field(default_factory=lambda: django_timezone.now())
    generated_by: str = "system"


@dataclass
class QualityThreshold:
    """Quality threshold structure"""
    metric: QualityMetric
    excellent_min: float = 0.9
    good_min: float = 0.7
    fair_min: float = 0.5
    poor_min: float = 0.3
    critical_max: float = 0.3


class ContinuousContentQualityMonitoring:
    """Continuous Content Quality Monitoring System"""
    
    def __init__(self, config: Dict[str, Any] = None):
        """Initialize quality monitoring system"""
        self.config = config or {}
        self.monitoring_enabled = self.config.get('monitoring_enabled', True)
        self.auto_checks = self.config.get('auto_checks', True)
        self.alerting_enabled = self.config.get('alerting_enabled', True)
        self.cache_enabled = self.config.get('cache_enabled', True)
        self.check_interval = self.config.get('check_interval', 3600)  # seconds
        
        # Initialize components
        self.quality_checks = {}
        self.quality_reports = {}
        self.quality_thresholds = {}
        self.cache = cache if self.cache_enabled else None
        
        # Initialize monitoring system
        self._initialize_monitoring_system()
        
        logger.info("Continuous Content Quality Monitoring initialized")
    
    def _initialize_monitoring_system(self):
        """Initialize monitoring system components"""
        try:
            # Initialize quality checkers
            self.checkers = {
                QualityMetric.ACCURACY: self._check_accuracy,
                QualityMetric.COMPLETENESS: self._check_completeness,
                QualityMetric.RELEVANCE: self._check_relevance,
                QualityMetric.CLARITY: self._check_clarity,
                QualityMetric.CONSISTENCY: self._check_consistency,
                QualityMetric.TIMELINESS: self._check_timeliness,
                QualityMetric.USABILITY: self._check_usability,
                QualityMetric.ACCESSIBILITY: self._check_accessibility
            }
            
            # Initialize quality thresholds
            self._initialize_quality_thresholds()
            
            logger.info("Monitoring system components initialized")
            
        except Exception as e:
            logger.error(f"Error initializing monitoring system: {e}")
            raise
    
    def _initialize_quality_thresholds(self):
        """Initialize quality thresholds"""
        try:
            thresholds = [
                QualityThreshold(QualityMetric.ACCURACY, 0.95, 0.85, 0.70, 0.50, 0.30),
                QualityThreshold(QualityMetric.COMPLETENESS, 0.90, 0.80, 0.65, 0.45, 0.25),
                QualityThreshold(QualityMetric.RELEVANCE, 0.90, 0.75, 0.60, 0.40, 0.20),
                QualityThreshold(QualityMetric.CLARITY, 0.85, 0.70, 0.55, 0.35, 0.15),
                QualityThreshold(QualityMetric.CONSISTENCY, 0.90, 0.80, 0.65, 0.45, 0.25),
                QualityThreshold(QualityMetric.TIMELINESS, 0.95, 0.85, 0.70, 0.50, 0.30),
                QualityThreshold(QualityMetric.USABILITY, 0.85, 0.70, 0.55, 0.35, 0.15),
                QualityThreshold(QualityMetric.ACCESSIBILITY, 0.90, 0.80, 0.65, 0.45, 0.25)
            ]
            
            for threshold in thresholds:
                self.quality_thresholds[threshold.metric] = threshold
            
            logger.info(f"Initialized {len(thresholds)} quality thresholds")
            
        except Exception as e:
            logger.error(f"Error initializing quality thresholds: {e}")
            raise
    
    def check_content_quality(self, content_id: str, content: str, metadata: Dict[str, Any] = None) -> QualityReport:
        """Check quality of content"""
        try:
            # Check cache first
            if self.cache_enabled:
                cache_key = f"quality_check_{content_id}_{hash(content) % 10000}"
                cached_report = self.cache.get(cache_key)
                if cached_report:
                    return cached_report
            
            # Perform quality checks
            checks = []
            for metric in QualityMetric:
                checker = self.checkers.get(metric)
                if checker:
                    check = checker(content_id, content, metadata or {})
                    checks.append(check)
                    self.quality_checks[check.id] = check
            
            # Calculate overall score
            overall_score = self._calculate_overall_score(checks)
            overall_level = self._determine_quality_level(overall_score)
            overall_status = self._determine_quality_status(overall_score)
            
            # Generate recommendations
            recommendations = self._generate_recommendations(checks)
            
            # Create quality report
            report = QualityReport(
                id=f"quality_report_{content_id}_{django_timezone.now().strftime('%Y%m%d_%H%M%S')}",
                content_id=content_id,
                overall_score=overall_score,
                overall_level=overall_level,
                overall_status=overall_status,
                checks=checks,
                recommendations=recommendations
            )
            
            # Store report
            self.quality_reports[report.id] = report
            
            # Cache report
            if self.cache_enabled:
                self.cache.set(cache_key, report, timeout=3600)
            
            logger.info(f"Quality check completed for content {content_id}: {overall_level.value}")
            return report
            
        except Exception as e:
            logger.error(f"Error checking content quality: {e}")
            raise
    
    def _check_accuracy(self, content_id: str, content: str, metadata: Dict[str, Any]) -> QualityCheck:
        """Check content accuracy"""
        try:
            score = 0.8  # Mock accuracy score
            
            # Mock accuracy checks
            if "error" in content.lower():
                score -= 0.1
            if "incorrect" in content.lower():
                score -= 0.1
            if "wrong" in content.lower():
                score -= 0.1
            
            # Ensure score is between 0 and 1
            score = max(0.0, min(1.0, score))
            
            level = self._determine_quality_level(score)
            status = self._determine_quality_status(score)
            
            check = QualityCheck(
                id=f"accuracy_check_{content_id}_{django_timezone.now().strftime('%Y%m%d_%H%M%S')}",
                content_id=content_id,
                metric=QualityMetric.ACCURACY,
                score=score,
                level=level,
                status=status,
                details=f"Accuracy score: {score:.2f}",
                recommendations=["Verify technical accuracy", "Check for typos"]
            )
            
            return check
            
        except Exception as e:
            logger.error(f"Error checking accuracy: {e}")
            return self._create_error_check(content_id, QualityMetric.ACCURACY)
    
    def _check_completeness(self, content_id: str, content: str, metadata: Dict[str, Any]) -> QualityCheck:
        """Check content completeness"""
        try:
            score = 0.7  # Mock completeness score
            
            # Mock completeness checks
            if len(content) < 100:
                score -= 0.2
            if "TODO" in content:
                score -= 0.1
            if "TBD" in content:
                score -= 0.1
            if "coming soon" in content.lower():
                score -= 0.1
            
            # Ensure score is between 0 and 1
            score = max(0.0, min(1.0, score))
            
            level = self._determine_quality_level(score)
            status = self._determine_quality_status(score)
            
            check = QualityCheck(
                id=f"completeness_check_{content_id}_{django_timezone.now().strftime('%Y%m%d_%H%M%S')}",
                content_id=content_id,
                metric=QualityMetric.COMPLETENESS,
                score=score,
                level=level,
                status=status,
                details=f"Completeness score: {score:.2f}",
                recommendations=["Add missing information", "Complete incomplete sections"]
            )
            
            return check
            
        except Exception as e:
            logger.error(f"Error checking completeness: {e}")
            return self._create_error_check(content_id, QualityMetric.COMPLETENESS)
    
    def _check_relevance(self, content_id: str, content: str, metadata: Dict[str, Any]) -> QualityCheck:
        """Check content relevance"""
        try:
            score = 0.75  # Mock relevance score
            
            # Mock relevance checks
            if "agilent" in content.lower():
                score += 0.1
            if "laboratory" in content.lower():
                score += 0.1
            if "instrument" in content.lower():
                score += 0.1
            
            # Ensure score is between 0 and 1
            score = max(0.0, min(1.0, score))
            
            level = self._determine_quality_level(score)
            status = self._determine_quality_status(score)
            
            check = QualityCheck(
                id=f"relevance_check_{content_id}_{django_timezone.now().strftime('%Y%m%d_%H%M%S')}",
                content_id=content_id,
                metric=QualityMetric.RELEVANCE,
                score=score,
                level=level,
                status=status,
                details=f"Relevance score: {score:.2f}",
                recommendations=["Improve topic relevance", "Add more specific information"]
            )
            
            return check
            
        except Exception as e:
            logger.error(f"Error checking relevance: {e}")
            return self._create_error_check(content_id, QualityMetric.RELEVANCE)
    
    def _check_clarity(self, content_id: str, content: str, metadata: Dict[str, Any]) -> QualityCheck:
        """Check content clarity"""
        try:
            score = 0.8  # Mock clarity score
            
            # Mock clarity checks
            if len(content.split()) < 50:
                score -= 0.1
            if "jargon" in content.lower():
                score -= 0.1
            if "complex" in content.lower():
                score -= 0.1
            
            # Ensure score is between 0 and 1
            score = max(0.0, min(1.0, score))
            
            level = self._determine_quality_level(score)
            status = self._determine_quality_status(score)
            
            check = QualityCheck(
                id=f"clarity_check_{content_id}_{django_timezone.now().strftime('%Y%m%d_%H%M%S')}",
                content_id=content_id,
                metric=QualityMetric.CLARITY,
                score=score,
                level=level,
                status=status,
                details=f"Clarity score: {score:.2f}",
                recommendations=["Simplify language", "Add explanations"]
            )
            
            return check
            
        except Exception as e:
            logger.error(f"Error checking clarity: {e}")
            return self._create_error_check(content_id, QualityMetric.CLARITY)
    
    def _check_consistency(self, content_id: str, content: str, metadata: Dict[str, Any]) -> QualityCheck:
        """Check content consistency"""
        try:
            score = 0.85  # Mock consistency score
            
            # Mock consistency checks
            if "inconsistent" in content.lower():
                score -= 0.1
            if "contradict" in content.lower():
                score -= 0.1
            
            # Ensure score is between 0 and 1
            score = max(0.0, min(1.0, score))
            
            level = self._determine_quality_level(score)
            status = self._determine_quality_status(score)
            
            check = QualityCheck(
                id=f"consistency_check_{content_id}_{django_timezone.now().strftime('%Y%m%d_%H%M%S')}",
                content_id=content_id,
                metric=QualityMetric.CONSISTENCY,
                score=score,
                level=level,
                status=status,
                details=f"Consistency score: {score:.2f}",
                recommendations=["Ensure consistent terminology", "Check for contradictions"]
            )
            
            return check
            
        except Exception as e:
            logger.error(f"Error checking consistency: {e}")
            return self._create_error_check(content_id, QualityMetric.CONSISTENCY)
    
    def _check_timeliness(self, content_id: str, content: str, metadata: Dict[str, Any]) -> QualityCheck:
        """Check content timeliness"""
        try:
            score = 0.9  # Mock timeliness score
            
            # Mock timeliness checks
            if "outdated" in content.lower():
                score -= 0.2
            if "old" in content.lower():
                score -= 0.1
            if "deprecated" in content.lower():
                score -= 0.2
            
            # Ensure score is between 0 and 1
            score = max(0.0, min(1.0, score))
            
            level = self._determine_quality_level(score)
            status = self._determine_quality_status(score)
            
            check = QualityCheck(
                id=f"timeliness_check_{content_id}_{django_timezone.now().strftime('%Y%m%d_%H%M%S')}",
                content_id=content_id,
                metric=QualityMetric.TIMELINESS,
                score=score,
                level=level,
                status=status,
                details=f"Timeliness score: {score:.2f}",
                recommendations=["Update outdated information", "Check for recent changes"]
            )
            
            return check
            
        except Exception as e:
            logger.error(f"Error checking timeliness: {e}")
            return self._create_error_check(content_id, QualityMetric.TIMELINESS)
    
    def _check_usability(self, content_id: str, content: str, metadata: Dict[str, Any]) -> QualityCheck:
        """Check content usability"""
        try:
            score = 0.75  # Mock usability score
            
            # Mock usability checks
            if "user-friendly" in content.lower():
                score += 0.1
            if "easy" in content.lower():
                score += 0.1
            if "difficult" in content.lower():
                score -= 0.1
            
            # Ensure score is between 0 and 1
            score = max(0.0, min(1.0, score))
            
            level = self._determine_quality_level(score)
            status = self._determine_quality_status(score)
            
            check = QualityCheck(
                id=f"usability_check_{content_id}_{django_timezone.now().strftime('%Y%m%d_%H%M%S')}",
                content_id=content_id,
                metric=QualityMetric.USABILITY,
                score=score,
                level=level,
                status=status,
                details=f"Usability score: {score:.2f}",
                recommendations=["Improve user experience", "Add user guidance"]
            )
            
            return check
            
        except Exception as e:
            logger.error(f"Error checking usability: {e}")
            return self._create_error_check(content_id, QualityMetric.USABILITY)
    
    def _check_accessibility(self, content_id: str, content: str, metadata: Dict[str, Any]) -> QualityCheck:
        """Check content accessibility"""
        try:
            score = 0.8  # Mock accessibility score
            
            # Mock accessibility checks
            if "accessible" in content.lower():
                score += 0.1
            if "inclusive" in content.lower():
                score += 0.1
            
            # Ensure score is between 0 and 1
            score = max(0.0, min(1.0, score))
            
            level = self._determine_quality_level(score)
            status = self._determine_quality_status(score)
            
            check = QualityCheck(
                id=f"accessibility_check_{content_id}_{django_timezone.now().strftime('%Y%m%d_%H%M%S')}",
                content_id=content_id,
                metric=QualityMetric.ACCESSIBILITY,
                score=score,
                level=level,
                status=status,
                details=f"Accessibility score: {score:.2f}",
                recommendations=["Improve accessibility", "Add alternative formats"]
            )
            
            return check
            
        except Exception as e:
            logger.error(f"Error checking accessibility: {e}")
            return self._create_error_check(content_id, QualityMetric.ACCESSIBILITY)
    
    def _create_error_check(self, content_id: str, metric: QualityMetric) -> QualityCheck:
        """Create an error check"""
        return QualityCheck(
            id=f"error_check_{content_id}_{metric.value}_{django_timezone.now().strftime('%Y%m%d_%H%M%S')}",
            content_id=content_id,
            metric=metric,
            score=0.0,
            level=QualityLevel.CRITICAL,
            status=QualityStatus.FAILING,
            details=f"Error checking {metric.value}",
            recommendations=["Fix quality check error"]
        )
    
    def _calculate_overall_score(self, checks: List[QualityCheck]) -> float:
        """Calculate overall quality score"""
        try:
            if not checks:
                return 0.0
            
            scores = [check.score for check in checks if check.score > 0]
            if not scores:
                return 0.0
            
            return statistics.mean(scores)
            
        except Exception as e:
            logger.error(f"Error calculating overall score: {e}")
            return 0.0
    
    def _determine_quality_level(self, score: float) -> QualityLevel:
        """Determine quality level from score"""
        try:
            if score >= 0.9:
                return QualityLevel.EXCELLENT
            elif score >= 0.7:
                return QualityLevel.GOOD
            elif score >= 0.5:
                return QualityLevel.FAIR
            elif score >= 0.3:
                return QualityLevel.POOR
            else:
                return QualityLevel.CRITICAL
            
        except Exception as e:
            logger.error(f"Error determining quality level: {e}")
            return QualityLevel.CRITICAL
    
    def _determine_quality_status(self, score: float) -> QualityStatus:
        """Determine quality status from score"""
        try:
            if score >= 0.7:
                return QualityStatus.PASSING
            elif score >= 0.5:
                return QualityStatus.WARNING
            else:
                return QualityStatus.FAILING
            
        except Exception as e:
            logger.error(f"Error determining quality status: {e}")
            return QualityStatus.FAILING
    
    def _generate_recommendations(self, checks: List[QualityCheck]) -> List[str]:
        """Generate quality recommendations"""
        try:
            recommendations = []
            
            for check in checks:
                if check.status == QualityStatus.FAILING:
                    recommendations.extend(check.recommendations)
                elif check.status == QualityStatus.WARNING:
                    recommendations.extend(check.recommendations[:1])  # Take first recommendation
            
            return list(set(recommendations))  # Remove duplicates
            
        except Exception as e:
            logger.error(f"Error generating recommendations: {e}")
            return []
    
    def get_quality_report(self, report_id: str) -> Optional[QualityReport]:
        """Get a quality report by ID"""
        return self.quality_reports.get(report_id)
    
    def get_quality_check(self, check_id: str) -> Optional[QualityCheck]:
        """Get a quality check by ID"""
        return self.quality_checks.get(check_id)
    
    def get_quality_trends(self, content_id: str, days: int = 30) -> Dict[str, Any]:
        """Get quality trends for content"""
        try:
            cutoff_date = django_timezone.now() - timedelta(days=days)
            
            # Get recent reports for content
            recent_reports = [
                report for report in self.quality_reports.values()
                if report.content_id == content_id and report.generated_at >= cutoff_date
            ]
            
            if not recent_reports:
                return {}
            
            # Calculate trends
            trends = {
                "overall_score_trend": [],
                "metric_trends": {},
                "status_changes": [],
                "recommendation_trends": []
            }
            
            # Overall score trend
            for report in sorted(recent_reports, key=lambda x: x.generated_at):
                trends["overall_score_trend"].append({
                    "date": report.generated_at.isoformat(),
                    "score": report.overall_score,
                    "level": report.overall_level.value,
                    "status": report.overall_status.value
                })
            
            # Metric trends
            for metric in QualityMetric:
                metric_trend = []
                for report in sorted(recent_reports, key=lambda x: x.generated_at):
                    metric_check = next((check for check in report.checks if check.metric == metric), None)
                    if metric_check:
                        metric_trend.append({
                            "date": report.generated_at.isoformat(),
                            "score": metric_check.score,
                            "level": metric_check.level.value,
                            "status": metric_check.status.value
                        })
                trends["metric_trends"][metric.value] = metric_trend
            
            return trends
            
        except Exception as e:
            logger.error(f"Error getting quality trends: {e}")
            return {}
    
    def get_quality_statistics(self) -> Dict[str, Any]:
        """Get quality monitoring statistics"""
        try:
            stats = {
                "total_checks": len(self.quality_checks),
                "total_reports": len(self.quality_reports),
                "checks_by_metric": {},
                "checks_by_level": {},
                "checks_by_status": {},
                "reports_by_level": {},
                "reports_by_status": {},
                "average_overall_score": 0.0,
                "monitoring_enabled": self.monitoring_enabled,
                "auto_checks": self.auto_checks,
                "alerting_enabled": self.alerting_enabled
            }
            
            # Count checks by metric
            for check in self.quality_checks.values():
                metric = check.metric.value
                stats["checks_by_metric"][metric] = stats["checks_by_metric"].get(metric, 0) + 1
                
                level = check.level.value
                stats["checks_by_level"][level] = stats["checks_by_level"].get(level, 0) + 1
                
                status = check.status.value
                stats["checks_by_status"][status] = stats["checks_by_status"].get(status, 0) + 1
            
            # Count reports by level and status
            overall_scores = []
            for report in self.quality_reports.values():
                level = report.overall_level.value
                stats["reports_by_level"][level] = stats["reports_by_level"].get(level, 0) + 1
                
                status = report.overall_status.value
                stats["reports_by_status"][status] = stats["reports_by_status"].get(status, 0) + 1
                
                overall_scores.append(report.overall_score)
            
            # Calculate average overall score
            if overall_scores:
                stats["average_overall_score"] = statistics.mean(overall_scores)
            
            return stats
            
        except Exception as e:
            logger.error(f"Error getting quality statistics: {e}")
            return {}
    
    def export_quality_data(self) -> Dict[str, Any]:
        """Export quality monitoring data"""
        try:
            return {
                "checks": [
                    {
                        "id": check.id,
                        "content_id": check.content_id,
                        "metric": check.metric.value,
                        "score": check.score,
                        "level": check.level.value,
                        "status": check.status.value,
                        "details": check.details,
                        "recommendations": check.recommendations,
                        "metadata": check.metadata,
                        "checked_at": check.checked_at.isoformat(),
                        "checked_by": check.checked_by
                    }
                    for check in self.quality_checks.values()
                ],
                "reports": [
                    {
                        "id": report.id,
                        "content_id": report.content_id,
                        "overall_score": report.overall_score,
                        "overall_level": report.overall_level.value,
                        "overall_status": report.overall_status.value,
                        "checks": [check.id for check in report.checks],
                        "trends": report.trends,
                        "recommendations": report.recommendations,
                        "generated_at": report.generated_at.isoformat(),
                        "generated_by": report.generated_by
                    }
                    for report in self.quality_reports.values()
                ],
                "thresholds": [
                    {
                        "metric": threshold.metric.value,
                        "excellent_min": threshold.excellent_min,
                        "good_min": threshold.good_min,
                        "fair_min": threshold.fair_min,
                        "poor_min": threshold.poor_min,
                        "critical_max": threshold.critical_max
                    }
                    for threshold in self.quality_thresholds.values()
                ]
            }
            
        except Exception as e:
            logger.error(f"Error exporting quality data: {e}")
            return {}
    
    def import_quality_data(self, data: Dict[str, Any]):
        """Import quality monitoring data"""
        try:
            # Import checks
            if "checks" in data:
                for check_data in data["checks"]:
                    check = QualityCheck(
                        id=check_data["id"],
                        content_id=check_data["content_id"],
                        metric=QualityMetric(check_data["metric"]),
                        score=check_data["score"],
                        level=QualityLevel(check_data["level"]),
                        status=QualityStatus(check_data["status"]),
                        details=check_data["details"],
                        recommendations=check_data.get("recommendations", []),
                        metadata=check_data.get("metadata", {}),
                        checked_at=datetime.fromisoformat(check_data["checked_at"]),
                        checked_by=check_data.get("checked_by", "system")
                    )
                    self.quality_checks[check.id] = check
            
            # Import reports
            if "reports" in data:
                for report_data in data["reports"]:
                    # Get checks for this report
                    report_checks = []
                    for check_id in report_data.get("checks", []):
                        check = self.quality_checks.get(check_id)
                        if check:
                            report_checks.append(check)
                    
                    report = QualityReport(
                        id=report_data["id"],
                        content_id=report_data["content_id"],
                        overall_score=report_data["overall_score"],
                        overall_level=QualityLevel(report_data["overall_level"]),
                        overall_status=QualityStatus(report_data["overall_status"]),
                        checks=report_checks,
                        trends=report_data.get("trends", {}),
                        recommendations=report_data.get("recommendations", []),
                        generated_at=datetime.fromisoformat(report_data["generated_at"]),
                        generated_by=report_data.get("generated_by", "system")
                    )
                    self.quality_reports[report.id] = report
            
            # Import thresholds
            if "thresholds" in data:
                for threshold_data in data["thresholds"]:
                    threshold = QualityThreshold(
                        metric=QualityMetric(threshold_data["metric"]),
                        excellent_min=threshold_data["excellent_min"],
                        good_min=threshold_data["good_min"],
                        fair_min=threshold_data["fair_min"],
                        poor_min=threshold_data["poor_min"],
                        critical_max=threshold_data["critical_max"]
                    )
                    self.quality_thresholds[threshold.metric] = threshold
            
            logger.info("Quality monitoring data imported successfully")
            
        except Exception as e:
            logger.error(f"Error importing quality data: {e}")
            raise
