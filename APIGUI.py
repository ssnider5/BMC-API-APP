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
        self.servers = []
        
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
        # Store the server info
        self.servers.append((environment, hostname))

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

        self.root.title("Manage Saved Configurations")

        # Create main frame
        main_frame = ttk.Frame(self.root)
        main_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)

        # Add the question label
        ttk.Label(main_frame, text="What would you like to do today?").pack(pady=20)

        # Create the dropdown
        self.action_var = tk.StringVar()
        self.action_dropdown = ttk.Combobox(main_frame, textvariable=self.action_var, state='readonly')
        self.action_dropdown['values'] = ('', 'Download', 'Upload', 'Restore', 'Create', 'Update')  # Added Update option
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


        elif selected_action == 'Create':
            # Create frame for the create form
            create_frame = ttk.Frame(self.config_frame)
            create_frame.pack(fill=tk.BOTH, expand=True, pady=20)

            # Name field
            name_frame = ttk.Frame(create_frame)
            name_frame.pack(fill=tk.X, pady=(0, 10))
            ttk.Label(name_frame, text="Name:").pack(side=tk.LEFT, padx=(0, 10))
            self.create_name = tk.StringVar()
            name_entry = ttk.Entry(name_frame, textvariable=self.create_name, width=60)
            name_entry.pack(side=tk.LEFT, fill=tk.X, expand=True)

            # Description field
            desc_frame = ttk.Frame(create_frame)
            desc_frame.pack(fill=tk.X, pady=(0, 10))
            ttk.Label(desc_frame, text="Description:").pack(side=tk.LEFT, padx=(0, 10))
            self.create_description = tk.StringVar()
            desc_entry = ttk.Entry(desc_frame, textvariable=self.create_description, width=60)
            desc_entry.pack(side=tk.LEFT, fill=tk.X, expand=True)

            # Add the Create button in the button_frame
            self.create_button = tk.Button(
                self.button_frame,
                text="Create",
                command=self.process_action
            )
            self.create_button.pack()

            # Bind Enter key to process_action
            self.root.bind('<Return>', lambda e: self.process_action())

        elif selected_action == 'Update':
            # Create a container frame for both tables
            container_frame = ttk.Frame(self.config_frame)
            container_frame.pack(fill=tk.BOTH, expand=True)

            # Create frames for source and target tables
            source_frame = ttk.Frame(container_frame)
            source_frame.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=5)
            
            target_frame = ttk.Frame(container_frame)
            target_frame.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=5)

            # Add titles for both tables
            ttk.Label(source_frame, text="Source (The server of the save config we want to copy)", 
                    font=('TkDefaultFont', 10, 'bold')).pack(pady=5)
            ttk.Label(target_frame, text="Target (The server that we want to update)", 
                    font=('TkDefaultFont', 10, 'bold')).pack(pady=5)

            # Create source table
            source_tree = ttk.Treeview(source_frame, columns=("Number", "Environment", "Hostname"), show='headings')
            source_tree.heading("Number", text="#")
            source_tree.heading("Environment", text="Environment")
            source_tree.heading("Hostname", text="Hostname")
            source_tree.column("Number", width=50)
            source_tree.column("Environment", width=150)
            source_tree.column("Hostname", width=300)
            source_tree.pack(fill=tk.BOTH, expand=True)

            # Create target table
            target_tree = ttk.Treeview(target_frame, columns=("Number", "Environment", "Hostname"), show='headings')
            target_tree.heading("Number", text="#")
            target_tree.heading("Environment", text="Environment")
            target_tree.heading("Hostname", text="Hostname")
            target_tree.column("Number", width=50)
            target_tree.column("Environment", width=150)
            target_tree.column("Hostname", width=300)
            target_tree.pack(fill=tk.BOTH, expand=True)

            # Store selected hostnames
            self.source_hostname = None
            self.target_hostname = None

            # Add selection handlers
            def on_source_select(event):
                selected_items = source_tree.selection()
                if selected_items:
                    item = source_tree.item(selected_items[0])
                    self.source_hostname = item['values'][2]  # Hostname is now in third column
                    print(f"Selected source hostname: {self.source_hostname}")

            def on_target_select(event):
                selected_items = target_tree.selection()
                if selected_items:
                    item = target_tree.item(selected_items[0])
                    self.target_hostname = item['values'][2]  # Hostname is now in third column
                    print(f"Selected target hostname: {self.target_hostname}")

            # Bind selection events
            source_tree.bind('<<TreeviewSelect>>', on_source_select)
            target_tree.bind('<<TreeviewSelect>>', on_target_select)

            # Populate both tables with server list
            for idx, (env, hostname) in enumerate(self.servers, 1):
                source_tree.insert("", tk.END, values=(str(idx), env, hostname))
                target_tree.insert("", tk.END, values=(str(idx), env, hostname))

            # Add number key handling for source table
            def handle_source_number_key(event):
                if event.char.isdigit():
                    index = int(event.char)
                    if 1 <= index <= len(self.servers):
                        children = source_tree.get_children()
                        source_tree.selection_set(children[index-1])
                        source_tree.focus(children[index-1])
                        self.source_hostname = self.servers[index-1][1]  # Get hostname
                        check_selection_status()

            # Add number key handling for target table
            def handle_target_number_key(event):
                if event.char.isdigit() and event.state & 0x1:  # Check if Shift is pressed
                    index = int(event.char)
                    if 1 <= index <= len(self.servers):
                        children = target_tree.get_children()
                        target_tree.selection_set(children[index-1])
                        target_tree.focus(children[index-1])
                        self.target_hostname = self.servers[index-1][1]  # Get hostname
                        check_selection_status()

            # Bind number keys
            self.root.bind('<KeyPress>', handle_source_number_key)
            self.root.bind('<KeyPress>', handle_target_number_key, add='+')

            # Add Update button in button frame
            self.update_button = tk.Button(
                self.button_frame,
                text="Update",
                command=self.process_action,
                state=tk.DISABLED  # Initially disabled until both source and target are selected
            )
            self.update_button.pack()

            # Add handler to enable/disable update button
            def check_selection_status(*args):
                if self.source_hostname and self.target_hostname:
                    self.update_button.config(state=tk.NORMAL)
                else:
                    self.update_button.config(state=tk.DISABLED)

            # Bind selection events to check status
            source_tree.bind('<<TreeviewSelect>>', lambda e: (on_source_select(e), check_selection_status()))
            target_tree.bind('<<TreeviewSelect>>', lambda e: (on_target_select(e), check_selection_status()))



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

        
        elif selected_action == 'Create':
            name = self.create_name.get()
            description = self.create_description.get()
            
            if name:
                print(f"Creating configuration with name: {name}")
                try:
                    # Create the request body
                    data = {
                        "name": name,
                        "description": description if description else None
                    }
                    
                    # Send the create request
                    response = m.post('/saved-configurations/' + name, data)
                    
                    if response.ok:
                        print("Configuration created successfully!")
                        # Optional: Clear the fields after successful creation
                        self.create_name.set("")
                        self.create_description.set("")
                    else:
                        print(f"Creation failed with status code: {response.status_code}")
                        print(f"Error message: {response.text}")
                        
                except Exception as e:
                    print(f"Error during creation: {str(e)}")
            else:
                print("Name is required for creation")

        
        elif selected_action == 'Update':
            if self.source_hostname and self.target_hostname:
                print(f"Updating configuration from {self.source_hostname} to {self.target_hostname}")
                try:
                    print(f"Source server: {self.source_hostname}")
                    print(f"Target server: {self.target_hostname}")
                    
                    # Create directories if they don't exist
                    user_docs = os.path.join(os.path.expanduser('~'), "OneDrive - Fiserv Corp", "Documents", "MergedSaveConfig")
                    source_dir = os.path.join(user_docs)
                    target_dir = os.path.join(user_docs)
                    
                    os.makedirs(source_dir, exist_ok=True)
                    os.makedirs(target_dir, exist_ok=True)

                    # Create separate connections for source and target
                    source_connection = mvcm.Mvcm()
                    target_connection = mvcm.Mvcm()

                    source_connection.connect(self.source_hostname, self.username, self.password)
                    target_connection.connect(self.target_hostname, self.username, self.password)
                    
                    # Download configurations
                    source_response = source_connection.getzip('/saved-configurations/source_Merge', 'zip')
                    target_response = target_connection.getzip('/saved-configurations/target_Merge', 'zip')

                    # Save the downloaded zip files
                    source_zip = os.path.join(source_dir, "source_Merge.zip")
                    target_zip = os.path.join(target_dir, "target_Merge.zip")

                    # Save files with proper file handling
                    with open(source_zip, 'wb') as f:
                        f.write(source_response.content)
                    with open(target_zip, 'wb') as f:
                        f.write(target_response.content)

                    # Perform the merge
                    merged_zip_path = source_connection.merge_configurations(
                        self.username,
                        self.source_hostname,
                        self.target_hostname
                        )
                    
                    # Upload merged configuration to target server
                    if os.path.exists(merged_zip_path):
                        print("Uploading merged configuration to target server...")
                        try:
                            # Get just the filename without path 
                            filename = os.path.basename(merged_zip_path)
                            
                            print(f"Uploading merged file: {merged_zip_path}")
                            
                            # Send the file
                            response = target_connection.postbinary('/saved-configurations', merged_zip_path)
                            
                            if response.ok:
                                print("Merged configuration uploaded successfully!")
                            else:
                                print(f"Upload failed with status code: {response.status_code}")
                                print(f"Error message: {response.text}")
                                
                        except Exception as e:
                            print(f"Error during upload: {str(e)}")

                    print("Update process completed successfully!")

                except Exception as e:
                    print(f"Error during update: {str(e)}")
                finally:
                    # Cleanup temporary files
                    try:
                        if os.path.exists(merged_zip_path):
                            os.remove(merged_zip_path)
                    except:
                        pass
            else:
                print("Both source and target servers must be selected")



if __name__ == "__main__":
    m = mvcm.Mvcm()
    root = tk.Tk()
    app = App(root)
    app.add_row("DR - Chandler", "qdlp2bcmapp0002.ess.fiserv.one")
    app.add_row("DR - Omaha", "Sylp2bcmapp0002.ess.fiserv.one")
    root.mainloop()