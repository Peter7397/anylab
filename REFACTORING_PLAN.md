# File Processing Refactoring Plan

## Current State Analysis

### Problem: Monolithic File Processing
- **`automatic_file_processor.py`**: 2,315 lines - **TOO LARGE**
- **`tasks.py`**: 1,634 lines - **TOO LARGE**
- Single class (`AutomaticFileProcessor`) handling too many responsibilities
- Difficult to maintain, test, and extend

### Current Responsibilities in `automatic_file_processor.py`:

1. **Main Processing Orchestration** (~350 lines)
   - `process_file_fully()` - Main workflow coordinator
   - Retry logic and error handling

2. **Metadata Extraction** (~160 lines)
   - `_extract_all_metadata()` - Handles PDF, Word, Excel, PowerPoint, Images, Text, HTML
   - File type-specific metadata extraction logic

3. **Chunking** (~600 lines)
   - `_generate_chunks()` - Main chunking coordinator
   - PDF chunking with OCR support
   - Word, Excel, PowerPoint chunking
   - HTML chunking
   - Archive extraction

4. **OCR Processing** (~600 lines)
   - `_process_pdf_with_ocr()` - OCR for scanned PDFs
   - `_ocr_image()` - Image OCR with multiple PSM modes
   - `_save_ocr_chunks_batch()` - Batch saving

5. **Embedding Generation** (~200 lines)
   - `_generate_embeddings()` - Batch embedding coordinator
   - `_get_bge_m3_embedding()` - Single embedding
   - `_get_bge_m3_embeddings_batch()` - Batch embeddings

6. **File Handling** (~100 lines)
   - `_get_file_path()` - File path resolution
   - `_is_archive_file()` - Archive detection
   - `_extract_archive_contents()` - Archive extraction

7. **Validation & Utilities** (~100 lines)
   - `_validate_metadata_completeness()` - Metadata validation
   - `_verify_ollama_connection()` - Service health check
   - `_create_document_file_for_uploaded_file()` - DocumentFile creation

## Proposed Refactoring Structure

### New Module Organization

```
backend/ai_assistant/
├── processors/
│   ├── __init__.py
│   ├── base_processor.py          # Base class for all processors
│   ├── file_processor.py          # Main orchestration (reduced to ~200 lines)
│   │
│   ├── metadata/
│   │   ├── __init__.py
│   │   ├── metadata_extractor.py  # Main metadata extraction coordinator
│   │   ├── pdf_metadata.py         # PDF-specific metadata
│   │   ├── office_metadata.py     # Word, Excel, PowerPoint metadata
│   │   ├── image_metadata.py      # Image metadata extraction
│   │   └── text_metadata.py       # Text/HTML metadata
│   │
│   ├── chunking/
│   │   ├── __init__.py
│   │   ├── chunk_generator.py    # Main chunking coordinator
│   │   ├── pdf_chunker.py         # PDF chunking logic
│   │   ├── office_chunker.py     # Word, Excel, PowerPoint chunking
│   │   ├── html_chunker.py       # HTML chunking
│   │   └── archive_chunker.py    # Archive extraction and chunking
│   │
│   ├── ocr/
│   │   ├── __init__.py
│   │   ├── ocr_processor.py      # Main OCR coordinator
│   │   ├── pdf_ocr.py            # PDF OCR processing
│   │   └── image_ocr.py          # Image OCR with PSM modes
│   │
│   └── embeddings/
│       ├── __init__.py
│       ├── embedding_generator.py # Main embedding coordinator
│       └── ollama_embedding.py    # Ollama BGE-M3 integration
│
├── utils/
│   ├── file_utils.py              # File path, archive detection
│   ├── validation.py              # Metadata validation, service checks
│   └── document_utils.py          # DocumentFile creation helpers
│
└── automatic_file_processor.py   # Thin wrapper (backward compatibility)
```

## Refactoring Benefits

### 1. **Single Responsibility Principle**
- Each module has one clear purpose
- Easier to understand and maintain
- Better testability

### 2. **Improved Maintainability**
- Smaller files (100-300 lines each)
- Easier to locate and fix bugs
- Clearer code organization

### 3. **Better Extensibility**
- Easy to add new file type support
- Easy to swap implementations (e.g., different OCR engines)
- Plugin-like architecture

### 4. **Enhanced Testability**
- Each module can be tested independently
- Mock dependencies easily
- Unit tests for each component

### 5. **Team Collaboration**
- Multiple developers can work on different modules
- Reduced merge conflicts
- Clearer code ownership

## Migration Strategy

### Phase 1: Extract Utilities (Low Risk)
1. Move file utilities to `utils/file_utils.py`
2. Move validation to `utils/validation.py`
3. Move document helpers to `utils/document_utils.py`
4. Update imports in `automatic_file_processor.py`

### Phase 2: Extract Metadata (Medium Risk)
1. Create `processors/metadata/` module
2. Extract metadata extraction logic
3. Create file-type specific extractors
4. Update `automatic_file_processor.py` to use new modules

### Phase 3: Extract Chunking (Medium Risk)
1. Create `processors/chunking/` module
2. Extract chunking logic by file type
3. Update main processor to use chunkers

### Phase 4: Extract OCR (Low Risk)
1. Create `processors/ocr/` module
2. Extract OCR processing logic
3. Isolate OCR dependencies

### Phase 5: Extract Embeddings (Low Risk)
1. Create `processors/embeddings/` module
2. Extract embedding generation logic
3. Isolate Ollama integration

### Phase 6: Refactor Main Processor (High Risk)
1. Simplify `automatic_file_processor.py` to orchestration only
2. Use dependency injection for processors
3. Maintain backward compatibility

## Backward Compatibility

- Keep `automatic_file_processor.py` as a thin wrapper
- Maintain the same public API
- Global instance `automatic_file_processor` remains available
- No changes to `tasks.py` imports initially

## Testing Strategy

1. **Unit Tests**: Test each extracted module independently
2. **Integration Tests**: Test the main processor with all modules
3. **Regression Tests**: Ensure existing functionality works
4. **Performance Tests**: Verify no performance degradation

## Estimated Impact

- **Files Created**: ~15 new files
- **Lines per File**: 100-300 lines (much more manageable)
- **Maintainability**: Significantly improved
- **Risk**: Low (can be done incrementally)
- **Time**: 2-3 days for complete refactoring

