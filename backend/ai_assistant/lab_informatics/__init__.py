"""
Lab Informatics Module

This module provides the sidebar layout and navigation structure
for the Lab Informatics Focus mode of the AnyLab application.
"""

from .enums import (
    LabInformaticsProduct,
    LabInformaticsCategory,
    TroubleshootingCategory,
)
from .dataclasses import (
    TroubleshootingItem,
    LabInformaticsNavigationItem,
    LabInformaticsSidebarSection,
    LabInformaticsSidebarLayout,
)

__all__ = [
    'LabInformaticsProduct',
    'LabInformaticsCategory',
    'TroubleshootingCategory',
    'TroubleshootingItem',
    'LabInformaticsNavigationItem',
    'LabInformaticsSidebarSection',
    'LabInformaticsSidebarLayout',
]

