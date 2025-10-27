"""
Metadata Validation Utility

Validates document metadata for completeness and correctness.
"""

import re
from typing import Dict, List, Tuple, Optional


VALID_PRODUCT_CATEGORIES = [
    'openlab_cds', 'openlab_ecm', 'openlab_eln', 'openlab_server',
    'masshunter_workstation', 'masshunter_quantitative', 'masshunter_qualitative',
    'masshunter_bioconfirm', 'masshunter_metabolomics',
    'vnmrj_current', 'vnmrj_legacy', 'vnmr_legacy'
]

VALID_CONTENT_TYPES = [
    'installation_guide', 'user_manual', 'configuration_guide',
    'troubleshooting_guide', 'maintenance_procedure', 'calibration_procedure',
    'best_practice_guide', 'video_tutorial', 'webinar_recording', 'ssb_kpr'
]

VERSION_PATTERN = re.compile(r'^\d+\.\d+(\.\d+)?(\.\d+)?$')


def validate_metadata(metadata: Dict) -> Tuple[bool, List[str]]:
    """
    Validate document metadata.
    
    Args:
        metadata: Metadata dictionary
    
    Returns:
        (is_valid, list_of_errors)
    """
    errors = []
    
    # Validate product_category
    product_category = metadata.get('product_category', '')
    if not product_category:
        errors.append('Product category is required')
    elif product_category not in VALID_PRODUCT_CATEGORIES:
        errors.append(f'Invalid product category: {product_category}')
    
    # Validate content_type
    content_type = metadata.get('content_type', '')
    if not content_type:
        errors.append('Content type is required')
    elif content_type not in VALID_CONTENT_TYPES:
        errors.append(f'Invalid content type: {content_type}')
    
    # Validate version format (optional)
    version = metadata.get('version', '')
    if version and not is_valid_version(version):
        errors.append(f'Invalid version format: {version}. Expected format: X.Y.Z')
    
    return len(errors) == 0, errors


def is_valid_version(version: str) -> bool:
    """Check if version string matches expected format (X.Y.Z)"""
    if not version or version == 'N/A':
        return False
    
    return bool(VERSION_PATTERN.match(version))


def sanitize_metadata(metadata: Dict) -> Dict:
    """Clean and sanitize metadata"""
    sanitized = {}
    
    # Sanitize product_category - handle None values
    product_category = metadata.get('product_category', '') or ''
    sanitized['product_category'] = str(product_category).strip().lower() if product_category else ''
    
    # Sanitize content_type - handle None values
    content_type = metadata.get('content_type', '') or ''
    sanitized['content_type'] = str(content_type).strip().lower() if content_type else ''
    
    # Sanitize version - handle None values
    version = metadata.get('version', '') or ''
    sanitized['version'] = str(version).strip() if version else ''
    
    # Sanitize document_type - handle None values
    document_type = metadata.get('document_type', 'pdf') or 'pdf'
    sanitized['document_type'] = str(document_type).strip().lower() if document_type else 'pdf'
    
    return sanitized

