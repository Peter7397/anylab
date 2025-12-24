"""
KPR Index Parser Module

This module provides parsing capabilities for Agilent's KPR (Known Problem Report) 
index page, extracting KPR entries by keyword sections and dates.
"""

import re
import logging
import json
import requests
import time
from typing import List, Dict, Any, Optional, Tuple
from datetime import datetime, timedelta
from bs4 import BeautifulSoup
from html import unescape

logger = logging.getLogger(__name__)


class KPRIndexParser:
    """Parser for KPR index pages"""
    
    def __init__(self):
        self.kpr_pattern = re.compile(r'KPR#:(\d+)\s+(.+?)(?=\n|KPR#:|$)', re.MULTILINE)
        self.keyword_pattern = re.compile(r'^Keyword:\s*(.+)$', re.MULTILINE)
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'AnyLab-KPR-Scraper/1.0',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
        })
        
    def parse_index_content(self, html_content: str) -> Dict[str, List[Dict]]:
        """
        Parse the KPR index page content
        
        Returns:
            Dictionary with keywords as keys and list of KPR entries as values
        """
        try:
            # Check if this is an MHTML file
            if html_content.strip().startswith('From:') or 'boundary=' in html_content[:200]:
                # This is MHTML format
                logger.info("Detected MHTML format")
                # Extract HTML part from MHTML
                html_part = self._extract_html_from_mhtml(html_content)
                if not html_part:
                    logger.error("Could not extract HTML from MHTML")
                    # Try parsing as raw text instead
                    return self._extract_kprs_by_keyword(html_content)
                
                soup = BeautifulSoup(html_part, 'html.parser')
                # Get text but preserve structure for better parsing
                text_content = '\n'.join([line.strip() for line in soup.get_text().split('\n') if line.strip()])
            else:
                # Parse regular HTML
                soup = BeautifulSoup(html_content, 'html.parser')
                text_content = '\n'.join([line.strip() for line in soup.get_text().split('\n') if line.strip()])
            
            # Extract KPRs organized by keyword sections
            kpr_by_keyword = self._extract_kprs_by_keyword(text_content)
            
            logger.info(f"Parsed {sum(len(kprs) for kprs in kpr_by_keyword.values())} KPRs from index")
            
            return kpr_by_keyword
            
        except Exception as e:
            logger.error(f"Error parsing KPR index: {e}")
            return {}
    
    def _extract_html_from_mhtml(self, mhtml_content: str) -> str:
        """Extract HTML content from MHTML file"""
        try:
            # Fix MIME quoted-printable encoding
            import quopri
            fixed_content = quopri.decodestring(mhtml_content.encode('latin-1')).decode('utf-8', errors='ignore')
            
            # Extract HTML between <html> and </html> or <body> and </body>
            import re
            
            # Try to extract body content
            body_match = re.search(r'<body[^>]*>(.*?)</body>', fixed_content, re.DOTALL | re.IGNORECASE)
            if body_match:
                html_part = body_match.group(1)
                # Decode HTML entities
                from html import unescape
                html_part = unescape(html_part)
                return html_part
            
            # Try to extract between HTML tags
            html_match = re.search(r'<html[^>]*>(.*?)</html>', fixed_content, re.DOTALL | re.IGNORECASE)
            if html_match:
                html_part = html_match.group(1)
                from html import unescape
                html_part = unescape(html_part)
                return html_part
            
            return fixed_content
            
        except Exception as e:
            logger.error(f"Error extracting HTML from MHTML: {e}")
            return mhtml_content
    
    def _extract_kprs_by_keyword(self, text: str) -> Dict[str, List[Dict]]:
        """Extract KPR entries organized by keyword sections"""
        kpr_by_keyword = {}
        current_keyword = "Unknown"
        
        # First find all keywords and their positions
        keyword_pattern = r'Keyword:\s*([^\n:]+)'
        keyword_positions = [(m.start(), m.group(1).strip()) for m in re.finditer(keyword_pattern, text, re.IGNORECASE)]
        
        if not keyword_positions:
            return kpr_by_keyword
        
        # Process each section between keywords
        for i, (start_pos, keyword) in enumerate(keyword_positions):
            current_keyword = re.sub(r'<[^>]+>', '', keyword).strip()
            # Use keyword name without start_pos to avoid duplicates
            if current_keyword not in kpr_by_keyword:
                kpr_by_keyword[current_keyword] = []
            
            # Find where this keyword section ends (next keyword or end)
            end_pos = keyword_positions[i + 1][0] if i + 1 < len(keyword_positions) else len(text)
            
            # Extract this section's text (skip the keyword line itself)
            section_text = text[start_pos:end_pos]
            
            # Find all KPR entries in this section using multi-line pattern
            # Match all KPR# entries until we hit the next section
            kpr_pattern = r'KPR#:\s*(\d+)'
            kpr_numbers = list(re.finditer(kpr_pattern, section_text, re.IGNORECASE))
            
            for i, kpr_match in enumerate(kpr_numbers):
                kpr_num = kpr_match.group(1)
                
                # Get the text after this KPR# until the next KPR# or end of section
                desc_start = kpr_match.end()
                desc_end = kpr_numbers[i+1].start() if i+1 < len(kpr_numbers) else len(section_text)
                raw_text = section_text[desc_start:desc_end].strip()
                
                # Parse structured KPR entry
                # Format: Product: ..., Keyword: ..., One-line Description: ..., Problem: ..., etc.
                
                kpr_entry = self._parse_structured_kpr(raw_text, kpr_num, current_keyword)
                
                if kpr_entry:
                    kpr_by_keyword[current_keyword].append(kpr_entry)
        
        return kpr_by_keyword
    
    def _parse_structured_kpr(self, text: str, kpr_num: str, keyword: str) -> Optional[Dict]:
        """Simple parsing - just extract basic info from KPR text"""
        # Just return basic KPR info without complex parsing
        # The file will be stored as-is for viewing
        cleaned_text = re.sub(r'\s+', ' ', text).strip()
        
        return {
            'kpr_number': kpr_num,
            'title': cleaned_text[:200] or f'KPR #{kpr_num}',
            'description': cleaned_text[:500],  # Limit description length
            'keyword': keyword,
            'severity': 'medium',
            'platform': 'Unknown',
            'product_category': 'Other Products',
            'category': keyword.lower(),
            'extracted_date': datetime.now().isoformat()
        }
    
    def _detect_severity(self, title: str) -> str:
        """Detect severity level from title text"""
        title_lower = title.lower()
        
        # Critical keywords
        critical_keywords = ['crash', 'fails', 'cannot', 'unable', 'error', 'exception', 'frozen', 'locked']
        if any(kw in title_lower for kw in critical_keywords):
            return 'critical'
        
        # High keywords
        high_keywords = ['incorrect', 'wrong', 'missing', 'failed', 'does not', 'not working']
        if any(kw in title_lower for kw in high_keywords):
            return 'high'
        
        # Medium keywords
        medium_keywords = ['may', 'sometimes', 'sporadic', 'intermittent', 'slow']
        if any(kw in title_lower for kw in medium_keywords):
            return 'medium'
        
        # Low keywords
        low_keywords = ['display', 'show', 'label', 'format']
        if any(kw in title_lower for kw in low_keywords):
            return 'low'
        
        # Default to medium
        return 'medium'
    
    def _detect_platform(self, title: str) -> str:
        """Detect platform from title"""
        title_lower = title.lower()
        
        platforms = {
            'openlab cds': ['openlab', 'cds'],
            'openlab ecm': ['ecm', 'content management'],
            'gc driver': ['gc', 'gas chromatography'],
            'lc driver': ['lc', 'liquid chromatography', 'hplc'],
            'masshunter': ['masshunter', 'mass hunter'],
            'chemstation': ['chemstation', 'chem station'],
            'ezchrom': ['ezchrom'],
            'chromeleon': ['chromeleon', 'chameleon'],
            'vnmrj': ['vnmrj', 'vnmr'],
            'agilent gc': ['6890', '7890', '8860', '8890', 'intuvo'],
            'agilent lc': ['1260', '1290', '1220'],
        }
        
        for platform, keywords in platforms.items():
            if any(kw in title_lower for kw in keywords):
                return platform
        
        # Try to extract version numbers
        version_match = re.search(r'\d+\.\d+[\.\d]*', title)
        if version_match:
            return f"OpenLab CDS {version_match.group()}"
        
        return 'Unknown'
    
    def _detect_product_category(self, title: str, keyword: str = '') -> str:
        """Detect product category for tab organization"""
        title_lower = (title + ' ' + keyword).lower()
        
        # Product categories for UI tabs
        products = {
            'OpenLab CDS': [
                'cds', 'openlab cds', 'openlab - cds', 'openlab cds2',
                'openlab cds 3', 'openlab cds 2'
            ],
            'OpenLab ChemStation': [
                'chemstation', 'chem station', 'ezchrom',
                '6890', '7890', 'gc'
            ],
            'OpenLab ECM': [
                'ecm', 'ecm xt', 'ecm xt 2', 'content management'
            ],
            'MassHunter': [
                'masshunter', 'mass hunter', 'lcmsworkstation'
            ],
            'Drivers & Hardware': [
                'driver', 'gc driver', 'lc driver', '6890n', '7693'
            ],
        }
        
        for product, keywords in products.items():
            if any(kw in title_lower for kw in keywords):
                return product
        
        return 'Other Products'
    
    def _categorize_kpr(self, title: str, keyword: str) -> str:
        """Categorize KPR based on title and keyword"""
        categories = {
            'driver': ['driver', 'gc driver', 'lc driver'],
            'acquisition': ['acquisition', 'data collection', 'sequence'],
            'data analysis': ['data analysis', 'processing', 'integration', 'reprocessing'],
            'reporting': ['report', 'template', 'printing'],
            'administration': ['admin', 'user', 'privilege', 'security'],
            'installation': ['install', 'upgrade', 'update'],
            'workflow': ['workflow', 'method', 'calibration'],
            'performance': ['performance', 'slow', 'memory', 'cpu'],
            'troubleshooting': ['error', 'crash', 'failed', 'issue'],
        }
        
        # Check keyword first
        keyword_lower = keyword.lower()
        for category, category_keywords in categories.items():
            if any(ckw in keyword_lower for ckw in category_keywords):
                return category
        
        # Check title
        title_lower = title.lower()
        for category, category_keywords in categories.items():
            if any(ckw in title_lower for ckw in category_keywords):
                return category
        
        return 'general'
    
    def filter_by_date_range(self, kpr_entries: List[Dict], months: int = 3) -> List[Dict]:
        """
        Filter KPR entries from last N months
        
        Since we don't have actual dates from the index, we'll use a scoring system
        based on KPR number (assuming newer KPRs have higher numbers)
        """
        # Sort by KPR number (higher number = likely newer)
        sorted_entries = sorted(kpr_entries, key=lambda x: int(x['kpr_number']), reverse=True)
        
        # Take the top entries (assuming they're the most recent)
        # This is a heuristic since we don't have actual dates
        target_count = min(len(sorted_entries), 100)  # Adjust based on typical monthly volume
        
        return sorted_entries[:target_count]
    
    def get_recent_kprs(self, html_content: str, months: int = 3) -> List[Dict]:
        """Get KPRs from the last N months"""
        # Parse all KPRs
        all_kprs_by_keyword = self.parse_index_content(html_content)
        
        # Flatten and get all entries
        all_kprs = []
        for keyword, kprs in all_kprs_by_keyword.items():
            all_kprs.extend(kprs)
        
        # Filter for recent ones
        recent_kprs = self.filter_by_date_range(all_kprs, months)
        
        logger.info(f"Found {len(recent_kprs)} KPRs from last {months} months")
        
        return recent_kprs
    
    def extract_kpr_metadata(self, kpr_entry: Dict, fetch_full_details: bool = False) -> Dict[str, Any]:
        """Extract metadata from a KPR entry - simplified version"""
        kpr_number = kpr_entry.get('kpr_number')
        description = kpr_entry.get('description', f'KPR #{kpr_number}')
        title = kpr_entry.get('title', f'KPR #{kpr_number}')
        
        # Build simple metadata
        metadata = {
            'kpr_number': kpr_number,
            'keyword': kpr_entry.get('keyword'),
            'severity': 'medium',
            'platform': 'Unknown',
            'product_category': 'Other Products',
            'category': kpr_entry.get('category', 'general'),
            'title': title,
            'description': description,
            'source_url': f"https://www.agilent.com/kpr/{kpr_number}",
            'document_type': 'SSB_KPR',
            'organization_mode': 'lab-informatics',
            'content_category': 'troubleshooting',
            'status': 'open',
            'created_date': datetime.now().isoformat(),
            'updated_date': datetime.now().isoformat(),
        }
        
        return metadata
    

