"""
Widget Builders for User Contribution Dashboard

This module contains functions for building dashboard widgets and layouts.
"""

import logging
from typing import Dict, Any, List
from ..dataclasses import DashboardWidget

logger = logging.getLogger(__name__)


def create_default_widgets() -> Dict[str, DashboardWidget]:
    """Create default dashboard widgets"""
    try:
        widgets = [
            DashboardWidget(
                id="contribution_summary",
                name="Contribution Summary",
                type="metric",
                title="My Contributions",
                description="Overview of your contributions",
                data_source="user_contributions",
                config={
                    "metrics": ["total_contributions", "approved_contributions", "pending_contributions", "total_points"]
                },
                position=(0, 0),
                size=(2, 1)
            ),
            DashboardWidget(
                id="contribution_trend",
                name="Contribution Trend",
                type="chart",
                title="Contribution Trend",
                description="Your contribution activity over time",
                data_source="contribution_analytics",
                config={
                    "chart_type": "line",
                    "x_axis": "date",
                    "y_axis": "count",
                    "period": "30_days"
                },
                position=(0, 2),
                size=(3, 2)
            ),
            DashboardWidget(
                id="quality_score",
                name="Quality Score",
                type="progress",
                title="Quality Score",
                description="Your content quality rating",
                data_source="user_quality",
                config={
                    "max_value": 100,
                    "color": "green"
                },
                position=(0, 5),
                size=(1, 1)
            ),
            DashboardWidget(
                id="recent_contributions",
                name="Recent Contributions",
                type="list",
                title="Recent Contributions",
                description="Your latest contributions",
                data_source="recent_contributions",
                config={
                    "limit": 10,
                    "show_status": True
                },
                position=(1, 0),
                size=(2, 2)
            ),
            DashboardWidget(
                id="contribution_types",
                name="Contribution Types",
                type="chart",
                title="Contribution Types",
                description="Breakdown by contribution type",
                data_source="contribution_types",
                config={
                    "chart_type": "pie",
                    "show_percentages": True
                },
                position=(1, 2),
                size=(2, 2)
            ),
            DashboardWidget(
                id="achievements",
                name="Achievements",
                type="list",
                title="Achievements",
                description="Your unlocked achievements",
                data_source="user_achievements",
                config={
                    "show_badges": True,
                    "limit": 5
                },
                position=(1, 4),
                size=(2, 2)
            ),
            DashboardWidget(
                id="engagement_metrics",
                name="Engagement Metrics",
                type="metric",
                title="Engagement",
                description="How your content is performing",
                data_source="engagement_metrics",
                config={
                    "metrics": ["total_views", "total_downloads", "total_shares", "average_rating"]
                },
                position=(2, 0),
                size=(2, 1)
            ),
            DashboardWidget(
                id="top_categories",
                name="Top Categories",
                type="list",
                title="Top Categories",
                description="Your most active categories",
                data_source="top_categories",
                config={
                    "limit": 5,
                    "show_counts": True
                },
                position=(2, 2),
                size=(2, 1)
            ),
            DashboardWidget(
                id="reputation_score",
                name="Reputation Score",
                type="metric",
                title="Reputation",
                description="Your community reputation",
                data_source="reputation_score",
                config={
                    "show_trend": True
                },
                position=(2, 4),
                size=(2, 1)
            )
        ]
        
        return {widget.id: widget for widget in widgets}
        
    except Exception as e:
        logger.error(f"Error creating default widgets: {e}")
        return {}


def create_dashboard_layouts() -> Dict[str, Dict[str, Any]]:
    """Create dashboard layouts"""
    try:
        layouts = {
            "default": {
                "name": "Default Layout",
                "description": "Standard dashboard layout",
                "widgets": [
                    "contribution_summary",
                    "contribution_trend",
                    "quality_score",
                    "recent_contributions",
                    "contribution_types",
                    "achievements",
                    "engagement_metrics",
                    "top_categories",
                    "reputation_score"
                ],
                "grid_size": (3, 6),
                "responsive": True
            },
            "minimal": {
                "name": "Minimal Layout",
                "description": "Minimal dashboard layout",
                "widgets": [
                    "contribution_summary",
                    "recent_contributions",
                    "quality_score"
                ],
                "grid_size": (2, 3),
                "responsive": True
            },
            "detailed": {
                "name": "Detailed Layout",
                "description": "Detailed dashboard layout",
                "widgets": [
                    "contribution_summary",
                    "contribution_trend",
                    "quality_score",
                    "recent_contributions",
                    "contribution_types",
                    "achievements",
                    "engagement_metrics",
                    "top_categories",
                    "reputation_score"
                ],
                "grid_size": (4, 6),
                "responsive": True
            }
        }
        
        return layouts
        
    except Exception as e:
        logger.error(f"Error creating dashboard layouts: {e}")
        return {}

