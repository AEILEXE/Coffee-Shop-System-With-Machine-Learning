"""
CAFÉCRAFT CONFIGURATION & SETTINGS

Central location for all application constants:
- App metadata
- Window dimensions
- Colors and fonts
- User roles
- Feature access mapping
"""

# =======================
# APP METADATA
# =======================
APP_NAME = "CaféCraft"
APP_TITLE = "CaféCraft — Coffee Shop Management System"
APP_VERSION = "1.0.0"

# =======================
# WINDOW DIMENSIONS
# =======================
WINDOW_WIDTH = 1200
WINDOW_HEIGHT = 800
WINDOW_MIN_WIDTH = 1000
WINDOW_MIN_HEIGHT = 700

SIDEBAR_WIDTH = 220
CONTENT_PADDING = 12

# =======================
# COLORS
# =======================
# Background colors
COLOR_PRIMARY_BG = "#1a1a2e"
COLOR_SECONDARY_BG = "#16213e"
COLOR_SIDEBAR_BG = "#2f2f2f"

# Accent colors
COLOR_ACCENT = "#d4a574"
COLOR_ACCENT_LIGHT = "#e8b895"
COLOR_ACCENT_DARK = "#b8915f"

# Status colors
COLOR_SUCCESS = "#28a745"
COLOR_ERROR = "#dc3545"
COLOR_WARNING = "#ffc107"
COLOR_INFO = "#17a2b8"

# Text colors
COLOR_TEXT_PRIMARY = "white"
COLOR_TEXT_SECONDARY = "#cccccc"
COLOR_TEXT_MUTED = "#999999"

# Button states
COLOR_BUTTON_HOVER = "#343a40"
COLOR_BUTTON_DISABLED = "#505050"

# =======================
# FONTS
# =======================
# Font families
FONT_PRIMARY = "Georgia"
FONT_SECONDARY = "Sans"
FONT_MONOSPACE = "Courier New"

# Font sizes
FONT_SIZE_SMALL = 10
FONT_SIZE_NORMAL = 12
FONT_SIZE_MEDIUM = 14
FONT_SIZE_LARGE = 16
FONT_SIZE_XLARGE = 20
FONT_SIZE_TITLE = 32

# Font styles (weight and family combinations)
FONT_TITLE = (FONT_PRIMARY, FONT_SIZE_TITLE, "bold")
FONT_HEADING = (FONT_PRIMARY, FONT_SIZE_LARGE, "bold")
FONT_SUBHEADING = (FONT_SECONDARY, FONT_SIZE_MEDIUM, "bold")
FONT_NORMAL = (FONT_SECONDARY, FONT_SIZE_NORMAL)
FONT_SMALL = (FONT_SECONDARY, FONT_SIZE_SMALL)

# =======================
# USER ROLES
# =======================
ROLE_OWNER = "owner"
ROLE_ADMIN = "admin"
ROLE_MANAGER = "manager"
ROLE_CASHIER = "cashier"
ROLE_INVENTORY_STAFF = "inventory_staff"
ROLE_EMPLOYEE = "employee"

VALID_ROLES = [
    ROLE_OWNER,
    ROLE_ADMIN,
    ROLE_MANAGER,
    ROLE_CASHIER,
    ROLE_INVENTORY_STAFF,
    ROLE_EMPLOYEE,
]

# =======================
# ROLE-BASED ACCESS CONTROL
# =======================
# Sidebar module access mapping: role -> list of accessible modules
ROLE_ACCESS_MAP = {
    ROLE_OWNER: {
        "pos": True,
        "inventory": True,
        "reports": True,
        "user_management": True,
    },
    ROLE_ADMIN: {
        "pos": True,
        "inventory": True,
        "reports": True,
        "user_management": True,
    },
    ROLE_MANAGER: {
        "pos": True,
        "inventory": True,
        "reports": True,
        "user_management": False,
    },
    ROLE_CASHIER: {
        "pos": True,
        "inventory": False,
        "reports": False,
        "user_management": False,
    },
    ROLE_INVENTORY_STAFF: {
        "pos": False,
        "inventory": True,
        "reports": False,
        "user_management": False,
    },
    ROLE_EMPLOYEE: {
        "pos": True,
        "inventory": False,
        "reports": False,
        "user_management": False,
    },
}

# =======================
# PERMISSION DEFAULTS BY ROLE
# =======================
# Default permission settings for new users based on role
PERMISSION_DEFAULTS = {
    ROLE_OWNER: {
        "can_pos": 1,
        "can_inventory": 1,
        "can_reports": 1,
        "can_user_management": 1,
    },
    ROLE_ADMIN: {
        "can_pos": 1,
        "can_inventory": 1,
        "can_reports": 1,
        "can_user_management": 1,
    },
    ROLE_MANAGER: {
        "can_pos": 1,
        "can_inventory": 1,
        "can_reports": 1,
        "can_user_management": 0,
    },
    ROLE_CASHIER: {
        "can_pos": 1,
        "can_inventory": 0,
        "can_reports": 0,
        "can_user_management": 0,
    },
    ROLE_INVENTORY_STAFF: {
        "can_pos": 0,
        "can_inventory": 1,
        "can_reports": 0,
        "can_user_management": 0,
    },
    ROLE_EMPLOYEE: {
        "can_pos": 1,
        "can_inventory": 0,
        "can_reports": 0,
        "can_user_management": 0,
    },
}

# =======================
# SIDEBAR NAVIGATION
# =======================
SIDEBAR_MODULES = [
    {
        "key": "pos",
        "label": "POS",
        "icon": "shopping_cart",  # Placeholder for icon name
    },
    {
        "key": "inventory",
        "label": "Inventory",
        "icon": "warehouse",
    },
    {
        "key": "reports",
        "label": "Reports",
        "icon": "bar_chart",
    },
    {
        "key": "user_management",
        "label": "User Management",
        "icon": "users",
    },
]

# =======================
# BUTTON DIMENSIONS
# =======================
BUTTON_WIDTH = 180
BUTTON_HEIGHT = 40
BUTTON_PADDING_X = 10
BUTTON_PADDING_Y = 5

# =======================
# DIALOG DIMENSIONS
# =======================
DIALOG_USER_MGMT_WIDTH = 800
DIALOG_USER_MGMT_HEIGHT = 600
DIALOG_ADD_USER_WIDTH = 400
DIALOG_ADD_USER_HEIGHT = 500
DIALOG_EDIT_USER_WIDTH = 400
DIALOG_EDIT_USER_HEIGHT = 400

# =======================
# PASSWORD REQUIREMENTS
# =======================
PASSWORD_MIN_LENGTH = 12
PASSWORD_REQUIRE_LOWERCASE = True
PASSWORD_REQUIRE_UPPERCASE = True
PASSWORD_REQUIRE_NUMBERS = True
PASSWORD_REQUIRE_SPECIAL = True

# =======================
# DATABASE
# =======================
DB_NAME = "cafecraft.db"

# =======================
# HELPER FUNCTION
# =======================
def get_access_for_role(role):
    """Get sidebar module access for a given role."""
    return ROLE_ACCESS_MAP.get(role, {})


def get_permissions_for_role(role):
    """Get default permissions for a given role."""
    return PERMISSION_DEFAULTS.get(role, {})


def is_role_valid(role):
    """Check if role is valid."""
    return role in VALID_ROLES
