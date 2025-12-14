import customtkinter as ctk
from tkinter import filedialog
from datetime import datetime
from finance_analyzer.models.transaction import Transaction

class ImportView(ctk.CTkFrame):
    def __init__(self, master, app_instance):
        super().__init__(master)
        self.app = app_instance
        
        self.grid_columnconfigure(0, weight=1)
        self.grid_columnconfigure(1, weight=1)
        
        # --- File Import Section ---
        self.import_label = ctk.CTkLabel(self, text="Import Bank Statement (CSV)", font=ctk.CTkFont(size=16, weight="bold"))
        self.import_label.grid(row=0, column=0, columnspan=2, padx=20, pady=10, sticky="w")
        
        self.btn_import = ctk.CTkButton(self, text="Select CSV File", command=self.select_file)
        self.btn_import.grid(row=1, column=0, columnspan=2, padx=20, pady=10, sticky="ew")
        
        self.status_label = ctk.CTkLabel(self, text="")
        self.status_label.grid(row=2, column=0, columnspan=2, padx=20, pady=5)
        
        # --- Manual Entry Section ---
        ctk.CTkLabel(self, text="Manual Entry", font=ctk.CTkFont(size=16, weight="bold")).grid(row=3, column=0, columnspan=2, padx=20, pady=(20, 10), sticky="w")
        
        ctk.CTkLabel(self, text="Date (YYYY-MM-DD):").grid(row=4, column=0, padx=20, pady=5, sticky="e")
        self.entry_date = ctk.CTkEntry(self)
        self.entry_date.grid(row=4, column=1, padx=20, pady=5, sticky="w")
        self.entry_date.insert(0, datetime.now().strftime("%Y-%m-%d"))

        ctk.CTkLabel(self, text="Description:").grid(row=5, column=0, padx=20, pady=5, sticky="e")
        self.entry_desc = ctk.CTkEntry(self)
        self.entry_desc.grid(row=5, column=1, padx=20, pady=5, sticky="w")

        ctk.CTkLabel(self, text="Amount:").grid(row=6, column=0, padx=20, pady=5, sticky="e")
        self.entry_amount = ctk.CTkEntry(self)
        self.entry_amount.grid(row=6, column=1, padx=20, pady=5, sticky="w")
        
        self.btn_add_manual = ctk.CTkButton(self, text="Add Entry", command=self.add_manual)
        self.btn_add_manual.grid(row=7, column=0, columnspan=2, padx=20, pady=20, sticky="ew")

    def select_file(self):
        file_path = filedialog.askopenfilename(filetypes=[("CSV Files", "*.csv")])
        if file_path:
            count = self.app.data_manager.add_transactions_from_file(file_path)
            self.status_label.configure(text=f"Imported {count} transactions from {file_path.split('/')[-1]}")

    def add_manual(self):
        try:
            date_str = self.entry_date.get()
            desc = self.entry_desc.get()
            amount_str = self.entry_amount.get()
            
            if not date_str or not desc or not amount_str:
                self.status_label.configure(text="Please fill all fields", text_color="red")
                return

            try:
                date_obj = datetime.strptime(date_str, "%Y-%m-%d")
            except ValueError:
                self.status_label.configure(text="Invalid Date Format", text_color="red")
                return
                 
            try:
                amount = float(amount_str)
            except ValueError:
                self.status_label.configure(text="Invalid Amount", text_color="red")
                return
            
            txn = Transaction(date=date_obj, amount=amount, description=desc, source="Manual Entry")
            self.app.data_manager.add_manual_entry(txn)
            self.status_label.configure(text="Manual entry added successfully", text_color="green")
            
            # clear entries
            self.entry_desc.delete(0, 'end')
            self.entry_amount.delete(0, 'end')
            
        except Exception as e:
            self.status_label.configure(text=f"Error: {e}", text_color="red")
