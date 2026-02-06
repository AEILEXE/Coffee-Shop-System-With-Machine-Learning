"""
Auth package for CAFÉCRAFT application.
"""

from .login import LoginScreen
from .permissions import (
    can_access,
    get_accessible_modules,
    get_inaccessible_modules,
    has_permission,
    get_permissions,
    is_valid_role,
    require_admin,
    require_manager_or_above,
    require_pos_access,
    require_inventory_access,
    require_reports_access,
    require_user_management_access,
    get_sidebar_modules,
    get_accessible_sidebar_modules,
)

__all__ = [
    "LoginScreen",
    "can_access",
    "get_accessible_modules",
    "get_inaccessible_modules",
    "has_permission",
    "get_permissions",
    "is_valid_role",
    "require_admin",
    "require_manager_or_above",
    "require_pos_access",
    "require_inventory_access",
    "require_reports_access",
    "require_user_management_access",
    "get_sidebar_modules",
    "get_accessible_sidebar_modules",
]
