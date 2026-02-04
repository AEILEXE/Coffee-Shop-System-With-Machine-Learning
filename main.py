import customtkinter as ctk
from tkinter import messagebox, ttk, BooleanVar
from datetime import datetime
from database import init_database, verify_user, get_connection
from auth import create_user
from pos import POSFrame
from inventory import InventoryFrame
from reports import ReportsFrame

# Set global theme
ctk.set_appearance_mode("Dark")
ctk.set_default_color_theme("blue")

class CoffeeShopApp:
    def __init__(self):
        self.root = ctk.CTk()
        self.root.title("COFFEEE SHOP POS")
        self.root.geometry("1200x800")
        self.current_user = None
        init_database()
        self.create_default_users()
        self.show_login()

    def create_default_users(self):
        conn = get_connection()
        cursor = conn.cursor()
        # Check if users exist
        cursor.execute("SELECT username FROM users WHERE username IN ('owner', 'employee1', 'employee2')")
        existing = [row[0] for row in cursor.fetchall()]
        conn.close()
        
        if 'owner' not in existing:
            create_user('owner', 'OwnerPass123!', 'owner', 'Owner Account')
        if 'employee1' not in existing:
            create_user('employee1', 'Emp1Pass123!', 'employee', 'Employee One')
        if 'employee2' not in existing:
            create_user('employee2', 'Emp2Pass123!', 'employee', 'Employee Two')

    def show_login(self):
        if not self.root or not self.root.winfo_exists():
            return
        self.clear_window()

        # Outer container for centering login frame
        container = ctk.CTkFrame(self.root)
        container.pack(expand=True, fill="both")

        # Login Frame
        frame = ctk.CTkFrame(container, corner_radius=10, width=400, height=400)
        frame.pack_propagate(False)  # Fix ValueError by preventing auto-resize
        frame.place(relx=0.5, rely=0.5, anchor="center")

        ctk.CTkLabel(frame, text="COFFEEE SHOP", font=("Georgia", 32, "bold"),
                     text_color="#d4a574").pack(pady=20)

        ctk.CTkLabel(frame, text=datetime.now().strftime("%Y-%m-%d %H:%M:%S")).pack(pady=10)

        ctk.CTkLabel(frame, text="Username").pack(pady=(10, 0))
        self.username_entry = ctk.CTkEntry(frame, width=250)
        self.username_entry.pack(pady=5)

        ctk.CTkLabel(frame, text="Password").pack(pady=(10, 0))
        # Password field with eye icon
        pwd_frame = ctk.CTkFrame(frame, fg_color="transparent")
        pwd_frame.pack(pady=5)
        self.password_entry = ctk.CTkEntry(pwd_frame, width=220, show="*")
        self.password_entry.pack(side="left")
        self.show_pwd_var = BooleanVar(value=False)
        def _toggle_pwd():
            self.show_pwd_var.set(not self.show_pwd_var.get())
            self.password_entry.configure(show='' if self.show_pwd_var.get() else '*')
        eye_btn = ctk.CTkButton(pwd_frame, text="👁", width=30, command=_toggle_pwd)
        eye_btn.pack(side="left")

        # Bind Enter key to login
        self.password_entry.bind('<Return>', lambda e: self.login())
        self.username_entry.bind('<Return>', lambda e: self.login())

        ctk.CTkButton(frame, text="Sign In", width=200, fg_color="#d4a574", text_color="white",
                      command=self.login).pack(pady=20)

    def login(self):
        username = self.username_entry.get()
        password = self.password_entry.get()
        user = verify_user(username, password)
        if user:
            self.current_user = {
                "id": user[0], 
                "name": user[1], 
                "role": user[2],
                "can_pos": user[3],
                "can_inventory": user[4],
                "can_reports": user[5],
                "can_user_management": user[6]
            }
            self.show_main_app()
        else:
            messagebox.showerror("Error", "Invalid credentials")

    def show_main_app(self):
        if not self.root or not self.root.winfo_exists():
            return
        self.clear_window()

        # Sidebar
        sidebar = ctk.CTkFrame(self.root, width=200, corner_radius=0, fg_color="#16213e")
        sidebar.pack(side="left", fill="y")
        sidebar.pack_propagate(False)

        ctk.CTkLabel(sidebar, text="COFFEEE SHOP", font=("Georgia", 20, "bold"),
                     text_color="#d4a574").pack(pady=20)
        ctk.CTkLabel(sidebar, text=f"Welcome, {self.current_user['name']}",
                     wraplength=180, text_color="white").pack(pady=10)

        # Permission-based module access
        allowed = []
        if self.current_user.get("can_pos"):
            allowed.append("pos")
        if self.current_user.get("can_inventory"):
            allowed.append("inventory")
        if self.current_user.get("can_reports"):
            allowed.append("reports")

        nav_map = {
            'pos': ("POS", lambda: self.show_module("pos")),
            'inventory': ("Inventory", lambda: self.show_module("inventory")),
            'reports': ("Reports", lambda: self.show_module("reports"))
        }

        for key in ['pos', 'inventory', 'reports']:
            text, command = nav_map[key]
            if key in allowed:
                ctk.CTkButton(sidebar, text=text, width=180, anchor="w",
                               fg_color="#1a1a2e", hover_color="#343a40",
                               command=command).pack(pady=5, padx=10)
            else:
                ctk.CTkButton(sidebar, text=text + " (locked)", width=180, anchor="w",
                               fg_color="#343a40", hover_color="#343a40",
                               state="disabled").pack(pady=5, padx=10)

        # Add User Management button if allowed
        if self.current_user.get("can_user_management"):
            ctk.CTkButton(sidebar, text="User Management", width=180, anchor="w",
                           fg_color="#1a1a2e", hover_color="#343a40",
                           command=self.open_user_management).pack(pady=5, padx=10)

        ctk.CTkButton(sidebar, text="Logout", width=180, fg_color="#dc3545",
                      hover_color="#c82333", command=self.show_login).pack(side="bottom", pady=20, padx=10)

        # Main content area
        self.content_frame = ctk.CTkFrame(self.root, fg_color="#1a1a2e")
        self.content_frame.pack(side="right", fill="both", expand=True)

        # Show default module
        if 'pos' in allowed:
            self.show_module("pos")
        elif allowed:
            self.show_module(allowed[0])

    def show_module(self, module_name):
        for widget in self.content_frame.winfo_children():
            widget.destroy()

        # Check access
        permission_map = {
            "pos": "can_pos",
            "inventory": "can_inventory",
            "reports": "can_reports"
        }
        required_perm = permission_map.get(module_name)
        if not required_perm or not self.current_user.get(required_perm):
            messagebox.showerror("Unauthorized", "You are not authorized to access this module")
            return

        # Load module
        if module_name == "pos":
            POSFrame(self.content_frame, self.current_user)
        elif module_name == "inventory":
            InventoryFrame(self.content_frame, self.current_user)
        elif module_name == "reports":
            ReportsFrame(self.content_frame)

    def load_users(self, dialog):
        for item in self.user_tree.get_children():
            self.user_tree.delete(item)
        
        conn = get_connection()
        cur = conn.cursor()
        cur.execute("SELECT id, username, full_name, role, created_at FROM users ORDER BY id")
        for row in cur.fetchall():
            self.user_tree.insert("", "end", values=row)
        conn.close()

    def open_user_management(self):
        # Open user management dialog for admins
        dialog = ctk.CTkToplevel(self.root)
        dialog.title("User Management")
        dialog.geometry("800x600")
        dialog.transient(self.root)
        dialog.grab_set()

        # Title
        ctk.CTkLabel(dialog, text="User Management", font=ctk.CTkFont(size=20, weight="bold")).pack(pady=10)

        # User list frame
        list_frame = ctk.CTkFrame(dialog)
        list_frame.pack(fill="both", expand=True, padx=20, pady=10)

        # Treeview for users
        columns = ("ID", "Username", "Full Name", "Role", "Created")
        self.user_tree = ttk.Treeview(list_frame, columns=columns, show="headings", height=10)
        for col in columns:
            self.user_tree.heading(col, text=col)
            self.user_tree.column(col, width=120)
        self.user_tree.pack(fill="both", expand=True, pady=10)

        # Load users
        self.load_users(dialog)

        # Buttons
        btn_frame = ctk.CTkFrame(dialog, fg_color="transparent")
        btn_frame.pack(fill="x", padx=20, pady=10)

        ctk.CTkButton(btn_frame, text="Add User", fg_color="#28a745", command=lambda: self.add_user(dialog)).pack(side="left", padx=5)
        ctk.CTkButton(btn_frame, text="Edit User", command=lambda: self.edit_user(dialog)).pack(side="left", padx=5)
        ctk.CTkButton(btn_frame, text="Delete User", fg_color="#dc3545", command=lambda: self.delete_user(dialog)).pack(side="left", padx=5)
        ctk.CTkButton(btn_frame, text="Refresh", command=lambda: self.load_users(dialog)).pack(side="right", padx=5)

    def add_user(self, parent_dialog):
        # Add user dialog
        add_win = ctk.CTkToplevel(parent_dialog)
        add_win.title("Add User")
        add_win.geometry("400x500")
        add_win.transient(parent_dialog)
        add_win.grab_set()

        ctk.CTkLabel(add_win, text="Add New User", font=ctk.CTkFont(size=16, weight="bold")).pack(pady=10)

        # Form
        form_frame = ctk.CTkFrame(add_win)
        form_frame.pack(fill="both", expand=True, padx=20, pady=10)

        ctk.CTkLabel(form_frame, text="Username:").pack(anchor="w")
        username_entry = ctk.CTkEntry(form_frame)
        username_entry.pack(fill="x", pady=5)

        ctk.CTkLabel(form_frame, text="Full Name:").pack(anchor="w")
        fullname_entry = ctk.CTkEntry(form_frame)
        fullname_entry.pack(fill="x", pady=5)

        ctk.CTkLabel(form_frame, text="Role:").pack(anchor="w")
        role_combo = ctk.CTkComboBox(form_frame, values=['owner', 'admin', 'manager', 'cashier', 'inventory_staff', 'employee'])
        role_combo.set('cashier')
        role_combo.pack(fill="x", pady=5)

        ctk.CTkLabel(form_frame, text="Password:").pack(anchor="w")
        pwd_entry = ctk.CTkEntry(form_frame, show="*")
        pwd_entry.pack(fill="x", pady=5)

        # Permissions
        ctk.CTkLabel(form_frame, text="Permissions:").pack(anchor="w", pady=(10,5))
        perm_frame = ctk.CTkFrame(form_frame, fg_color="transparent")
        perm_frame.pack(fill="x", pady=5)

        can_pos_var = ctk.BooleanVar(value=True)
        ctk.CTkCheckBox(perm_frame, text="POS Access", variable=can_pos_var).pack(anchor="w")

        can_inventory_var = ctk.BooleanVar(value=False)
        ctk.CTkCheckBox(perm_frame, text="Inventory Access", variable=can_inventory_var).pack(anchor="w")

        can_reports_var = ctk.BooleanVar(value=False)
        ctk.CTkCheckBox(perm_frame, text="Reports Access", variable=can_reports_var).pack(anchor="w")

        can_user_mgmt_var = ctk.BooleanVar(value=False)
        ctk.CTkCheckBox(perm_frame, text="User Management", variable=can_user_mgmt_var).pack(anchor="w")

        # Save button
        def save():
            try:
                from auth import create_user
                permissions = {
                    'can_pos': 1 if can_pos_var.get() else 0,
                    'can_inventory': 1 if can_inventory_var.get() else 0,
                    'can_reports': 1 if can_reports_var.get() else 0,
                    'can_user_management': 1 if can_user_mgmt_var.get() else 0
                }
                create_user(username_entry.get(), pwd_entry.get(), role_combo.get(), fullname_entry.get(), permissions)
                messagebox.showinfo("Success", "User created")
                add_win.destroy()
                self.load_users(parent_dialog)
            except Exception as e:
                messagebox.showerror("Error", str(e))

        ctk.CTkButton(form_frame, text="Create User", command=save).pack(pady=10)

    def edit_user(self, parent_dialog):
        sel = self.user_tree.selection()
        if not sel:
            messagebox.showwarning("Select User", "Please select a user to edit")
            return
        
        user_id = self.user_tree.item(sel[0])["values"][0]
        
        # Prevent editing self
        if user_id == self.current_user['id']:
            messagebox.showwarning("Cannot Edit", "You cannot edit your own account")
            return
        conn = get_connection()
        cur = conn.cursor()
        cur.execute("SELECT username, full_name, role, can_pos, can_inventory, can_reports, can_user_management FROM users WHERE id=?", (user_id,))
        row = cur.fetchone()
        conn.close()
        if not row:
            return
        
        # Edit dialog
        edit_win = ctk.CTkToplevel(parent_dialog)
        edit_win.title("Edit User")
        edit_win.geometry("400x400")
        edit_win.transient(parent_dialog)
        edit_win.grab_set()

        ctk.CTkLabel(edit_win, text="Edit User", font=ctk.CTkFont(size=16, weight="bold")).pack(pady=10)

        # Form
        form_frame = ctk.CTkFrame(edit_win)
        form_frame.pack(fill="both", expand=True, padx=20, pady=10)

        ctk.CTkLabel(form_frame, text="Username:").pack(anchor="w")
        username_entry = ctk.CTkEntry(form_frame)
        username_entry.insert(0, row[0])
        username_entry.pack(fill="x", pady=5)

        ctk.CTkLabel(form_frame, text="Full Name:").pack(anchor="w")
        fullname_entry = ctk.CTkEntry(form_frame)
        fullname_entry.insert(0, row[1])
        fullname_entry.pack(fill="x", pady=5)

        ctk.CTkLabel(form_frame, text="Role:").pack(anchor="w")
        role_combo = ctk.CTkComboBox(form_frame, values=['owner', 'admin', 'manager', 'cashier', 'inventory_staff', 'employee'])
        role_combo.set(row[2])
        role_combo.pack(fill="x", pady=5)

        # Password change
        ctk.CTkLabel(form_frame, text="New Password (leave empty to keep current):").pack(anchor="w")
        pwd_entry = ctk.CTkEntry(form_frame, show="*")
        pwd_entry.pack(fill="x", pady=5)

        show_pwd = BooleanVar()
        ctk.CTkCheckBox(form_frame, text="Show password", variable=show_pwd, command=lambda: pwd_entry.configure(show="" if show_pwd.get() else "*")).pack(anchor="w")

        # Permissions
        ctk.CTkLabel(form_frame, text="Permissions:").pack(anchor="w", pady=(10,5))
        perm_frame = ctk.CTkFrame(form_frame, fg_color="transparent")
        perm_frame.pack(fill="x", pady=5)

        can_pos_var = BooleanVar(value=bool(row[3]))
        ctk.CTkCheckBox(perm_frame, text="POS Access", variable=can_pos_var).pack(anchor="w")

        can_inventory_var = BooleanVar(value=bool(row[4]))
        ctk.CTkCheckBox(perm_frame, text="Inventory Access", variable=can_inventory_var).pack(anchor="w")

        can_reports_var = BooleanVar(value=bool(row[5]))
        ctk.CTkCheckBox(perm_frame, text="Reports Access", variable=can_reports_var).pack(anchor="w")

        can_user_mgmt_var = BooleanVar(value=bool(row[6]))
        ctk.CTkCheckBox(perm_frame, text="User Management", variable=can_user_mgmt_var).pack(anchor="w")

        # Save button
        def save():
            try:
                from auth import update_user
                data = {
                    'username': username_entry.get(),
                    'full_name': fullname_entry.get(),
                    'role': role_combo.get(),
                    'can_pos': 1 if can_pos_var.get() else 0,
                    'can_inventory': 1 if can_inventory_var.get() else 0,
                    'can_reports': 1 if can_reports_var.get() else 0,
                    'can_user_management': 1 if can_user_mgmt_var.get() else 0
                }
                pwd = pwd_entry.get()
                if pwd:
                    data['password'] = pwd
                update_user(user_id, data)
                messagebox.showinfo("Success", "User updated")
                edit_win.destroy()
                self.load_users(parent_dialog)
            except Exception as e:
                messagebox.showerror("Error", str(e))

        ctk.CTkButton(form_frame, text="Save", command=save).pack(pady=10)

    def delete_user(self, parent_dialog):
        sel = self.user_tree.selection()
        if not sel:
            messagebox.showwarning("Select User", "Please select a user to delete")
            return
        
        user_id = self.user_tree.item(sel[0])["values"][0]
        username = self.user_tree.item(sel[0])["values"][1]
        
        # Prevent deleting self
        if user_id == self.current_user['id']:
            messagebox.showwarning("Cannot Delete", "You cannot delete your own account")
            return
        
        if not messagebox.askyesno("Confirm Delete", f"Delete user '{username}'? This cannot be undone."):
            return
        
        try:
            from auth import delete_user
            delete_user(user_id)
            messagebox.showinfo("Deleted", f"User '{username}' deleted")
            self.load_users(parent_dialog)
        except Exception as e:
            messagebox.showerror("Error", str(e))

    def clear_window(self):
        if self.root and self.root.winfo_exists():
            for widget in self.root.winfo_children():
                widget.destroy()

    def run(self):
        self.root.mainloop()


if __name__ == "__main__":
    app = CoffeeShopApp()
    app.run()
