"""
AI Content Analysis and Classification

This module provides comprehensive AI-powered content analysis and classification
capabilities including sentiment analysis, topic modeling, and content quality assessment.
"""

import logging
import json
import re
from typing import Dict, Any, List, Optional, Tuple, Set
from dataclasses import dataclass
from datetime import datetime
import hashlib
import numpy as np
from sklearn.feature_extraction.text import TfidfVectorizer, CountVectorizer
from sklearn.decomposition import LatentDirichletAllocation, NMF
from sklearn.cluster import KMeans
from sklearn.metrics.pairwise import cosine_similarity
from transformers import pipeline, AutoTokenizer, AutoModel
import spacy
from textblob import TextBlob
import nltk
from nltk.corpus import stopwords
from nltk.tokenize import word_tokenize, sent_tokenize
from nltk.stem import WordNetLemmatizer
import matplotlib.pyplot as plt
import seaborn as sns
from wordcloud import WordCloud
import plotly.graph_objects as go
import plotly.express as px

logger = logging.getLogger(__name__)


@dataclass
class ContentAnalysisResult:
    """Content analysis result structure"""
    content_id: str
    analysis_type: str
    sentiment: Dict[str, float]
    topics: List[Dict[str, Any]]
    entities: List[Dict[str, Any]]
    keywords: List[str]
    language: str
    readability_score: float
    complexity_score: float
    quality_score: float
    technical_level: str
    content_type: str
    target_audience: str
    confidence: float
    processing_time: float
    metadata: Dict[str, Any]


@dataclass
class TopicModel:
    """Topic model structure"""
    topic_id: int
    topic_words: List[Tuple[str, float]]
    topic_weight: float
    topic_name: str
    topic_description: str


@dataclass
class EntityAnalysis:
    """Entity analysis structure"""
    entity_text: str
    entity_type: str
    start_pos: int
    end_pos: int
    confidence: float
    context: str
    relationships: List[str]


@dataclass
class ContentQualityMetrics:
    """Content quality metrics structure"""
    coherence_score: float
    completeness_score: float
    accuracy_score: float
    relevance_score: float
    clarity_score: float
    structure_score: float
    overall_score: float


class AIContentAnalyzer:
    """AI-powered content analyzer and classifier"""
    
    def __init__(self, config: Dict[str, Any] = None):
        """Initialize AI content analyzer with configuration"""
        self.config = config or {}
        self.sentiment_analysis_enabled = self.config.get('sentiment_analysis_enabled', True)
        self.topic_modeling_enabled = self.config.get('topic_modeling_enabled', True)
        self.entity_extraction_enabled = self.config.get('entity_extraction_enabled', True)
        self.quality_assessment_enabled = self.config.get('quality_assessment_enabled', True)
        self.classification_enabled = self.config.get('classification_enabled', True)
        self.visualization_enabled = self.config.get('visualization_enabled', True)
        
        # Sentiment analysis configuration
        self.sentiment_model = self.config.get('sentiment_model', 'cardiffnlp/twitter-roberta-base-sentiment-latest')
        self.sentiment_confidence_threshold = self.config.get('sentiment_confidence_threshold', 0.5)
        
        # Topic modeling configuration
        self.topic_model_type = self.config.get('topic_model_type', 'lda')
        self.num_topics = self.config.get('num_topics', 10)
        self.max_features = self.config.get('max_features', 1000)
        self.min_df = self.config.get('min_df', 2)
        self.max_df = self.config.get('max_df', 0.95)
        
        # Entity extraction configuration
        self.ner_model = self.config.get('ner_model', 'en_core_web_sm')
        self.entity_types = self.config.get('entity_types', [
            'PERSON', 'ORG', 'GPE', 'PRODUCT', 'SOFTWARE', 'HARDWARE', 
            'VERSION', 'ERROR_CODE', 'COMMAND', 'FILE_PATH', 'URL', 'EMAIL'
        ])
        
        # Quality assessment configuration
        self.quality_weights = self.config.get('quality_weights', {
            'coherence': 0.2,
            'completeness': 0.2,
            'accuracy': 0.2,
            'relevance': 0.2,
            'clarity': 0.1,
            'structure': 0.1
        })
        
        # Classification configuration
        self.classification_model = self.config.get('classification_model', 'microsoft/DialoGPT-medium')
        self.classification_categories = self.config.get('classification_categories', [
            'troubleshooting', 'installation', 'configuration', 'maintenance',
            'user_guide', 'technical_specification', 'release_notes', 'faq',
            'api_documentation', 'security', 'performance', 'integration'
        ])
        
        # Visualization configuration
        self.visualization_format = self.config.get('visualization_format', 'plotly')
        self.wordcloud_enabled = self.config.get('wordcloud_enabled', True)
        self.topic_visualization_enabled = self.config.get('topic_visualization_enabled', True)
        
        # Initialize components
        self._initialize_components()
        
        logger.info("AI Content Analyzer initialized with configuration")
    
    def _initialize_components(self):
        """Initialize AI analysis components"""
        try:
            # Initialize sentiment analysis
            if self.sentiment_analysis_enabled:
                self.sentiment_pipeline = pipeline(
                    "sentiment-analysis",
                    model=self.sentiment_model,
                    return_all_scores=True
                )
                logger.info(f"Sentiment analysis model '{self.sentiment_model}' loaded")
            
            # Initialize NER model
            if self.entity_extraction_enabled:
                try:
                    self.nlp = spacy.load(self.ner_model)
                    logger.info(f"NER model '{self.ner_model}' loaded")
                except OSError:
                    logger.warning(f"NER model '{self.ner_model}' not found, using basic NER")
                    self.nlp = None
            
            # Initialize topic modeling
            if self.topic_modeling_enabled:
                self.tfidf_vectorizer = TfidfVectorizer(
                    max_features=self.max_features,
                    stop_words='english',
                    ngram_range=(1, 2),
                    min_df=self.min_df,
                    max_df=self.max_df
                )
                
                if self.topic_model_type == 'lda':
                    self.topic_model = LatentDirichletAllocation(
                        n_components=self.num_topics,
                        random_state=42,
                        max_iter=100
                    )
                elif self.topic_model_type == 'nmf':
                    self.topic_model = NMF(
                        n_components=self.num_topics,
                        random_state=42,
                        max_iter=100
                    )
                else:
                    self.topic_model = LatentDirichletAllocation(
                        n_components=self.num_topics,
                        random_state=42,
                        max_iter=100
                    )
                
                logger.info(f"Topic modeling components initialized with {self.topic_model_type}")
            
            # Initialize classification
            if self.classification_enabled:
                self.classification_pipeline = pipeline(
                    "text-classification",
                    model=self.classification_model,
                    return_all_scores=True
                )
                logger.info(f"Classification model '{self.classification_model}' loaded")
            
            # Initialize NLTK components
            try:
                nltk.download('punkt', quiet=True)
                nltk.download('stopwords', quiet=True)
                nltk.download('averaged_perceptron_tagger', quiet=True)
                nltk.download('wordnet', quiet=True)
                self.stop_words = set(stopwords.words('english'))
                self.lemmatizer = WordNetLemmatizer()
            except:
                self.stop_words = set()
                self.lemmatizer = None
            
            # Initialize visualization
            if self.visualization_enabled:
                plt.style.use('default')
                sns.set_palette("husl")
                logger.info("Visualization components initialized")
            
        except Exception as e:
            logger.error(f"Error initializing components: {e}")
            raise
    
    def analyze_content(self, content: str, content_id: str = None, analysis_type: str = 'comprehensive') -> ContentAnalysisResult:
        """Analyze content using AI-powered methods"""
        start_time = datetime.now()
        
        try:
            if not content_id:
                content_id = hashlib.md5(content.encode()).hexdigest()
            
            logger.info(f"Starting AI content analysis for {content_id}")
            
            # Analyze sentiment
            sentiment = self._analyze_sentiment(content) if self.sentiment_analysis_enabled else {'positive': 0.0, 'negative': 0.0, 'neutral': 0.0}
            
            # Extract topics
            topics = self._extract_topics(content) if self.topic_modeling_enabled else []
            
            # Extract entities
            entities = self._extract_entities(content) if self.entity_extraction_enabled else []
            
            # Extract keywords
            keywords = self._extract_keywords(content)
            
            # Detect language
            language = self._detect_language(content)
            
            # Calculate readability score
            readability_score = self._calculate_readability_score(content)
            
            # Calculate complexity score
            complexity_score = self._calculate_complexity_score(content)
            
            # Assess content quality
            quality_metrics = self._assess_content_quality(content) if self.quality_assessment_enabled else ContentQualityMetrics(0.5, 0.5, 0.5, 0.5, 0.5, 0.5, 0.5)
            
            # Determine technical level
            technical_level = self._determine_technical_level(content, complexity_score)
            
            # Determine content type
            content_type = self._determine_content_type(content)
            
            # Determine target audience
            target_audience = self._determine_target_audience(content)
            
            # Calculate overall confidence
            confidence = self._calculate_analysis_confidence(sentiment, topics, entities, keywords)
            
            # Calculate processing time
            processing_time = (datetime.now() - start_time).total_seconds()
            
            # Create analysis result
            result = ContentAnalysisResult(
                content_id=content_id,
                analysis_type=analysis_type,
                sentiment=sentiment,
                topics=topics,
                entities=entities,
                keywords=keywords,
                language=language,
                readability_score=readability_score,
                complexity_score=complexity_score,
                quality_score=quality_metrics.overall_score,
                technical_level=technical_level,
                content_type=content_type,
                target_audience=target_audience,
                confidence=confidence,
                processing_time=processing_time,
                metadata={
                    'quality_metrics': {
                        'coherence': quality_metrics.coherence_score,
                        'completeness': quality_metrics.completeness_score,
                        'accuracy': quality_metrics.accuracy_score,
                        'relevance': quality_metrics.relevance_score,
                        'clarity': quality_metrics.clarity_score,
                        'structure': quality_metrics.structure_score
                    },
                    'text_length': len(content),
                    'word_count': len(content.split()),
                    'sentence_count': len(sent_tokenize(content)),
                    'paragraph_count': len([p for p in content.split('\n\n') if p.strip()])
                }
            )
            
            logger.info(f"AI content analysis completed in {processing_time:.2f} seconds")
            return result
            
        except Exception as e:
            logger.error(f"Error analyzing content: {e}")
            raise
    
    def _analyze_sentiment(self, content: str) -> Dict[str, float]:
        """Analyze sentiment of content"""
        try:
            if not self.sentiment_analysis_enabled:
                return {'positive': 0.0, 'negative': 0.0, 'neutral': 0.0}
            
            # Split content into chunks if too long
            max_length = 512
            if len(content) > max_length:
                chunks = [content[i:i+max_length] for i in range(0, len(content), max_length)]
            else:
                chunks = [content]
            
            # Analyze each chunk
            sentiment_scores = []
            for chunk in chunks:
                try:
                    result = self.sentiment_pipeline(chunk)
                    sentiment_scores.append(result)
                except Exception as e:
                    logger.warning(f"Sentiment analysis failed for chunk: {e}")
                    continue
            
            # Aggregate sentiment scores
            if not sentiment_scores:
                return {'positive': 0.0, 'negative': 0.0, 'neutral': 0.0}
            
            # Calculate average sentiment
            avg_sentiment = {'positive': 0.0, 'negative': 0.0, 'neutral': 0.0}
            
            for chunk_scores in sentiment_scores:
                for score_item in chunk_scores:
                    label = score_item['label'].lower()
                    score = score_item['score']
                    
                    if 'positive' in label:
                        avg_sentiment['positive'] += score
                    elif 'negative' in label:
                        avg_sentiment['negative'] += score
                    elif 'neutral' in label:
                        avg_sentiment['neutral'] += score
            
            # Normalize scores
            total_chunks = len(sentiment_scores)
            for key in avg_sentiment:
                avg_sentiment[key] /= total_chunks
            
            return avg_sentiment
            
        except Exception as e:
            logger.error(f"Error analyzing sentiment: {e}")
            return {'positive': 0.0, 'negative': 0.0, 'neutral': 0.0}
    
    def _extract_topics(self, content: str) -> List[Dict[str, Any]]:
        """Extract topics from content using topic modeling"""
        try:
            if not self.topic_modeling_enabled:
                return []
            
            # Prepare text for topic modeling
            sentences = sent_tokenize(content)
            sentences = [s.strip() for s in sentences if s.strip() and len(s) > 10]
            
            if len(sentences) < 3:
                return []
            
            # Vectorize text
            tfidf_matrix = self.tfidf_vectorizer.fit_transform(sentences)
            
            # Fit topic model
            topic_model = self.topic_model
            topic_model.fit(tfidf_matrix)
            
            # Get topic-word distributions
            feature_names = self.tfidf_vectorizer.get_feature_names_out()
            topics = []
            
            for topic_idx, topic in enumerate(topic_model.components_):
                # Get top words for this topic
                top_words = [(feature_names[i], topic[i]) for i in topic.argsort()[-10:][::-1]]
                
                # Calculate topic weight
                topic_weight = np.mean(topic_model.transform(tfidf_matrix)[:, topic_idx])
                
                # Generate topic name and description
                topic_name = f"Topic_{topic_idx + 1}"
                topic_description = f"Topic related to {', '.join([word for word, _ in top_words[:3]])}"
                
                topics.append({
                    'topic_id': topic_idx,
                    'topic_name': topic_name,
                    'topic_description': topic_description,
                    'topic_words': top_words,
                    'topic_weight': topic_weight,
                    'top_words': [word for word, _ in top_words[:5]]
                })
            
            return topics
            
        except Exception as e:
            logger.error(f"Error extracting topics: {e}")
            return []
    
    def _extract_entities(self, content: str) -> List[Dict[str, Any]]:
        """Extract entities from content using NER"""
        try:
            if not self.entity_extraction_enabled:
                return []
            
            entities = []
            
            # Use spaCy NER if available
            if self.nlp:
                try:
                    doc = self.nlp(content)
                    for ent in doc.ents:
                        if ent.label_ in self.entity_types:
                            entities.append({
                                'entity_text': ent.text,
                                'entity_type': ent.label_,
                                'start_pos': ent.start_char,
                                'end_pos': ent.end_char,
                                'confidence': ent.confidence if hasattr(ent, 'confidence') else 0.8,
                                'context': self._get_entity_context(content, ent.start_char, ent.end_char),
                                'relationships': []
                            })
                except Exception as e:
                    logger.warning(f"spaCy NER failed: {e}")
            
            # Add rule-based entity extraction
            rule_based_entities = self._extract_rule_based_entities(content)
            entities.extend(rule_based_entities)
            
            # Remove duplicates
            unique_entities = []
            seen_entities = set()
            
            for entity in entities:
                entity_key = (entity['entity_text'], entity['entity_type'])
                if entity_key not in seen_entities:
                    unique_entities.append(entity)
                    seen_entities.add(entity_key)
            
            return unique_entities[:20]  # Limit to 20 entities
            
        except Exception as e:
            logger.error(f"Error extracting entities: {e}")
            return []
    
    def _extract_keywords(self, content: str) -> List[str]:
        """Extract keywords from content"""
        try:
            # Tokenize and clean text
            words = word_tokenize(content.lower())
            words = [word for word in words if word.isalpha() and word not in self.stop_words]
            
            # Use TF-IDF for keyword extraction
            if self.topic_modeling_enabled:
                try:
                    tfidf_matrix = self.tfidf_vectorizer.fit_transform([content])
                    feature_names = self.tfidf_vectorizer.get_feature_names_out()
                    
                    # Get top keywords
                    scores = tfidf_matrix.toarray()[0]
                    top_indices = np.argsort(scores)[-20:][::-1]  # Top 20 keywords
                    
                    keywords = [feature_names[i] for i in top_indices if scores[i] > 0.1]
                    
                    return keywords
                except Exception as e:
                    logger.warning(f"TF-IDF keyword extraction failed: {e}")
            
            # Fallback: use frequency-based extraction
            word_freq = {}
            for word in words:
                if len(word) > 3:  # Only consider words longer than 3 characters
                    word_freq[word] = word_freq.get(word, 0) + 1
            
            # Sort by frequency and return top keywords
            sorted_words = sorted(word_freq.items(), key=lambda x: x[1], reverse=True)
            keywords = [word for word, freq in sorted_words[:20] if freq > 1]
            
            return keywords
            
        except Exception as e:
            logger.error(f"Error extracting keywords: {e}")
            return []
    
    def _detect_language(self, content: str) -> str:
        """Detect language of content"""
        try:
            blob = TextBlob(content)
            return blob.detect_language()
        except:
            return 'en'  # Default to English
    
    def _calculate_readability_score(self, content: str) -> float:
        """Calculate readability score using Flesch Reading Ease"""
        try:
            sentences = sent_tokenize(content)
            words = word_tokenize(content)
            
            if not sentences or not words:
                return 0.5
            
            # Calculate average sentence length
            avg_sentence_length = len(words) / len(sentences)
            
            # Calculate average syllables per word (simplified)
            syllables = 0
            for word in words:
                syllables += self._count_syllables(word)
            
            avg_syllables = syllables / len(words)
            
            # Flesch Reading Ease formula
            score = 206.835 - (1.015 * avg_sentence_length) - (84.6 * avg_syllables)
            
            # Normalize to 0-1 scale
            normalized_score = max(0, min(1, score / 100))
            
            return normalized_score
            
        except Exception as e:
            logger.error(f"Error calculating readability score: {e}")
            return 0.5
    
    def _calculate_complexity_score(self, content: str) -> float:
        """Calculate complexity score for content"""
        try:
            score = 0.0
            
            # Technical terms contribute to complexity
            technical_terms = self._extract_technical_terms(content)
            score += min(len(technical_terms) / 50.0, 0.3)
            
            # Abbreviations contribute to complexity
            abbreviations = self._extract_abbreviations(content)
            score += min(len(abbreviations) / 20.0, 0.2)
            
            # Code snippets contribute to complexity
            code_snippets = self._extract_code_snippets(content)
            score += min(len(code_snippets) / 10.0, 0.2)
            
            # Readability score (inverse)
            readability_score = self._calculate_readability_score(content)
            score += (1.0 - readability_score) * 0.3
            
            return min(score, 1.0)
            
        except Exception as e:
            logger.error(f"Error calculating complexity score: {e}")
            return 0.5
    
    def _assess_content_quality(self, content: str) -> ContentQualityMetrics:
        """Assess content quality using multiple metrics"""
        try:
            # Coherence score (based on sentence flow and transitions)
            coherence_score = self._calculate_coherence_score(content)
            
            # Completeness score (based on content structure and completeness)
            completeness_score = self._calculate_completeness_score(content)
            
            # Accuracy score (based on technical accuracy indicators)
            accuracy_score = self._calculate_accuracy_score(content)
            
            # Relevance score (based on relevance to Agilent products)
            relevance_score = self._calculate_relevance_score(content)
            
            # Clarity score (based on clarity indicators)
            clarity_score = self._calculate_clarity_score(content)
            
            # Structure score (based on content structure)
            structure_score = self._calculate_structure_score(content)
            
            # Calculate overall score
            overall_score = (
                coherence_score * self.quality_weights['coherence'] +
                completeness_score * self.quality_weights['completeness'] +
                accuracy_score * self.quality_weights['accuracy'] +
                relevance_score * self.quality_weights['relevance'] +
                clarity_score * self.quality_weights['clarity'] +
                structure_score * self.quality_weights['structure']
            )
            
            return ContentQualityMetrics(
                coherence_score=coherence_score,
                completeness_score=completeness_score,
                accuracy_score=accuracy_score,
                relevance_score=relevance_score,
                clarity_score=clarity_score,
                structure_score=structure_score,
                overall_score=overall_score
            )
            
        except Exception as e:
            logger.error(f"Error assessing content quality: {e}")
            return ContentQualityMetrics(0.5, 0.5, 0.5, 0.5, 0.5, 0.5, 0.5)
    
    def _determine_technical_level(self, content: str, complexity_score: float) -> str:
        """Determine technical level of content"""
        try:
            if complexity_score > 0.7:
                return 'expert'
            elif complexity_score > 0.4:
                return 'intermediate'
            else:
                return 'beginner'
        except Exception as e:
            logger.error(f"Error determining technical level: {e}")
            return 'intermediate'
    
    def _determine_content_type(self, content: str) -> str:
        """Determine content type"""
        try:
            content_lower = content.lower()
            
            # Check for different content types
            if any(term in content_lower for term in ['error', 'problem', 'issue', 'troubleshoot']):
                return 'troubleshooting'
            elif any(term in content_lower for term in ['install', 'setup', 'deploy']):
                return 'installation'
            elif any(term in content_lower for term in ['config', 'setting', 'parameter']):
                return 'configuration'
            elif any(term in content_lower for term in ['guide', 'tutorial', 'how to']):
                return 'user_guide'
            elif any(term in content_lower for term in ['api', 'endpoint', 'service']):
                return 'api_documentation'
            elif any(term in content_lower for term in ['security', 'authentication', 'authorization']):
                return 'security'
            else:
                return 'general'
                
        except Exception as e:
            logger.error(f"Error determining content type: {e}")
            return 'general'
    
    def _determine_target_audience(self, content: str) -> str:
        """Determine target audience of content"""
        try:
            content_lower = content.lower()
            
            # Check for administrator content
            if any(term in content_lower for term in ['admin', 'administrator', 'install', 'configure']):
                return 'administrator'
            
            # Check for developer content
            if any(term in content_lower for term in ['api', 'sdk', 'develop', 'programming']):
                return 'developer'
            
            # Check for end-user content
            if any(term in content_lower for term in ['user', 'how to', 'guide', 'tutorial']):
                return 'end_user'
            
            return 'general'
            
        except Exception as e:
            logger.error(f"Error determining target audience: {e}")
            return 'general'
    
    def _calculate_analysis_confidence(self, sentiment: Dict[str, float], topics: List[Dict[str, Any]], 
                                     entities: List[Dict[str, Any]], keywords: List[str]) -> float:
        """Calculate confidence in analysis results"""
        try:
            confidence = 0.0
            
            # Sentiment confidence
            if sentiment and any(score > 0.1 for score in sentiment.values()):
                confidence += 0.2
            
            # Topics confidence
            if topics and len(topics) > 0:
                confidence += 0.2
            
            # Entities confidence
            if entities and len(entities) > 0:
                confidence += 0.2
            
            # Keywords confidence
            if keywords and len(keywords) > 0:
                confidence += 0.2
            
            # Overall confidence
            confidence += 0.2
            
            return min(confidence, 1.0)
            
        except Exception as e:
            logger.error(f"Error calculating analysis confidence: {e}")
            return 0.5
    
    def _count_syllables(self, word: str) -> int:
        """Count syllables in a word (simplified)"""
        vowels = 'aeiouy'
        word = word.lower()
        count = 0
        prev_was_vowel = False
        
        for char in word:
            is_vowel = char in vowels
            if is_vowel and not prev_was_vowel:
                count += 1
            prev_was_vowel = is_vowel
        
        # Handle silent 'e'
        if word.endswith('e') and count > 1:
            count -= 1
        
        return max(1, count)
    
    def _extract_technical_terms(self, content: str) -> List[str]:
        """Extract technical terms from content"""
        try:
            technical_terms = [
                'openlab', 'masshunter', 'chemstation', 'vnmrj', 'agilent',
                'chromatography', 'mass spectrometry', 'nmr', 'hplc', 'gc',
                'database', 'server', 'client', 'api', 'sdk', 'configuration',
                'installation', 'troubleshooting', 'maintenance', 'upgrade',
                'license', 'authentication', 'authorization', 'encryption',
                'backup', 'restore', 'migration', 'deployment', 'monitoring'
            ]
            
            found_terms = []
            content_lower = content.lower()
            
            for term in technical_terms:
                if term in content_lower:
                    found_terms.append(term)
            
            return found_terms
            
        except Exception as e:
            logger.error(f"Error extracting technical terms: {e}")
            return []
    
    def _extract_abbreviations(self, content: str) -> List[str]:
        """Extract abbreviations from content"""
        try:
            pattern = r'\b[A-Z]{2,5}\b'
            abbreviations = re.findall(pattern, content)
            
            # Filter out common words
            common_words = {'THE', 'AND', 'FOR', 'ARE', 'BUT', 'NOT', 'YOU', 'ALL', 'CAN', 'HAD', 'HER', 'WAS', 'ONE', 'OUR', 'OUT', 'DAY', 'GET', 'HAS', 'HIM', 'HIS', 'HOW', 'MAN', 'NEW', 'NOW', 'OLD', 'SEE', 'TWO', 'WAY', 'WHO', 'BOY', 'DID', 'ITS', 'LET', 'PUT', 'SAY', 'SHE', 'TOO', 'USE'}
            
            abbreviations = [abbr for abbr in abbreviations if abbr not in common_words]
            
            return list(set(abbreviations))[:10]
            
        except Exception as e:
            logger.error(f"Error extracting abbreviations: {e}")
            return []
    
    def _extract_code_snippets(self, content: str) -> List[str]:
        """Extract code snippets from content"""
        try:
            code_patterns = [
                r'^\s*[a-zA-Z_][a-zA-Z0-9_]*\s*=',
                r'^\s*[a-zA-Z_][a-zA-Z0-9_]*\s*\(',
                r'^\s*[a-zA-Z_][a-zA-Z0-9_]*\s*\{',
                r'^\s*[a-zA-Z_][a-zA-Z0-9_]*\s*:',
            ]
            
            code_snippets = []
            lines = content.split('\n')
            
            for line in lines:
                for pattern in code_patterns:
                    if re.match(pattern, line):
                        code_snippets.append(line.strip())
                        break
            
            return code_snippets[:10]
            
        except Exception as e:
            logger.error(f"Error extracting code snippets: {e}")
            return []
    
    def _extract_rule_based_entities(self, content: str) -> List[Dict[str, Any]]:
        """Extract entities using rule-based approach"""
        try:
            entities = []
            
            # Extract URLs
            url_pattern = r'http[s]?://(?:[a-zA-Z]|[0-9]|[$-_@.&+]|[!*\\(\\),]|(?:%[0-9a-fA-F][0-9a-fA-F]))+'
            urls = re.findall(url_pattern, content)
            for url in urls:
                entities.append({
                    'entity_text': url,
                    'entity_type': 'URL',
                    'start_pos': content.find(url),
                    'end_pos': content.find(url) + len(url),
                    'confidence': 0.9,
                    'context': self._get_entity_context(content, content.find(url), content.find(url) + len(url)),
                    'relationships': []
                })
            
            # Extract email addresses
            email_pattern = r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b'
            emails = re.findall(email_pattern, content)
            for email in emails:
                entities.append({
                    'entity_text': email,
                    'entity_type': 'EMAIL',
                    'start_pos': content.find(email),
                    'end_pos': content.find(email) + len(email),
                    'confidence': 0.9,
                    'context': self._get_entity_context(content, content.find(email), content.find(email) + len(email)),
                    'relationships': []
                })
            
            # Extract version numbers
            version_pattern = r'\b\d+\.\d+(?:\.\d+)?\b'
            versions = re.findall(version_pattern, content)
            for version in versions:
                entities.append({
                    'entity_text': version,
                    'entity_type': 'VERSION',
                    'start_pos': content.find(version),
                    'end_pos': content.find(version) + len(version),
                    'confidence': 0.8,
                    'context': self._get_entity_context(content, content.find(version), content.find(version) + len(version)),
                    'relationships': []
                })
            
            return entities
            
        except Exception as e:
            logger.error(f"Error extracting rule-based entities: {e}")
            return []
    
    def _get_entity_context(self, content: str, start_pos: int, end_pos: int, context_length: int = 50) -> str:
        """Get context around an entity"""
        try:
            context_start = max(0, start_pos - context_length)
            context_end = min(len(content), end_pos + context_length)
            return content[context_start:context_end].strip()
        except:
            return ""
    
    def _calculate_coherence_score(self, content: str) -> float:
        """Calculate coherence score based on sentence flow"""
        try:
            sentences = sent_tokenize(content)
            if len(sentences) < 2:
                return 0.5
            
            # Check for transition words
            transition_words = ['however', 'therefore', 'furthermore', 'moreover', 'additionally', 'consequently', 'meanwhile', 'subsequently']
            transition_count = 0
            
            for sentence in sentences:
                for transition in transition_words:
                    if transition in sentence.lower():
                        transition_count += 1
            
            # Calculate coherence score
            coherence_score = min(transition_count / len(sentences), 1.0)
            return coherence_score
            
        except Exception as e:
            logger.error(f"Error calculating coherence score: {e}")
            return 0.5
    
    def _calculate_completeness_score(self, content: str) -> float:
        """Calculate completeness score based on content structure"""
        try:
            score = 0.0
            
            # Check for introduction
            if any(term in content.lower() for term in ['introduction', 'overview', 'summary']):
                score += 0.2
            
            # Check for main content
            if len(content.split()) > 100:
                score += 0.3
            
            # Check for conclusion
            if any(term in content.lower() for term in ['conclusion', 'summary', 'in conclusion']):
                score += 0.2
            
            # Check for examples
            if any(term in content.lower() for term in ['example', 'for instance', 'such as']):
                score += 0.2
            
            # Check for references
            if any(term in content.lower() for term in ['reference', 'see also', 'for more information']):
                score += 0.1
            
            return min(score, 1.0)
            
        except Exception as e:
            logger.error(f"Error calculating completeness score: {e}")
            return 0.5
    
    def _calculate_accuracy_score(self, content: str) -> float:
        """Calculate accuracy score based on technical accuracy indicators"""
        try:
            score = 0.0
            
            # Check for technical terms
            technical_terms = self._extract_technical_terms(content)
            if technical_terms:
                score += 0.3
            
            # Check for version numbers
            version_pattern = r'\b\d+\.\d+(?:\.\d+)?\b'
            versions = re.findall(version_pattern, content)
            if versions:
                score += 0.2
            
            # Check for error codes
            error_pattern = r'error\s+\d+'
            errors = re.findall(error_pattern, content.lower())
            if errors:
                score += 0.2
            
            # Check for commands
            command_pattern = r'^\s*[a-zA-Z_][a-zA-Z0-9_]*\s*\(.*\)'
            commands = re.findall(command_pattern, content, re.MULTILINE)
            if commands:
                score += 0.2
            
            # Check for file paths
            path_pattern = r'[a-zA-Z]:\\[^\\]+|/[^/]+'
            paths = re.findall(path_pattern, content)
            if paths:
                score += 0.1
            
            return min(score, 1.0)
            
        except Exception as e:
            logger.error(f"Error calculating accuracy score: {e}")
            return 0.5
    
    def _calculate_relevance_score(self, content: str) -> float:
        """Calculate relevance score for Agilent products"""
        try:
            score = 0.0
            
            # Check for Agilent-related terms
            agilent_terms = ['agilent', 'openlab', 'masshunter', 'chemstation', 'vnmrj']
            content_lower = content.lower()
            
            for term in agilent_terms:
                if term in content_lower:
                    score += 0.2
            
            # Check for technical content
            technical_terms = self._extract_technical_terms(content)
            if technical_terms:
                score += 0.2
            
            # Check for troubleshooting content
            troubleshooting_terms = ['error', 'problem', 'issue', 'troubleshoot', 'fix', 'solution']
            for term in troubleshooting_terms:
                if term in content_lower:
                    score += 0.1
            
            return min(score, 1.0)
            
        except Exception as e:
            logger.error(f"Error calculating relevance score: {e}")
            return 0.5
    
    def _calculate_clarity_score(self, content: str) -> float:
        """Calculate clarity score based on clarity indicators"""
        try:
            score = 0.0
            
            # Check for clear explanations
            clarity_indicators = ['clearly', 'obviously', 'simply', 'easily', 'straightforward']
            content_lower = content.lower()
            
            for indicator in clarity_indicators:
                if indicator in content_lower:
                    score += 0.2
            
            # Check for step-by-step instructions
            if 'step' in content_lower and 'by' in content_lower:
                score += 0.3
            
            # Check for examples
            if 'example' in content_lower or 'for instance' in content_lower:
                score += 0.3
            
            # Check for visual aids
            if any(term in content_lower for term in ['figure', 'table', 'diagram', 'image']):
                score += 0.2
            
            return min(score, 1.0)
            
        except Exception as e:
            logger.error(f"Error calculating clarity score: {e}")
            return 0.5
    
    def _calculate_structure_score(self, content: str) -> float:
        """Calculate structure score based on content organization"""
        try:
            score = 0.0
            
            # Check for headings
            heading_pattern = r'^#+\s+.*$'
            headings = re.findall(heading_pattern, content, re.MULTILINE)
            if headings:
                score += 0.3
            
            # Check for numbered lists
            list_pattern = r'^\s*\d+\.\s+.*$'
            lists = re.findall(list_pattern, content, re.MULTILINE)
            if lists:
                score += 0.2
            
            # Check for bullet points
            bullet_pattern = r'^\s*[-*]\s+.*$'
            bullets = re.findall(bullet_pattern, content, re.MULTILINE)
            if bullets:
                score += 0.2
            
            # Check for paragraphs
            paragraphs = [p for p in content.split('\n\n') if p.strip()]
            if len(paragraphs) > 1:
                score += 0.2
            
            # Check for code blocks
            code_pattern = r'```.*?```'
            code_blocks = re.findall(code_pattern, content, re.DOTALL)
            if code_blocks:
                score += 0.1
            
            return min(score, 1.0)
            
        except Exception as e:
            logger.error(f"Error calculating structure score: {e}")
            return 0.5
    
    def generate_analysis_report(self, result: ContentAnalysisResult) -> Dict[str, Any]:
        """Generate comprehensive analysis report"""
        try:
            report = {
                'content_id': result.content_id,
                'analysis_type': result.analysis_type,
                'summary': {
                    'language': result.language,
                    'technical_level': result.technical_level,
                    'content_type': result.content_type,
                    'target_audience': result.target_audience,
                    'overall_quality': result.quality_score,
                    'confidence': result.confidence
                },
                'sentiment_analysis': result.sentiment,
                'topic_analysis': {
                    'topics': result.topics,
                    'topic_count': len(result.topics)
                },
                'entity_analysis': {
                    'entities': result.entities,
                    'entity_count': len(result.entities),
                    'entity_types': list(set([e['entity_type'] for e in result.entities]))
                },
                'keyword_analysis': {
                    'keywords': result.keywords,
                    'keyword_count': len(result.keywords)
                },
                'quality_metrics': result.metadata['quality_metrics'],
                'readability': {
                    'score': result.readability_score,
                    'level': 'high' if result.readability_score > 0.7 else 'medium' if result.readability_score > 0.4 else 'low'
                },
                'complexity': {
                    'score': result.complexity_score,
                    'level': result.technical_level
                },
                'processing_info': {
                    'processing_time': result.processing_time,
                    'text_length': result.metadata['text_length'],
                    'word_count': result.metadata['word_count'],
                    'sentence_count': result.metadata['sentence_count'],
                    'paragraph_count': result.metadata['paragraph_count']
                }
            }
            
            return report
            
        except Exception as e:
            logger.error(f"Error generating analysis report: {e}")
            return {}
    
    def batch_analyze(self, contents: List[str], content_ids: List[str] = None) -> List[ContentAnalysisResult]:
        """Analyze multiple contents in batch"""
        try:
            if not content_ids:
                content_ids = [hashlib.md5(content.encode()).hexdigest() for content in contents]
            
            results = []
            for i, content in enumerate(contents):
                result = self.analyze_content(content, content_ids[i])
                results.append(result)
            
            return results
            
        except Exception as e:
            logger.error(f"Error in batch analysis: {e}")
            return []
    
    def get_analysis_statistics(self, results: List[ContentAnalysisResult]) -> Dict[str, Any]:
        """Get statistics from analysis results"""
        try:
            if not results:
                return {}
            
            stats = {
                'total_contents': len(results),
                'average_quality': sum(r.quality_score for r in results) / len(results),
                'average_readability': sum(r.readability_score for r in results) / len(results),
                'average_complexity': sum(r.complexity_score for r in results) / len(results),
                'average_confidence': sum(r.confidence for r in results) / len(results),
                'language_distribution': {},
                'technical_level_distribution': {},
                'content_type_distribution': {},
                'target_audience_distribution': {},
                'sentiment_distribution': {'positive': 0, 'negative': 0, 'neutral': 0},
                'processing_time_stats': {
                    'total': sum(r.processing_time for r in results),
                    'average': sum(r.processing_time for r in results) / len(results),
                    'min': min(r.processing_time for r in results),
                    'max': max(r.processing_time for r in results)
                }
            }
            
            # Calculate distributions
            for result in results:
                # Language distribution
                stats['language_distribution'][result.language] = stats['language_distribution'].get(result.language, 0) + 1
                
                # Technical level distribution
                stats['technical_level_distribution'][result.technical_level] = stats['technical_level_distribution'].get(result.technical_level, 0) + 1
                
                # Content type distribution
                stats['content_type_distribution'][result.content_type] = stats['content_type_distribution'].get(result.content_type, 0) + 1
                
                # Target audience distribution
                stats['target_audience_distribution'][result.target_audience] = stats['target_audience_distribution'].get(result.target_audience, 0) + 1
                
                # Sentiment distribution
                if result.sentiment:
                    max_sentiment = max(result.sentiment.items(), key=lambda x: x[1])[0]
                    stats['sentiment_distribution'][max_sentiment] += 1
            
            return stats
            
        except Exception as e:
            logger.error(f"Error getting analysis statistics: {e}")
            return {}
    
    def export_analysis_results(self, results: List[ContentAnalysisResult], format: str = 'json') -> str:
        """Export analysis results in specified format"""
        try:
            if format.lower() == 'json':
                return self._export_json(results)
            elif format.lower() == 'csv':
                return self._export_csv(results)
            else:
                raise ValueError(f"Unsupported export format: {format}")
                
        except Exception as e:
            logger.error(f"Error exporting analysis results: {e}")
            return ""
    
    def _export_json(self, results: List[ContentAnalysisResult]) -> str:
        """Export results as JSON"""
        try:
            data = []
            for result in results:
                data.append({
                    'content_id': result.content_id,
                    'analysis_type': result.analysis_type,
                    'sentiment': result.sentiment,
                    'topics': result.topics,
                    'entities': result.entities,
                    'keywords': result.keywords,
                    'language': result.language,
                    'readability_score': result.readability_score,
                    'complexity_score': result.complexity_score,
                    'quality_score': result.quality_score,
                    'technical_level': result.technical_level,
                    'content_type': result.content_type,
                    'target_audience': result.target_audience,
                    'confidence': result.confidence,
                    'processing_time': result.processing_time,
                    'metadata': result.metadata
                })
            
            return json.dumps(data, indent=2, ensure_ascii=False)
            
        except Exception as e:
            logger.error(f"Error exporting JSON: {e}")
            return ""
    
    def _export_csv(self, results: List[ContentAnalysisResult]) -> str:
        """Export results as CSV"""
        try:
            import csv
            import io
            
            output = io.StringIO()
            writer = csv.writer(output)
            
            # Write header
            writer.writerow([
                'content_id', 'analysis_type', 'language', 'technical_level',
                'content_type', 'target_audience', 'quality_score', 'readability_score',
                'complexity_score', 'confidence', 'processing_time', 'word_count',
                'sentence_count', 'paragraph_count'
            ])
            
            # Write data
            for result in results:
                writer.writerow([
                    result.content_id,
                    result.analysis_type,
                    result.language,
                    result.technical_level,
                    result.content_type,
                    result.target_audience,
                    result.quality_score,
                    result.readability_score,
                    result.complexity_score,
                    result.confidence,
                    result.processing_time,
                    result.metadata['word_count'],
                    result.metadata['sentence_count'],
                    result.metadata['paragraph_count']
                ])
            
            return output.getvalue()
            
        except Exception as e:
            logger.error(f"Error exporting CSV: {e}")
            return ""
