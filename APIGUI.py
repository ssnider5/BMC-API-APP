import tkinter as tk
from tkinter import ttk
from tkinter import filedialog
import mvcm
import json
import os

class App:
    def __init__(self, root):
        self.root = root
        self.root.title("Server Selector")
        self.selected_hostname = None
        self.username = None
        self.password = None
        self.is_login_screen = False
        self.saved_configs = None
        self.selected_config_name = None

        # Create the table
        self.tree = ttk.Treeview(root, columns=("Environment", "Hostname"), show='headings')
        self.tree.heading("Environment", text="Environment")
        self.tree.heading("Hostname", text="Hostname")
        self.tree.pack()

        # Add a button to select the row
        self.select_button = tk.Button(root, text="Select Row", command=self.select_row)
        self.select_button.pack()

        # Add a label to display the selected hostname
        self.selected_label = tk.Label(root, text="Selected Hostname: None")
        self.selected_label.pack()

        # Bind number keys and Enter key
        self.root.bind('<Return>', self.enter_key)
        self.root.bind('<KeyPress>', self.handle_keypress)

    def handle_keypress(self, event):
        if self.is_login_screen:
            return
        if event.char.isdigit():
            index = int(event.char)
            if index == 0:  # Skip if 0 is pressed
                return
            children = self.tree.get_children()
            if 1 <= index <= len(children):  # Check if index (starting from 1) is valid
                self.tree.selection_set(children[index-1])  # Subtract 1 to convert to 0-based index
                self.tree.focus_set()
                self.tree.focus(children[index-1])

    def add_row(self, environment="Environment", hostname="Hostname"):
        # Add row number prefix to environment (starting from 1)
        row_num = len(self.tree.get_children()) + 1
        labeled_environment = f"{row_num}: {environment}"
        self.tree.insert("", "end", values=(labeled_environment, hostname))

    def enter_key(self, event):
        if not self.is_login_screen:
            self.select_row()
        else:
            self.login()

    def select_row(self):
        selected_item = self.tree.selection()
        if selected_item:
            item = self.tree.item(selected_item)
            self.selected_hostname = item['values'][1]
            self.selected_label.config(text=f"Selected Hostname: {self.selected_hostname}")
            self.show_login_screen()

    def show_login_screen(self):
        self.is_login_screen = True
        
        # Clear the current window
        for widget in self.root.winfo_children():
            widget.destroy()

        self.root.title("Login")

        # Create username and password labels and entries
        tk.Label(self.root, text="Username").pack()
        self.username_entry = tk.Entry(self.root)
        self.username_entry.pack()

        tk.Label(self.root, text="Password").pack()
        self.password_entry = tk.Entry(self.root, show="*")
        self.password_entry.pack()

        # Add a login button
        self.login_button = tk.Button(self.root, text="Login", command=self.login)
        self.login_button.pack()

        # Bind Enter key for login screen
        self.root.bind('<Return>', self.enter_key)

    def login(self):
        self.username = self.username_entry.get()
        self.password = self.password_entry.get()
        m.connect(self.selected_hostname, self.username, self.password)
        r = m.get("/saved-configurations", "application/json")
        self.saved_configs = r.json()
        self.show_action_screen()

    def show_action_screen(self):
        # Clear the current window
        for widget in self.root.winfo_children():
            widget.destroy()

        self.root.title("Action Selection")

        # Create main frame
        main_frame = ttk.Frame(self.root)
        main_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)

        # Add the question label
        ttk.Label(main_frame, text="What would you like to do today?").pack(pady=20)

        # Create the dropdown
        self.action_var = tk.StringVar()
        self.action_dropdown = ttk.Combobox(main_frame, textvariable=self.action_var, state='readonly')
        self.action_dropdown['values'] = ('', 'Download')
        self.action_dropdown.pack(pady=10)

        # Bind dropdown selection change
        self.action_dropdown.bind('<<ComboboxSelected>>', self.on_action_selected)

        # Create frame for configurations table (initially empty)
        self.config_frame = ttk.Frame(main_frame)
        self.config_frame.pack(fill=tk.BOTH, expand=True, pady=20)

        # Add the Download button (changed from Next)
        self.download_button = tk.Button(main_frame, text="Download", command=self.process_action)
        self.download_button.pack(pady=20)

        # Bind Enter key to process_action
        self.root.bind('<Return>', lambda e: self.process_action())



    def show_action_screen(self):
        # Clear the current window
        for widget in self.root.winfo_children():
            widget.destroy()

        self.root.title("Action Selection")

        # Create main frame
        main_frame = ttk.Frame(self.root)
        main_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)

        # Add the question label
        ttk.Label(main_frame, text="What would you like to do today?").pack(pady=20)

        # Create the dropdown
        self.action_var = tk.StringVar()
        self.action_dropdown = ttk.Combobox(main_frame, textvariable=self.action_var, state='readonly')
        self.action_dropdown['values'] = ('', 'Download', 'Upload', 'Restore')  # Added Restore option
        self.action_dropdown.pack(pady=10)

        # Bind dropdown selection change
        self.action_dropdown.bind('<<ComboboxSelected>>', self.on_action_selected)

        # Create frame for configurations table (initially empty)
        self.config_frame = ttk.Frame(main_frame)
        self.config_frame.pack(fill=tk.BOTH, expand=True, pady=20)

        # Create frame for the action button
        self.button_frame = ttk.Frame(main_frame)
        self.button_frame.pack(pady=20)

    def on_action_selected(self, event):
        # Clear existing widgets in config_frame and button_frame
        for widget in self.config_frame.winfo_children():
            widget.destroy()
        for widget in self.button_frame.winfo_children():
            widget.destroy()

        selected_action = self.action_var.get()

        if selected_action in ['Download', 'Restore']:  # Handle both Download and Restore similarly
            # Create a container frame for both table and download location
            container_frame = ttk.Frame(self.config_frame)
            container_frame.pack(fill=tk.BOTH, expand=True)

            # Create refresh button frame
            refresh_frame = ttk.Frame(container_frame)
            refresh_frame.pack(fill=tk.X, pady=(0, 10))

            # Add refresh button
            def refresh_configs():
                try:
                    # Call the API to get updated configurations
                    r = m.get("/saved-configurations", "application/json")
                    if r.ok:
                        self.saved_configs = r.json()
                        
                        # Clear existing items in the table
                        for item in self.config_tree.get_children():
                            self.config_tree.delete(item)
                        
                        # Repopulate with new data
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

            refresh_button = ttk.Button(refresh_frame, text="↻ Refresh", command=refresh_configs)
            refresh_button.pack(side=tk.RIGHT, padx=5)

            # Create table frame
            table_frame = ttk.Frame(container_frame)
            table_frame.pack(fill=tk.BOTH, expand=True, pady=(0, 10))

            # Create configurations table
            self.config_tree = ttk.Treeview(table_frame, 
                                    columns=("Number", "Name", "Description", "Date", "User"),
                                    show='headings')
        
            # Define column headings
            self.config_tree.heading("Number", text="#")
            self.config_tree.heading("Name", text="Name")
            self.config_tree.heading("Description", text="Description")
            self.config_tree.heading("Date", text="Date")
            self.config_tree.heading("User", text="User")

            # Set column widths
            self.config_tree.column("Number", width=50)
            self.config_tree.column("Name", width=200)
            self.config_tree.column("Description", width=400)
            self.config_tree.column("Date", width=100)
            self.config_tree.column("User", width=100)

            # Add scrollbar
            scrollbar = ttk.Scrollbar(table_frame, orient=tk.VERTICAL, command=self.config_tree.yview)
            self.config_tree.configure(yscrollcommand=scrollbar.set)

            # Pack the table and scrollbar
            self.config_tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
            scrollbar.pack(side=tk.RIGHT, fill=tk.Y)

            if selected_action == 'Download':
                # Create download location frame
                download_frame = ttk.Frame(container_frame)
                download_frame.pack(fill=tk.X, pady=(10, 0))

                # Add download location label and entry
                ttk.Label(download_frame, text="Download Location:").pack(side=tk.LEFT, padx=(0, 10))
                self.download_location = tk.StringVar()
                self.download_location.set(fr"C:\Users\{self.username}\OneDrive - Fiserv Corp\Documents\saved_configuration.zip")
                self.download_entry = ttk.Entry(download_frame, textvariable=self.download_location, width=80)
                self.download_entry.pack(side=tk.LEFT, fill=tk.X, expand=True)

                # Add the Download button in the button_frame
                self.download_button = tk.Button(self.button_frame, text="Download", command=self.process_action)
                self.download_button.pack()
            else:  # Restore action
                # Add the Restore button in the button_frame
                self.restore_button = tk.Button(self.button_frame, text="Restore", command=self.process_action)
                self.restore_button.pack()

            # Bind Enter key to process_action
            self.root.bind('<Return>', lambda e: self.process_action())

            # Populate table with configurations
            if self.saved_configs:
                for idx, config in enumerate(self.saved_configs, 1):
                    self.config_tree.insert("", tk.END, values=(
                        str(idx),
                        config['name'],
                        config['description'],
                        config['date'],
                        config['user']
                    ))

            # Bind number keys for config selection
            def handle_config_number_key(event):
                if event.char.isdigit():
                    index = int(event.char)
                    if 1 <= index <= len(self.saved_configs):
                        children = self.config_tree.get_children()
                        # Clear previous selection
                        self.config_tree.selection_remove(self.config_tree.selection())
                        # Select the row
                        self.config_tree.selection_set(children[index-1])
                        self.config_tree.focus(children[index-1])
                        # Store the selected config name
                        selected_item = self.config_tree.item(children[index-1])
                        self.selected_config_name = selected_item['values'][1]  # Name is in the second column

            # Bind selection event
            def on_select(event):
                selected_items = self.config_tree.selection()
                if selected_items:
                    item = self.config_tree.item(selected_items[0])
                    self.selected_config_name = item['values'][1]  # Name is in the second column

            # Bind the events
            self.root.bind('<KeyPress>', handle_config_number_key)
            self.config_tree.bind('<<TreeviewSelect>>', on_select)

        elif selected_action == 'Upload':
            # Create upload frame
            upload_frame = ttk.Frame(self.config_frame)
            upload_frame.pack(fill=tk.BOTH, expand=True)

            # Create file selection frame
            file_frame = ttk.Frame(upload_frame)
            file_frame.pack(fill=tk.X, pady=20)

            # Add file path label and entry
            ttk.Label(file_frame, text="Selected File:").pack(side=tk.LEFT, padx=(0, 10))
            self.file_path = tk.StringVar()
            self.file_entry = ttk.Entry(file_frame, textvariable=self.file_path, width=60)
            self.file_entry.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=(0, 10))

            # Add browse button
            def browse_file():
                filename = filedialog.askopenfilename(
                    title="Select a ZIP file",
                    filetypes=[("ZIP files", "*.zip")]
                )
                if filename:
                    self.file_path.set(filename)

            browse_button = ttk.Button(file_frame, text="Browse", command=browse_file)
            browse_button.pack(side=tk.LEFT)

            # Add the Upload button in the button_frame
            self.upload_button = tk.Button(
                self.button_frame,
                text="Upload",
                command=self.process_action,
                state=tk.DISABLED  # Initially disabled until file is selected
            )
            self.upload_button.pack()

            # Enable/disable upload button based on file selection
            def on_file_path_change(*args):
                if self.file_path.get():
                    self.upload_button.config(state=tk.NORMAL)
                else:
                    self.upload_button.config(state=tk.DISABLED)

            self.file_path.trace('w', on_file_path_change)

    def process_action(self):
        selected_action = self.action_var.get()
        if selected_action == 'Download' and self.selected_config_name:
            print(f"Selected configuration: {self.selected_config_name}")
            # Add your download logic here using self.selected_config_name
            r = m.getzip('/saved-configurations/' + self.selected_config_name, 'zip')
            if r.status_code == 200:
                # Save the ZIP file content using the custom download location
                zip_file_path = self.download_location.get()
                with open(zip_file_path, 'wb') as f:
                    f.write(r.content)
                print(f'Successfully downloaded the ZIP file to {zip_file_path}')
            else:
                print(f'Failed to retrieve configurations. Status code: {r.status_code}')

        elif selected_action == 'Upload':
            selected_file = self.file_path.get()
            if selected_file:
                print(f"Selected file for upload: {selected_file}")
                try:
                    # Get just the filename without path 
                    filename = os.path.basename(selected_file)

                    # Create file parameter
                    files = {'file': (filename, open(selected_file, 'rb'))}
                    
                    print("Uploading file...")
                    
                    # Send the file
                    response = m.postbinary('/saved-configurations', selected_file)
                    
                    if response.ok:
                        print("Upload successful!")
                    else:
                        print(f"Upload failed with status code: {response.status_code}")
                        print(f"Error message: {response.text}")
                        
                except Exception as e:
                    print(f"Error during upload: {str(e)}")
        
        elif selected_action == 'Restore' and self.selected_config_name:
            print(f"Restoring configuration: {self.selected_config_name}")
            # Add your restore logic here using self.selected_config_name
            # For example:
            try:
                response = m.post(f'/saved-configurations/{self.selected_config_name}/operations/restore', None)
                if response.ok:
                    print("Restore successful!")
                else:
                    print(f"Restore failed with status code: {response.status_code}")
                    print(f"Error message: {response.text}")
            except Exception as e:
                print(f"Error during restore: {str(e)}")

if __name__ == "__main__":
    m = mvcm.Mvcm()
    root = tk.Tk()
    app = App(root)
    app.add_row("DR - Chandler", "qdlp2bcmapp0002.ess.fiserv.one")
    root.mainloop()