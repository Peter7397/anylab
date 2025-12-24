"""
Lab Informatics Focus Sidebar Layout

This module provides the sidebar layout and navigation structure
for the Lab Informatics Focus mode of the AnyLab application.
"""

import logging
from typing import Dict, Any, List, Optional, Tuple
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from django.utils import timezone as django_timezone

logger = logging.getLogger(__name__)


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
    category: LabInformaticsCategory = None


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


class LabInformaticsSidebarLayoutManager:
    """Lab Informatics Focus Sidebar Layout Manager"""
    
    def __init__(self, config: Dict[str, Any] = None):
        """Initialize Lab Informatics sidebar layout"""
        self.config = config or {}
        self.layout_enabled = self.config.get('layout_enabled', True)
        self.troubleshooting_enabled = self.config.get('troubleshooting_enabled', True)
        self.dynamic_content_enabled = self.config.get('dynamic_content_enabled', True)
        self.user_preferences_enabled = self.config.get('user_preferences_enabled', True)
        self.analytics_enabled = self.config.get('analytics_enabled', True)
        
        # Layout configuration
        self.default_theme = self.config.get('default_theme', 'lab-informatics')
        self.default_width = self.config.get('default_width', '320px')
        self.collapsible_sections = self.config.get('collapsible_sections', True)
        self.remember_state = self.config.get('remember_state', True)
        
        # Troubleshooting configuration
        self.show_troubleshooting_counts = self.config.get('show_troubleshooting_counts', True)
        self.show_featured_troubleshooting = self.config.get('show_featured_troubleshooting', True)
        self.max_troubleshooting_items = self.config.get('max_troubleshooting_items', 10)
        
        # Content configuration
        self.show_product_counts = self.config.get('show_product_counts', True)
        self.show_recent_content = self.config.get('show_recent_content', True)
        self.show_popular_content = self.config.get('show_popular_content', True)
        self.max_recent_items = self.config.get('max_recent_items', 5)
        self.max_popular_items = self.config.get('max_popular_items', 5)
        
        # Initialize layout
        self._initialize_layout()
        
        logger.info("Lab Informatics Sidebar Layout initialized")
    
    def _initialize_layout(self):
        """Initialize the sidebar layout structure"""
        try:
            # Create main layout
            self.layout = LabInformaticsSidebarLayout(
                id="lab_informatics_sidebar",
                name="Lab Informatics Focus",
                description="Sidebar layout for Lab Informatics Focus navigation",
                sections=[],
                theme=self.default_theme,
                width=self.default_width
            )
            
            # Create sections
            self._create_main_sections()
            
            logger.info("Lab Informatics sidebar layout initialized with sections")
            
        except Exception as e:
            logger.error(f"Error initializing sidebar layout: {e}")
    
    def _create_main_sections(self):
        """Create main sidebar sections"""
        try:
            sections = [
                self._create_dashboard_section(),
                self._create_lab_informatics_products_section(),
                self._create_troubleshooting_section(),
                self._create_data_management_section(),
                self._create_workflow_automation_section(),
                self._create_compliance_section(),
                self._create_integration_section(),
                self._create_analytics_section(),
                self._create_collaboration_section(),
                self._create_infrastructure_section(),
                self._create_security_section(),
                self._create_support_section(),
                self._create_ai_assistant_section(),
                self._create_user_section()
            ]
            
            # Add sections to layout
            self.layout.sections.extend(sections)
            
        except Exception as e:
            logger.error(f"Error creating main sections: {e}")
    
    def _create_dashboard_section(self) -> LabInformaticsSidebarSection:
        """Create dashboard section"""
        try:
            items = [
                LabInformaticsNavigationItem(
                    id="dashboard_overview",
                    title="Overview",
                    type="link",
                    icon="dashboard",
                    url="/lab-informatics/dashboard",
                    order=1
                ),
                LabInformaticsNavigationItem(
                    id="dashboard_system_health",
                    title="System Health",
                    type="link",
                    icon="health",
                    url="/lab-informatics/system-health",
                    order=2
                ),
                LabInformaticsNavigationItem(
                    id="dashboard_performance",
                    title="Performance",
                    type="link",
                    icon="performance",
                    url="/lab-informatics/performance",
                    order=3
                ),
                LabInformaticsNavigationItem(
                    id="dashboard_analytics",
                    title="Analytics",
                    type="link",
                    icon="analytics",
                    url="/lab-informatics/analytics",
                    order=4
                )
            ]
            
            return LabInformaticsSidebarSection(
                id="dashboard",
                title="Dashboard",
                icon="dashboard",
                items=items,
                order=1,
                is_collapsible=True
            )
            
        except Exception as e:
            logger.error(f"Error creating dashboard section: {e}")
            return LabInformaticsSidebarSection(id="dashboard", title="Dashboard", icon="dashboard", items=[], order=1)
    
    def _create_lab_informatics_products_section(self) -> LabInformaticsSidebarSection:
        """Create Lab Informatics products section"""
        try:
            items = [
                LabInformaticsNavigationItem(
                    id="products_openlab",
                    title="OpenLab",
                    type="dropdown",
                    icon="openlab",
                    order=1,
                    related_products=[LabInformaticsProduct.OPENLAB_CDS, LabInformaticsProduct.OPENLAB_ECM, LabInformaticsProduct.OPENLAB_CDS_2, LabInformaticsProduct.OPENLAB_CONNECT, LabInformaticsProduct.OPENLAB_SHARED_SERVICES, LabInformaticsProduct.OPENLAB_INFRASTRUCTURE],
                    children=[
                        LabInformaticsNavigationItem(
                            id="products_openlab_cds",
                            title="OpenLab CDS",
                            type="link",
                            url="/lab-informatics/products/openlab-cds",
                            order=1,
                            related_products=[LabInformaticsProduct.OPENLAB_CDS]
                        ),
                        LabInformaticsNavigationItem(
                            id="products_openlab_ecm",
                            title="OpenLab ECM",
                            type="link",
                            url="/lab-informatics/products/openlab-ecm",
                            order=2,
                            related_products=[LabInformaticsProduct.OPENLAB_ECM]
                        ),
                        LabInformaticsNavigationItem(
                            id="products_openlab_cds_2",
                            title="OpenLab CDS 2",
                            type="link",
                            url="/lab-informatics/products/openlab-cds-2",
                            order=3,
                            related_products=[LabInformaticsProduct.OPENLAB_CDS_2]
                        ),
                        LabInformaticsNavigationItem(
                            id="products_openlab_connect",
                            title="OpenLab Connect",
                            type="link",
                            url="/lab-informatics/products/openlab-connect",
                            order=4,
                            related_products=[LabInformaticsProduct.OPENLAB_CONNECT]
                        ),
                        LabInformaticsNavigationItem(
                            id="products_openlab_shared_services",
                            title="OpenLab Shared Services",
                            type="link",
                            url="/lab-informatics/products/openlab-shared-services",
                            order=5,
                            related_products=[LabInformaticsProduct.OPENLAB_SHARED_SERVICES]
                        ),
                        LabInformaticsNavigationItem(
                            id="products_openlab_infrastructure",
                            title="OpenLab Infrastructure",
                            type="link",
                            url="/lab-informatics/products/openlab-infrastructure",
                            order=6,
                            related_products=[LabInformaticsProduct.OPENLAB_INFRASTRUCTURE]
                        )
                    ]
                ),
                LabInformaticsNavigationItem(
                    id="products_masshunter",
                    title="MassHunter",
                    type="dropdown",
                    icon="masshunter",
                    order=2,
                    related_products=[LabInformaticsProduct.MASSHUNTER],
                    children=[
                        LabInformaticsNavigationItem(
                            id="products_masshunter_workstation",
                            title="MassHunter Workstation",
                            type="link",
                            url="/lab-informatics/products/masshunter-workstation",
                            order=1,
                            related_products=[LabInformaticsProduct.MASSHUNTER]
                        ),
                        LabInformaticsNavigationItem(
                            id="products_masshunter_qualitative",
                            title="MassHunter Qualitative",
                            type="link",
                            url="/lab-informatics/products/masshunter-qualitative",
                            order=2,
                            related_products=[LabInformaticsProduct.MASSHUNTER]
                        ),
                        LabInformaticsNavigationItem(
                            id="products_masshunter_quantitative",
                            title="MassHunter Quantitative",
                            type="link",
                            url="/lab-informatics/products/masshunter-quantitative",
                            order=3,
                            related_products=[LabInformaticsProduct.MASSHUNTER]
                        )
                    ]
                ),
                LabInformaticsNavigationItem(
                    id="products_chemstation",
                    title="ChemStation",
                    type="dropdown",
                    icon="chemstation",
                    order=3,
                    related_products=[LabInformaticsProduct.CHEMSTATION],
                    children=[
                        LabInformaticsNavigationItem(
                            id="products_chemstation_gc",
                            title="ChemStation for GC",
                            type="link",
                            url="/lab-informatics/products/chemstation-gc",
                            order=1,
                            related_products=[LabInformaticsProduct.CHEMSTATION]
                        ),
                        LabInformaticsNavigationItem(
                            id="products_chemstation_lc",
                            title="ChemStation for LC",
                            type="link",
                            url="/lab-informatics/products/chemstation-lc",
                            order=2,
                            related_products=[LabInformaticsProduct.CHEMSTATION]
                        )
                    ]
                ),
                LabInformaticsNavigationItem(
                    id="products_vnmrj",
                    title="VnmrJ",
                    type="link",
                    icon="vnmrj",
                    url="/lab-informatics/products/vnmrj",
                    order=4,
                    related_products=[LabInformaticsProduct.VNMRJ]
                ),
                LabInformaticsNavigationItem(
                    id="products_agilent_connect",
                    title="Agilent Connect",
                    type="link",
                    icon="agilent-connect",
                    url="/lab-informatics/products/agilent-connect",
                    order=5,
                    related_products=[LabInformaticsProduct.AGILENT_CONNECT]
                ),
                LabInformaticsNavigationItem(
                    id="products_agilent_crosslab",
                    title="Agilent CrossLab",
                    type="link",
                    icon="agilent-crosslab",
                    url="/lab-informatics/products/agilent-crosslab",
                    order=6,
                    related_products=[LabInformaticsProduct.AGILENT_CROSSLAB]
                )
            ]
            
            return LabInformaticsSidebarSection(
                id="lab_informatics_products",
                title="Lab Informatics Products",
                icon="lab-informatics",
                items=items,
                order=2,
                is_collapsible=True,
                category=LabInformaticsCategory.DATA_MANAGEMENT
            )
            
        except Exception as e:
            logger.error(f"Error creating Lab Informatics products section: {e}")
            return LabInformaticsSidebarSection(id="lab_informatics_products", title="Lab Informatics Products", icon="lab-informatics", items=[], order=2)
    
    def _create_troubleshooting_section(self) -> LabInformaticsSidebarSection:
        """Create troubleshooting section"""
        try:
            items = [
                LabInformaticsNavigationItem(
                    id="troubleshooting_installation",
                    title="Installation Issues",
                    type="link",
                    icon="install",
                    url="/lab-informatics/troubleshooting/installation",
                    order=1,
                    troubleshooting_items=[
                        TroubleshootingItem(
                            id="troubleshooting_install_openlab_cds",
                            title="OpenLab CDS Installation Issues",
                            category=TroubleshootingCategory.INSTALLATION,
                            severity="high",
                            description="Common installation issues with OpenLab CDS",
                            solution="Check system requirements and run installer as administrator",
                            related_products=[LabInformaticsProduct.OPENLAB_CDS],
                            tags=["installation", "openlab", "cds"]
                        )
                    ]
                ),
                LabInformaticsNavigationItem(
                    id="troubleshooting_configuration",
                    title="Configuration Issues",
                    type="link",
                    icon="config",
                    url="/lab-informatics/troubleshooting/configuration",
                    order=2,
                    troubleshooting_items=[
                        TroubleshootingItem(
                            id="troubleshooting_config_database",
                            title="Database Configuration Issues",
                            category=TroubleshootingCategory.CONFIGURATION,
                            severity="medium",
                            description="Database connection and configuration problems",
                            solution="Verify database settings and connection strings",
                            related_products=[LabInformaticsProduct.OPENLAB_CDS, LabInformaticsProduct.OPENLAB_ECM],
                            tags=["database", "configuration", "connection"]
                        )
                    ]
                ),
                LabInformaticsNavigationItem(
                    id="troubleshooting_connectivity",
                    title="Connectivity Issues",
                    type="link",
                    icon="connectivity",
                    url="/lab-informatics/troubleshooting/connectivity",
                    order=3,
                    troubleshooting_items=[
                        TroubleshootingItem(
                            id="troubleshooting_connectivity_instruments",
                            title="Instrument Connectivity Issues",
                            category=TroubleshootingCategory.CONNECTIVITY,
                            severity="high",
                            description="Problems connecting to instruments",
                            solution="Check network settings and instrument drivers",
                            related_products=[LabInformaticsProduct.OPENLAB_CDS, LabInformaticsProduct.CHEMSTATION],
                            tags=["connectivity", "instruments", "network"]
                        )
                    ]
                ),
                LabInformaticsNavigationItem(
                    id="troubleshooting_performance",
                    title="Performance Issues",
                    type="link",
                    icon="performance",
                    url="/lab-informatics/troubleshooting/performance",
                    order=4,
                    troubleshooting_items=[
                        TroubleshootingItem(
                            id="troubleshooting_performance_slow",
                            title="Slow System Performance",
                            category=TroubleshootingCategory.PERFORMANCE,
                            severity="medium",
                            description="System running slowly or unresponsive",
                            solution="Check system resources and optimize database",
                            related_products=[LabInformaticsProduct.OPENLAB_CDS, LabInformaticsProduct.OPENLAB_ECM],
                            tags=["performance", "slow", "optimization"]
                        )
                    ]
                ),
                LabInformaticsNavigationItem(
                    id="troubleshooting_data_issues",
                    title="Data Issues",
                    type="link",
                    icon="data",
                    url="/lab-informatics/troubleshooting/data-issues",
                    order=5,
                    troubleshooting_items=[
                        TroubleshootingItem(
                            id="troubleshooting_data_corruption",
                            title="Data Corruption Issues",
                            category=TroubleshootingCategory.DATA_ISSUES,
                            severity="critical",
                            description="Data corruption or loss",
                            solution="Restore from backup and check data integrity",
                            related_products=[LabInformaticsProduct.OPENLAB_CDS, LabInformaticsProduct.OPENLAB_ECM],
                            tags=["data", "corruption", "backup"]
                        )
                    ]
                ),
                LabInformaticsNavigationItem(
                    id="troubleshooting_user_access",
                    title="User Access Issues",
                    type="link",
                    icon="user-access",
                    url="/lab-informatics/troubleshooting/user-access",
                    order=6,
                    troubleshooting_items=[
                        TroubleshootingItem(
                            id="troubleshooting_user_login",
                            title="User Login Issues",
                            category=TroubleshootingCategory.USER_ACCESS,
                            severity="medium",
                            description="Users unable to log in",
                            solution="Check user accounts and permissions",
                            related_products=[LabInformaticsProduct.OPENLAB_CDS, LabInformaticsProduct.OPENLAB_ECM],
                            tags=["user", "login", "permissions"]
                        )
                    ]
                ),
                LabInformaticsNavigationItem(
                    id="troubleshooting_integration",
                    title="Integration Issues",
                    type="link",
                    icon="integration",
                    url="/lab-informatics/troubleshooting/integration",
                    order=7,
                    troubleshooting_items=[
                        TroubleshootingItem(
                            id="troubleshooting_integration_lims",
                            title="LIMS Integration Issues",
                            category=TroubleshootingCategory.INTEGRATION,
                            severity="high",
                            description="Problems integrating with LIMS systems",
                            solution="Verify integration settings and API connections",
                            related_products=[LabInformaticsProduct.OPENLAB_CDS, LabInformaticsProduct.OPENLAB_CONNECT],
                            tags=["integration", "lims", "api"]
                        )
                    ]
                ),
                LabInformaticsNavigationItem(
                    id="troubleshooting_backup_restore",
                    title="Backup & Restore",
                    type="link",
                    icon="backup",
                    url="/lab-informatics/troubleshooting/backup-restore",
                    order=8,
                    troubleshooting_items=[
                        TroubleshootingItem(
                            id="troubleshooting_backup_failure",
                            title="Backup Failure Issues",
                            category=TroubleshootingCategory.BACKUP_RESTORE,
                            severity="high",
                            description="Backup processes failing",
                            solution="Check backup settings and storage space",
                            related_products=[LabInformaticsProduct.OPENLAB_CDS, LabInformaticsProduct.OPENLAB_ECM],
                            tags=["backup", "restore", "storage"]
                        )
                    ]
                ),
                LabInformaticsNavigationItem(
                    id="troubleshooting_security",
                    title="Security Issues",
                    type="link",
                    icon="security",
                    url="/lab-informatics/troubleshooting/security",
                    order=9,
                    troubleshooting_items=[
                        TroubleshootingItem(
                            id="troubleshooting_security_access",
                            title="Security Access Issues",
                            category=TroubleshootingCategory.SECURITY,
                            severity="high",
                            description="Security-related access problems",
                            solution="Review security settings and user permissions",
                            related_products=[LabInformaticsProduct.OPENLAB_CDS, LabInformaticsProduct.OPENLAB_ECM],
                            tags=["security", "access", "permissions"]
                        )
                    ]
                ),
                LabInformaticsNavigationItem(
                    id="troubleshooting_general",
                    title="General Issues",
                    type="link",
                    icon="general",
                    url="/lab-informatics/troubleshooting/general",
                    order=10,
                    troubleshooting_items=[
                        TroubleshootingItem(
                            id="troubleshooting_general_errors",
                            title="General Error Messages",
                            category=TroubleshootingCategory.GENERAL,
                            severity="low",
                            description="Common error messages and solutions",
                            solution="Check error logs and system status",
                            related_products=[LabInformaticsProduct.OPENLAB_CDS, LabInformaticsProduct.OPENLAB_ECM, LabInformaticsProduct.MASSHUNTER, LabInformaticsProduct.CHEMSTATION],
                            tags=["errors", "general", "logs"]
                        )
                    ]
                )
            ]
            
            return LabInformaticsSidebarSection(
                id="troubleshooting",
                title="Troubleshooting",
                icon="troubleshoot",
                items=items,
                order=3,
                is_collapsible=True,
                category=LabInformaticsCategory.COMPLIANCE
            )
            
        except Exception as e:
            logger.error(f"Error creating troubleshooting section: {e}")
            return LabInformaticsSidebarSection(id="troubleshooting", title="Troubleshooting", icon="troubleshoot", items=[], order=3)
    
    def _create_data_management_section(self) -> LabInformaticsSidebarSection:
        """Create data management section"""
        try:
            items = [
                LabInformaticsNavigationItem(
                    id="data_management_storage",
                    title="Data Storage",
                    type="link",
                    icon="storage",
                    url="/lab-informatics/data-management/storage",
                    order=1
                ),
                LabInformaticsNavigationItem(
                    id="data_management_archiving",
                    title="Data Archiving",
                    type="link",
                    icon="archive",
                    url="/lab-informatics/data-management/archiving",
                    order=2
                ),
                LabInformaticsNavigationItem(
                    id="data_management_retention",
                    title="Data Retention",
                    type="link",
                    icon="retention",
                    url="/lab-informatics/data-management/retention",
                    order=3
                ),
                LabInformaticsNavigationItem(
                    id="data_management_migration",
                    title="Data Migration",
                    type="link",
                    icon="migration",
                    url="/lab-informatics/data-management/migration",
                    order=4
                ),
                LabInformaticsNavigationItem(
                    id="data_management_validation",
                    title="Data Validation",
                    type="link",
                    icon="validation",
                    url="/lab-informatics/data-management/validation",
                    order=5
                )
            ]
            
            return LabInformaticsSidebarSection(
                id="data_management",
                title="Data Management",
                icon="data-management",
                items=items,
                order=4,
                is_collapsible=True,
                category=LabInformaticsCategory.DATA_MANAGEMENT
            )
            
        except Exception as e:
            logger.error(f"Error creating data management section: {e}")
            return LabInformaticsSidebarSection(id="data_management", title="Data Management", icon="data-management", items=[], order=4)
    
    def _create_workflow_automation_section(self) -> LabInformaticsSidebarSection:
        """Create workflow automation section"""
        try:
            items = [
                LabInformaticsNavigationItem(
                    id="workflow_automation_design",
                    title="Workflow Design",
                    type="link",
                    icon="workflow-design",
                    url="/lab-informatics/workflow-automation/design",
                    order=1
                ),
                LabInformaticsNavigationItem(
                    id="workflow_automation_execution",
                    title="Workflow Execution",
                    type="link",
                    icon="workflow-execution",
                    url="/lab-informatics/workflow-automation/execution",
                    order=2
                ),
                LabInformaticsNavigationItem(
                    id="workflow_automation_monitoring",
                    title="Workflow Monitoring",
                    type="link",
                    icon="workflow-monitoring",
                    url="/lab-informatics/workflow-automation/monitoring",
                    order=3
                ),
                LabInformaticsNavigationItem(
                    id="workflow_automation_optimization",
                    title="Workflow Optimization",
                    type="link",
                    icon="workflow-optimization",
                    url="/lab-informatics/workflow-automation/optimization",
                    order=4
                )
            ]
            
            return LabInformaticsSidebarSection(
                id="workflow_automation",
                title="Workflow Automation",
                icon="workflow",
                items=items,
                order=5,
                is_collapsible=True,
                category=LabInformaticsCategory.WORKFLOW_AUTOMATION
            )
            
        except Exception as e:
            logger.error(f"Error creating workflow automation section: {e}")
            return LabInformaticsSidebarSection(id="workflow_automation", title="Workflow Automation", icon="workflow", items=[], order=5)
    
    def _create_compliance_section(self) -> LabInformaticsSidebarSection:
        """Create compliance section"""
        try:
            items = [
                LabInformaticsNavigationItem(
                    id="compliance_21_cfr_part_11",
                    title="21 CFR Part 11",
                    type="link",
                    icon="21-cfr",
                    url="/lab-informatics/compliance/21-cfr-part-11",
                    order=1
                ),
                LabInformaticsNavigationItem(
                    id="compliance_gmp",
                    title="GMP Compliance",
                    type="link",
                    icon="gmp",
                    url="/lab-informatics/compliance/gmp",
                    order=2
                ),
                LabInformaticsNavigationItem(
                    id="compliance_glp",
                    title="GLP Compliance",
                    type="link",
                    icon="glp",
                    url="/lab-informatics/compliance/glp",
                    order=3
                ),
                LabInformaticsNavigationItem(
                    id="compliance_iso",
                    title="ISO Compliance",
                    type="link",
                    icon="iso",
                    url="/lab-informatics/compliance/iso",
                    order=4
                ),
                LabInformaticsNavigationItem(
                    id="compliance_audit",
                    title="Audit Trail",
                    type="link",
                    icon="audit",
                    url="/lab-informatics/compliance/audit-trail",
                    order=5
                )
            ]
            
            return LabInformaticsSidebarSection(
                id="compliance",
                title="Compliance",
                icon="compliance",
                items=items,
                order=6,
                is_collapsible=True,
                category=LabInformaticsCategory.COMPLIANCE
            )
            
        except Exception as e:
            logger.error(f"Error creating compliance section: {e}")
            return LabInformaticsSidebarSection(id="compliance", title="Compliance", icon="compliance", items=[], order=6)
    
    def _create_integration_section(self) -> LabInformaticsSidebarSection:
        """Create integration section"""
        try:
            items = [
                LabInformaticsNavigationItem(
                    id="integration_lims",
                    title="LIMS Integration",
                    type="link",
                    icon="lims",
                    url="/lab-informatics/integration/lims",
                    order=1
                ),
                LabInformaticsNavigationItem(
                    id="integration_erp",
                    title="ERP Integration",
                    type="link",
                    icon="erp",
                    url="/lab-informatics/integration/erp",
                    order=2
                ),
                LabInformaticsNavigationItem(
                    id="integration_instruments",
                    title="Instrument Integration",
                    type="link",
                    icon="instruments",
                    url="/lab-informatics/integration/instruments",
                    order=3
                ),
                LabInformaticsNavigationItem(
                    id="integration_apis",
                    title="API Integration",
                    type="link",
                    icon="api",
                    url="/lab-informatics/integration/apis",
                    order=4
                ),
                LabInformaticsNavigationItem(
                    id="integration_web_services",
                    title="Web Services",
                    type="link",
                    icon="web-services",
                    url="/lab-informatics/integration/web-services",
                    order=5
                )
            ]
            
            return LabInformaticsSidebarSection(
                id="integration",
                title="Integration",
                icon="integration",
                items=items,
                order=7,
                is_collapsible=True,
                category=LabInformaticsCategory.INTEGRATION
            )
            
        except Exception as e:
            logger.error(f"Error creating integration section: {e}")
            return LabInformaticsSidebarSection(id="integration", title="Integration", icon="integration", items=[], order=7)
    
    def _create_analytics_section(self) -> LabInformaticsSidebarSection:
        """Create analytics section"""
        try:
            items = [
                LabInformaticsNavigationItem(
                    id="analytics_reporting",
                    title="Reporting",
                    type="link",
                    icon="reporting",
                    url="/lab-informatics/analytics/reporting",
                    order=1
                ),
                LabInformaticsNavigationItem(
                    id="analytics_dashboards",
                    title="Dashboards",
                    type="link",
                    icon="dashboards",
                    url="/lab-informatics/analytics/dashboards",
                    order=2
                ),
                LabInformaticsNavigationItem(
                    id="analytics_kpis",
                    title="KPIs",
                    type="link",
                    icon="kpis",
                    url="/lab-informatics/analytics/kpis",
                    order=3
                ),
                LabInformaticsNavigationItem(
                    id="analytics_trends",
                    title="Trend Analysis",
                    type="link",
                    icon="trends",
                    url="/lab-informatics/analytics/trends",
                    order=4
                ),
                LabInformaticsNavigationItem(
                    id="analytics_predictive",
                    title="Predictive Analytics",
                    type="link",
                    icon="predictive",
                    url="/lab-informatics/analytics/predictive",
                    order=5
                )
            ]
            
            return LabInformaticsSidebarSection(
                id="analytics",
                title="Analytics",
                icon="analytics",
                items=items,
                order=8,
                is_collapsible=True,
                category=LabInformaticsCategory.ANALYTICS
            )
            
        except Exception as e:
            logger.error(f"Error creating analytics section: {e}")
            return LabInformaticsSidebarSection(id="analytics", title="Analytics", icon="analytics", items=[], order=8)
    
    def _create_collaboration_section(self) -> LabInformaticsSidebarSection:
        """Create collaboration section"""
        try:
            items = [
                LabInformaticsNavigationItem(
                    id="collaboration_teams",
                    title="Teams",
                    type="link",
                    icon="teams",
                    url="/lab-informatics/collaboration/teams",
                    order=1
                ),
                LabInformaticsNavigationItem(
                    id="collaboration_projects",
                    title="Projects",
                    type="link",
                    icon="projects",
                    url="/lab-informatics/collaboration/projects",
                    order=2
                ),
                LabInformaticsNavigationItem(
                    id="collaboration_sharing",
                    title="Data Sharing",
                    type="link",
                    icon="sharing",
                    url="/lab-informatics/collaboration/sharing",
                    order=3
                ),
                LabInformaticsNavigationItem(
                    id="collaboration_communication",
                    title="Communication",
                    type="link",
                    icon="communication",
                    url="/lab-informatics/collaboration/communication",
                    order=4
                )
            ]
            
            return LabInformaticsSidebarSection(
                id="collaboration",
                title="Collaboration",
                icon="collaboration",
                items=items,
                order=9,
                is_collapsible=True,
                category=LabInformaticsCategory.COLLABORATION
            )
            
        except Exception as e:
            logger.error(f"Error creating collaboration section: {e}")
            return LabInformaticsSidebarSection(id="collaboration", title="Collaboration", icon="collaboration", items=[], order=9)
    
    def _create_infrastructure_section(self) -> LabInformaticsSidebarSection:
        """Create infrastructure section"""
        try:
            items = [
                LabInformaticsNavigationItem(
                    id="infrastructure_servers",
                    title="Servers",
                    type="link",
                    icon="servers",
                    url="/lab-informatics/infrastructure/servers",
                    order=1
                ),
                LabInformaticsNavigationItem(
                    id="infrastructure_networking",
                    title="Networking",
                    type="link",
                    icon="networking",
                    url="/lab-informatics/infrastructure/networking",
                    order=2
                ),
                LabInformaticsNavigationItem(
                    id="infrastructure_storage",
                    title="Storage",
                    type="link",
                    icon="storage",
                    url="/lab-informatics/infrastructure/storage",
                    order=3
                ),
                LabInformaticsNavigationItem(
                    id="infrastructure_virtualization",
                    title="Virtualization",
                    type="link",
                    icon="virtualization",
                    url="/lab-informatics/infrastructure/virtualization",
                    order=4
                ),
                LabInformaticsNavigationItem(
                    id="infrastructure_monitoring",
                    title="Infrastructure Monitoring",
                    type="link",
                    icon="monitoring",
                    url="/lab-informatics/infrastructure/monitoring",
                    order=5
                )
            ]
            
            return LabInformaticsSidebarSection(
                id="infrastructure",
                title="Infrastructure",
                icon="infrastructure",
                items=items,
                order=10,
                is_collapsible=True,
                category=LabInformaticsCategory.INFRASTRUCTURE
            )
            
        except Exception as e:
            logger.error(f"Error creating infrastructure section: {e}")
            return LabInformaticsSidebarSection(id="infrastructure", title="Infrastructure", icon="infrastructure", items=[], order=10)
    
    def _create_security_section(self) -> LabInformaticsSidebarSection:
        """Create security section"""
        try:
            items = [
                LabInformaticsNavigationItem(
                    id="security_authentication",
                    title="Authentication",
                    type="link",
                    icon="authentication",
                    url="/lab-informatics/security/authentication",
                    order=1
                ),
                LabInformaticsNavigationItem(
                    id="security_authorization",
                    title="Authorization",
                    type="link",
                    icon="authorization",
                    url="/lab-informatics/security/authorization",
                    order=2
                ),
                LabInformaticsNavigationItem(
                    id="security_encryption",
                    title="Encryption",
                    type="link",
                    icon="encryption",
                    url="/lab-informatics/security/encryption",
                    order=3
                ),
                LabInformaticsNavigationItem(
                    id="security_audit",
                    title="Security Audit",
                    type="link",
                    icon="security-audit",
                    url="/lab-informatics/security/audit",
                    order=4
                ),
                LabInformaticsNavigationItem(
                    id="security_compliance",
                    title="Security Compliance",
                    type="link",
                    icon="security-compliance",
                    url="/lab-informatics/security/compliance",
                    order=5
                )
            ]
            
            return LabInformaticsSidebarSection(
                id="security",
                title="Security",
                icon="security",
                items=items,
                order=11,
                is_collapsible=True,
                category=LabInformaticsCategory.SECURITY
            )
            
        except Exception as e:
            logger.error(f"Error creating security section: {e}")
            return LabInformaticsSidebarSection(id="security", title="Security", icon="security", items=[], order=11)
    
    def _create_support_section(self) -> LabInformaticsSidebarSection:
        """Create support section"""
        try:
            items = [
                LabInformaticsNavigationItem(
                    id="support_contact",
                    title="Contact Support",
                    type="link",
                    icon="support",
                    url="/lab-informatics/support/contact",
                    order=1
                ),
                LabInformaticsNavigationItem(
                    id="support_tickets",
                    title="Support Tickets",
                    type="link",
                    icon="ticket",
                    url="/lab-informatics/support/tickets",
                    order=2
                ),
                LabInformaticsNavigationItem(
                    id="support_knowledge_base",
                    title="Knowledge Base",
                    type="link",
                    icon="knowledge",
                    url="/lab-informatics/support/knowledge-base",
                    order=3
                ),
                LabInformaticsNavigationItem(
                    id="support_forums",
                    title="Community Forums",
                    type="link",
                    icon="forum",
                    url="/lab-informatics/support/forums",
                    order=4
                ),
                LabInformaticsNavigationItem(
                    id="support_remote_assistance",
                    title="Remote Assistance",
                    type="link",
                    icon="remote",
                    url="/lab-informatics/support/remote-assistance",
                    order=5
                ),
                LabInformaticsNavigationItem(
                    id="support_service_centers",
                    title="Service Centers",
                    type="link",
                    icon="service-center",
                    url="/lab-informatics/support/service-centers",
                    order=6
                ),
                LabInformaticsNavigationItem(
                    id="support_warranty",
                    title="Warranty Information",
                    type="link",
                    icon="warranty",
                    url="/lab-informatics/support/warranty",
                    order=7
                )
            ]
            
            return LabInformaticsSidebarSection(
                id="support",
                title="Support",
                icon="support",
                items=items,
                order=12,
                is_collapsible=True
            )
            
        except Exception as e:
            logger.error(f"Error creating support section: {e}")
            return LabInformaticsSidebarSection(id="support", title="Support", icon="support", items=[], order=12)
    
    def _create_ai_assistant_section(self) -> LabInformaticsSidebarSection:
        """Create AI assistant section"""
        try:
            items = [
                LabInformaticsNavigationItem(
                    id="ai_chat",
                    title="AI Chat Assistant",
                    type="link",
                    icon="chat",
                    url="/lab-informatics/ai/chat",
                    order=1
                ),
                LabInformaticsNavigationItem(
                    id="ai_rag_search",
                    title="RAG Search",
                    type="link",
                    icon="search",
                    url="/lab-informatics/ai/rag-search",
                    order=2
                ),
                LabInformaticsNavigationItem(
                    id="ai_advanced_search",
                    title="Advanced Search",
                    type="link",
                    icon="advanced-search",
                    url="/lab-informatics/ai/advanced-search",
                    order=3
                ),
                LabInformaticsNavigationItem(
                    id="ai_comprehensive_search",
                    title="Comprehensive Search",
                    type="link",
                    icon="comprehensive-search",
                    url="/lab-informatics/ai/comprehensive-search",
                    order=4
                ),
                LabInformaticsNavigationItem(
                    id="ai_document_manager",
                    title="Document Manager",
                    type="link",
                    icon="document-manager",
                    url="/lab-informatics/ai/document-manager",
                    order=5
                ),
                LabInformaticsNavigationItem(
                    id="ai_content_analysis",
                    title="Content Analysis",
                    type="link",
                    icon="analysis",
                    url="/lab-informatics/ai/content-analysis",
                    order=6
                ),
                LabInformaticsNavigationItem(
                    id="ai_troubleshooting_assistant",
                    title="Troubleshooting Assistant",
                    type="link",
                    icon="troubleshoot-assistant",
                    url="/lab-informatics/ai/troubleshooting-assistant",
                    order=7
                )
            ]
            
            return LabInformaticsSidebarSection(
                id="ai_assistant",
                title="AI Assistant",
                icon="ai",
                items=items,
                order=13,
                is_collapsible=True
            )
            
        except Exception as e:
            logger.error(f"Error creating AI assistant section: {e}")
            return LabInformaticsSidebarSection(id="ai_assistant", title="AI Assistant", icon="ai", items=[], order=13)
    
    def _create_user_section(self) -> LabInformaticsSidebarSection:
        """Create user section"""
        try:
            items = [
                LabInformaticsNavigationItem(
                    id="user_profile",
                    title="Profile",
                    type="link",
                    icon="profile",
                    url="/lab-informatics/user/profile",
                    order=1
                ),
                LabInformaticsNavigationItem(
                    id="user_preferences",
                    title="Preferences",
                    type="link",
                    icon="preferences",
                    url="/lab-informatics/user/preferences",
                    order=2
                ),
                LabInformaticsNavigationItem(
                    id="user_history",
                    title="History",
                    type="link",
                    icon="history",
                    url="/lab-informatics/user/history",
                    order=3
                ),
                LabInformaticsNavigationItem(
                    id="user_favorites",
                    title="Favorites",
                    type="link",
                    icon="favorites",
                    url="/lab-informatics/user/favorites",
                    order=4
                ),
                LabInformaticsNavigationItem(
                    id="user_notifications",
                    title="Notifications",
                    type="link",
                    icon="notifications",
                    url="/lab-informatics/user/notifications",
                    order=5
                ),
                LabInformaticsNavigationItem(
                    id="user_settings",
                    title="Settings",
                    type="link",
                    icon="settings",
                    url="/lab-informatics/user/settings",
                    order=6
                )
            ]
            
            return LabInformaticsSidebarSection(
                id="user",
                title="User",
                icon="user",
                items=items,
                order=14,
                is_collapsible=True
            )
            
        except Exception as e:
            logger.error(f"Error creating user section: {e}")
            return LabInformaticsSidebarSection(id="user", title="User", icon="user", items=[], order=14)
    
    def get_layout(self) -> LabInformaticsSidebarLayout:
        """Get the current sidebar layout"""
        return self.layout
    
    def get_section(self, section_id: str) -> Optional[LabInformaticsSidebarSection]:
        """Get a specific section by ID"""
        try:
            for section in self.layout.sections:
                if section.id == section_id:
                    return section
            return None
            
        except Exception as e:
            logger.error(f"Error getting section {section_id}: {e}")
            return None
    
    def get_navigation_item(self, item_id: str) -> Optional[LabInformaticsNavigationItem]:
        """Get a specific navigation item by ID"""
        try:
            for section in self.layout.sections:
                for item in section.items:
                    if item.id == item_id:
                        return item
                    
                    # Check children
                    for child in item.children:
                        if child.id == item_id:
                            return child
            
            return None
            
        except Exception as e:
            logger.error(f"Error getting navigation item {item_id}: {e}")
            return None
    
    def get_troubleshooting_items(self, category: TroubleshootingCategory = None, product: LabInformaticsProduct = None) -> List[TroubleshootingItem]:
        """Get troubleshooting items filtered by category and product"""
        try:
            items = []
            
            for section in self.layout.sections:
                for item in section.items:
                    for troubleshooting_item in item.troubleshooting_items:
                        if category and troubleshooting_item.category != category:
                            continue
                        if product and product not in troubleshooting_item.related_products:
                            continue
                        items.append(troubleshooting_item)
            
            return items
            
        except Exception as e:
            logger.error(f"Error getting troubleshooting items: {e}")
            return []
    
    def get_featured_troubleshooting_items(self, limit: int = 5) -> List[TroubleshootingItem]:
        """Get featured troubleshooting items"""
        try:
            items = []
            
            for section in self.layout.sections:
                for item in section.items:
                    for troubleshooting_item in item.troubleshooting_items:
                        if troubleshooting_item.is_featured:
                            items.append(troubleshooting_item)
            
            # Sort by view count and limit
            items.sort(key=lambda x: x.view_count, reverse=True)
            return items[:limit]
            
        except Exception as e:
            logger.error(f"Error getting featured troubleshooting items: {e}")
            return []
    
    def search_troubleshooting(self, query: str) -> List[TroubleshootingItem]:
        """Search troubleshooting items"""
        try:
            results = []
            query_lower = query.lower()
            
            for section in self.layout.sections:
                for item in section.items:
                    for troubleshooting_item in item.troubleshooting_items:
                        # Search in title, description, solution, and tags
                        if (query_lower in troubleshooting_item.title.lower() or
                            query_lower in troubleshooting_item.description.lower() or
                            query_lower in troubleshooting_item.solution.lower() or
                            any(query_lower in tag.lower() for tag in troubleshooting_item.tags)):
                            results.append(troubleshooting_item)
            
            return results
            
        except Exception as e:
            logger.error(f"Error searching troubleshooting: {e}")
            return []
    
    def get_product_troubleshooting(self, product: LabInformaticsProduct) -> List[TroubleshootingItem]:
        """Get troubleshooting items for a specific product"""
        try:
            items = []
            
            for section in self.layout.sections:
                for item in section.items:
                    for troubleshooting_item in item.troubleshooting_items:
                        if product in troubleshooting_item.related_products:
                            items.append(troubleshooting_item)
            
            return items
            
        except Exception as e:
            logger.error(f"Error getting product troubleshooting: {e}")
            return []
    
    def get_category_troubleshooting(self, category: TroubleshootingCategory) -> List[TroubleshootingItem]:
        """Get troubleshooting items for a specific category"""
        try:
            items = []
            
            for section in self.layout.sections:
                for item in section.items:
                    for troubleshooting_item in item.troubleshooting_items:
                        if troubleshooting_item.category == category:
                            items.append(troubleshooting_item)
            
            return items
            
        except Exception as e:
            logger.error(f"Error getting category troubleshooting: {e}")
            return []
    
    def add_troubleshooting_item(self, item: TroubleshootingItem, section_id: str, navigation_item_id: str):
        """Add a troubleshooting item to a navigation item"""
        try:
            navigation_item = self.get_navigation_item(navigation_item_id)
            if navigation_item:
                navigation_item.troubleshooting_items.append(item)
                logger.info(f"Added troubleshooting item {item.id} to {navigation_item_id}")
            
        except Exception as e:
            logger.error(f"Error adding troubleshooting item: {e}")
    
    def update_troubleshooting_item(self, item_id: str, updates: Dict[str, Any]):
        """Update a troubleshooting item"""
        try:
            for section in self.layout.sections:
                for item in section.items:
                    for troubleshooting_item in item.troubleshooting_items:
                        if troubleshooting_item.id == item_id:
                            for key, value in updates.items():
                                if hasattr(troubleshooting_item, key):
                                    setattr(troubleshooting_item, key, value)
                            
                            logger.info(f"Updated troubleshooting item: {item_id}")
                            return
            
        except Exception as e:
            logger.error(f"Error updating troubleshooting item: {e}")
    
    def remove_troubleshooting_item(self, item_id: str):
        """Remove a troubleshooting item"""
        try:
            for section in self.layout.sections:
                for item in section.items:
                    item.troubleshooting_items = [
                        troubleshooting_item for troubleshooting_item in item.troubleshooting_items
                        if troubleshooting_item.id != item_id
                    ]
            
            logger.info(f"Removed troubleshooting item: {item_id}")
            
        except Exception as e:
            logger.error(f"Error removing troubleshooting item: {e}")
    
    def increment_troubleshooting_view_count(self, item_id: str):
        """Increment view count for a troubleshooting item"""
        try:
            for section in self.layout.sections:
                for item in section.items:
                    for troubleshooting_item in item.troubleshooting_items:
                        if troubleshooting_item.id == item_id:
                            troubleshooting_item.view_count += 1
                            logger.info(f"Incremented view count for troubleshooting item: {item_id}")
                            return
            
        except Exception as e:
            logger.error(f"Error incrementing view count: {e}")
    
    def get_troubleshooting_statistics(self) -> Dict[str, Any]:
        """Get troubleshooting statistics"""
        try:
            stats = {
                'total_items': 0,
                'items_by_category': {},
                'items_by_product': {},
                'items_by_severity': {},
                'featured_items': 0,
                'total_views': 0,
                'most_viewed': []
            }
            
            for section in self.layout.sections:
                for item in section.items:
                    for troubleshooting_item in item.troubleshooting_items:
                        stats['total_items'] += 1
                        
                        # Count by category
                        category = troubleshooting_item.category.value
                        stats['items_by_category'][category] = stats['items_by_category'].get(category, 0) + 1
                        
                        # Count by product
                        for product in troubleshooting_item.related_products:
                            product_name = product.value
                            stats['items_by_product'][product_name] = stats['items_by_product'].get(product_name, 0) + 1
                        
                        # Count by severity
                        severity = troubleshooting_item.severity
                        stats['items_by_severity'][severity] = stats['items_by_severity'].get(severity, 0) + 1
                        
                        # Count featured items
                        if troubleshooting_item.is_featured:
                            stats['featured_items'] += 1
                        
                        # Count total views
                        stats['total_views'] += troubleshooting_item.view_count
                        
                        # Track most viewed
                        stats['most_viewed'].append({
                            'id': troubleshooting_item.id,
                            'title': troubleshooting_item.title,
                            'views': troubleshooting_item.view_count
                        })
            
            # Sort most viewed by view count
            stats['most_viewed'].sort(key=lambda x: x['views'], reverse=True)
            stats['most_viewed'] = stats['most_viewed'][:10]  # Top 10
            
            return stats
            
        except Exception as e:
            logger.error(f"Error getting troubleshooting statistics: {e}")
            return {}
    
    def export_layout(self) -> Dict[str, Any]:
        """Export the sidebar layout configuration"""
        try:
            layout_data = {
                'id': self.layout.id,
                'name': self.layout.name,
                'description': self.layout.description,
                'theme': self.layout.theme,
                'width': self.layout.width,
                'is_resizable': self.layout.is_resizable,
                'show_search': self.layout.show_search,
                'show_user_info': self.layout.show_user_info,
                'show_notifications': self.layout.show_notifications,
                'show_troubleshooting': self.layout.show_troubleshooting,
                'sections': []
            }
            
            for section in self.layout.sections:
                section_data = {
                    'id': section.id,
                    'title': section.title,
                    'icon': section.icon,
                    'order': section.order,
                    'is_collapsible': section.is_collapsible,
                    'is_collapsed': section.is_collapsed,
                    'permissions': section.permissions,
                    'category': section.category.value if section.category else None,
                    'items': []
                }
                
                for item in section.items:
                    item_data = {
                        'id': item.id,
                        'title': item.title,
                        'type': item.type,
                        'icon': item.icon,
                        'url': item.url,
                        'badge': item.badge,
                        'tooltip': item.tooltip,
                        'permissions': item.permissions,
                        'is_active': item.is_active,
                        'is_expanded': item.is_expanded,
                        'order': item.order,
                        'metadata': item.metadata,
                        'related_products': [product.value for product in item.related_products],
                        'troubleshooting_items': [
                            {
                                'id': troubleshooting_item.id,
                                'title': troubleshooting_item.title,
                                'category': troubleshooting_item.category.value,
                                'severity': troubleshooting_item.severity,
                                'description': troubleshooting_item.description,
                                'solution': troubleshooting_item.solution,
                                'related_products': [product.value for product in troubleshooting_item.related_products],
                                'tags': troubleshooting_item.tags,
                                'url': troubleshooting_item.url,
                                'is_featured': troubleshooting_item.is_featured,
                                'view_count': troubleshooting_item.view_count,
                                'last_updated': troubleshooting_item.last_updated.isoformat()
                            }
                            for troubleshooting_item in item.troubleshooting_items
                        ],
                        'children': []
                    }
                    
                    for child in item.children:
                        child_data = {
                            'id': child.id,
                            'title': child.title,
                            'type': child.type,
                            'icon': child.icon,
                            'url': child.url,
                            'badge': child.badge,
                            'tooltip': child.tooltip,
                            'permissions': child.permissions,
                            'is_active': child.is_active,
                            'is_expanded': child.is_expanded,
                            'order': child.order,
                            'metadata': child.metadata,
                            'related_products': [product.value for product in child.related_products]
                        }
                        item_data['children'].append(child_data)
                    
                    section_data['items'].append(item_data)
                
                layout_data['sections'].append(section_data)
            
            return layout_data
            
        except Exception as e:
            logger.error(f"Error exporting layout: {e}")
            return {}
    
    def import_layout(self, layout_data: Dict[str, Any]):
        """Import sidebar layout configuration"""
        try:
            # Update layout properties
            self.layout.name = layout_data.get('name', self.layout.name)
            self.layout.description = layout_data.get('description', self.layout.description)
            self.layout.theme = layout_data.get('theme', self.layout.theme)
            self.layout.width = layout_data.get('width', self.layout.width)
            self.layout.is_resizable = layout_data.get('is_resizable', self.layout.is_resizable)
            self.layout.show_search = layout_data.get('show_search', self.layout.show_search)
            self.layout.show_user_info = layout_data.get('show_user_info', self.layout.show_user_info)
            self.layout.show_notifications = layout_data.get('show_notifications', self.layout.show_notifications)
            self.layout.show_troubleshooting = layout_data.get('show_troubleshooting', self.layout.show_troubleshooting)
            
            # Clear existing sections
            self.layout.sections = []
            
            # Import sections
            for section_data in layout_data.get('sections', []):
                section = LabInformaticsSidebarSection(
                    id=section_data['id'],
                    title=section_data['title'],
                    icon=section_data['icon'],
                    items=[],
                    order=section_data['order'],
                    is_collapsible=section_data.get('is_collapsible', True),
                    is_collapsed=section_data.get('is_collapsed', False),
                    permissions=section_data.get('permissions', []),
                    category=LabInformaticsCategory(section_data['category']) if section_data.get('category') else None
                )
                
                # Import items
                for item_data in section_data.get('items', []):
                    item = LabInformaticsNavigationItem(
                        id=item_data['id'],
                        title=item_data['title'],
                        type=item_data['type'],
                        icon=item_data.get('icon'),
                        url=item_data.get('url'),
                        badge=item_data.get('badge'),
                        tooltip=item_data.get('tooltip'),
                        permissions=item_data.get('permissions', []),
                        is_active=item_data.get('is_active', False),
                        is_expanded=item_data.get('is_expanded', False),
                        order=item_data.get('order', 0),
                        metadata=item_data.get('metadata', {}),
                        related_products=[LabInformaticsProduct(product) for product in item_data.get('related_products', [])]
                    )
                    
                    # Import troubleshooting items
                    for troubleshooting_data in item_data.get('troubleshooting_items', []):
                        troubleshooting_item = TroubleshootingItem(
                            id=troubleshooting_data['id'],
                            title=troubleshooting_data['title'],
                            category=TroubleshootingCategory(troubleshooting_data['category']),
                            severity=troubleshooting_data['severity'],
                            description=troubleshooting_data['description'],
                            solution=troubleshooting_data['solution'],
                            related_products=[LabInformaticsProduct(product) for product in troubleshooting_data['related_products']],
                            tags=troubleshooting_data['tags'],
                            url=troubleshooting_data.get('url'),
                            is_featured=troubleshooting_data.get('is_featured', False),
                            view_count=troubleshooting_data.get('view_count', 0),
                            last_updated=datetime.fromisoformat(troubleshooting_data['last_updated'])
                        )
                        item.troubleshooting_items.append(troubleshooting_item)
                    
                    # Import children
                    for child_data in item_data.get('children', []):
                        child = LabInformaticsNavigationItem(
                            id=child_data['id'],
                            title=child_data['title'],
                            type=child_data['type'],
                            icon=child_data.get('icon'),
                            url=child_data.get('url'),
                            badge=child_data.get('badge'),
                            tooltip=child_data.get('tooltip'),
                            permissions=child_data.get('permissions', []),
                            is_active=child_data.get('is_active', False),
                            is_expanded=child_data.get('is_expanded', False),
                            order=child_data.get('order', 0),
                            metadata=child_data.get('metadata', {}),
                            related_products=[LabInformaticsProduct(product) for product in child_data.get('related_products', [])]
                        )
                        item.children.append(child)
                    
                    section.items.append(item)
                
                self.layout.sections.append(section)
            
            # Sort sections by order
            self.layout.sections.sort(key=lambda x: x.order)
            
            logger.info("Lab Informatics layout imported successfully")
            
        except Exception as e:
            logger.error(f"Error importing layout: {e}")
    
    def get_layout_statistics(self) -> Dict[str, Any]:
        """Get layout statistics"""
        try:
            stats = {
                'total_sections': len(self.layout.sections),
                'total_items': 0,
                'total_children': 0,
                'active_items': 0,
                'expanded_items': 0,
                'collapsed_sections': 0,
                'total_troubleshooting_items': 0,
                'featured_troubleshooting_items': 0,
                'sections_by_category': {},
                'items_by_type': {},
                'troubleshooting_by_category': {},
                'troubleshooting_by_product': {}
            }
            
            for section in self.layout.sections:
                if section.is_collapsed:
                    stats['collapsed_sections'] += 1
                
                stats['total_items'] += len(section.items)
                
                # Count by category
                if section.category:
                    category = section.category.value
                    stats['sections_by_category'][category] = stats['sections_by_category'].get(category, 0) + 1
                
                for item in section.items:
                    if item.is_active:
                        stats['active_items'] += 1
                    
                    if item.is_expanded:
                        stats['expanded_items'] += 1
                    
                    stats['total_children'] += len(item.children)
                    
                    # Count by type
                    item_type = item.type
                    stats['items_by_type'][item_type] = stats['items_by_type'].get(item_type, 0) + 1
                    
                    # Count troubleshooting items
                    stats['total_troubleshooting_items'] += len(item.troubleshooting_items)
                    
                    for troubleshooting_item in item.troubleshooting_items:
                        if troubleshooting_item.is_featured:
                            stats['featured_troubleshooting_items'] += 1
                        
                        # Count by category
                        category = troubleshooting_item.category.value
                        stats['troubleshooting_by_category'][category] = stats['troubleshooting_by_category'].get(category, 0) + 1
                        
                        # Count by product
                        for product in troubleshooting_item.related_products:
                            product_name = product.value
                            stats['troubleshooting_by_product'][product_name] = stats['troubleshooting_by_product'].get(product_name, 0) + 1
            
            return stats
            
        except Exception as e:
            logger.error(f"Error getting layout statistics: {e}")
            return {}
    
    def validate_layout(self) -> List[str]:
        """Validate the layout configuration"""
        try:
            errors = []
            
            # Check for duplicate IDs
            all_ids = set()
            for section in self.layout.sections:
                if section.id in all_ids:
                    errors.append(f"Duplicate section ID: {section.id}")
                all_ids.add(section.id)
                
                for item in section.items:
                    if item.id in all_ids:
                        errors.append(f"Duplicate item ID: {item.id}")
                    all_ids.add(item.id)
                    
                    for child in item.children:
                        if child.id in all_ids:
                            errors.append(f"Duplicate child ID: {child.id}")
                        all_ids.add(child.id)
                    
                    for troubleshooting_item in item.troubleshooting_items:
                        if troubleshooting_item.id in all_ids:
                            errors.append(f"Duplicate troubleshooting item ID: {troubleshooting_item.id}")
                        all_ids.add(troubleshooting_item.id)
            
            # Check for missing required fields
            for section in self.layout.sections:
                if not section.title:
                    errors.append(f"Section {section.id} missing title")
                
                for item in section.items:
                    if not item.title:
                        errors.append(f"Item {item.id} missing title")
                    
                    if item.type == "link" and not item.url:
                        errors.append(f"Link item {item.id} missing URL")
            
            return errors
            
        except Exception as e:
            logger.error(f"Error validating layout: {e}")
            return [f"Validation error: {e}"]
    
    def reset_layout(self):
        """Reset layout to default configuration"""
        try:
            self._initialize_layout()
            logger.info("Lab Informatics layout reset to default configuration")
            
        except Exception as e:
            logger.error(f"Error resetting layout: {e}")
    
    def get_mobile_layout(self) -> LabInformaticsSidebarLayout:
        """Get mobile-optimized layout"""
        try:
            mobile_layout = LabInformaticsSidebarLayout(
                id="lab_informatics_mobile_sidebar",
                name="Lab Informatics Focus (Mobile)",
                description="Mobile-optimized sidebar layout for Lab Informatics",
                sections=[],
                theme=self.default_theme,
                width="100%",
                is_resizable=False,
                show_search=True,
                show_user_info=True,
                show_notifications=True,
                show_troubleshooting=True
            )
            
            # Create simplified sections for mobile
            mobile_sections = [
                self._create_mobile_dashboard_section(),
                self._create_mobile_products_section(),
                self._create_mobile_troubleshooting_section(),
                self._create_mobile_ai_section()
            ]
            
            mobile_layout.sections.extend(mobile_sections)
            
            return mobile_layout
            
        except Exception as e:
            logger.error(f"Error creating mobile layout: {e}")
            return self.layout
    
    def _create_mobile_dashboard_section(self) -> LabInformaticsSidebarSection:
        """Create mobile dashboard section"""
        return LabInformaticsSidebarSection(
            id="mobile_dashboard",
            title="Dashboard",
            icon="dashboard",
            items=[
                LabInformaticsNavigationItem(
                    id="mobile_dashboard_overview",
                    title="Overview",
                    type="link",
                    icon="dashboard",
                    url="/lab-informatics/dashboard",
                    order=1
                )
            ],
            order=1,
            is_collapsible=False
        )
    
    def _create_mobile_products_section(self) -> LabInformaticsSidebarSection:
        """Create mobile products section"""
        return LabInformaticsSidebarSection(
            id="mobile_products",
            title="Products",
            icon="lab-informatics",
            items=[
                LabInformaticsNavigationItem(
                    id="mobile_products_all",
                    title="All Products",
                    type="link",
                    icon="lab-informatics",
                    url="/lab-informatics/products",
                    order=1
                )
            ],
            order=2,
            is_collapsible=False
        )
    
    def _create_mobile_troubleshooting_section(self) -> LabInformaticsSidebarSection:
        """Create mobile troubleshooting section"""
        return LabInformaticsSidebarSection(
            id="mobile_troubleshooting",
            title="Troubleshooting",
            icon="troubleshoot",
            items=[
                LabInformaticsNavigationItem(
                    id="mobile_troubleshooting_all",
                    title="All Issues",
                    type="link",
                    icon="troubleshoot",
                    url="/lab-informatics/troubleshooting",
                    order=1
                )
            ],
            order=3,
            is_collapsible=False
        )
    
    def _create_mobile_ai_section(self) -> LabInformaticsSidebarSection:
        """Create mobile AI section"""
        return LabInformaticsSidebarSection(
            id="mobile_ai",
            title="AI Assistant",
            icon="ai",
            items=[
                LabInformaticsNavigationItem(
                    id="mobile_ai_chat",
                    title="AI Chat",
                    type="link",
                    icon="chat",
                    url="/lab-informatics/ai/chat",
                    order=1
                )
            ],
            order=4,
            is_collapsible=False
        )
