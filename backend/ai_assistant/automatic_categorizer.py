"""
Automatic Categorization System

This module provides intelligent automatic categorization capabilities
for documents and content based on AI analysis and rule-based classification.
"""

import logging
import json
import re
from typing import Dict, Any, List, Optional, Tuple, Set
from dataclasses import dataclass
from datetime import datetime
import hashlib
import numpy as np
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.naive_bayes import MultinomialNB
from sklearn.linear_model import LogisticRegression
from sklearn.ensemble import RandomForestClassifier
from sklearn.model_selection import train_test_split
from sklearn.metrics import classification_report, accuracy_score
import joblib
import pickle
from pathlib import Path

logger = logging.getLogger(__name__)


@dataclass
class CategoryRule:
    """Category rule definition"""
    category: str
    keywords: List[str]
    patterns: List[str]
    weight: float
    required_keywords: List[str]
    excluded_keywords: List[str]
    min_confidence: float


@dataclass
class CategoryResult:
    """Category classification result"""
    category: str
    confidence: float
    reasoning: str
    matched_keywords: List[str]
    matched_patterns: List[str]
    rule_type: str


@dataclass
class ClassificationModel:
    """Classification model definition"""
    name: str
    model_type: str
    accuracy: float
    categories: List[str]
    features: List[str]
    model_path: str
    created_at: datetime
    last_updated: datetime


class AutomaticCategorizer:
    """Automatic categorization system"""
    
    def __init__(self, config: Dict[str, Any] = None):
        """Initialize automatic categorizer with configuration"""
        self.config = config or {}
        self.model_enabled = self.config.get('model_enabled', True)
        self.rule_enabled = self.config.get('rule_enabled', True)
        self.hybrid_enabled = self.config.get('hybrid_enabled', True)
        self.auto_learning_enabled = self.config.get('auto_learning_enabled', True)
        
        # Model configuration
        self.model_type = self.config.get('model_type', 'logistic_regression')
        self.model_path = self.config.get('model_path', 'models/categorization_model.pkl')
        self.vectorizer_path = self.config.get('vectorizer_path', 'models/vectorizer.pkl')
        self.min_confidence = self.config.get('min_confidence', 0.6)
        self.max_categories = self.config.get('max_categories', 5)
        
        # Rule configuration
        self.rule_weight = self.config.get('rule_weight', 0.3)
        self.model_weight = self.config.get('model_weight', 0.7)
        
        # Learning configuration
        self.learning_threshold = self.config.get('learning_threshold', 0.8)
        self.retrain_interval = self.config.get('retrain_interval', 100)  # documents
        self.validation_split = self.config.get('validation_split', 0.2)
        
        # Initialize components
        self._initialize_components()
        
        logger.info("Automatic Categorizer initialized with configuration")
    
    def _initialize_components(self):
        """Initialize categorization components"""
        try:
            # Create models directory
            Path(self.model_path).parent.mkdir(parents=True, exist_ok=True)
            
            # Initialize vectorizer
            self.vectorizer = TfidfVectorizer(
                max_features=5000,
                stop_words='english',
                ngram_range=(1, 3),
                min_df=2,
                max_df=0.95
            )
            
            # Initialize model
            self.model = self._create_model()
            
            # Load existing model if available
            self._load_model()
            
            # Initialize category rules
            self.category_rules = self._initialize_category_rules()
            
            # Initialize learning data
            self.learning_data = []
            self.learning_labels = []
            
            logger.info("Categorization components initialized")
            
        except Exception as e:
            logger.error(f"Error initializing components: {e}")
            raise
    
    def _create_model(self):
        """Create classification model based on configuration"""
        if self.model_type == 'naive_bayes':
            return MultinomialNB()
        elif self.model_type == 'logistic_regression':
            return LogisticRegression(random_state=42, max_iter=1000)
        elif self.model_type == 'random_forest':
            return RandomForestClassifier(random_state=42, n_estimators=100)
        else:
            return LogisticRegression(random_state=42, max_iter=1000)
    
    def _load_model(self):
        """Load existing model and vectorizer"""
        try:
            model_file = Path(self.model_path)
            vectorizer_file = Path(self.vectorizer_path)
            
            if model_file.exists() and vectorizer_file.exists():
                self.model = joblib.load(model_file)
                self.vectorizer = joblib.load(vectorizer_file)
                logger.info(f"Loaded existing model from {self.model_path}")
            else:
                logger.info("No existing model found, will train new model")
                
        except Exception as e:
            logger.warning(f"Error loading model: {e}")
    
    def _initialize_category_rules(self) -> List[CategoryRule]:
        """Initialize category rules for rule-based classification"""
        rules = [
            # Troubleshooting
            CategoryRule(
                category='troubleshooting',
                keywords=['error', 'problem', 'issue', 'troubleshoot', 'fix', 'solution', 'debug', 'bug', 'fail', 'crash'],
                patterns=[r'error\s+\d+', r'problem\s+with', r'issue\s+in', r'fix\s+for', r'solution\s+to'],
                weight=1.0,
                required_keywords=[],
                excluded_keywords=['installation', 'configuration'],
                min_confidence=0.7
            ),
            
            # Installation
            CategoryRule(
                category='installation',
                keywords=['install', 'setup', 'deploy', 'deployment', 'setup', 'initialize', 'configure'],
                patterns=[r'install\s+\w+', r'setup\s+\w+', r'deploy\s+\w+', r'configure\s+\w+'],
                weight=1.0,
                required_keywords=[],
                excluded_keywords=['troubleshooting', 'maintenance'],
                min_confidence=0.7
            ),
            
            # Configuration
            CategoryRule(
                category='configuration',
                keywords=['config', 'setting', 'parameter', 'option', 'preference', 'customize', 'adjust'],
                patterns=[r'config\s+\w+', r'setting\s+\w+', r'parameter\s+\w+', r'option\s+\w+'],
                weight=1.0,
                required_keywords=[],
                excluded_keywords=['installation', 'troubleshooting'],
                min_confidence=0.7
            ),
            
            # Maintenance
            CategoryRule(
                category='maintenance',
                keywords=['maintain', 'update', 'upgrade', 'backup', 'restore', 'migration', 'cleanup'],
                patterns=[r'update\s+\w+', r'upgrade\s+\w+', r'backup\s+\w+', r'restore\s+\w+'],
                weight=1.0,
                required_keywords=[],
                excluded_keywords=['installation', 'troubleshooting'],
                min_confidence=0.7
            ),
            
            # User Guide
            CategoryRule(
                category='user_guide',
                keywords=['guide', 'tutorial', 'how to', 'step by step', 'manual', 'instruction', 'walkthrough'],
                patterns=[r'how\s+to\s+\w+', r'step\s+by\s+step', r'guide\s+to\s+\w+', r'tutorial\s+for'],
                weight=1.0,
                required_keywords=[],
                excluded_keywords=['troubleshooting', 'installation'],
                min_confidence=0.7
            ),
            
            # Technical Specification
            CategoryRule(
                category='technical_specification',
                keywords=['spec', 'requirement', 'specification', 'standard', 'protocol', 'interface'],
                patterns=[r'spec\s+\w+', r'requirement\s+\w+', r'specification\s+\w+', r'standard\s+\w+'],
                weight=1.0,
                required_keywords=[],
                excluded_keywords=['troubleshooting', 'user_guide'],
                min_confidence=0.7
            ),
            
            # Release Notes
            CategoryRule(
                category='release_notes',
                keywords=['release', 'version', 'changelog', 'new feature', 'update', 'patch'],
                patterns=[r'release\s+\d+', r'version\s+\d+', r'changelog\s+\w+', r'new\s+feature'],
                weight=1.0,
                required_keywords=[],
                excluded_keywords=['troubleshooting', 'installation'],
                min_confidence=0.7
            ),
            
            # FAQ
            CategoryRule(
                category='faq',
                keywords=['faq', 'frequently asked', 'question', 'answer', 'q&a', 'common'],
                patterns=[r'faq\s+\w+', r'frequently\s+asked', r'question\s+\d+', r'answer\s+\d+'],
                weight=1.0,
                required_keywords=[],
                excluded_keywords=['troubleshooting', 'installation'],
                min_confidence=0.7
            ),
            
            # API Documentation
            CategoryRule(
                category='api_documentation',
                keywords=['api', 'endpoint', 'service', 'rest', 'soap', 'interface', 'method'],
                patterns=[r'api\s+\w+', r'endpoint\s+\w+', r'service\s+\w+', r'interface\s+\w+'],
                weight=1.0,
                required_keywords=[],
                excluded_keywords=['troubleshooting', 'user_guide'],
                min_confidence=0.7
            ),
            
            # Security
            CategoryRule(
                category='security',
                keywords=['security', 'authentication', 'authorization', 'encryption', 'password', 'ssl', 'tls'],
                patterns=[r'security\s+\w+', r'authentication\s+\w+', r'authorization\s+\w+', r'encryption\s+\w+'],
                weight=1.0,
                required_keywords=[],
                excluded_keywords=['troubleshooting', 'installation'],
                min_confidence=0.7
            )
        ]
        
        return rules
    
    def categorize(self, content: str, content_type: str = 'text') -> List[CategoryResult]:
        """Categorize content using hybrid approach"""
        try:
            logger.info(f"Starting categorization for {content_type} content")
            
            results = []
            
            # Rule-based categorization
            if self.rule_enabled:
                rule_results = self._categorize_by_rules(content)
                results.extend(rule_results)
            
            # Model-based categorization
            if self.model_enabled and self._is_model_trained():
                model_results = self._categorize_by_model(content)
                results.extend(model_results)
            
            # Hybrid approach
            if self.hybrid_enabled and len(results) > 1:
                results = self._combine_results(results)
            
            # Sort by confidence and limit results
            results.sort(key=lambda x: x.confidence, reverse=True)
            results = results[:self.max_categories]
            
            # Filter by minimum confidence
            results = [r for r in results if r.confidence >= self.min_confidence]
            
            logger.info(f"Categorization completed with {len(results)} categories")
            return results
            
        except Exception as e:
            logger.error(f"Error categorizing content: {e}")
            return []
    
    def _categorize_by_rules(self, content: str) -> List[CategoryResult]:
        """Categorize content using rule-based approach"""
        try:
            results = []
            content_lower = content.lower()
            
            for rule in self.category_rules:
                confidence = 0.0
                matched_keywords = []
                matched_patterns = []
                
                # Check required keywords
                if rule.required_keywords:
                    if not all(keyword in content_lower for keyword in rule.required_keywords):
                        continue
                
                # Check excluded keywords
                if rule.excluded_keywords:
                    if any(keyword in content_lower for keyword in rule.excluded_keywords):
                        continue
                
                # Check keywords
                for keyword in rule.keywords:
                    if keyword in content_lower:
                        matched_keywords.append(keyword)
                        confidence += rule.weight * 0.1
                
                # Check patterns
                for pattern in rule.patterns:
                    matches = re.findall(pattern, content_lower)
                    if matches:
                        matched_patterns.extend(matches)
                        confidence += rule.weight * 0.2
                
                # Normalize confidence
                confidence = min(confidence, 1.0)
                
                if confidence >= rule.min_confidence:
                    results.append(CategoryResult(
                        category=rule.category,
                        confidence=confidence,
                        reasoning=f"Matched {len(matched_keywords)} keywords and {len(matched_patterns)} patterns",
                        matched_keywords=matched_keywords,
                        matched_patterns=matched_patterns,
                        rule_type='rule_based'
                    ))
            
            return results
            
        except Exception as e:
            logger.error(f"Error in rule-based categorization: {e}")
            return []
    
    def _categorize_by_model(self, content: str) -> List[CategoryResult]:
        """Categorize content using machine learning model"""
        try:
            if not self._is_model_trained():
                return []
            
            # Vectorize content
            content_vector = self.vectorizer.transform([content])
            
            # Get predictions
            predictions = self.model.predict_proba(content_vector)[0]
            categories = self.model.classes_
            
            results = []
            for i, confidence in enumerate(predictions):
                if confidence >= self.min_confidence:
                    results.append(CategoryResult(
                        category=categories[i],
                        confidence=confidence,
                        reasoning=f"Model prediction with {confidence:.3f} confidence",
                        matched_keywords=[],
                        matched_patterns=[],
                        rule_type='model_based'
                    ))
            
            return results
            
        except Exception as e:
            logger.error(f"Error in model-based categorization: {e}")
            return []
    
    def _combine_results(self, results: List[CategoryResult]) -> List[CategoryResult]:
        """Combine results from different approaches"""
        try:
            # Group results by category
            category_groups = {}
            for result in results:
                if result.category not in category_groups:
                    category_groups[result.category] = []
                category_groups[result.category].append(result)
            
            # Combine results for each category
            combined_results = []
            for category, category_results in category_groups.items():
                # Calculate weighted average confidence
                total_confidence = 0.0
                total_weight = 0.0
                all_keywords = []
                all_patterns = []
                reasoning_parts = []
                
                for result in category_results:
                    if result.rule_type == 'rule_based':
                        weight = self.rule_weight
                    else:
                        weight = self.model_weight
                    
                    total_confidence += result.confidence * weight
                    total_weight += weight
                    all_keywords.extend(result.matched_keywords)
                    all_patterns.extend(result.matched_patterns)
                    reasoning_parts.append(result.reasoning)
                
                if total_weight > 0:
                    combined_confidence = total_confidence / total_weight
                    combined_results.append(CategoryResult(
                        category=category,
                        confidence=combined_confidence,
                        reasoning='; '.join(reasoning_parts),
                        matched_keywords=list(set(all_keywords)),
                        matched_patterns=list(set(all_patterns)),
                        rule_type='hybrid'
                    ))
            
            return combined_results
            
        except Exception as e:
            logger.error(f"Error combining results: {e}")
            return results
    
    def train_model(self, training_data: List[Tuple[str, str]]) -> Dict[str, Any]:
        """Train the categorization model"""
        try:
            logger.info(f"Training model with {len(training_data)} samples")
            
            # Prepare data
            texts = [item[0] for item in training_data]
            labels = [item[1] for item in training_data]
            
            # Split data
            X_train, X_test, y_train, y_test = train_test_split(
                texts, labels, test_size=self.validation_split, random_state=42
            )
            
            # Vectorize texts
            X_train_vectorized = self.vectorizer.fit_transform(X_train)
            X_test_vectorized = self.vectorizer.transform(X_test)
            
            # Train model
            self.model.fit(X_train_vectorized, y_train)
            
            # Evaluate model
            y_pred = self.model.predict(X_test_vectorized)
            accuracy = accuracy_score(y_test, y_pred)
            
            # Generate classification report
            report = classification_report(y_test, y_pred, output_dict=True)
            
            # Save model and vectorizer
            self._save_model()
            
            # Update learning data
            self.learning_data.extend(texts)
            self.learning_labels.extend(labels)
            
            result = {
                'success': True,
                'accuracy': accuracy,
                'classification_report': report,
                'training_samples': len(training_data),
                'test_samples': len(X_test),
                'categories': list(set(labels)),
                'model_type': self.model_type
            }
            
            logger.info(f"Model training completed with accuracy: {accuracy:.3f}")
            return result
            
        except Exception as e:
            logger.error(f"Error training model: {e}")
            return {'success': False, 'error': str(e)}
    
    def add_training_sample(self, content: str, category: str, confidence: float = 1.0):
        """Add a training sample for continuous learning"""
        try:
            if not self.auto_learning_enabled:
                return
            
            # Add to learning data
            self.learning_data.append(content)
            self.learning_labels.append(category)
            
            # Check if retraining is needed
            if len(self.learning_data) >= self.retrain_interval:
                self._retrain_model()
            
            logger.info(f"Added training sample for category: {category}")
            
        except Exception as e:
            logger.error(f"Error adding training sample: {e}")
    
    def _retrain_model(self):
        """Retrain model with accumulated learning data"""
        try:
            if len(self.learning_data) < 10:  # Minimum samples for retraining
                return
            
            logger.info(f"Retraining model with {len(self.learning_data)} samples")
            
            # Prepare training data
            training_data = list(zip(self.learning_data, self.learning_labels))
            
            # Train model
            result = self.train_model(training_data)
            
            if result['success']:
                # Clear learning data
                self.learning_data = []
                self.learning_labels = []
                logger.info("Model retraining completed successfully")
            else:
                logger.error(f"Model retraining failed: {result.get('error', 'Unknown error')}")
            
        except Exception as e:
            logger.error(f"Error retraining model: {e}")
    
    def _is_model_trained(self) -> bool:
        """Check if model is trained"""
        try:
            return hasattr(self.model, 'classes_') and len(self.model.classes_) > 0
        except:
            return False
    
    def _save_model(self):
        """Save model and vectorizer"""
        try:
            joblib.dump(self.model, self.model_path)
            joblib.dump(self.vectorizer, self.vectorizer_path)
            logger.info(f"Model saved to {self.model_path}")
        except Exception as e:
            logger.error(f"Error saving model: {e}")
    
    def get_category_statistics(self) -> Dict[str, Any]:
        """Get category statistics"""
        try:
            stats = {
                'total_categories': len(self.category_rules),
                'model_trained': self._is_model_trained(),
                'learning_samples': len(self.learning_data),
                'categories': [rule.category for rule in self.category_rules],
                'model_type': self.model_type,
                'hybrid_enabled': self.hybrid_enabled,
                'auto_learning_enabled': self.auto_learning_enabled
            }
            
            if self._is_model_trained():
                stats['model_categories'] = list(self.model.classes_)
                stats['model_features'] = len(self.vectorizer.get_feature_names_out())
            
            return stats
            
        except Exception as e:
            logger.error(f"Error getting category statistics: {e}")
            return {}
    
    def update_category_rule(self, category: str, rule: CategoryRule):
        """Update category rule"""
        try:
            # Find existing rule
            for i, existing_rule in enumerate(self.category_rules):
                if existing_rule.category == category:
                    self.category_rules[i] = rule
                    logger.info(f"Updated rule for category: {category}")
                    return
            
            # Add new rule
            self.category_rules.append(rule)
            logger.info(f"Added new rule for category: {category}")
            
        except Exception as e:
            logger.error(f"Error updating category rule: {e}")
    
    def remove_category_rule(self, category: str):
        """Remove category rule"""
        try:
            self.category_rules = [rule for rule in self.category_rules if rule.category != category]
            logger.info(f"Removed rule for category: {category}")
        except Exception as e:
            logger.error(f"Error removing category rule: {e}")
    
    def export_model(self, export_path: str) -> bool:
        """Export model to specified path"""
        try:
            if not self._is_model_trained():
                return False
            
            # Create export directory
            Path(export_path).parent.mkdir(parents=True, exist_ok=True)
            
            # Export model
            joblib.dump(self.model, f"{export_path}_model.pkl")
            joblib.dump(self.vectorizer, f"{export_path}_vectorizer.pkl")
            
            # Export rules
            rules_data = {
                'rules': [
                    {
                        'category': rule.category,
                        'keywords': rule.keywords,
                        'patterns': rule.patterns,
                        'weight': rule.weight,
                        'required_keywords': rule.required_keywords,
                        'excluded_keywords': rule.excluded_keywords,
                        'min_confidence': rule.min_confidence
                    }
                    for rule in self.category_rules
                ]
            }
            
            with open(f"{export_path}_rules.json", 'w') as f:
                json.dump(rules_data, f, indent=2)
            
            logger.info(f"Model exported to {export_path}")
            return True
            
        except Exception as e:
            logger.error(f"Error exporting model: {e}")
            return False
    
    def import_model(self, import_path: str) -> bool:
        """Import model from specified path"""
        try:
            # Import model
            model_file = f"{import_path}_model.pkl"
            vectorizer_file = f"{import_path}_vectorizer.pkl"
            rules_file = f"{import_path}_rules.json"
            
            if not all(Path(f).exists() for f in [model_file, vectorizer_file, rules_file]):
                return False
            
            # Load model and vectorizer
            self.model = joblib.load(model_file)
            self.vectorizer = joblib.load(vectorizer_file)
            
            # Load rules
            with open(rules_file, 'r') as f:
                rules_data = json.load(f)
            
            self.category_rules = [
                CategoryRule(
                    category=rule['category'],
                    keywords=rule['keywords'],
                    patterns=rule['patterns'],
                    weight=rule['weight'],
                    required_keywords=rule['required_keywords'],
                    excluded_keywords=rule['excluded_keywords'],
                    min_confidence=rule['min_confidence']
                )
                for rule in rules_data['rules']
            ]
            
            logger.info(f"Model imported from {import_path}")
            return True
            
        except Exception as e:
            logger.error(f"Error importing model: {e}")
            return False
    
    def validate_categorization(self, content: str, expected_category: str) -> Dict[str, Any]:
        """Validate categorization accuracy"""
        try:
            results = self.categorize(content)
            
            # Find expected category in results
            expected_result = None
            for result in results:
                if result.category == expected_category:
                    expected_result = result
                    break
            
            validation = {
                'expected_category': expected_category,
                'found': expected_result is not None,
                'confidence': expected_result.confidence if expected_result else 0.0,
                'top_category': results[0].category if results else None,
                'top_confidence': results[0].confidence if results else 0.0,
                'all_results': [
                    {
                        'category': r.category,
                        'confidence': r.confidence,
                        'reasoning': r.reasoning
                    }
                    for r in results
                ]
            }
            
            return validation
            
        except Exception as e:
            logger.error(f"Error validating categorization: {e}")
            return {}
    
    def get_category_suggestions(self, content: str) -> List[str]:
        """Get category suggestions based on content analysis"""
        try:
            suggestions = []
            content_lower = content.lower()
            
            # Analyze content for category hints
            for rule in self.category_rules:
                # Check if content matches rule keywords
                keyword_matches = sum(1 for keyword in rule.keywords if keyword in content_lower)
                pattern_matches = sum(1 for pattern in rule.patterns if re.search(pattern, content_lower))
                
                if keyword_matches > 0 or pattern_matches > 0:
                    suggestions.append(rule.category)
            
            # Remove duplicates and return
            return list(set(suggestions))
            
        except Exception as e:
            logger.error(f"Error getting category suggestions: {e}")
            return []
    
    def batch_categorize(self, contents: List[str]) -> List[List[CategoryResult]]:
        """Categorize multiple contents in batch"""
        try:
            results = []
            for content in contents:
                result = self.categorize(content)
                results.append(result)
            
            return results
            
        except Exception as e:
            logger.error(f"Error in batch categorization: {e}")
            return []
    
    def get_categorization_report(self, contents: List[str], expected_categories: List[str] = None) -> Dict[str, Any]:
        """Generate categorization report"""
        try:
            results = self.batch_categorize(contents)
            
            report = {
                'total_contents': len(contents),
                'categorization_results': [],
                'category_distribution': {},
                'confidence_statistics': {
                    'min': 0.0,
                    'max': 0.0,
                    'avg': 0.0,
                    'median': 0.0
                }
            }
            
            # Process results
            confidences = []
            for i, result in enumerate(results):
                content_report = {
                    'index': i,
                    'categories': [
                        {
                            'category': r.category,
                            'confidence': r.confidence,
                            'reasoning': r.reasoning
                        }
                        for r in result
                    ],
                    'top_category': result[0].category if result else None,
                    'top_confidence': result[0].confidence if result else 0.0
                }
                
                if expected_categories and i < len(expected_categories):
                    content_report['expected_category'] = expected_categories[i]
                    content_report['correct'] = (
                        result[0].category == expected_categories[i] if result else False
                    )
                
                report['categorization_results'].append(content_report)
                
                # Update category distribution
                if result:
                    top_category = result[0].category
                    report['category_distribution'][top_category] = report['category_distribution'].get(top_category, 0) + 1
                
                # Collect confidences
                if result:
                    confidences.append(result[0].confidence)
            
            # Calculate confidence statistics
            if confidences:
                confidences.sort()
                report['confidence_statistics'] = {
                    'min': confidences[0],
                    'max': confidences[-1],
                    'avg': sum(confidences) / len(confidences),
                    'median': confidences[len(confidences) // 2]
                }
            
            return report
            
        except Exception as e:
            logger.error(f"Error generating categorization report: {e}")
            return {}
