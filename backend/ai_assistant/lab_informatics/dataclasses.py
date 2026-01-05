"""
Lab Informatics Data Classes

This module contains all dataclasses used in the Lab Informatics sidebar layout.
"""

from typing import Dict, Any, List, Optional
from dataclasses import dataclass, field
from datetime import datetime
from django.utils import timezone as django_timezone

from .enums import LabInformaticsProduct, TroubleshootingCategory, LabInformaticsCategory


@dataclass
class TroubleshootingItem:
    """Troubleshooting item structure"""
    id: str
    title: str
    category: TroubleshootingCategory
    severity: str
    description: str
    solution: str
    related_products: List[LabInformaticsProduct]
    tags: List[str]
    url: Optional[str] = None
    is_featured: bool = False
    view_count: int = 0
    last_updated: datetime = field(default_factory=lambda: django_timezone.now())


@dataclass
class LabInformaticsNavigationItem:
    """Lab Informatics navigation item structure"""
    id: str
    title: str
    type: str
    icon: Optional[str] = None
    url: Optional[str] = None
    children: List['LabInformaticsNavigationItem'] = field(default_factory=list)
    badge: Optional[str] = None
    tooltip: Optional[str] = None
    permissions: List[str] = field(default_factory=list)
    is_active: bool = False
    is_expanded: bool = False
    order: int = 0
    metadata: Dict[str, Any] = field(default_factory=dict)
    related_products: List[LabInformaticsProduct] = field(default_factory=list)
    troubleshooting_items: List[TroubleshootingItem] = field(default_factory=list)


@dataclass
class LabInformaticsSidebarSection:
    """Lab Informatics sidebar section structure"""
    id: str
    title: str
    icon: str
    items: List[LabInformaticsNavigationItem]
    order: int
    is_collapsible: bool = True
    is_collapsed: bool = False
    permissions: List[str] = field(default_factory=list)
    category: Optional[LabInformaticsCategory] = None


@dataclass
class LabInformaticsSidebarLayout:
    """Lab Informatics sidebar layout structure"""
    id: str
    name: str
    description: str
    sections: List[LabInformaticsSidebarSection]
    theme: str = "lab-informatics"
    width: str = "320px"
    is_resizable: bool = True
    show_search: bool = True
    show_user_info: bool = True
    show_notifications: bool = True
    show_troubleshooting: bool = True
    created_at: datetime = field(default_factory=lambda: django_timezone.now())
    updated_at: datetime = field(default_factory=lambda: django_timezone.now())

