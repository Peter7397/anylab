"""
Version Detection Utility

Extracts version numbers from filenames, titles, and text.
"""

import re
from typing import Optional, Tuple


def detect_version(text: str) -> Optional[str]:
    """
    Detect version number from text using multiple patterns.
    
    Supports formats:
    - v3.2.1
    - version 3.2.1
    - V3.2
    - Release 3.2.1
    - 3.2.1.0
    """
    if not text:
        return None
    
    # Pattern 1: vX.Y.Z or vX.Y
    pattern1 = r'v(\d+\.\d+(?:\.\d+)?(?:\.\d+)?)'
    match = re.search(pattern1, text, re.IGNORECASE)
    if match:
        return match.group(1)
    
    # Pattern 2: version X.Y.Z
    pattern2 = r'version\s+(\d+\.\d+(?:\.\d+)?(?:\.\d+)?)'
    match = re.search(pattern2, text, re.IGNORECASE)
    if match:
        return match.group(1)
    
    # Pattern 3: Release X.Y.Z
    pattern3 = r'release\s+(\d+\.\d+(?:\.\d+)?(?:\.\d+)?)'
    match = re.search(pattern3, text, re.IGNORECASE)
    if match:
        return match.group(1)
    
    # Pattern 4: Just X.Y.Z format at the beginning or end
    pattern4 = r'^(\d+\.\d+(?:\.\d+)?(?:\.\d+)?)|\s(\d+\.\d+(?:\.\d+)?(?:\.\d+)?)$'
    matches = re.findall(pattern4, text)
    if matches:
        # Return the first valid match (non-empty)
        for match in matches:
            version = match[0] if match[0] else match[1]
            if version:
                return version
    
    return None


def parse_version(version_str: str) -> Tuple[int, ...]:
    """
    Parse version string to tuple for comparison.
    
    Example: "3.2.1" -> (3, 2, 1)
    """
    if not version_str:
        return (0, 0, 0)
    
    try:
        parts = version_str.split('.')
        return tuple(int(part) for part in parts if part.isdigit())
    except (ValueError, AttributeError):
        return (0, 0, 0)


def compare_versions(version1: str, version2: str) -> int:
    """
    Compare two version strings.
    
    Returns:
        -1 if version1 < version2
        0 if version1 == version2
        1 if version1 > version2
    """
    v1 = parse_version(version1)
    v2 = parse_version(version2)
    
    # Pad to same length
    max_len = max(len(v1), len(v2))
    v1 += (0,) * (max_len - len(v1))
    v2 += (0,) * (max_len - len(v2))
    
    if v1 < v2:
        return -1
    elif v1 > v2:
        return 1
    else:
        return 0


def get_latest_version(versions: list) -> Optional[str]:
    """Get the latest version from a list of version strings."""
    if not versions:
        return None
    
    latest = versions[0]
    for version in versions[1:]:
        if compare_versions(version, latest) > 0:
            latest = version
    
    return latest

