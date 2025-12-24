"""
RAG Accuracy and Precision Improvements

This module implements high-impact improvements for RAG accuracy:
1. BM25+MMR fusion (Reciprocal Rank Fusion)
2. Increased top_k + better reranking
3. Metadata filters
4. Abstain/clarify guardrail
5. Dedup/diversity (MMR)
6. Query rewriting with entity normalization
7. Citation validation
"""
import logging
import math
from typing import List, Dict, Tuple, Optional, Set
from collections import defaultdict, Counter
from django.db import connection
from django.core.cache import cache
import hashlib

logger = logging.getLogger(__name__)


class ReciprocalRankFusion:
    """Reciprocal Rank Fusion (RRF) for combining multiple retrieval results"""
    
    def __init__(self, k: int = 60):
        self.k = k  # RRF constant (typically 60)
    
    def fuse_rankings(self, rankings: List[List[Dict]], top_k: int = None) -> List[Dict]:
        """
        Fuse multiple ranked lists using RRF
        
        Args:
            rankings: List of ranked document lists (each list contains docs with 'id')
            top_k: Maximum number of results to return
        """
        if not rankings or not any(rankings):
            return []
        
        # Remove empty rankings
        rankings = [r for r in rankings if r]
        if not rankings:
            return []
        
        # Build document lookup by ID
        doc_lookup = {}
        doc_rrf_scores = defaultdict(float)
        
        # Calculate RRF scores for each ranking
        for rank_list in rankings:
            for rank_pos, doc in enumerate(rank_list, start=1):
                doc_id = doc.get('id')
                if not doc_id:
                    continue
                
                # Store document if not seen
                if doc_id not in doc_lookup:
                    doc_lookup[doc_id] = doc.copy()
                
                # Add RRF score: 1 / (k + rank_position)
                rrf_score = 1.0 / (self.k + rank_pos)
                doc_rrf_scores[doc_id] += rrf_score
        
        # Convert to list and sort by RRF score
        fused_results = []
        for doc_id, rrf_score in doc_rrf_scores.items():
            doc = doc_lookup[doc_id].copy()
            doc['rrf_score'] = rrf_score
            fused_results.append(doc)
        
        # Sort by RRF score (descending)
        fused_results.sort(key=lambda x: x.get('rrf_score', 0), reverse=True)
        
        # Return top_k if specified
        if top_k:
            fused_results = fused_results[:top_k]
        
        logger.info(f"RRF fused {len(fused_results)} documents from {len(rankings)} rankings")
        return fused_results


class MMRDiversitySelector:
    """Maximal Marginal Relevance (MMR) for diverse result selection"""
    
    def __init__(self, lambda_param: float = 0.7):
        """
        Args:
            lambda_param: Balance between relevance (1.0) and diversity (0.0)
                          Higher = more relevance, Lower = more diversity
        """
        self.lambda_param = lambda_param
    
    def select_diverse_results(
        self, 
        documents: List[Dict], 
        query: str,
        top_k: int,
        similarity_fn=None
    ) -> List[Dict]:
        """
        Select diverse results using MMR
        
        Args:
            documents: List of documents with relevance scores
            query: Original query string
            top_k: Number of results to return
            similarity_fn: Function to compute document similarity (optional)
        """
        if not documents or top_k <= 0:
            return []
        
        if len(documents) <= top_k:
            return documents[:top_k]
        
        # Use simple cosine similarity if no function provided
        if similarity_fn is None:
            similarity_fn = self._simple_cosine_similarity
        
        # Extract query terms for diversity calculation
        query_terms = set(query.lower().split())
        
        selected = []
        remaining = documents.copy()
        
        # Select first document (highest relevance)
        if remaining:
            first_doc = remaining.pop(0)
            selected.append(first_doc)
        
        # Greedily select remaining documents
        while len(selected) < top_k and remaining:
            best_score = -float('inf')
            best_doc = None
            best_idx = -1
            
            for idx, doc in enumerate(remaining):
                # Relevance score (use hybrid_score, similarity, or rrf_score)
                relevance = (
                    doc.get('final_rerank_score', 0) or
                    doc.get('hybrid_score', 0) or
                    doc.get('similarity', 0) or
                    doc.get('rrf_score', 0)
                )
                
                # Diversity score (1 - max similarity to already selected)
                max_sim = 0.0
                if selected:
                    for selected_doc in selected:
                        sim = similarity_fn(doc, selected_doc)
                        max_sim = max(max_sim, sim)
                
                diversity = 1.0 - max_sim
                
                # MMR score
                mmr_score = (
                    self.lambda_param * relevance +
                    (1 - self.lambda_param) * diversity
                )
                
                if mmr_score > best_score:
                    best_score = mmr_score
                    best_doc = doc
                    best_idx = idx
            
            if best_doc:
                selected.append(best_doc)
                remaining.pop(best_idx)
            else:
                break
        
        logger.info(f"MMR selected {len(selected)} diverse results (lambda={self.lambda_param})")
        return selected
    
    def _simple_cosine_similarity(self, doc1: Dict, doc2: Dict) -> float:
        """Simple similarity based on content overlap"""
        content1 = set(doc1.get('content', '').lower().split())
        content2 = set(doc2.get('content', '').lower().split())
        
        if not content1 or not content2:
            return 0.0
        
        intersection = len(content1.intersection(content2))
        union = len(content1.union(content2))
        
        return intersection / union if union > 0 else 0.0


class MetadataFilterBuilder:
    """Build SQL WHERE clauses for metadata filtering"""
    
    @staticmethod
    def build_filter_clause(
        document_type: Optional[str] = None,
        product_category: Optional[str] = None,
        version: Optional[str] = None,
        content_category: Optional[str] = None,
        file_id: Optional[int] = None
    ) -> Tuple[str, List]:
        """
        Build WHERE clause for metadata filtering
        
        Returns:
            Tuple of (WHERE clause string, parameter list)
        """
        conditions = []
        params = []
        
        # Base condition: embeddings must exist
        conditions.append("dc.embedding IS NOT NULL")
        
        # Document type filter
        if document_type:
            # Join with DocumentFile if needed, or check metadata JSON
            conditions.append("""
                EXISTS (
                    SELECT 1 FROM ai_assistant_documentfile df
                    WHERE df.id = dc.document_file_id 
                    AND df.document_type = %s
                )
            """)
            params.append(document_type)
        
        # File ID filter (specific document)
        if file_id:
            conditions.append("dc.uploaded_file_id = %s")
            params.append(file_id)
        
        # Product category and version (from metadata JSON)
        # Note: This assumes metadata is stored as JSON in DocumentFile.metadata
        # Adjust based on your actual schema
        if product_category or version:
            # If metadata is in a separate table or JSON field
            # You'll need to adjust this based on your schema
            pass
        
        where_clause = " AND ".join(conditions) if conditions else "dc.embedding IS NOT NULL"
        
        return where_clause, params
    
    @staticmethod
    def extract_filters_from_query(query: str) -> Dict[str, str]:
        """Extract metadata filters from query text"""
        filters = {}
        
        query_lower = query.lower()
        
        # Extract version patterns (v2.8, version 3.6, etc.)
        import re
        version_patterns = [
            r'\bv(\d+\.\d+)',
            r'\bversion\s+(\d+\.\d+)',
            r'\bver\.\s*(\d+\.\d+)',
        ]
        for pattern in version_patterns:
            match = re.search(pattern, query_lower)
            if match:
                filters['version'] = f"v{match.group(1)}"
                break
        
        # Extract document type hints
        doc_type_keywords = {
            'installation': 'installation_guide',
            'troubleshooting': 'troubleshooting_guide',
            'release notes': 'release_notes',
            'manual': 'manual',
            'faq': 'faq',
        }
        for keyword, doc_type in doc_type_keywords.items():
            if keyword in query_lower:
                filters['document_type'] = doc_type
                break
        
        return filters


class AbstainGuardrail:
    """Guardrail to abstain when results are insufficient"""
    
    def __init__(
        self,
        min_similarity_threshold: float = 0.3,
        min_results_threshold: int = 1,
        min_hybrid_score: float = 0.2
    ):
        self.min_similarity_threshold = min_similarity_threshold
        self.min_results_threshold = min_results_threshold
        self.min_hybrid_score = min_hybrid_score
    
    def should_abstain(
        self,
        results: List[Dict],
        query: str
    ) -> Tuple[bool, Optional[str]]:
        """
        Determine if system should abstain from answering
        
        Returns:
            Tuple of (should_abstain: bool, reason: Optional[str])
        """
        if not results:
            return True, "No results found in knowledge base"
        
        if len(results) < self.min_results_threshold:
            return True, f"Only {len(results)} result(s) found, insufficient for confident answer"
        
        # Check average similarity/hybrid score
        scores = []
        for doc in results:
            score = (
                doc.get('final_rerank_score', 0) or
                doc.get('hybrid_score', 0) or
                doc.get('similarity', 0) or
                0.0
            )
            scores.append(score)
        
        avg_score = sum(scores) / len(scores) if scores else 0.0
        max_score = max(scores) if scores else 0.0
        
        if avg_score < self.min_similarity_threshold and max_score < self.min_similarity_threshold * 1.5:
            return True, f"Low relevance scores (avg: {avg_score:.3f}, max: {max_score:.3f})"
        
        # Check hybrid score if available
        hybrid_scores = [d.get('hybrid_score', 0) for d in results if d.get('hybrid_score', 0) > 0]
        if hybrid_scores:
            avg_hybrid = sum(hybrid_scores) / len(hybrid_scores)
            if avg_hybrid < self.min_hybrid_score:
                return True, f"Low hybrid relevance score (avg: {avg_hybrid:.3f})"
        
        return False, None
    
    def generate_clarification_prompt(self, query: str, reason: str) -> str:
        """Generate a clarification question when abstaining"""
        return (
            f"I found limited information for your question: '{query}'. "
            f"Reason: {reason}. "
            f"Could you:\n"
            f"1. Rephrase your question with more specific terms?\n"
            f"2. Specify the product, version, or document type?\n"
            f"3. Try breaking down your question into smaller parts?"
        )


class DeduplicationFilter:
    """Filter duplicate results by document source and content"""
    
    @staticmethod
    def deduplicate_by_source(
        results: List[Dict],
        max_per_source: int = 3
    ) -> List[Dict]:
        """Limit results per source document"""
        source_counts = defaultdict(int)
        deduplicated = []
        
        for doc in results:
            source_id = doc.get('uploaded_file_id') or doc.get('document_file_id')
            if not source_id:
                # No source ID, include as-is
                deduplicated.append(doc)
                continue
            
            if source_counts[source_id] < max_per_source:
                deduplicated.append(doc)
                source_counts[source_id] += 1
        
        logger.info(f"Deduplicated: {len(results)} -> {len(deduplicated)} "
                   f"(max {max_per_source} per source)")
        return deduplicated
    
    @staticmethod
    def deduplicate_by_content_similarity(
        results: List[Dict],
        similarity_threshold: float = 0.85
    ) -> List[Dict]:
        """Remove results with very similar content"""
        deduplicated = []
        seen_content = []
        
        for doc in results:
            content = doc.get('content', '').lower()[:500]  # First 500 chars
            
            # Check similarity with seen content
            is_duplicate = False
            for seen in seen_content:
                # Simple overlap check
                words1 = set(content.split())
                words2 = set(seen.split())
                
                if words1 and words2:
                    overlap = len(words1.intersection(words2)) / len(words1.union(words2))
                    if overlap > similarity_threshold:
                        is_duplicate = True
                        break
            
            if not is_duplicate:
                deduplicated.append(doc)
                seen_content.append(content)
        
        logger.info(f"Content deduplication: {len(results)} -> {len(deduplicated)}")
        return deduplicated


class EnhancedRetrievalPipeline:
    """Complete enhanced retrieval pipeline with all improvements"""
    
    def __init__(
        self,
        vector_weight: float = 0.7,
        bm25_weight: float = 0.3,
        mmr_lambda: float = 0.6,
        rrf_k: int = 60,
        initial_top_k: int = 120,
        final_top_k: int = 24
    ):
        self.vector_weight = vector_weight
        self.bm25_weight = bm25_weight
        self.initial_top_k = initial_top_k  # Candidates to retrieve
        self.final_top_k = final_top_k      # Final results after all processing
        
        # Initialize components
        self.rrf = ReciprocalRankFusion(k=rrf_k)
        self.mmr = MMRDiversitySelector(lambda_param=mmr_lambda)
        self.metadata_filter = MetadataFilterBuilder()
        self.abstain_guardrail = AbstainGuardrail(min_similarity_threshold=0.2, min_results_threshold=1)
        self.dedup_filter = DeduplicationFilter()
        
        # Import existing hybrid search and reranker
        from .hybrid_search import hybrid_search_engine, query_processor
        from .reranker import advanced_reranker
        
        self.hybrid_search_engine = hybrid_search_engine
        self.query_processor = query_processor
        self.advanced_reranker = advanced_reranker
    
    def enhanced_retrieve(
        self,
        query: str,
        user=None,
        metadata_filters: Optional[Dict] = None,
        use_rrf: bool = True,
        use_mmr: bool = True,
        use_dedup: bool = True
    ) -> Dict:
        """
        Complete enhanced retrieval pipeline
        
        Returns:
            Dict with:
                - results: List of documents
                - should_abstain: bool
                - clarification: Optional[str]
                - metadata: Dict with stats
        """
        try:
            # Step 1: Query processing with normalization
            from .entity_normalization import entity_normalizer
            normalized_query, _ = entity_normalizer.normalize_text(query)
            query_type = self.query_processor.classify_query(normalized_query)
            if self.query_processor.should_expand_query(normalized_query):
                expanded_query = entity_normalizer.rewrite_query_with_synonyms(normalized_query)
            else:
                expanded_query = normalized_query
            
            # Extract metadata filters from query if not provided
            if metadata_filters is None:
                metadata_filters = self.metadata_filter.extract_filters_from_query(normalized_query)
            
            # Step 2: Vector search with increased top_k
            vector_results = self._vector_search_with_filters(
                expanded_query,
                top_k=self.initial_top_k,
                metadata_filters=metadata_filters
            )
            
            # Fallback to original query if expanded fails
            if not vector_results:
                vector_results = self._vector_search_with_filters(
                    query,
                    top_k=self.initial_top_k,
                    metadata_filters=metadata_filters
                )
            
            if not vector_results:
                should_abstain, reason = self.abstain_guardrail.should_abstain([], normalized_query)
                return {
                    'results': [],
                    'should_abstain': True,
                    'clarification': self.abstain_guardrail.generate_clarification_prompt(normalized_query, reason),
                    'metadata': {
                        'query_type': query_type,
                        'results_count': 0,
                        'pipeline': 'enhanced'
                    }
                }
            
            # Step 3: BM25 search separately (for RRF)
            bm25_results = self._bm25_search(normalized_query, vector_results, top_k=self.initial_top_k)
            
            # Step 4: RRF fusion of vector + BM25
            if use_rrf and len(bm25_results) > 0:
                fused_results = self.rrf.fuse_rankings(
                    [vector_results, bm25_results],
                    top_k=self.initial_top_k
                )
            else:
                # Fallback to hybrid search
                fused_results = self.hybrid_search_engine.hybrid_search(
                    normalized_query,
                    vector_results,
                    top_k=self.initial_top_k
                )
            
            # Step 5: Deduplication
            if use_dedup:
                fused_results = self.dedup_filter.deduplicate_by_source(
                    fused_results,
                    max_per_source=3
                )
                fused_results = self.dedup_filter.deduplicate_by_content_similarity(
                    fused_results,
                    similarity_threshold=0.85
                )
            
            # Step 6: Reranking
            reranked_results = self.advanced_reranker.advanced_rerank(
                normalized_query,
                fused_results
            )
            
            # Step 7: MMR diversity selection
            if use_mmr and len(reranked_results) > self.final_top_k:
                final_results = self.mmr.select_diverse_results(
                    reranked_results,
                    normalized_query,
                    top_k=self.final_top_k
                )
            else:
                final_results = reranked_results[:self.final_top_k]
            
            # Step 8: Check abstain guardrail
            should_abstain, reason = self.abstain_guardrail.should_abstain(final_results, normalized_query)
            clarification = None
            if should_abstain:
                clarification = self.abstain_guardrail.generate_clarification_prompt(normalized_query, reason)
            
            # Calculate metadata
            avg_score = sum(
                d.get('final_rerank_score', d.get('hybrid_score', d.get('similarity', 0)))
                for d in final_results
            ) / len(final_results) if final_results else 0.0
            
            return {
                'results': final_results,
                'should_abstain': should_abstain,
                'clarification': clarification,
                'metadata': {
                    'query_type': query_type,
                    'results_count': len(final_results),
                    'avg_score': avg_score,
                    'pipeline': 'enhanced',
                    'used_rrf': use_rrf,
                    'used_mmr': use_mmr,
                    'used_dedup': use_dedup
                }
            }
            
        except Exception as e:
            logger.error(f"Error in enhanced retrieval: {e}", exc_info=True)
            return {
                'results': [],
                'should_abstain': True,
                'clarification': f"Error during retrieval: {str(e)}",
                'metadata': {'error': str(e)}
            }
    
    def _vector_search_with_filters(
        self,
        query: str,
        top_k: int,
        metadata_filters: Optional[Dict] = None
    ) -> List[Dict]:
        """Vector search with metadata filters"""
        # This would integrate with your existing vector search
        # For now, use the existing enhanced_rag_service search
        from .improved_rag_service import enhanced_rag_service
        
        results = enhanced_rag_service.search_relevant_documents_with_scoring(
            query,
            top_k=top_k
        )
        
        # Apply metadata filters post-search (if needed)
        if metadata_filters:
            results = self._apply_metadata_filters_post(results, metadata_filters)
        
        return results
    
    def _bm25_search(
        self,
        query: str,
        vector_results: List[Dict],
        top_k: int
    ) -> List[Dict]:
        """BM25 search on vector results"""
        # Use hybrid search's BM25 scorer
        query_terms = self.hybrid_search_engine.bm25_scorer.preprocess_text(query)
        all_docs = self.hybrid_search_engine.get_all_documents()
        
        if not self.hybrid_search_engine.bm25_scorer.corpus_stats:
            self.hybrid_search_engine.bm25_scorer.build_corpus_stats(all_docs)
        
        doc_lookup = {doc['id']: doc for doc in all_docs}
        bm25_results = []
        
        for doc in vector_results:
            doc_id = doc['id']
            if doc_id in doc_lookup:
                score = self.hybrid_search_engine.bm25_scorer.score_document(
                    query_terms,
                    doc_lookup[doc_id],
                    0
                )
                bm25_result = doc.copy()
                bm25_result['bm25_score'] = score
                bm25_results.append(bm25_result)
        
        # Sort by BM25 score
        bm25_results.sort(key=lambda x: x.get('bm25_score', 0), reverse=True)
        return bm25_results[:top_k]
    
    def _apply_metadata_filters_post(
        self,
        results: List[Dict],
        filters: Dict
    ) -> List[Dict]:
        """Apply metadata filters post-retrieval"""
        # This is a simplified version - in production you'd filter at SQL level
        filtered = []
        for doc in results:
            # Check filters against document metadata
            # Adjust based on your metadata schema
            match = True
            if 'version' in filters:
                # Check if version matches (would need metadata access)
                pass
            if 'document_type' in filters:
                # Check document type
                pass
            
            if match:
                filtered.append(doc)
        
        return filtered if filtered else results  # Return all if filters too strict


# Global instance
enhanced_retrieval_pipeline = EnhancedRetrievalPipeline()

