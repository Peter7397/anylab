"""
Base Section Builder

This module provides the base class and utilities for section builders.
"""

import logging
from typing import List
from ..dataclasses import LabInformaticsSidebarSection, LabInformaticsNavigationItem

logger = logging.getLogger(__name__)


class BaseSectionBuilder:
    """Base class for section builders"""
    
    @staticmethod
    def create_error_section(section_id: str, title: str, icon: str, order: int) -> LabInformaticsSidebarSection:
        """Create an error fallback section"""
        logger.error(f"Error creating {section_id} section")
        return LabInformaticsSidebarSection(
            id=section_id,
            title=title,
            icon=icon,
            items=[],
            order=order
        )

