"""
AI-Powered Metadata Extraction

This module provides comprehensive AI-powered metadata extraction capabilities
including content analysis, entity recognition, and automatic tagging.
"""

import logging
import json
import re
from typing import Dict, Any, List, Optional, Tuple
from dataclasses import dataclass
from datetime import datetime
import hashlib
import requests
from transformers import pipeline, AutoTokenizer, AutoModel
import spacy
from textblob import TextBlob
import nltk
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.cluster import KMeans
import numpy as np

logger = logging.getLogger(__name__)


@dataclass
class ExtractedMetadata:
    """Extracted metadata structure"""
    title: str
    description: str
    keywords: List[str]
    categories: List[str]
    entities: List[Dict[str, Any]]
    topics: List[str]
    language: str
    sentiment: Dict[str, float]
    complexity_score: float
    relevance_score: float
    quality_score: float
    technical_level: str
    content_type: str
    target_audience: str
    extraction_confidence: float
    processing_time: float


@dataclass
class ContentAnalysis:
    """Content analysis structure"""
    text_length: int
    word_count: int
    sentence_count: int
    paragraph_count: int
    readability_score: float
    technical_terms: List[str]
    abbreviations: List[str]
    references: List[str]
    code_snippets: List[str]
    urls: List[str]
    email_addresses: List[str]
    phone_numbers: List[str]
    dates: List[str]
    numbers: List[str]


class AIMetadataExtractor:
    """AI-powered metadata extractor"""
    
    def __init__(self, config: Dict[str, Any] = None):
        """Initialize AI metadata extractor with configuration"""
        self.config = config or {}
        self.llm_enabled = self.config.get('llm_enabled', True)
        self.ner_enabled = self.config.get('ner_enabled', True)
        self.sentiment_analysis_enabled = self.config.get('sentiment_analysis_enabled', True)
        self.topic_modeling_enabled = self.config.get('topic_modeling_enabled', True)
        self.classification_enabled = self.config.get('classification_enabled', True)
        self.entity_extraction_enabled = self.config.get('entity_extraction_enabled', True)
        
        # LLM configuration
        self.llm_model = self.config.get('llm_model', 'microsoft/DialoGPT-medium')
        self.llm_max_length = self.config.get('llm_max_length', 512)
        self.llm_temperature = self.config.get('llm_temperature', 0.7)
        
        # NER configuration
        self.ner_model = self.config.get('ner_model', 'en_core_web_sm')
        self.ner_confidence_threshold = self.config.get('ner_confidence_threshold', 0.5)
        
        # Sentiment analysis configuration
        self.sentiment_model = self.config.get('sentiment_model', 'cardiffnlp/twitter-roberta-base-sentiment-latest')
        
        # Topic modeling configuration
        self.topic_model = self.config.get('topic_model', 'lda')
        self.num_topics = self.config.get('num_topics', 5)
        self.max_features = self.config.get('max_features', 1000)
        
        # Classification configuration
        self.classification_model = self.config.get('classification_model', 'microsoft/DialoGPT-medium')
        self.classification_categories = self.config.get('classification_categories', [
            'troubleshooting', 'installation', 'configuration', 'maintenance', 
            'user_guide', 'technical_specification', 'release_notes', 'faq'
        ])
        
        # Entity extraction configuration
        self.entity_types = self.config.get('entity_types', [
            'PERSON', 'ORG', 'GPE', 'PRODUCT', 'SOFTWARE', 'HARDWARE', 
            'VERSION', 'ERROR_CODE', 'COMMAND', 'FILE_PATH'
        ])
        
        # Initialize components
        self._initialize_components()
        
        logger.info("AI Metadata Extractor initialized with configuration")
    
    def _initialize_components(self):
        """Initialize AI components"""
        try:
            # Initialize NER model
            if self.ner_enabled:
                try:
                    self.nlp = spacy.load(self.ner_model)
                    logger.info(f"NER model '{self.ner_model}' loaded")
                except OSError:
                    logger.warning(f"NER model '{self.ner_model}' not found, using basic NER")
                    self.nlp = None
            
            # Initialize sentiment analysis
            if self.sentiment_analysis_enabled:
                self.sentiment_pipeline = pipeline(
                    "sentiment-analysis",
                    model=self.sentiment_model,
                    return_all_scores=True
                )
                logger.info(f"Sentiment analysis model '{self.sentiment_model}' loaded")
            
            # Initialize topic modeling
            if self.topic_modeling_enabled:
                self.tfidf_vectorizer = TfidfVectorizer(
                    max_features=self.max_features,
                    stop_words='english',
                    ngram_range=(1, 2)
                )
                logger.info("Topic modeling components initialized")
            
            # Initialize classification
            if self.classification_enabled:
                self.classification_pipeline = pipeline(
                    "text-classification",
                    model=self.classification_model,
                    return_all_scores=True
                )
                logger.info(f"Classification model '{self.classification_model}' loaded")
            
            # Download NLTK data
            try:
                nltk.download('punkt', quiet=True)
                nltk.download('stopwords', quiet=True)
                nltk.download('averaged_perceptron_tagger', quiet=True)
            except:
                pass
            
        except Exception as e:
            logger.error(f"Error initializing components: {e}")
            raise
    
    def extract_metadata(self, content: str, content_type: str = 'text') -> ExtractedMetadata:
        """Extract metadata from content using AI"""
        start_time = datetime.now()
        
        try:
            logger.info(f"Starting AI metadata extraction for {content_type} content")
            
            # Analyze content
            content_analysis = self._analyze_content(content)
            
            # Extract title
            title = self._extract_title(content, content_analysis)
            
            # Extract description
            description = self._extract_description(content, content_analysis)
            
            # Extract keywords
            keywords = self._extract_keywords(content, content_analysis)
            
            # Extract categories
            categories = self._extract_categories(content, content_analysis)
            
            # Extract entities
            entities = self._extract_entities(content, content_analysis)
            
            # Extract topics
            topics = self._extract_topics(content, content_analysis)
            
            # Detect language
            language = self._detect_language(content)
            
            # Analyze sentiment
            sentiment = self._analyze_sentiment(content) if self.sentiment_analysis_enabled else {'positive': 0.0, 'negative': 0.0, 'neutral': 0.0}
            
            # Calculate complexity score
            complexity_score = self._calculate_complexity_score(content, content_analysis)
            
            # Calculate relevance score
            relevance_score = self._calculate_relevance_score(content, content_analysis)
            
            # Calculate quality score
            quality_score = self._calculate_quality_score(content, content_analysis)
            
            # Determine technical level
            technical_level = self._determine_technical_level(content, content_analysis)
            
            # Determine target audience
            target_audience = self._determine_target_audience(content, content_analysis)
            
            # Calculate extraction confidence
            extraction_confidence = self._calculate_extraction_confidence(
                title, description, keywords, categories, entities, topics
            )
            
            # Calculate processing time
            processing_time = (datetime.now() - start_time).total_seconds()
            
            # Create metadata object
            metadata = ExtractedMetadata(
                title=title,
                description=description,
                keywords=keywords,
                categories=categories,
                entities=entities,
                topics=topics,
                language=language,
                sentiment=sentiment,
                complexity_score=complexity_score,
                relevance_score=relevance_score,
                quality_score=quality_score,
                technical_level=technical_level,
                content_type=content_type,
                target_audience=target_audience,
                extraction_confidence=extraction_confidence,
                processing_time=processing_time
            )
            
            logger.info(f"AI metadata extraction completed in {processing_time:.2f} seconds")
            return metadata
            
        except Exception as e:
            logger.error(f"Error extracting metadata: {e}")
            raise
    
    def _analyze_content(self, content: str) -> ContentAnalysis:
        """Analyze content structure and extract basic information"""
        try:
            # Basic text analysis
            text_length = len(content)
            word_count = len(content.split())
            sentence_count = len(re.split(r'[.!?]+', content))
            paragraph_count = len([p for p in content.split('\n\n') if p.strip()])
            
            # Calculate readability score
            readability_score = self._calculate_readability_score(content)
            
            # Extract technical terms
            technical_terms = self._extract_technical_terms(content)
            
            # Extract abbreviations
            abbreviations = self._extract_abbreviations(content)
            
            # Extract references
            references = self._extract_references(content)
            
            # Extract code snippets
            code_snippets = self._extract_code_snippets(content)
            
            # Extract URLs
            urls = self._extract_urls(content)
            
            # Extract email addresses
            email_addresses = self._extract_email_addresses(content)
            
            # Extract phone numbers
            phone_numbers = self._extract_phone_numbers(content)
            
            # Extract dates
            dates = self._extract_dates(content)
            
            # Extract numbers
            numbers = self._extract_numbers(content)
            
            return ContentAnalysis(
                text_length=text_length,
                word_count=word_count,
                sentence_count=sentence_count,
                paragraph_count=paragraph_count,
                readability_score=readability_score,
                technical_terms=technical_terms,
                abbreviations=abbreviations,
                references=references,
                code_snippets=code_snippets,
                urls=urls,
                email_addresses=email_addresses,
                phone_numbers=phone_numbers,
                dates=dates,
                numbers=numbers
            )
            
        except Exception as e:
            logger.error(f"Error analyzing content: {e}")
            raise
    
    def _extract_title(self, content: str, analysis: ContentAnalysis) -> str:
        """Extract title from content"""
        try:
            # Try to find title in first few lines
            lines = content.split('\n')
            for line in lines[:5]:
                line = line.strip()
                if line and len(line) < 100 and not line.endswith('.'):
                    # Check if line looks like a title
                    if self._looks_like_title(line):
                        return line
            
            # Fallback: use first sentence
            sentences = re.split(r'[.!?]+', content)
            if sentences:
                first_sentence = sentences[0].strip()
                if len(first_sentence) < 100:
                    return first_sentence
            
            # Fallback: use first 50 characters
            return content[:50].strip()
            
        except Exception as e:
            logger.error(f"Error extracting title: {e}")
            return "Untitled"
    
    def _extract_description(self, content: str, analysis: ContentAnalysis) -> str:
        """Extract description from content"""
        try:
            # Use first paragraph or first few sentences
            paragraphs = [p.strip() for p in content.split('\n\n') if p.strip()]
            
            if paragraphs:
                first_paragraph = paragraphs[0]
                if len(first_paragraph) > 200:
                    # Truncate to 200 characters
                    first_paragraph = first_paragraph[:200] + "..."
                return first_paragraph
            
            # Fallback: use first 200 characters
            return content[:200].strip()
            
        except Exception as e:
            logger.error(f"Error extracting description: {e}")
            return ""
    
    def _extract_keywords(self, content: str, analysis: ContentAnalysis) -> List[str]:
        """Extract keywords from content"""
        try:
            keywords = []
            
            # Add technical terms
            keywords.extend(analysis.technical_terms[:10])
            
            # Add abbreviations
            keywords.extend(analysis.abbreviations[:5])
            
            # Use TF-IDF for additional keywords
            if self.topic_modeling_enabled:
                tfidf_keywords = self._extract_tfidf_keywords(content)
                keywords.extend(tfidf_keywords[:10])
            
            # Remove duplicates and limit
            keywords = list(set(keywords))[:20]
            
            return keywords
            
        except Exception as e:
            logger.error(f"Error extracting keywords: {e}")
            return []
    
    def _extract_categories(self, content: str, analysis: ContentAnalysis) -> List[str]:
        """Extract categories from content"""
        try:
            categories = []
            
            # Use classification if enabled
            if self.classification_enabled:
                try:
                    classification_result = self.classification_pipeline(content[:512])  # Limit length
                    for result in classification_result:
                        if result['score'] > 0.5:
                            categories.append(result['label'])
                except Exception as e:
                    logger.warning(f"Classification failed: {e}")
            
            # Fallback: use rule-based categorization
            if not categories:
                categories = self._categorize_by_rules(content, analysis)
            
            return categories[:5]  # Limit to 5 categories
            
        except Exception as e:
            logger.error(f"Error extracting categories: {e}")
            return []
    
    def _extract_entities(self, content: str, analysis: ContentAnalysis) -> List[Dict[str, Any]]:
        """Extract entities from content"""
        try:
            entities = []
            
            # Use NER if available
            if self.ner_enabled and self.nlp:
                try:
                    doc = self.nlp(content)
                    for ent in doc.ents:
                        if ent.label_ in self.entity_types and ent.confidence >= self.ner_confidence_threshold:
                            entities.append({
                                'text': ent.text,
                                'label': ent.label_,
                                'start': ent.start_char,
                                'end': ent.end_char,
                                'confidence': ent.confidence
                            })
                except Exception as e:
                    logger.warning(f"NER failed: {e}")
            
            # Add technical terms as entities
            for term in analysis.technical_terms[:10]:
                entities.append({
                    'text': term,
                    'label': 'TECHNICAL_TERM',
                    'start': 0,
                    'end': len(term),
                    'confidence': 0.8
                })
            
            # Add abbreviations as entities
            for abbr in analysis.abbreviations[:5]:
                entities.append({
                    'text': abbr,
                    'label': 'ABBREVIATION',
                    'start': 0,
                    'end': len(abbr),
                    'confidence': 0.7
                })
            
            return entities[:20]  # Limit to 20 entities
            
        except Exception as e:
            logger.error(f"Error extracting entities: {e}")
            return []
    
    def _extract_topics(self, content: str, analysis: ContentAnalysis) -> List[str]:
        """Extract topics from content"""
        try:
            topics = []
            
            # Use topic modeling if enabled
            if self.topic_modeling_enabled:
                try:
                    topic_keywords = self._extract_topic_keywords(content)
                    topics.extend(topic_keywords)
                except Exception as e:
                    logger.warning(f"Topic modeling failed: {e}")
            
            # Add rule-based topics
            rule_based_topics = self._extract_rule_based_topics(content, analysis)
            topics.extend(rule_based_topics)
            
            # Remove duplicates and limit
            topics = list(set(topics))[:10]
            
            return topics
            
        except Exception as e:
            logger.error(f"Error extracting topics: {e}")
            return []
    
    def _detect_language(self, content: str) -> str:
        """Detect language of content"""
        try:
            blob = TextBlob(content)
            return blob.detect_language()
        except:
            return 'en'  # Default to English
    
    def _analyze_sentiment(self, content: str) -> Dict[str, float]:
        """Analyze sentiment of content"""
        try:
            if not self.sentiment_analysis_enabled:
                return {'positive': 0.0, 'negative': 0.0, 'neutral': 0.0}
            
            # Use sentiment analysis pipeline
            result = self.sentiment_pipeline(content[:512])  # Limit length
            
            sentiment = {'positive': 0.0, 'negative': 0.0, 'neutral': 0.0}
            
            for item in result:
                label = item['label'].lower()
                score = item['score']
                
                if 'positive' in label:
                    sentiment['positive'] = score
                elif 'negative' in label:
                    sentiment['negative'] = score
                elif 'neutral' in label:
                    sentiment['neutral'] = score
            
            return sentiment
            
        except Exception as e:
            logger.error(f"Error analyzing sentiment: {e}")
            return {'positive': 0.0, 'negative': 0.0, 'neutral': 0.0}
    
    def _calculate_complexity_score(self, content: str, analysis: ContentAnalysis) -> float:
        """Calculate complexity score for content"""
        try:
            score = 0.0
            
            # Technical terms contribute to complexity
            score += min(len(analysis.technical_terms) / 50.0, 0.3)
            
            # Abbreviations contribute to complexity
            score += min(len(analysis.abbreviations) / 20.0, 0.2)
            
            # Code snippets contribute to complexity
            score += min(len(analysis.code_snippets) / 10.0, 0.2)
            
            # Readability score (inverse)
            score += (1.0 - analysis.readability_score) * 0.3
            
            return min(score, 1.0)
            
        except Exception as e:
            logger.error(f"Error calculating complexity score: {e}")
            return 0.5
    
    def _calculate_relevance_score(self, content: str, analysis: ContentAnalysis) -> float:
        """Calculate relevance score for content"""
        try:
            score = 0.0
            
            # Check for Agilent-related terms
            agilent_terms = ['agilent', 'openlab', 'masshunter', 'chemstation', 'vnmrj']
            content_lower = content.lower()
            
            for term in agilent_terms:
                if term in content_lower:
                    score += 0.2
            
            # Check for technical content
            if analysis.technical_terms:
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
    
    def _calculate_quality_score(self, content: str, analysis: ContentAnalysis) -> float:
        """Calculate quality score for content"""
        try:
            score = 0.0
            
            # Length score
            if analysis.word_count > 100:
                score += 0.2
            
            # Structure score
            if analysis.paragraph_count > 1:
                score += 0.2
            
            # Technical content score
            if analysis.technical_terms:
                score += 0.2
            
            # Readability score
            score += analysis.readability_score * 0.2
            
            # Completeness score
            if analysis.urls or analysis.references:
                score += 0.2
            
            return min(score, 1.0)
            
        except Exception as e:
            logger.error(f"Error calculating quality score: {e}")
            return 0.5
    
    def _determine_technical_level(self, content: str, analysis: ContentAnalysis) -> str:
        """Determine technical level of content"""
        try:
            complexity_score = self._calculate_complexity_score(content, analysis)
            
            if complexity_score > 0.7:
                return 'expert'
            elif complexity_score > 0.4:
                return 'intermediate'
            else:
                return 'beginner'
                
        except Exception as e:
            logger.error(f"Error determining technical level: {e}")
            return 'intermediate'
    
    def _determine_target_audience(self, content: str, analysis: ContentAnalysis) -> str:
        """Determine target audience of content"""
        try:
            content_lower = content.lower()
            
            # Check for administrator content
            admin_terms = ['admin', 'administrator', 'install', 'configure', 'setup']
            if any(term in content_lower for term in admin_terms):
                return 'administrator'
            
            # Check for developer content
            dev_terms = ['api', 'sdk', 'develop', 'programming', 'code']
            if any(term in content_lower for term in dev_terms):
                return 'developer'
            
            # Check for end-user content
            user_terms = ['user', 'how to', 'guide', 'tutorial', 'step by step']
            if any(term in content_lower for term in user_terms):
                return 'end_user'
            
            return 'general'
            
        except Exception as e:
            logger.error(f"Error determining target audience: {e}")
            return 'general'
    
    def _calculate_extraction_confidence(self, title: str, description: str, keywords: List[str], 
                                       categories: List[str], entities: List[str], topics: List[str]) -> float:
        """Calculate confidence in extraction results"""
        try:
            confidence = 0.0
            
            # Title confidence
            if title and len(title) > 5:
                confidence += 0.2
            
            # Description confidence
            if description and len(description) > 20:
                confidence += 0.2
            
            # Keywords confidence
            if keywords:
                confidence += 0.2
            
            # Categories confidence
            if categories:
                confidence += 0.2
            
            # Entities confidence
            if entities:
                confidence += 0.1
            
            # Topics confidence
            if topics:
                confidence += 0.1
            
            return min(confidence, 1.0)
            
        except Exception as e:
            logger.error(f"Error calculating extraction confidence: {e}")
            return 0.5
    
    def _looks_like_title(self, text: str) -> bool:
        """Check if text looks like a title"""
        # Simple heuristics for title detection
        if len(text) > 100:
            return False
        
        if text.endswith('.'):
            return False
        
        if text.count(' ') > 10:
            return False
        
        return True
    
    def _calculate_readability_score(self, content: str) -> float:
        """Calculate readability score using simple metrics"""
        try:
            sentences = re.split(r'[.!?]+', content)
            words = content.split()
            
            if not sentences or not words:
                return 0.5
            
            avg_sentence_length = len(words) / len(sentences)
            avg_word_length = sum(len(word) for word in words) / len(words)
            
            # Simple readability score (0-1, higher is more readable)
            score = 1.0 - (avg_sentence_length / 50.0) - (avg_word_length / 20.0)
            return max(0.0, min(score, 1.0))
            
        except Exception as e:
            logger.error(f"Error calculating readability score: {e}")
            return 0.5
    
    def _extract_technical_terms(self, content: str) -> List[str]:
        """Extract technical terms from content"""
        try:
            # Common technical terms in Agilent context
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
            # Pattern for abbreviations (2-5 uppercase letters)
            pattern = r'\b[A-Z]{2,5}\b'
            abbreviations = re.findall(pattern, content)
            
            # Filter out common words
            common_words = {'THE', 'AND', 'FOR', 'ARE', 'BUT', 'NOT', 'YOU', 'ALL', 'CAN', 'HAD', 'HER', 'WAS', 'ONE', 'OUR', 'OUT', 'DAY', 'GET', 'HAS', 'HIM', 'HIS', 'HOW', 'MAN', 'NEW', 'NOW', 'OLD', 'SEE', 'TWO', 'WAY', 'WHO', 'BOY', 'DID', 'ITS', 'LET', 'PUT', 'SAY', 'SHE', 'TOO', 'USE'}
            
            abbreviations = [abbr for abbr in abbreviations if abbr not in common_words]
            
            return list(set(abbreviations))[:10]  # Limit to 10 unique abbreviations
            
        except Exception as e:
            logger.error(f"Error extracting abbreviations: {e}")
            return []
    
    def _extract_references(self, content: str) -> List[str]:
        """Extract references from content"""
        try:
            # Pattern for references (e.g., "See section 1.2", "Refer to page 5")
            patterns = [
                r'see section \d+\.?\d*',
                r'refer to page \d+',
                r'see page \d+',
                r'reference \d+',
                r'see \w+ \d+'
            ]
            
            references = []
            for pattern in patterns:
                matches = re.findall(pattern, content.lower())
                references.extend(matches)
            
            return list(set(references))[:10]  # Limit to 10 unique references
            
        except Exception as e:
            logger.error(f"Error extracting references: {e}")
            return []
    
    def _extract_code_snippets(self, content: str) -> List[str]:
        """Extract code snippets from content"""
        try:
            # Pattern for code snippets (lines starting with common code indicators)
            code_patterns = [
                r'^\s*[a-zA-Z_][a-zA-Z0-9_]*\s*=',  # Variable assignment
                r'^\s*[a-zA-Z_][a-zA-Z0-9_]*\s*\(',  # Function call
                r'^\s*[a-zA-Z_][a-zA-Z0-9_]*\s*\{',  # Block start
                r'^\s*[a-zA-Z_][a-zA-Z0-9_]*\s*:',   # Label or key-value
            ]
            
            code_snippets = []
            lines = content.split('\n')
            
            for line in lines:
                for pattern in code_patterns:
                    if re.match(pattern, line):
                        code_snippets.append(line.strip())
                        break
            
            return code_snippets[:10]  # Limit to 10 code snippets
            
        except Exception as e:
            logger.error(f"Error extracting code snippets: {e}")
            return []
    
    def _extract_urls(self, content: str) -> List[str]:
        """Extract URLs from content"""
        try:
            # Pattern for URLs
            url_pattern = r'http[s]?://(?:[a-zA-Z]|[0-9]|[$-_@.&+]|[!*\\(\\),]|(?:%[0-9a-fA-F][0-9a-fA-F]))+'
            urls = re.findall(url_pattern, content)
            
            return list(set(urls))[:10]  # Limit to 10 unique URLs
            
        except Exception as e:
            logger.error(f"Error extracting URLs: {e}")
            return []
    
    def _extract_email_addresses(self, content: str) -> List[str]:
        """Extract email addresses from content"""
        try:
            # Pattern for email addresses
            email_pattern = r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b'
            emails = re.findall(email_pattern, content)
            
            return list(set(emails))[:5]  # Limit to 5 unique emails
            
        except Exception as e:
            logger.error(f"Error extracting email addresses: {e}")
            return []
    
    def _extract_phone_numbers(self, content: str) -> List[str]:
        """Extract phone numbers from content"""
        try:
            # Pattern for phone numbers
            phone_pattern = r'\b\d{3}[-.]?\d{3}[-.]?\d{4}\b'
            phones = re.findall(phone_pattern, content)
            
            return list(set(phones))[:5]  # Limit to 5 unique phone numbers
            
        except Exception as e:
            logger.error(f"Error extracting phone numbers: {e}")
            return []
    
    def _extract_dates(self, content: str) -> List[str]:
        """Extract dates from content"""
        try:
            # Pattern for dates
            date_patterns = [
                r'\b\d{1,2}[/-]\d{1,2}[/-]\d{2,4}\b',  # MM/DD/YYYY or DD/MM/YYYY
                r'\b\d{4}[/-]\d{1,2}[/-]\d{1,2}\b',     # YYYY/MM/DD
                r'\b(?:Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec)[a-z]* \d{1,2},? \d{4}\b',  # Month DD, YYYY
            ]
            
            dates = []
            for pattern in date_patterns:
                matches = re.findall(pattern, content)
                dates.extend(matches)
            
            return list(set(dates))[:10]  # Limit to 10 unique dates
            
        except Exception as e:
            logger.error(f"Error extracting dates: {e}")
            return []
    
    def _extract_numbers(self, content: str) -> List[str]:
        """Extract numbers from content"""
        try:
            # Pattern for numbers
            number_pattern = r'\b\d+(?:\.\d+)?\b'
            numbers = re.findall(number_pattern, content)
            
            return list(set(numbers))[:20]  # Limit to 20 unique numbers
            
        except Exception as e:
            logger.error(f"Error extracting numbers: {e}")
            return []
    
    def _extract_tfidf_keywords(self, content: str) -> List[str]:
        """Extract keywords using TF-IDF"""
        try:
            # Prepare text for TF-IDF
            sentences = re.split(r'[.!?]+', content)
            sentences = [s.strip() for s in sentences if s.strip()]
            
            if len(sentences) < 2:
                return []
            
            # Fit TF-IDF vectorizer
            tfidf_matrix = self.tfidf_vectorizer.fit_transform(sentences)
            feature_names = self.tfidf_vectorizer.get_feature_names_out()
            
            # Get top keywords
            mean_scores = np.mean(tfidf_matrix.toarray(), axis=0)
            top_indices = np.argsort(mean_scores)[-20:]  # Top 20 keywords
            
            keywords = [feature_names[i] for i in top_indices if mean_scores[i] > 0.1]
            
            return keywords
            
        except Exception as e:
            logger.error(f"Error extracting TF-IDF keywords: {e}")
            return []
    
    def _categorize_by_rules(self, content: str, analysis: ContentAnalysis) -> List[str]:
        """Categorize content using rule-based approach"""
        try:
            categories = []
            content_lower = content.lower()
            
            # Define category rules
            category_rules = {
                'troubleshooting': ['error', 'problem', 'issue', 'troubleshoot', 'fix', 'solution', 'debug'],
                'installation': ['install', 'setup', 'configure', 'deploy', 'setup'],
                'configuration': ['config', 'setting', 'parameter', 'option', 'preference'],
                'maintenance': ['maintain', 'update', 'upgrade', 'backup', 'restore'],
                'user_guide': ['guide', 'tutorial', 'how to', 'step by step', 'manual'],
                'technical_specification': ['spec', 'requirement', 'specification', 'standard'],
                'release_notes': ['release', 'version', 'changelog', 'new feature'],
                'faq': ['faq', 'frequently asked', 'question', 'answer']
            }
            
            # Apply rules
            for category, keywords in category_rules.items():
                if any(keyword in content_lower for keyword in keywords):
                    categories.append(category)
            
            return categories
            
        except Exception as e:
            logger.error(f"Error categorizing by rules: {e}")
            return []
    
    def _extract_topic_keywords(self, content: str) -> List[str]:
        """Extract topic keywords using topic modeling"""
        try:
            # Prepare text for topic modeling
            sentences = re.split(r'[.!?]+', content)
            sentences = [s.strip() for s in sentences if s.strip()]
            
            if len(sentences) < 3:
                return []
            
            # Fit TF-IDF vectorizer
            tfidf_matrix = self.tfidf_vectorizer.fit_transform(sentences)
            
            # Apply K-means clustering
            kmeans = KMeans(n_clusters=min(self.num_topics, len(sentences)), random_state=42)
            kmeans.fit(tfidf_matrix)
            
            # Get top keywords for each cluster
            feature_names = self.tfidf_vectorizer.get_feature_names_out()
            topics = []
            
            for i in range(kmeans.n_clusters):
                cluster_center = kmeans.cluster_centers_[i]
                top_indices = np.argsort(cluster_center)[-5:]  # Top 5 keywords per cluster
                cluster_keywords = [feature_names[idx] for idx in top_indices if cluster_center[idx] > 0.1]
                topics.extend(cluster_keywords)
            
            return list(set(topics))[:10]  # Limit to 10 unique topics
            
        except Exception as e:
            logger.error(f"Error extracting topic keywords: {e}")
            return []
    
    def _extract_rule_based_topics(self, content: str, analysis: ContentAnalysis) -> List[str]:
        """Extract topics using rule-based approach"""
        try:
            topics = []
            content_lower = content.lower()
            
            # Define topic rules
            topic_rules = {
                'chromatography': ['hplc', 'gc', 'chromatography', 'column', 'detector'],
                'mass_spectrometry': ['mass', 'spectrometry', 'ms', 'ion', 'molecular'],
                'nmr': ['nmr', 'nuclear', 'magnetic', 'resonance', 'spectrum'],
                'data_analysis': ['analysis', 'data', 'processing', 'calculation', 'statistics'],
                'software': ['software', 'application', 'program', 'interface', 'gui'],
                'hardware': ['hardware', 'instrument', 'equipment', 'device', 'component'],
                'networking': ['network', 'connection', 'communication', 'protocol', 'tcp'],
                'security': ['security', 'authentication', 'authorization', 'encryption', 'password'],
                'database': ['database', 'sql', 'query', 'table', 'record'],
                'api': ['api', 'interface', 'endpoint', 'service', 'rest']
            }
            
            # Apply rules
            for topic, keywords in topic_rules.items():
                if any(keyword in content_lower for keyword in keywords):
                    topics.append(topic)
            
            return topics
            
        except Exception as e:
            logger.error(f"Error extracting rule-based topics: {e}")
            return []
    
    def export_metadata(self, metadata: ExtractedMetadata, format: str = 'json') -> str:
        """Export metadata in specified format"""
        if format.lower() == 'json':
            return self._export_json(metadata)
        elif format.lower() == 'yaml':
            return self._export_yaml(metadata)
        else:
            raise ValueError(f"Unsupported export format: {format}")
    
    def _export_json(self, metadata: ExtractedMetadata) -> str:
        """Export metadata as JSON"""
        data = {
            'title': metadata.title,
            'description': metadata.description,
            'keywords': metadata.keywords,
            'categories': metadata.categories,
            'entities': metadata.entities,
            'topics': metadata.topics,
            'language': metadata.language,
            'sentiment': metadata.sentiment,
            'complexity_score': metadata.complexity_score,
            'relevance_score': metadata.relevance_score,
            'quality_score': metadata.quality_score,
            'technical_level': metadata.technical_level,
            'content_type': metadata.content_type,
            'target_audience': metadata.target_audience,
            'extraction_confidence': metadata.extraction_confidence,
            'processing_time': metadata.processing_time
        }
        
        return json.dumps(data, indent=2, ensure_ascii=False)
    
    def _export_yaml(self, metadata: ExtractedMetadata) -> str:
        """Export metadata as YAML"""
        import yaml
        
        data = {
            'title': metadata.title,
            'description': metadata.description,
            'keywords': metadata.keywords,
            'categories': metadata.categories,
            'entities': metadata.entities,
            'topics': metadata.topics,
            'language': metadata.language,
            'sentiment': metadata.sentiment,
            'complexity_score': metadata.complexity_score,
            'relevance_score': metadata.relevance_score,
            'quality_score': metadata.quality_score,
            'technical_level': metadata.technical_level,
            'content_type': metadata.content_type,
            'target_audience': metadata.target_audience,
            'extraction_confidence': metadata.extraction_confidence,
            'processing_time': metadata.processing_time
        }
        
        return yaml.dump(data, default_flow_style=False, allow_unicode=True)
