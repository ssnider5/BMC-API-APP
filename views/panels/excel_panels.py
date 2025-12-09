import tkinter as tk
from tkinter import ttk, messagebox, filedialog
import pandas as pd

class ExcelBasePanel(tk.Frame):
    """Shared logic for browsing and showing Excel data"""
    def __init__(self, master, excel_service, **kwargs):
        super().__init__(master, **kwargs)
        self.excel_service = excel_service
        self.file_path_var = tk.StringVar(value="No file selected")
        self.setup_ui()

    def setup_ui(self):
        # Browse Area
        top = ttk.Frame(self)
        top.pack(fill=tk.X, pady=10)
        ttk.Label(top, text="Excel File:").pack(side=tk.LEFT)
        ttk.Entry(top, textvariable=self.file_path_var, state='readonly').pack(side=tk.LEFT, fill=tk.X, expand=True, padx=5)
        ttk.Button(top, text="Browse", command=self.browse).pack(side=tk.LEFT)

        # Table Area
        self.table_frame = ttk.Frame(self)
        self.table_frame.pack(fill=tk.BOTH, expand=True)
        self.tree = ttk.Treeview(self.table_frame, show='headings')
        self.tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        
        # Scrollbars
        vsb = ttk.Scrollbar(self.table_frame, orient="vertical", command=self.tree.yview)
        vsb.pack(side=tk.RIGHT, fill='y')
        self.tree.configure(yscrollcommand=vsb.set)

        # Import Button
        self.import_btn = ttk.Button(self, text="Run Import", command=self.run_import, state='disabled')
        self.import_btn.pack(pady=10)

        # Tags for Colors
        self.tree.tag_configure('success', background='#90EE90')
        self.tree.tag_configure('failure', background='#FFCCCB')

    def browse(self):
        path = filedialog.askopenfilename(filetypes=[("Excel files", "*.xlsx *.xls")])
        if path:
            self.file_path_var.set(path)
            self.load_preview(path)

    def load_preview(self, path):
        headers, rows = self.excel_service.read_excel(path, sheet_name=self.sheet_index)
        
        self.tree['columns'] = headers
        for h in headers:
            self.tree.heading(h, text=h)
            self.tree.column(h, width=100)
            
        for item in self.tree.get_children(): self.tree.delete(item)
        for row in rows:
            self.tree.insert("", tk.END, values=row)
            
        self.import_btn.config(state='normal')

    def color_row(self, identifier, tag, col_idx=0):
        """
        Colors a row based on a value in a specific column.
        """
        for item in self.tree.get_children():
            vals = self.tree.item(item)['values']
            # Convert both to string to ensure safe comparison
            if vals and str(vals[col_idx]) == str(identifier):
                # FIX: Remove old tags first so the new color takes effect
                self.tree.item(item, tags=()) 
                self.tree.item(item, tags=(tag,))
                # Force update to ensure color renders immediately
                self.update_idletasks()

    def run_import(self):
        pass 

# -----------------------------------------------------------------------------
# Create CCS Server Panel (Verification Removed)
# -----------------------------------------------------------------------------
class CreateFromExcelPanel(ExcelBasePanel):
    def __init__(self, master, server_controller, excel_service, **kwargs):
        self.sheet_index = 0
        self.controller = server_controller
        super().__init__(master, excel_service, **kwargs)

    def run_import(self):
        data = self.excel_service.get_json_data()
        success_count, errors = self.controller.create_ccs_servers_from_json(data)
        
        if not errors:
            messagebox.showinfo("Import Complete", f"Created {success_count} servers.")
        else:
            messagebox.showwarning("Import Errors", "\n".join(errors))

# -----------------------------------------------------------------------------
# Create Console Panel (Verification Added Here)
# -----------------------------------------------------------------------------
class CreateConsoleFromExcelPanel(ExcelBasePanel):
    def __init__(self, master, server_controller, excel_service, **kwargs):
        self.sheet_index = 1
        self.controller = server_controller
        super().__init__(master, excel_service, **kwargs)

    def run_import(self):
        data = self.excel_service.get_json_data()
        
        # 1. Create Consoles
        success_count, errors = self.controller.create_consoles_from_json(data)
        
        if errors:
            messagebox.showwarning("Creation Errors", "\n".join(errors))
            return # Don't verify if creation failed heavily
            
        messagebox.showinfo("Success", f"Created {success_count} consoles.")
        
        # 2. Ask to Verify
        if messagebox.askyesno("Verify", "Do you want to run network diagnostics on these consoles?"):
            self.verify_consoles(data)

    def verify_consoles(self, json_data):
        # Progress Window
        prog_win = tk.Toplevel(self)
        prog_win.title("Running Diagnostics...")
        pbar = ttk.Progressbar(prog_win, maximum=len(json_data))
        pbar.pack(padx=20, pady=20)
        
        lbl = ttk.Label(prog_win, text="Initializing...")
        lbl.pack(pady=5)
        
        passed = 0
        
        for i, row in enumerate(json_data):
            # We need to extract the specific fields for verification
            # row is a dictionary from the excel service
            
            # Note: create_consoles_from_json modifies the list in place in the controller
            # but we passed a copy or we re-read the data. 
            # To be safe, we use the raw data from excel_service again or rely on the fact
            # that we need 'Server' (hostname) and 'name' (luName) and 'Port'.
            
            host = row.get('hostname') # You said "hostname being the ccs server hostname" - check your excel column name
            # If your excel column is "Server", use that.
            if not host: host = row.get('Server') 
            
            lu_name = row.get('name')
            port = row.get('Port')
            
            lbl.config(text=f"Checking {lu_name}...")
            pbar['value'] = i+1
            prog_win.update()

            if host and lu_name:
                is_connected, msg = self.controller.verify_console_connectivity(host, lu_name, port)
                
                # Update UI Color
                # We color based on the 'name' column which is index 0 in the tree usually?
                # Actually, check your excel headers. 
                # Assuming 'name' (LU Name) is unique enough for this list.
                if is_connected:
                    self.color_row(lu_name, 'success', col_idx=1) # Assuming Name is column 1. Adjust if needed.
                    passed += 1
                else:
                    self.color_row(lu_name, 'failure', col_idx=1)
                    print(f"Diagnostics failed for {lu_name}: {msg}")
            
        prog_win.destroy()
        messagebox.showinfo("Verification Complete", f"Diagnostics Passed: {passed}/{len(json_data)}")
