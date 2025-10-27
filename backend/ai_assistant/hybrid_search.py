"""
Hybrid Search Implementation combining BM25 and Vector Similarity
"""
import math
import re
import logging
from typing import List, Dict, Tuple, Optional
from collections import defaultdict, Counter
from django.db import connection
from django.core.cache import cache
import hashlib
import numpy as np

logger = logging.getLogger(__name__)

class BM25Scorer:
    """BM25 (Best Matching 25) algorithm for keyword-based relevance scoring"""
    
    def __init__(self, k1: float = 1.5, b: float = 0.75):
        self.k1 = k1  # Term frequency saturation parameter
        self.b = b    # Length normalization parameter
        self.corpus_stats = None
        self.doc_frequencies = None
        self.avg_doc_length = 0
        
    def preprocess_text(self, text: str) -> List[str]:
        """Preprocess text for BM25 scoring"""
        # Convert to lowercase and extract words
        text = text.lower()
        # Remove punctuation and split on whitespace
        words = re.findall(r'\b[a-zA-Z]{2,}\b', text)
        return words
    
    def build_corpus_stats(self, documents: List[Dict]):
        """Build corpus statistics for BM25 scoring"""
        cache_key = "bm25_corpus_stats"
        cached_stats = cache.get(cache_key)
        
        if cached_stats:
            self.corpus_stats, self.doc_frequencies, self.avg_doc_length = cached_stats
            return
        
        logger.info("Building BM25 corpus statistics...")
        
        # Document frequencies: how many documents contain each term
        doc_frequencies = defaultdict(int)
        doc_lengths = []
        total_docs = len(documents)
        
        for doc in documents:
            content = doc.get('content', '')
            words = self.preprocess_text(content)
            doc_lengths.append(len(words))
            
            # Count unique terms in this document
            unique_terms = set(words)
            for term in unique_terms:
                doc_frequencies[term] += 1
        
        self.doc_frequencies = dict(doc_frequencies)
        self.avg_doc_length = sum(doc_lengths) / len(doc_lengths) if doc_lengths else 0
        self.corpus_stats = {
            'total_docs': total_docs,
            'doc_lengths': doc_lengths,
            'avg_doc_length': self.avg_doc_length
        }
        
        # Cache for 1 hour
        cache.set(cache_key, (self.corpus_stats, self.doc_frequencies, self.avg_doc_length), 3600)
        logger.info(f"Built BM25 stats: {total_docs} docs, avg length: {self.avg_doc_length:.1f}")
    
    def score_document(self, query_terms: List[str], document: Dict, doc_index: int) -> float:
        """Calculate BM25 score for a document given query terms"""
        if not self.corpus_stats:
            return 0.0
        
        content = document.get('content', '')
        doc_words = self.preprocess_text(content)
        doc_length = len(doc_words)
        
        if doc_length == 0:
            return 0.0
        
        # Count term frequencies in document
        term_frequencies = Counter(doc_words)
        total_docs = self.corpus_stats['total_docs']
        
        score = 0.0
        for term in query_terms:
            if term not in self.doc_frequencies:
                continue
                
            # Term frequency in document
            tf = term_frequencies.get(term, 0)
            if tf == 0:
                continue
            
            # Document frequency (how many docs contain this term)
            df = self.doc_frequencies[term]
            
            # Inverse document frequency
            idf = math.log((total_docs - df + 0.5) / (df + 0.5))
            
            # BM25 formula
            numerator = tf * (self.k1 + 1)
            denominator = tf + self.k1 * (1 - self.b + self.b * (doc_length / self.avg_doc_length))
            
            score += idf * (numerator / denominator)
        
        return score

class HybridSearchEngine:
    """Hybrid search combining BM25 and vector similarity"""
    
    def __init__(self, vector_weight: float = 0.7, bm25_weight: float = 0.3):
        self.vector_weight = vector_weight
        self.bm25_weight = bm25_weight
        self.bm25_scorer = BM25Scorer()
        
    def get_all_documents(self) -> List[Dict]:
        """Retrieve all document chunks for BM25 corpus building"""
        cache_key = "hybrid_search_documents"
        cached_docs = cache.get(cache_key)
        
        if cached_docs:
            return cached_docs
        
        with connection.cursor() as cursor:
            cursor.execute("""
                SELECT dc.id, dc.content, dc.uploaded_file_id, dc.page_number, dc.chunk_index,
                       COALESCE(uf.filename, 'Unknown Document') as filename,
                       COALESCE(uf.file_hash, '') as file_hash, 
                       COALESCE(uf.file_size, 0) as file_size
                FROM ai_assistant_documentchunk dc
                LEFT JOIN ai_assistant_uploadedfile uf ON dc.uploaded_file_id = uf.id
                WHERE dc.embedding IS NOT NULL AND dc.content IS NOT NULL
                ORDER BY dc.id;
            """)
            results = cursor.fetchall()
        
        documents = []
        for row in results:
            uploaded_file_id = row[2]
            page_number = row[3] or 1
            filename = row[5] or "Unknown Document"
            content = row[1]
            
            # Generate title: use filename if valid, otherwise extract from content
            if filename and filename != "Unknown Document":
                title = filename
            else:
                # Extract first meaningful words from content as title
                words = content.split()[:10]  # First 10 words
                title = " ".join(words)
                if len(title) > 100:
                    title = title[:100] + "..."
            
            # Create view URL for PDF viewer
            view_url = None
            if uploaded_file_id:
                view_url = f"/api/ai/pdf/{uploaded_file_id}/view/?page={page_number}"
            
            documents.append({
                "id": row[0],
                "content": content,
                "uploaded_file_id": uploaded_file_id,
                "page_number": page_number,
                "chunk_index": row[4],
                "filename": filename,
                "title": title,  # Smart title: filename or content excerpt
                "file_hash": row[6],
                "file_size": row[7],
                "view_url": view_url,
                "source_display": f"{filename} (Page {page_number})" if filename != "Unknown Document" else f"Page {page_number}"
            })
        
        # Cache for 30 minutes
        cache.set(cache_key, documents, 1800)
        return documents
    
    def normalize_scores(self, scores: List[float]) -> List[float]:
        """Normalize scores to 0-1 range"""
        if not scores:
            return scores
        
        min_score = min(scores)
        max_score = max(scores)
        
        if max_score == min_score:
            return [1.0] * len(scores)
        
        return [(score - min_score) / (max_score - min_score) for score in scores]
    
    def hybrid_search(self, query: str, vector_results: List[Dict], top_k: int = 10) -> List[Dict]:
        """Perform hybrid search combining vector similarity and BM25"""
        if not vector_results:
            return []
        
        try:
            # Get all documents for BM25
            all_documents = self.get_all_documents()
            
            # Build BM25 corpus statistics if needed
            if not self.bm25_scorer.corpus_stats:
                self.bm25_scorer.build_corpus_stats(all_documents)
            
            # Create document lookup for BM25 scoring
            doc_lookup = {doc['id']: doc for doc in all_documents}
            
            # Preprocess query for BM25
            query_terms = self.bm25_scorer.preprocess_text(query)
            
            # Calculate hybrid scores
            hybrid_results = []
            vector_similarities = [doc.get('similarity', 0) for doc in vector_results]
            bm25_scores = []
            
            # Calculate BM25 scores for vector results
            for doc in vector_results:
                doc_id = doc['id']
                if doc_id in doc_lookup:
                    bm25_score = self.bm25_scorer.score_document(query_terms, doc_lookup[doc_id], 0)
                    bm25_scores.append(bm25_score)
                else:
                    bm25_scores.append(0.0)
            
            # Normalize both score types
            normalized_vector = self.normalize_scores(vector_similarities)
            normalized_bm25 = self.normalize_scores(bm25_scores)
            
            # Combine scores
            for i, doc in enumerate(vector_results):
                vector_score = normalized_vector[i]
                bm25_score = normalized_bm25[i]
                
                # Hybrid score combination
                hybrid_score = (self.vector_weight * vector_score + 
                               self.bm25_weight * bm25_score)
                
                # Add scoring details to document
                enhanced_doc = doc.copy()
                enhanced_doc.update({
                    'hybrid_score': hybrid_score,
                    'vector_score': vector_score,
                    'bm25_score': bm25_score,
                    'original_similarity': doc.get('similarity', 0)
                })
                hybrid_results.append(enhanced_doc)
            
            # Sort by hybrid score (descending)
            hybrid_results.sort(key=lambda x: x['hybrid_score'], reverse=True)
            
            # Return top-k results
            final_results = hybrid_results[:top_k]
            
            logger.info(f"Hybrid search: {len(final_results)} results, "
                       f"avg hybrid score: {sum(r['hybrid_score'] for r in final_results) / len(final_results):.3f}")
            
            return final_results
            
        except Exception as e:
            logger.error(f"Error in hybrid search: {e}")
            # Fallback to vector results
            return vector_results[:top_k]

class QueryProcessor:
    """Advanced query processing with adaptive expansion"""
    
    def __init__(self):
        self.stop_words = {
            'the', 'a', 'an', 'and', 'or', 'but', 'in', 'on', 'at', 'to', 'for', 
            'of', 'with', 'by', 'is', 'are', 'was', 'were', 'be', 'been', 'have',
            'has', 'had', 'do', 'does', 'did', 'will', 'would', 'could', 'should',
            'may', 'might', 'can', 'this', 'that', 'these', 'those', 'i', 'you',
            'he', 'she', 'it', 'we', 'they', 'me', 'him', 'her', 'us', 'them'
        }
        
        # Technical synonyms for better search
        self.synonyms = {
            'install': ['installation', 'setup', 'configure', 'deploy'],
            'error': ['problem', 'issue', 'failure', 'bug'],
            'configure': ['configuration', 'setup', 'setting', 'config'],
            'connect': ['connection', 'link', 'attach', 'join'],
            'start': ['begin', 'launch', 'run', 'execute'],
            'stop': ['end', 'terminate', 'halt', 'shutdown'],
            'update': ['upgrade', 'modify', 'change', 'refresh']
        }
    
    def extract_key_terms(self, query: str) -> List[str]:
        """Extract key terms from query, removing stop words"""
        words = re.findall(r'\b[a-zA-Z]{2,}\b', query.lower())
        return [word for word in words if word not in self.stop_words]
    
    def should_expand_query(self, query: str) -> bool:
        """Determine if query should be expanded based on its characteristics"""
        # Check if query contains exact phrases (quoted strings)
        if '"' in query:
            return False  # Exact phrases should not be expanded
        
        # Count significant words (non-stop words)
        significant_words = self.extract_key_terms(query)
        word_count = len(significant_words)
        
        # Don't expand very specific queries (too many terms)
        if word_count > 8:
            return False
        
        # Do expand very short queries (need more context)
        if word_count < 3:
            return True
        
        # Don't expand if query contains technical terms that should be exact
        technical_exact_terms = ['version', 'ip', 'url', 'api', 'id', 'uuid', 'hash']
        query_lower = query.lower()
        if any(term in query_lower for term in technical_exact_terms):
            return False
        
        # Check for specific question patterns that might not benefit from expansion
        specific_patterns = [
            r'^what is (the )?\w+$',  # "what is x" - definitional
            r'^where is (the )?\w+$',  # "where is x" - locational
            r'^when did \w+',          # "when did x" - temporal
        ]
        for pattern in specific_patterns:
            if re.match(pattern, query.lower()):
                return False
        
        # Default: expand for better recall
        return True
    
    def expand_query(self, query: str) -> str:
        """Expand query with synonyms for better matching (with adaptive logic)"""
        # Check if expansion should be applied
        if not self.should_expand_query(query):
            logger.debug(f"Skipping expansion for specific query: {query[:50]}")
            return query
        
        words = query.lower().split()
        expanded_terms = []
        
        for word in words:
            expanded_terms.append(word)
            # Add synonyms if available
            if word in self.synonyms:
                expanded_terms.extend(self.synonyms[word])
        
        # Create expanded query (original + synonyms)
        expanded = ' '.join(expanded_terms)
        logger.debug(f"Query expansion: '{query}' -> '{expanded[:100]}'")
        return expanded
    
    def classify_query(self, query: str) -> str:
        """Classify query type for better processing"""
        query_lower = query.lower()
        
        if any(word in query_lower for word in ['how to', 'how do', 'steps', 'process', 'procedure']):
            return 'procedural'
        elif any(word in query_lower for word in ['what is', 'what are', 'define', 'definition']):
            return 'definitional'
        elif any(word in query_lower for word in ['error', 'problem', 'issue', 'troubleshoot', 'fix']):
            return 'troubleshooting'
        elif any(word in query_lower for word in ['where', 'location', 'find']):
            return 'locational'
        else:
            return 'general'

# Global instances
hybrid_search_engine = HybridSearchEngine(vector_weight=0.7, bm25_weight=0.3)
query_processor = QueryProcessor()
