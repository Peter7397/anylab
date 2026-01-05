"""
Dynamic Layout Data Classes

This module contains all dataclasses used in the Dynamic Content Layout system.
"""

from typing import Dict, Any, List, Optional, Tuple
from dataclasses import dataclass, field
from datetime import datetime
from django.utils import timezone as django_timezone

from .enums import LayoutType, ContentType, ResponsiveBreakpoint, LayoutOrientation


@dataclass
class LayoutBreakpoint:
    """Layout breakpoint configuration"""
    breakpoint: ResponsiveBreakpoint
    columns: int
    gap: str
    padding: str
    margin: str
    font_size: str
    line_height: str
    max_width: Optional[str] = None
    min_width: Optional[str] = None


@dataclass
class ContentBlock:
    """Content block structure"""
    id: str
    type: ContentType
    title: str
    content: Any
    metadata: Dict[str, Any] = field(default_factory=dict)
    style: Dict[str, Any] = field(default_factory=dict)
    responsive: Dict[ResponsiveBreakpoint, Dict[str, Any]] = field(default_factory=dict)
    order: int = 0
    is_visible: bool = True
    is_draggable: bool = True
    is_resizable: bool = False
    permissions: List[str] = field(default_factory=list)
    created_at: datetime = field(default_factory=lambda: django_timezone.now())
    updated_at: datetime = field(default_factory=lambda: django_timezone.now())


@dataclass
class LayoutSection:
    """Layout section structure"""
    id: str
    title: str
    blocks: List[ContentBlock]
    layout_type: LayoutType
    orientation: LayoutOrientation
    breakpoints: List[LayoutBreakpoint] = field(default_factory=list)
    style: Dict[str, Any] = field(default_factory=dict)
    metadata: Dict[str, Any] = field(default_factory=dict)
    order: int = 0
    is_collapsible: bool = False
    is_collapsed: bool = False
    permissions: List[str] = field(default_factory=list)
    created_at: datetime = field(default_factory=lambda: django_timezone.now())
    updated_at: datetime = field(default_factory=lambda: django_timezone.now())


@dataclass
class DynamicLayout:
    """Dynamic layout structure"""
    id: str
    name: str
    description: str
    sections: List[LayoutSection]
    layout_type: LayoutType
    orientation: LayoutOrientation
    breakpoints: List[LayoutBreakpoint] = field(default_factory=list)
    style: Dict[str, Any] = field(default_factory=dict)
    metadata: Dict[str, Any] = field(default_factory=dict)
    is_responsive: bool = True
    is_customizable: bool = True
    is_public: bool = False
    created_at: datetime = field(default_factory=lambda: django_timezone.now())
    updated_at: datetime = field(default_factory=lambda: django_timezone.now())


@dataclass
class UserLayoutPreference:
    """User layout preference structure"""
    user_id: str
    layout_id: str
    preferences: Dict[str, Any] = field(default_factory=dict)
    customizations: Dict[str, Any] = field(default_factory=dict)
    saved_layouts: List[str] = field(default_factory=list)
    created_at: datetime = field(default_factory=lambda: django_timezone.now())
    updated_at: datetime = field(default_factory=lambda: django_timezone.now())

