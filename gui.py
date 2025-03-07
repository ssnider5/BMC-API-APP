import tkinter as tk
from tkinter import ttk, filedialog
import os
import mvcm
from business import BusinessController
from business import ExcelParser
import threading
from tkinter import messagebox
from tkinter import PhotoImage

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
            success = self.controller.download_configuration(self.selected_config_name, dl_location)
            if success:
                print(f"Successfully downloaded the ZIP file to {dl_location}")
            else:
                print("Download failed.")
        elif self.action == 'Restore' and self.selected_config_name:
            success = self.controller.restore_configuration(self.selected_config_name)
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
            print("Configuration created successfully!" if success else "Creation failed.")
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
        self.import_button.pack(side=tk.RIGHT, padx=5)

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
            self.excel_parser.create_ccs_server(self.mvcm_inst, json)
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
        options = ["Saved Configurations", "CCS Server"]
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
        options = ["Create from Excel"]
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
            ("DR - Omaha", "Sylp2bcmapp0002.ess.fiserv.one")
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
        self.controller.connect(hostname, username, password)
        self.show_action_panel()

    def show_action_panel(self):
        for widget in self.winfo_children():
            widget.destroy()
        self.title("Manage Saved Configurations")
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