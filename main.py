"""
CAFÉCRAFT MAIN ENTRY POINT

Responsibilities:
- Create the main CustomTkinter window
- Set window title, size, and theme
- Initialize the database
- Load the GUI application
- Handle app startup only

Does NOT contain business logic.
"""

try:
    import customtkinter as ctk
    CTK_AVAILABLE = True
except ImportError:
    import tkinter as tk
    CTK_AVAILABLE = False

# ✓ CORRECTED: Import init_database from database package (exported in __init__.py)
from database import init_database
# ✓ CORRECTED: Import Dashboard class (not CafeCraftGUI which doesn't exist)
from ui import Dashboard


def setup_window():
    """Configure main window properties and appearance."""
    if CTK_AVAILABLE:
        ctk.set_appearance_mode('Dark')
        ctk.set_default_color_theme('dark-blue')
        root = ctk.CTk()
    else:
        root = tk.Tk()

    root.title('CaféCraft — Coffee Shop Management System')
    root.geometry('1200x800')
    root.minsize(1000, 700)

    return root


def main():
    """Application startup entry point."""
    # ✓ CORRECTED: init_database() now imported from database.schema
    init_database()

    # Create and configure main window
    root = setup_window()

    # ✓ CORRECTED: Dashboard class (was CafeCraftGUI) - pass root window to constructor
    app = Dashboard(root)

    # Start the application event loop
    root.mainloop()


if __name__ == '__main__':
    main()
