# Process Documents First - Then Apply GraphRAG Improvements

## The Situation

You have **147 PDF files** but they're all showing as "Not processed". This means:
- ❌ No chunks created yet
- ❌ No embeddings generated
- ❌ Can't apply GraphRAG improvements yet

**You need to process the documents first (create chunks and embeddings), THEN apply GraphRAG improvements.**

## Step-by-Step Workflow

### Step 1: Process Documents (Create Chunks & Embeddings)

First, process your PDFs to create chunks and embeddings:

```bash
cd /Volumes/Orico/Anylab103/backend
source venv/bin/activate

# Process all unprocessed PDFs
python manage.py reprocess_pdfs
```

**What this does:**
- Extracts text from PDFs
- Creates chunks (600 char chunks with 120 char overlap)
- Generates embeddings (BGE-M3 via Ollama)
- Marks documents as 'ready'

**Time:** This will take a while for 147 documents (depends on Ollama processing speed)

### Step 2: Check Processing Status

After processing, verify documents are ready:

```bash
python manage.py check_pdf_status
```

**Look for:**
- ✅ Documents showing as "Processed" or "Ready"
- ✅ Total chunks > 0
- ✅ Documents with `chunks_created=True`

### Step 3: Apply GraphRAG Improvements

Once documents are processed, apply GraphRAG improvements:

```bash
# Test with one document first
python manage.py reprocess_graph_rag --document-id <ID>

# Then process all
python manage.py reprocess_graph_rag --batch-size 5
```

## Alternative: Process and GraphRAG in One Go

If you want to process documents AND apply GraphRAG improvements automatically:

**New documents uploaded will automatically:**
1. Get processed (chunks + embeddings)
2. Get GraphRAG improvements applied

**For existing documents, you need to:**
1. Process them first: `python manage.py reprocess_pdfs`
2. Then apply GraphRAG: `python manage.py reprocess_graph_rag`

## Processing Options

### Process All Documents

```bash
python manage.py reprocess_pdfs
```

### Process Specific Document

```bash
# Find document ID first
python manage.py check_pdf_status

# Process specific document (if command supports it)
# Or use the automatic file processor
```

### Process in Batches (If Needed)

The reprocess_pdfs command should handle batching automatically, but if you need more control, you might need to process documents through the admin interface or API.

## Expected Timeline

For 147 documents:
- **Processing (chunks + embeddings):** 1-3 hours (depends on Ollama speed)
- **GraphRAG improvements:** 30-60 minutes (after processing)

## Quick Start Commands

```bash
# 1. Activate virtual environment
cd /Volumes/Orico/Anylab103/backend
source venv/bin/activate

# 2. Process all PDFs (this will take time!)
python manage.py reprocess_pdfs

# 3. Check status (wait for processing to complete)
python manage.py check_pdf_status

# 4. Once documents show as processed, apply GraphRAG improvements
python manage.py reprocess_graph_rag --batch-size 5
```

## Monitoring Progress

While processing, you can:
- Check logs: `tail -f logs/anylab.log`
- Check status: `python manage.py check_pdf_status`
- Monitor Celery (if using): Check Celery worker logs

## Important Notes

1. **Processing takes time:** 147 documents will take 1-3 hours
2. **Ollama must be running:** For embeddings generation
3. **Neo4j must be running:** For GraphRAG (can start after processing)
4. **Don't interrupt:** Let processing complete

## After Processing Completes

Once you see documents as "Processed" in `check_pdf_status`:

```bash
# Verify documents are ready
python manage.py check_pdf_status

# Apply GraphRAG improvements
python manage.py reprocess_graph_rag --batch-size 5

# Verify improvements
python manage.py analyze_graph --entity-types
python manage.py test_graph_rag_query "What are the key points?" --show-entities
```

---

**Start with:** `python manage.py reprocess_pdfs`

This will begin processing all 147 documents. It will take time, but you can monitor progress with `check_pdf_status`.

