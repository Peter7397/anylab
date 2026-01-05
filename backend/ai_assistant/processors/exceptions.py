"""
Custom exceptions for processors.
"""


class ProcessorError(Exception):
    """Base exception for processor errors"""
    pass


class FileNotFoundError(ProcessorError):
    """File not found error"""
    pass


class ProcessingError(ProcessorError):
    """General processing error"""
    pass


class EmbeddingError(ProcessorError):
    """Embedding generation error"""
    pass


class OCRError(ProcessorError):
    """OCR processing error"""
    pass


class ChunkingError(ProcessorError):
    """Chunking error"""
    pass


class MetadataExtractionError(ProcessorError):
    """Metadata extraction error"""
    pass

