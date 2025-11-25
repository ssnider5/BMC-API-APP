import tkinter as tk
from tkinter import ttk, filedialog, messagebox
import threading
import os

# -------------------------------
# Download/Restore Panel
# -------------------------------
class DownloadRestorePanel(tk.Frame):
    def __init__(self, master, controller, username, action, **kwargs):
        super().__init__(master, **kwargs)
        self.action = action
        self.saved_configs = None
        self.username = username
        self.controller = controller
        self.selected_config_name = None
        self.create_widgets()
        self.refresh_configs()

    def create_widgets(self):
        container = ttk.Frame(self)
        container.pack(fill=tk.BOTH, expand=True)
        
        refresh_frame = ttk.Frame(container)
        refresh_frame.pack(fill=tk.X, pady=(0, 10))
        refresh_button = ttk.Button(refresh_frame, text="↻ Refresh", command=self.refresh_configs)
        refresh_button.pack(side=tk.RIGHT, padx=5)
        
        table_frame = ttk.Frame(container)
        table_frame.pack(fill=tk.BOTH, expand=True, pady=(0, 10))
        
        self.config_tree = ttk.Treeview(table_frame, 
                                        columns=("Number", "Name", "Description", "Date", "User"), 
                                        show='headings')
        cols = [("Number", "#", 50), ("Name", "Name", 200), ("Description", "Description", 400), 
                ("Date", "Date", 100), ("User", "User", 100)]
        
        for col_id, col_name, width in cols:
            self.config_tree.heading(col_id, text=col_name)
            self.config_tree.column(col_id, width=width)

        self.config_tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        
        scrollbar = ttk.Scrollbar(table_frame, orient=tk.VERTICAL, command=self.config_tree.yview)
        self.config_tree.configure(yscrollcommand=scrollbar.set)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        
        self.button_frame = ttk.Frame(self.master)
        self.button_frame.pack(side=tk.BOTTOM,pady=(0,10))
        process_button = tk.Button(self.button_frame, text=self.action, command=self.process_action)
        process_button.pack(pady=10)
        
        self.bind_all('<KeyPress>', self.handle_number_key)
        self.config_tree.bind('<<TreeviewSelect>>', self.on_tree_select)

    def refresh_configs(self):
        try:
            # Direct call to controller
            configs = self.controller.get_saved_configurations()
            self.saved_configs = configs
            for item in self.config_tree.get_children():
                self.config_tree.delete(item)
            
            if configs:
                for idx, config in enumerate(configs, 1):
                    self.config_tree.insert("", tk.END, values=(
                        str(idx), config['name'], config['description'], 
                        config['date'], config['user']
                    ))
                print("Configurations refreshed successfully!")
        except Exception as e:
            print(f"Error refreshing configurations: {str(e)}")

    def handle_number_key(self, event):
        if event.char.isdigit() and self.saved_configs:
            index = int(event.char)
            if 1 <= index <= len(self.saved_configs):
                children = self.config_tree.get_children()
                self.config_tree.selection_remove(self.config_tree.selection())
                self.config_tree.selection_set(children[index-1])
                self.config_tree.focus(children[index-1])
                item = self.config_tree.item(children[index-1])
                self.selected_config_name = item['values'][1]

    def on_tree_select(self, event):
        selected = self.config_tree.selection()
        if selected:
            item = self.config_tree.item(selected[0])
            self.selected_config_name = item['values'][1]

    def process_action(self):
        if not self.selected_config_name:
            return

        if self.action == 'Download':
            # Default location logic
            dl_location = fr"C:\Users\{self.username}\OneDrive - Fiserv Corp\Documents\saved_configuration.zip"
            # Fallback if path doesn't exist/writable? (Optional: Add FileDialog here)
            
            try:
                success = self.controller.download_configuration(self.selected_config_name, dl_location)
                if success:
                    messagebox.showinfo("Success", f"Downloaded to {dl_location}")
                else:
                    messagebox.showerror("Error", "Download failed.")
            except Exception as e:
                messagebox.showerror("Error", f"Failed: {str(e)}")

        elif self.action == 'Restore':
            try:
                success = self.controller.restore_configuration(self.selected_config_name)
                if success:
                    messagebox.showinfo("Success", "Restore Successful")
                else:
                    messagebox.showerror("Error", "Restore Failed")
            except Exception as e:
                messagebox.showerror("Error", f"Failed: {str(e)}")

# -------------------------------
# Upload Panel
# -------------------------------
class UploadPanel(tk.Frame):
    def __init__(self, master, controller, **kwargs):
        super().__init__(master, **kwargs)
        self.controller = controller
        self.selected_file = None
        self.create_widgets()

    def create_widgets(self):
        upload_frame = ttk.Frame(self)
        upload_frame.pack(fill=tk.BOTH, expand=True, pady=20)
        
        file_frame = ttk.Frame(upload_frame)
        file_frame.pack(fill=tk.X, pady=20)
        
        ttk.Label(file_frame, text="Selected File:").pack(side=tk.LEFT, padx=(0, 10))
        self.file_path = tk.StringVar()
        self.file_entry = ttk.Entry(file_frame, textvariable=self.file_path, width=60)
        self.file_entry.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=(0, 10))
        
        browse_button = ttk.Button(file_frame, text="Browse", command=self.browse_file)
        browse_button.pack(side=tk.LEFT)
        
        self.button_frame = ttk.Frame(self.master)
        self.button_frame.pack(side=tk.BOTTOM,pady=(0,10))
        process_button = tk.Button(self.button_frame, text="Upload", command=self.process_action)
        process_button.pack(pady=10)

    def browse_file(self):
        filename = filedialog.askopenfilename(title="Select ZIP", filetypes=[("ZIP files", "*.zip")])
        if filename:
            self.file_path.set(filename)
            self.selected_file = filename

    def process_action(self):
        if self.selected_file:
            success = self.controller.upload_configuration(self.selected_file)
            if success:
                messagebox.showinfo("Success", "Upload successful!")
            else:
                messagebox.showerror("Error", "Upload failed.")

# -------------------------------
# Create Panel
# -------------------------------
class CreatePanel(tk.Frame):
    def __init__(self, master, controller, **kwargs):
        super().__init__(master, **kwargs)
        self.controller = controller
        self.create_widgets()

    def create_widgets(self):
        create_frame = ttk.Frame(self)
        create_frame.pack(fill=tk.BOTH, expand=True, pady=20)
        
        # Name
        name_frame = ttk.Frame(create_frame)
        name_frame.pack(fill=tk.X, pady=(0, 10))
        ttk.Label(name_frame, text="Name:").pack(side=tk.LEFT, padx=(0, 10))
        self.name_var = tk.StringVar()
        ttk.Entry(name_frame, textvariable=self.name_var, width=60).pack(side=tk.LEFT, fill=tk.X, expand=True)
        
        # Description
        desc_frame = ttk.Frame(create_frame)
        desc_frame.pack(fill=tk.X, pady=(0, 10))
        ttk.Label(desc_frame, text="Description:").pack(side=tk.LEFT, padx=(0, 10))
        self.desc_var = tk.StringVar()
        ttk.Entry(desc_frame, textvariable=self.desc_var, width=60).pack(side=tk.LEFT, fill=tk.X, expand=True)
        
        self.button_frame = ttk.Frame(self.master)
        self.button_frame.pack(side=tk.BOTTOM,pady=(0,10))
        tk.Button(self.button_frame, text="Create", command=self.process_action).pack(pady=10)       

    def process_action(self):
        name, description = self.name_var.get(), self.desc_var.get()
        if name:
            success = self.controller.create_configuration(name, description)
            if success:
                messagebox.showinfo("Success", "Config created!")
            else:
                messagebox.showerror("Error", "Failed to create config")
        else:
            messagebox.showwarning("Warning", "Name is required.")

# -------------------------------
# Update Panel
# -------------------------------
class UpdatePanel(tk.Frame):
    def __init__(self, master, controller, servers, username, password, **kwargs):
        super().__init__(master, **kwargs)
        self.controller = controller
        self.servers = servers
        self.username = username
        self.password = password
        self.source_hostname = None
        self.target_hostname = None
        self.create_widgets()

    def create_widgets(self):
        container = ttk.Frame(self)
        container.pack(fill=tk.BOTH, expand=True)
        
        # Source & Target Columns
        source_frame = ttk.Frame(container)
        source_frame.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=5)
        target_frame = ttk.Frame(container)
        target_frame.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=5)
        
        ttk.Label(source_frame, text="Source (Copy From)", font=('TkDefaultFont', 10, 'bold')).pack(pady=5)
        ttk.Label(target_frame, text="Target (Update To)", font=('TkDefaultFont', 10, 'bold')).pack(pady=5)
        
        # Setup Trees
        self.source_tree = self._create_server_tree(source_frame)
        self.target_tree = self._create_server_tree(target_frame)
        
        # Populate
        for idx, (env, hostname) in enumerate(self.servers, 1):
            self.source_tree.insert("", tk.END, values=(str(idx), env, hostname))
            self.target_tree.insert("", tk.END, values=(str(idx), env, hostname))
            
        self.button_frame = ttk.Frame(self.master)
        self.button_frame.pack(side=tk.BOTTOM,pady=(0,10))
        tk.Button(self.button_frame, text="Execute Update", command=self.process_action).pack(pady=10)       
        
        self.source_tree.bind('<<TreeviewSelect>>', self.on_source_select)
        self.target_tree.bind('<<TreeviewSelect>>', self.on_target_select)

    def _create_server_tree(self, parent):
        tree = ttk.Treeview(parent, columns=("Number", "Environment", "Hostname"), show='headings')
        tree.heading("Number", text="#")
        tree.heading("Environment", text="Environment")
        tree.heading("Hostname", text="Hostname")
        tree.column("Number", width=50)
        tree.pack(fill=tk.BOTH, expand=True)
        return tree

    def on_source_select(self, event):
        sel = self.source_tree.selection()
        if sel: self.source_hostname = self.source_tree.item(sel[0])['values'][2]

    def on_target_select(self, event):
        sel = self.target_tree.selection()
        if sel: self.target_hostname = self.target_tree.item(sel[0])['values'][2]

    def process_action(self):
        if self.source_hostname and self.target_hostname:
            self._start_update_thread()
        else:
            messagebox.showwarning("Warning", "Select both a source and a target server.")

    def _start_update_thread(self):
        # Local import to avoid circular dependency if LoadingDialog was in same file
        # But here we assume LoadingDialog is passed or available. 
        # For simplicity, we use a basic blocking approach or we need to import LoadingDialog from Dashboard.
        # To avoid circular imports, let's keep it simple or assume passed in controller.
        
        # Note: In the refactor, LoadingDialog is in ui/dashboard.py. 
        # We can emit an event or just do a simple wait cursor for now, 
        # OR we inject the loading dialog class.
        
        thread = threading.Thread(target=self._run_update, daemon=True)
        thread.start()

    def _run_update(self):
        try:
            success = self.controller.update_configuration(
                self.source_hostname, self.target_hostname, 
                self.username, self.password
            )
            self.after(0, lambda: self._update_done(success))
        except Exception as e:
            self.after(0, lambda: self._update_done(False, str(e)))

    def _update_done(self, success, error=None):
        if success:
            messagebox.showinfo("Success", "Update Completed.")
        else:
            msg = f"Update Failed: {error}" if error else "Update Failed."
            messagebox.showerror("Error", msg)

