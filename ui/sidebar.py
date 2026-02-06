try:
    import customtkinter as ctk
    CTK_AVAILABLE = True
except ImportError:
    import tkinter as tk
    CTK_AVAILABLE = False

from auth.permissions import get_accessible_sidebar_modules
from config.settings import (
    SIDEBAR_WIDTH,
    COLOR_SECONDARY_BG,
    COLOR_ACCENT,
    COLOR_ERROR,
    COLOR_TEXT_PRIMARY,
    SIDEBAR_MODULES,
)
from typing import Callable, Optional, List, Dict

from ui.recipe_view import RecipeView


class Sidebar:
    def __init__(
        self,
        parent,
        user_role: str,
        on_module_selected: Optional[Callable[[str], None]] = None,
        on_logout: Optional[Callable[[], None]] = None,
        db_path: Optional[str] = None,
    ):
        self.parent = parent
        self.user_role = user_role
        self.on_module_selected = on_module_selected
        self.on_logout = on_logout
        self.db_path = db_path
        self.active_module = None
        self.module_buttons = {}

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

        self._build_sidebar()

    def _build_sidebar(self):
        if CTK_AVAILABLE:
            top_section = ctk.CTkFrame(self.frame, fg_color="transparent")
        else:
            top_section = tk.Frame(self.frame, bg=COLOR_SECONDARY_BG)
        top_section.pack(fill="x", pady=(25, 10))

        if CTK_AVAILABLE:
            title = ctk.CTkLabel(
                top_section,
                text="MENU",
                font=ctk.CTkFont(size=14, weight="bold"),
                text_color=COLOR_ACCENT,
            )
        else:
            title = tk.Label(
                top_section,
                text="MENU",
                font=("Georgia", 14, "bold"),
                fg=COLOR_ACCENT,
                bg=COLOR_SECONDARY_BG,
            )
        title.pack(anchor="w", padx=20)

        if CTK_AVAILABLE:
            divider = ctk.CTkFrame(self.frame, height=2, fg_color="#3a3a4e")
        else:
            divider = tk.Frame(self.frame, height=2, bg="#3a3a4e")
        divider.pack(fill="x", padx=20, pady=(10, 15))

        if CTK_AVAILABLE:
            self.modules_frame = ctk.CTkFrame(self.frame, fg_color="transparent")
        else:
            self.modules_frame = tk.Frame(self.frame, bg=COLOR_SECONDARY_BG)
        self.modules_frame.pack(fill="both", expand=True, padx=15)

        self._build_module_buttons()
        self._add_recipe_manager_button()

        if CTK_AVAILABLE:
            bottom_section = ctk.CTkFrame(self.frame, fg_color="transparent")
        else:
            bottom_section = tk.Frame(self.frame, bg=COLOR_SECONDARY_BG)
        bottom_section.pack(fill="x", pady=(10, 20), padx=15)

        if CTK_AVAILABLE:
            bottom_divider = ctk.CTkFrame(bottom_section, height=2, fg_color="#3a3a4e")
        else:
            bottom_divider = tk.Frame(bottom_section, height=2, bg="#3a3a4e")
        bottom_divider.pack(fill="x", pady=(0, 15))

        if CTK_AVAILABLE:
            logout_btn = ctk.CTkButton(
                bottom_section,
                text="Logout",
                width=SIDEBAR_WIDTH - 40,
                fg_color=COLOR_ERROR,
                hover_color="#b02a2a",
                corner_radius=8,
                command=self._on_logout_clicked,
            )
        else:
            logout_btn = tk.Button(
                bottom_section,
                text="Logout",
                width=25,
                bg=COLOR_ERROR,
                fg="white",
                relief="flat",
                command=self._on_logout_clicked,
            )
        logout_btn.pack()

    def _build_module_buttons(self):
        self.module_buttons.clear()
        for widget in self.modules_frame.winfo_children():
            widget.destroy()

        accessible_modules = get_accessible_sidebar_modules(self.user_role)
        for module in accessible_modules:
            self._add_module_button(module)

    def _add_module_button(self, module: Dict):
        module_key = module["key"]
        module_label = module["label"]

        if CTK_AVAILABLE:
            btn = ctk.CTkButton(
                self.modules_frame,
                text=module_label,
                width=SIDEBAR_WIDTH - 40,
                fg_color="#2f2f44",
                hover_color="#40405c",
                corner_radius=8,
                anchor="w",
                command=lambda: self._on_module_clicked(module_key),
            )
        else:
            btn = tk.Button(
                self.modules_frame,
                text=module_label,
                width=24,
                bg="#2f2f44",
                fg=COLOR_TEXT_PRIMARY,
                activebackground="#40405c",
                relief="flat",
                anchor="w",
                command=lambda: self._on_module_clicked(module_key),
            )

        btn.pack(pady=6, fill="x")
        self.module_buttons[module_key] = btn

    def _add_recipe_manager_button(self):
        allowed_roles = {"owner", "admin", "manager", "inventory_staff"}
        if self.user_role not in allowed_roles:
            return

        if CTK_AVAILABLE:
            btn = ctk.CTkButton(
                self.modules_frame,
                text="Recipe Manager",
                width=SIDEBAR_WIDTH - 40,
                fg_color="#2f2f44",
                hover_color="#40405c",
                corner_radius=8,
                anchor="w",
                command=self._open_recipe_manager,
            )
        else:
            btn = tk.Button(
                self.modules_frame,
                text="Recipe Manager",
                width=24,
                bg="#2f2f44",
                fg=COLOR_TEXT_PRIMARY,
                activebackground="#40405c",
                relief="flat",
                anchor="w",
                command=self._open_recipe_manager,
            )

        btn.pack(pady=6, fill="x")

    def _open_recipe_manager(self):
        try:
            RecipeView(self.parent, db_path=self.db_path)
        except Exception as e:
            print(f"Failed to open Recipe Manager: {e}")

    def _on_module_clicked(self, module_name: str):
        self.set_active_module(module_name)
        if self.on_module_selected:
            self.on_module_selected(module_name)

    def _on_logout_clicked(self):
        if self.on_logout:
            self.on_logout()

    def set_active_module(self, module_name: str):
        for btn in self.module_buttons.values():
            if CTK_AVAILABLE:
                btn.configure(fg_color="#2f2f44", text_color=COLOR_TEXT_PRIMARY)
            else:
                btn.configure(bg="#2f2f44", fg=COLOR_TEXT_PRIMARY)

        if module_name in self.module_buttons:
            btn = self.module_buttons[module_name]
            if CTK_AVAILABLE:
                btn.configure(fg_color=COLOR_ACCENT, text_color="#1a1a2e")
            else:
                btn.configure(bg=COLOR_ACCENT, fg="#1a1a2e")

        self.active_module = module_name

    def refresh_modules(self, user_role: str):
        self.user_role = user_role
        self.module_buttons.clear()
        self._build_module_buttons()
        self._add_recipe_manager_button()
        self.active_module = None

    def add_custom_button(
        self,
        button_text: str,
        callback: Callable[[], None],
        color: str = "#3a3a4e",
    ):
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
        self.frame.pack(side="left", fill="y")

    def hide(self):
        self.frame.pack_forget()

    def get_frame(self):
        return self.frame


class SimpleSidebar:
    def __init__(
        self,
        parent,
        modules: Optional[List[Dict]] = None,
        on_module_selected: Optional[Callable[[str], None]] = None,
    ):
        self.parent = parent
        self.modules = modules or SIDEBAR_MODULES
        self.on_module_selected = on_module_selected
        self.active_module = None
        self.module_buttons = {}

        if CTK_AVAILABLE:
            self.frame = ctk.CTkFrame(parent, width=SIDEBAR_WIDTH, fg_color=COLOR_SECONDARY_BG)
        else:
            self.frame = tk.Frame(parent, width=SIDEBAR_WIDTH, bg=COLOR_SECONDARY_BG)
        self.frame.pack_propagate(False)

        self._build()

    def _build(self):
        if CTK_AVAILABLE:
            modules_frame = ctk.CTkFrame(self.frame, fg_color="transparent")
        else:
            modules_frame = tk.Frame(self.frame, bg=COLOR_SECONDARY_BG)

        modules_frame.pack(fill="both", expand=True, padx=15, pady=20)

        for module in self.modules:
            btn = self._create_button(modules_frame, module)
            self.module_buttons[module["key"]] = btn

    def _create_button(self, parent, module: Dict):
        if CTK_AVAILABLE:
            btn = ctk.CTkButton(
                parent,
                text=module["label"],
                width=SIDEBAR_WIDTH - 40,
                fg_color="#2f2f44",
                hover_color="#40405c",
                corner_radius=8,
                anchor="w",
                command=lambda: self._button_clicked(module["key"]),
            )
        else:
            btn = tk.Button(
                parent,
                text=module["label"],
                width=24,
                bg="#2f2f44",
                fg=COLOR_TEXT_PRIMARY,
                relief="flat",
                anchor="w",
                command=lambda: self._button_clicked(module["key"]),
            )

        btn.pack(pady=6, fill="x")
        return btn

    def _button_clicked(self, module_key: str):
        self.set_active(module_key)
        if self.on_module_selected:
            self.on_module_selected(module_key)

    def set_active(self, module_key: str):
        for btn in self.module_buttons.values():
            if CTK_AVAILABLE:
                btn.configure(fg_color="#2f2f44", text_color=COLOR_TEXT_PRIMARY)
            else:
                btn.configure(bg="#2f2f44", fg=COLOR_TEXT_PRIMARY)

        if module_key in self.module_buttons:
            btn = self.module_buttons[module_key]
            if CTK_AVAILABLE:
                btn.configure(fg_color=COLOR_ACCENT, text_color="#1a1a2e")
            else:
                btn.configure(bg=COLOR_ACCENT, fg="#1a1a2e")

        self.active_module = module_key

    def get_frame(self):
        return self.frame
