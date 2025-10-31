"""
Citation Validator

Lightweight validator that checks whether response sentences are supported
by retrieved sources via simple lexical overlap.
"""
import re
from typing import List, Dict


def split_sentences(text: str) -> List[str]:
    parts = re.split(r'(?<=[\.!?])\s+', text.strip()) if text else []
    return [p.strip() for p in parts if p.strip()]


def sentence_supported(sentence: str, sources: List[Dict], threshold: float = 0.15) -> bool:
    s_tokens = set(re.findall(r"[A-Za-z0-9]+", sentence.lower()))
    if not s_tokens:
        return True
    for src in sources:
        content = (src.get('content') or '')
        tokens = set(re.findall(r"[A-Za-z0-9]+", content.lower()))
        if not tokens:
            continue
        overlap = len(s_tokens & tokens) / max(1, len(s_tokens | tokens))
        if overlap >= threshold:
            return True
    return False


def validate_response_support(response: str, sources: List[Dict]) -> Dict:
    sentences = split_sentences(response)
    unsupported = []
    for s in sentences:
        if not sentence_supported(s, sources):
            unsupported.append(s)
    return {
        'total_sentences': len(sentences),
        'unsupported_count': len(unsupported),
        'unsupported_samples': unsupported[:3]
    }


