"""
Analytics Generators for User Contribution Dashboard

This module contains functions for generating analytics data and trends.
"""

import logging
from typing import Dict, Any, List
from datetime import datetime, timedelta
from ..dataclasses import UserContribution

logger = logging.getLogger(__name__)


def calculate_reputation_score(contributions: List[UserContribution]) -> float:
    """Calculate reputation score based on contributions"""
    try:
        if not contributions:
            return 0.0
        
        # Base score from points
        total_points = sum(c.points_earned for c in contributions)
        
        # Quality multiplier
        avg_quality = sum(c.quality_score for c in contributions) / len(contributions) if contributions else 0.0
        
        # Engagement multiplier
        total_engagement = sum(
            c.view_count + c.download_count + c.share_count + c.comment_count
            for c in contributions
        )
        
        # Approval rate
        approved_count = len([c for c in contributions if c.status.value == 'approved'])
        approval_rate = approved_count / len(contributions) if contributions else 0.0
        
        # Calculate reputation score
        reputation = (
            total_points * 0.4 +
            avg_quality * 10 * 0.3 +
            (total_engagement / max(len(contributions), 1)) * 0.2 +
            approval_rate * 100 * 0.1
        )
        
        return min(100.0, max(0.0, reputation))
        
    except Exception as e:
        logger.error(f"Error calculating reputation score: {e}")
        return 0.0


def generate_contribution_trend(contributions: List[UserContribution], 
                                start_date: datetime, 
                                end_date: datetime) -> List[Dict[str, Any]]:
    """Generate contribution trend data"""
    try:
        trend = []
        current_date = start_date
        
        while current_date <= end_date:
            next_date = current_date + timedelta(days=1)
            count = len([
                c for c in contributions
                if current_date <= c.created_at < next_date
            ])
            
            trend.append({
                'date': current_date.isoformat(),
                'count': count
            })
            
            current_date = next_date
        
        return trend
        
    except Exception as e:
        logger.error(f"Error generating contribution trend: {e}")
        return []


def generate_quality_trend(contributions: List[UserContribution], 
                           start_date: datetime, 
                           end_date: datetime) -> List[Dict[str, Any]]:
    """Generate quality trend data"""
    try:
        trend = []
        current_date = start_date
        
        while current_date <= end_date:
            next_date = current_date + timedelta(days=1)
            day_contributions = [
                c for c in contributions
                if current_date <= c.created_at < next_date
            ]
            
            avg_quality = (
                sum(c.quality_score for c in day_contributions) / len(day_contributions)
                if day_contributions else 0.0
            )
            
            trend.append({
                'date': current_date.isoformat(),
                'average_quality': avg_quality,
                'count': len(day_contributions)
            })
            
            current_date = next_date
        
        return trend
        
    except Exception as e:
        logger.error(f"Error generating quality trend: {e}")
        return []


def generate_engagement_trend(contributions: List[UserContribution], 
                               start_date: datetime, 
                               end_date: datetime) -> List[Dict[str, Any]]:
    """Generate engagement trend data"""
    try:
        trend = []
        current_date = start_date
        
        while current_date <= end_date:
            next_date = current_date + timedelta(days=1)
            day_contributions = [
                c for c in contributions
                if current_date <= c.created_at < next_date
            ]
            
            total_views = sum(c.view_count for c in day_contributions)
            total_downloads = sum(c.download_count for c in day_contributions)
            total_shares = sum(c.share_count for c in day_contributions)
            total_comments = sum(c.comment_count for c in day_contributions)
            
            trend.append({
                'date': current_date.isoformat(),
                'views': total_views,
                'downloads': total_downloads,
                'shares': total_shares,
                'comments': total_comments,
                'total_engagement': total_views + total_downloads + total_shares + total_comments
            })
            
            current_date = next_date
        
        return trend
        
    except Exception as e:
        logger.error(f"Error generating engagement trend: {e}")
        return []

