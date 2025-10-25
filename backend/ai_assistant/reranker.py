"""
Result Reranking using Cross-Encoder and Advanced Scoring
"""
import logging
from typing import List, Dict, Tuple
import re
import hashlib
from django.core.cache import cache
from django.conf import settings

logger = logging.getLogger(__name__)

class CrossEncoderReranker:
    """Cross-encoder based reranking for better relevance"""
    
    def __init__(self):
        self.model = None
        self.device = 'cpu'
        self.use_lightweight = True
        
    def _load_model(self):
        """Load cross-encoder model if available"""
        try:
            # Try to use sentence-transformers cross-encoder
            from sentence_transformers import CrossEncoder
            
            # Use a lightweight cross-encoder model
            model_name = 'cross-encoder/ms-marco-MiniLM-L-2-v2'
            self.model = CrossEncoder(model_name, device=self.device)
            logger.info(f"Loaded cross-encoder model: {model_name}")
            return True
        except Exception as e:
            logger.warning(f"Could not load cross-encoder model: {e}")
            return False
    
    def rerank_with_cross_encoder(self, query: str, documents: List[Dict]) -> List[Dict]:
        """Rerank documents using cross-encoder model"""
        if not self.model and not self._load_model():
            # Fallback to rule-based reranking
            return self.rerank_with_rules(query, documents)
        
        try:
            # Prepare query-document pairs
            pairs = []
            for doc in documents:
                content = doc.get('content', '')[:512]  # Limit content length
                pairs.append([query, content])
            
            # Get cross-encoder scores
            scores = self.model.predict(pairs)
            
            # Add scores to documents
            reranked_docs = []
            for i, doc in enumerate(documents):
                enhanced_doc = doc.copy()
                enhanced_doc['cross_encoder_score'] = float(scores[i])
                reranked_docs.append(enhanced_doc)
            
            # Sort by cross-encoder score
            reranked_docs.sort(key=lambda x: x['cross_encoder_score'], reverse=True)
            
            logger.info(f"Cross-encoder reranking: {len(reranked_docs)} documents")
            return reranked_docs
            
        except Exception as e:
            logger.error(f"Cross-encoder reranking failed: {e}")
            return self.rerank_with_rules(query, documents)
    
    def rerank_with_rules(self, query: str, documents: List[Dict]) -> List[Dict]:
        """Rule-based reranking as fallback"""
        query_terms = set(query.lower().split())
        
        for doc in documents:
            content = doc.get('content', '').lower()
            filename = doc.get('filename', '').lower()
            
            # Calculate rule-based relevance score
            relevance_score = 0.0
            
            # 1. Exact phrase matching (highest weight)
            if query.lower() in content:
                relevance_score += 2.0
            
            # 2. Term frequency in content
            content_words = set(content.split())
            term_matches = len(query_terms.intersection(content_words))
            relevance_score += term_matches * 0.5
            
            # 3. Term frequency in filename
            filename_words = set(filename.split())
            filename_matches = len(query_terms.intersection(filename_words))
            relevance_score += filename_matches * 0.3
            
            # 4. Position bonus (earlier terms get higher score)
            for term in query_terms:
                pos = content.find(term)
                if pos >= 0:
                    # Earlier positions get higher bonus
                    position_bonus = max(0, 1.0 - (pos / len(content)))
                    relevance_score += position_bonus * 0.2
            
            # 5. Length penalty (very short or very long documents get penalty)
            content_length = len(content)
            if content_length < 50:
                relevance_score *= 0.8  # Too short
            elif content_length > 2000:
                relevance_score *= 0.9  # Too long
            
            doc['rule_based_score'] = relevance_score
        
        # Sort by rule-based score
        documents.sort(key=lambda x: x.get('rule_based_score', 0), reverse=True)
        
        logger.info(f"Rule-based reranking: {len(documents)} documents")
        return documents

class AdvancedReranker:
    """Advanced reranking combining multiple signals"""
    
    def __init__(self):
        self.cross_encoder = CrossEncoderReranker()
        
        # Reranking weights
        self.weights = {
            'hybrid_score': 0.4,      # From hybrid search
            'cross_encoder': 0.3,     # Cross-encoder relevance
            'freshness': 0.1,         # Document recency
            'quality': 0.1,           # Content quality indicators
            'user_feedback': 0.1      # User interaction signals
        }
    
    def calculate_freshness_score(self, doc: Dict) -> float:
        """Calculate freshness score based on document age"""
        # For now, return neutral score
        # In production, you'd use document upload/modification dates
        return 0.5
    
    def calculate_quality_score(self, doc: Dict) -> float:
        """Calculate content quality score"""
        content = doc.get('content', '')
        
        quality_score = 0.5  # Base score
        
        # Length indicators
        if 100 <= len(content) <= 1000:
            quality_score += 0.2  # Good length
        
        # Structure indicators
        if any(marker in content.lower() for marker in ['step', 'procedure', 'process']):
            quality_score += 0.1  # Structured content
        
        # Technical content indicators
        if any(term in content.lower() for term in ['configure', 'install', 'setup']):
            quality_score += 0.1  # Technical relevance
        
        # Completeness indicators
        if content.count('.') > 2:  # Multiple sentences
            quality_score += 0.1
        
        return min(quality_score, 1.0)
    
    def calculate_user_feedback_score(self, doc: Dict) -> float:
        """Calculate user feedback score (placeholder)"""
        # In production, this would use actual user feedback data
        return 0.5
    
    def advanced_rerank(self, query: str, documents: List[Dict]) -> List[Dict]:
        """Perform advanced reranking with multiple signals"""
        if not documents:
            return documents
        
        # Get cross-encoder scores
        cross_encoder_docs = self.cross_encoder.rerank_with_cross_encoder(query, documents)
        
        # Calculate additional scores
        final_docs = []
        for doc in cross_encoder_docs:
            enhanced_doc = doc.copy()
            
            # Get individual scores
            hybrid_score = doc.get('hybrid_score', doc.get('similarity', 0))
            cross_encoder_score = doc.get('cross_encoder_score', doc.get('rule_based_score', 0))
            freshness_score = self.calculate_freshness_score(doc)
            quality_score = self.calculate_quality_score(doc)
            feedback_score = self.calculate_user_feedback_score(doc)
            
            # Normalize cross-encoder score to 0-1 range
            if cross_encoder_score > 1:
                cross_encoder_score = 1.0
            elif cross_encoder_score < -1:
                cross_encoder_score = 0.0
            else:
                cross_encoder_score = (cross_encoder_score + 1) / 2
            
            # Calculate final reranking score
            final_score = (
                self.weights['hybrid_score'] * hybrid_score +
                self.weights['cross_encoder'] * cross_encoder_score +
                self.weights['freshness'] * freshness_score +
                self.weights['quality'] * quality_score +
                self.weights['user_feedback'] * feedback_score
            )
            
            enhanced_doc.update({
                'final_rerank_score': final_score,
                'freshness_score': freshness_score,
                'quality_score': quality_score,
                'feedback_score': feedback_score,
                'cross_encoder_score': cross_encoder_score
            })
            
            final_docs.append(enhanced_doc)
        
        # Final sort by reranking score
        final_docs.sort(key=lambda x: x['final_rerank_score'], reverse=True)
        
        logger.info(f"Advanced reranking complete: {len(final_docs)} documents, "
                   f"avg final score: {sum(d['final_rerank_score'] for d in final_docs) / len(final_docs):.3f}")
        
        return final_docs

class ContextOptimizer:
    """Optimize context generation for better RAG responses"""
    
    def __init__(self, max_context_length: int = 4000):
        self.max_context_length = max_context_length
    
    def optimize_context(self, query: str, documents: List[Dict]) -> str:
        """Generate optimized context from ranked documents"""
        if not documents:
            return ""
        
        context_parts = []
        current_length = 0
        
        # Add documents until we reach the context limit
        for i, doc in enumerate(documents, 1):
            content = doc.get('content', '')
            filename = doc.get('filename', 'Unknown')
            page = doc.get('page_number', 1)
            
            # Get relevance indicators
            hybrid_score = doc.get('hybrid_score', doc.get('similarity', 0))
            final_score = doc.get('final_rerank_score', hybrid_score)
            
            # Format document with metadata
            doc_header = f"[{i}] {filename} (Page {page}, Relevance: {final_score:.3f})"
            
            # Truncate content if needed
            available_length = self.max_context_length - current_length - len(doc_header) - 50
            if available_length <= 0:
                break
            
            if len(content) > available_length:
                # Smart truncation - try to end at sentence boundary
                truncated = content[:available_length]
                last_period = truncated.rfind('.')
                if last_period > available_length * 0.7:  # If we can keep 70% of content
                    truncated = truncated[:last_period + 1]
                else:
                    truncated = truncated + "..."
                content = truncated
            
            doc_text = f"{doc_header}\n{content}"
            context_parts.append(doc_text)
            current_length += len(doc_text) + 2  # +2 for newlines
            
            if current_length >= self.max_context_length:
                break
        
        optimized_context = "\n\n".join(context_parts)
        
        logger.info(f"Optimized context: {len(context_parts)} documents, {len(optimized_context)} characters")
        return optimized_context
    
    def generate_enhanced_prompt(self, query: str, context: str, query_type: str = 'general') -> str:
        """Generate enhanced prompt based on query type and context"""
        
        # Base instruction
        base_instruction = (
            "You are an expert technical assistant. Answer the user's question using ONLY the provided context.\n"
            "CRITICAL RULES:\n"
            "1. Use ONLY information from the context - never use external knowledge\n"
            "2. Cite sources using reference numbers [1], [2], etc.\n"
            "3. If information is not in context, say 'I don't know'\n"
            "4. Provide comprehensive, well-structured answers\n"
            "5. When multiple sources agree, synthesize the information\n"
            "6. Mention relevance scores when information quality varies significantly\n\n"
        )
        
        # Query-type specific instructions
        type_instructions = {
            'procedural': "Focus on step-by-step procedures and processes. Number the steps clearly.",
            'definitional': "Provide clear, comprehensive definitions with examples if available.",
            'troubleshooting': "Focus on problem identification and solution steps. Prioritize actionable advice.",
            'locational': "Specify exact locations, paths, or positions mentioned in the context.",
            'general': "Provide a comprehensive answer addressing all aspects of the question."
        }
        
        specific_instruction = type_instructions.get(query_type, type_instructions['general'])
        
        # Construct final prompt
        enhanced_prompt = (
            f"{base_instruction}"
            f"QUERY TYPE: {query_type.title()}\n"
            f"SPECIFIC GUIDANCE: {specific_instruction}\n\n"
            f"CONTEXT:\n{context}\n\n"
            f"QUESTION: {query}\n\n"
            f"ANSWER:"
        )
        
        return enhanced_prompt

# Global instances
advanced_reranker = AdvancedReranker()
context_optimizer = ContextOptimizer(max_context_length=4000)
