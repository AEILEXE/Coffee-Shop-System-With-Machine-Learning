"""
CAFÉCRAFT MAIN DASHBOARD

Responsibilities:
- Main application layout (header, sidebar, content)
- Dynamic module loading (POS, Inventory, Reports, User Management)
- User session info storage and display
- Navigation between modules
- Role-based sidebar visibility

Uses auth.permissions for access control.
No direct SQL queries.
"""

try:
    import customtkinter as ctk
    CTK_AVAILABLE = True
except ImportError:
    import tkinter as tk
    CTK_AVAILABLE = False

from tkinter import messagebox
from auth.login import LoginScreen
from auth.permissions import (
    get_accessible_sidebar_modules,
    can_access,
    require_admin,
)
from config.settings import (
    APP_NAME,
    WINDOW_WIDTH,
    WINDOW_HEIGHT,
    SIDEBAR_WIDTH,
    COLOR_PRIMARY_BG,
    COLOR_SECONDARY_BG,
    COLOR_ACCENT,
    COLOR_SUCCESS,
    COLOR_ERROR,
    COLOR_TEXT_PRIMARY,
    FONT_HEADING,
    FONT_NORMAL,
)


class Dashboard:
    """Main application dashboard with sidebar navigation and dynamic module loading."""

    def __init__(self, root_window):
        """
        Initialize dashboard.

        Args:
            root_window: The main CustomTkinter root window.
        """
        self.root = root_window
        self.current_user = None
        self.current_module = None
        self.content_frame = None

        # Build the dashboard layout
        self._build_layout()

        # Show login screen first
        self._show_login()

    def _build_layout(self):
        """Build main dashboard layout structure."""
        # Main container
        if CTK_AVAILABLE:
            main_container = ctk.CTkFrame(self.root, fg_color=COLOR_PRIMARY_BG)
        else:
            main_container = tk.Frame(self.root, bg=COLOR_PRIMARY_BG)
        main_container.pack(fill="both", expand=True)

        # Header
        self._build_header(main_container)

        # Body container (sidebar + content)
        if CTK_AVAILABLE:
            body_container = ctk.CTkFrame(main_container, fg_color=COLOR_PRIMARY_BG)
        else:
            body_container = tk.Frame(main_container, bg=COLOR_PRIMARY_BG)
        body_container.pack(fill="both", expand=True, padx=0, pady=0)
        body_container.grid_columnconfigure(1, weight=1)
        body_container.grid_rowconfigure(0, weight=1)

        # Sidebar
        self.sidebar_frame = self._build_sidebar(body_container)
        self.sidebar_frame.grid(row=0, column=0, sticky="nsw")

        # Content area
        self.content_frame = self._build_content_area(body_container)
        self.content_frame.grid(row=0, column=1, sticky="nsew", padx=12, pady=12)

    def _build_header(self, parent):
        """Build header with app title and user info."""
        if CTK_AVAILABLE:
            header = ctk.CTkFrame(
                parent,
                height=80,
                corner_radius=0,
                fg_color=COLOR_SECONDARY_BG,
            )
        else:
            header = tk.Frame(parent, height=80, bg=COLOR_SECONDARY_BG)
        header.pack(fill="x", padx=0, pady=0)
        header.pack_propagate(False)

        # Left side - App title
        if CTK_AVAILABLE:
            title_label = ctk.CTkLabel(
                header,
                text=APP_NAME,
                font=ctk.CTkFont(size=24, weight="bold"),
                text_color=COLOR_ACCENT,
            )
            title_label.pack(side="left", padx=20, pady=20)

            # Right side - User info
            self.user_info_label = ctk.CTkLabel(
                header,
                text="",
                font=ctk.CTkFont(size=12),
                text_color=COLOR_TEXT_PRIMARY,
            )
        else:
            title_label = tk.Label(
                header,
                text=APP_NAME,
                font=("Georgia", 24, "bold"),
                fg=COLOR_ACCENT,
                bg=COLOR_SECONDARY_BG,
            )
            title_label.pack(side="left", padx=20, pady=20)

            # Right side - User info
            self.user_info_label = tk.Label(
                header,
                text="",
                font=("Sans", 12),
                fg=COLOR_TEXT_PRIMARY,
                bg=COLOR_SECONDARY_BG,
            )
        self.user_info_label.pack(side="right", padx=20, pady=20)

    def _build_sidebar(self, parent):
        """Build sidebar navigation."""
        if CTK_AVAILABLE:
            sidebar = ctk.CTkFrame(
                parent,
                width=SIDEBAR_WIDTH,
                corner_radius=0,
                fg_color=COLOR_SECONDARY_BG,
            )
        else:
            sidebar = tk.Frame(
                parent,
                width=SIDEBAR_WIDTH,
                bg=COLOR_SECONDARY_BG,
            )
        sidebar.pack_propagate(False)

        # Sidebar title
        if CTK_AVAILABLE:
            sidebar_title = ctk.CTkLabel(
                sidebar,
                text="Navigation",
                font=ctk.CTkFont(size=16, weight="bold"),
                text_color=COLOR_ACCENT,
            )
            sidebar_title.pack(pady=(20, 15), padx=15)
        else:
            sidebar_title = tk.Label(
                sidebar,
                text="Navigation",
                font=("Georgia", 16, "bold"),
                fg=COLOR_ACCENT,
                bg=COLOR_SECONDARY_BG,
            )
            sidebar_title.pack(pady=(20, 15), padx=15)

        # Buttons container
        self.sidebar_buttons_frame = sidebar

        # Logout button (at bottom)
        if CTK_AVAILABLE:
            logout_btn = ctk.CTkButton(
                sidebar,
                text="Logout",
                width=SIDEBAR_WIDTH - 30,
                fg_color=COLOR_ERROR,
                hover_color="#a02020",
                command=self._logout,
            )
        else:
            logout_btn = tk.Button(
                sidebar,
                text="Logout",
                width=25,
                bg=COLOR_ERROR,
                fg="white",
                relief="flat",
                command=self._logout,
            )
        logout_btn.pack(side="bottom", pady=20, padx=15)

        return sidebar

    def _build_content_area(self, parent):
        """Build main content area."""
        if CTK_AVAILABLE:
            content = ctk.CTkFrame(
                parent,
                corner_radius=10,
                fg_color="#2a2a3e",
            )
        else:
            content = tk.Frame(parent, bg="#2a2a3e")
        return content

    def _show_login(self):
        """Show login screen."""
        self._clear_content()
        # Render the login UI inside the content area so header/sidebar persist
        LoginScreen(self.content_frame, on_login_success=self._on_login_success)

    def _on_login_success(self, user_dict):
        """Called when login is successful."""
        self.current_user = user_dict
        self._update_header()
        self._build_sidebar_buttons()
        self._show_default_module()

    def _show_default_module(self):
        """Load the default module after successful login.

        Chooses the first accessible module for the user's role, or shows
        a placeholder if none are available.
        """
        if not self.current_user:
            return

        modules = get_accessible_sidebar_modules(self.current_user.get("role", ""))
        if modules:
            # Load the first accessible module
            default_key = modules[0].get("key")
            if default_key:
                self._load_module(default_key)
                return

        # Fallback placeholder
        self._show_placeholder("Home")

    def _update_header(self):
        """Update header with current user info."""
        if self.current_user:
            user_text = f"User: {self.current_user['name']} | Role: {self.current_user['role'].upper()}"
            self.user_info_label.configure(text=user_text)

    def _build_sidebar_buttons(self):
        """Build navigation buttons based on user role."""
        # Clear existing buttons (except title and logout)
        for widget in self.sidebar_buttons_frame.winfo_children():
            if widget != self.user_info_label:
                # Skip title and logout button
                if hasattr(widget, "_is_module_button"):
                    widget.destroy()

        if not self.current_user:
            return

        # Get accessible modules
        modules = get_accessible_sidebar_modules(self.current_user["role"])

        # Create buttons for accessible modules
        for i, module in enumerate(modules):
            btn_text = module["label"]
            module_key = module["key"]

            if CTK_AVAILABLE:
                btn = ctk.CTkButton(
                    self.sidebar_buttons_frame,
                    text=btn_text,
                    width=SIDEBAR_WIDTH - 30,
                    fg_color="#3a3a4e",
                    hover_color="#4a4a5e",
                    command=lambda m=module_key: self._load_module(m),
                )
            else:
                btn = tk.Button(
                    self.sidebar_buttons_frame,
                    text=btn_text,
                    width=25,
                    bg="#3a3a4e",
                    fg=COLOR_TEXT_PRIMARY,
                    relief="flat",
                    command=lambda m=module_key: self._load_module(m),
                )
            btn.pack(pady=8, padx=15, fill="x")
            btn._is_module_button = True

    def _load_module(self, module_name):
        """Load a module into the content area."""
        # Check access
        if not can_access(self.current_user["role"], module_name):
            messagebox.showerror(
                "Unauthorized",
                f"You do not have access to {module_name} module.",
            )
            return

        self._clear_content()
        self.current_module = module_name

        # Load the appropriate module
        if module_name == "pos":
            self._load_pos_module()
        elif module_name == "inventory":
            self._load_inventory_module()
        elif module_name == "reports":
            self._load_reports_module()
        elif module_name == "user_management":
            self._load_user_management_module()
        else:
            self._show_placeholder(module_name)

    def _load_pos_module(self):
        """Load POS module."""
        try:
            from pos.pos_manager import POSManager
            self.pos_manager = POSManager(
                self.content_frame,
                self.current_user,
                on_transaction_complete=self._on_pos_transaction_complete,
            )
        except Exception as e:
            self._show_placeholder("POS")
            from tkinter import messagebox
            messagebox.showerror("Error", f"Failed to load POS module: {e}")

    def _load_inventory_module(self):
        """Load Inventory module."""
        try:
            from inventory.inventory_manager import InventoryManager
            self.inventory_manager = InventoryManager(
                self.content_frame,
                self.current_user,
                on_stock_update=self._on_inventory_update,
            )
        except Exception as e:
            self._show_placeholder("Inventory")
            from tkinter import messagebox
            messagebox.showerror("Error", f"Failed to load Inventory module: {e}")

    def _load_reports_module(self):
        """Load Reports module."""
        try:
            from reports.reports_manager import ReportsManager
            self.reports_manager = ReportsManager(
                self.content_frame,
                self.current_user,
            )
        except Exception as e:
            self._show_placeholder("Reports")
            from tkinter import messagebox
            messagebox.showerror("Error", f"Failed to load Reports module: {e}")

    def _load_user_management_module(self):
        """Load User Management module."""
        if not require_admin(self.current_user["role"]):
            from tkinter import messagebox
            messagebox.showerror(
                "Unauthorized",
                "You do not have permission to manage users.",
            )
            return

        try:
            from auth.user_management_service import UserManagementService
            service = UserManagementService()
            users = service.get_all_users()
            
            # Simple placeholder for now - shows user list
            if CTK_AVAILABLE:
                import customtkinter as ctk
                from tkinter import ttk
                
                frame = ctk.CTkFrame(self.content_frame, fg_color=COLOR_PRIMARY_BG)
                frame.pack(fill="both", expand=True, padx=10, pady=10)
                
                title = ctk.CTkLabel(
                    frame,
                    text="User Management",
                    font=ctk.CTkFont(size=24, weight="bold"),
                    text_color=COLOR_ACCENT,
                )
                title.pack(pady=20)
                
                # Users table
                tree_frame = ctk.CTkFrame(frame, fg_color="transparent")
                tree_frame.pack(fill="both", expand=True, padx=10, pady=10)
                
                cols = ("Username", "Full Name", "Role", "Active")
                tree = ttk.Treeview(tree_frame, columns=cols, show="headings", height=15)
                tree.heading("Username", text="Username")
                tree.heading("Full Name", text="Full Name")
                tree.heading("Role", text="Role")
                tree.heading("Active", text="Active")
                
                tree.column("Username", width=120)
                tree.column("Full Name", width=150)
                tree.column("Role", width=100)
                tree.column("Active", width=60)
                
                for user in users:
                    active_text = "Yes" if user["is_active"] else "No"
                    tree.insert("", "end", values=(
                        user["username"],
                        user["full_name"],
                        user["role"],
                        active_text,
                    ))
                
                tree.pack(fill="both", expand=True)
        except Exception as e:
            self._show_placeholder("User Management")
            from tkinter import messagebox
            messagebox.showerror("Error", f"Failed to load User Management: {e}")

    def _on_pos_transaction_complete(self, transaction_result):
        """Handle completed POS transaction."""
        try:
            # Log with inventory if needed
            if hasattr(self, 'inventory_manager'):
                for item in transaction_result['transaction_data']['items']:
                    self.inventory_manager.service.deduct_stock_for_sale(
                        product_id=item['id'],
                        quantity=item['quantity'],
                    )
            
            # Refresh reports if open
            if hasattr(self, 'reports_manager'):
                self.reports_manager.refresh()
                
        except Exception as e:
            print(f"Error processing transaction: {e}")

    def _on_inventory_update(self, inventory_data):
        """Handle inventory update."""
        try:
            # Refresh reports if open
            if hasattr(self, 'reports_manager'):
                self.reports_manager.refresh()
        except Exception as e:
            print(f"Error updating reports: {e}")

    def _show_placeholder(self, module_name: str):
        """Show a placeholder for a module."""
        if CTK_AVAILABLE:
            placeholder = ctk.CTkFrame(
                self.content_frame,
                corner_radius=10,
                fg_color="#2a2a3e",
            )
        else:
            placeholder = tk.Frame(self.content_frame, bg="#2a2a3e")
        placeholder.pack(fill="both", expand=True, padx=20, pady=20)

        if CTK_AVAILABLE:
            title = ctk.CTkLabel(
                placeholder,
                text=module_name,
                font=ctk.CTkFont(size=24, weight="bold"),
                text_color=COLOR_ACCENT,
            )
            title.pack(pady=20)

            description = ctk.CTkLabel(
                placeholder,
                text=f"{module_name} module placeholder\n(Module implementation pending)",
                font=ctk.CTkFont(size=14),
                text_color=COLOR_TEXT_PRIMARY,
            )
            description.pack(pady=10)
        else:
            title = tk.Label(
                placeholder,
                text=module_name,
                font=("Georgia", 24, "bold"),
                fg=COLOR_ACCENT,
                bg="#2a2a3e",
            )
            title.pack(pady=20)

            description = tk.Label(
                placeholder,
                text=f"{module_name} module placeholder\n(Module implementation pending)",
                font=("Sans", 14),
                fg=COLOR_TEXT_PRIMARY,
                bg="#2a2a3e",
            )
            description.pack(pady=10)

    def _clear_content(self):
        """Clear all widgets from content area."""
        if self.content_frame:
            for widget in self.content_frame.winfo_children():
                widget.destroy()

    def _logout(self):
        """Logout current user."""
        if messagebox.askyesno("Confirm Logout", "Are you sure you want to logout?"):
            self.current_user = None
            self._clear_content()
            self._show_login()

    def show(self):
        """Display the dashboard (run main loop)."""
        self.root.mainloop()
