"""
Entity Normalization and Query Rewriting

Provides canonicalization for products, software, versions, and error codes,
and utilities to rewrite queries using normalized forms and aliases.
"""
import re
from typing import Dict, List, Tuple


class EntityNormalizer:
    """Normalize domain entities to canonical forms with alias mapping"""

    def __init__(self):
        # Canonical product/software names and aliases
        self.alias_map: Dict[str, str] = {
            'openlab cds': 'OpenLab CDS',
            'openlab content management': 'OpenLab ECM',
            'ol cds': 'OpenLab CDS',
            'ol ecm': 'OpenLab ECM',
            '7890b gc': '7890B GC',
            'masshunter': 'MassHunter',
        }

        # Error code patterns (canonicalize e.g., m8401 -> M8401)
        self.error_code_pattern = re.compile(r'\b([kmKM])[ -]?(\d{3,6}[A-Z]?)\b')

        # Version patterns: v2.8, version 2.8, ver. 3.6
        self.version_patterns = [
            re.compile(r'\bv(?P<ver>\d+(?:\.\d+){0,2})\b', re.IGNORECASE),
            re.compile(r'\bver\.?\s*(?P<ver>\d+(?:\.\d+){0,2})\b', re.IGNORECASE),
            re.compile(r'\bversion\s+(?P<ver>\d+(?:\.\d+){0,2})\b', re.IGNORECASE),
        ]

    def normalize_text(self, text: str) -> Tuple[str, Dict[str, str]]:
        """Normalize entities in free text and return mapping of found entities"""
        if not text:
            return text, {}

        original = text
        found: Dict[str, str] = {}

        # Normalize product/software aliases
        lowered = original.lower()
        for alias, canonical in self.alias_map.items():
            if alias in lowered:
                found[alias] = canonical
        for alias, canonical in found.items():
            # Replace case-insensitively while preserving surrounding text
            pattern = re.compile(re.escape(alias), re.IGNORECASE)
            original = pattern.sub(canonical, original)

        # Normalize error codes (uppercase K/M and digits)
        def _canon_err(m):
            prefix = m.group(1).upper()
            rest = m.group(2).upper()
            return f"{prefix}{rest}"

        original = self.error_code_pattern.sub(_canon_err, original)

        # Normalize versions to vX[.Y[.Z]] form
        for pat in self.version_patterns:
            for m in pat.finditer(original):
                ver = m.group('ver')
                canonical = f"v{ver}"
                span = m.span()
                original = original[:span[0]] + canonical + original[span[1]:]
                break

        return original, found

    def rewrite_query_with_synonyms(self, query: str) -> str:
        """Expand query with canonical forms and common synonyms"""
        normalized, found = self.normalize_text(query)
        expansions: List[str] = []

        # Add synonyms for common intent words
        synonym_groups = {
            'install': ['installation', 'setup', 'configure'],
            'upgrade': ['update', 'migrate'],
            'troubleshoot': ['troubleshooting', 'fix', 'resolve'],
            'error': ['issue', 'problem', 'failure'],
        }
        ql = normalized.lower()
        for root, syns in synonym_groups.items():
            if root in ql:
                expansions.extend(syns)

        if found:
            expansions.extend(set(found.values()))

        # Build expanded query (deduplicated)
        tokens = normalized.split()
        for term in expansions:
            if term not in tokens:
                tokens.append(term)

        return ' '.join(tokens)


# Global instance
entity_normalizer = EntityNormalizer()


