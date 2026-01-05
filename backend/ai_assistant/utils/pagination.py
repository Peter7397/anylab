"""
Pagination utilities for RAG query results
Provides cursor-based and offset-based pagination
"""
from typing import List, Dict, Any, Optional
from django.core.paginator import Paginator
import hashlib
import base64


class CursorPaginator:
    """
    Cursor-based pagination for large result sets
    
    More efficient than offset-based pagination for large datasets
    """
    
    def __init__(self, items: List[Dict], page_size: int = 10, cursor_field: str = 'id'):
        """
        Initialize cursor paginator
        
        Args:
            items: List of items to paginate
            page_size: Number of items per page
            cursor_field: Field to use for cursor (must be unique)
        """
        self.items = items
        self.page_size = page_size
        self.cursor_field = cursor_field
    
    def get_page(self, cursor: Optional[str] = None) -> Dict[str, Any]:
        """
        Get page starting from cursor
        
        Args:
            cursor: Base64-encoded cursor (None for first page)
            
        Returns:
            Dict with:
                - items: List of items on this page
                - next_cursor: Cursor for next page (None if last page)
                - prev_cursor: Cursor for previous page (None if first page)
                - has_next: Boolean indicating if there's a next page
                - has_prev: Boolean indicating if there's a previous page
                - total_items: Total number of items
        """
        if not self.items:
            return {
                'items': [],
                'next_cursor': None,
                'prev_cursor': None,
                'has_next': False,
                'has_prev': False,
                'total_items': 0
            }
        
        # Decode cursor if provided
        start_index = 0
        if cursor:
            try:
                decoded = base64.b64decode(cursor.encode()).decode()
                start_index = int(decoded)
            except Exception:
                start_index = 0
        
        # Get page items
        end_index = min(start_index + self.page_size, len(self.items))
        page_items = self.items[start_index:end_index]
        
        # Generate cursors
        next_cursor = None
        if end_index < len(self.items):
            next_cursor = self._encode_cursor(end_index)
        
        prev_cursor = None
        if start_index > 0:
            prev_cursor = self._encode_cursor(max(0, start_index - self.page_size))
        
        return {
            'items': page_items,
            'next_cursor': next_cursor,
            'prev_cursor': prev_cursor,
            'has_next': end_index < len(self.items),
            'has_prev': start_index > 0,
            'total_items': len(self.items),
            'page_size': self.page_size,
            'current_start': start_index,
            'current_end': end_index
        }
    
    def _encode_cursor(self, index: int) -> str:
        """Encode index as base64 cursor"""
        return base64.b64encode(str(index).encode()).decode()
    
    @staticmethod
    def decode_cursor(cursor: str) -> Optional[int]:
        """Decode base64 cursor to index"""
        try:
            decoded = base64.b64decode(cursor.encode()).decode()
            return int(decoded)
        except Exception:
            return None


class OffsetPaginator:
    """
    Simple offset-based pagination
    """
    
    def __init__(self, items: List[Dict], page_size: int = 10):
        """
        Initialize offset paginator
        
        Args:
            items: List of items to paginate
            page_size: Number of items per page
        """
        self.paginator = Paginator(items, page_size)
    
    def get_page(self, page_number: int = 1) -> Dict[str, Any]:
        """
        Get page by page number
        
        Args:
            page_number: Page number (1-indexed)
            
        Returns:
            Dict with pagination info and items
        """
        page = self.paginator.get_page(page_number)
        
        return {
            'items': list(page.object_list),
            'page_number': page.number,
            'num_pages': page.paginator.num_pages,
            'has_next': page.has_next(),
            'has_previous': page.has_previous(),
            'next_page_number': page.next_page_number() if page.has_next() else None,
            'previous_page_number': page.previous_page_number() if page.has_previous() else None,
            'total_items': page.paginator.count,
            'page_size': self.paginator.per_page
        }


def paginate_results(
    results: List[Dict],
    page_size: int = 10,
    cursor: Optional[str] = None,
    use_cursor: bool = True
) -> Dict[str, Any]:
    """
    Paginate results using cursor or offset pagination
    
    Args:
        results: List of result dictionaries
        page_size: Number of items per page
        cursor: Cursor for cursor-based pagination
        use_cursor: If True, use cursor-based pagination
        
    Returns:
        Paginated results dictionary
    """
    if use_cursor:
        paginator = CursorPaginator(results, page_size=page_size)
        return paginator.get_page(cursor)
    else:
        paginator = OffsetPaginator(results, page_size=page_size)
        # Extract page number from cursor if provided
        page_number = 1
        if cursor:
            decoded = CursorPaginator.decode_cursor(cursor)
            if decoded is not None:
                page_number = (decoded // page_size) + 1
        return paginator.get_page(page_number)

