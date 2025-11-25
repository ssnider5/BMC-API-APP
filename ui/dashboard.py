import tkinter as tk
from tkinter import ttk
from ui.simple_panels import DownloadRestorePanel, UploadPanel, CreatePanel, UpdatePanel
from ui.complex_panels import CreateFromExcelPanel, CreateConsoleFromExcelPanel, LogSearchPanel, AutomationPanel
from core.excel_parser import ExcelParser

class LoadingDialog(tk.Toplevel):
    def __init__(self, parent, message="Processing..."):
        super().__init__(parent)
        self.title("Loading")
        self.transient(parent)
        self.grab_set()
        self.overrideredirect(True)
        
        # Center
        x = parent.winfo_rootx() + parent.winfo_width()//2 - 150
        y = parent.winfo_rooty() + parent.winfo_height()//2 - 50
        self.geometry(f'300x100+{x}+{y}')
        
        f = ttk.Frame(self, relief='raised', borderwidth=2)
        f.pack(fill=tk.BOTH, expand=True)
        ttk.Label(f, text=message).pack(pady=10)
        self.pb = ttk.Progressbar(f, mode='indeterminate')
        self.pb.pack(pady=10)
        self.pb.start(10)

class ActionPanel(tk.Frame):
    def __init__(self, master, controller, username, password, servers, **kwargs):
        super().__init__(master, **kwargs)
        self.controller = controller
        self.username = username
        self.password = password
        self.servers = servers
        self.selected_server = self.servers[0]
        
        self.side_panel_buttons = {}
        self.action_buttons = {}
        self.current_mode = "Saved Configurations"
        
        self.create_layout()
        self.switch_mode("Saved Configurations")

    def create_layout(self):
        # 1. Top Banner
        banner = ttk.Frame(self)
        banner.pack(fill=tk.X, padx=5, pady=10)
        
        tk.Label(banner, text="BMC API Tool", font=('Arial', 14, 'bold')).pack(side=tk.LEFT, padx=10)
        ttk.Separator(banner, orient=tk.VERTICAL).pack(side=tk.LEFT, fill=tk.Y, padx=10)
        
        modes = ["Saved Configurations", "CCS Server", "Automation Server"]
        for m in modes:
            btn = tk.Button(banner, text=m, command=lambda x=m: self.switch_mode(x), relief='flat')
            btn.pack(side=tk.LEFT, padx=5)
            self.action_buttons[m] = btn
            
        tk.Frame(self, bg="orange", height=2).pack(fill=tk.X)
        
        # 2. Main Body (Split Left/Right)
        body = ttk.Frame(self)
        body.pack(fill=tk.BOTH, expand=True)
        
        # Sidebar
        self.sidebar = ttk.Frame(body, width=200, style="Side.TFrame")
        self.sidebar.pack(side=tk.LEFT, fill=tk.Y)
        self.sidebar.pack_propagate(False)
        
        style = ttk.Style()
        style.configure("Side.TFrame", background="#444444")
        
        # Content
        self.content = ttk.Frame(body)
        self.content.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        # Header inside content
        self.header_frame = ttk.Frame(self.content)
        self.header_frame.pack(fill=tk.X, pady=(0, 10))
        
        self.title_lbl = ttk.Label(self.header_frame, text="", font=('Arial', 12, 'bold'))
        self.title_lbl.pack(anchor='w')
        
        self.server_lbl = ttk.Label(self.header_frame, text=f"Current: {self.selected_server[0]}")
        self.server_lbl.pack(anchor='w')
        
        # Server Dropdown
        mb = tk.Menubutton(self.header_frame, text="Change Server ▼", relief="flat")
        mb.menu = tk.Menu(mb, tearoff=0)
        mb["menu"] = mb.menu
        for s in self.servers:
            mb.menu.add_command(label=s[0], command=lambda x=s: self.change_server(x))
        mb.pack(anchor='w')
        
        # Dynamic Panel Area
        self.panel_area = ttk.Frame(self.content)
        self.panel_area.pack(fill=tk.BOTH, expand=True)

    def change_server(self, server):
        self.selected_server = server
        self.server_lbl.config(text=f"Current: {server[0]}")
        self.controller.connect(server[1], self.username, self.password)
        for w in self.panel_area.winfo_children():
            if hasattr(w, 'refresh_configs'): w.refresh_configs()

    def switch_mode(self, mode):
        self.current_mode = mode
        
        for m, btn in self.action_buttons.items():
            btn.config(bg="orange" if m == mode else "SystemButtonFace")
            
        for w in self.sidebar.winfo_children(): w.destroy()
        self.side_panel_buttons = {}
        
        options = []
        if mode == "Saved Configurations":
            options = ["Download", "Upload", "Restore", "Create", "Update"]
            self.title_lbl.config(text="Manage Configurations")
        elif mode == "CCS Server":
            options = ["Create from Excel", "Create Console from Excel", "Search Logs"]
            self.title_lbl.config(text="Manage CCS Servers")
        elif mode == "Automation Server":
            options = ["Automation Import"]
            self.title_lbl.config(text="Automation")
            
        for opt in options:
            btn = tk.Button(self.sidebar, text=opt, command=lambda x=opt: self.load_panel(x),
                           bg="#444444", fg="white", relief="flat", anchor="w", padx=10)
            btn.pack(fill=tk.X, pady=1)
            self.side_panel_buttons[opt] = btn
            
        if options: self.load_panel(options[0])

    def load_panel(self, name):
        for n, btn in self.side_panel_buttons.items():
            try: btn.config(bg="#FF8C00" if n == name else "#444444")
            except: pass
            
        for w in self.panel_area.winfo_children(): w.destroy()
        
        p = self.panel_area
        c = self.controller
        
        if name in ["Download", "Restore"]:
            DownloadRestorePanel(p, c, self.username, name).pack(fill=tk.BOTH, expand=True)
        elif name == "Upload":
            UploadPanel(p, c).pack(fill=tk.BOTH, expand=True)
        elif name == "Create":
            CreatePanel(p, c).pack(fill=tk.BOTH, expand=True)
        elif name == "Update":
            UpdatePanel(p, c, self.servers, self.username, self.password).pack(fill=tk.BOTH, expand=True)
        # --- FIXED LINES BELOW: Pass 'c' (controller) instead of 'c.mvcm' ---
        elif name == "Create from Excel":
            CreateFromExcelPanel(p, ExcelParser(), c).pack(fill=tk.BOTH, expand=True)
        elif name == "Create Console from Excel":
            CreateConsoleFromExcelPanel(p, ExcelParser(), c).pack(fill=tk.BOTH, expand=True)
        # --------------------------------------------------------------------
        elif name == "Search Logs":
            LogSearchPanel(p, c).pack(fill=tk.BOTH, expand=True)
        elif name == "Automation Import":
            AutomationPanel(p, c).pack(fill=tk.BOTH, expand=True)


