import tkinter as tk
from tkinter import ttk, messagebox, filedialog
import os
from views.components.dialogs import LoadingDialog

# -----------------------------------------------------------------------------
# Download / Restore Panel
# -----------------------------------------------------------------------------
class DownloadRestorePanel(tk.Frame):
    def __init__(self, master, controller, username, action, **kwargs):
        super().__init__(master, **kwargs)
        self.controller = controller
        self.username = username
        self.action = action  # "Download" or "Restore"
        self.saved_configs = []
        self.selected_config_name = None
        
        self.create_widgets()
        self.refresh_configs()

    def create_widgets(self):
        # Top Bar (Refresh)
        top_frame = ttk.Frame(self)
        top_frame.pack(fill=tk.X, pady=(0, 10))
        ttk.Button(top_frame, text="↻ Refresh", command=self.refresh_configs).pack(side=tk.RIGHT)

        # Treeview
        columns = ("Number", "Name", "Description", "Date", "User")
        self.tree = ttk.Treeview(self, columns=columns, show='headings')
        for col in columns:
            self.tree.heading(col, text=col)
            width = 50 if col == "Number" else 150
            if col == "Description": width = 300
            self.tree.column(col, width=width)
            
        self.tree.pack(fill=tk.BOTH, expand=True)
        self.tree.bind('<<TreeviewSelect>>', self.on_select)
        
        # Action Button
        btn_text = "Restore Config" if self.action == "Restore" else "Download Config"
        self.action_btn = ttk.Button(self, text=btn_text, command=self.process_action)
        self.action_btn.pack(pady=10)

    def refresh_configs(self):
        # Controller Call
        self.saved_configs = self.controller.get_saved_configurations()
        
        # Clear and Refill UI
        for item in self.tree.get_children():
            self.tree.delete(item)
            
        for idx, config in enumerate(self.saved_configs, 1):
            self.tree.insert("", tk.END, values=(
                str(idx), config['name'], config['description'], 
                config['date'], config['user']
            ))

    def on_select(self, event):
        selected = self.tree.selection()
        if selected:
            self.selected_config_name = self.tree.item(selected[0])['values'][1]

    def process_action(self):
        if not self.selected_config_name:
            return

        if self.action == "Download":
            # Default path logic preserved
            default_path = fr"C:\Users\{self.username}\OneDrive - Fiserv Corp\Documents\saved_configuration.zip"
            # Optional: Add file dialog here if you want users to choose
            
            success = self.controller.download_configuration(self.selected_config_name, default_path)
            if success:
                messagebox.showinfo("Success", f"Downloaded to {default_path}")
            else:
                messagebox.showerror("Error", "Download failed.")
                
        elif self.action == "Restore":
            success = self.controller.restore_configuration(self.selected_config_name)
            if success:
                messagebox.showinfo("Success", "Restore initiated successfully.")
            else:
                messagebox.showerror("Error", "Restore failed.")

# -----------------------------------------------------------------------------
# Upload Panel
# -----------------------------------------------------------------------------
class UploadPanel(tk.Frame):
    def __init__(self, master, controller, **kwargs):
        super().__init__(master, **kwargs)
        self.controller = controller
        self.file_path = tk.StringVar()
        self.create_widgets()

    def create_widgets(self):
        frame = ttk.Frame(self)
        frame.pack(pady=20, fill=tk.X)
        
        ttk.Label(frame, text="File:").pack(side=tk.LEFT)
        ttk.Entry(frame, textvariable=self.file_path, width=50).pack(side=tk.LEFT, padx=5)
        ttk.Button(frame, text="Browse", command=self.browse).pack(side=tk.LEFT)
        
        ttk.Button(self, text="Upload", command=self.upload).pack(pady=20)

    def browse(self):
        f = filedialog.askopenfilename(filetypes=[("ZIP files", "*.zip")])
        if f: self.file_path.set(f)

    def upload(self):
        if not self.file_path.get(): return
        success = self.controller.upload_configuration(self.file_path.get())
        if success:
            messagebox.showinfo("Success", "Upload Complete")
        else:
            messagebox.showerror("Error", "Upload Failed")

# -----------------------------------------------------------------------------
# Create Panel
# -----------------------------------------------------------------------------
class CreatePanel(tk.Frame):
    def __init__(self, master, controller, **kwargs):
        super().__init__(master, **kwargs)
        self.controller = controller
        self.name_var = tk.StringVar()
        self.desc_var = tk.StringVar()
        self.create_widgets()

    def create_widgets(self):
        form = ttk.Frame(self)
        form.pack(pady=20)
        
        ttk.Label(form, text="Name:").grid(row=0, column=0, pady=5, sticky='e')
        ttk.Entry(form, textvariable=self.name_var, width=40).grid(row=0, column=1, pady=5)
        
        ttk.Label(form, text="Description:").grid(row=1, column=0, pady=5, sticky='e')
        ttk.Entry(form, textvariable=self.desc_var, width=40).grid(row=1, column=1, pady=5)
        
        ttk.Button(self, text="Create", command=self.submit).pack(pady=20)

    def submit(self):
        if self.controller.create_configuration(self.name_var.get(), self.desc_var.get()):
            messagebox.showinfo("Success", "Configuration Created")
        else:
            messagebox.showerror("Error", "Creation Failed")

# -----------------------------------------------------------------------------
# Update Panel (Async Logic moved to Controller)
# -----------------------------------------------------------------------------
class UpdatePanel(tk.Frame):
    def __init__(self, master, controller, servers, username, password, **kwargs):
        super().__init__(master, **kwargs)
        self.controller = controller
        self.servers = servers
        self.username = username
        self.password = password
        self.source_host = None
        self.target_host = None
        self.create_widgets()

    def create_widgets(self):
        # Two side-by-side lists
        paned = ttk.PanedWindow(self, orient=tk.HORIZONTAL)
        paned.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
        
        # Source
        f1 = ttk.LabelFrame(paned, text="Source (Copy From)")
        self.tree_src = self._build_tree(f1)
        self.tree_src.bind('<<TreeviewSelect>>', lambda e: self._set_host(e, 'source'))
        paned.add(f1, weight=1)
        
        # Target
        f2 = ttk.LabelFrame(paned, text="Target (Update To)")
        self.tree_tgt = self._build_tree(f2)
        self.tree_tgt.bind('<<TreeviewSelect>>', lambda e: self._set_host(e, 'target'))
        paned.add(f2, weight=1)

        ttk.Button(self, text="Run Update", command=self.start_update).pack(pady=20)

    def _build_tree(self, parent):
        cols = ("Env", "Host")
        tree = ttk.Treeview(parent, columns=cols, show='headings')
        tree.heading("Env", text="Environment")
        tree.heading("Host", text="Hostname")
        tree.pack(fill=tk.BOTH, expand=True)
        for env, host in self.servers:
            tree.insert("", tk.END, values=(env, host))
        return tree

    def _set_host(self, event, side):
        tree = event.widget
        sel = tree.selection()
        if sel:
            host = tree.item(sel[0])['values'][1]
            if side == 'source': self.source_host = host
            else: self.target_host = host

    def start_update(self):
        if not self.source_host or not self.target_host:
            messagebox.showwarning("Selection Missing", "Select both Source and Target servers.")
            return

        self.loading = LoadingDialog(self, "Merging Configurations...")
        
        # Controller handles the threading. We just give it a callback.
        self.controller.run_update_async(
            self.source_host, self.target_host, self.username, self.password,
            callback=self.on_update_complete
        )

    def on_update_complete(self, success, message):
        # This runs in the callback, so we must be thread-safe (Tkinter is mostly thread-safe for simple calls, but `after` is safer)
        self.after(0, lambda: self._finish_ui(success, message))

    def _finish_ui(self, success, message):
        if self.loading: self.loading.stop()
        if success:
            messagebox.showinfo("Success", message)
        else:
            messagebox.showerror("Error", message)
