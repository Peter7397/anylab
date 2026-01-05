"""
Chunk generation coordinator for all file types.
"""

import logging
import os
from pathlib import Path
from ...utils.file_utils import get_file_path
from ...models import DocumentFile
from ...enhanced_chunking import semantic_chunker

logger = logging.getLogger(__name__)


class ChunkGenerator:
    """Generate chunks from various file types"""
    
    def __init__(self, max_chunks_per_doc=2000):
        self.MAX_CHUNKS_PER_DOC = max_chunks_per_doc
    
    def generate_chunks(self, uploaded_file, file_path=None, file_ext=None):
        """
        Generate chunks with UNLIMITED approach for maximum quality
        
        Args:
            uploaded_file: UploadedFile instance
            file_path: Optional file path (will be resolved if not provided)
            file_ext: Optional file extension (will be extracted from filename if not provided)
        
        Returns:
            List of chunk data dictionaries
        """
        try:
            # If this upload has an associated DocumentFile with website content metadata, use that path
            doc_file = DocumentFile.objects.filter(uploaded_file=uploaded_file).first()
            if doc_file and isinstance(getattr(doc_file, 'metadata', None), dict):
                if doc_file.metadata.get('content_type') == 'website' or doc_file.metadata.get('html_content'):
                    return self.generate_html_chunks(uploaded_file)
            
            if file_path is None:
                file_path = get_file_path(uploaded_file)
            
            if not os.path.exists(file_path):
                raise FileNotFoundError(f"File not found: {file_path}")
            
            if file_ext is None:
                file_ext = Path(uploaded_file.filename).suffix.lower()
            
            chunks_data = []
            
            # Delegate to file-type specific chunkers
            if file_ext == '.pdf':
                # PDF chunking is complex and handled in main processor for now
                # This will be extracted to pdf_chunker.py in a future refactoring
                raise NotImplementedError("PDF chunking should be handled by main processor")
            elif file_ext in ['.docx', '.doc']:
                chunks_data = self._chunk_word_document(file_path)
            elif file_ext in ['.xlsx', '.xls']:
                chunks_data = self._chunk_excel_document(file_path)
            elif file_ext in ['.pptx', '.ppt']:
                chunks_data = self._chunk_powerpoint_document(file_path)
            else:
                logger.warning(f"Unsupported file type for chunking: {file_ext}")
                return []
            
            # Track truncation status
            chunks_count = len(chunks_data)
            logger.info(f"Generated {chunks_count} chunks from {uploaded_file.filename}")
            
            if chunks_count >= self.MAX_CHUNKS_PER_DOC:
                uploaded_file.is_truncated = True
                uploaded_file.processing_coverage = min(100.0, (self.MAX_CHUNKS_PER_DOC / chunks_count) * 100)
                logger.warning(
                    f"Document '{uploaded_file.filename}' hit the {self.MAX_CHUNKS_PER_DOC} chunk limit. "
                    f"Document was truncated (coverage: {uploaded_file.processing_coverage:.1f}%)"
                )
                uploaded_file.save()
                # Truncate to max chunks
                chunks_data = chunks_data[:self.MAX_CHUNKS_PER_DOC]
            else:
                uploaded_file.is_truncated = False
                uploaded_file.processing_coverage = 100.0
                uploaded_file.save()
            
            return chunks_data
            
        except Exception as e:
            logger.error(f"Chunking error: {e}")
            raise
    
    def generate_html_chunks(self, uploaded_file):
        """Generate chunks from HTML content stored in metadata"""
        try:
            logger.info(f"Generating chunks from HTML content for {uploaded_file.filename}")
            doc_file = DocumentFile.objects.filter(uploaded_file=uploaded_file).first()
            meta = (doc_file.metadata if (doc_file and isinstance(getattr(doc_file, 'metadata', None), dict)) else {})
            html_content = meta.get('html_content', '')
            if not html_content:
                logger.error(f"No HTML content found in metadata for {uploaded_file.filename}")
                return []
            
            chunks_data = []
            
            # Extract structured content from metadata
            extracted_elements = meta.get('extracted_elements', {})
            source_url = meta.get('source_url', '')
            title = meta.get('title', '')
            
            # Create overview chunk
            overview_content = f"Website: {title}\nURL: {source_url}\n"
            if meta.get('description'):
                overview_content += f"Description: {meta.get('description')}\n"
            
            overview_content += f"Content Summary:\n"
            overview_content += f"- Links: {extracted_elements.get('links_count', 0)}\n"
            overview_content += f"- Images: {extracted_elements.get('images_count', 0)}\n"
            overview_content += f"- Tables: {extracted_elements.get('tables_count', 0)}\n"
            overview_content += f"- Headings: {extracted_elements.get('headings_count', 0)}\n"
            overview_content += f"- Paragraphs: {extracted_elements.get('paragraphs_count', 0)}\n"
            overview_content += f"- Lists: {extracted_elements.get('lists_count', 0)}\n"
            overview_content += f"- Code blocks: {extracted_elements.get('code_blocks_count', 0)}\n"
            overview_content += f"- Forms: {extracted_elements.get('forms_count', 0)}\n"
            
            chunks_data.append({
                'content': overview_content,
                'page_number': 1,
                'chunk_index': len(chunks_data)
            })
            
            # Process main HTML content using semantic chunker
            if html_content.strip():
                content_chunks = semantic_chunker.chunk_by_sentences(html_content, page_number=1)
                
                for chunk in content_chunks:
                    chunk_content = f"[Source: {source_url}]\n{chunk.content}"
                    chunks_data.append({
                        'content': chunk_content,
                        'page_number': chunk.page_number,
                        'chunk_index': len(chunks_data)
                    })
            
            logger.info(f"Generated {len(chunks_data)} chunks from HTML content for {uploaded_file.filename}")
            return chunks_data
            
        except Exception as e:
            logger.error(f"Error generating HTML chunks for {uploaded_file.filename}: {e}", exc_info=True)
            return []
    
    def _chunk_markdown_file(self, file_path, uploaded_file):
        """Chunk Markdown file"""
        chunks_data = []
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
            
            if not content.strip():
                logger.warning(f"Markdown file {uploaded_file.filename} is empty")
                return chunks_data
            
            # Use semantic chunker for markdown (treats it as text)
            markdown_chunks = semantic_chunker.chunk_by_sentences(
                content,
                page_number=1
            )
            
            for chunk in markdown_chunks:
                chunks_data.append({
                    'content': chunk.content,
                    'page_number': chunk.page_number,
                    'chunk_index': len(chunks_data)
                })
            
            logger.info(f"Generated {len(chunks_data)} chunks from Markdown file {uploaded_file.filename}")
            
        except UnicodeDecodeError:
            # Try with different encoding
            try:
                with open(file_path, 'r', encoding='latin-1') as f:
                    content = f.read()
                markdown_chunks = semantic_chunker.chunk_by_sentences(content, page_number=1)
                for chunk in markdown_chunks:
                    chunks_data.append({
                        'content': chunk.content,
                        'page_number': chunk.page_number,
                        'chunk_index': len(chunks_data)
                    })
            except Exception as e:
                logger.error(f"Error processing Markdown file {uploaded_file.filename}: {e}", exc_info=True)
        except Exception as e:
            logger.error(f"Error generating Markdown chunks for {uploaded_file.filename}: {e}", exc_info=True)
        
        return chunks_data
    
    def _chunk_word_document(self, file_path):
        """Chunk Word document"""
        chunks_data = []
        try:
            from docx import Document
            doc = Document(file_path)
            
            for para_idx, para in enumerate(doc.paragraphs):
                if para.text.strip():
                    para_chunks = semantic_chunker.chunk_by_sentences(
                        para.text,
                        page_number=para_idx + 1
                    )
                    for chunk in para_chunks:
                        chunks_data.append({
                            'content': chunk.content,
                            'page_number': chunk.page_number,
                            'chunk_index': len(chunks_data)
                        })
        except ImportError:
            logger.warning("python-docx not available")
        except Exception as e:
            logger.warning(f"Error processing Word document: {e}")
        return chunks_data
    
    def _chunk_excel_document(self, file_path):
        """Chunk Excel document"""
        chunks_data = []
        try:
            import openpyxl
            workbook = openpyxl.load_workbook(file_path, data_only=True, read_only=True)
            
            for sheet_idx, sheet in enumerate(workbook.worksheets):
                for row_idx, row in enumerate(sheet.iter_rows(values_only=True)):
                    row_text = ' '.join(str(cell) if cell else '' for cell in row if cell)
                    if row_text.strip():
                        chunks_data.append({
                            'content': row_text,
                            'page_number': sheet_idx + 1,
                            'chunk_index': len(chunks_data)
                        })
        except ImportError:
            logger.warning("openpyxl not available")
        except Exception as e:
            logger.warning(f"Error processing Excel document: {e}")
        return chunks_data
    
    def _chunk_powerpoint_document(self, file_path):
        """Chunk PowerPoint document"""
        chunks_data = []
        try:
            from pptx import Presentation
            prs = Presentation(file_path)
            
            for slide_idx, slide in enumerate(prs.slides):
                slide_text = []
                for shape in slide.shapes:
                    if hasattr(shape, "text"):
                        slide_text.append(shape.text)
                
                slide_content = '\n'.join(slide_text)
                if slide_content.strip():
                    slide_chunks = semantic_chunker.chunk_by_sentences(
                        slide_content,
                        page_number=slide_idx + 1
                    )
                    
                    for chunk in slide_chunks:
                        chunks_data.append({
                            'content': chunk.content,
                            'page_number': chunk.page_number,
                            'chunk_index': len(chunks_data)
                        })
        except ImportError:
            logger.warning("python-pptx not available")
        except Exception as e:
            logger.warning(f"Error processing PowerPoint document: {e}")
        return chunks_data

