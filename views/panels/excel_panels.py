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
        self.tree = ttk.Treeview(self.table_frame, show='headings') # Columns set dynamically later
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
        # Use Service to read data
        headers, rows = self.excel_service.read_excel(path, sheet_name=self.sheet_index)
        
        # Reset Tree
        self.tree['columns'] = headers
        for h in headers:
            self.tree.heading(h, text=h)
            self.tree.column(h, width=100)
            
        for item in self.tree.get_children(): self.tree.delete(item)
        for row in rows:
            self.tree.insert("", tk.END, values=row)
            
        self.import_btn.config(state='normal')

    def run_import(self):
        pass # Override in child

# -----------------------------------------------------------------------------
# Create CCS Server Panel
# -----------------------------------------------------------------------------
class CreateFromExcelPanel(ExcelBasePanel):
    def __init__(self, master, server_controller, excel_service, **kwargs):
        self.sheet_index = 0
        self.controller = server_controller
        super().__init__(master, excel_service, **kwargs)

    def run_import(self):
        # 1. Get JSON from Service
        data = self.excel_service.get_json_data()
        
        # 2. Extract names for verification later
        self.server_names = self.excel_service.extract_names(data) # Ensure service has this method
        
        # 3. Create Servers via Controller
        success_count, errors = self.controller.create_ccs_servers_from_json(data)
        
        if not errors:
            messagebox.showinfo("Import Complete", f"Created {success_count} servers.")
            self.ask_verification()
        else:
            messagebox.showwarning("Import Errors", "\n".join(errors))

    def ask_verification(self):
        if messagebox.askyesno("Verify", "Do you want to verify servers (Start & Check Logs)?"):
            self.verify_process()

    def verify_process(self):
        # Progress Window
        prog_win = tk.Toplevel(self)
        prog_win.title("Verifying...")
        pbar = ttk.Progressbar(prog_win, maximum=len(self.server_names))
        pbar.pack(padx=20, pady=20)
        
        success_count = 0
        
        for i, name in enumerate(self.server_names):
            pbar['value'] = i+1
            prog_win.update()
            
            # ASK CONTROLLER (No log parsing here!)
            is_ok, msg = self.controller.verify_server_start(name)
            
            if is_ok:
                success_count += 1
                self.color_row(name, 'success')
            else:
                self.color_row(name, 'failure')
                print(f"Verification failed for {name}: {msg}")

        prog_win.destroy()
        messagebox.showinfo("Verification Done", f"Verified {success_count}/{len(self.server_names)}")

    def color_row(self, server_name, tag):
        # Find row with server name in first column (Column 0)
        for item in self.tree.get_children():
            vals = self.tree.item(item)['values']
            if vals and str(vals[0]) == server_name:
                self.tree.item(item, tags=(tag,))

# -----------------------------------------------------------------------------
# Create Console Panel
# -----------------------------------------------------------------------------
class CreateConsoleFromExcelPanel(ExcelBasePanel):
    def __init__(self, master, server_controller, excel_service, **kwargs):
        self.sheet_index = 1
        self.controller = server_controller
        super().__init__(master, excel_service, **kwargs)

    def run_import(self):
        data = self.excel_service.get_json_data()
        
        # Controller handles the loop and POST
        success_count, errors = self.controller.create_consoles_from_json(data)
        
        if not errors:
            messagebox.showinfo("Success", "Consoles Created")
        else:
            messagebox.showwarning("Errors", "\n".join(errors))
