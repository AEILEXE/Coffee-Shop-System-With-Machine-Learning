"""
CAFÉCRAFT PERMISSIONS & ROLE-BASED ACCESS CONTROL

Responsibilities:
- Role-based access control logic
- Permission checking functions
- Used by sidebar and module loaders

No GUI dependencies.
"""

from config.settings import (
    ROLE_ACCESS_MAP,
    PERMISSION_DEFAULTS,
    VALID_ROLES,
)
from typing import List, Dict, Optional


# =======================
# ACCESS CONTROL
# =======================

def can_access(role: str, module_name: str) -> bool:
    """
    Check if a role can access a specific module.
    
    Args:
        role: User role (e.g., 'admin', 'cashier').
        module_name: Module name (e.g., 'pos', 'inventory', 'reports').
        
    Returns:
        True if role can access module, False otherwise.
    """
    if role not in ROLE_ACCESS_MAP:
        return False
    
    access_map = ROLE_ACCESS_MAP[role]
    return access_map.get(module_name, False)


def get_accessible_modules(role: str) -> List[str]:
    """
    Get list of all modules accessible to a role.
    
    Args:
        role: User role.
        
    Returns:
        List of module names accessible to the role.
    """
    if role not in ROLE_ACCESS_MAP:
        return []
    
    access_map = ROLE_ACCESS_MAP[role]
    return [module for module, accessible in access_map.items() if accessible]


def get_inaccessible_modules(role: str) -> List[str]:
    """
    Get list of all modules NOT accessible to a role.
    
    Args:
        role: User role.
        
    Returns:
        List of module names not accessible to the role.
    """
    if role not in ROLE_ACCESS_MAP:
        return []
    
    access_map = ROLE_ACCESS_MAP[role]
    return [module for module, accessible in access_map.items() if not accessible]


def can_access_multiple(role: str, module_names: List[str]) -> bool:
    """
    Check if a role can access ALL modules in a list.
    
    Args:
        role: User role.
        module_names: List of module names to check.
        
    Returns:
        True if role can access all modules, False otherwise.
    """
    return all(can_access(role, module) for module in module_names)


def can_access_any(role: str, module_names: List[str]) -> bool:
    """
    Check if a role can access ANY module in a list.
    
    Args:
        role: User role.
        module_names: List of module names to check.
        
    Returns:
        True if role can access at least one module, False otherwise.
    """
    return any(can_access(role, module) for module in module_names)


# =======================
# PERMISSION CHECKS
# =======================

def has_permission(role: str, permission_key: str) -> bool:
    """
    Check if a role has a specific permission.
    
    Permission keys: 'can_pos', 'can_inventory', 'can_reports', 'can_user_management'
    
    Args:
        role: User role.
        permission_key: Permission key (e.g., 'can_pos').
        
    Returns:
        True if role has permission, False otherwise.
    """
    if role not in PERMISSION_DEFAULTS:
        return False
    
    permissions = PERMISSION_DEFAULTS[role]
    return bool(permissions.get(permission_key, 0))


def get_permissions(role: str) -> Dict[str, int]:
    """
    Get all permissions for a role.
    
    Args:
        role: User role.
        
    Returns:
        Dictionary of permission keys and values (0 or 1).
    """
    return PERMISSION_DEFAULTS.get(role, {})


def has_any_permission(role: str, permission_keys: List[str]) -> bool:
    """
    Check if a role has ANY of the specified permissions.
    
    Args:
        role: User role.
        permission_keys: List of permission keys to check.
        
    Returns:
        True if role has at least one permission, False otherwise.
    """
    return any(has_permission(role, key) for key in permission_keys)


def has_all_permissions(role: str, permission_keys: List[str]) -> bool:
    """
    Check if a role has ALL of the specified permissions.
    
    Args:
        role: User role.
        permission_keys: List of permission keys to check.
        
    Returns:
        True if role has all permissions, False otherwise.
    """
    return all(has_permission(role, key) for key in permission_keys)


# =======================
# ROLE VALIDATION
# =======================

def is_valid_role(role: str) -> bool:
    """
    Check if a role is valid.
    
    Args:
        role: Role name to validate.
        
    Returns:
        True if role is in VALID_ROLES, False otherwise.
    """
    return role in VALID_ROLES


def validate_role(role: str) -> str:
    """
    Validate and normalize a role.
    
    Args:
        role: Role to validate.
        
    Returns:
        The role if valid.
        
    Raises:
        ValueError: If role is invalid.
    """
    if not is_valid_role(role):
        raise ValueError(f"Invalid role: {role}. Valid roles: {VALID_ROLES}")
    return role


# =======================
# PERMISSION HELPERS
# =======================

def require_admin(role: str) -> bool:
    """
    Check if role is admin or owner.
    
    Args:
        role: User role.
        
    Returns:
        True if user is admin or owner, False otherwise.
    """
    return role in ["owner", "admin"]


def require_manager_or_above(role: str) -> bool:
    """
    Check if role is manager, admin, or owner.
    
    Args:
        role: User role.
        
    Returns:
        True if user is manager or above, False otherwise.
    """
    return role in ["owner", "admin", "manager"]


def require_pos_access(role: str) -> bool:
    """
    Check if role can access POS system.
    
    Args:
        role: User role.
        
    Returns:
        True if user can access POS, False otherwise.
    """
    return can_access(role, "pos")


def require_inventory_access(role: str) -> bool:
    """
    Check if role can access inventory system.
    
    Args:
        role: User role.
        
    Returns:
        True if user can access inventory, False otherwise.
    """
    return can_access(role, "inventory")


def require_reports_access(role: str) -> bool:
    """
    Check if role can access reports.
    
    Args:
        role: User role.
        
    Returns:
        True if user can access reports, False otherwise.
    """
    return can_access(role, "reports")


def require_user_management_access(role: str) -> bool:
    """
    Check if role can manage users.
    
    Args:
        role: User role.
        
    Returns:
        True if user can manage other users, False otherwise.
    """
    return can_access(role, "user_management")


# =======================
# DECORATOR FOR PERMISSION CHECKS
# =======================

def require_role(required_role):
    """
    Decorator to guard functions/methods by required role.
    
    Usage:
        @require_role('admin')
        def admin_only_function():
            pass
    
    Args:
        required_role: Single role string or list of allowed roles.
        
    Returns:
        Decorator function.
    """
    if isinstance(required_role, str):
        allowed_roles = {required_role}
    else:
        allowed_roles = set(required_role)
    
    def decorator(func):
        def wrapper(current_user_role, *args, **kwargs):
            if current_user_role not in allowed_roles:
                raise PermissionError(
                    f"User role '{current_user_role}' is not authorized. "
                    f"Required: {allowed_roles}"
                )
            return func(*args, **kwargs)
        return wrapper
    return decorator


def require_permission_dec(permission_key):
    """
    Decorator to guard functions/methods by required permission.
    
    Usage:
        @require_permission_dec('can_user_management')
        def user_management_function():
            pass
    
    Args:
        permission_key: Permission key to check.
        
    Returns:
        Decorator function.
    """
    def decorator(func):
        def wrapper(current_user_role, *args, **kwargs):
            if not has_permission(current_user_role, permission_key):
                raise PermissionError(
                    f"User role '{current_user_role}' does not have "
                    f"permission '{permission_key}'"
                )
            return func(*args, **kwargs)
        return wrapper
    return decorator


# =======================
# SIDEBAR MODULE FILTERING
# =======================

def get_sidebar_modules(role: str) -> List[Dict]:
    """
    Get sidebar module configuration filtered for a role.
    
    Used by GUI to build sidebar navigation.
    
    Args:
        role: User role.
        
    Returns:
        List of module dicts with access info.
    """
    from config.settings import SIDEBAR_MODULES
    
    accessible = get_accessible_modules(role)
    
    modules = []
    for module in SIDEBAR_MODULES:
        is_accessible = module["key"] in accessible
        modules.append({
            **module,
            "accessible": is_accessible,
            "locked": not is_accessible,
        })
    
    return modules


def get_accessible_sidebar_modules(role: str) -> List[Dict]:
    """
    Get only accessible sidebar modules for a role.
    
    Args:
        role: User role.
        
    Returns:
        List of accessible module dicts.
    """
    all_modules = get_sidebar_modules(role)
    return [m for m in all_modules if m["accessible"]]
