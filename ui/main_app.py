import tkinter as tk
from tkinter import messagebox, ttk
from ui.dashboard import ActionPanel

class LoginPanel(tk.Frame):
    def __init__(self, master, hostname, on_login, **kwargs):
        super().__init__(master, **kwargs)
        self.on_login = on_login
        
        # Center the login box
        frame = ttk.Frame(self, padding="20 20 20 20", relief="raised")
        frame.place(relx=0.5, rely=0.5, anchor=tk.CENTER)
        
        ttk.Label(frame, text=f"Login to {hostname}", font=('Arial', 12)).pack(pady=10)
        
        ttk.Label(frame, text="Username").pack(anchor='w')
        self.user_ent = ttk.Entry(frame)
        self.user_ent.pack(fill=tk.X, pady=5)
        
        ttk.Label(frame, text="Password").pack(anchor='w')
        self.pass_ent = ttk.Entry(frame, show="*")
        self.pass_ent.pack(fill=tk.X, pady=5)
        
        ttk.Button(frame, text="Login", command=self._do_login).pack(pady=15, fill=tk.X)
        
        # Enter key triggers login
        self.master.bind('<Return>', lambda e: self._do_login())

    def _do_login(self):
        u = self.user_ent.get()
        p = self.pass_ent.get()
        if u and p: self.on_login(None, u, p) # Hostname handled by main app list

class MainApp(tk.Tk):
    def __init__(self, controller):
        super().__init__()
        self.controller = controller
        self.title("BMC API Manager")
        self.geometry("1100x700")
        
        # Default Servers
        self.servers = [
            ("DR - Chandler", "qdlp2bcmapp0002.ess.fiserv.one"),
            ("DR - Omaha", "Sylp2bcmapp0002.ess.fiserv.one"),
            ("PROD - Omaha", "Sylp2bcmapp0001.ess.fiserv.one")
        ]
        
        self.show_login()

    def show_login(self):
        for w in self.winfo_children(): w.destroy()
        # Default to first server for display
        LoginPanel(self, self.servers[0][1], self.on_login).pack(fill=tk.BOTH, expand=True)

    def on_login(self, _, user, password):
        try:
            # Attempt loop logon
            status = self.controller.loop_logon(user, password, self.servers)
            if status == 200:
                self.show_dashboard(user, password)
            elif status == 403:
                messagebox.showerror("Login Failed", "Invalid Credentials")
            else:
                messagebox.showerror("Login Failed", f"Server Error: {status}")
        except Exception as e:
            messagebox.showerror("Error", str(e))

    def show_dashboard(self, user, pwd):
        for w in self.winfo_children(): w.destroy()
        ActionPanel(self, self.controller, user, pwd, self.servers).pack(fill=tk.BOTH, expand=True)

