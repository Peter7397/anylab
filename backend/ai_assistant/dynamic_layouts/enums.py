"""
Dynamic Layout Enumerations

This module contains all enumerations used in the Dynamic Content Layout system.
"""

from enum import Enum


class LayoutType(Enum):
    """Layout type enumeration"""
    GRID = "grid"
    LIST = "list"
    CARD = "card"
    TABLE = "table"
    TIMELINE = "timeline"
    DASHBOARD = "dashboard"
    GALLERY = "gallery"
    MAGAZINE = "magazine"
    SIDEBAR = "sidebar"
    FULLSCREEN = "fullscreen"


class ContentType(Enum):
    """Content type enumeration"""
    TEXT = "text"
    IMAGE = "image"
    VIDEO = "video"
    AUDIO = "audio"
    DOCUMENT = "document"
    LINK = "link"
    EMBED = "embed"
    WIDGET = "widget"
    CHART = "chart"
    FORM = "form"
    NAVIGATION = "navigation"
    SEARCH = "search"
    FILTER = "filter"
    PAGINATION = "pagination"


class ResponsiveBreakpoint(Enum):
    """Responsive breakpoint enumeration"""
    MOBILE = "mobile"  # < 768px
    TABLET = "tablet"  # 768px - 1024px
    DESKTOP = "desktop"  # > 1024px
    LARGE_DESKTOP = "large_desktop"  # > 1440px


class LayoutOrientation(Enum):
    """Layout orientation enumeration"""
    HORIZONTAL = "horizontal"
    VERTICAL = "vertical"
    MIXED = "mixed"

