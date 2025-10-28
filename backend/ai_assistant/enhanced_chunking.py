"""
Enhanced text chunking utilities for improved RAG performance
"""
import re
import logging
from typing import List, Tuple
from dataclasses import dataclass

logger = logging.getLogger(__name__)

@dataclass
class TextChunk:
    """Represents a chunk of text with metadata"""
    content: str
    start_pos: int
    end_pos: int
    chunk_index: int
    page_number: int = 1
    section_title: str = ""
    
class SemanticChunker:
    """Advanced text chunking with semantic awareness"""
    
    def __init__(self, 
                 chunk_size: int = 100,  # Optimal size for RAG quality
                 chunk_overlap: int = 10,
                 max_chunks_per_doc: int = 10000):  # REMOVED LIMIT - Quality over speed
        self.chunk_size = chunk_size
        self.chunk_overlap = chunk_overlap
        self.max_chunks_per_doc = max_chunks_per_doc
        
        # Sentence boundary patterns
        self.sentence_endings = re.compile(r'[.!?]+\s+')
        self.paragraph_breaks = re.compile(r'\n\s*\n')
        
    def preprocess_text(self, text: str) -> str:
        """Clean and normalize text before chunking"""
        # Remove excessive whitespace
        text = re.sub(r'\s+', ' ', text)
        
        # Normalize unicode
        text = text.encode('utf-8', errors='ignore').decode('utf-8')
        
        # Remove page headers/footers (common patterns)
        text = re.sub(r'Page \d+.*?\n', '', text, flags=re.IGNORECASE)
        text = re.sub(r'^\d+\s*\n', '', text, flags=re.MULTILINE)
        
        # Clean up bullet points and lists
        text = re.sub(r'^\s*[•\-\*]\s+', '• ', text, flags=re.MULTILINE)
        
        # Remove excessive line breaks
        text = re.sub(r'\n{3,}', '\n\n', text)
        
        return text.strip()
    
    def find_sentence_boundaries(self, text: str) -> List[int]:
        """Find sentence boundaries in text"""
        boundaries = [0]
        
        for match in self.sentence_endings.finditer(text):
            end_pos = match.end()
            if end_pos < len(text):
                boundaries.append(end_pos)
        
        boundaries.append(len(text))
        return sorted(set(boundaries))
    
    def chunk_by_sentences(self, text: str, page_number: int = 1) -> List[TextChunk]:
        """Chunk text by sentences with overlap"""
        # Preprocess text
        clean_text = self.preprocess_text(text)
        
        if len(clean_text) <= self.chunk_size:
            return [TextChunk(
                content=clean_text,
                start_pos=0,
                end_pos=len(clean_text),
                chunk_index=0,
                page_number=page_number
            )]
        
        # Find sentence boundaries
        boundaries = self.find_sentence_boundaries(clean_text)
        
        chunks = []
        chunk_start = 0
        chunk_index = 0
        
        # NO LIMIT - Process all content for maximum RAG quality
        while chunk_start < len(clean_text):
            # Only limit if we exceed safety threshold (10k chunks)
            if chunk_index >= self.max_chunks_per_doc:
                logger.warning(f"Document has {len(chunks)} chunks, which is very large. Consider document size.")
                break
            
            # Find end position for this chunk
            chunk_end = min(chunk_start + self.chunk_size, len(clean_text))
            
            # Adjust to sentence boundary if possible
            best_end = chunk_end
            for boundary in boundaries:
                if chunk_start < boundary <= chunk_end + 100:  # Allow some flexibility
                    best_end = boundary
            
            # Extract chunk content
            chunk_content = clean_text[chunk_start:best_end].strip()
            
            if chunk_content:  # Only add non-empty chunks
                chunks.append(TextChunk(
                    content=chunk_content,
                    start_pos=chunk_start,
                    end_pos=best_end,
                    chunk_index=chunk_index,
                    page_number=page_number
                ))
                chunk_index += 1
            
            # Calculate next start position with overlap
            next_start = max(chunk_start + self.chunk_size - self.chunk_overlap, best_end)
            if next_start <= chunk_start:
                next_start = chunk_start + 1
            
            chunk_start = next_start
        
        return chunks
    
    def chunk_document_pages(self, page_texts: List[str]) -> List[TextChunk]:
        """Chunk multiple pages of a document"""
        all_chunks = []
        
        for page_num, page_text in enumerate(page_texts, 1):
            if not page_text.strip():
                continue
                
            page_chunks = self.chunk_by_sentences(page_text, page_number=page_num)
            all_chunks.extend(page_chunks)
            
            # Quality-focused: Process all pages without truncation
            # Log large documents but continue processing for maximum quality
            if len(all_chunks) > 5000:
                logger.info(f"Processing large document with {len(all_chunks)} chunks - maximizing RAG quality")
        
        return all_chunks
    
    def chunk_single_text(self, text: str, page_number: int = 1) -> List[TextChunk]:
        """Chunk a single text document"""
        return self.chunk_by_sentences(text, page_number)

class AdvancedChunker(SemanticChunker):
    """Advanced chunker with section awareness"""
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        
        # Section header patterns
        self.section_patterns = [
            re.compile(r'^(Chapter|Section|Part)\s+\d+', re.IGNORECASE | re.MULTILINE),
            re.compile(r'^\d+\.\s+[A-Z][^.]*$', re.MULTILINE),
            re.compile(r'^[A-Z][A-Z\s]{5,}$', re.MULTILINE),  # ALL CAPS headers
        ]
    
    def find_sections(self, text: str) -> List[Tuple[int, str]]:
        """Find section headers in text"""
        sections = []
        
        for pattern in self.section_patterns:
            for match in pattern.finditer(text):
                sections.append((match.start(), match.group().strip()))
        
        return sorted(sections, key=lambda x: x[0])
    
    def chunk_with_sections(self, text: str, page_number: int = 1) -> List[TextChunk]:
        """Chunk text while preserving section context"""
        # Find sections
        sections = self.find_sections(text)
        
        # Get basic chunks
        chunks = self.chunk_by_sentences(text, page_number)
        
        # Add section context to chunks
        for chunk in chunks:
            # Find the most recent section header
            current_section = ""
            for section_pos, section_title in sections:
                if section_pos <= chunk.start_pos:
                    current_section = section_title
                else:
                    break
            chunk.section_title = current_section
        
        return chunks

# Global chunker instances
# QUALITY FOCUS: No chunk limits, 100 char chunks for maximum RAG precision
semantic_chunker = SemanticChunker(
    chunk_size=100,           # Optimal size for semantic understanding
    chunk_overlap=10,         # Maintain context between chunks
    max_chunks_per_doc=10000  # NO PRACTICAL LIMIT - Process entire document
)

advanced_chunker = AdvancedChunker(
    chunk_size=100,           # Optimal size for semantic understanding
    chunk_overlap=10,         # Maintain context between chunks
    max_chunks_per_doc=10000  # NO PRACTICAL LIMIT - Process entire document
)
