import tkinter as tk
from tkinter import ttk

class LoginPanel(tk.Frame):
    def __init__(self, master, default_hostname, on_login_callback, **kwargs):
        super().__init__(master, **kwargs)
        self.hostname = default_hostname
        self.on_login = on_login_callback
        self.create_widgets()

    def create_widgets(self):
        container = ttk.Frame(self)
        container.pack(expand=True)

        ttk.Label(container, text="Username").pack(pady=5)
        self.username_entry = ttk.Entry(container)
        self.username_entry.pack(pady=5)

        ttk.Label(container, text="Password").pack(pady=5)
        self.password_entry = ttk.Entry(container, show="*")
        self.password_entry.pack(pady=5)

        self.login_button = ttk.Button(container, text="Login", command=self.login)
        self.login_button.pack(pady=10)

        self.master.bind('<Return>', lambda e: self.login())

    def login(self):
        username = self.username_entry.get()
        password = self.password_entry.get()
        self.on_login(self.hostname, username, password)
