# Get Started: Apply GraphRAG Improvements Now

Follow these steps to apply the GraphRAG improvements to your existing documents.

## Step 0: Setup Environment (REQUIRED FIRST!)

### 0a. Activate Virtual Environment

**IMPORTANT:** You must activate the virtual environment before running any commands!

```bash
cd /Volumes/Orico/Anylab103/backend

# Activate virtual environment (macOS/Linux)
source venv/bin/activate

# You should see (venv) in your prompt after activation
```

**If you see `(venv)` in your prompt, you're ready!**

### 0b. Fix psycopg2 Installation (If Needed)

If you get `pg_config executable not found` error when installing requirements:

**Since you're using PostgreSQL from Docker, install only the client libraries:**

```bash
# Install libpq (PostgreSQL client library only - lightweight!)
brew install libpq

# Add to PATH (for this session)
export PATH="/opt/homebrew/opt/libpq/bin:$PATH"
# Or for Intel Mac: export PATH="/usr/local/opt/libpq/bin:$PATH"

# Verify pg_config is available
which pg_config

# Then install requirements
cd /Volumes/Orico/Anylab103/backend
source venv/bin/activate
pip install -r requirements.txt
```

**See `FIX_PSYCOPG2.md` for detailed troubleshooting.**

## Step 1: Verify Prerequisites (2 minutes)

Make sure required services are running:

```bash
# Check Neo4j is running
docker ps | grep neo4j

# Check Ollama is running (for LLM extraction)
curl http://localhost:11434/api/tags
```

**If services are not running:**
- Neo4j: `docker-compose up -d neo4j`
- Ollama: Start your Ollama service

## Step 2: Check Current State (3 minutes)

See what documents you have and their current state:

```bash
cd backend

# Check document status
python manage.py check_pdf_status

# Analyze current graph (if any)
python manage.py analyze_graph
```

**Note:** If you see "No entities found" or no enhanced entity types, that's expected - you'll fix this in the next steps.

## Step 3: Test with One Document First (5 minutes)

**IMPORTANT:** Always test with one document first to make sure everything works!

```bash
# Find a document ID (from Step 2 output or admin interface)
# Replace 1 with your actual document ID

# Dry run first (see what would happen)
python manage.py reprocess_graph_rag --document-id 1 --dry-run

# If dry run looks good, actually process it
python manage.py reprocess_graph_rag --document-id 1
```

**What to expect:**
- Processing takes 30-60 seconds per document (with LLM)
- You'll see progress messages
- At the end, you'll see entity counts and success/failure

**If it fails:**
- Check the error message
- Verify Ollama is running (if using LLM)
- Try with `--skip-llm` to skip LLM extraction (faster but less comprehensive)

## Step 4: Verify the Test Document (3 minutes)

Check that improvements worked:

```bash
# Analyze the graph to see new entity types
python manage.py analyze_graph --entity-types

# Test a query
python manage.py test_graph_rag_query "What are the key points?" --show-entities
```

**What to look for:**
- ✅ Enhanced entity types (CONCEPT, KEY_TERM, IMPORTANT_INFO) in the analysis
- ✅ Enhanced entities extracted from queries (marked with ✨)
- ✅ Graph-enhanced results in query responses

**If you see enhanced entity types, you're ready for the next step!**

## Step 5: Process All Documents (10-30 minutes)

Once the test document worked, process all your documents:

```bash
# Process all documents in batches of 5
python manage.py reprocess_graph_rag --batch-size 5
```

**Options:**
- **Faster (skip LLM):** `python manage.py reprocess_graph_rag --skip-llm --batch-size 10`
- **Clean slate:** `python manage.py reprocess_graph_rag --clear-graph --batch-size 5`
- **Specific status:** `python manage.py reprocess_graph_rag --status ready --batch-size 5`

**What to expect:**
- Progress for each document
- Summary at the end with total entities and relationships
- Processing time depends on number of documents and LLM usage

**Tips:**
- Let it run - don't interrupt
- Monitor for errors (they'll be shown)
- If errors occur, note which documents failed and retry them individually

## Step 6: Verify All Improvements (5 minutes)

Check that everything worked:

```bash
# Full graph analysis
python manage.py analyze_graph --entity-types --top-entities 20

# Test multiple queries
python manage.py test_graph_rag_query --sample-queries
```

**Success indicators:**
- ✅ Enhanced entity types represent 20%+ of total entities
- ✅ Queries extract enhanced entity types
- ✅ Graph-enhanced results appear in responses
- ✅ Important sections are prioritized

## Step 7: Test in Your Application

Test the improvements in your actual application:

1. **Go to your frontend/UI**
2. **Try conceptual queries:**
   - "What are the key points?"
   - "What is the main idea?"
   - "How does this work?"
   - "What should I know about X?"

3. **Compare results:**
   - Do important sections appear first?
   - Are results more relevant?
   - Do conceptual queries work better?

## Troubleshooting

### Problem: "No documents found to process"

**Solution:**
```bash
# Check document status
python manage.py check_pdf_status

# Process documents with different status
python manage.py reprocess_graph_rag --status pending
```

### Problem: LLM extraction fails or times out

**Solution:**
```bash
# Skip LLM for faster processing
python manage.py reprocess_graph_rag --skip-llm --batch-size 10

# Or check Ollama
curl http://localhost:11434/api/tags
```

### Problem: Neo4j connection errors

**Solution:**
```bash
# Check Neo4j is running
docker ps | grep neo4j

# Start Neo4j if needed
docker-compose up -d neo4j

# Wait a few seconds, then retry
```

### Problem: Out of memory

**Solution:**
```bash
# Process smaller batches
python manage.py reprocess_graph_rag --batch-size 3

# Or skip LLM
python manage.py reprocess_graph_rag --skip-llm --batch-size 5
```

## Quick Reference Commands

```bash
# Check current state
python manage.py analyze_graph

# Test with one document
python manage.py reprocess_graph_rag --document-id 1

# Process all documents
python manage.py reprocess_graph_rag --batch-size 5

# Verify improvements
python manage.py analyze_graph --entity-types
python manage.py test_graph_rag_query "What are the key points?" --show-entities
```

## Expected Timeline

- **Step 1-2:** 5 minutes (setup and checking)
- **Step 3-4:** 8 minutes (test one document)
- **Step 5:** 10-30 minutes (process all documents, depends on count)
- **Step 6-7:** 10 minutes (verification and testing)

**Total:** ~30-50 minutes for complete setup

## What Success Looks Like

After completing all steps, you should see:

1. **In graph analysis:**
   ```
   ✨ CONCEPT              150 (25.0%)
   ✨ KEY_TERM             80 (13.3%)
   ✨ IMPORTANT_INFO       60 (10.0%)
   ✅ Enhanced entity types found: 290 (48.3%)
   ```

2. **In query testing:**
   ```
   Extracted 3 entities:
     ✨ CONCEPT              "key points" (conf: 0.85)
   Graph-enhanced: 3 ✨
   ✅ 60.0% of results are graph-enhanced
   ```

3. **In your application:**
   - Better query results
   - Important information appears first
   - Conceptual queries work well

## Next Steps After Setup

1. **Monitor performance:** Check query results regularly
2. **Reprocess new documents:** New uploads automatically get improvements
3. **Optimize if needed:** Adjust based on your specific use case
4. **Regular analysis:** Run `analyze_graph` periodically to monitor health

---

**Ready? Start with Step 1!** 🚀

