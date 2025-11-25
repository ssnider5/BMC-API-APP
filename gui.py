import tkinter as tk
from tkinter import ttk, filedialog, messagebox
import os
import mvcm
from business import BusinessController
from business import ExcelParser
import threading
from tkinter import messagebox
from concurrent.futures import ThreadPoolExecutor, as_completed
import concurrent.futures
from concurrent.futures import ThreadPoolExecutor
import queue
import json
from datetime import datetime
import time

# -------------------------------
# Server Selection Panel – kept for reference
# -------------------------------
class ServerSelectionPanel(tk.Frame):
    def __init__(self, master, on_select, **kwargs):
        super().__init__(master, **kwargs)
        self.on_select = on_select
        self.servers = []
        self.create_widgets()

    def create_widgets(self):
        self.tree = ttk.Treeview(self, columns=("Environment", "Hostname"), show='headings')
        self.tree.heading("Environment", text="Environment")
        self.tree.heading("Hostname", text="Hostname")
        self.tree.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)

        self.select_button = tk.Button(self, text="Select Row", command=self.select_row)
        self.select_button.pack(pady=5)

        self.selected_label = tk.Label(self, text="Selected Hostname: None")
        self.selected_label.pack(pady=5)

        self.master.bind('<Return>', lambda e: self.select_row())
        self.master.bind('<KeyPress>', self.handle_keypress)

    def handle_keypress(self, event):
        if event.char.isdigit():
            index = int(event.char)
            if index == 0:
                return
            children = self.tree.get_children()
            if 1 <= index <= len(children):
                self.tree.selection_set(children[index-1])
                self.tree.focus(children[index-1])

    def add_row(self, environment, hostname):
        row_num = len(self.tree.get_children()) + 1
        labeled_env = f"{row_num}: {environment}"
        self.tree.insert("", "end", values=(labeled_env, hostname))
        self.servers.append((environment, hostname))

    def select_row(self):
        selected = self.tree.selection()
        if selected:
            item = self.tree.item(selected[0])
            hostname = item['values'][1]
            self.selected_label.config(text=f"Selected Hostname: {hostname}")
            self.on_select(hostname, self.servers)

# -------------------------------
# Login Panel – appears immediately
# -------------------------------
class LoginPanel(tk.Frame):
    def __init__(self, master, hostname, on_login, **kwargs):
        super().__init__(master, **kwargs)
        self.hostname = hostname
        self.on_login = on_login
        self.create_widgets()

    def create_widgets(self):

        tk.Label(self, text="Username").pack(pady=5)
        self.username_entry = tk.Entry(self)
        self.username_entry.pack(pady=5)

        tk.Label(self, text="Password").pack(pady=5)
        self.password_entry = tk.Entry(self, show="*")
        self.password_entry.pack(pady=5)

        self.login_button = tk.Button(self, text="Login", command=self.login)
        self.login_button.pack(pady=10)

        self.master.bind('<Return>', lambda e: self.login())

    def login(self):
        username = self.username_entry.get()
        password = self.password_entry.get()
        self.on_login(self.hostname, username, password)

        

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
        self.config_tree.heading("Number", text="#")
        self.config_tree.heading("Name", text="Name")
        self.config_tree.heading("Description", text="Description")
        self.config_tree.heading("Date", text="Date")
        self.config_tree.heading("User", text="User")
        self.config_tree.column("Number", width=50)
        self.config_tree.column("Name", width=200)
        self.config_tree.column("Description", width=400)
        self.config_tree.column("Date", width=100)
        self.config_tree.column("User", width=100)
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
            r = self.controller.mvcm.get("/saved-configurations", "application/json")
            if r.ok:
                self.saved_configs = r.json()
                for item in self.config_tree.get_children():
                    self.config_tree.delete(item)
                for idx, config in enumerate(self.saved_configs, 1):
                    self.config_tree.insert("", tk.END, values=(
                        str(idx),
                        config['name'],
                        config['description'],
                        config['date'],
                        config['user']
                    ))
                print("Configurations refreshed successfully!")
            else:
                print(f"Failed to refresh configurations. Status code: {r.status_code}")
        except Exception as e:
            print(f"Error refreshing configurations: {str(e)}")

    def handle_number_key(self, event):
        if event.char.isdigit():
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
        if self.action == 'Download' and self.selected_config_name:
            dl_location = None
            if not dl_location:
                dl_location = fr"C:\Users\{self.username}\OneDrive - Fiserv Corp\Documents\saved_configuration.zip"
            try:
                success = self.controller.download_configuration(self.selected_config_name, dl_location)
                messagebox.showinfo("Download Successful", "Data has been successfully downloaded!")
            except Exception as e:
                messagebox.showerror("Download Failed", f"Failed to download config: {str(e)}")
            if success:
                print(f"Successfully downloaded the ZIP file to {dl_location}")
            else:
                print("Download failed.")
        elif self.action == 'Restore' and self.selected_config_name:
            try:
                success = self.controller.restore_configuration(self.selected_config_name)
                messagebox.showinfo("Restore Successful", "Data has been successfully restored!")
            except Exception as e:
                messagebox.showerror("Restore Failed", f"Failed to restore config: {str(e)}")
            if success:
                print(f"Successfully restored")
            else:
                print("Restore failed.")
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
        filename = filedialog.askopenfilename(
            title="Select a ZIP file", filetypes=[("ZIP files", "*.zip")])
        if filename:
            self.file_path.set(filename)
            if filename and os.path.exists(filename):
                self.selected_file = filename

    def process_action(self):
        success = self.controller.upload_configuration(self.selected_file)
        print("Upload successful!" if success else "Upload failed.")

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
        name_frame = ttk.Frame(create_frame)
        name_frame.pack(fill=tk.X, pady=(0, 10))
        ttk.Label(name_frame, text="Name:").pack(side=tk.LEFT, padx=(0, 10))
        self.name_var = tk.StringVar()
        name_entry = ttk.Entry(name_frame, textvariable=self.name_var, width=60)
        name_entry.pack(side=tk.LEFT, fill=tk.X, expand=True)
        desc_frame = ttk.Frame(create_frame)
        desc_frame.pack(fill=tk.X, pady=(0, 10))
        ttk.Label(desc_frame, text="Description:").pack(side=tk.LEFT, padx=(0, 10))
        self.desc_var = tk.StringVar()
        desc_entry = ttk.Entry(desc_frame, textvariable=self.desc_var, width=60)
        desc_entry.pack(side=tk.LEFT, fill=tk.X, expand=True)
        self.button_frame = ttk.Frame(self.master)
        self.button_frame.pack(side=tk.BOTTOM,pady=(0,10))
        process_button = tk.Button(self.button_frame, text="Create", command=self.process_action)
        process_button.pack(pady=10)       

    def process_action(self):
        name, description = self.name_var.get(), self.desc_var.get()
        if name:
            success = self.controller.create_configuration(name, description)
            if success:
                messagebox.showinfo("Create Successful", "Config has been successfully created!")
            else:
                messagebox.showerror("Create Failed", f"Failed to create saved config")
        else:
            print("Name is required for creation.")

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
        source_frame = ttk.Frame(container)
        source_frame.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=5)
        target_frame = ttk.Frame(container)
        target_frame.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=5)
        ttk.Label(source_frame, text="Source (Server to copy)", font=('TkDefaultFont', 10, 'bold')).pack(pady=5)
        ttk.Label(target_frame, text="Target (Server to update)", font=('TkDefaultFont', 10, 'bold')).pack(pady=5)
        self.source_tree = ttk.Treeview(source_frame, columns=("Number", "Environment", "Hostname"), show='headings')
        self.source_tree.heading("Number", text="#")
        self.source_tree.heading("Environment", text="Environment")
        self.source_tree.heading("Hostname", text="Hostname")
        self.source_tree.column("Number", width=50)
        self.source_tree.column("Environment", width=150)
        self.source_tree.column("Hostname", width=300)
        self.source_tree.pack(fill=tk.BOTH, expand=True)
        self.target_tree = ttk.Treeview(target_frame, columns=("Number", "Environment", "Hostname"), show='headings')
        self.target_tree.heading("Number", text="#")
        self.target_tree.heading("Environment", text="Environment")
        self.target_tree.heading("Hostname", text="Hostname")
        self.target_tree.column("Number", width=50)
        self.target_tree.column("Environment", width=150)
        self.target_tree.column("Hostname", width=300)
        self.target_tree.pack(fill=tk.BOTH, expand=True)
        for idx, (env, hostname) in enumerate(self.servers, 1):
            self.source_tree.insert("", tk.END, values=(str(idx), env, hostname))
            self.target_tree.insert("", tk.END, values=(str(idx), env, hostname))
        self.button_frame = ttk.Frame(self.master)
        self.button_frame.pack(side=tk.BOTTOM,pady=(0,10))
        process_button = tk.Button(self.button_frame, text="Create", command=self.process_action)
        process_button.pack(pady=10)       
        self.source_tree.bind('<<TreeviewSelect>>', self.on_source_select)
        self.target_tree.bind('<<TreeviewSelect>>', self.on_target_select)
        self.bind_all('<KeyPress>', self.handle_number_keys)

    def on_source_select(self, event):
        selected = self.source_tree.selection()
        if selected:
            item = self.source_tree.item(selected[0])
            self.source_hostname = item['values'][2]

    def on_target_select(self, event):
        selected = self.target_tree.selection()
        if selected:
            item = self.target_tree.item(selected[0])
            self.target_hostname = item['values'][2]

    def handle_number_keys(self, event):
        if event.char.isdigit():
            index = int(event.char)
            if index <= len(self.servers):
                if event.state & 0x1:  # Shift pressed, select target
                    children = self.target_tree.get_children()
                    self.target_tree.selection_set(children[index-1])
                    self.target_tree.focus(children[index-1])
                    self.target_hostname = self.servers[index-1][1]
                else:
                    children = self.source_tree.get_children()
                    self.source_tree.selection_set(children[index-1])
                    self.source_tree.focus(children[index-1])
                    self.source_hostname = self.servers[index-1][1]
    
    def process_action(self):
        if self.source_hostname and self.target_hostname:
            self.process_update()
        else:
            print("You need to select two servers.")

    def process_update(self):      
        # Create and show loading dialog
        loading_dialog = LoadingDialog(self, "Updating configuration, please wait...")
        loading_dialog.start()  # Start the progress bar animation
        
        def update_thread():
            success = False
            error_message = None
            try:
                success = self.controller.update_configuration(
                    self.source_hostname,
                    self.target_hostname,
                    self.username,
                    self.password
                )
            except Exception as e:
                error_message = str(e)
            finally:
                # Schedule UI updates in the main thread
                if loading_dialog.winfo_exists():  # Check if dialog still exists
                    self.after(0, lambda: self.update_complete(loading_dialog, success, error_message))
        
        # Start the update process in a separate thread
        thread = threading.Thread(target=update_thread, daemon=True)
        thread.start()

    def update_complete(self, loading_dialog, success, error_message=None):
        try:          
            # Destroy the loading dialog
            if loading_dialog.winfo_exists():
                loading_dialog.destroy()
            
            # Show appropriate message
            if success:
                messagebox.showinfo("Success", "Update process completed successfully!")
            else:
                error_msg = "Update failed." if not error_message else f"Update failed: {error_message}"
                messagebox.showerror("Error", error_msg)
        except Exception as e:
            print(f"Error in update_complete: {str(e)}")


# -------------------------------
# Create From Excel Panel
# -------------------------------

class CreateFromExcelPanel(tk.Frame):
    def __init__(self, master, excel_parser, mvcm_inst, **kwargs):
        super().__init__(master, **kwargs)
        self.excel_parser = excel_parser
        self.selected_file = None
        self.create_widgets()
        self.mvcm_inst = mvcm_inst
        self.created_servers = []  # To store names of created servers
        self.verification_results = {}  # Store verification results for each server
        self.notification_showing = False
        self.colors_defined = False  # Track if colors have been defined
        
        # This will map server_name -> Treeview item ID for quick color updates
        self.server_item_map = {}

    def create_widgets(self):
        # Main container
        container = ttk.Frame(self)
        container.pack(fill=tk.BOTH, expand=True)
        
        # File selection frame
        file_frame = ttk.Frame(container)
        file_frame.pack(fill=tk.X, pady=(10, 20))
        
        # File path display
        self.file_path_var = tk.StringVar()
        self.file_path_var.set("No file selected")
        file_path_label = ttk.Label(file_frame, text="Excel File:")
        file_path_label.pack(side=tk.LEFT, padx=5)
        file_path_entry = ttk.Entry(file_frame, textvariable=self.file_path_var, width=50, state='readonly')
        file_path_entry.pack(side=tk.LEFT, padx=5, expand=True, fill=tk.X)
        
        # Browse button
        browse_button = ttk.Button(file_frame, text="Browse...", command=self.browse_file)
        browse_button.pack(side=tk.LEFT, padx=5)
        
        # Table frame
        self.table_frame = ttk.Frame(container)
        self.table_frame.pack(fill=tk.BOTH, expand=True, pady=(0, 10))
        
        # Initially empty message
        self.empty_label = ttk.Label(self.table_frame, text="Select an Excel file to display data")
        self.empty_label.pack(expand=True)
        
        # Actions frame
        actions_frame = ttk.Frame(container)
        actions_frame.pack(fill=tk.X, pady=(10, 0))
        
        # Import button (initially disabled)
        self.import_button = ttk.Button(actions_frame, text="Create CCS servers", command=self.import_data, state='disabled')
        self.import_button.pack(side=tk.BOTTOM, pady=10)
        
        # Status bar for notifications
        self.status_frame = ttk.Frame(self)
        self.status_frame.pack(fill=tk.X, side=tk.BOTTOM)
        
        # Create notification widget (initially hidden)
        self.notification_frame = ttk.Frame(self.master, relief="raised", borderwidth=2)
        self.notification_label = ttk.Label(self.notification_frame, text="", wraplength=300)
        self.notification_label.pack(padx=10, pady=10)
        self.close_button = ttk.Button(self.notification_frame, text="×", width=2, 
                                       command=self.hide_notification)
        self.close_button.pack(side=tk.RIGHT, anchor=tk.NE, padx=5, pady=5)

    def hide_notification(self):
        """Hide the notification popup"""
        self.notification_frame.place_forget()
        self.notification_showing = False

    def show_notification(self, message, error=False, log_text=None):
        """Show a notification popup in the bottom right corner"""

        self.notification_log_text = log_text

        # Configure notification appearance
        if error:
            self.notification_label.config(foreground="red")
        else:
            self.notification_label.config(foreground="black")
        
        # Update message
        self.notification_label.config(text=message)

        for child in self.notification_frame.pack_slaves():
            if getattr(child, "_is_view_log_button", False):
                child.destroy()

        if log_text:
            view_log_button = ttk.Button(
                self.notification_frame,
                text="View Log",
                command=self.view_log
            )

            view_log_button._is_view_log_button = True

            view_log_button.pack(side=tk.LEFT, padx=(10,0), pady=5)
        
        # Calculate position (bottom right)
        window_width = self.master.winfo_width()
        window_height = self.master.winfo_height()
        notification_width = 320  # Fixed width for notification
        notification_height = 100  # Approximate height
        
        x_position = window_width - notification_width - 20
        y_position = window_height - notification_height - 20
        
        # Show notification
        self.notification_frame.place(x=x_position, y=y_position, width=notification_width)
        self.notification_showing = True

    def view_log(self):

        if not self.notification_log_text:
            messagebox.showinfo("No Log avaliable", "No text avaliable")

        log_window = tk.Toplevel(self)
        log_window.title("Error Log")
        log_window.geometry("600x400")

        text_widget = tk.Text(log_window, wrap='word')
        text_widget.pack(fill=tk.BOTH, expand=True)

        text_widget.insert(tk.END, self.notification_log_text)

        text_widget.config(state='disabled')
        

    def browse_file(self):
        file_path = filedialog.askopenfilename(
            title="Select Excel File",
            filetypes=[("Excel files", "*.xlsx *.xls")]
        )
        
        if file_path:
            self.selected_file = file_path
            self.file_path_var.set(file_path)
            self.load_excel_preview()
    
    def load_excel_preview(self):
        # Clear existing table if any
        for widget in self.table_frame.winfo_children():
            widget.destroy()
        
        try:
            # Use the excel parser to read the file
            headers, data = self.excel_parser.read_excel(self.selected_file)
            
            # Create new treeview for the data
            self.data_tree = ttk.Treeview(self.table_frame, columns=headers, show='headings')
            
            # Define tag colors immediately after creating the treeview
            self.data_tree.tag_configure('success', background='#90EE90')  # Light green
            self.data_tree.tag_configure('failure', background='#FFCCCB')  # Light red
            self.colors_defined = True
            
            # Set column headings
            for header in headers:
                self.data_tree.heading(header, text=header)
                # Adjust column width based on content
                self.data_tree.column(header, width=100)
            
            # Insert data rows
            self.server_item_map = {}  # Reset mapping
            for row in data:
                item_id = self.data_tree.insert("", tk.END, values=row)
                # For convenience, assume the server name is in row[0] or row[3], etc.
                # Adjust as needed:
                if len(row) > 0:
                    server_name = row[3]  # or row[3] if that’s where server is
                    self.server_item_map[server_name] = item_id
            
            # Add scrollbars
            y_scrollbar = ttk.Scrollbar(self.table_frame, orient=tk.VERTICAL, command=self.data_tree.yview)
            self.data_tree.configure(yscrollcommand=y_scrollbar.set)
            
            x_scrollbar = ttk.Scrollbar(self.table_frame, orient=tk.HORIZONTAL, command=self.data_tree.xview)
            self.data_tree.configure(xscrollcommand=x_scrollbar.set)
            
            # Pack everything in the right order
            x_scrollbar.pack(side=tk.BOTTOM, fill=tk.X)
            y_scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
            self.data_tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
            
            # Bind selection event to show details
            self.data_tree.bind("<<TreeviewSelect>>", self.on_tree_select)
            
            # Enable import button
            self.import_button.config(state='normal')
            
        except Exception as e:
            error_label = ttk.Label(self.table_frame, text=f"Error loading Excel file: {str(e)}", foreground="red")
            error_label.pack(expand=True)   
            self.import_button.config(state='disabled')
    
    def on_tree_select(self, event):
        """Handle selection of a row in the treeview"""
        selected_items = self.data_tree.selection()
        if not selected_items:
            return

        item_id = selected_items[0]

        item_tags = self.data_tree.item(item_id, "tags")    
        if 'failure' in item_tags:
            item_values = self.data_tree.item(item_id,"values")
            if item_values:
                server_name = item_values[3]
                error_info = self.verification_results.get(server_name,{})
                error_code = error_info.get('error_code', 'Unknown Error')
                log_text = error_info.get('logText', 'No log text avaliable')
                self.show_notification(f"Error for {server_name}: {error_code}", error=True, log_text=log_text)

        item_values = self.data_tree.item(selected_items[0], "values")
        if not item_values:
            return
            
        # Adjust index based on your actual data structure
        server_name = item_values[0]
        
        # Check if we have verification results for this server
        if server_name in self.verification_results:
            result = self.verification_results[server_name]
            if result.get('error'):
                self.show_notification(f"Error for {server_name}: {result['error_code']}", error=True)
    
    def import_data(self):
        try:
            json_data = self.excel_parser.get_json_data()
            self.created_servers = self.excel_parser.extract_names(json_data)
            _result = self.excel_parser.create_ccs_server(self.mvcm_inst, json_data)
            
            messagebox.showinfo("Import Successful", "Data has been successfully imported!")
            self.show_verification_prompt()
            
        except Exception as e:
            messagebox.showerror("Import Failed", f"Failed to import data: {str(e)}")

    def show_verification_prompt(self):
        """Shows a popup asking if the user wants to verify the servers"""
        verify = messagebox.askyesno("Verify Servers", "Would you like to verify the server(s)?")
        if verify:
            self.verify_import()

    def verify_import(self):
        """Verifies the imported servers by sending POST requests in parallel."""
        if not self.created_servers:
            messagebox.showinfo("Verification", "No servers to verify.")
            return

        # Reset verification results
        self.verification_results = {}

        # Create a small progress window that will remain open while threads run
        progress_window = tk.Toplevel(self)
        progress_window.title("Verifying Servers")
        progress_window.geometry("300x100")
        progress_window.transient(self)
        progress_window.grab_set()
        
        progress_label = ttk.Label(progress_window, text="Verifying servers...")
        progress_label.pack(pady=10)
        
        progress = ttk.Progressbar(progress_window, length=250, mode='determinate')
        progress.pack(pady=10)
        progress['maximum'] = len(self.created_servers)
        
        # We’ll use a queue to get results from worker threads
        result_queue = queue.Queue()

        def verify_one_server(server_name):
            """
            This function runs in a worker thread.
            It returns a dict with all relevant info
            needed to update the UI.
            """
            try:
                endpoint = f"/api/ccs/servers/{server_name}/operations/start"
                _response = self.mvcm_inst.post(endpoint)  # start the server
                
                if _response.status_code == 404:
                    future = executor.submit(verify_one_server, server_name)
                    future.add_done_callback(worker_done)
                    self.futures.append(future)
                
                r = self.mvcm_inst.getlog(server_name)
                log_text = r.text
                lines = log_text.splitlines()

                is_success = False
                if len(lines) >= 3:
                    third_to_last_line = lines[-3]
                    if "Error exit" in third_to_last_line:
                        is_success = False
                    else:
                        is_success = True
                else:
                    "Log file is not greater than 3 lines"

                return {
                    'server_name': server_name,
                    'success': is_success,
                    'error': lines[-4],
                    'error_code': lines[-4],
                    'logText': log_text
                }
            except Exception as e:
                return {
                    'server_name': server_name,
                    'success': False,
                    'error': True,
                    'error_code': str(e)
                }

        def worker_done(future):
            """
            Called when a single future completes (in the main thread).
            We pull the result, push it into the queue for UI updates.
            """
            res = future.result()
            result_queue.put(res)

        # Create a thread pool
        executor = ThreadPoolExecutor(max_workers=1)

        # Submit tasks
        self.futures = []
        for server_name in self.created_servers:
            # skip empty
            if not server_name:
                continue
            future = executor.submit(verify_one_server, server_name)
            future.add_done_callback(worker_done)
            self.futures.append(future)

        # Track how many servers have finished
        finished_count = [0]  # put in a list so we can modify inside the function

        def process_results():
            """
            Periodically called in the main thread (via self.after).
            We check for completed results in the queue and update the GUI.
            """
            while not result_queue.empty():
                res = result_queue.get_nowait()
                server_name = res['server_name']
                self.verification_results[server_name] = res

                # Bump progress
                finished_count[0] += 1
                progress['value'] = finished_count[0]
                progress_label.config(text=f"Verifying {server_name}...")

                # Update the corresponding row color
                # Make sure color tags are defined
                if not self.colors_defined:
                    self.data_tree.tag_configure('success', background='#90EE90')
                    self.data_tree.tag_configure('failure', background='#FFCCCB')
                    self.colors_defined = True

                if server_name in self.server_item_map:
                    item_id = self.server_item_map[server_name]
                    # Clear existing tags
                    current_tags = list(self.data_tree.item(item_id, "tags"))
                    if 'success' in current_tags:
                        current_tags.remove('success')
                    if 'failure' in current_tags:
                        current_tags.remove('failure')
                    # Add success/failure
                    new_tag = 'success' if res['success'] else 'failure'
                    current_tags.append(new_tag)
                    self.data_tree.item(item_id, tags=current_tags)

            # If all futures are done, finalize. Otherwise, check again.
            if all(f.done() for f in self.futures):
                # Close the executor
                executor.shutdown(wait=False)
                # Close progress window
                progress_window.destroy()
                # Show summary
                success_count = sum(1 for v in self.verification_results.values() if v['success'])
                failure_count = len(self.verification_results) - success_count
                messagebox.showinfo(
                    "Verification Complete",
                    f"Verification complete.\nSuccessful: {success_count}\nFailed: {failure_count}\n\n"
                    f"Select a server in the table for error details."
                )
            else:
                # Not all done; schedule another check
                self.after(100, process_results)

        # Start checking results
        self.after(100, process_results)

# -------------------------------
# Create Console From Excel Panel
# -------------------------------
class CreateConsoleFromExcelPanel(tk.Frame):
    def __init__(self, master, excel_parser, mvcm_inst, **kwargs):
        super().__init__(master, **kwargs)
        self.excel_parser = excel_parser
        self.selected_file = None
        self.create_widgets()
        self.mvcm_inst = mvcm_inst

    def create_widgets(self):
        # Main container
        container = ttk.Frame(self)
        container.pack(fill=tk.BOTH, expand=True)
        
        # File selection frame
        file_frame = ttk.Frame(container)
        file_frame.pack(fill=tk.X, pady=(10, 20))
        
        # File path display
        self.file_path_var = tk.StringVar()
        self.file_path_var.set("No file selected")
        file_path_label = ttk.Label(file_frame, text="Excel File:")
        file_path_label.pack(side=tk.LEFT, padx=5)
        file_path_entry = ttk.Entry(file_frame, textvariable=self.file_path_var, width=50, state='readonly')
        file_path_entry.pack(side=tk.LEFT, padx=5, expand=True, fill=tk.X)
        
        # Browse button
        browse_button = ttk.Button(file_frame, text="Browse...", command=self.browse_file)
        browse_button.pack(side=tk.LEFT, padx=5)
        
        # Table frame
        self.table_frame = ttk.Frame(container)
        self.table_frame.pack(fill=tk.BOTH, expand=True, pady=(0, 10))
        
        # Initially empty message
        self.empty_label = ttk.Label(self.table_frame, text="Select an Excel file to display data")
        self.empty_label.pack(expand=True)
        
        # Actions frame
        actions_frame = ttk.Frame(container)
        actions_frame.pack(fill=tk.X, pady=(10, 0))
        
        # Import button (initially disabled)
        self.import_button = ttk.Button(actions_frame, text="Create CCS servers", command=self.import_data, state='disabled')
        self.import_button.pack(side=tk.BOTTOM, pady=10)

    def browse_file(self):
        file_path = filedialog.askopenfilename(
            title="Select Excel File",
            filetypes=[("Excel files", "*.xlsx *.xls")]
        )
        
        if file_path:
            self.selected_file = file_path
            self.file_path_var.set(file_path)
            self.load_excel_preview()
    
    def load_excel_preview(self):
        # Clear existing table if any
        for widget in self.table_frame.winfo_children():
            widget.destroy()
        
        try:
            # Use the excel parser to read the file
            headers, data = self.excel_parser.read_excel(self.selected_file, sheet_name=1)
            
            # Create new treeview for the data
            self.data_tree = ttk.Treeview(self.table_frame, columns=headers, show='headings')
            
            # Set column headings
            for header in headers:
                self.data_tree.heading(header, text=header)
                # Adjust column width based on content
                self.data_tree.column(header, width=100)
            
            # Insert data rows
            for row in data:
                self.data_tree.insert("", tk.END, values=row)
            
            # Add scrollbars
            y_scrollbar = ttk.Scrollbar(self.table_frame, orient=tk.VERTICAL, command=self.data_tree.yview)
            self.data_tree.configure(yscrollcommand=y_scrollbar.set)
            
            x_scrollbar = ttk.Scrollbar(self.table_frame, orient=tk.HORIZONTAL, command=self.data_tree.xview)
            self.data_tree.configure(xscrollcommand=x_scrollbar.set)
            
            # Pack everything
            self.data_tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
            y_scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
            x_scrollbar.pack(side=tk.BOTTOM, fill=tk.X)
            
            # Enable import button
            self.import_button.config(state='normal')
            
        except Exception as e:
            error_label = ttk.Label(self.table_frame, text=f"Error loading Excel file: {str(e)}", foreground="red")
            error_label.pack(expand=True)   
            self.import_button.config(state='disabled')
    
    def import_data(self):
        # This method would be implemented to handle the actual import process
        # For example, sending the data to an API or processing it further
        try:
            # Example implementation:
            json = self.excel_parser.get_json_data()
            print(json)
            self.excel_parser.create_ccs_console(self.mvcm_inst, json)
            # result = self.mvcm.post("/import-excel-data", json=self.excel_parser.get_json_data())
            messagebox.showinfo("Import Successful", "Data has been successfully imported!")
        except Exception as e:
            messagebox.showerror("Import Failed", f"Failed to import data: {str(e)}")

# # -------------------------------
# Action Panel – now features a banner with buttons,
# displays the title and underneath it the current server info
# (with a drop down to change the server),
# and refreshes the saved configurations correctly when a new server is selected.
# -------------------------------
class ActionPanel(tk.Frame):
    def __init__(self, master, controller, username, password, servers, **kwargs):
        super().__init__(master, **kwargs)
        self.controller = controller
        self.username = username
        self.password = password
        self.servers = servers  # List of tuples: (Environment, Hostname)
        self.current_action = None
        self.action_buttons = {}  # To store references to action buttons
        self.side_panel_buttons = {}  # To store references to side panel buttons
        # Set default selected server to the first one
        self.selected_server = self.servers[0]
        self.current_panel_mode = "saved_configurations"  # Default panel mode
        self.is_panel_expanded = True  # Track if side panel is expanded
        self.side_panel_width = 200  # Default width of side panel when expanded
        self.create_widgets()

    def create_widgets(self):
        # ---------------------------
        # Banner: Program name and new action buttons
        # ---------------------------
        banner_frame = ttk.Frame(self)
        banner_frame.pack(fill=tk.X, padx=5, pady=10)  # Increased padding makes banner bigger
        
        # Program name on the far left (with a slightly larger font)
        program_label = tk.Label(banner_frame, text="bmc api", font=('TkDefaultFont', 14, 'bold'))
        program_label.pack(side=tk.LEFT, padx=(5, 10))

        # Vertical Separator
        separator = ttk.Separator(banner_frame, orient=tk.VERTICAL)
        separator.pack(side=tk.LEFT, fill=tk.Y, padx=(0, 10))
        
        # Action buttons in the banner
        options = ["Saved Configurations", "CCS Server", "Automation Server"]
        for option in options:
            btn = tk.Button(banner_frame,
                            text=option,
                            command=lambda opt=option: self.switch_panel_mode(opt),
                            relief="flat", bd=0, padx=10, pady=5)
            btn.pack(side=tk.LEFT, padx=5)
            self.action_buttons[option] = btn

        # ---------------------------
        # Orange line underneath the banner
        # ---------------------------
        orange_line = tk.Frame(self, bg="orange", height=2)
        orange_line.pack(fill=tk.X, padx=0, pady=(0, 0))
        
        # ---------------------------
        # Main content container to hold side panel and content area
        # ---------------------------
        main_container = ttk.Frame(self)
        main_container.pack(fill=tk.BOTH, expand=True)
        
        # ---------------------------
        # Side panel (runs the entire length below the banner)
        # ---------------------------
        self.side_panel_container = ttk.Frame(main_container)
        self.side_panel_container.pack(side=tk.LEFT, fill=tk.Y, padx=0, pady=0)
        
        self.side_panel = ttk.Frame(self.side_panel_container, width=self.side_panel_width)
        self.side_panel.pack(side=tk.LEFT, fill=tk.Y, padx=0, pady=0)
        self.side_panel.pack_propagate(False)  # Don't shrink to fit content
        
        # Toggle button for collapsing/expanding side panel
        self.toggle_frame = ttk.Frame(self.side_panel_container, width=20)
        self.toggle_frame.pack(side=tk.LEFT, fill=tk.Y)
        
        # Configure toggle frame with dark grey background
        toggle_style = ttk.Style()
        toggle_style.configure("Toggle.TFrame", background="#444444")
        self.toggle_frame.configure(style="Toggle.TFrame")
        
        # Add toggle button with arrow icon
        self.toggle_button = tk.Button(
            self.toggle_frame, 
            text="◀", 
            command=self.toggle_side_panel,
            relief="flat", 
            bd=0, 
            bg="#444444", 
            fg="white", 
            activebackground="#555555", 
            activeforeground="white"
        )
        self.toggle_button.pack(side=tk.TOP, pady=10)
        
        # Side panel style - dark grey background
        side_panel_style = ttk.Style()
        side_panel_style.configure("SidePanel.TFrame", background="#444444")
        self.side_panel.configure(style="SidePanel.TFrame")
        
        # ---------------------------
        # Content area (right of side panel)
        # ---------------------------
        self.content_area = ttk.Frame(main_container)
        self.content_area.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        # ---------------------------
        # Initialize both panel modes but only show the default one
        # ---------------------------
        self.create_saved_configs_panel()
        self.switch_panel_mode("Saved Configurations")  # Start with saved configurations
        
    def create_saved_configs_panel(self):
        # Clear any existing content in the side panel
        for widget in self.side_panel.winfo_children():
            widget.destroy()
        self.side_panel_buttons = {}
        
        # Create buttons for saved configurations in the side panel
        options = ["Download", "Upload", "Restore", "Create", "Update"]
        for option in options:
            btn = tk.Button(self.side_panel,
                           text=option,
                           command=lambda opt=option: self.show_panel(opt),
                           relief="flat", bd=0, padx=10, pady=10,
                           bg="#444444", fg="white", activebackground="#555555", activeforeground="white",
                           width=20, anchor="w")
            btn.pack(fill=tk.X, pady=1)
            self.side_panel_buttons[option] = btn
            
    def create_ccs_server_panel(self):
        # Clear any existing content in the side panel
        for widget in self.side_panel.winfo_children():
            widget.destroy()
        
        self.side_panel_buttons = {}

                # Create buttons for saved configurations in the side panel
        options = ["Create from Excel", "Create Console from Excel", "Search Logs"]
        for option in options:
            test = tk.Button(self.side_panel,
                           text=option,
                           command=lambda opt=option: self.show_panel(opt),
                           relief="flat", bd=0, padx=10, pady=10,
                           bg="#444444", fg="white", activebackground="#555555", activeforeground="white",
                           width=20, anchor="w")
            test.pack(fill=tk.X, pady=1)
            self.side_panel_buttons[option] = test
    
    def create_automation_server_panel(self):
        # Clear any existing content in the side panel
        for widget in self.side_panel.winfo_children():
            widget.destroy()
        
        self.side_panel_buttons = {}

                # Create buttons for saved configurations in the side panel
        options = ["Create Automation from Excel"]
        for option in options:
            test = tk.Button(self.side_panel,
                           text=option,
                           command=lambda opt=option: self.show_panel(opt),
                           relief="flat", bd=0, padx=10, pady=10,
                           bg="#444444", fg="white", activebackground="#555555", activeforeground="white",
                           width=20, anchor="w")
            test.pack(fill=tk.X, pady=1)
            self.side_panel_buttons[option] = test
            
    def switch_panel_mode(self, mode):
        # Update button colors in banner
        for act, button in self.action_buttons.items():
            if act == mode:
                button.config(bg="orange", activebackground="orange", fg="white")
            else:
                button.config(bg="SystemButtonFace", activebackground="SystemButtonFace", fg="black")
        
        # Clear any existing content in the content area
        for widget in self.content_area.winfo_children():
            widget.destroy()
            
        # Update the side panel and content area based on the selected mode
        if mode == "Saved Configurations":
            self.current_panel_mode = "saved_configurations"
            self.create_saved_configs_panel()
            self.setup_saved_configs_content()
        elif mode == "CCS Server":
            self.current_panel_mode = "ccs_server"
            self.create_ccs_server_panel()
            self.setup_ccs_server_content()
        elif mode == "Automation Server":
            self.current_panel_mode = "automation_server"
            self.create_automation_server_panel()
            self.setup_automation_server_content()
            
    def setup_saved_configs_content(self):
        # ---------------------------
        # Title and Current Server Label (centered)
        # ---------------------------
        title_label = ttk.Label(self.content_area, text="Manage Saved Configurations", font=('TkDefaultFont', 12, 'bold'))
        title_label.pack(pady=(10, 5))
        self.current_server_label = ttk.Label(
            self.content_area,
            text=f"Current Server: {self.selected_server[0]} ({self.selected_server[1]})",
            font=('TkDefaultFont', 10)
        )
        self.current_server_label.pack(pady=(0, 10))

        # ---------------------------
        # Server Drop-Down Button (aligned to the left)
        # ---------------------------
        server_dropdown_frame = ttk.Frame(self.content_area)
        server_dropdown_frame.pack(fill=tk.X, padx=5, pady=(0, 10), anchor="w")
        self.servers_mb = tk.Menubutton(server_dropdown_frame, text="Change Server ▼", relief="flat", bd=0)
        self.servers_mb.menu = tk.Menu(self.servers_mb, tearoff=0)
        self.servers_mb["menu"] = self.servers_mb.menu
        for server in self.servers:
            env, hostname = server
            label = f"{env} ({hostname})"
            self.servers_mb.menu.add_command(label=label, command=lambda s=server: self.set_server(s))
        self.servers_mb.pack(side=None)
        
        # ---------------------------
        # Container for dynamic panels and action button
        # ---------------------------
        self.panel_container = ttk.Frame(self.content_area)
        self.panel_container.pack(fill=tk.BOTH, expand=True, pady=10)
        
    def setup_ccs_server_content(self):
        # ---------------------------
        # Title for CCS Server management
        # ---------------------------
        title_label = ttk.Label(self.content_area, text="Manage CCS Servers", font=('TkDefaultFont', 12, 'bold'))
        title_label.pack(pady=(10, 5))
        self.current_server_label = ttk.Label(
            self.content_area,
            text=f"Current Server: {self.selected_server[0]} ({self.selected_server[1]})",
            font=('TkDefaultFont', 10)
        )
        self.current_server_label.pack(pady=(0, 10))

        # ---------------------------
        # Server Drop-Down Button (aligned to the left)
        # ---------------------------
        server_dropdown_frame = ttk.Frame(self.content_area)
        server_dropdown_frame.pack(fill=tk.X, padx=5, pady=(0, 10), anchor="w")
        self.servers_mb = tk.Menubutton(server_dropdown_frame, text="Change Server ▼", relief="flat", bd=0)
        self.servers_mb.menu = tk.Menu(self.servers_mb, tearoff=0)
        self.servers_mb["menu"] = self.servers_mb.menu
        for server in self.servers:
            env, hostname = server
            label = f"{env} ({hostname})"
            self.servers_mb.menu.add_command(label=label, command=lambda s=server: self.set_server(s))
        self.servers_mb.pack(side=None)
        
        # ---------------------------
        # Container for dynamic panels and action button
        # ---------------------------
        self.panel_container = ttk.Frame(self.content_area)
        self.panel_container.pack(fill=tk.BOTH, expand=True, pady=10)
        self.button_frame = ttk.Frame(self.content_area)
        self.button_frame.pack(pady=10)
        
        # Note: The CCS server content area is similar to saved configurations
        # but with a different title. You can add more specific content as needed.

    def setup_automation_server_content(self):
        # ---------------------------
        # Title for CCS Server management
        # ---------------------------
        title_label = ttk.Label(self.content_area, text="Manage Automation Servers", font=('TkDefaultFont', 12, 'bold'))
        title_label.pack(pady=(10, 5))
        self.current_server_label = ttk.Label(
            self.content_area,
            text=f"Current Server: {self.selected_server[0]} ({self.selected_server[1]})",
            font=('TkDefaultFont', 10)
        )
        self.current_server_label.pack(pady=(0, 10))

        # ---------------------------
        # Server Drop-Down Button (aligned to the left)
        # ---------------------------
        server_dropdown_frame = ttk.Frame(self.content_area)
        server_dropdown_frame.pack(fill=tk.X, padx=5, pady=(0, 10), anchor="w")
        self.servers_mb = tk.Menubutton(server_dropdown_frame, text="Change Server ▼", relief="flat", bd=0)
        self.servers_mb.menu = tk.Menu(self.servers_mb, tearoff=0)
        self.servers_mb["menu"] = self.servers_mb.menu
        for server in self.servers:
            env, hostname = server
            label = f"{env} ({hostname})"
            self.servers_mb.menu.add_command(label=label, command=lambda s=server: self.set_server(s))
        self.servers_mb.pack(side=None)
        
        # ---------------------------
        # Container for dynamic panels and action button
        # ---------------------------
        self.panel_container = ttk.Frame(self.content_area)
        self.panel_container.pack(fill=tk.BOTH, expand=True, pady=10)
        self.button_frame = ttk.Frame(self.content_area)
        self.button_frame.pack(pady=10)
        
        # Note: The CCS server content area is similar to saved configurations
        # but with a different title. You can add more specific content as needed.

    def set_server(self, server):
        self.selected_server = server
        # Update the server label in the current content area
        for widget in self.content_area.winfo_children():
            if isinstance(widget, ttk.Label) and hasattr(widget, 'cget') and widget.cget('text').startswith("Current Server:"):
                widget.config(text=f"Current Server: {server[0]} ({server[1]})")
                break
        
        self.controller.connect(server[1], self.username, self.password)
        new_configs = self.controller.get_saved_configurations()
        self.saved_configs = new_configs
        print(f"Connected to new server: {server[0]} ({server[1]})")
        for widget in self.panel_container.winfo_children():
            if hasattr(widget, 'refresh_configs'):
                widget.saved_configs = new_configs
                widget.refresh_configs()

    def show_panel(self, action):
        self.current_action = action
        # Update button colors in side panel: set the active button to orange, others to default
        for act, button in self.side_panel_buttons.items():
            if act == action:
                button.config(bg="#FF8C00", activebackground="#FF8C00", fg="white")
            else:
                button.config(bg="#444444", activebackground="#555555", fg="white")

        # Clear any existing panel from the panel container and button frame
        for widget in self.panel_container.winfo_children():
            widget.destroy()

        if action in ['Download', 'Restore']:
            panel = DownloadRestorePanel(self.panel_container, self.controller,
                                        self.username, self.current_action)
            panel.pack(fill=tk.BOTH, expand=True)
        elif action == 'Upload':
            panel = UploadPanel(self.panel_container, self.controller)
            panel.pack(fill=tk.BOTH, expand=True)
        elif action == 'Create':
            panel = CreatePanel(self.panel_container, self.controller)
            panel.pack(fill=tk.BOTH, expand=True)
        elif action == 'Update':
            panel = UpdatePanel(self.panel_container, self.controller, self.servers, self.username, self.password)
            panel.pack(fill=tk.BOTH, expand=True)
        elif action == 'Create from Excel':
            excel_parser = ExcelParser()
            panel = CreateFromExcelPanel(self.panel_container, excel_parser, self.controller.mvcm)
            panel.pack(fill=tk.BOTH, expand=True)
        elif action == "Create Console from Excel":
            excel_parser = ExcelParser()
            panel = CreateConsoleFromExcelPanel(self.panel_container, excel_parser, self.controller.mvcm)
            panel.pack(fill=tk.BOTH, expand=True)
        elif action == "Search Logs":
            panel = LogSearchPanel(self.panel_container, self.controller)
            panel.pack(fill=tk.BOTH, expand=True)
        elif action == "Create Automation from Excel":
            panel = TestCode(self.panel_container, self.controller)
            panel.pack(fill=tk.BOTH, expand=True)
    
    def toggle_side_panel(self):
        """Toggle the side panel between collapsed and expanded states"""
        if self.is_panel_expanded:
            # Collapse the panel
            self.side_panel.pack_forget()
            self.toggle_button.config(text="▶")  # Change arrow direction
            self.is_panel_expanded = False
        else:
            # Expand the panel
            self.side_panel.pack(side=tk.LEFT, fill=tk.Y, padx=0, pady=0)
            self.toggle_button.config(text="◀")  # Change arrow direction
            self.is_panel_expanded = True

# ------------------------------
# LOADING SCREEN
# ------------------------------
class LoadingDialog(tk.Toplevel):
    def __init__(self, parent, message="Processing..."):
        super().__init__(parent)
        self.title("Loading")
        
        # Make the dialog modal
        self.transient(parent)
        self.grab_set()
        
        # Remove window decorations
        self.overrideredirect(True)
        
        # Center the dialog on the parent window
        window_width = 300
        window_height = 100
        screen_width = parent.winfo_screenwidth()
        screen_height = parent.winfo_screenheight()
        x = (screen_width - window_width) // 2
        y = (screen_height - window_height) // 2
        self.geometry(f'{window_width}x{window_height}+{x}+{y}')
        
        # Create a frame with a border
        main_frame = ttk.Frame(self, relief='raised', borderwidth=2)
        main_frame.pack(fill=tk.BOTH, expand=True, padx=2, pady=2)
        
        # Add message label
        self.message_label = ttk.Label(main_frame, text=message, font=('TkDefaultFont', 10))
        self.message_label.pack(pady=10)
        
        # Add progress bar
        self.progress_bar = ttk.Progressbar(main_frame, mode='indeterminate', length=200)
        self.progress_bar.pack(pady=10)
        
        # Start the progress bar animation
        self.progress_bar.start(10)
        
        # Force update of the dialog
        self.update_idletasks()
        
        # Keep dialog on top
        self.lift()
        self.focus_force()

    def update_progress(self):
        # Keep updating the dialog while it's visible
        if self.winfo_exists():
            self.update_idletasks()
            self.after(100, self.update_progress)

    def start(self):
        self.update_progress()

class LogSearchPanel(tk.Frame):

    def __init__(self, master, controller, **kwargs):
        super().__init__(master, **kwargs)
        self.controller = controller
        self.base_url = 'https://sylp2bcmapp0002.ess.fiserv.one/mvcm-api/logs'
        
        # Two-level caching strategy
        self.raw_log_cache = {}  # Cache for raw downloaded logs
        self.filtered_log_cache = {}  # Cache for filtered results
        
        # Create an input frame for date and time filters.
        self.input_frame = ttk.Frame(self)
        self.input_frame.pack(pady=10)
        
        ttk.Label(self.input_frame, text="Date (YYYY-MM-DD):").grid(row=0, column=0, padx=5, pady=2)
        self.date_entry = ttk.Entry(self.input_frame)
        self.date_entry.grid(row=0, column=1, padx=5, pady=2)
        
        ttk.Label(self.input_frame, text="Time (HH: or HH:MM):").grid(row=1, column=0, padx=5, pady=2)
        self.time_entry = ttk.Entry(self.input_frame)
        self.time_entry.grid(row=1, column=1, padx=5, pady=2)
        
        self.retrieve_button = ttk.Button(self.input_frame, text="Retrieve Logs", command=self.start_log_retrieval)
        self.retrieve_button.grid(row=2, column=0, columnspan=2, pady=5)

        ttk.Label(self.input_frame, text="Cache Status:").grid(row=3, column=0, padx=5, pady=2)
        self.cache_status = ttk.Label(self.input_frame, text="0 logs cached")
        self.cache_status.grid(row=3, column=1, padx=5, pady=2)
        
        self.clear_cache_button = ttk.Button(self.input_frame, text="Clear Cache", command=self.clear_cache)
        self.clear_cache_button.grid(row=4, column=0, columnspan=2, pady=5)
        
        # -------------------------
        # New UI structure: A horizontal container holding:
        #  - Left: TOC (Table of Contents)
        #  - Right: Log details (with a floating header and scrollbars)
        # -------------------------
        self.content_frame = ttk.Frame(self)
        self.content_frame.pack(fill='both', expand=True, padx=10, pady=10)
        
        # Left panel: TOC
        self.toc_frame = ttk.Frame(self.content_frame)
        self.toc_frame.pack(side='left', fill='y')
        
        # Create a Treeview for the table of contents.
        self.toc_tree = ttk.Treeview(self.toc_frame)
        self.toc_tree.pack(fill='both', expand=True)
        # Bind a selection event so clicking scrolls to the log.
        self.toc_tree.bind("<<TreeviewSelect>>", self.on_toc_select)
        
        # Right panel: Log details with a floating header.
        self.log_panel = ttk.Frame(self.content_frame)
        self.log_panel.pack(side='left', fill='both', expand=True)
        
        # Floating header label that displays the current log and log type.
        self.current_log_label = ttk.Label(self.log_panel, text="Current Log: ")
        self.current_log_label.pack(fill='x')
        
        # Create a frame for the Text widget and its scrollbars.
        self.text_frame = ttk.Frame(self.log_panel)
        self.text_frame.pack(fill='both', expand=True)
        
        # Text widget for log output; wrap is set to 'none' to allow horizontal scrolling.
        self.text_widget = tk.Text(self.text_frame, wrap='none', font=("Verdana", 8))
        self.text_widget.pack(side='left', fill='both', expand=True)
        
        # Vertical scrollbar
        self.v_scrollbar = ttk.Scrollbar(self.text_frame, orient='vertical', command=self.text_widget.yview)
        self.v_scrollbar.pack(side='right', fill='y')
        self.text_widget.configure(yscrollcommand=self.v_scrollbar.set)
        
        # Horizontal scrollbar
        self.h_scrollbar = ttk.Scrollbar(self.log_panel, orient='horizontal', command=self.text_widget.xview)
        self.h_scrollbar.pack(side='bottom', fill='x')
        self.text_widget.configure(xscrollcommand=self.h_scrollbar.set)
        
        self.previous_log = None
        # Bind scroll events to update the floating header.
        self.text_widget.bind("<ButtonRelease-1>", self.update_current_log_header)
        self.text_widget.bind("<KeyRelease>", self.update_current_log_header)
        self.text_widget.bind("<MouseWheel>", self.update_current_log_header)
    
    def clear_cache(self):
        """Clears both raw and filtered log caches."""
        self.raw_log_cache = {}
        self.filtered_log_cache = {}
        self.update_cache_status()
        self.text_widget.delete("1.0", tk.END)
        self.text_widget.insert(tk.END, "Cache cleared.\n")
    
    def update_cache_status(self):
        """Updates the cache status display."""
        self.cache_status.config(text=f"{len(self.raw_log_cache)} logs cached")
    
    def start_log_retrieval(self):
        """Starts a background thread to retrieve logs based on the entered date and time filters."""
        date_filter = self.date_entry.get().strip() or None
        time_filter = self.time_entry.get().strip() or ""
        
        self.text_widget.delete("1.0", tk.END)
        self.text_widget.insert(tk.END, "Starting log retrieval...\n")
        
        retrieval_thread = threading.Thread(target=self.testCode, args=(date_filter, time_filter))
        retrieval_thread.daemon = True
        retrieval_thread.start()
    
    def update_current_log_header(self, event=None):
        """
        Determine the current log section visible in the text widget and update the floating header.
        Assumes that each log starts with lines like:
           "Log Name: <name>"
           "Log Type: <type>"
        """
        # Get the index of the top visible pixel in the text widget.
        first_visible_index = self.text_widget.index("@0,0")
        # Get the line number
        line_num = int(first_visible_index.split('.')[0])
        # Retrieve all text lines.
        all_lines = self.text_widget.get("1.0", tk.END).splitlines()
        
        current_log = "Unknown"
        current_log_type = "Unknown"
        # Search upward from the current line until we find a header.
        for i in range(line_num - 1, -1, -1):
            line = all_lines[i]
            if line.startswith("Log Name:"):
                current_log = line.replace("Log Name:", "").strip()
                self.previous_log = current_log
            if line.startswith("Log Type:"):
                current_log_type = line.replace("Log Type:", "").strip()
                previous_log_type = current_log_type
                # Once both are found, break.
                break
        
        self.current_log_label.config(text=f"Current Log: {current_log} | Type: {current_log_type}" if self.previous_log is None else f"Current Log: {self.previous_log} | Type: {previous_log_type}" )
    
    def on_toc_select(self, event):
        """
        When a user selects an item from the TOC tree, scroll the text widget to the corresponding log header.
        If a log (child node) is selected, scroll to its "Log Name:" line.
        If a log type (parent node) is selected, scroll to the first log of that type.
        """
        selected_item = self.toc_tree.selection()
        if not selected_item:
            return
        item_text = self.toc_tree.item(selected_item, "text")
        parent = self.toc_tree.parent(selected_item[0])
        if parent:  # This is a log (child node)
            search_term = f"Log Name: {item_text}"
        else:  # This is a log type (parent node)
            search_term = f"Log Type: {item_text}"
        pos = self.text_widget.search(search_term, "1.0", tk.END)
        if pos:
            self.text_widget.see(pos)
    
    def log_timing(self, message):
        """Log timing information to the text widget on the main thread."""
        self.text_widget.after(0, lambda: self.text_widget.insert(tk.END, f"{message}\n"))
        
    def get_or_download_log(self, package_index, parent, name):
        """
        Gets a log from cache or downloads it if not cached.
        Returns the raw log content.
        """
        # Construct the download URL
        if parent and not (name.startswith('server.') and name.endswith('.log') and name[7:-4].isdigit()) and not (name.startswith('catalina.')):
            download_url = f'{self.base_url}/download/{package_index}/{parent}/{name}'
        else:
            download_url = f'{self.base_url}/download/{package_index}/{name}'
        
        # Cache key for raw log
        cache_key = download_url
        
        # Check raw log cache first
        if cache_key in self.raw_log_cache:
            return self.raw_log_cache[cache_key], 0  # Return cached content and 0 download time
        
        # Download the log file if not in cache
        start_time = time.time()
        download_resp = self.controller.mvcm.getalllogs(download_url)
        download_time = time.time() - start_time
        
        log_content = download_resp.text if hasattr(download_resp, 'text') else download_resp
        
        # Cache the raw log
        self.raw_log_cache[cache_key] = log_content
        self.update_cache_status()
        
        return log_content, download_time
    
    def get_filtered_log(self, raw_log, time_filter, date_filter):
        """
        Filters a log based on time and date filters.
        First checks if this filter has been applied before (in filtered_log_cache).
        """
        # If no filters, return raw log
        if not time_filter and (not date_filter or date_filter == "0000-00-00"):
            return raw_log, 0
        
        # Create a unique key for this raw log and filter combination
        # We'll use a hash of the raw log as part of the key to avoid extremely long keys
        raw_log_hash = hash(raw_log)
        filter_key = f"{raw_log_hash}_{time_filter}_{date_filter}"
        
        # Check filtered log cache
        if filter_key in self.filtered_log_cache:
            return self.filtered_log_cache[filter_key], 0
        
        # Apply filter and time it
        start_time = time.time()
        filtered_log = self.filter_log_content(raw_log, time_filter, date_filter)
        filter_time = time.time() - start_time
        
        # Cache the filtered result
        self.filtered_log_cache[filter_key] = filtered_log
        
        return filtered_log, filter_time
    
    def filter_log_content(self, log_content, time_filter, date_filter):
        """
        Filters log content based on time and date filters.
        This is separated for better profiling and optimization.
        """
        # Shortcut: if both filters are None, return the original content
        if not time_filter and (not date_filter or date_filter == "0000-00-00"):
            return log_content
            
        # Parse time filter
        desired_hour = None
        desired_minute = None
        desired_tenth = None
        
        if time_filter:
            time_parts = time_filter.split(":")
            desired_hour = time_parts[0]
            if len(time_parts) > 1:
                desired_minute = time_parts[1]
                if len(desired_minute) == 1:
                    desired_tenth = desired_minute[0]
                if desired_minute == '':
                    desired_minute = None
        
        desired_date = date_filter if date_filter and date_filter != "0000-00-00" else None
        
        # Create a regular expression pattern for faster filtering
        if desired_date and desired_hour and desired_minute:
            # Full date and time (YYYY-MM-DD HH:MM)
            pattern = f"{desired_date} {desired_hour}:{desired_minute}"
            filtered_lines = [line for line in log_content.splitlines() if len(line) >= 19 and line.startswith(pattern)]
            print(pattern, filtered_lines)
        elif desired_date and desired_hour and desired_tenth:
            # Date, hour and tenth of minute (YYYY-MM-DD HH:M)
            pattern = f"{desired_date} {desired_hour}:{desired_tenth}"
            filtered_lines = [line for line in log_content.splitlines() if len(line) >= 19 and line.startswith(pattern)]
        elif desired_date and desired_hour:
            # Date and hour only (YYYY-MM-DD HH)
            pattern = f"{desired_date} {desired_hour}:"
            filtered_lines = [line for line in log_content.splitlines() if len(line) >= 19 and line.startswith(pattern)]
        elif desired_date:
            # Date only (YYYY-MM-DD)
            filtered_lines = [line for line in log_content.splitlines() if len(line) >= 10 and line.startswith(desired_date)]
        elif desired_hour and desired_minute:
            # Hour and minute only (HH:MM)
            pattern = f"{desired_hour}:{desired_minute}"
            filtered_lines = [line for line in log_content.splitlines() if len(line) >= 19 and pattern in line[:16]]
        elif desired_hour and desired_tenth:
            # Hour and tenth of minute (HH:M)
            pattern = f"{desired_hour}:{desired_tenth}"
            filtered_lines = [line for line in log_content.splitlines() if len(line) >= 19 and pattern in line[:15]]
        elif desired_hour:
            # Hour only (HH)
            pattern = f"{desired_hour}:"
            filtered_lines = [line for line in log_content.splitlines() if len(line) >= 19 and pattern in line[:14]]
        else:
            # No valid filters, return the original content
            return log_content
        
        return "\n".join(filtered_lines)

    def download_and_filter_log(self, package_index, parent, name, time_filter, date_filter):
        """
        Gets a log (from cache or by downloading) and applies filtering.
        Returns a tuple of (filtered_log_content, download_time, filter_time)
        """
        # First, get or download the raw log
        raw_log, download_time = self.get_or_download_log(package_index, parent, name)
        
        # Then filter the log (from filter cache or by applying filter)
        filtered_log, filter_time = self.get_filtered_log(raw_log, time_filter, date_filter)
        
        return filtered_log, download_time, filter_time

    def testCode(self, specified_date=None, specified_time=None):
        """
        Retrieve log files from the API with optional date and time filtering.
        """
        overall_start_time = time.time()
        
        # Set default date filter if none provided
        date_filter = specified_date if specified_date else "0000-00-00"
        time_filter = specified_time if specified_time else ""
        
        self.log_timing(f"Starting log retrieval with date filter: {date_filter}, time filter: {time_filter}")
        
        # Fetch packages list
        packages_start_time = time.time()
        resp = self.controller.mvcm.getalllogs(self.base_url)
        packages_end_time = time.time()
        packages_time = packages_end_time - packages_start_time
        self.log_timing(f"API call for packages list took: {packages_time:.3f} seconds")
        
        try:
            packages = resp.json()
        except Exception:
            packages = json.loads(resp.text)
        
        # Collect all logs to be downloaded
        logs_to_download = []
        log_list_fetch_time = 0
        
        for i, package in enumerate(packages, 1):
            log_type = package.get('name', 'Unknown')
            
            list_start_time = time.time()
            resp = self.controller.mvcm.getalllogs(f'{self.base_url}/{i}')
            list_end_time = time.time()
            log_list_fetch_time += list_end_time - list_start_time
            
            log_files_array = resp.json().get('logFiles', [])
            for log_file in log_files_array:
                name = log_file.get('name', 'Unnamed Log')
                parent = log_file.get('parent')
                date_modified = log_file.get('dateModified')
                
                # Only process logs modified on or after the specified date
                if not date_filter or date_filter == "0000-00-00" or (date_modified and date_modified >= date_filter):
                    logs_to_download.append((i, parent, name, log_type))
        
        self.log_timing(f"API calls for log lists took: {log_list_fetch_time:.3f} seconds")
        self.log_timing(f"Found {len(logs_to_download)} logs to process")
        
        # Track cache statistics
        cache_hits = 0
        cache_misses = 0
        
        # Use ThreadPoolExecutor to parallelize the API calls for downloading logs
        log_files = {}
        total_download_time = 0
        total_filter_time = 0
        
        with ThreadPoolExecutor(max_workers=10) as executor:
            future_to_log = {}
            for (package_index, parent, name, log_type) in logs_to_download:
                future = executor.submit(
                    self.download_and_filter_log, 
                    package_index, parent, name, time_filter, date_filter
                )
                future_to_log[future] = (name, log_type)
            
            # Collect results as they complete
            for future in concurrent.futures.as_completed(future_to_log):
                name, log_type = future_to_log[future]
                try:
                    log_content, download_time, filter_time = future.result()
                    
                    # If download_time is 0, it was a cache hit
                    if download_time == 0:
                        cache_hits += 1
                    else:
                        cache_misses += 1
                        total_download_time += download_time
                        
                    total_filter_time += filter_time
                    
                    if log_content and log_content.strip():  # Only keep non-empty logs
                        log_files[name] = {'type': log_type, 'content': log_content}
                except Exception as exc:
                    self.log_timing(f"Error retrieving log {name}: {exc}")
        
        overall_end_time = time.time()
        overall_time = overall_end_time - overall_start_time
        
        # Summary timing information
        self.log_timing(f"Cache hits: {cache_hits}, Cache misses: {cache_misses}")
        self.log_timing(f"Total download time: {total_download_time:.3f} seconds")
        self.log_timing(f"Total filtering time: {total_filter_time:.3f} seconds")
        self.log_timing(f"Overall processing time: {overall_time:.3f} seconds")
        self.log_timing(f"Retrieved {len(log_files)} logs with content")

        print(f"Cache hits: {cache_hits}, Cache misses: {cache_misses}")
        print(f"Total download time: {total_download_time:.3f} seconds")
        print(f"Total filtering time: {total_filter_time:.3f} seconds")
        print(f"Overall processing time: {overall_time:.3f} seconds")
        print(f"Retrieved {len(log_files)} logs with content")
        
        # Schedule the UI update on the main thread
        self.text_widget.after(0, self.update_text_widget, log_files)
    
    def update_text_widget(self, log_files):
            """
            Update the Text widget with the retrieved logs and populate the TOC.
            This example organizes the TOC by log type.
            """
            self.text_widget.delete("1.0", tk.END)
            # Clear existing TOC items.
            for item in self.toc_tree.get_children():
                self.toc_tree.delete(item)
            
            # Organize logs by type.
            toc_data = {}
            for log_name, details in log_files.items():
                log_type = details['type']
                toc_data.setdefault(log_type, []).append(log_name)
            
            # Populate the TOC Treeview.
            for log_type, logs in toc_data.items():
                parent_id = self.toc_tree.insert("", "end", text=log_type, open=True)
                for log_name in logs:
                    self.toc_tree.insert(parent_id, "end", text=log_name)
            
            # Insert logs into the text widget.
            self.text_widget.insert(tk.END, "Collected Log Files:\n")
            self.text_widget.insert(tk.END, "=" * 80 + "\n")
            for log_name, details in log_files.items():
                if not details['content']:
                    continue
                self.text_widget.insert(tk.END, f"Log Name: {log_name}\n")
                self.text_widget.insert(tk.END, f"Log Type: {details['type']}\n")
                self.text_widget.insert(tk.END, "-" * 80 + "\n")
                self.text_widget.insert(tk.END, details['content'] + "\n")
                self.text_widget.insert(tk.END, "=" * 80 + "\n")

class TestCode(tk.Frame):
    def __init__(self, master, controller, **kwargs):
        super().__init__(master, **kwargs)
        self.controller = controller
        self.create_server()

    def create_server(self):
        # Get the server data
        response = self.controller.mvcm.getalllogs('https://sylp2bcmapp0002.ess.fiserv.one/mvcm-api/api/automation/servers?includeSessions=true')
        # Parse the JSON response
        server_data = response.json()
        
        print(server_data)
        # Initialize an array to store session details
        session_details = []

        # Define the servers we're interested in
        target_servers = ['EMEA', 'MERCHANT_CONSOLES', 'OPTIS_CONSOLES']

        # Iterate through the servers
        for server in server_data['servers']:
            # Check if the current server is one we're interested in
            if server['name'] in target_servers:
                # Iterate through the sessions of this server
                for session in server['sessions']:
                    try:
                        session_name_parts = session['name'].split('_', 1)
                        session_details.append({
                            "id": session['id'],
                            "session": session_name_parts[0],
                            "server": session_name_parts[1]
                        })
                    except:
                        pass

        # Create the JSON content for the POST request
        jsoncontent = {
        }

        # Print the JSON content to verify
        #print(json.dumps(jsoncontent, indent=4))

        # Make the POST request with the collected session names
        response = self.controller.mvcm.posttest('https://sylp2bcmapp0002.ess.fiserv.one/mvcm-api/automation/servers/ALL_CONSOLES', jsoncontent)

        
        # Create the JSON content for the POST request
        jsoncontent = {
            "sessionNamePattern": "%CcsConsole%_%CcsServer%",
            "username": "SVC-BMC-AMI-CM",
            "password": r"NR+..gYQB7TGNyhy7$Dp!jd5z\5Rpo6Z",
            "domain": "",
            "ccs-sessions": session_details
        }

        print(json.dumps(jsoncontent, indent=4))

        response = self.controller.mvcm.posttest('https://sylp2bcmapp0002.ess.fiserv.one/mvcm-api/automation/servers/ALL_CONSOLES/operations/import-ccs', jsoncontent)

        print(response.status_code)
        print(response.text)

# -------------------------------
# Main Application – Login screen appears immediately
# -------------------------------
class MainApp(tk.Tk):
    def __init__(self, controller):
        super().__init__()
        self.controller = controller
        self.title("Server Selector")
        self.servers = [
            ("DR - Chandler", "qdlp2bcmapp0002.ess.fiserv.one"),
            ("DR - Omaha", "Sylp2bcmapp0002.ess.fiserv.one"),
            ("PROD - Omaha", "Sylp2bcmapp0001.ess.fiserv.one")
        ]
        self.selected_hostname = None
        self.username = None
        self.password = None
        self.geometry("1100x600")
        self.show_login()

    def show_login(self):
        for widget in self.winfo_children():
            widget.destroy()
        self.title("Login")
        default_hostname = self.servers[0][1]
        self.login_panel = LoginPanel(self, default_hostname, on_login=self.on_login)
        self.login_panel.pack(fill=tk.BOTH, expand=True)

    def on_login(self, hostname, username, password):
        self.username = username
        self.password = password
        try:    
            resp = self.controller.loop_logon(username, password, self.servers)
            if resp == 403:
                messagebox.showerror("Log on Failed", f"Incorrect username or password")
                self.show_login()
            elif resp == 200:
                self.show_action_panel()
            else: 
                messagebox.showerror("Log on Failed", f"Unknown 500")
        except Exception as e:
            messagebox.showerror("Log on Failed", f"{str(e)}")

    def show_action_panel(self):
        for widget in self.winfo_children():
            widget.destroy()
        self.title("Manage Saved Configurations")
     #   self.test_code = TestCode(self, self.controller, self.username, self.password,
     #                          self.servers)
     #   self.test_code.pack(fill=tk.BOTH, expand=True)
        self.action_panel = ActionPanel(self, self.controller, self.username, self.password,
                                     self.servers)
        self.action_panel.pack(fill=tk.BOTH, expand=True)

def main():
    mvcm_instance = mvcm.Mvcm()
    controller = BusinessController(mvcm_instance)
    app = MainApp(controller)
    app.mainloop()

if __name__ == "__main__":
    main()
