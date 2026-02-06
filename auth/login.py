"""
CAFÉCRAFT LOGIN SCREEN

Responsibilities:
- CustomTkinter login GUI
- Username and password input fields
- Show/hide password toggle
- Enter key submits login
- Validate credentials against database
- On success, invoke callback to show dashboard
- On failure, display error messagebox

Uses database.verify_user() for authentication.
"""

try:
    import customtkinter as ctk
    CTK_AVAILABLE = True
except ImportError:
    import tkinter as tk
    from tkinter import messagebox
    CTK_AVAILABLE = False

if CTK_AVAILABLE:
    from tkinter import messagebox
from datetime import datetime
from database import verify_user
from config.settings import (
    APP_NAME,
    COLOR_PRIMARY_BG,
    COLOR_ACCENT,
    COLOR_TEXT_PRIMARY,
    FONT_TITLE,
    FONT_NORMAL,
)


class LoginScreen:
    """CustomTkinter login screen for CAFÉCRAFT."""

    def __init__(self, parent_window, on_login_success=None):
        """
        Initialize login screen.

        Args:
            parent_window: The main window (CustomTkinter root).
            on_login_success: Callback function(user_dict) on successful login.
        """
        self.root = parent_window
        self.on_login_success = on_login_success

        # Clear window
        self._clear_window()

        # Build login UI
        self._build_ui()

    def _clear_window(self):
        """Clear all widgets from window."""
        for widget in self.root.winfo_children():
            widget.destroy()

    def _build_ui(self):
        """Build the login screen UI."""
        # Outer container for centering
        if CTK_AVAILABLE:
            container = ctk.CTkFrame(self.root, fg_color=COLOR_PRIMARY_BG)
        else:
            container = tk.Frame(self.root, bg=COLOR_PRIMARY_BG)
        container.pack(expand=True, fill="both")

        # Login frame (centered)
        if CTK_AVAILABLE:
            login_frame = ctk.CTkFrame(
                container,
                corner_radius=15,
                width=420,
                height=480,
                fg_color="#2a2a3e",
            )
            login_frame.pack_propagate(False)
            login_frame.place(relx=0.5, rely=0.5, anchor="center")
        else:
            login_frame = tk.Frame(
                container,
                width=420,
                height=480,
                bg="#2a2a3e",
            )
            login_frame.pack_propagate(False)
            login_frame.place(relx=0.5, rely=0.5, anchor="center")

        # Title
        if CTK_AVAILABLE:
            title_label = ctk.CTkLabel(
                login_frame,
                text=APP_NAME,
                font=ctk.CTkFont(size=32, weight="bold"),
                text_color=COLOR_ACCENT,
            )
        else:
            title_label = tk.Label(
                login_frame,
                text=APP_NAME,
                font=("Georgia", 32, "bold"),
                fg=COLOR_ACCENT,
                bg="#2a2a3e",
            )
        title_label.pack(pady=(30, 10))

        # Subtitle with current date/time
        current_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        if CTK_AVAILABLE:
            subtitle_label = ctk.CTkLabel(
                login_frame,
                text=current_time,
                font=ctk.CTkFont(size=12),
                text_color="#cccccc",
            )
        else:
            subtitle_label = tk.Label(
                login_frame,
                text=current_time,
                font=("Sans", 12),
                fg="#cccccc",
                bg="#2a2a3e",
            )
        subtitle_label.pack(pady=(0, 20))

        # Username label and entry
        if CTK_AVAILABLE:
            username_lbl = ctk.CTkLabel(
                login_frame,
                text="Username",
                font=ctk.CTkFont(size=14),
                text_color=COLOR_TEXT_PRIMARY,
            )
        else:
            username_lbl = tk.Label(
                login_frame,
                text="Username",
                font=("Sans", 14),
                fg=COLOR_TEXT_PRIMARY,
                bg="#2a2a3e",
            )
        username_lbl.pack(anchor="w", padx=40, pady=(15, 5))

        if CTK_AVAILABLE:
            self.username_entry = ctk.CTkEntry(
                login_frame,
                width=280,
                placeholder_text="Enter username",
            )
        else:
            self.username_entry = tk.Entry(
                login_frame,
                width=35,
                font=("Sans", 12),
            )
        self.username_entry.pack(padx=40, pady=(0, 15))
        self.username_entry.bind("<Return>", lambda e: self._attempt_login())

        # Password label
        if CTK_AVAILABLE:
            password_lbl = ctk.CTkLabel(
                login_frame,
                text="Password",
                font=ctk.CTkFont(size=14),
                text_color=COLOR_TEXT_PRIMARY,
            )
        else:
            password_lbl = tk.Label(
                login_frame,
                text="Password",
                font=("Sans", 14),
                fg=COLOR_TEXT_PRIMARY,
                bg="#2a2a3e",
            )
        password_lbl.pack(anchor="w", padx=40, pady=(15, 5))

        # Password entry with toggle button inside frame
        if CTK_AVAILABLE:
            pwd_container = ctk.CTkFrame(login_frame, fg_color="transparent")
        else:
            pwd_container = tk.Frame(login_frame, bg="#2a2a3e")
        pwd_container.pack(padx=40, pady=(0, 20))

        if CTK_AVAILABLE:
            self.password_entry = ctk.CTkEntry(
                pwd_container,
                width=240,
                placeholder_text="Enter password",
                show="*",
            )
            self.password_entry.pack(side="left", padx=(0, 8))

            self.show_password_var = ctk.BooleanVar(value=False)
            toggle_btn = ctk.CTkButton(
                pwd_container,
                text="Show",
                width=60,
                height=40,
                command=self._toggle_password_visibility,
            )
            toggle_btn.pack(side="left")
        else:
            self.password_entry = tk.Entry(
                pwd_container,
                width=28,
                font=("Sans", 12),
                show="*",
            )
            self.password_entry.pack(side="left", padx=(0, 8))

            self.show_password_var = tk.BooleanVar(value=False)
            toggle_btn = tk.Button(
                pwd_container,
                text="Show",
                width=8,
                height=1,
                command=self._toggle_password_visibility,
                bg="#343a40",
                fg="white",
                relief="flat",
            )
            toggle_btn.pack(side="left")

        self.password_entry.bind("<Return>", lambda e: self._attempt_login())

        # Login button
        if CTK_AVAILABLE:
            login_btn = ctk.CTkButton(
                login_frame,
                text="Sign In",
                width=280,
                height=45,
                fg_color=COLOR_ACCENT,
                text_color="#1a1a2e",
                font=ctk.CTkFont(size=16, weight="bold"),
                command=self._attempt_login,
            )
        else:
            login_btn = tk.Button(
                login_frame,
                text="Sign In",
                width=40,
                height=2,
                bg=COLOR_ACCENT,
                fg="#1a1a2e",
                font=("Sans", 16, "bold"),
                relief="flat",
                command=self._attempt_login,
            )
        login_btn.pack(pady=20)

        # Status label (for error messages)
        if CTK_AVAILABLE:
            self.status_label = ctk.CTkLabel(
                login_frame,
                text="",
                font=ctk.CTkFont(size=11),
                text_color="#ff6b6b",
            )
        else:
            self.status_label = tk.Label(
                login_frame,
                text="",
                font=("Sans", 11),
                fg="#ff6b6b",
                bg="#2a2a3e",
            )
        self.status_label.pack(pady=(10, 20))

        # Focus on username entry
        self.username_entry.focus()

    def _toggle_password_visibility(self):
        """Toggle password visibility."""
        if self.show_password_var.get():
            self.password_entry.configure(show="*")
            self.show_password_var.set(False)
        else:
            self.password_entry.configure(show="")
            self.show_password_var.set(True)

    def _attempt_login(self):
        """Validate credentials and attempt login."""
        username = self.username_entry.get().strip()
        password = self.password_entry.get()

        # Validate inputs
        if not username:
            self._show_error("Please enter your username")
            self.username_entry.focus()
            return

        if not password:
            self._show_error("Please enter your password")
            self.password_entry.focus()
            return

        # Verify credentials
        user = verify_user(username, password)

        if user:
            # Login successful
            user_dict = {
                "id": user[0],
                "name": user[1],
                "role": user[2],
                "can_pos": user[3],
                "can_inventory": user[4],
                "can_reports": user[5],
                "can_user_management": user[6],
            }

            # Invoke callback
            if self.on_login_success:
                self.on_login_success(user_dict)
        else:
            # Login failed
            self._show_error("Invalid username or password")
            self.password_entry.delete(0, "end")
            self.username_entry.focus()

    def _show_error(self, message: str):
        """Display error message."""
        self.status_label.configure(text=message)
        messagebox.showerror("Login Failed", message)
