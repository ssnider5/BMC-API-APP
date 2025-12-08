import tkinter as tk
from tkinter import ttk

class LoadingDialog(tk.Toplevel):
    def __init__(self, parent, message="Processing..."):
        super().__init__(parent)
        self.title("Loading")
        self.transient(parent)
        self.grab_set()
        self.overrideredirect(True)
        
        # Center the dialog
        window_width = 300
        window_height = 100
        screen_width = parent.winfo_screenwidth()
        screen_height = parent.winfo_screenheight()
        x = (screen_width - window_width) // 2
        y = (screen_height - window_height) // 2
        self.geometry(f'{window_width}x{window_height}+{x}+{y}')
        
        main_frame = ttk.Frame(self, relief='raised', borderwidth=2)
        main_frame.pack(fill=tk.BOTH, expand=True, padx=2, pady=2)
        
        self.message_label = ttk.Label(main_frame, text=message)
        self.message_label.pack(pady=10)
        
        self.progress_bar = ttk.Progressbar(main_frame, mode='indeterminate', length=200)
        self.progress_bar.pack(pady=10)
        self.progress_bar.start(10)
        
        self.focus_force()

    def stop(self):
        self.destroy()
