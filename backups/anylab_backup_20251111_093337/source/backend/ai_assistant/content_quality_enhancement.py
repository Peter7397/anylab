"""
Content Quality Enhancement System for AnyLab AI Assistant

This module provides comprehensive content quality enhancement capabilities including
content validation, quality scoring, improvement suggestions, automated corrections,
and quality monitoring for the AnyLab knowledge base.
"""

import os
import json
import logging
import re
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional, Tuple
from dataclasses import dataclass, asdict
from enum import Enum
from django.conf import settings
from django.core.cache import cache
from django.utils import timezone

logger = logging.getLogger(__name__)


class QualityLevel(Enum):
    """Content quality levels"""
    POOR = "poor"
    FAIR = "fair"
    GOOD = "good"
    EXCELLENT = "excellent"


class QualityDimension(Enum):
    """Quality assessment dimensions"""
    ACCURACY = "accuracy"
    COMPLETENESS = "completeness"
    CLARITY = "clarity"
    RELEVANCE = "relevance"
    TIMELINESS = "timeliness"
    STRUCTURE = "structure"
    LANGUAGE = "language"
    TECHNICAL_CORRECTNESS = "technical_correctness"


class ContentType(Enum):
    """Types of content"""
    DOCUMENT = "document"
    ARTICLE = "article"
    FAQ = "faq"
    TUTORIAL = "tutorial"
    REFERENCE = "reference"
    TROUBLESHOOTING = "troubleshooting"
    PROCEDURE = "procedure"
    SPECIFICATION = "specification"


class EnhancementAction(Enum):
    """Types of enhancement actions"""
    CORRECT_SPELLING = "correct_spelling"
    IMPROVE_GRAMMAR = "improve_grammar"
    ADD_STRUCTURE = "add_structure"
    ENHANCE_CLARITY = "enhance_clarity"
    ADD_EXAMPLES = "add_examples"
    UPDATE_INFORMATION = "update_information"
    ADD_METADATA = "add_metadata"
    IMPROVE_FORMATTING = "improve_formatting"


@dataclass
class QualityScore:
    """Quality score for content"""
    overall_score: float  # 0-100
    dimension_scores: Dict[QualityDimension, float]
    quality_level: QualityLevel
    assessment_date: datetime
    assessor: str
    confidence: float


@dataclass
class QualityIssue:
    """Quality issue identified in content"""
    id: str
    content_id: str
    issue_type: str
    severity: str  # low, medium, high, critical
    description: str
    location: Optional[str]  # line number, section, etc.
    suggestion: str
    auto_fixable: bool
    detected_at: datetime
    resolved: bool
    resolved_at: Optional[datetime]


@dataclass
class EnhancementSuggestion:
    """Enhancement suggestion for content"""
    id: str
    content_id: str
    action_type: EnhancementAction
    description: str
    priority: str  # low, medium, high
    effort_estimate: str  # low, medium, high
    impact_estimate: str  # low, medium, high
    suggested_changes: List[str]
    created_at: datetime
    implemented: bool
    implemented_at: Optional[datetime]


@dataclass
class ContentQualityProfile:
    """Quality profile for content"""
    content_id: str
    content_type: ContentType
    current_score: Optional[QualityScore]
    quality_history: List[QualityScore]
    issues: List[QualityIssue]
    suggestions: List[EnhancementSuggestion]
    last_assessed: Optional[datetime]
    improvement_trend: str  # improving, declining, stable
    target_score: float


class ContentValidator:
    """Validates content against quality standards"""
    
    def __init__(self):
        self.validation_rules = self._initialize_validation_rules()
        self.spell_checker = self._initialize_spell_checker()
        self.grammar_checker = self._initialize_grammar_checker()
    
    def _initialize_validation_rules(self) -> Dict[str, Any]:
        """Initialize content validation rules"""
        return {
            "min_length": {
                ContentType.DOCUMENT: 500,
                ContentType.ARTICLE: 300,
                ContentType.FAQ: 100,
                ContentType.TUTORIAL: 1000,
                ContentType.REFERENCE: 200,
                ContentType.TROUBLESHOOTING: 200,
                ContentType.PROCEDURE: 300,
                ContentType.SPECIFICATION: 400
            },
            "max_length": {
                ContentType.DOCUMENT: 10000,
                ContentType.ARTICLE: 5000,
                ContentType.FAQ: 2000,
                ContentType.TUTORIAL: 15000,
                ContentType.REFERENCE: 3000,
                ContentType.TROUBLESHOOTING: 3000,
                ContentType.PROCEDURE: 2000,
                ContentType.SPECIFICATION: 5000
            },
            "required_sections": {
                ContentType.DOCUMENT: ["title", "introduction", "body", "conclusion"],
                ContentType.ARTICLE: ["title", "introduction", "body"],
                ContentType.FAQ: ["question", "answer"],
                ContentType.TUTORIAL: ["title", "introduction", "steps", "conclusion"],
                ContentType.REFERENCE: ["title", "description", "parameters"],
                ContentType.TROUBLESHOOTING: ["title", "problem", "solution"],
                ContentType.PROCEDURE: ["title", "purpose", "steps", "notes"],
                ContentType.SPECIFICATION: ["title", "overview", "details", "requirements"]
            },
            "forbidden_words": [
                "lorem", "ipsum", "placeholder", "test", "example", "dummy"
            ],
            "required_elements": {
                "has_title": True,
                "has_introduction": True,
                "has_conclusion": False,
                "has_examples": False,
                "has_references": False
            }
        }
    
    def _initialize_spell_checker(self) -> Dict[str, Any]:
        """Initialize spell checker (simplified version)"""
        # In a real implementation, this would use a proper spell checking library
        return {
            "common_misspellings": {
                "recieve": "receive",
                "seperate": "separate",
                "occured": "occurred",
                "definately": "definitely",
                "accomodate": "accommodate"
            }
        }
    
    def _initialize_grammar_checker(self) -> Dict[str, Any]:
        """Initialize grammar checker (simplified version)"""
        # In a real implementation, this would use a proper grammar checking library
        return {
            "grammar_rules": [
                "sentence_starts_with_capital",
                "sentence_ends_with_punctuation",
                "no_double_spaces",
                "consistent_tense"
            ]
        }
    
    def validate_content(self, content: str, content_type: ContentType) -> Dict[str, Any]:
        """Validate content against quality standards"""
        validation_result = {
            "is_valid": True,
            "errors": [],
            "warnings": [],
            "suggestions": [],
            "score": 0.0
        }
        
        # Check length requirements
        content_length = len(content)
        min_length = self.validation_rules["min_length"].get(content_type, 100)
        max_length = self.validation_rules["max_length"].get(content_type, 5000)
        
        if content_length < min_length:
            validation_result["errors"].append(f"Content too short: {content_length} < {min_length}")
            validation_result["is_valid"] = False
        elif content_length > max_length:
            validation_result["warnings"].append(f"Content too long: {content_length} > {max_length}")
        
        # Check for forbidden words
        content_lower = content.lower()
        for forbidden_word in self.validation_rules["forbidden_words"]:
            if forbidden_word in content_lower:
                validation_result["warnings"].append(f"Contains forbidden word: {forbidden_word}")
        
        # Check spelling
        spelling_issues = self._check_spelling(content)
        validation_result["errors"].extend(spelling_issues)
        
        # Check grammar
        grammar_issues = self._check_grammar(content)
        validation_result["warnings"].extend(grammar_issues)
        
        # Check structure
        structure_issues = self._check_structure(content, content_type)
        validation_result["suggestions"].extend(structure_issues)
        
        # Calculate score
        validation_result["score"] = self._calculate_validation_score(validation_result)
        
        return validation_result
    
    def _check_spelling(self, content: str) -> List[str]:
        """Check for spelling errors"""
        errors = []
        words = re.findall(r'\b\w+\b', content.lower())
        
        for word in words:
            if word in self.spell_checker["common_misspellings"]:
                correct_word = self.spell_checker["common_misspellings"][word]
                errors.append(f"Spelling error: '{word}' should be '{correct_word}'")
        
        return errors
    
    def _check_grammar(self, content: str) -> List[str]:
        """Check for grammar issues"""
        warnings = []
        
        # Check sentence capitalization
        sentences = re.split(r'[.!?]+', content)
        for sentence in sentences:
            sentence = sentence.strip()
            if sentence and not sentence[0].isupper():
                warnings.append("Sentence should start with capital letter")
        
        # Check double spaces
        if '  ' in content:
            warnings.append("Content contains double spaces")
        
        return warnings
    
    def _check_structure(self, content: str, content_type: ContentType) -> List[str]:
        """Check content structure"""
        suggestions = []
        
        # Check for required sections
        required_sections = self.validation_rules["required_sections"].get(content_type, [])
        
        for section in required_sections:
            if section not in content.lower():
                suggestions.append(f"Consider adding a {section} section")
        
        # Check for examples
        if "example" not in content.lower() and content_type in [ContentType.TUTORIAL, ContentType.PROCEDURE]:
            suggestions.append("Consider adding examples to improve clarity")
        
        return suggestions
    
    def _calculate_validation_score(self, validation_result: Dict[str, Any]) -> float:
        """Calculate validation score based on issues found"""
        base_score = 100.0
        
        # Deduct points for errors
        base_score -= len(validation_result["errors"]) * 10
        
        # Deduct points for warnings
        base_score -= len(validation_result["warnings"]) * 5
        
        # Deduct points for suggestions
        base_score -= len(validation_result["suggestions"]) * 2
        
        return max(0.0, base_score)


class QualityAssessor:
    """Assesses content quality across multiple dimensions"""
    
    def __init__(self):
        self.assessment_criteria = self._initialize_assessment_criteria()
    
    def _initialize_assessment_criteria(self) -> Dict[QualityDimension, Dict[str, Any]]:
        """Initialize quality assessment criteria"""
        return {
            QualityDimension.ACCURACY: {
                "weight": 0.25,
                "factors": ["factual_correctness", "technical_accuracy", "source_reliability"]
            },
            QualityDimension.COMPLETENESS: {
                "weight": 0.20,
                "factors": ["coverage", "detail_level", "missing_information"]
            },
            QualityDimension.CLARITY: {
                "weight": 0.20,
                "factors": ["readability", "organization", "explanation_quality"]
            },
            QualityDimension.RELEVANCE: {
                "weight": 0.15,
                "factors": ["topic_relevance", "audience_match", "current_applicability"]
            },
            QualityDimension.TIMELINESS: {
                "weight": 0.10,
                "factors": ["publication_date", "update_frequency", "currency"]
            },
            QualityDimension.STRUCTURE: {
                "weight": 0.05,
                "factors": ["logical_flow", "section_organization", "formatting"]
            },
            QualityDimension.LANGUAGE: {
                "weight": 0.03,
                "factors": ["grammar", "spelling", "style"]
            },
            QualityDimension.TECHNICAL_CORRECTNESS: {
                "weight": 0.02,
                "factors": ["technical_accuracy", "terminology", "procedures"]
            }
        }
    
    def assess_content_quality(self, content: str, content_type: ContentType, 
                             assessor: str = "system") -> QualityScore:
        """Assess content quality across all dimensions"""
        dimension_scores = {}
        
        for dimension, criteria in self.assessment_criteria.items():
            score = self._assess_dimension(content, dimension, content_type)
            dimension_scores[dimension] = score
        
        # Calculate overall score
        overall_score = sum(
            score * criteria["weight"] 
            for dimension, score in dimension_scores.items()
            for criteria in [self.assessment_criteria[dimension]]
        )
        
        # Determine quality level
        quality_level = self._determine_quality_level(overall_score)
        
        # Calculate confidence (simplified)
        confidence = min(0.95, 0.7 + (overall_score / 100) * 0.25)
        
        return QualityScore(
            overall_score=overall_score,
            dimension_scores=dimension_scores,
            quality_level=quality_level,
            assessment_date=timezone.now(),
            assessor=assessor,
            confidence=confidence
        )
    
    def _assess_dimension(self, content: str, dimension: QualityDimension, 
                        content_type: ContentType) -> float:
        """Assess a specific quality dimension"""
        if dimension == QualityDimension.ACCURACY:
            return self._assess_accuracy(content)
        elif dimension == QualityDimension.COMPLETENESS:
            return self._assess_completeness(content, content_type)
        elif dimension == QualityDimension.CLARITY:
            return self._assess_clarity(content)
        elif dimension == QualityDimension.RELEVANCE:
            return self._assess_relevance(content, content_type)
        elif dimension == QualityDimension.TIMELINESS:
            return self._assess_timeliness(content)
        elif dimension == QualityDimension.STRUCTURE:
            return self._assess_structure(content)
        elif dimension == QualityDimension.LANGUAGE:
            return self._assess_language(content)
        elif dimension == QualityDimension.TECHNICAL_CORRECTNESS:
            return self._assess_technical_correctness(content)
        else:
            return 50.0  # Default score
    
    def _assess_accuracy(self, content: str) -> float:
        """Assess accuracy dimension"""
        score = 70.0  # Base score
        
        # Check for factual indicators
        if any(word in content.lower() for word in ["verified", "confirmed", "tested", "validated"]):
            score += 15
        
        # Check for source citations
        if any(word in content.lower() for word in ["source:", "reference:", "according to"]):
            score += 10
        
        # Check for uncertainty indicators
        if any(word in content.lower() for word in ["maybe", "possibly", "might", "could be"]):
            score -= 5
        
        return min(100.0, max(0.0, score))
    
    def _assess_completeness(self, content: str, content_type: ContentType) -> float:
        """Assess completeness dimension"""
        score = 60.0  # Base score
        
        # Check content length
        content_length = len(content)
        if content_length > 1000:
            score += 20
        elif content_length > 500:
            score += 10
        
        # Check for comprehensive coverage indicators
        if any(word in content.lower() for word in ["overview", "introduction", "conclusion", "summary"]):
            score += 10
        
        # Check for examples
        if "example" in content.lower() or "for instance" in content.lower():
            score += 10
        
        return min(100.0, max(0.0, score))
    
    def _assess_clarity(self, content: str) -> float:
        """Assess clarity dimension"""
        score = 70.0  # Base score
        
        # Check for clear explanations
        if any(word in content.lower() for word in ["clearly", "simply", "easily", "straightforward"]):
            score += 10
        
        # Check for step-by-step instructions
        if any(word in content.lower() for word in ["step 1", "first", "next", "then", "finally"]):
            score += 15
        
        # Check for complex sentences (negative indicator)
        sentences = re.split(r'[.!?]+', content)
        long_sentences = [s for s in sentences if len(s.split()) > 25]
        if len(long_sentences) > len(sentences) * 0.3:
            score -= 10
        
        return min(100.0, max(0.0, score))
    
    def _assess_relevance(self, content: str, content_type: ContentType) -> float:
        """Assess relevance dimension"""
        score = 80.0  # Base score
        
        # Check for topic-specific keywords
        topic_keywords = {
            ContentType.TROUBLESHOOTING: ["problem", "issue", "error", "solution", "fix"],
            ContentType.TUTORIAL: ["how to", "step", "guide", "learn"],
            ContentType.REFERENCE: ["specification", "parameter", "setting", "configuration"],
            ContentType.PROCEDURE: ["procedure", "process", "workflow", "steps"]
        }
        
        keywords = topic_keywords.get(content_type, [])
        keyword_matches = sum(1 for keyword in keywords if keyword in content.lower())
        score += min(20, keyword_matches * 4)
        
        return min(100.0, max(0.0, score))
    
    def _assess_timeliness(self, content: str) -> float:
        """Assess timeliness dimension"""
        score = 75.0  # Base score
        
        # Check for date references
        if re.search(r'\b(20\d{2}|january|february|march|april|may|june|july|august|september|october|november|december)\b', content.lower()):
            score += 15
        
        # Check for current technology references
        current_tech = ["2024", "2023", "latest", "current", "modern", "recent"]
        if any(tech in content.lower() for tech in current_tech):
            score += 10
        
        return min(100.0, max(0.0, score))
    
    def _assess_structure(self, content: str) -> float:
        """Assess structure dimension"""
        score = 70.0  # Base score
        
        # Check for headings
        if re.search(r'^#+\s', content, re.MULTILINE):
            score += 15
        
        # Check for lists
        if re.search(r'^\s*[-*+]\s', content, re.MULTILINE) or re.search(r'^\s*\d+\.\s', content, re.MULTILINE):
            score += 10
        
        # Check for paragraphs
        paragraphs = content.split('\n\n')
        if len(paragraphs) > 2:
            score += 5
        
        return min(100.0, max(0.0, score))
    
    def _assess_language(self, content: str) -> float:
        """Assess language dimension"""
        score = 80.0  # Base score
        
        # Check for spelling errors (simplified)
        common_errors = ["recieve", "seperate", "occured", "definately"]
        error_count = sum(1 for error in common_errors if error in content.lower())
        score -= error_count * 10
        
        # Check for grammar issues
        if not re.search(r'[.!?]$', content.strip()):
            score -= 5
        
        return min(100.0, max(0.0, score))
    
    def _assess_technical_correctness(self, content: str) -> float:
        """Assess technical correctness dimension"""
        score = 75.0  # Base score
        
        # Check for technical terminology
        if any(word in content.lower() for word in ["api", "database", "algorithm", "protocol", "configuration"]):
            score += 15
        
        # Check for code examples
        if "```" in content or "code:" in content.lower():
            score += 10
        
        return min(100.0, max(0.0, score))
    
    def _determine_quality_level(self, score: float) -> QualityLevel:
        """Determine quality level based on score"""
        if score >= 90:
            return QualityLevel.EXCELLENT
        elif score >= 75:
            return QualityLevel.GOOD
        elif score >= 60:
            return QualityLevel.FAIR
        else:
            return QualityLevel.POOR


class ContentEnhancer:
    """Provides content enhancement suggestions and automated improvements"""
    
    def __init__(self):
        self.enhancement_templates = self._initialize_enhancement_templates()
    
    def _initialize_enhancement_templates(self) -> Dict[EnhancementAction, Dict[str, Any]]:
        """Initialize enhancement templates"""
        return {
            EnhancementAction.CORRECT_SPELLING: {
                "description": "Correct spelling errors",
                "effort": "low",
                "impact": "medium"
            },
            EnhancementAction.IMPROVE_GRAMMAR: {
                "description": "Improve grammar and sentence structure",
                "effort": "medium",
                "impact": "medium"
            },
            EnhancementAction.ADD_STRUCTURE: {
                "description": "Add headings, lists, and better organization",
                "effort": "medium",
                "impact": "high"
            },
            EnhancementAction.ENHANCE_CLARITY: {
                "description": "Improve clarity and readability",
                "effort": "high",
                "impact": "high"
            },
            EnhancementAction.ADD_EXAMPLES: {
                "description": "Add examples and illustrations",
                "effort": "high",
                "impact": "high"
            },
            EnhancementAction.UPDATE_INFORMATION: {
                "description": "Update outdated information",
                "effort": "medium",
                "impact": "high"
            },
            EnhancementAction.ADD_METADATA: {
                "description": "Add metadata and tags",
                "effort": "low",
                "impact": "medium"
            },
            EnhancementAction.IMPROVE_FORMATTING: {
                "description": "Improve formatting and presentation",
                "effort": "low",
                "impact": "medium"
            }
        }
    
    def generate_enhancement_suggestions(self, content: str, content_type: ContentType,
                                       quality_score: QualityScore) -> List[EnhancementSuggestion]:
        """Generate enhancement suggestions based on quality assessment"""
        suggestions = []
        
        # Analyze dimension scores to identify improvement areas
        for dimension, score in quality_score.dimension_scores.items():
            if score < 70:  # Below good quality
                suggestion = self._create_suggestion_for_dimension(
                    content, dimension, score, content_type
                )
                if suggestion:
                    suggestions.append(suggestion)
        
        # Add general suggestions based on content analysis
        general_suggestions = self._analyze_content_for_suggestions(content, content_type)
        suggestions.extend(general_suggestions)
        
        # Sort by priority
        suggestions.sort(key=lambda x: self._calculate_priority(x), reverse=True)
        
        return suggestions
    
    def _create_suggestion_for_dimension(self, content: str, dimension: QualityDimension,
                                       score: float, content_type: ContentType) -> Optional[EnhancementSuggestion]:
        """Create enhancement suggestion for a specific dimension"""
        if dimension == QualityDimension.LANGUAGE and score < 70:
            return EnhancementSuggestion(
                id=f"LANG-{hash(content) % 10000}",
                content_id="content_id",  # Would be passed in real implementation
                action_type=EnhancementAction.IMPROVE_GRAMMAR,
                description="Improve grammar and language quality",
                priority="high" if score < 50 else "medium",
                effort_estimate="medium",
                impact_estimate="medium",
                suggested_changes=[
                    "Review sentence structure",
                    "Check for grammatical errors",
                    "Improve word choice"
                ],
                created_at=timezone.now(),
                implemented=False,
                implemented_at=None
            )
        
        elif dimension == QualityDimension.STRUCTURE and score < 70:
            return EnhancementSuggestion(
                id=f"STRUCT-{hash(content) % 10000}",
                content_id="content_id",
                action_type=EnhancementAction.ADD_STRUCTURE,
                description="Improve content structure and organization",
                priority="high" if score < 50 else "medium",
                effort_estimate="medium",
                impact_estimate="high",
                suggested_changes=[
                    "Add clear headings",
                    "Organize content into logical sections",
                    "Add bullet points or numbered lists"
                ],
                created_at=timezone.now(),
                implemented=False,
                implemented_at=None
            )
        
        elif dimension == QualityDimension.CLARITY and score < 70:
            return EnhancementSuggestion(
                id=f"CLARITY-{hash(content) % 10000}",
                content_id="content_id",
                action_type=EnhancementAction.ENHANCE_CLARITY,
                description="Improve content clarity and readability",
                priority="high" if score < 50 else "medium",
                effort_estimate="high",
                impact_estimate="high",
                suggested_changes=[
                    "Simplify complex sentences",
                    "Add explanations for technical terms",
                    "Use more descriptive language"
                ],
                created_at=timezone.now(),
                implemented=False,
                implemented_at=None
            )
        
        return None
    
    def _analyze_content_for_suggestions(self, content: str, content_type: ContentType) -> List[EnhancementSuggestion]:
        """Analyze content for general enhancement opportunities"""
        suggestions = []
        
        # Check for examples
        if content_type in [ContentType.TUTORIAL, ContentType.PROCEDURE] and "example" not in content.lower():
            suggestions.append(EnhancementSuggestion(
                id=f"EXAMPLES-{hash(content) % 10000}",
                content_id="content_id",
                action_type=EnhancementAction.ADD_EXAMPLES,
                description="Add examples to improve understanding",
                priority="high",
                effort_estimate="high",
                impact_estimate="high",
                suggested_changes=[
                    "Add practical examples",
                    "Include code samples if applicable",
                    "Provide real-world scenarios"
                ],
                created_at=timezone.now(),
                implemented=False,
                implemented_at=None
            ))
        
        # Check for metadata
        if not any(word in content.lower() for word in ["tags:", "keywords:", "category:"]):
            suggestions.append(EnhancementSuggestion(
                id=f"METADATA-{hash(content) % 10000}",
                content_id="content_id",
                action_type=EnhancementAction.ADD_METADATA,
                description="Add metadata for better discoverability",
                priority="medium",
                effort_estimate="low",
                impact_estimate="medium",
                suggested_changes=[
                    "Add relevant tags",
                    "Include keywords",
                    "Specify content category"
                ],
                created_at=timezone.now(),
                implemented=False,
                implemented_at=None
            ))
        
        return suggestions
    
    def _calculate_priority(self, suggestion: EnhancementSuggestion) -> int:
        """Calculate priority score for suggestion"""
        priority_scores = {"low": 1, "medium": 2, "high": 3}
        effort_scores = {"low": 3, "medium": 2, "high": 1}
        impact_scores = {"low": 1, "medium": 2, "high": 3}
        
        return (priority_scores.get(suggestion.priority, 2) + 
                effort_scores.get(suggestion.effort_estimate, 2) + 
                impact_scores.get(suggestion.impact_estimate, 2))


class QualityMonitor:
    """Monitors content quality over time"""
    
    def __init__(self):
        self.quality_profiles = {}
        self.monitoring_rules = self._initialize_monitoring_rules()
    
    def _initialize_monitoring_rules(self) -> Dict[str, Any]:
        """Initialize quality monitoring rules"""
        return {
            "quality_thresholds": {
                QualityLevel.POOR: 0.6,
                QualityLevel.FAIR: 0.75,
                QualityLevel.GOOD: 0.85,
                QualityLevel.EXCELLENT: 0.95
            },
            "monitoring_frequency": {
                "high_priority": 7,  # days
                "medium_priority": 30,
                "low_priority": 90
            },
            "alert_conditions": [
                "quality_decline",
                "new_issues",
                "outdated_content",
                "low_user_satisfaction"
            ]
        }
    
    def create_quality_profile(self, content_id: str, content_type: ContentType) -> ContentQualityProfile:
        """Create quality profile for content"""
        profile = ContentQualityProfile(
            content_id=content_id,
            content_type=content_type,
            current_score=None,
            quality_history=[],
            issues=[],
            suggestions=[],
            last_assessed=None,
            improvement_trend="stable",
            target_score=80.0
        )
        
        self.quality_profiles[content_id] = profile
        logger.info(f"Created quality profile for content: {content_id}")
        return profile
    
    def update_quality_profile(self, content_id: str, quality_score: QualityScore,
                              issues: List[QualityIssue] = None,
                              suggestions: List[EnhancementSuggestion] = None) -> bool:
        """Update quality profile with new assessment"""
        if content_id not in self.quality_profiles:
            return False
        
        profile = self.quality_profiles[content_id]
        
        # Update current score
        profile.current_score = quality_score
        profile.last_assessed = quality_score.assessment_date
        
        # Add to history
        profile.quality_history.append(quality_score)
        
        # Update issues
        if issues:
            profile.issues.extend(issues)
        
        # Update suggestions
        if suggestions:
            profile.suggestions.extend(suggestions)
        
        # Calculate improvement trend
        profile.improvement_trend = self._calculate_improvement_trend(profile.quality_history)
        
        logger.info(f"Updated quality profile for content: {content_id}")
        return True
    
    def _calculate_improvement_trend(self, quality_history: List[QualityScore]) -> str:
        """Calculate improvement trend from quality history"""
        if len(quality_history) < 2:
            return "stable"
        
        recent_scores = [score.overall_score for score in quality_history[-3:]]
        
        if len(recent_scores) >= 2:
            if recent_scores[-1] > recent_scores[-2]:
                return "improving"
            elif recent_scores[-1] < recent_scores[-2]:
                return "declining"
        
        return "stable"
    
    def get_content_needing_review(self) -> List[str]:
        """Get list of content IDs that need quality review"""
        content_needing_review = []
        current_time = timezone.now()
        
        for content_id, profile in self.quality_profiles.items():
            if not profile.last_assessed:
                content_needing_review.append(content_id)
                continue
            
            days_since_assessment = (current_time - profile.last_assessed).days
            
            # Determine review frequency based on current quality
            if profile.current_score:
                if profile.current_score.overall_score < 60:
                    review_frequency = self.monitoring_rules["monitoring_frequency"]["high_priority"]
                elif profile.current_score.overall_score < 80:
                    review_frequency = self.monitoring_rules["monitoring_frequency"]["medium_priority"]
                else:
                    review_frequency = self.monitoring_rules["monitoring_frequency"]["low_priority"]
                
                if days_since_assessment >= review_frequency:
                    content_needing_review.append(content_id)
        
        return content_needing_review
    
    def get_quality_alerts(self) -> List[Dict[str, Any]]:
        """Get quality alerts for content"""
        alerts = []
        
        for content_id, profile in self.quality_profiles.items():
            if not profile.current_score:
                continue
            
            # Check for quality decline
            if profile.improvement_trend == "declining":
                alerts.append({
                    "content_id": content_id,
                    "alert_type": "quality_decline",
                    "severity": "medium",
                    "message": f"Quality declining for content {content_id}",
                    "current_score": profile.current_score.overall_score
                })
            
            # Check for low quality
            if profile.current_score.overall_score < 60:
                alerts.append({
                    "content_id": content_id,
                    "alert_type": "low_quality",
                    "severity": "high",
                    "message": f"Low quality content detected: {content_id}",
                    "current_score": profile.current_score.overall_score
                })
            
            # Check for outdated content
            if profile.last_assessed and (timezone.now() - profile.last_assessed).days > 365:
                alerts.append({
                    "content_id": content_id,
                    "alert_type": "outdated_content",
                    "severity": "medium",
                    "message": f"Content may be outdated: {content_id}",
                    "last_assessed": profile.last_assessed
                })
        
        return alerts


# Example usage and testing
if __name__ == "__main__":
    # Initialize content quality enhancement system
    validator = ContentValidator()
    assessor = QualityAssessor()
    enhancer = ContentEnhancer()
    monitor = QualityMonitor()
    
    # Sample content for testing
    sample_content = """
    # HPLC Troubleshooting Guide
    
    High Performance Liquid Chromatography (HPLC) is a widely used analytical technique in laboratories.
    This guide provides common troubleshooting steps for HPLC systems.
    
    ## Common Problems
    
    1. **Peak Tailing**: This occurs when peaks are not symmetrical.
       - Check column condition
       - Verify mobile phase pH
       - Ensure proper sample preparation
    
    2. **Baseline Drift**: Gradual change in baseline signal.
       - Check temperature stability
       - Verify mobile phase composition
       - Inspect detector lamp
    
    ## Solutions
    
    For peak tailing, try adjusting the mobile phase pH or replacing the column.
    For baseline drift, ensure temperature control and check for air bubbles.
    
    ## Examples
    
    Example 1: If you see peak tailing, first check the column pressure.
    Example 2: For baseline issues, start with temperature verification.
    """
    
    content_type = ContentType.TROUBLESHOOTING
    
    # Validate content
    validation_result = validator.validate_content(sample_content, content_type)
    print(f"Validation score: {validation_result['score']}")
    print(f"Errors: {len(validation_result['errors'])}")
    print(f"Warnings: {len(validation_result['warnings'])}")
    print(f"Suggestions: {len(validation_result['suggestions'])}")
    
    # Assess quality
    quality_score = assessor.assess_content_quality(sample_content, content_type)
    print(f"\nQuality Assessment:")
    print(f"Overall score: {quality_score.overall_score}")
    print(f"Quality level: {quality_score.quality_level.value}")
    print(f"Confidence: {quality_score.confidence}")
    
    # Generate enhancement suggestions
    suggestions = enhancer.generate_enhancement_suggestions(sample_content, content_type, quality_score)
    print(f"\nEnhancement suggestions: {len(suggestions)}")
    for suggestion in suggestions[:3]:  # Show first 3
        print(f"- {suggestion.description} (Priority: {suggestion.priority})")
    
    # Create quality profile
    content_id = "HPLC_TROUBLESHOOTING_001"
    profile = monitor.create_quality_profile(content_id, content_type)
    monitor.update_quality_profile(content_id, quality_score, suggestions=suggestions)
    
    print(f"\nQuality profile created for: {content_id}")
    print(f"Improvement trend: {profile.improvement_trend}")
    
    print("\nContent Quality Enhancement System initialized successfully!")
