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

from database import init_database
from gui_app import CafeCraftGUI


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
    # Initialize database
    init_database()

    # Create and configure main window
    root = setup_window()

    # Initialize GUI application
    app = CafeCraftGUI()

    # Start the application event loop
    root.mainloop()


if __name__ == '__main__':
    main()
