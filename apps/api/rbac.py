"""
Role-Based Access Control (RBAC) Configuration
Defines roles, permissions, and access control for Nexus Data Platform
"""

from enum import Enum
from typing import List, Set
from pydantic import BaseModel


# ============================================
# Role Definitions
# ============================================

class Role(str, Enum):
    """Platform roles with hierarchical permissions"""
    ADMIN = "admin"                      # Full platform access
    DATA_ENGINEER = "data_engineer"      # ETL, pipeline management
    DATA_SCIENTIST = "data_scientist"    # Data access, ML models
    ANALYST = "analyst"                  # Read analytics, dashboards
    VIEWER = "viewer"                    # Read-only access
    API_CLIENT = "api_client"            # External API consumers


# ============================================
# Permission Definitions
# ============================================

class Permission(str, Enum):
    """Granular permissions for platform operations"""
    
    # Data Access
    READ_BRONZE = "read:bronze"
    READ_SILVER = "read:silver"
    READ_GOLD = "read:gold"
    WRITE_BRONZE = "write:bronze"
    WRITE_SILVER = "write:silver"
    WRITE_GOLD = "write:gold"
    
    # Pipeline Management
    VIEW_PIPELINES = "view:pipelines"
    RUN_PIPELINES = "run:pipelines"
    MANAGE_PIPELINES = "manage:pipelines"
    
    # Kafka Operations
    PRODUCE_KAFKA = "produce:kafka"
    CONSUME_KAFKA = "consume:kafka"
    MANAGE_KAFKA_TOPICS = "manage:kafka_topics"
    
    # Spark Operations
    SUBMIT_SPARK_JOB = "submit:spark_job"
    MANAGE_SPARK_CLUSTER = "manage:spark_cluster"
    
    # Monitoring
    VIEW_METRICS = "view:metrics"
    VIEW_LOGS = "view:logs"
    MANAGE_ALERTS = "manage:alerts"
    
    # Data Quality
    VIEW_QUALITY_REPORTS = "view:quality_reports"
    RUN_QUALITY_CHECKS = "run:quality_checks"
    MANAGE_QUALITY_RULES = "manage:quality_rules"
    
    # Metadata & Lineage
    VIEW_METADATA = "view:metadata"
    EDIT_METADATA = "edit:metadata"
    VIEW_LINEAGE = "view:lineage"
    
    # Analytics
    VIEW_DASHBOARDS = "view:dashboards"
    EDIT_DASHBOARDS = "edit:dashboards"
    QUERY_CLICKHOUSE = "query:clickhouse"
    
    # API Access
    INGEST_DATA = "ingest:data"
    QUERY_API = "query:api"
    
    # System Administration
    MANAGE_USERS = "manage:users"
    MANAGE_ROLES = "manage:roles"
    MANAGE_SERVICES = "manage:services"
    VIEW_AUDIT_LOGS = "view:audit_logs"


# ============================================
# Role-Permission Mapping
# ============================================

ROLE_PERMISSIONS: dict[Role, Set[Permission]] = {
    
    Role.ADMIN: {
        # Admins have ALL permissions
        *list(Permission)
    },
    
    Role.DATA_ENGINEER: {
        # Data layer access
        Permission.READ_BRONZE,
        Permission.READ_SILVER,
        Permission.READ_GOLD,
        Permission.WRITE_BRONZE,
        Permission.WRITE_SILVER,
        Permission.WRITE_GOLD,
        
        # Pipeline management
        Permission.VIEW_PIPELINES,
        Permission.RUN_PIPELINES,
        Permission.MANAGE_PIPELINES,
        
        # Kafka operations
        Permission.PRODUCE_KAFKA,
        Permission.CONSUME_KAFKA,
        Permission.MANAGE_KAFKA_TOPICS,
        
        # Spark operations
        Permission.SUBMIT_SPARK_JOB,
        
        # Monitoring
        Permission.VIEW_METRICS,
        Permission.VIEW_LOGS,
        
        # Data quality
        Permission.VIEW_QUALITY_REPORTS,
        Permission.RUN_QUALITY_CHECKS,
        Permission.MANAGE_QUALITY_RULES,
        
        # Metadata
        Permission.VIEW_METADATA,
        Permission.EDIT_METADATA,
        Permission.VIEW_LINEAGE,
        
        # API
        Permission.INGEST_DATA,
    },
    
    Role.DATA_SCIENTIST: {
        # Read access to curated data
        Permission.READ_SILVER,
        Permission.READ_GOLD,
        
        # Pipeline viewing
        Permission.VIEW_PIPELINES,
        Permission.RUN_PIPELINES,  # Run ML pipelines
        
        # Spark jobs
        Permission.SUBMIT_SPARK_JOB,
        
        # Monitoring
        Permission.VIEW_METRICS,
        Permission.VIEW_LOGS,
        
        # Data quality
        Permission.VIEW_QUALITY_REPORTS,
        
        # Metadata
        Permission.VIEW_METADATA,
        Permission.VIEW_LINEAGE,
        
        # Analytics
        Permission.VIEW_DASHBOARDS,
        Permission.QUERY_CLICKHOUSE,
        
        # API
        Permission.QUERY_API,
    },
    
    Role.ANALYST: {
        # Read access to analytics layer
        Permission.READ_GOLD,
        
        # Pipeline viewing only
        Permission.VIEW_PIPELINES,
        
        # Monitoring
        Permission.VIEW_METRICS,
        
        # Data quality
        Permission.VIEW_QUALITY_REPORTS,
        
        # Metadata
        Permission.VIEW_METADATA,
        Permission.VIEW_LINEAGE,
        
        # Analytics
        Permission.VIEW_DASHBOARDS,
        Permission.EDIT_DASHBOARDS,
        Permission.QUERY_CLICKHOUSE,
        
        # API
        Permission.QUERY_API,
    },
    
    Role.VIEWER: {
        # Read-only access
        Permission.READ_GOLD,
        Permission.VIEW_PIPELINES,
        Permission.VIEW_METRICS,
        Permission.VIEW_QUALITY_REPORTS,
        Permission.VIEW_METADATA,
        Permission.VIEW_DASHBOARDS,
    },
    
    Role.API_CLIENT: {
        # External API consumers
        Permission.INGEST_DATA,
        Permission.QUERY_API,
        Permission.VIEW_METRICS,
    },
}


# ============================================
# RBAC Models
# ============================================

class User(BaseModel):
    """User model with role assignment"""
    username: str
    email: str
    roles: List[Role]
    active: bool = True
    
    def has_permission(self, permission: Permission) -> bool:
        """Check if user has a specific permission"""
        for role in self.roles:
            if permission in ROLE_PERMISSIONS.get(role, set()):
                return True
        return False
    
    def has_any_permission(self, permissions: List[Permission]) -> bool:
        """Check if user has any of the given permissions"""
        return any(self.has_permission(perm) for perm in permissions)
    
    def has_all_permissions(self, permissions: List[Permission]) -> bool:
        """Check if user has all of the given permissions"""
        return all(self.has_permission(perm) for perm in permissions)
    
    def get_permissions(self) -> Set[Permission]:
        """Get all permissions for user's roles"""
        permissions = set()
        for role in self.roles:
            permissions.update(ROLE_PERMISSIONS.get(role, set()))
        return permissions


# ============================================
# Resource-Based Access Control
# ============================================

class Resource(str, Enum):
    """Platform resources that can be access-controlled"""
    BRONZE_DATA = "bronze_data"
    SILVER_DATA = "silver_data"
    GOLD_DATA = "gold_data"
    PIPELINE = "pipeline"
    KAFKA_TOPIC = "kafka_topic"
    SPARK_JOB = "spark_job"
    DASHBOARD = "dashboard"
    QUALITY_RULE = "quality_rule"


class Action(str, Enum):
    """Actions that can be performed on resources"""
    CREATE = "create"
    READ = "read"
    UPDATE = "update"
    DELETE = "delete"
    EXECUTE = "execute"


# Resource-Action to Permission mapping
RESOURCE_ACTION_PERMISSIONS = {
    (Resource.BRONZE_DATA, Action.READ): Permission.READ_BRONZE,
    (Resource.BRONZE_DATA, Action.CREATE): Permission.WRITE_BRONZE,
    (Resource.BRONZE_DATA, Action.UPDATE): Permission.WRITE_BRONZE,
    
    (Resource.SILVER_DATA, Action.READ): Permission.READ_SILVER,
    (Resource.SILVER_DATA, Action.CREATE): Permission.WRITE_SILVER,
    (Resource.SILVER_DATA, Action.UPDATE): Permission.WRITE_SILVER,
    
    (Resource.GOLD_DATA, Action.READ): Permission.READ_GOLD,
    (Resource.GOLD_DATA, Action.CREATE): Permission.WRITE_GOLD,
    (Resource.GOLD_DATA, Action.UPDATE): Permission.WRITE_GOLD,
    
    (Resource.PIPELINE, Action.READ): Permission.VIEW_PIPELINES,
    (Resource.PIPELINE, Action.EXECUTE): Permission.RUN_PIPELINES,
    (Resource.PIPELINE, Action.CREATE): Permission.MANAGE_PIPELINES,
    (Resource.PIPELINE, Action.UPDATE): Permission.MANAGE_PIPELINES,
    (Resource.PIPELINE, Action.DELETE): Permission.MANAGE_PIPELINES,
    
    (Resource.KAFKA_TOPIC, Action.CREATE): Permission.MANAGE_KAFKA_TOPICS,
    (Resource.KAFKA_TOPIC, Action.DELETE): Permission.MANAGE_KAFKA_TOPICS,
    
    (Resource.SPARK_JOB, Action.EXECUTE): Permission.SUBMIT_SPARK_JOB,
    
    (Resource.DASHBOARD, Action.READ): Permission.VIEW_DASHBOARDS,
    (Resource.DASHBOARD, Action.UPDATE): Permission.EDIT_DASHBOARDS,
    
    (Resource.QUALITY_RULE, Action.READ): Permission.VIEW_QUALITY_REPORTS,
    (Resource.QUALITY_RULE, Action.CREATE): Permission.MANAGE_QUALITY_RULES,
    (Resource.QUALITY_RULE, Action.UPDATE): Permission.MANAGE_QUALITY_RULES,
    (Resource.QUALITY_RULE, Action.DELETE): Permission.MANAGE_QUALITY_RULES,
}


def check_resource_access(user: User, resource: Resource, action: Action) -> bool:
    """Check if user can perform action on resource"""
    required_permission = RESOURCE_ACTION_PERMISSIONS.get((resource, action))
    if not required_permission:
        return False
    return user.has_permission(required_permission)


# ============================================
# Example Users (for testing)
# ============================================

DEMO_USERS = {
    "admin": User(
        username="admin",
        email="admin@nexus.com",
        roles=[Role.ADMIN]
    ),
    "engineer": User(
        username="data_engineer",
        email="engineer@nexus.com",
        roles=[Role.DATA_ENGINEER]
    ),
    "scientist": User(
        username="data_scientist",
        email="scientist@nexus.com",
        roles=[Role.DATA_SCIENTIST]
    ),
    "analyst": User(
        username="analyst",
        email="analyst@nexus.com",
        roles=[Role.ANALYST]
    ),
    "viewer": User(
        username="viewer",
        email="viewer@nexus.com",
        roles=[Role.VIEWER]
    ),
    "api_client": User(
        username="api_client",
        email="client@external.com",
        roles=[Role.API_CLIENT]
    ),
}
