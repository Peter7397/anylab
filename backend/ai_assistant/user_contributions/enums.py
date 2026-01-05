"""
User Contribution Enumerations

This module contains all enumerations used in the User Contribution Dashboard.
"""

from enum import Enum


class ContributionType(Enum):
    """Contribution type enumeration"""
    FILE_UPLOAD = "file_upload"
    URL_SUBMISSION = "url_submission"
    CONTENT_REVIEW = "content_review"
    METADATA_EDIT = "metadata_edit"
    CATEGORIZATION = "categorization"
    TRANSLATION = "translation"
    ANNOTATION = "annotation"
    COMMENT = "comment"
    RATING = "rating"
    SHARE = "share"
    DOWNLOAD = "download"
    VIEW = "view"
    SEARCH = "search"
    FEEDBACK = "feedback"
    BUG_REPORT = "bug_report"
    FEATURE_REQUEST = "feature_request"
    COMMUNITY_POST = "community_post"
    EXPERT_ANSWER = "expert_answer"
    TUTORIAL_CREATION = "tutorial_creation"
    DOCUMENTATION_UPDATE = "documentation_update"


class ContributionStatus(Enum):
    """Contribution status enumeration"""
    PENDING = "pending"
    APPROVED = "approved"
    REJECTED = "rejected"
    UNDER_REVIEW = "under_review"
    PUBLISHED = "published"
    ARCHIVED = "archived"
    DELETED = "deleted"
    DRAFT = "draft"
    SUBMITTED = "submitted"
    PROCESSING = "processing"
    COMPLETED = "completed"
    FAILED = "failed"


class UserRole(Enum):
    """User role enumeration"""
    VIEWER = "viewer"
    CONTRIBUTOR = "contributor"
    REVIEWER = "reviewer"
    MODERATOR = "moderator"
    ADMIN = "admin"
    EXPERT = "expert"
    TRANSLATOR = "translator"
    CURATOR = "curator"


class AchievementType(Enum):
    """Achievement type enumeration"""
    FIRST_CONTRIBUTION = "first_contribution"
    CONTRIBUTION_MILESTONE = "contribution_milestone"
    QUALITY_CONTRIBUTOR = "quality_contributor"
    EXPERT_REVIEWER = "expert_reviewer"
    COMMUNITY_HELPER = "community_helper"
    TRANSLATION_EXPERT = "translation_expert"
    DOCUMENTATION_MASTER = "documentation_master"
    TUTORIAL_CREATOR = "tutorial_creator"
    BUG_HUNTER = "bug_hunter"
    FEATURE_ADVOCATE = "feature_advocate"

