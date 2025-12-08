import tkinter as tk
from tkinter import ttk
from views.panels.config_panels import (
    DownloadRestorePanel, UploadPanel, CreatePanel, UpdatePanel
)
from views.panels.excel_panels import (
    CreateFromExcelPanel, CreateConsoleFromExcelPanel
)

class ActionPanel(tk.Frame):
    def __init__(self, master, config_ctrl, server_ctrl, excel_service, user, pwd, servers, **kwargs):
        super().__init__(master, **kwargs)
        # Dependencies
        self.config_ctrl = config_ctrl
        self.server_ctrl = server_ctrl
        self.excel_service = excel_service
        self.user = user
        self.pwd = pwd
        self.servers = servers
        self.current_server = servers[0] # (Env, Host)
        
        self.current_mode = "Saved Configurations" 
        self.create_layout()

    def create_layout(self):
        # 1. Top Banner
        banner = ttk.Frame(self)
        banner.pack(fill=tk.X, padx=5, pady=5)
        
        tk.Label(banner, text="BMC API Tool", font=('Arial', 14, 'bold')).pack(side=tk.LEFT, padx=10)
        ttk.Separator(banner, orient=tk.VERTICAL).pack(side=tk.LEFT, fill=tk.Y, padx=10)
        
        # Mode Switch Buttons
        self.btn_configs = tk.Button(banner, text="Saved Configurations", command=lambda: self.set_mode("Saved Configurations"))
        self.btn_configs.pack(side=tk.LEFT, padx=5)
        
        self.btn_servers = tk.Button(banner, text="CCS Server", command=lambda: self.set_mode("CCS Server"))
        self.btn_servers.pack(side=tk.LEFT, padx=5)

        tk.Frame(self, bg="orange", height=2).pack(fill=tk.X)

        # 2. Main Container (Sidebar + Content)
        container = ttk.Frame(self)
        container.pack(fill=tk.BOTH, expand=True)
        
        # Sidebar
        self.sidebar = tk.Frame(container, width=200, bg="#444444")
        self.sidebar.pack(side=tk.LEFT, fill=tk.Y)
        self.sidebar.pack_propagate(False)

        # Content Area
        self.content_area = ttk.Frame(container)
        self.content_area.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        # Server Selector (In content area)
        self.top_content_frame = ttk.Frame(self.content_area)
        self.top_content_frame.pack(fill=tk.X, pady=(0, 10))
        
        self.lbl_server = ttk.Label(self.top_content_frame, text=f"Connected: {self.current_server[0]}")
        self.lbl_server.pack(side=tk.LEFT)
        
        mb = ttk.Menubutton(self.top_content_frame, text="Change Server")
        menu = tk.Menu(mb, tearoff=0)
        for s in self.servers:
            menu.add_command(label=s[0], command=lambda x=s: self.change_server(x))
        mb.config(menu=menu)
        mb.pack(side=tk.LEFT, padx=10)

        # Dynamic Panel Container
        self.dynamic_frame = ttk.Frame(self.content_area)
        self.dynamic_frame.pack(fill=tk.BOTH, expand=True)

        # Initial Load
        self.set_mode("Saved Configurations")

    def change_server(self, server_tuple):
        self.current_server = server_tuple
        self.lbl_server.config(text=f"Connected: {server_tuple[0]}")
        # Notify controller to switch connection
        self.config_ctrl.connect_to_new_host(server_tuple[1], self.user, self.pwd) 
        # Refresh current panel
        self.load_sub_panel(self.current_sub_action)

    def set_mode(self, mode):
        self.current_mode = mode
        # Style buttons
        self.btn_configs.config(bg="orange" if mode == "Saved Configurations" else "SystemButtonFace")
        self.btn_servers.config(bg="orange" if mode == "CCS Server" else "SystemButtonFace")
        
        # Clear Sidebar
        for w in self.sidebar.winfo_children(): w.destroy()
        
        # Populate Sidebar
        options = []
        if mode == "Saved Configurations":
            options = ["Download", "Upload", "Restore", "Create", "Update"]
        else:
            options = ["Create from Excel", "Create Console from Excel"]
            
        for opt in options:
            btn = tk.Button(self.sidebar, text=opt, command=lambda x=opt: self.load_sub_panel(x),
                            bg="#444444", fg="white", relief="flat", anchor="w", padx=10)
            btn.pack(fill=tk.X, pady=1)

        # Load first option by default
        if options: self.load_sub_panel(options[0])

    def load_sub_panel(self, action):
        self.current_sub_action = action
        # Highlight sidebar button
        for btn in self.sidebar.winfo_children():
            if btn['text'] == action: btn.config(bg="orange")
            else: btn.config(bg="#444444")

        # Clear Content
        for w in self.dynamic_frame.winfo_children(): w.destroy()
        
        # Switch Logic
        p = None
        if action in ["Download", "Restore"]:
            p = DownloadRestorePanel(self.dynamic_frame, self.config_ctrl, self.user, action)
        elif action == "Upload":
            p = UploadPanel(self.dynamic_frame, self.config_ctrl)
        elif action == "Create":
            p = CreatePanel(self.dynamic_frame, self.config_ctrl)
        elif action == "Update":
            p = UpdatePanel(self.dynamic_frame, self.config_ctrl, self.servers, self.user, self.pwd)
        elif action == "Create from Excel":
            p = CreateFromExcelPanel(self.dynamic_frame, self.server_ctrl, self.excel_service)
        elif action == "Create Console from Excel":
            p = CreateConsoleFromExcelPanel(self.dynamic_frame, self.server_ctrl, self.excel_service)
            
        if p: p.pack(fill=tk.BOTH, expand=True)
