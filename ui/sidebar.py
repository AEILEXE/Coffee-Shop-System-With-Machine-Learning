"""
CAFÉCRAFT SIDEBAR NAVIGATION COMPONENT

Responsibilities:
- Reusable sidebar navigation widget
- Show/hide buttons based on user role
- Highlight active module
- Trigger content switching callbacks
- Support for dynamic module buttons

No database logic.
"""

try:
    import customtkinter as ctk
    CTK_AVAILABLE = True
except ImportError:
    import tkinter as tk
    CTK_AVAILABLE = False

from auth.permissions import (
    get_accessible_sidebar_modules,
    can_access,
)
from config.settings import (
    SIDEBAR_WIDTH,
    COLOR_SECONDARY_BG,
    COLOR_ACCENT,
    COLOR_ERROR,
    COLOR_TEXT_PRIMARY,
    SIDEBAR_MODULES,
)
from typing import Callable, Optional, List, Dict


class Sidebar:
    """Reusable sidebar navigation component."""

    def __init__(
        self,
        parent,
        user_role: str,
        on_module_selected: Optional[Callable[[str], None]] = None,
        on_logout: Optional[Callable[[], None]] = None,
    ):
        """
        Initialize sidebar.

        Args:
            parent: Parent widget.
            user_role: Role of logged-in user.
            on_module_selected: Callback function(module_name) when module button clicked.
            on_logout: Callback function() when logout button clicked.
        """
        self.parent = parent
        self.user_role = user_role
        self.on_module_selected = on_module_selected
        self.on_logout = on_logout
        self.active_module = None
        self.module_buttons = {}

        # Create sidebar frame
        if CTK_AVAILABLE:
            self.frame = ctk.CTkFrame(
                parent,
                width=SIDEBAR_WIDTH,
                corner_radius=0,
                fg_color=COLOR_SECONDARY_BG,
            )
        else:
            self.frame = tk.Frame(
                parent,
                width=SIDEBAR_WIDTH,
                bg=COLOR_SECONDARY_BG,
            )
        self.frame.pack_propagate(False)

        # Build sidebar
        self._build_sidebar()

    def _build_sidebar(self):
        """Build sidebar structure."""
        # Title
        if CTK_AVAILABLE:
            title = ctk.CTkLabel(
                self.frame,
                text="Navigation",
                font=ctk.CTkFont(size=16, weight="bold"),
                text_color=COLOR_ACCENT,
            )
        else:
            title = tk.Label(
                self.frame,
                text="Navigation",
                font=("Georgia", 16, "bold"),
                fg=COLOR_ACCENT,
                bg=COLOR_SECONDARY_BG,
            )
        title.pack(pady=(20, 15), padx=15)

        # Scrollable modules section
        if CTK_AVAILABLE:
            self.modules_frame = ctk.CTkFrame(
                self.frame,
                fg_color="transparent",
            )
        else:
            self.modules_frame = tk.Frame(
                self.frame,
                bg=COLOR_SECONDARY_BG,
            )
        self.modules_frame.pack(fill="both", expand=True, padx=15, pady=10)

        # Build module buttons
        self._build_module_buttons()

        # Bottom section (spacer + logout)
        if CTK_AVAILABLE:
            bottom_frame = ctk.CTkFrame(
                self.frame,
                fg_color="transparent",
            )
        else:
            bottom_frame = tk.Frame(
                self.frame,
                bg=COLOR_SECONDARY_BG,
            )
        bottom_frame.pack(fill="x", padx=15, pady=15)

        # Logout button
        if CTK_AVAILABLE:
            logout_btn = ctk.CTkButton(
                bottom_frame,
                text="Logout",
                width=SIDEBAR_WIDTH - 30,
                fg_color=COLOR_ERROR,
                hover_color="#a02020",
                command=self._on_logout_clicked,
            )
        else:
            logout_btn = tk.Button(
                bottom_frame,
                text="Logout",
                width=25,
                bg=COLOR_ERROR,
                fg="white",
                relief="flat",
                command=self._on_logout_clicked,
            )
        logout_btn.pack(side="bottom")

    def _build_module_buttons(self):
        """Build navigation buttons for accessible modules."""
        # Clear existing buttons
        self.module_buttons.clear()
        for widget in self.modules_frame.winfo_children():
            widget.destroy()

        # Get accessible modules
        accessible_modules = get_accessible_sidebar_modules(self.user_role)

        # Create button for each accessible module
        for module in accessible_modules:
            self._add_module_button(module)

    def _add_module_button(self, module: Dict):
        """
        Add a module button to the sidebar.

        Args:
            module: Module dict with 'key' and 'label'.
        """
        module_key = module["key"]
        module_label = module["label"]

        if CTK_AVAILABLE:
            btn = ctk.CTkButton(
                self.modules_frame,
                text=module_label,
                width=SIDEBAR_WIDTH - 30,
                fg_color="#3a3a4e",
                hover_color="#4a4a5e",
                command=lambda: self._on_module_clicked(module_key),
            )
        else:
            btn = tk.Button(
                self.modules_frame,
                text=module_label,
                width=25,
                bg="#3a3a4e",
                fg=COLOR_TEXT_PRIMARY,
                activebackground="#4a4a5e",
                relief="flat",
                command=lambda: self._on_module_clicked(module_key),
            )
        btn.pack(pady=8, fill="x")

        self.module_buttons[module_key] = btn

    def _on_module_clicked(self, module_name: str):
        """Called when a module button is clicked."""
        # Update active state
        self.set_active_module(module_name)

        # Invoke callback
        if self.on_module_selected:
            self.on_module_selected(module_name)

    def _on_logout_clicked(self):
        """Called when logout button is clicked."""
        if self.on_logout:
            self.on_logout()

    def set_active_module(self, module_name: str):
        """
        Highlight the active module button.

        Args:
            module_name: Module name to highlight.
        """
        # Reset all buttons to default color
        for btn in self.module_buttons.values():
            if CTK_AVAILABLE:
                btn.configure(fg_color="#3a3a4e")
            else:
                btn.configure(bg="#3a3a4e")

        # Highlight active button
        if module_name in self.module_buttons:
            btn = self.module_buttons[module_name]
            if CTK_AVAILABLE:
                btn.configure(fg_color=COLOR_ACCENT)
            else:
                btn.configure(bg=COLOR_ACCENT, fg="#1a1a2e")

        self.active_module = module_name

    def refresh_modules(self, user_role: str):
        """
        Refresh sidebar after role change.

        Args:
            user_role: New user role.
        """
        self.user_role = user_role
        self.module_buttons.clear()
        self._build_module_buttons()
        self.active_module = None

    def add_custom_button(
        self,
        button_text: str,
        callback: Callable[[], None],
        color: str = "#3a3a4e",
    ):
        """
        Add a custom button to the sidebar.

        Args:
            button_text: Text to display on button.
            callback: Function to call when button clicked.
            color: Background color for button.
        """
        if CTK_AVAILABLE:
            btn = ctk.CTkButton(
                self.modules_frame,
                text=button_text,
                width=SIDEBAR_WIDTH - 30,
                fg_color=color,
                hover_color="#4a4a5e",
                command=callback,
            )
        else:
            btn = tk.Button(
                self.modules_frame,
                text=button_text,
                width=25,
                bg=color,
                fg=COLOR_TEXT_PRIMARY,
                activebackground="#4a4a5e",
                relief="flat",
                command=callback,
            )
        btn.pack(pady=8, fill="x")

        return btn

    def show(self):
        """Pack the sidebar frame."""
        self.frame.pack(side="left", fill="y")

    def hide(self):
        """Unpack the sidebar frame."""
        self.frame.pack_forget()

    def get_frame(self):
        """Get the sidebar frame widget."""
        return self.frame


class SimpleSidebar:
    """Lightweight sidebar variant with minimal features."""

    def __init__(
        self,
        parent,
        modules: Optional[List[Dict]] = None,
        on_module_selected: Optional[Callable[[str], None]] = None,
    ):
        """
        Initialize lightweight sidebar.

        Args:
            parent: Parent widget.
            modules: List of module dicts with 'key' and 'label'.
            on_module_selected: Callback function(module_name).
        """
        self.parent = parent
        self.modules = modules or SIDEBAR_MODULES
        self.on_module_selected = on_module_selected
        self.active_module = None
        self.module_buttons = {}

        # Create frame
        if CTK_AVAILABLE:
            self.frame = ctk.CTkFrame(
                parent,
                width=SIDEBAR_WIDTH,
                fg_color=COLOR_SECONDARY_BG,
            )
        else:
            self.frame = tk.Frame(
                parent,
                width=SIDEBAR_WIDTH,
                bg=COLOR_SECONDARY_BG,
            )
        self.frame.pack_propagate(False)

        self._build()

    def _build(self):
        """Build simple sidebar."""
        if CTK_AVAILABLE:
            modules_frame = ctk.CTkFrame(
                self.frame,
                fg_color="transparent",
            )
        else:
            modules_frame = tk.Frame(
                self.frame,
                bg=COLOR_SECONDARY_BG,
            )
        modules_frame.pack(fill="both", expand=True, padx=10, pady=10)

        # Create buttons
        for module in self.modules:
            btn = self._create_button(modules_frame, module)
            self.module_buttons[module["key"]] = btn

    def _create_button(self, parent, module: Dict):
        """Create a module button."""
        if CTK_AVAILABLE:
            btn = ctk.CTkButton(
                parent,
                text=module["label"],
                width=SIDEBAR_WIDTH - 20,
                fg_color="#3a3a4e",
                hover_color="#4a4a5e",
                command=lambda: self._button_clicked(module["key"]),
            )
        else:
            btn = tk.Button(
                parent,
                text=module["label"],
                width=22,
                bg="#3a3a4e",
                fg=COLOR_TEXT_PRIMARY,
                relief="flat",
                command=lambda: self._button_clicked(module["key"]),
            )
        btn.pack(pady=5, fill="x")
        return btn

    def _button_clicked(self, module_key: str):
        """Handle button click."""
        self.set_active(module_key)
        if self.on_module_selected:
            self.on_module_selected(module_key)

    def set_active(self, module_key: str):
        """Highlight active module."""
        # Reset all
        for btn in self.module_buttons.values():
            if CTK_AVAILABLE:
                btn.configure(fg_color="#3a3a4e")
            else:
                btn.configure(bg="#3a3a4e")

        # Highlight active
        if module_key in self.module_buttons:
            btn = self.module_buttons[module_key]
            if CTK_AVAILABLE:
                btn.configure(fg_color=COLOR_ACCENT)
            else:
                btn.configure(bg=COLOR_ACCENT, fg="#1a1a2e")

        self.active_module = module_key

    def get_frame(self):
        """Get sidebar frame."""
        return self.frame
