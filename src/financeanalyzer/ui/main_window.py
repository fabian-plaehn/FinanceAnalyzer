"""Main window for FinanceAnalyzer."""

from PySide6.QtWidgets import (
    QMainWindow,
    QWidget,
    QVBoxLayout,
    QHBoxLayout,
    QTabWidget,
    QToolBar,
    QComboBox,
    QLabel,
    QStatusBar,
    QMessageBox,
    QFileDialog,
)
from PySide6.QtCore import Qt, Signal
from PySide6.QtGui import QAction, QFont

from ..database.models import Profile
from ..services.profile_service import ProfileService
from ..services.entry_service import EntryService
from ..services.category_service import CategoryService

from .tabs.dashboard_tab import DashboardTab
from .tabs.uncategorized_tab import UncategorizedTab
from .tabs.conflicts_tab import ConflictsTab
from .tabs.all_entries_tab import AllEntriesTab
from .dialogs.import_dialog import ImportDialog
from .dialogs.category_dialog import CategoryManagerDialog
from .dialogs.rule_dialog import RuleManagerDialog
from .dialogs.entry_dialog import EntryDialog
from .dialogs.export_dialog import ExportDialog


class MainWindow(QMainWindow):
    """Main application window."""
    
    profile_changed = Signal(int)  # Emitted when profile changes
    
    def __init__(self, profile: Profile):
        super().__init__()
        self.current_profile = profile
        self._profile_service = ProfileService()
        
        self._setup_ui()
        self._create_menus()
        self._create_toolbar()
        self._update_status_bar()
    
    def _setup_ui(self):
        """Set up the main window UI."""
        self.setWindowTitle(f"FinanceAnalyzer - {self.current_profile.name}")
        self.setMinimumSize(1200, 700)
        
        # Central widget
        central = QWidget()
        self.setCentralWidget(central)
        layout = QVBoxLayout(central)
        layout.setContentsMargins(0, 0, 0, 0)
        
        # Tab widget
        self.tabs = QTabWidget()
        self.tabs.setDocumentMode(True)
        
        # Create tabs
        self.dashboard_tab = DashboardTab(self.current_profile.id)
        self.uncategorized_tab = UncategorizedTab(self.current_profile.id)
        self.conflicts_tab = ConflictsTab(self.current_profile.id)
        self.all_entries_tab = AllEntriesTab(self.current_profile.id)
        
        self.tabs.addTab(self.dashboard_tab, "📊 Dashboard")
        self.tabs.addTab(self.uncategorized_tab, "❓ Uncategorized")
        self.tabs.addTab(self.conflicts_tab, "⚠️ Conflicts")
        self.tabs.addTab(self.all_entries_tab, "📋 All Entries")
        
        layout.addWidget(self.tabs)
        
        # Status bar
        self.status_bar = QStatusBar()
        self.setStatusBar(self.status_bar)
        
        # Connect signals
        self.tabs.currentChanged.connect(self._on_tab_changed)
    
    def _create_menus(self):
        """Create menu bar."""
        menubar = self.menuBar()
        
        # File menu
        file_menu = menubar.addMenu("&File")
        
        import_action = QAction("📥 Import CSV...", self)
        import_action.setShortcut("Ctrl+I")
        import_action.triggered.connect(self._import_csv)
        file_menu.addAction(import_action)
        
        manual_action = QAction("➕ Add Manual Entry...", self)
        manual_action.setShortcut("Ctrl+N")
        manual_action.triggered.connect(self._add_manual_entry)
        file_menu.addAction(manual_action)
        
        file_menu.addSeparator()
        
        export_action = QAction("📤 Export to Excel...", self)
        export_action.setShortcut("Ctrl+E")
        export_action.triggered.connect(self._export_excel)
        file_menu.addAction(export_action)
        
        file_menu.addSeparator()
        
        exit_action = QAction("Exit", self)
        exit_action.setShortcut("Ctrl+Q")
        exit_action.triggered.connect(self.close)
        file_menu.addAction(exit_action)
        
        # Edit menu
        edit_menu = menubar.addMenu("&Edit")
        
        categories_action = QAction("📁 Manage Categories...", self)
        categories_action.triggered.connect(self._manage_categories)
        edit_menu.addAction(categories_action)
        
        rules_action = QAction("📏 Manage Rules...", self)
        rules_action.triggered.connect(self._manage_rules)
        edit_menu.addAction(rules_action)
        
        edit_menu.addSeparator()
        
        reapply_action = QAction("🔄 Reapply All Rules", self)
        reapply_action.triggered.connect(self._reapply_rules)
        edit_menu.addAction(reapply_action)
        
        # View menu  
        view_menu = menubar.addMenu("&View")
        
        refresh_action = QAction("🔄 Refresh", self)
        refresh_action.setShortcut("F5")
        refresh_action.triggered.connect(self._refresh_all)
        view_menu.addAction(refresh_action)
    
    def _create_toolbar(self):
        """Create toolbar."""
        toolbar = QToolBar("Main Toolbar")
        toolbar.setMovable(False)
        self.addToolBar(toolbar)
        
        # Profile selector
        toolbar.addWidget(QLabel("  Profile: "))
        
        self.profile_combo = QComboBox()
        self.profile_combo.setMinimumWidth(150)
        self._load_profiles()
        self.profile_combo.currentIndexChanged.connect(self._on_profile_changed)
        toolbar.addWidget(self.profile_combo)
        
        toolbar.addSeparator()
        
        # Quick actions
        import_btn = QAction("📥 Import", self)
        import_btn.triggered.connect(self._import_csv)
        toolbar.addAction(import_btn)
        
        manual_btn = QAction("➕ Add Entry", self)
        manual_btn.triggered.connect(self._add_manual_entry)
        toolbar.addAction(manual_btn)
        
        export_btn = QAction("📤 Export", self)
        export_btn.triggered.connect(self._export_excel)
        toolbar.addAction(export_btn)
        
        toolbar.addSeparator()
        
        refresh_btn = QAction("🔄 Refresh", self)
        refresh_btn.triggered.connect(self._refresh_all)
        toolbar.addAction(refresh_btn)
    
    def _load_profiles(self):
        """Load profiles into combo box."""
        self.profile_combo.blockSignals(True)
        self.profile_combo.clear()
        
        profiles = self._profile_service.get_all_profiles()
        current_index = 0
        
        for i, profile in enumerate(profiles):
            self.profile_combo.addItem(profile.name, profile.id)
            if profile.id == self.current_profile.id:
                current_index = i
        
        self.profile_combo.setCurrentIndex(current_index)
        self.profile_combo.blockSignals(False)
    
    def _on_profile_changed(self, index: int):
        """Handle profile change from combo box."""
        if index < 0:
            return
        
        profile_id = self.profile_combo.itemData(index)
        if profile_id == self.current_profile.id:
            return
        
        profile = self._profile_service.get_profile(profile_id)
        if profile:
            self.current_profile = profile
            self.setWindowTitle(f"FinanceAnalyzer - {profile.name}")
            
            # Update all tabs
            self.dashboard_tab.set_profile(profile_id)
            self.uncategorized_tab.set_profile(profile_id)
            self.conflicts_tab.set_profile(profile_id)
            self.all_entries_tab.set_profile(profile_id)
            
            self._update_status_bar()
            self.profile_changed.emit(profile_id)
    
    def _on_tab_changed(self, index: int):
        """Handle tab change."""
        tab = self.tabs.widget(index)
        if hasattr(tab, 'refresh'):
            tab.refresh()
    
    def _update_status_bar(self):
        """Update status bar with current stats."""
        entry_service = EntryService(self.current_profile.id)
        total = entry_service.get_entry_count()
        uncategorized = entry_service.get_uncategorized_count()
        conflicts = entry_service.get_conflict_count()
        entry_service.close()
        
        self.status_bar.showMessage(
            f"Total entries: {total} | Uncategorized: {uncategorized} | Conflicts: {conflicts}"
        )
    
    def _import_csv(self):
        """Open CSV import dialog."""
        dialog = ImportDialog(self.current_profile.id, self)
        if dialog.exec():
            self._refresh_all()
    
    def _add_manual_entry(self):
        """Open manual entry dialog."""
        dialog = EntryDialog(self.current_profile.id, self)
        if dialog.exec():
            self._refresh_all()
    
    def _export_excel(self):
        """Open export dialog."""
        dialog = ExportDialog(self.current_profile.id, self)
        dialog.exec()
    
    def _manage_categories(self):
        """Open category manager dialog."""
        dialog = CategoryManagerDialog(self.current_profile.id, self)
        dialog.exec()
        self._refresh_all()
    
    def _manage_rules(self):
        """Open rule manager dialog."""
        dialog = RuleManagerDialog(self.current_profile.id, self)
        dialog.exec()
        self._refresh_all()
    
    def _reapply_rules(self):
        """Reapply all categorization rules."""
        from ..services.categorization_engine import CategorizationEngine
        
        reply = QMessageBox.question(
            self,
            "Reapply Rules",
            "This will reapply all categorization rules to entries that were not manually categorized.\n\n"
            "Continue?",
            QMessageBox.Yes | QMessageBox.No
        )
        
        if reply == QMessageBox.Yes:
            engine = CategorizationEngine(self.current_profile.id)
            categorized, conflicts, uncategorized = engine.reapply_rules()
            engine.close()
            
            QMessageBox.information(
                self,
                "Rules Applied",
                f"Rules have been reapplied:\n\n"
                f"• Categorized: {categorized}\n"
                f"• Conflicts: {conflicts}\n"
                f"• Uncategorized: {uncategorized}"
            )
            self._refresh_all()
    
    def _refresh_all(self):
        """Refresh all tabs and status bar."""
        current_tab = self.tabs.currentWidget()
        if hasattr(current_tab, 'refresh'):
            current_tab.refresh()
        self._update_status_bar()
    
    def closeEvent(self, event):
        """Handle window close."""
        self._profile_service.close()
        super().closeEvent(event)
