"""
Product Detection Utility

Automatically detects product name from filenames and titles.
"""

import re
from typing import Optional, Dict, List


# Product keywords mapping
PRODUCT_KEYWORDS: Dict[str, List[str]] = {
    'openlab_cds': ['openlab cds', 'openlabcds', 'cds', 'chromatography data system'],
    'openlab_ecm': ['openlab ecm', 'openlabecm', 'ecm', 'enterprise content management'],
    'openlab_eln': ['openlab eln', 'openlabeln', 'eln', 'electronic lab notebook'],
    'openlab_server': ['openlab server', 'openlabserver'],
    'masshunter_workstation': ['masshunter workstation', 'mass hunter workstation'],
    'masshunter_quantitative': ['masshunter quantitative', 'mass hunter quantitative', 'quan'],
    'masshunter_qualitative': ['masshunter qualitative', 'mass hunter qualitative', 'qual'],
    'masshunter_bioconfirm': ['masshunter bioconfirm', 'mass hunter bioconfirm', 'bioconfirm'],
    'masshunter_metabolomics': ['masshunter metabolomics', 'mass hunter metabolomics', 'metabolomics'],
    'vnmrj_current': ['vnmrj', 'vn mri'],
    'vnmrj_legacy': ['vnmrj legacy'],
    'vnmr_legacy': ['vnmr legacy']
}


def detect_product(text: str) -> Optional[str]:
    """
    Detect product category from text (filename, title, etc.)
    
    Args:
        text: Text to analyze (filename, title, etc.)
    
    Returns:
        Product category code or None
    """
    if not text:
        return None
    
    text_lower = text.lower()
    
    # Try exact keyword matching first
    for product, keywords in PRODUCT_KEYWORDS.items():
        for keyword in keywords:
            if keyword in text_lower:
                return product
    
    # Try pattern-based detection
    pattern_matches = _detect_by_pattern(text_lower)
    if pattern_matches:
        return pattern_matches
    
    return None


def _detect_by_pattern(text: str) -> Optional[str]:
    """Detect product using regex patterns"""
    
    # Pattern 1: OpenLab CDS patterns
    if re.search(r'openlab\s*cds|cds\s*(\d+|v\d+|version)', text):
        return 'openlab_cds'
    
    # Pattern 2: OpenLab ECM patterns
    if re.search(r'openlab\s*ecm|ecm\s*(\d+|v\d+|version)', text):
        return 'openlab_ecm'
    
    # Pattern 3: OpenLab ELN patterns
    if re.search(r'openlab\s*eln|eln\s*(\d+|v\d+|version)', text):
        return 'openlab_eln'
    
    # Pattern 4: MassHunter patterns
    if re.search(r'mass\s*hunter', text):
        if 'quantitative' in text or 'quan' in text:
            return 'masshunter_quantitative'
        elif 'qualitative' in text or 'qual' in text:
            return 'masshunter_qualitative'
        elif 'bioconfirm' in text or 'bio confirm' in text:
            return 'masshunter_bioconfirm'
        elif 'metabolomics' in text:
            return 'masshunter_metabolomics'
        else:
            return 'masshunter_workstation'
    
    # Pattern 5: VNMR patterns
    if re.search(r'vnmr', text, re.IGNORECASE):
        if 'legacy' in text:
            return 'vnmr_legacy'
        elif 'j' in text:
            return 'vnmrj_current'
        else:
            return 'vnmrj_current'
    
    return None


def detect_content_type(text: str) -> Optional[str]:
    """
    Detect content type from text
    
    Returns:
        Content type code or None
    """
    if not text:
        return None
    
    text_lower = text.lower()
    
    content_types = {
        'installation_guide': ['installation', 'install', 'setup', 'install guide'],
        'user_manual': ['user manual', 'manual', 'guide', 'user guide'],
        'configuration_guide': ['configuration', 'config', 'setup', 'config guide'],
        'troubleshooting_guide': ['troubleshooting', 'troubleshoot', 'tsb', 'fix'],
        'maintenance_procedure': ['maintenance', 'service', 'repair'],
        'calibration_procedure': ['calibration', 'calibrate', 'cal'],
        'best_practice_guide': ['best practice', 'practice', 'best practices'],
        'video_tutorial': ['video', 'tutorial', 'walkthrough'],
        'webinar_recording': ['webinar', 'recording'],
        'ssb_kpr': ['ssb', 'kpr', 'known problem']
    }
    
    for content_type, keywords in content_types.items():
        for keyword in keywords:
            if keyword in text_lower:
                return content_type
    
    return None

