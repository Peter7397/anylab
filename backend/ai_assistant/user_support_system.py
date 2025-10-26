"""
User Support System for AnyLab AI Assistant

This module provides comprehensive user support capabilities including ticket management,
knowledge base integration, automated responses, escalation procedures, and support analytics.
"""

import os
import json
import logging
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional, Tuple
from dataclasses import dataclass, asdict
from enum import Enum
from django.conf import settings
from django.core.cache import cache
from django.utils import timezone
from django.contrib.auth.models import User

logger = logging.getLogger(__name__)


class SupportTicketStatus(Enum):
    """Support ticket status levels"""
    OPEN = "open"
    IN_PROGRESS = "in_progress"
    WAITING_FOR_USER = "waiting_for_user"
    RESOLVED = "resolved"
    CLOSED = "closed"
    ESCALATED = "escalated"


class SupportTicketPriority(Enum):
    """Support ticket priority levels"""
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"
    URGENT = "urgent"


class SupportTicketCategory(Enum):
    """Support ticket categories"""
    TECHNICAL_ISSUE = "technical_issue"
    FEATURE_REQUEST = "feature_request"
    BUG_REPORT = "bug_report"
    ACCOUNT_ISSUE = "account_issue"
    BILLING_ISSUE = "billing_issue"
    GENERAL_INQUIRY = "general_inquiry"
    DOCUMENTATION_REQUEST = "documentation_request"
    TRAINING_REQUEST = "training_request"


class SupportChannel(Enum):
    """Support communication channels"""
    EMAIL = "email"
    CHAT = "chat"
    PHONE = "phone"
    TICKET_SYSTEM = "ticket_system"
    FORUM = "forum"
    AI_ASSISTANT = "ai_assistant"


class SupportAgentRole(Enum):
    """Support agent roles"""
    LEVEL_1 = "level_1"
    LEVEL_2 = "level_2"
    LEVEL_3 = "level_3"
    SPECIALIST = "specialist"
    MANAGER = "manager"
    ADMIN = "admin"


@dataclass
class SupportTicket:
    """Support ticket data structure"""
    id: str
    title: str
    description: str
    category: SupportTicketCategory
    priority: SupportTicketPriority
    status: SupportTicketStatus
    created_by: str
    assigned_to: Optional[str]
    created_at: datetime
    updated_at: datetime
    resolved_at: Optional[datetime]
    tags: List[str]
    attachments: List[str]
    related_tickets: List[str]
    escalation_history: List[Dict[str, Any]]
    resolution_notes: Optional[str]
    satisfaction_rating: Optional[int]
    channel: SupportChannel


@dataclass
class SupportAgent:
    """Support agent information"""
    user_id: str
    name: str
    email: str
    role: SupportAgentRole
    specializations: List[str]
    active_tickets: int
    max_tickets: int
    availability_status: str
    response_time_avg: float
    resolution_rate: float
    satisfaction_score: float


@dataclass
class SupportKnowledge:
    """Knowledge base entry for support"""
    id: str
    title: str
    content: str
    category: SupportTicketCategory
    tags: List[str]
    created_at: datetime
    updated_at: datetime
    author: str
    views: int
    helpful_votes: int
    status: str
    related_articles: List[str]


class SupportTicketManager:
    """Manages support tickets and their lifecycle"""
    
    def __init__(self):
        self.tickets = {}
        self.ticket_counter = 0
        self.escalation_rules = self._initialize_escalation_rules()
    
    def _initialize_escalation_rules(self) -> Dict[str, Any]:
        """Initialize escalation rules for different scenarios"""
        return {
            "priority_escalation": {
                SupportTicketPriority.CRITICAL: {"escalate_after_hours": 1},
                SupportTicketPriority.URGENT: {"escalate_after_hours": 4},
                SupportTicketPriority.HIGH: {"escalate_after_hours": 24},
                SupportTicketPriority.MEDIUM: {"escalate_after_hours": 72},
                SupportTicketPriority.LOW: {"escalate_after_hours": 168}  # 1 week
            },
            "category_escalation": {
                SupportTicketCategory.TECHNICAL_ISSUE: {"escalate_to": SupportAgentRole.LEVEL_2},
                SupportTicketCategory.BUG_REPORT: {"escalate_to": SupportAgentRole.SPECIALIST},
                SupportTicketCategory.BILLING_ISSUE: {"escalate_to": SupportAgentRole.MANAGER}
            }
        }
    
    def create_ticket(self, title: str, description: str, category: SupportTicketCategory,
                     priority: SupportTicketPriority, created_by: str, 
                     channel: SupportChannel = SupportChannel.TICKET_SYSTEM) -> SupportTicket:
        """Create a new support ticket"""
        self.ticket_counter += 1
        ticket_id = f"TICKET-{self.ticket_counter:06d}"
        
        ticket = SupportTicket(
            id=ticket_id,
            title=title,
            description=description,
            category=category,
            priority=priority,
            status=SupportTicketStatus.OPEN,
            created_by=created_by,
            assigned_to=None,
            created_at=timezone.now(),
            updated_at=timezone.now(),
            resolved_at=None,
            tags=[],
            attachments=[],
            related_tickets=[],
            escalation_history=[],
            resolution_notes=None,
            satisfaction_rating=None,
            channel=channel
        )
        
        self.tickets[ticket_id] = ticket
        
        # Auto-assign ticket based on rules
        self._auto_assign_ticket(ticket)
        
        # Check for escalation
        self._check_escalation_rules(ticket)
        
        logger.info(f"Created support ticket: {ticket_id}")
        return ticket
    
    def _auto_assign_ticket(self, ticket: SupportTicket):
        """Auto-assign ticket based on category and availability"""
        # In a real implementation, this would query available agents
        # For now, we'll simulate assignment logic
        
        if ticket.category == SupportTicketCategory.TECHNICAL_ISSUE:
            ticket.assigned_to = "agent_tech_001"
        elif ticket.category == SupportTicketCategory.BILLING_ISSUE:
            ticket.assigned_to = "agent_billing_001"
        else:
            ticket.assigned_to = "agent_general_001"
        
        ticket.status = SupportTicketStatus.IN_PROGRESS
        ticket.updated_at = timezone.now()
    
    def _check_escalation_rules(self, ticket: SupportTicket):
        """Check if ticket should be escalated based on rules"""
        escalation_time = self.escalation_rules["priority_escalation"].get(
            ticket.priority, {}
        ).get("escalate_after_hours", 168)
        
        # Schedule escalation check
        escalation_time_delta = timedelta(hours=escalation_time)
        escalation_time = ticket.created_at + escalation_time_delta
        
        # In a real implementation, this would schedule a background task
        logger.info(f"Ticket {ticket.id} will be checked for escalation at {escalation_time}")
    
    def update_ticket_status(self, ticket_id: str, status: SupportTicketStatus, 
                           notes: Optional[str] = None) -> bool:
        """Update ticket status"""
        if ticket_id not in self.tickets:
            return False
        
        ticket = self.tickets[ticket_id]
        ticket.status = status
        ticket.updated_at = timezone.now()
        
        if status == SupportTicketStatus.RESOLVED:
            ticket.resolved_at = timezone.now()
            if notes:
                ticket.resolution_notes = notes
        
        logger.info(f"Updated ticket {ticket_id} status to {status.value}")
        return True
    
    def assign_ticket(self, ticket_id: str, agent_id: str) -> bool:
        """Assign ticket to a support agent"""
        if ticket_id not in self.tickets:
            return False
        
        ticket = self.tickets[ticket_id]
        ticket.assigned_to = agent_id
        ticket.status = SupportTicketStatus.IN_PROGRESS
        ticket.updated_at = timezone.now()
        
        logger.info(f"Assigned ticket {ticket_id} to agent {agent_id}")
        return True
    
    def escalate_ticket(self, ticket_id: str, reason: str, escalated_to: str) -> bool:
        """Escalate ticket to higher level support"""
        if ticket_id not in self.tickets:
            return False
        
        ticket = self.tickets[ticket_id]
        
        escalation_record = {
            "timestamp": timezone.now(),
            "reason": reason,
            "escalated_to": escalated_to,
            "escalated_by": ticket.assigned_to
        }
        
        ticket.escalation_history.append(escalation_record)
        ticket.status = SupportTicketStatus.ESCALATED
        ticket.assigned_to = escalated_to
        ticket.updated_at = timezone.now()
        
        logger.info(f"Escalated ticket {ticket_id} to {escalated_to}")
        return True
    
    def add_ticket_comment(self, ticket_id: str, comment: str, author: str) -> bool:
        """Add comment to ticket"""
        if ticket_id not in self.tickets:
            return False
        
        ticket = self.tickets[ticket_id]
        ticket.updated_at = timezone.now()
        
        # In a real implementation, comments would be stored separately
        logger.info(f"Added comment to ticket {ticket_id} by {author}")
        return True
    
    def get_ticket(self, ticket_id: str) -> Optional[SupportTicket]:
        """Get ticket by ID"""
        return self.tickets.get(ticket_id)
    
    def get_tickets_by_user(self, user_id: str) -> List[SupportTicket]:
        """Get all tickets created by a user"""
        return [ticket for ticket in self.tickets.values() 
                if ticket.created_by == user_id]
    
    def get_tickets_by_agent(self, agent_id: str) -> List[SupportTicket]:
        """Get all tickets assigned to an agent"""
        return [ticket for ticket in self.tickets.values() 
                if ticket.assigned_to == agent_id]
    
    def search_tickets(self, query: str, filters: Dict[str, Any] = None) -> List[SupportTicket]:
        """Search tickets based on query and filters"""
        results = []
        
        for ticket in self.tickets.values():
            # Text search
            if query.lower() in ticket.title.lower() or query.lower() in ticket.description.lower():
                # Apply filters
                if filters:
                    if "status" in filters and ticket.status != filters["status"]:
                        continue
                    if "priority" in filters and ticket.priority != filters["priority"]:
                        continue
                    if "category" in filters and ticket.category != filters["category"]:
                        continue
                
                results.append(ticket)
        
        return results


class SupportKnowledgeManager:
    """Manages support knowledge base"""
    
    def __init__(self):
        self.knowledge_articles = {}
        self.article_counter = 0
        self.search_index = {}
    
    def create_article(self, title: str, content: str, category: SupportTicketCategory,
                      author: str, tags: List[str] = None) -> SupportKnowledge:
        """Create a new knowledge base article"""
        self.article_counter += 1
        article_id = f"KB-{self.article_counter:06d}"
        
        article = SupportKnowledge(
            id=article_id,
            title=title,
            content=content,
            category=category,
            tags=tags or [],
            created_at=timezone.now(),
            updated_at=timezone.now(),
            author=author,
            views=0,
            helpful_votes=0,
            status="published",
            related_articles=[]
        )
        
        self.knowledge_articles[article_id] = article
        self._update_search_index(article)
        
        logger.info(f"Created knowledge article: {article_id}")
        return article
    
    def _update_search_index(self, article: SupportKnowledge):
        """Update search index for article"""
        # Simple keyword indexing
        keywords = article.title.lower().split() + article.content.lower().split()
        
        for keyword in keywords:
            if keyword not in self.search_index:
                self.search_index[keyword] = []
            if article.id not in self.search_index[keyword]:
                self.search_index[keyword].append(article.id)
    
    def search_articles(self, query: str, category: Optional[SupportTicketCategory] = None) -> List[SupportKnowledge]:
        """Search knowledge base articles"""
        results = []
        query_words = query.lower().split()
        
        for article in self.knowledge_articles.values():
            if category and article.category != category:
                continue
            
            # Check if any query words match
            article_text = f"{article.title} {article.content}".lower()
            if any(word in article_text for word in query_words):
                results.append(article)
        
        # Sort by relevance (simple scoring)
        results.sort(key=lambda x: x.helpful_votes + x.views, reverse=True)
        return results
    
    def get_article(self, article_id: str) -> Optional[SupportKnowledge]:
        """Get article by ID"""
        article = self.knowledge_articles.get(article_id)
        if article:
            article.views += 1
        return article
    
    def update_article(self, article_id: str, updates: Dict[str, Any]) -> bool:
        """Update knowledge base article"""
        if article_id not in self.knowledge_articles:
            return False
        
        article = self.knowledge_articles[article_id]
        
        if "title" in updates:
            article.title = updates["title"]
        if "content" in updates:
            article.content = updates["content"]
        if "tags" in updates:
            article.tags = updates["tags"]
        
        article.updated_at = timezone.now()
        
        logger.info(f"Updated knowledge article: {article_id}")
        return True
    
    def vote_article(self, article_id: str, helpful: bool) -> bool:
        """Vote on article helpfulness"""
        if article_id not in self.knowledge_articles:
            return False
        
        article = self.knowledge_articles[article_id]
        if helpful:
            article.helpful_votes += 1
        
        logger.info(f"Voted on article {article_id}: {helpful}")
        return True


class SupportAgentManager:
    """Manages support agents and their assignments"""
    
    def __init__(self):
        self.agents = {}
        self.workload_distribution = {}
    
    def register_agent(self, user_id: str, name: str, email: str, role: SupportAgentRole,
                      specializations: List[str] = None) -> SupportAgent:
        """Register a new support agent"""
        agent = SupportAgent(
            user_id=user_id,
            name=name,
            email=email,
            role=role,
            specializations=specializations or [],
            active_tickets=0,
            max_tickets=self._get_max_tickets_for_role(role),
            availability_status="available",
            response_time_avg=0.0,
            resolution_rate=0.0,
            satisfaction_score=0.0
        )
        
        self.agents[user_id] = agent
        logger.info(f"Registered support agent: {user_id}")
        return agent
    
    def _get_max_tickets_for_role(self, role: SupportAgentRole) -> int:
        """Get maximum tickets for agent role"""
        max_tickets = {
            SupportAgentRole.LEVEL_1: 20,
            SupportAgentRole.LEVEL_2: 15,
            SupportAgentRole.LEVEL_3: 10,
            SupportAgentRole.SPECIALIST: 8,
            SupportAgentRole.MANAGER: 5,
            SupportAgentRole.ADMIN: 3
        }
        return max_tickets.get(role, 10)
    
    def get_available_agents(self, category: Optional[SupportTicketCategory] = None) -> List[SupportAgent]:
        """Get available agents for ticket assignment"""
        available_agents = []
        
        for agent in self.agents.values():
            if (agent.availability_status == "available" and 
                agent.active_tickets < agent.max_tickets):
                
                # Check specialization match
                if category and agent.specializations:
                    category_match = any(
                        cat.value in agent.specializations 
                        for cat in [category]
                    )
                    if not category_match:
                        continue
                
                available_agents.append(agent)
        
        # Sort by workload (least busy first)
        available_agents.sort(key=lambda x: x.active_tickets)
        return available_agents
    
    def update_agent_workload(self, agent_id: str, ticket_count: int):
        """Update agent's current ticket workload"""
        if agent_id in self.agents:
            self.agents[agent_id].active_tickets = ticket_count
    
    def update_agent_metrics(self, agent_id: str, response_time: float, 
                           resolution_rate: float, satisfaction_score: float):
        """Update agent performance metrics"""
        if agent_id in self.agents:
            agent = self.agents[agent_id]
            agent.response_time_avg = response_time
            agent.resolution_rate = resolution_rate
            agent.satisfaction_score = satisfaction_score


class SupportAnalytics:
    """Provides analytics and reporting for support operations"""
    
    def __init__(self, ticket_manager: SupportTicketManager, 
                 agent_manager: SupportAgentManager):
        self.ticket_manager = ticket_manager
        self.agent_manager = agent_manager
    
    def get_ticket_statistics(self, start_date: datetime, end_date: datetime) -> Dict[str, Any]:
        """Get ticket statistics for a date range"""
        tickets_in_range = [
            ticket for ticket in self.ticket_manager.tickets.values()
            if start_date <= ticket.created_at <= end_date
        ]
        
        stats = {
            "total_tickets": len(tickets_in_range),
            "by_status": {},
            "by_priority": {},
            "by_category": {},
            "resolution_time_avg": 0.0,
            "satisfaction_avg": 0.0
        }
        
        # Count by status
        for ticket in tickets_in_range:
            status = ticket.status.value
            stats["by_status"][status] = stats["by_status"].get(status, 0) + 1
        
        # Count by priority
        for ticket in tickets_in_range:
            priority = ticket.priority.value
            stats["by_priority"][priority] = stats["by_priority"].get(priority, 0) + 1
        
        # Count by category
        for ticket in tickets_in_range:
            category = ticket.category.value
            stats["by_category"][category] = stats["by_category"].get(category, 0) + 1
        
        # Calculate average resolution time
        resolved_tickets = [t for t in tickets_in_range if t.resolved_at]
        if resolved_tickets:
            total_resolution_time = sum(
                (t.resolved_at - t.created_at).total_seconds() 
                for t in resolved_tickets
            )
            stats["resolution_time_avg"] = total_resolution_time / len(resolved_tickets)
        
        # Calculate average satisfaction
        rated_tickets = [t for t in tickets_in_range if t.satisfaction_rating is not None]
        if rated_tickets:
            stats["satisfaction_avg"] = sum(t.satisfaction_rating for t in rated_tickets) / len(rated_tickets)
        
        return stats
    
    def get_agent_performance(self, agent_id: str, start_date: datetime, 
                            end_date: datetime) -> Dict[str, Any]:
        """Get performance metrics for a specific agent"""
        agent_tickets = [
            ticket for ticket in self.ticket_manager.tickets.values()
            if (ticket.assigned_to == agent_id and 
                start_date <= ticket.created_at <= end_date)
        ]
        
        performance = {
            "tickets_assigned": len(agent_tickets),
            "tickets_resolved": len([t for t in agent_tickets if t.status == SupportTicketStatus.RESOLVED]),
            "resolution_rate": 0.0,
            "avg_resolution_time": 0.0,
            "satisfaction_score": 0.0,
            "escalation_rate": 0.0
        }
        
        if agent_tickets:
            resolved_tickets = [t for t in agent_tickets if t.status == SupportTicketStatus.RESOLVED]
            performance["resolution_rate"] = len(resolved_tickets) / len(agent_tickets)
            
            if resolved_tickets:
                total_time = sum(
                    (t.resolved_at - t.created_at).total_seconds() 
                    for t in resolved_tickets if t.resolved_at
                )
                performance["avg_resolution_time"] = total_time / len(resolved_tickets)
            
            rated_tickets = [t for t in agent_tickets if t.satisfaction_rating is not None]
            if rated_tickets:
                performance["satisfaction_score"] = sum(t.satisfaction_rating for t in rated_tickets) / len(rated_tickets)
            
            escalated_tickets = [t for t in agent_tickets if t.status == SupportTicketStatus.ESCALATED]
            performance["escalation_rate"] = len(escalated_tickets) / len(agent_tickets)
        
        return performance
    
    def generate_support_report(self, start_date: datetime, end_date: datetime) -> Dict[str, Any]:
        """Generate comprehensive support report"""
        ticket_stats = self.get_ticket_statistics(start_date, end_date)
        
        report = {
            "period": {
                "start": start_date,
                "end": end_date
            },
            "ticket_statistics": ticket_stats,
            "agent_performance": {},
            "trends": {},
            "recommendations": []
        }
        
        # Get agent performance
        for agent_id in self.agent_manager.agents:
            report["agent_performance"][agent_id] = self.get_agent_performance(
                agent_id, start_date, end_date
            )
        
        # Generate recommendations
        if ticket_stats["resolution_time_avg"] > 86400:  # More than 24 hours
            report["recommendations"].append("Consider increasing support staff or improving processes")
        
        if ticket_stats["satisfaction_avg"] < 4.0:
            report["recommendations"].append("Focus on improving customer satisfaction")
        
        return report


class SupportAutomation:
    """Provides automated support features"""
    
    def __init__(self, knowledge_manager: SupportKnowledgeManager):
        self.knowledge_manager = knowledge_manager
        self.auto_responses = self._initialize_auto_responses()
    
    def _initialize_auto_responses(self) -> Dict[str, str]:
        """Initialize automated response templates"""
        return {
            "welcome": "Thank you for contacting AnyLab support. We have received your ticket and will respond within 24 hours.",
            "acknowledgment": "We have received your message and assigned it to our support team.",
            "resolution": "Your ticket has been resolved. Please let us know if you need any further assistance.",
            "escalation": "Your ticket has been escalated to our senior support team for faster resolution."
        }
    
    def suggest_solutions(self, ticket: SupportTicket) -> List[SupportKnowledge]:
        """Suggest knowledge base articles based on ticket content"""
        query = f"{ticket.title} {ticket.description}"
        suggestions = self.knowledge_manager.search_articles(query, ticket.category)
        
        # Return top 3 suggestions
        return suggestions[:3]
    
    def auto_categorize_ticket(self, title: str, description: str) -> SupportTicketCategory:
        """Automatically categorize ticket based on content"""
        content = f"{title} {description}".lower()
        
        # Simple keyword-based categorization
        if any(word in content for word in ["bug", "error", "crash", "broken"]):
            return SupportTicketCategory.BUG_REPORT
        elif any(word in content for word in ["feature", "enhancement", "improvement"]):
            return SupportTicketCategory.FEATURE_REQUEST
        elif any(word in content for word in ["billing", "payment", "invoice", "charge"]):
            return SupportTicketCategory.BILLING_ISSUE
        elif any(word in content for word in ["account", "login", "password", "access"]):
            return SupportTicketCategory.ACCOUNT_ISSUE
        elif any(word in content for word in ["documentation", "help", "guide", "tutorial"]):
            return SupportTicketCategory.DOCUMENTATION_REQUEST
        else:
            return SupportTicketCategory.GENERAL_INQUIRY
    
    def auto_assign_priority(self, ticket: SupportTicket) -> SupportTicketPriority:
        """Automatically assign priority based on content and keywords"""
        content = f"{ticket.title} {ticket.description}".lower()
        
        # Critical keywords
        if any(word in content for word in ["urgent", "critical", "down", "outage", "emergency"]):
            return SupportTicketPriority.CRITICAL
        
        # High priority keywords
        elif any(word in content for word in ["important", "asap", "blocking", "cannot work"]):
            return SupportTicketPriority.HIGH
        
        # Medium priority (default for most tickets)
        else:
            return SupportTicketPriority.MEDIUM


# Example usage and testing
if __name__ == "__main__":
    # Initialize support system
    ticket_manager = SupportTicketManager()
    knowledge_manager = SupportKnowledgeManager()
    agent_manager = SupportAgentManager()
    analytics = SupportAnalytics(ticket_manager, agent_manager)
    automation = SupportAutomation(knowledge_manager)
    
    # Register support agents
    agent1 = agent_manager.register_agent(
        "agent_001", "John Smith", "john@anylab.com", 
        SupportAgentRole.LEVEL_1, ["technical_issue", "general_inquiry"]
    )
    
    agent2 = agent_manager.register_agent(
        "agent_002", "Jane Doe", "jane@anylab.com", 
        SupportAgentRole.LEVEL_2, ["bug_report", "technical_issue"]
    )
    
    # Create knowledge base articles
    kb_article = knowledge_manager.create_article(
        "How to Reset Password",
        "To reset your password, click on 'Forgot Password' on the login page...",
        SupportTicketCategory.ACCOUNT_ISSUE,
        "admin",
        ["password", "login", "account"]
    )
    
    # Create a support ticket
    ticket = ticket_manager.create_ticket(
        "Cannot login to system",
        "I'm getting an error when trying to login. It says invalid credentials.",
        SupportTicketCategory.ACCOUNT_ISSUE,
        SupportTicketPriority.MEDIUM,
        "user_123"
    )
    
    print(f"Created ticket: {ticket.id}")
    print(f"Auto-assigned to: {ticket.assigned_to}")
    print(f"Status: {ticket.status.value}")
    
    # Search knowledge base
    suggestions = automation.suggest_solutions(ticket)
    print(f"Found {len(suggestions)} knowledge base suggestions")
    
    # Get analytics
    end_date = timezone.now()
    start_date = end_date - timedelta(days=30)
    
    stats = analytics.get_ticket_statistics(start_date, end_date)
    print(f"Ticket statistics: {stats}")
    
    print("\nSupport system initialized successfully!")
