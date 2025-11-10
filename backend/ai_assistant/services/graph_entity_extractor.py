"""
Enhanced Entity Extraction for Graph RAG

This service extracts domain-specific entities from documents for storage in Neo4j.
Includes entity linking, disambiguation, and normalization.
Now includes LLM-based extraction for concepts and important information.
"""

import logging
import re
import json
import requests
from typing import List, Dict, Any, Optional, Set
from dataclasses import dataclass
import hashlib
from django.conf import settings

logger = logging.getLogger(__name__)


@dataclass
class ExtractedEntity:
    """Structure for extracted entities"""
    text: str  # Original text
    normalized_text: str  # Normalized/canonical form
    entity_type: str  # Type of entity
    start_pos: int  # Character position in document
    end_pos: int  # Character position in document
    confidence: float  # Confidence score 0-1
    context: str  # Surrounding context
    metadata: Dict[str, Any]  # Additional metadata


class GraphEntityExtractor:
    """Enhanced entity extractor for Graph RAG with domain-specific patterns"""
    
    # Domain-specific entity patterns
    PRODUCT_PATTERNS = [
        r'OpenLab\s+(?:CDS|ECM|ELN|Server|XT)',
        r'MassHunter\s+(?:Workstation|Quantitative|Qualitative|BioConfirm|Metabolomics)',
        r'7890B?\s+GC',
        r'[0-9]{4}[A-Z]?\s+(?:GC|LC|MS|NMR)',
        r'VNMR[EJ]?',
        r'OpenLab\s+Data\s+Analysis',
    ]
    
    VERSION_PATTERNS = [
        r'(?:v|version|ver\.?|Release)\s*(\d+(?:\.\d+)*(?:\.\d+)?)',
        r'(\d+\.\d+(?:\.\d+)?)\s*(?:Release|Version)',
        r'v(\d+\.\d+)',
    ]
    
    ERROR_CODE_PATTERNS = [
        r'(?:KPR|M)\d+[A-Z]?\d+[A-Z]?',  # KPR-1476890N, M84xx
        r'Error\s+(?:Code|#)?\s*:?\s*([A-Z0-9\-]+)',
        r'(?:ERROR|WARNING|FATAL)\s+([A-Z0-9\-_]+)',
    ]
    
    SOFTWARE_PATTERNS = [
        r'Windows\s+(?:Server\s+)?(?:10|11|2016|2019|2022)',
        r'Linux\s+(?:Red\s+Hat|Ubuntu|CentOS|Debian)',
        r'SQL\s+Server\s+\d{4}',
        r'Oracle\s+\d{1,2}[c|g]?',
    ]
    
    # Entity types for Graph RAG
    ENTITY_TYPES = {
        'PRODUCT': 'Product name (hardware/software)',
        'SOFTWARE': 'Software platform or operating system',
        'VERSION': 'Version number',
        'ERROR_CODE': 'Error code or KPR number',
        'PROBLEM': 'Problem or issue description',
        'SOLUTION': 'Solution or fix description',
        'CATEGORY': 'Content category',
        'PROTOCOL': 'Protocol or procedure',
        'INSTRUMENT': 'Laboratory instrument',
        'COMPANY': 'Company or organization name',
        'PERSON': 'Person name (author/contributor)',
    }
    
    def __init__(self):
        """Initialize entity extractor"""
        self.compiled_patterns = self._compile_patterns()
        self.ollama_url = getattr(settings, 'OLLAMA_API_URL', 'http://localhost:11434')
        self.model_name = getattr(settings, 'OLLAMA_MODEL', 'llama3:8b')
        self.use_llm_extraction = True  # Enable LLM-based extraction for concepts
        logger.info("GraphEntityExtractor initialized with LLM-based extraction")
    
    def _compile_patterns(self) -> Dict[str, List[re.Pattern]]:
        """Compile regex patterns for entity extraction"""
        return {
            'PRODUCT': [re.compile(pattern, re.IGNORECASE) for pattern in self.PRODUCT_PATTERNS],
            'VERSION': [re.compile(pattern, re.IGNORECASE) for pattern in self.VERSION_PATTERNS],
            'ERROR_CODE': [re.compile(pattern, re.IGNORECASE) for pattern in self.ERROR_CODE_PATTERNS],
            'SOFTWARE': [re.compile(pattern, re.IGNORECASE) for pattern in self.SOFTWARE_PATTERNS],
        }
    
    def extract_entities(self, content: str, document_id: str = None) -> List[ExtractedEntity]:
        """
        Extract entities from content using both pattern-based and LLM-based extraction
        
        Args:
            content: Document content text
            document_id: Optional document ID for context
            
        Returns:
            List of extracted entities
        """
        entities = []
        
        # Step 1: Extract using patterns (fast, reliable for known entities)
        pattern_entities = self._extract_with_patterns(content)
        entities.extend(pattern_entities)
        
        # Step 2: Extract problems and solutions (heuristic-based)
        problem_solution_entities = self._extract_problems_and_solutions(content)
        entities.extend(problem_solution_entities)
        
        # Step 3: LLM-based extraction for concepts and important information
        if self.use_llm_extraction and len(content) > 100:
            try:
                llm_entities = self._extract_with_llm(content)
                entities.extend(llm_entities)
                logger.info(f"LLM extraction found {len(llm_entities)} additional entities")
            except Exception as e:
                logger.warning(f"LLM extraction failed, continuing with pattern-based only: {e}")
        
        # Step 4: Extract key concepts and important information
        concept_entities = self._extract_key_concepts(content)
        entities.extend(concept_entities)
        
        # Normalize and deduplicate
        normalized_entities = self._normalize_entities(entities)
        
        # Add context
        for entity in normalized_entities:
            entity.context = self._get_entity_context(content, entity.start_pos, entity.end_pos)
        
        logger.info(f"Extracted {len(normalized_entities)} total entities from document {document_id}")
        
        return normalized_entities
    
    def _extract_with_patterns(self, content: str) -> List[ExtractedEntity]:
        """Extract entities using regex patterns"""
        entities = []
        
        for entity_type, patterns in self.compiled_patterns.items():
            for pattern in patterns:
                for match in pattern.finditer(content):
                    entity = ExtractedEntity(
                        text=match.group(0),
                        normalized_text=self._normalize_entity_text(match.group(0), entity_type),
                        entity_type=entity_type,
                        start_pos=match.start(),
                        end_pos=match.end(),
                        confidence=0.8,  # Pattern matches have high confidence
                        context="",
                        metadata={}
                    )
                    entities.append(entity)
        
        return entities
    
    def _extract_problems_and_solutions(self, content: str) -> List[ExtractedEntity]:
        """Extract problems and solutions concisely"""
        entities = []
        content_lower = content.lower()
        
        # Problem indicators
        problem_keywords = [
            'error', 'issue', 'problem', 'bug', 'failure', 'crash',
            'does not work', 'unable to', 'cannot', 'fails', 'broken'
        ]
        
        # Solution indicators
        solution_keywords = [
            'solution', 'fix', 'resolve', 'workaround', 'workaround',
            'steps to', 'procedure', 'how to fix', 'corrected by'
        ]
        
        # Simple heuristic: look for sentences containing problem keywords
        sentences = re.split(r'[.!?]\s+', content)
        
        for i, sentence in enumerate(sentences):
            sentence_lower = sentence.lower()
            
            # Check for problems
            if any(keyword in sentence_lower for keyword in problem_keywords):
                # Extract first 200 chars as problem description
                problem_text = sentence.strip()[:200]
                if len(problem_text) > 20:  # Minimum length
                    pos = content.find(sentence)
                    entities.append(ExtractedEntity(
                        text=problem_text,
                        normalized_text=problem_text.lower(),
                        entity_type='PROBLEM',
                        start_pos=pos if pos >= 0 else 0,
                        end_pos=pos + len(problem_text) if pos >= 0 else len(problem_text),
                        confidence=0.6,
                        context="",
                        metadata={'extraction_method': 'keyword_heuristic'}
                    ))
            
            # Check for solutions
            if any(keyword in sentence_lower for keyword in solution_keywords):
                solution_text = sentence.strip()[:200]
                if len(solution_text) > 20:
                    pos = content.find(sentence)
                    entities.append(ExtractedEntity(
                        text=solution_text,
                        normalized_text=solution_text.lower(),
                        entity_type='SOLUTION',
                        start_pos=pos if pos >= 0 else 0,
                        end_pos=pos + len(solution_text) if pos >= 0 else len(solution_text),
                        confidence=0.6,
                        context="",
                        metadata={'extraction_method': 'keyword_heuristic'}
                    ))
        
        return entities
    
    def _normalize_entity_text(self, text: str, entity_type: str) -> str:
        """Normalize entity text to canonical form"""
        normalized = text.strip()
        
        # Normalize case
        if entity_type in ['PRODUCT', 'SOFTWARE']:
            # Capitalize first letter of each word
            normalized = ' '.join(word.capitalize() for word in normalized.split())
        elif entity_type == 'VERSION':
            # Extract version number
            version_match = re.search(r'(\d+(?:\.\d+)*(?:\.\d+)?)', normalized)
            if version_match:
                normalized = f"v{version_match.group(1)}"
        elif entity_type == 'ERROR_CODE':
            # Uppercase error codes
            normalized = normalized.upper()
        else:
            # Default: lowercase
            normalized = normalized.lower()
        
        return normalized
    
    def _normalize_entities(self, entities: List[ExtractedEntity]) -> List[ExtractedEntity]:
        """Normalize and deduplicate entities"""
        seen = {}
        normalized = []
        
        for entity in entities:
            # Create unique key
            key = (entity.normalized_text.lower(), entity.entity_type)
            
            if key not in seen:
                seen[key] = entity
                normalized.append(entity)
            else:
                # Merge if better confidence
                existing = seen[key]
                if entity.confidence > existing.confidence:
                    seen[key] = entity
                    normalized.remove(existing)
                    normalized.append(entity)
        
        return normalized
    
    def _get_entity_context(self, content: str, start: int, end: int, context_window: int = 100) -> str:
        """Get surrounding context for an entity"""
        context_start = max(0, start - context_window)
        context_end = min(len(content), end + context_window)
        return content[context_start:context_end]
    
    def link_entities(self, entities: List[ExtractedEntity]) -> Dict[str, List[str]]:
        """
        Link related entities together
        
        Returns dictionary mapping entity IDs to related entity IDs
        """
        links = {}
        
        for i, entity in enumerate(entities):
            entity_id = self._generate_entity_id(entity)
            links[entity_id] = []
            
            # Link related entities (same type, co-occurring)
            for j, other_entity in enumerate(entities):
                if i != j:
                    # Link versions to products
                    if entity.entity_type == 'VERSION' and other_entity.entity_type == 'PRODUCT':
                        if abs(entity.start_pos - other_entity.start_pos) < 200:
                            links[entity_id].append(self._generate_entity_id(other_entity))
                    
                    # Link error codes to problems
                    if entity.entity_type == 'ERROR_CODE' and other_entity.entity_type == 'PROBLEM':
                        if abs(entity.start_pos - other_entity.start_pos) < 200:
                            links[entity_id].append(self._generate_entity_id(other_entity))
                    
                    # Link solutions to problems
                    if entity.entity_type == 'SOLUTION' and other_entity.entity_type == 'PROBLEM':
                        if abs(entity.start_pos - other_entity.start_pos) < 500:
                            links[entity_id].append(self._generate_entity_id(other_entity))
        
        return links
    
    def _extract_with_llm(self, content: str, max_length: int = 4000) -> List[ExtractedEntity]:
        """
        Extract entities using LLM for better concept understanding
        
        This extracts:
        - Key concepts and topics
        - Important technical terms
        - Main ideas and themes
        - Domain-specific concepts
        """
        entities = []
        
        # Truncate content if too long (to avoid token limits)
        content_sample = content[:max_length] if len(content) > max_length else content
        
        prompt = f"""Extract important entities, concepts, and key information from this technical documentation.

Focus on:
1. Key technical concepts and terms
2. Important procedures or methods
3. Main topics and themes
4. Critical information points
5. Domain-specific terminology

Return a JSON array of entities, each with:
- "text": the extracted text/phrase
- "type": one of: CONCEPT, KEY_TERM, PROCEDURE, TOPIC, IMPORTANT_INFO
- "importance": score from 0.0 to 1.0 (higher = more important)

Document content:
{content_sample}

Return ONLY valid JSON array, no other text:"""

        try:
            response = requests.post(
                f"{self.ollama_url}/api/chat",
                json={
                    "model": self.model_name,
                    "messages": [
                        {"role": "user", "content": prompt}
                    ],
                    "stream": False,
                    "options": {
                        "temperature": 0.1,  # Low temperature for consistent extraction
                        "num_predict": 2000,
                        "num_ctx": 4096
                    }
                },
                timeout=30
            )
            response.raise_for_status()
            response_text = response.json()["message"]["content"].strip()
            
            # Try to extract JSON from response (may have markdown code blocks)
            json_match = re.search(r'\[.*\]', response_text, re.DOTALL)
            if json_match:
                response_text = json_match.group(0)
            
            extracted_data = json.loads(response_text)
            
            # Convert to ExtractedEntity objects
            for idx, item in enumerate(extracted_data):
                if isinstance(item, dict) and 'text' in item:
                    text = item['text']
                    entity_type = item.get('type', 'CONCEPT')
                    importance = item.get('importance', 0.7)
                    
                    # Find position in original content
                    pos = content.find(text)
                    if pos == -1:
                        # Try to find similar text
                        pos = content.lower().find(text.lower())
                    
                    if pos >= 0:
                        entities.append(ExtractedEntity(
                            text=text,
                            normalized_text=text.lower().strip(),
                            entity_type=entity_type,
                            start_pos=pos,
                            end_pos=pos + len(text),
                            confidence=importance,
                            context="",
                            metadata={'extraction_method': 'llm', 'importance': importance}
                        ))
            
        except json.JSONDecodeError as e:
            logger.warning(f"Failed to parse LLM extraction JSON: {e}")
        except Exception as e:
            logger.warning(f"LLM extraction error: {e}")
        
        return entities
    
    def _extract_key_concepts(self, content: str) -> List[ExtractedEntity]:
        """
        Extract key concepts using heuristics for important information
        
        Looks for:
        - Summary sections
        - Conclusion sections
        - Key points (bulleted lists)
        - Important definitions
        """
        entities = []
        
        # Find summary/conclusion sections
        summary_patterns = [
            (r'(?:summary|conclusion|overview|key points?)[:.]?\s*\n(.{50,300})', 'IMPORTANT_INFO', 0.9),
            (r'(?:important|note|warning|caution)[:.]?\s*\n(.{30,200})', 'IMPORTANT_INFO', 0.85),
            (r'^\s*[•\-\*]\s+(.{20,150})', 'KEY_POINT', 0.8),  # Bullet points
            (r'(?:definition|defined as|means)[:.]?\s*(.{20,200})', 'CONCEPT', 0.75),
        ]
        
        for pattern, entity_type, confidence in summary_patterns:
            for match in re.finditer(pattern, content, re.IGNORECASE | re.MULTILINE):
                text = match.group(1).strip() if match.groups() else match.group(0).strip()
                if len(text) > 15:  # Minimum length
                    entities.append(ExtractedEntity(
                        text=text[:200],  # Limit length
                        normalized_text=text.lower().strip()[:200],
                        entity_type=entity_type,
                        start_pos=match.start(),
                        end_pos=match.end(),
                        confidence=confidence,
                        context="",
                        metadata={'extraction_method': 'heuristic_concept'}
                    ))
        
        return entities
    
    def _generate_entity_id(self, entity: ExtractedEntity) -> str:
        """Generate unique ID for an entity"""
        # Create hash-based ID
        key = f"{entity.normalized_text}:{entity.entity_type}"
        return hashlib.md5(key.encode()).hexdigest()[:12]

