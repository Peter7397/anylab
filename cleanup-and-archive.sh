#!/bin/bash
# Safe Cleanup and Archive Script for AnyLab
# This script archives old documentation and removes unused files
# AFTER verifying the system can still run

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"

ARCHIVE_DIR="docs/archive/cleanup-$(date +%Y%m%d)"
LOG_FILE="cleanup.log"

echo "🧹 AnyLab Cleanup and Archive Script"
echo "===================================="
echo ""

# Function to log
log() {
    echo "[$(date +'%Y-%m-%d %H:%M:%S')] $1" | tee -a "$LOG_FILE"
}

# Step 1: Pre-flight checks
log "Step 1: Pre-flight system checks..."

# Check if backend can start
log "Checking backend dependencies..."
if [ ! -d "backend/venv" ]; then
    log "ERROR: Backend venv not found. Cannot proceed with cleanup."
    exit 1
fi

# Check if frontend dependencies exist
if [ ! -d "frontend/node_modules" ]; then
    log "WARNING: Frontend node_modules not found. May need npm install."
fi

log "✅ Pre-flight checks passed"

# Step 2: Create archive structure
log ""
log "Step 2: Creating archive structure..."
mkdir -p "$ARCHIVE_DIR/old-docs"
mkdir -p "$ARCHIVE_DIR/logs"
mkdir -p "$ARCHIVE_DIR/test-files"
mkdir -p "$ARCHIVE_DIR/unused-scripts"
log "✅ Archive structure created at $ARCHIVE_DIR"

# Step 3: Archive old documentation (keep essential ones)
log ""
log "Step 3: Archiving old documentation files..."

# Keep these essential docs in root
KEEP_DOCS=(
    "README.md"
    "QUICK_START_GUIDE.md"
    "TESTING_GUIDE.md"
    "ProjectDetails.md"
    "VERSION"
)

# Archive these old docs
ARCHIVE_DOCS=(
    "AUTHENTICATION_TESTING_GUIDE.md"
    "BUILD_GRAPH_GUIDE.md"
    "COMMIT_SUMMARY.md"
    "CURRENT_SERVICE_STATUS.md"
    "DASHBOARD_IMPLEMENTATION_PLAN.md"
    "DUPLICATES_AND_CLEANUP_SUMMARY.md"
    "GRAPH_BUILD_SUCCESS.md"
    "GRAPH_RAG_IMPLEMENTATION_COMPLETE.md"
    "GRAPH_RAG_MIGRATION_PLAN.md"
    "GRAPH_RAG_OPTIONS_SUMMARY.md"
    "GRAPH_RAG_PROGRESS.md"
    "GRAPH_RAG_UI_COMPLETE.md"
    "GRAPH_RAG_UI_PLAN.md"
    "GRAPH_RAG_WEEK2_COMPLETE.md"
    "GRAPH_RAG_WEEK5_COMPLETE.md"
    "GRAPH_VISUALIZATION_FEATURE.md"
    "HYBRID_CONFIGURATION_INVESTIGATION.md"
    "HYBRID_SYSTEM_RELIABILITY_PLAN.md"
    "ICON_PLACEMENT_GUIDE.md"
    "NEO4J_ADVANCED_QUERIES.md"
    "NEO4J_EXPLORATION_QUERIES.md"
    "NEO4J_INSTALLATION_COMPLETE.md"
    "NEO4J_INSTALLATION_GUIDE.md"
    "NEO4J_MANUAL_INSTALL.md"
    "NEO4J_SETUP_COMPLETE.md"
    "NEO4J_SETUP_GUIDE.md"
    "NEO4J_STATUS_AND_RECOMMENDATION.md"
    "NEXT_STEPS.md"
    "QUICK_BUILD_GRAPH.md"
    "SSB_CRASH_PREVENTION_GUARANTEES.md"
    "WEBSITE_INTEGRATION_DOCUMENTATION.md"
)

for doc in "${ARCHIVE_DOCS[@]}"; do
    if [ -f "$doc" ]; then
        mv "$doc" "$ARCHIVE_DIR/old-docs/"
        log "  Archived: $doc"
    fi
done

log "✅ Documentation archived"

# Step 4: Remove macOS resource fork files (._*)
log ""
log "Step 4: Removing macOS resource fork files..."
FOUND_COUNT=0
while IFS= read -r -d '' file; do
    rm -f "$file"
    ((FOUND_COUNT++))
done < <(find . -name "._*" -type f -print0 2>/dev/null || true)
log "  Removed $FOUND_COUNT macOS resource fork files"

# Step 5: Archive old log files
log ""
log "Step 5: Archiving old log files..."
if [ -f "backend_startup.log" ]; then
    mv "backend_startup.log" "$ARCHIVE_DIR/logs/"
    log "  Archived: backend_startup.log"
fi
if [ -f "frontend.log" ]; then
    mv "frontend.log" "$ARCHIVE_DIR/logs/"
    log "  Archived: frontend.log"
fi

# Archive backend logs older than 7 days
if [ -d "backend/logs" ]; then
    find backend/logs -name "*.log" -mtime +7 -exec mv {} "$ARCHIVE_DIR/logs/" \; 2>/dev/null || true
    log "  Archived old backend logs"
fi

log "✅ Log files archived"

# Step 6: Archive test files
log ""
log "Step 6: Archiving test files..."
if [ -f "create_test_pdf.py" ]; then
    mv "create_test_pdf.py" "$ARCHIVE_DIR/test-files/"
    log "  Archived: create_test_pdf.py"
fi
if [ -f "backend/test_pdf_processing.py" ]; then
    mv "backend/test_pdf_processing.py" "$ARCHIVE_DIR/test-files/"
    log "  Archived: backend/test_pdf_processing.py"
fi
if [ -d "test_documents" ]; then
    mv "test_documents" "$ARCHIVE_DIR/test-files/"
    log "  Archived: test_documents/"
fi

log "✅ Test files archived"

# Step 7: Archive unused scripts (if any)
log ""
log "Step 7: Checking for unused scripts..."
# Keep essential startup scripts
# Archive cleanup scripts if they exist
if [ -f "cleanup-duplicates.sh" ]; then
    mv "cleanup-duplicates.sh" "$ARCHIVE_DIR/unused-scripts/"
    log "  Archived: cleanup-duplicates.sh"
fi

log "✅ Scripts checked"

# Step 8: Archive appmon if it's not being used
log ""
log "Step 8: Checking appmon directory..."
if [ -d "appmon" ]; then
    # Check if appmon is referenced anywhere
    if ! grep -r "appmon" backend/ frontend/ --exclude-dir=node_modules --exclude-dir=venv --exclude-dir=__pycache__ 2>/dev/null | grep -v "archive" | grep -v ".md" | grep -q .; then
        log "  appmon directory not referenced in code, archiving..."
        mv "appmon" "$ARCHIVE_DIR/"
        log "  Archived: appmon/"
    else
        log "  appmon directory is referenced, keeping it"
    fi
fi

# Step 9: Clean up .mhtml files in media (these are usually test files)
log ""
log "Step 9: Archiving old media test files..."
if [ -d "backend/media" ]; then
    MHTML_COUNT=0
    for file in backend/media/*.mhtml; do
        if [ -f "$file" ]; then
            mv "$file" "$ARCHIVE_DIR/test-files/" 2>/dev/null && ((MHTML_COUNT++)) || true
        fi
    done
    if [ $MHTML_COUNT -gt 0 ]; then
        log "  Archived $MHTML_COUNT .mhtml test files"
    fi
fi

# Step 10: Create archive index
log ""
log "Step 10: Creating archive index..."
cat > "$ARCHIVE_DIR/ARCHIVE_INDEX.md" << EOF
# Cleanup Archive Index
Created: $(date)

## Archived Files

### Documentation
Archived old documentation files that are no longer actively used.
Essential docs (README.md, QUICK_START_GUIDE.md, etc.) remain in root.

### Logs
Archived old log files. Current logs remain in backend/logs/.

### Test Files
Archived test scripts and test documents.

### Unused Scripts
Archived cleanup and utility scripts that are no longer needed.

## Restore

To restore any archived file:
\`\`\`bash
# Find the file
find docs/archive/cleanup-* -name "filename"

# Restore it
cp docs/archive/cleanup-YYYYMMDD/path/to/file /original/location/
\`\`\`

EOF
log "✅ Archive index created"

# Step 11: Verify system can still run
log ""
log "Step 11: Verifying system integrity..."

# Check critical files exist
CRITICAL_FILES=(
    "backend/manage.py"
    "backend/requirements.txt"
    "frontend/package.json"
    "README.md"
    "QUICK_START_GUIDE.md"
    "docker-compose.yml"
)

for file in "${CRITICAL_FILES[@]}"; do
    if [ ! -f "$file" ]; then
        log "ERROR: Critical file missing: $file"
        log "Please restore from archive before proceeding!"
        exit 1
    fi
done

# Check if backend can import
log "  Testing backend imports..."
cd backend
if ./venv/bin/python -c "import django; print('Django OK')" 2>/dev/null; then
    log "  ✅ Django imports work"
else
    log "  ⚠️  Django import check failed (may need venv activation)"
fi
cd ..

# Check if frontend package.json is valid
log "  Testing frontend configuration..."
if [ -f "frontend/package.json" ]; then
    if node -e "require('./frontend/package.json')" 2>/dev/null; then
        log "  ✅ Frontend package.json is valid"
    else
        log "  ⚠️  Frontend package.json may have issues"
    fi
fi

log ""
log "===================================="
log "✅ Cleanup completed successfully!"
log ""
log "Summary:"
log "  - Archive location: $ARCHIVE_DIR"
log "  - Log file: $LOG_FILE"
log ""
log "Next steps:"
log "  1. Review the archive to ensure nothing important was moved"
log "  2. Test the system: ./start-hybrid.sh"
log "  3. If everything works, the cleanup is complete"
log "  4. If issues arise, restore files from: $ARCHIVE_DIR"
log ""

