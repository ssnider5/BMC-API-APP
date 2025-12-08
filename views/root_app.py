import tkinter as tk
from views.panels.login_panel import LoginPanel
from views.panels.action_panel import ActionPanel
from tkinter import messagebox

class RootApp(tk.Tk):
    def __init__(self, mvcm_service, server_ctrl, config_ctrl, excel_service):
        super().__init__()
        self.title("BMC Server Tool")
        self.geometry("1100x700")
        
        # Inject Dependencies
        self.mvcm = mvcm_service
        self.server_ctrl = server_ctrl
        self.config_ctrl = config_ctrl
        self.excel_service = excel_service
        
        self.servers = [
            ("DR - Chandler", "qdlp2bcmapp0002.ess.fiserv.one"),
            ("DR - Omaha", "Sylp2bcmapp0002.ess.fiserv.one")
        ]
        
        # Start at Login
        self.show_login()

    def show_login(self):
        for w in self.winfo_children(): w.destroy()
        # Default to first server
        LoginPanel(self, self.servers[0][1], self.on_login_attempt).pack(fill=tk.BOTH, expand=True)

    def on_login_attempt(self, hostname, user, pwd):
        # We can use the service directly here or a specific LoginController
        # For simplicity, we use the mvcm service directly as per your original design
        try:
            self.mvcm.connect(hostname, user, pwd)
            # If connect succeeds, we store creds and move on
            self.user = user
            self.pwd = pwd
            self.show_main_app()
        except Exception as e:
            messagebox.showerror("Login Failed", str(e))

    def show_main_app(self):
        for w in self.winfo_children(): w.destroy()
        
        ActionPanel(
            self, 
            self.config_ctrl, 
            self.server_ctrl, 
            self.excel_service,
            self.user, 
            self.pwd, 
            self.servers
        ).pack(fill=tk.BOTH, expand=True)
