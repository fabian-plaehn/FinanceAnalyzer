import customtkinter as ctk
from finance_analyzer.core.data_manager import DataManager
from finance_analyzer.core.rules import RuleEngine
from finance_analyzer.gui.views.import_view import ImportView
from finance_analyzer.gui.views.rules_view import RulesView
from finance_analyzer.gui.views.analysis_view import AnalysisView

ctk.set_appearance_mode("System")
ctk.set_default_color_theme("blue")

class App(ctk.CTk):
    def __init__(self):
        super().__init__()

        # --- Core Components ---
        self.data_manager = DataManager()
        self.rule_engine = RuleEngine()

        # --- Layout ---
        self.title("Finance Analyzer")
        self.geometry(f"{1100}x{700}")

        self.grid_columnconfigure(1, weight=1)
        self.grid_columnconfigure((2, 3), weight=0)
        self.grid_rowconfigure((0, 1, 2), weight=1)

        # Sidebar
        self.sidebar_frame = ctk.CTkFrame(self, width=140, corner_radius=0)
        self.sidebar_frame.grid(row=0, column=0, rowspan=4, sticky="nsew")
        self.sidebar_frame.grid_rowconfigure(4, weight=1)
        
        self.logo_label = ctk.CTkLabel(self.sidebar_frame, text="FinanceAnalyzer", font=ctk.CTkFont(size=20, weight="bold"))
        self.logo_label.grid(row=0, column=0, padx=20, pady=(20, 10))
        
        self.sidebar_button_dashboard = ctk.CTkButton(self.sidebar_frame, command=self.show_dashboard_event, text="Dashboard")
        self.sidebar_button_dashboard.grid(row=1, column=0, padx=20, pady=10)
        
        self.sidebar_button_import = ctk.CTkButton(self.sidebar_frame, command=self.show_import_event, text="Import Data")
        self.sidebar_button_import.grid(row=2, column=0, padx=20, pady=10)
        
        self.sidebar_button_rules = ctk.CTkButton(self.sidebar_frame, command=self.show_rules_event, text="Rules")
        self.sidebar_button_rules.grid(row=3, column=0, padx=20, pady=10)

        # Views Container
        self.views = {}
        
        # Initialize Views
        self.views["dashboard"] = AnalysisView(self, self)
        self.views["import"] = ImportView(self, self)
        self.views["rules"] = RulesView(self, self)
        
        # Select default
        self.select_view("dashboard")

    def select_view(self, name):
        # Hide all
        for view in self.views.values():
            view.grid_forget()
        
        # Show selected
        self.views[name].grid(row=0, column=1, rowspan=4, padx=20, pady=20, sticky="nsew")
        
        # Refresh if needed
        if name == "dashboard":
            self.views["dashboard"].refresh_table()

    def show_dashboard_event(self):
        self.select_view("dashboard")

    def show_import_event(self):
        self.select_view("import")

    def show_rules_event(self):
        self.select_view("rules")
