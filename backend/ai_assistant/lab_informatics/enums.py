"""
Lab Informatics Enumerations

This module contains all enumerations used in the Lab Informatics sidebar layout.
"""

from enum import Enum


class LabInformaticsProduct(Enum):
    """Lab Informatics product enumeration"""
    OPENLAB_CDS = "openlab_cds"
    OPENLAB_ECM = "openlab_ecm"
    OPENLAB_CDS_2 = "openlab_cds_2"
    OPENLAB_CONNECT = "openlab_connect"
    OPENLAB_SHARED_SERVICES = "openlab_shared_services"
    OPENLAB_INFRASTRUCTURE = "openlab_infrastructure"
    MASSHUNTER = "masshunter"
    CHEMSTATION = "chemstation"
    VNMRJ = "vnmrj"
    AGILENT_CONNECT = "agilent_connect"
    AGILENT_CROSSLAB = "agilent_crosslab"


class LabInformaticsCategory(Enum):
    """Lab Informatics category enumeration"""
    DATA_MANAGEMENT = "data_management"
    WORKFLOW_AUTOMATION = "workflow_automation"
    COMPLIANCE = "compliance"
    INTEGRATION = "integration"
    ANALYTICS = "analytics"
    COLLABORATION = "collaboration"
    INFRASTRUCTURE = "infrastructure"
    SECURITY = "security"
    BACKUP_RECOVERY = "backup_recovery"
    MONITORING = "monitoring"


class TroubleshootingCategory(Enum):
    """Troubleshooting category enumeration"""
    INSTALLATION = "installation"
    CONFIGURATION = "configuration"
    CONNECTIVITY = "connectivity"
    PERFORMANCE = "performance"
    DATA_ISSUES = "data_issues"
    USER_ACCESS = "user_access"
    INTEGRATION = "integration"
    BACKUP_RESTORE = "backup_restore"
    SECURITY = "security"
    GENERAL = "general"

