import customtkinter as ctk
import tkinter as tk
from tkinter import ttk, messagebox

class RulesView(ctk.CTkFrame):
    def __init__(self, master, app_instance):
        super().__init__(master)
        self.app = app_instance
        
        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(2, weight=1)
        
        # --- Add Rule Form ---
        form_frame = ctk.CTkFrame(self)
        form_frame.grid(row=0, column=0, sticky="ew", padx=10, pady=10)
        
        ctk.CTkLabel(form_frame, text="Keyword:").pack(side="left", padx=5)
        self.entry_keyword = ctk.CTkEntry(form_frame, width=150)
        self.entry_keyword.pack(side="left", padx=5)
        
        ctk.CTkLabel(form_frame, text="Category:").pack(side="left", padx=5)
        self.entry_category = ctk.CTkEntry(form_frame, width=150)
        self.entry_category.pack(side="left", padx=5)
        
        self.var_regex = ctk.BooleanVar()
        self.check_regex = ctk.CTkCheckBox(form_frame, text="Is Regex", variable=self.var_regex)
        self.check_regex.pack(side="left", padx=10)
        
        self.btn_add = ctk.CTkButton(form_frame, text="Add Rule", command=self.add_rule)
        self.btn_add.pack(side="left", padx=10)
        
        # --- Actions ---
        action_frame = ctk.CTkFrame(self)
        action_frame.grid(row=1, column=0, sticky="ew", padx=10, pady=(0, 10))
        
        self.btn_apply = ctk.CTkButton(action_frame, text="Apply Rules to Data (Re-Run)", command=self.apply_rules)
        self.btn_apply.pack(side="left", padx=10, pady=10)
        
        self.btn_delete = ctk.CTkButton(action_frame, text="Delete Selected Rule", command=self.delete_selected_rule, fg_color="#d63031", hover_color="#b71c1c")
        self.btn_delete.pack(side="right", padx=10, pady=10)
        
        # --- Table ---
        self._setup_tree()
        self.refresh_table()

    def _setup_tree(self):
        style = ttk.Style()
        style.theme_use("default")
        
        columns = ("ID", "Keyword", "Category", "Is Regex")
        self.tree = ttk.Treeview(self, columns=columns, show="headings")
        
        self.tree.heading("Keyword", text="Keyword")
        self.tree.heading("Category", text="Category")
        self.tree.heading("Is Regex", text="Is Regex")
        self.tree.column("ID", width=0, stretch=False)
        self.tree.column("Keyword", width=200)
        self.tree.column("Category", width=150)
        self.tree.column("Is Regex", width=80)
        
        self.tree.grid(row=2, column=0, sticky="nsew", padx=10, pady=5)
        
        scrollbar = ttk.Scrollbar(self, orient="vertical", command=self.tree.yview)
        scrollbar.grid(row=2, column=1, sticky="ns", pady=5)
        self.tree.configure(yscrollcommand=scrollbar.set)

    def refresh_table(self):
        for item in self.tree.get_children():
            self.tree.delete(item)
            
        rules = self.app.rule_engine.rules
        for rule in rules:
            self.tree.insert("", "end", values=(rule.id, rule.keyword, rule.category, "Yes" if rule.is_regex else "No"))

    def add_rule(self):
        keyword = self.entry_keyword.get()
        category = self.entry_category.get()
        is_regex = self.var_regex.get()
        
        if keyword and category:
            # This triggers reapply_all inside rule_engine
            self.app.rule_engine.add_rule(keyword, category, is_regex)
            self.entry_keyword.delete(0, ct.END) if hasattr(ctk, 'END') else self.entry_keyword.delete(0, 'end')
            self.entry_category.delete(0, 'end')
            self.refresh_table()
            print("Rule added and rules re-applied.")
        else:
            print("Keyword and Category required.")

    def delete_selected_rule(self):
        selected = self.tree.selection()
        if not selected:
            return
            
        item = self.tree.item(selected)
        rule_id = item['values'][0]
        
        # This triggers reapply_all inside rule_engine
        self.app.rule_engine.delete_rule(rule_id)
        self.refresh_table()
        print(f"Rule {rule_id} deleted and rules re-applied.")

    def apply_rules(self):
        # Explicit re-run
        self.app.rule_engine.reapply_all()
        print("Rules re-applied to all data.")
