import tkinter as tk
from tkinter import ttk
import mvcm
import json

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
                self.select_row()

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

        # Add the Next button
        self.next_button = tk.Button(main_frame, text="Next", command=self.process_action)
        self.next_button.pack(pady=20)

        self.root.bind('<Return>', self.enter_key)

    def on_action_selected(self, event):
        # Clear existing widgets in config_frame
        for widget in self.config_frame.winfo_children():
            widget.destroy()

        if self.action_var.get() == 'Download':
            # Create configurations table
            self.config_tree = ttk.Treeview(self.config_frame, 
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
            scrollbar = ttk.Scrollbar(self.config_frame, orient=tk.VERTICAL, command=self.config_tree.yview)
            self.config_tree.configure(yscrollcommand=scrollbar.set)

            # Pack the table and scrollbar
            self.config_tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
            scrollbar.pack(side=tk.RIGHT, fill=tk.Y)

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

    def process_action(self):
        selected_action = self.action_var.get()
        if selected_action == 'Download' and self.selected_config_name:
            print(f"Selected configuration: {self.selected_config_name}")
            # Add your download logic here using self.selected_config_name
            r = m.getzip('/saved-configurations/' + self.selected_config_name, 'zip')
            if r.status_code == 200:
                # Save the ZIP file content
                zip_file_path = fr"C:\Users\{self.username}\OneDrive - Fiserv Corp\Documents\BMC API\saved_configurations.zip"
                with open(zip_file_path, 'wb') as f:
                    f.write(r.content)
                print(f'Successfully downloaded the ZIP file to {zip_file_path}')
            else:
                print(f'Failed to retrieve configurations. Status code: {r.status_code}')

print('==================================================')

if __name__ == "__main__":
    m = mvcm.Mvcm()
    root = tk.Tk()
    app = App(root)
    app.add_row("DR - Chandler", "qdlp2bcmapp0002.ess.fiserv.one")
    root.mainloop()