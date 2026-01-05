# Implementation Plan: Workflow Improvements & Bug Fixes

**Date:** 2026-01-04  
**Status:** Planning Phase  
**Priority:** High

---

## Overview

This document outlines the implementation plan for fixing bugs and improving the file upload-to-processing workflow. The plan is organized by priority with clear steps, dependencies, and testing requirements.

---

## Phase 1: Critical Bug Fixes (Do First)

### 1.1 Fix DocumentFile Signal Bug ⚠️ CRITICAL

**Issue:** DocumentFile signal passes wrong ID, causing duplicate processing  
**Impact:** Duplicate chunks created (2x storage, 2x processing time)  
**Files:** `backend/ai_assistant/signals.py`

**Changes:**
```python
# Line 68-86: auto_process_document_file signal
@receiver(post_save, sender=DocumentFile)
def auto_process_document_file(sender, instance, created, **kwargs):
    if created:
        try:
            # Check if file needs processing (status is pending)
            status = instance.get_processing_status()
            if status.get('status') == 'pending' and not status.get('is_ready'):
                # FIX: Check if UploadedFile is already being processed
                if instance.uploaded_file and instance.uploaded_file.processing_status in ['processing', 'metadata_extracting', 'chunking', 'embedding']:
                    logger.info(f"DocumentFile {instance.id} linked to UploadedFile {instance.uploaded_file.id} already being processed. Skipping duplicate trigger.")
                    return
                
                # FIX: Use UploadedFile ID, not DocumentFile ID
                if instance.uploaded_file:
                    from .tasks import process_file_automatically
                    logger.info(f"Auto-processing DocumentFile: {instance.filename} (UploadedFile ID: {instance.uploaded_file.id}, async=True)")
                    process_file_automatically.delay(instance.uploaded_file.id)  # ✅ FIXED: Use uploaded_file.id
                    logger.info(f"Scheduled background processing for UploadedFile {instance.uploaded_file.id}")
                else:
                    logger.warning(f"DocumentFile {instance.id} has no linked UploadedFile, cannot trigger processing")
        except Exception as e:
            logger.error(f"Error processing DocumentFile: {e}", exc_info=True)
```

**Testing:**
1. Upload a new file
2. Verify only ONE set of chunks created (not duplicates)
3. Check logs for "Skipping duplicate trigger" message
4. Verify processing completes in expected time (not 2x)

**Estimated Time:** 30 minutes  
**Risk:** Low (isolated change)

---

## Phase 2: High Priority Performance Improvements

### 2.1 Implement Bulk Insert for DocumentChunk Creation

**Issue:** Sequential `create()` calls are slow (159 individual database writes)  
**Impact:** 50-70% reduction in database write time  
**Files:** `backend/ai_assistant/processors/embeddings/embedding_generator.py`

**Changes:**
```python
# Line 93-108: Replace individual creates with bulk_create
def generate_embeddings(self, chunks_data, uploaded_file):
    embedding_count = 0
    
    try:
        valid_chunks = [chunk for chunk in chunks_data if chunk['content'].strip()]
        total_batches = (len(valid_chunks) + self.batch_size - 1) // self.batch_size
        
        logger.info(f"Processing {len(valid_chunks)} chunks in {total_batches} batches for {uploaded_file.filename}")
        
        # NEW: Collect all chunks for bulk insert
        chunks_to_create = []
        
        for batch_idx in range(0, len(valid_chunks), self.batch_size):
            batch = valid_chunks[batch_idx:batch_idx + self.batch_size]
            current_batch = batch_idx // self.batch_size + 1
            
            logger.info(f"Processing batch {current_batch}/{total_batches} ({len(batch)} chunks)")
            
            # Extract batch content and clean null bytes
            batch_texts = []
            for chunk in batch:
                text = chunk['content']
                if isinstance(text, str):
                    text = text.replace('\x00', '').replace('\0', '')
                    text = ''.join(char for char in text if ord(char) >= 32 or char in ['\n', '\r', '\t'])
                batch_texts.append(text)
            
            # Get batch embeddings
            batch_embeddings = self.ollama_embedding.get_embeddings_batch(batch_texts)
            
            # NEW: Prepare chunks for bulk insert instead of individual creates
            for chunk_data, embedding in zip(batch, batch_embeddings):
                cleaned_content = chunk_data['content']
                if isinstance(cleaned_content, str):
                    cleaned_content = cleaned_content.replace('\x00', '').replace('\0', '')
                    cleaned_content = ''.join(char for char in cleaned_content if ord(char) >= 32 or char in ['\n', '\r', '\t'])
                
                chunks_to_create.append(
                    DocumentChunk(
                        uploaded_file=uploaded_file,
                        content=cleaned_content,
                        embedding=embedding,
                        page_number=chunk_data.get('page_number', 1),
                        chunk_index=embedding_count
                    )
                )
                embedding_count += 1
            
            # NEW: Bulk insert every 500 chunks or at end of batch
            if len(chunks_to_create) >= 500 or batch_idx + self.batch_size >= len(valid_chunks):
                DocumentChunk.objects.bulk_create(chunks_to_create, batch_size=500)
                logger.debug(f"Bulk inserted {len(chunks_to_create)} chunks (total: {embedding_count})")
                chunks_to_create = []  # Reset for next batch
            
            # Log progress every 100 chunks
            if embedding_count % 100 == 0:
                logger.info(f"Generated {embedding_count}/{len(valid_chunks)} embeddings for {uploaded_file.filename}")
        
        # NEW: Insert any remaining chunks
        if chunks_to_create:
            DocumentChunk.objects.bulk_create(chunks_to_create, batch_size=500)
            logger.debug(f"Bulk inserted final {len(chunks_to_create)} chunks")
        
        logger.info(f"Total embeddings created: {embedding_count}")
        return embedding_count
        
    except Exception as e:
        error_msg = (
            f"Embedding generation failed for {uploaded_file.filename} (ID: {uploaded_file.id}). "
            f"Error: {str(e)}. "
            f"Progress: {embedding_count}/{len(valid_chunks)} embeddings created before failure. "
            f"Please check Ollama is running at {self.ollama_embedding.ollama_url} and try again."
        )
        logger.error(error_msg, exc_info=True)
        raise Exception(error_msg) from e
```

**Testing:**
1. Upload file with 159 chunks
2. Monitor database write time (should be < 1 second instead of 2-3 seconds)
3. Verify all chunks created correctly
4. Check chunk_index ordering is correct

**Estimated Time:** 1 hour  
**Risk:** Medium (database operation change, need to verify bulk_create works with pgvector)

---

### 2.2 Add Progress Updates During Embedding

**Issue:** Status stuck at 'embedding' for entire duration, no visibility  
**Impact:** Better user experience, real-time progress tracking  
**Files:** `backend/ai_assistant/processors/embeddings/embedding_generator.py`, `backend/ai_assistant/automatic_file_processor.py`

**Changes:**

**File 1: `embedding_generator.py`**
```python
# Modify generate_embeddings to accept progress callback
def generate_embeddings(self, chunks_data, uploaded_file, progress_callback=None):
    # ... existing code ...
    
    # After each batch completion:
    if progress_callback:
        progress_callback(embedding_count, len(valid_chunks))
```

**File 2: `automatic_file_processor.py`**
```python
# Line 260-261: Add progress callback
def _update_embedding_progress(uploaded_file, current_count, total_count):
    """Update embedding progress in database"""
    uploaded_file.embedding_count = current_count
    uploaded_file.save(update_fields=['embedding_count'])
    logger.debug(f"Embedding progress: {current_count}/{total_count} ({current_count/total_count*100:.1f}%)")

# Step 4: Generate embeddings with progress callback
embedding_count = self.embedding_generator.generate_embeddings(
    chunks_data, 
    uploaded_file,
    progress_callback=lambda current, total: _update_embedding_progress(uploaded_file, current, total)
)
```

**Testing:**
1. Upload file and monitor `embedding_count` field in database
2. Verify it updates every 50 chunks (each batch)
3. Check logs show progress percentage

**Estimated Time:** 45 minutes  
**Risk:** Low (additive change, doesn't affect core logic)

---

### 2.3 Simplify Retry Logic

**Issue:** Double retry mechanism (Celery + internal) is confusing  
**Impact:** Clearer error messages, easier debugging  
**Files:** `backend/ai_assistant/automatic_file_processor.py`

**Changes:**
```python
# Line 106-138: Remove internal retry loop, rely on Celery
def process_file_fully(self, uploaded_file_id: int, max_retries: int = 3):
    """
    Complete automatic processing workflow
    NOTE: Retries are handled by Celery task (autoretry_for), not here
    """
    uploaded_file = UploadedFile.objects.get(id=uploaded_file_id)
    
    # SAFETY CHECK: Ensure DocumentFile exists
    # ... existing code ...
    
    # PRE-CHECK: Verify Ollama is accessible
    # ... existing code ...
    
    # REMOVED: Internal retry loop (for attempt in range(1, max_retries + 1))
    # Celery will handle retries automatically
    
    try:
        logger.info(f"Starting automatic processing for: {uploaded_file.filename}")
        
        # Step 1: Verify file exists
        # ... existing code ...
        
        # Step 2-5: Process file (metadata, chunking, embedding)
        # ... existing code ...
        
        return {
            'success': True,
            'chunk_count': len(chunks_data),
            'embedding_count': embedding_count,
            'status': 'ready',
            'attempts': 1  # Always 1, Celery handles retries
        }
        
    except Exception as e:
        error_str = str(e)
        logger.error(f"Processing failed for {uploaded_file.filename}: {error_str}", exc_info=True)
        
        # Store error details
        uploaded_file.processing_error = error_str
        uploaded_file.processing_status = 'failed'
        uploaded_file.save()
        
        # Re-raise for Celery to handle retry
        raise Exception(error_str) from e
```

**Testing:**
1. Upload file that will fail (e.g., corrupted PDF)
2. Verify Celery retries 3 times (check logs)
3. Verify error messages are clear
4. Check no duplicate processing attempts

**Estimated Time:** 1 hour  
**Risk:** Medium (removing retry logic, need to ensure Celery retries work correctly)

---

## Phase 3: Medium Priority Improvements

### 3.1 Add Embedding Deduplication

**Issue:** Identical chunks (headers, footers) processed multiple times  
**Impact:** 20-40% time savings on repetitive documents  
**Files:** `backend/ai_assistant/processors/embeddings/embedding_generator.py`

**Changes:**
```python
import hashlib
from django.core.cache import cache

def generate_embeddings(self, chunks_data, uploaded_file, progress_callback=None):
    embedding_count = 0
    cache_hits = 0
    
    try:
        valid_chunks = [chunk for chunk in chunks_data if chunk['content'].strip()]
        total_batches = (len(valid_chunks) + self.batch_size - 1) // self.batch_size
        
        logger.info(f"Processing {len(valid_chunks)} chunks in {total_batches} batches for {uploaded_file.filename}")
        
        chunks_to_create = []
        chunks_needing_embeddings = []  # NEW: Track which chunks need new embeddings
        chunk_hash_map = {}  # NEW: Map hash -> embedding
        
        # NEW: Phase 1 - Check cache for all chunks
        for chunk_data in valid_chunks:
            cleaned_content = chunk_data['content']
            if isinstance(cleaned_content, str):
                cleaned_content = cleaned_content.replace('\x00', '').replace('\0', '')
                cleaned_content = ''.join(char for char in cleaned_content if ord(char) >= 32 or char in ['\n', '\r', '\t'])
            
            # Hash the content
            content_hash = hashlib.md5(cleaned_content.encode('utf-8')).hexdigest()
            cache_key = f"embedding_content_{content_hash}"
            
            # Check cache
            cached_embedding = cache.get(cache_key)
            if cached_embedding:
                chunk_hash_map[content_hash] = cached_embedding
                cache_hits += 1
            else:
                chunks_needing_embeddings.append((chunk_data, cleaned_content, content_hash))
        
        if cache_hits > 0:
            logger.info(f"Embedding cache hits: {cache_hits}/{len(valid_chunks)} chunks ({cache_hits/len(valid_chunks)*100:.1f}%)")
        
        # NEW: Phase 2 - Get embeddings only for uncached chunks
        for batch_idx in range(0, len(chunks_needing_embeddings), self.batch_size):
            batch = chunks_needing_embeddings[batch_idx:batch_idx + self.batch_size]
            current_batch = batch_idx // self.batch_size + 1
            
            logger.info(f"Processing batch {current_batch}/{total_batches} ({len(batch)} chunks, {cache_hits} cached)")
            
            # Extract texts for embedding
            batch_texts = [cleaned_content for _, cleaned_content, _ in batch]
            batch_hashes = [content_hash for _, _, content_hash in batch]
            
            # Get embeddings
            batch_embeddings = self.ollama_embedding.get_embeddings_batch(batch_texts)
            
            # Cache new embeddings
            for (chunk_data, cleaned_content, content_hash), embedding in zip(batch, batch_embeddings):
                cache_key = f"embedding_content_{content_hash}"
                cache.set(cache_key, embedding, 24 * 3600)  # 24 hour TTL
                chunk_hash_map[content_hash] = embedding
        
        # NEW: Phase 3 - Create DocumentChunk records using cached or new embeddings
        for chunk_data in valid_chunks:
            cleaned_content = chunk_data['content']
            if isinstance(cleaned_content, str):
                cleaned_content = cleaned_content.replace('\x00', '').replace('\0', '')
                cleaned_content = ''.join(char for char in cleaned_content if ord(char) >= 32 or char in ['\n', '\r', '\t'])
            
            content_hash = hashlib.md5(cleaned_content.encode('utf-8')).hexdigest()
            embedding = chunk_hash_map[content_hash]
            
            chunks_to_create.append(
                DocumentChunk(
                    uploaded_file=uploaded_file,
                    content=cleaned_content,
                    embedding=embedding,
                    page_number=chunk_data.get('page_number', 1),
                    chunk_index=embedding_count
                )
            )
            embedding_count += 1
            
            # Bulk insert every 500 chunks
            if len(chunks_to_create) >= 500:
                DocumentChunk.objects.bulk_create(chunks_to_create, batch_size=500)
                chunks_to_create = []
                
                if progress_callback:
                    progress_callback(embedding_count, len(valid_chunks))
        
        # Insert remaining chunks
        if chunks_to_create:
            DocumentChunk.objects.bulk_create(chunks_to_create, batch_size=500)
        
        logger.info(f"Total embeddings created: {embedding_count} (cache hits: {cache_hits})")
        return embedding_count
```

**Testing:**
1. Upload document with repetitive content (headers/footers)
2. Verify cache hits logged
3. Upload same document again - should see high cache hit rate
4. Verify all chunks still created correctly

**Estimated Time:** 2 hours  
**Risk:** Medium (cache logic, need to verify cache backend works correctly)

---

### 3.2 Increase/Configure Chunk Limit

**Issue:** 2000 chunk hard limit truncates large documents  
**Impact:** Better coverage for large documents  
**Files:** `backend/ai_assistant/automatic_file_processor.py`, `backend/ai_assistant/enhanced_chunking.py`

**Changes:**

**Option A: Simple Increase**
```python
# Line 88: Increase limit
self.MAX_CHUNKS_PER_DOC = 5000  # Increased from 2000
```

**Option B: Dynamic Based on System Resources (Better)**
```python
# Line 84-104: Add dynamic calculation
def __init__(self):
    # Calculate max chunks based on available memory
    try:
        import psutil
        available_memory_gb = psutil.virtual_memory().available / (1024 ** 3)
        
        # Estimate: Each chunk + embedding = ~10KB
        # Use 20% of available memory for chunks
        memory_for_chunks_gb = available_memory_gb * 0.2
        estimated_max_chunks = int((memory_for_chunks_gb * 1024 * 1024) / 10)  # KB to chunks
        
        # Clamp between reasonable bounds
        self.MAX_CHUNKS_PER_DOC = max(2000, min(estimated_max_chunks, 10000))
        
        logger.info(f"Calculated MAX_CHUNKS_PER_DOC: {self.MAX_CHUNKS_PER_DOC} (available memory: {available_memory_gb:.2f} GB)")
    except Exception:
        # Fallback to default
        self.MAX_CHUNKS_PER_DOC = 5000
        logger.warning("Could not calculate dynamic chunk limit, using default 5000")
    
    # ... rest of init ...
```

**Testing:**
1. Upload document with > 2000 chunks
2. Verify more chunks processed (up to new limit)
3. Check `is_truncated` and `processing_coverage` fields updated correctly
4. Monitor memory usage during processing

**Estimated Time:** 1 hour (Option A) or 2 hours (Option B)  
**Risk:** Low (Option A) or Medium (Option B - system resource detection)

---

### 3.3 Wrap Embedding in Transaction with Rollback

**Issue:** Partial failures leave orphaned chunks  
**Impact:** Data consistency, cleaner database  
**Files:** `backend/ai_assistant/automatic_file_processor.py`

**Changes:**
```python
# Line 260-282: Wrap embedding in transaction
from django.db import transaction

# Step 4: Generate embeddings (BGE-M3 ONLY, NO FALLBACKS)
try:
    with transaction.atomic():
        # Delete any existing chunks for this file (in case of retry)
        DocumentChunk.objects.filter(uploaded_file=uploaded_file).delete()
        
        embedding_count = self.embedding_generator.generate_embeddings(
            chunks_data, 
            uploaded_file,
            progress_callback=lambda current, total: _update_embedding_progress(uploaded_file, current, total)
        )
        
        # VALIDATION: Check embeddings were created
        if embedding_count == 0:
            raise Exception("No embeddings generated")
        
        if embedding_count != len(chunks_data):
            logger.warning(
                f"Embedding count ({embedding_count}) doesn't match chunk count ({len(chunks_data)}) "
                f"for {uploaded_file.filename}"
            )
        
        uploaded_file.embeddings_created = True
        uploaded_file.embedding_count = embedding_count
        uploaded_file.processing_status = 'ready'
        uploaded_file.processing_completed_at = timezone.now()
        uploaded_file.processing_error = None
        uploaded_file.save()
        
        logger.info(f"File {uploaded_file.filename} marked as READY: {embedding_count} embeddings created")
        
except Exception as e:
    # Transaction will rollback automatically
    logger.error(f"Embedding generation failed for {uploaded_file.filename}: {e}", exc_info=True)
    uploaded_file.processing_status = 'failed'
    uploaded_file.processing_error = f"Embedding failed: {str(e)}"
    uploaded_file.save()
    raise  # Re-raise for Celery retry
```

**Testing:**
1. Simulate embedding failure (e.g., stop Ollama mid-processing)
2. Verify no orphaned chunks in database
3. Verify file status set to 'failed'
4. Retry processing - should start fresh

**Estimated Time:** 45 minutes  
**Risk:** Low (transaction wrapper is standard Django pattern)

---

## Phase 4: Low Priority Improvements

### 4.1 Move GraphRAG to Separate Async Task

**Issue:** GraphRAG delays "ready" status even though it's optional  
**Impact:** Faster "ready" status, better user experience  
**Files:** `backend/ai_assistant/automatic_file_processor.py`, `backend/ai_assistant/tasks/file_processing_tasks.py`

**Changes:**

**File 1: `automatic_file_processor.py`**
```python
# Line 289-321: Remove GraphRAG from main flow, trigger async task instead
# Step 5: Build GraphRAG (moved to async task)
try:
    from .tasks import build_graph_for_file
    logger.info(f"Scheduling GraphRAG build for {uploaded_file.filename}")
    build_graph_for_file.delay(uploaded_file.id)  # Async, non-blocking
except ImportError:
    logger.warning("GraphBuilder not available, skipping GraphRAG")
```

**File 2: `tasks/file_processing_tasks.py` (NEW)**
```python
@shared_task(name='ai_assistant.tasks.build_graph_for_file')
def build_graph_for_file(uploaded_file_id: int):
    """Build GraphRAG for a file asynchronously"""
    try:
        from ai_assistant.models import UploadedFile, DocumentChunk
        from ai_assistant.service_classes.graph_builder import GraphBuilder
        
        uploaded_file = UploadedFile.objects.get(id=uploaded_file_id)
        chunks = DocumentChunk.objects.filter(uploaded_file=uploaded_file)
        
        graph_builder = GraphBuilder()
        graph_result = graph_builder.build_graph_from_document(uploaded_file, list(chunks))
        
        if graph_result.get('success', False):
            logger.info(f"GraphRAG built for {uploaded_file.filename}: {graph_result}")
        else:
            logger.warning(f"GraphRAG failed for {uploaded_file.filename}: {graph_result.get('error')}")
            
    except Exception as e:
        logger.error(f"GraphRAG task failed for file {uploaded_file_id}: {e}", exc_info=True)
```

**Testing:**
1. Upload file
2. Verify file becomes "ready" immediately after embeddings
3. Check GraphRAG task runs separately in Celery
4. Verify entities/relationships still created

**Estimated Time:** 1 hour  
**Risk:** Low (decoupling, doesn't affect core functionality)

---

## Implementation Schedule

### Week 1: Critical Fixes
- **Day 1-2:** Fix DocumentFile signal bug (1.1)
- **Day 3:** Testing and verification

### Week 2: High Priority Performance
- **Day 1-2:** Bulk insert implementation (2.1)
- **Day 3:** Progress updates (2.2)
- **Day 4-5:** Simplify retry logic (2.3)
- **Day 6-7:** Testing and optimization

### Week 3: Medium Priority
- **Day 1-3:** Embedding deduplication (3.1)
- **Day 4:** Chunk limit increase (3.2)
- **Day 5:** Transaction wrapper (3.3)
- **Day 6-7:** Testing

### Week 4: Low Priority & Polish
- **Day 1-2:** GraphRAG async task (4.1)
- **Day 3-4:** Integration testing
- **Day 5-7:** Documentation and deployment

---

## Testing Strategy

### Unit Tests
- Test bulk_create with pgvector embeddings
- Test progress callback updates
- Test embedding deduplication cache
- Test transaction rollback on failure

### Integration Tests
- End-to-end upload → ready workflow
- Verify no duplicate chunks
- Verify progress updates
- Verify GraphRAG still works

### Performance Tests
- Measure database write time (before/after bulk insert)
- Measure total processing time (before/after improvements)
- Monitor memory usage with increased chunk limits

### Regression Tests
- Verify existing functionality still works
- Test edge cases (large files, corrupted files, network failures)

---

## Risk Mitigation

1. **Database Changes (bulk_create):**
   - Test with pgvector extension
   - Verify embeddings stored correctly
   - Have rollback plan

2. **Retry Logic Changes:**
   - Monitor Celery retry behavior closely
   - Keep old code commented for quick rollback
   - Test failure scenarios thoroughly

3. **Cache Implementation:**
   - Verify cache backend configured correctly
   - Test cache expiration
   - Monitor cache hit rates

4. **Transaction Wrapper:**
   - Test with long-running embeddings
   - Verify no deadlocks
   - Monitor transaction log size

---

## Success Metrics

### Performance
- **Database write time:** < 1 second (from 2-3 seconds)
- **Total processing time:** 40-50% reduction
- **Cache hit rate:** 20-40% on repetitive documents

### Quality
- **Duplicate chunks:** 0 (from current 2x)
- **Orphaned chunks:** 0 (from current possibility)
- **Error clarity:** Improved error messages

### User Experience
- **Progress visibility:** Real-time updates
- **Ready status:** Faster (GraphRAG doesn't block)
- **Retry clarity:** Clear attempt tracking

---

## Dependencies

1. **Django Cache Backend:** Must be configured for deduplication
2. **Celery:** Must be running for async tasks
3. **pgvector:** Must support bulk_create with vector fields
4. **Ollama:** Must be accessible for embeddings

---

## Rollback Plan

Each change should be:
1. **Committed separately** - Easy to revert individual changes
2. **Feature-flagged** - Can disable new features if issues arise
3. **Backward compatible** - Old code path still works
4. **Well-tested** - Comprehensive tests before deployment

---

## Notes

- All changes should maintain backward compatibility
- Database migrations may be needed for new fields
- Monitor production metrics after each phase
- Document any configuration changes needed

---

**Next Steps:**
1. Review and approve this plan
2. Set up feature branch for implementation
3. Begin Phase 1 (Critical Fixes)
4. Schedule regular check-ins for progress review

