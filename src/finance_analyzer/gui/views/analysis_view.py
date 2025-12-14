import customtkinter as ctk
import tkinter as tk
from tkinter import ttk
import pandas as pd
from tkinter import filedialog
from finance_analyzer.core.exporter import export_to_excel

class AnalysisView(ctk.CTkFrame):
    def __init__(self, master, app_instance):
        super().__init__(master)
        self.app = app_instance
        
        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(1, weight=1) 
        
        # --- Header ---
        self.header_frame = ctk.CTkFrame(self)
        self.header_frame.grid(row=0, column=0, sticky="ew", padx=10, pady=5)
        
        self.btn_refresh = ctk.CTkButton(self.header_frame, text="Refresh Data", command=self.refresh_table)
        self.btn_refresh.pack(side="left", padx=10, pady=10)
        
        self.btn_export = ctk.CTkButton(self.header_frame, text="Export to Excel", command=self.export_excel)
        self.btn_export.pack(side="right", padx=10, pady=10)
        
        # --- Tabs ---
        self.tabview = ctk.CTkTabview(self)
        self.tabview.grid(row=1, column=0, sticky="nsew", padx=10, pady=5)
        
        self.tab_overview = self.tabview.add("Overview")
        self.tab_review = self.tabview.add("Review Needed")
        self.tab_clashes = self.tabview.add("Clashes")
        
        # Overview Layout: Left = Tree, Right = Stats
        self.tab_overview.grid_columnconfigure(0, weight=3) # Tree Container
        self.tab_overview.grid_columnconfigure(1, weight=1) # Stats
        self.tab_overview.grid_rowconfigure(0, weight=1)
        
        self.tab_review.grid_columnconfigure(0, weight=1)
        self.tab_review.grid_rowconfigure(0, weight=1)

        self.tab_clashes.grid_columnconfigure(0, weight=1)
        self.tab_clashes.grid_rowconfigure(0, weight=1)

        # --- Sidebar Stats in Overview ---
        self.stats_frame = ctk.CTkScrollableFrame(self.tab_overview, label_text="Category Sums")
        self.stats_frame.grid(row=0, column=1, sticky="nsew", padx=(5, 0))

        # --- Treeview Setup ---
        self._setup_styles()
        
        # Overview Tree (Wrapper Frame)
        self.tree_overview_container, self.tree_overview = self._create_tree(self.tab_overview)
        self.tree_overview_container.grid(row=0, column=0, sticky="nsew") 
        self.tree_overview.bind("<Double-1>", self.on_double_click_overview)
        
        # Review Tree
        self.tree_review_container, self.tree_review = self._create_tree(self.tab_review)
        self.tree_review_container.grid(row=0, column=0, sticky="nsew")
        self.tree_review.bind("<Double-1>", self.on_double_click_review)
        
        # Clashes Tree
        self.tree_clashes_container, self.tree_clashes = self._create_tree(self.tab_clashes)
        self.tree_clashes_container.grid(row=0, column=0, sticky="nsew")
        self.tree_clashes.bind("<Double-1>", self.on_double_click_clash)


    def _setup_styles(self):
        style = ttk.Style()
        style.theme_use("default") 
        bg_color = "#2b2b2b"
        fg_color = "white"
        selected_color = "#1f538d"
        
        style.configure("Treeview", 
                        background=bg_color, 
                        foreground=fg_color, 
                        fieldbackground=bg_color,
                        rowheight=25,
                        font=("Arial", 10))
        style.map('Treeview', background=[('selected', selected_color)])
        style.configure("Treeview.Heading", 
                        background="#3a3a3a", 
                        foreground="white", 
                        font=("Arial", 11, "bold"))

    def _create_tree(self, parent_widget):
        # Create a container frame to hold tree + scrollbar
        container = ctk.CTkFrame(parent_widget, fg_color="transparent")
        container.grid_columnconfigure(0, weight=1)
        container.grid_rowconfigure(0, weight=1)
        
        columns = ("ID", "Date", "Description", "Amount", "Category", "Source", "ClashInfo")
        tree = ttk.Treeview(container, columns=columns, show="headings")
        
        tree.heading("Date", text="Date")
        tree.heading("Description", text="Description")
        tree.heading("Amount", text="Amount")
        tree.heading("Category", text="Category")
        tree.heading("Source", text="Source")
        tree.heading("ClashInfo", text="Clash Info") # Hidden usually
        
        tree.column("ID", width=0, stretch=False) 
        tree.column("Date", width=100)
        tree.column("Description", width=350)
        tree.column("Amount", width=100, anchor="e")
        tree.column("Category", width=150)
        tree.column("Source", width=80)
        tree.column("ClashInfo", width=0, stretch=False) # display only in clash tab?
        
        scrollbar = ttk.Scrollbar(container, orient="vertical", command=tree.yview)
        tree.configure(yscrollcommand=scrollbar.set)
        
        tree.grid(row=0, column=0, sticky="nsew")
        scrollbar.grid(row=0, column=1, sticky="ns")
        
        tree.tag_configure("positive", foreground="#00e676")
        tree.tag_configure("negative", foreground="#ff5252")
        
        return container, tree

    def refresh_table(self):
        self._clear_tree(self.tree_overview)
        self._clear_tree(self.tree_review)
        self._clear_tree(self.tree_clashes)
        for widget in self.stats_frame.winfo_children():
            widget.destroy()
            
        df = self.app.data_manager.get_data()
        if df.empty:
            return
            
        # Grouping
        # Check for Clashes first
        if 'clash_info' in df.columns:
            clashes = df[df['clash_info'].notna() & (df['clash_info'] != '')]
        else:
            clashes = pd.DataFrame()
            
        uncategorized = df[(df['category'].isna() | (df['category'] == ''))].sort_values(by='date', ascending=False)
        # Exclude clashes from uncategorized/categorized if we want exclusive views?
        # User said: "create a new window... to resolve clashes".
        # Let's show clashes in Clashes tab.
        # And keep them in Overview/Review? Maybe keep them in Review if they have no category logic...
        
        # Categorized
        categorized = df[~df.index.isin(uncategorized.index)].sort_values(by=['category', 'date'], ascending=[True, False])

        # --- Clashes Tab ---
        if not clashes.empty:
            # Modify Clashes Tree to show Info
            self.tree_clashes.column("ClashInfo", width=200, stretch=True)
            for _, row in clashes.iterrows():
                self._insert_row(self.tree_clashes, row, None)
        else:
            self.tree_clashes.column("ClashInfo", width=0, stretch=False)

        # --- Review Tab ---
        for _, row in uncategorized.iterrows():
            self._insert_row(self.tree_review, row, None)
            
        # --- Overview Tab ---
        current_cat = None
        parent_node = None
        
        # Valid Categories Sums
        cat_sums = categorized.groupby('category')['amount'].sum().sort_values()
        
        for cat, amount in cat_sums.items():
            color = "#ff5252" if amount < 0 else "#00e676"
            ctk.CTkLabel(self.stats_frame, text=f"{cat}:", font=ctk.CTkFont(weight="bold")).pack(anchor="w", padx=5)
            ctk.CTkLabel(self.stats_frame, text=f"{amount:.2f} €", text_color=color).pack(anchor="w", padx=15, pady=(0, 5))

        for _, row in categorized.iterrows():
            if row['category'] != current_cat:
                current_cat = row['category']
                parent_node = self.tree_overview.insert("", "end", values=("", "", f"> {current_cat}", "", "", "", ""), open=True)
            
            self._insert_row(self.tree_overview, row, parent_node)

    def _clear_tree(self, tree):
        for item in tree.get_children():
            tree.delete(item)

    def _insert_row(self, tree, row, parent):
        date_str = row['date'].strftime('%Y-%m-%d') if pd.notnull(row['date']) else ""
        desc = str(row['description'])
        cat = str(row['category']) if row['category'] else "-"
        src = str(row['source']) if 'source' in row else "Unknown"
        clash = str(row['clash_info']) if 'clash_info' in row and pd.notnull(row['clash_info']) else ""
        txn_id = row['id']
        
        amt = row['amount'] if pd.notnull(row['amount']) else 0.0
        amt_str = f"{amt:.2f}"
        
        tag = "negative" if amt < 0 else "positive"
        
        values = (txn_id, date_str, desc, amt_str, cat, src, clash)
        if parent:
             tree.insert(parent, "end", values=values, tags=(tag,))
        else:
             tree.insert("", "end", values=values, tags=(tag,))

    def on_double_click_overview(self, event):
        self.open_edit_dialog(self.tree_overview)

    def on_double_click_review(self, event):
        self.open_edit_dialog(self.tree_review)

    def on_double_click_clash(self, event):
        self.open_edit_dialog(self.tree_clashes)

    def open_edit_dialog(self, tree):
        item_id = tree.selection()
        if not item_id:
            return
        
        item = tree.item(item_id)
        values = item['values']
        
        if not values or values[0] == "":
            return

        txn_id = values[0]
        desc = values[2]
        current_cat = values[4]
        
        # Create Custom TopLevel
        dialog = ctk.CTkToplevel(self)
        dialog.title("Edit Category")
        dialog.geometry("400x200")
        dialog.attributes("-topmost", True)
        
        ctk.CTkLabel(dialog, text=f"Update Category for:\n'{desc}'", wraplength=380).pack(pady=10)
        
        existing_cats = self.app.data_manager.get_all_categories()
        combo = ctk.CTkComboBox(dialog, values=existing_cats)
        combo.set(current_cat)
        combo.pack(pady=10)
        
        def save():
            new_cat = combo.get()
            if new_cat:
                self.app.data_manager.update_category(txn_id, new_cat)
                self.refresh_table()
                dialog.destroy()
        
        ctk.CTkButton(dialog, text="Save", command=save).pack(pady=10)

    def export_excel(self):
        print("Exporting to Excel...")
        file_path = filedialog.asksaveasfilename(defaultextension=".xlsx", filetypes=[("Excel Files", "*.xlsx")])
        if file_path:
            success, msg = export_to_excel(self.app.data_manager.get_data(), file_path)
            if success:
                print(msg) 
            else:
                print(f"Export failed: {msg}")
