"""Uncategorized entries tab for FinanceAnalyzer."""

from PySide6.QtWidgets import (
    QWidget,
    QVBoxLayout,
    QHBoxLayout,
    QTableWidget,
    QTableWidgetItem,
    QPushButton,
    QLabel,
    QComboBox,
    QHeaderView,
    QAbstractItemView,
    QMessageBox,
    QMenu,
)
from PySide6.QtCore import Qt
from PySide6.QtGui import QColor, QAction

from ...services.entry_service import EntryService
from ...services.category_service import CategoryService


class UncategorizedTab(QWidget):
    """Tab for managing uncategorized entries."""
    
    def __init__(self, profile_id: int, parent=None):
        super().__init__(parent)
        self.profile_id = profile_id
        
        self._setup_ui()
        self.refresh()
    
    def _setup_ui(self):
        """Set up the tab UI."""
        layout = QVBoxLayout(self)
        layout.setContentsMargins(10, 10, 10, 10)
        
        # Header
        header_layout = QHBoxLayout()
        
        self.count_label = QLabel("0 uncategorized entries")
        self.count_label.setStyleSheet("font-size: 14px; font-weight: bold; color: #f0883e;")
        header_layout.addWidget(self.count_label)
        
        header_layout.addStretch()
        
        # Bulk action
        header_layout.addWidget(QLabel("Assign selected to:"))
        
        self.category_combo = QComboBox()
        self.category_combo.setMinimumWidth(150)
        header_layout.addWidget(self.category_combo)
        
        self.assign_btn = QPushButton("Assign")
        self.assign_btn.clicked.connect(self._assign_category)
        header_layout.addWidget(self.assign_btn)
        
        layout.addLayout(header_layout)
        
        # Table
        self.table = QTableWidget()
        self.table.setColumnCount(6)
        self.table.setHorizontalHeaderLabels([
            "Date", "Amount", "Sender/Receiver", "Description", "Source", "Actions"
        ])
        self.table.setAlternatingRowColors(True)
        self.table.setSelectionBehavior(QAbstractItemView.SelectRows)
        self.table.setEditTriggers(QAbstractItemView.NoEditTriggers)
        self.table.setContextMenuPolicy(Qt.CustomContextMenu)
        self.table.customContextMenuRequested.connect(self._show_context_menu)
        
        header = self.table.horizontalHeader()
        header.setSectionResizeMode(0, QHeaderView.ResizeToContents)
        header.setSectionResizeMode(1, QHeaderView.ResizeToContents)
        header.setSectionResizeMode(2, QHeaderView.ResizeToContents)
        header.setSectionResizeMode(3, QHeaderView.Stretch)
        header.setSectionResizeMode(4, QHeaderView.ResizeToContents)
        header.setSectionResizeMode(5, QHeaderView.ResizeToContents)
        
        layout.addWidget(self.table)
        
        # Footer
        footer_layout = QHBoxLayout()
        
        self.refresh_btn = QPushButton("🔄 Refresh")
        self.refresh_btn.clicked.connect(self.refresh)
        footer_layout.addWidget(self.refresh_btn)
        
        footer_layout.addStretch()
        layout.addLayout(footer_layout)
    
    def set_profile(self, profile_id: int):
        """Set the current profile."""
        self.profile_id = profile_id
        self.refresh()
    
    def _load_categories(self):
        """Load categories into combo box."""
        self.category_combo.clear()
        category_service = CategoryService(self.profile_id)
        categories = category_service.get_all_categories()
        category_service.close()
        
        for cat in categories:
            self.category_combo.addItem(cat.name, cat.id)
    
    def refresh(self):
        """Refresh the table data."""
        self._load_categories()
        
        entry_service = EntryService(self.profile_id)
        entries = entry_service.get_all_entries(uncategorized_only=True)
        entry_service.close()
        
        # Cache categories once for performance
        category_service = CategoryService(self.profile_id)
        categories = category_service.get_all_categories()
        category_service.close()
        self._cached_categories = categories  # Store for context menu
        
        # Pre-create colors (dark theme compatible)
        color_green = QColor("#3fb950")
        color_red = QColor("#f85149")
        
        # Disable updates during population
        self.table.setUpdatesEnabled(False)
        self.table.blockSignals(True)
        self.table.setSortingEnabled(False)
        self.table.setRowCount(0)
        self.table.setRowCount(len(entries))
        self.count_label.setText(f"{len(entries)} uncategorized entries")
        
        for row, entry in enumerate(entries):
            # Date
            date_item = QTableWidgetItem(entry.entry_date.strftime("%d.%m.%Y"))
            date_item.setData(Qt.UserRole, entry.id)
            self.table.setItem(row, 0, date_item)
            
            # Amount
            amount_item = QTableWidgetItem(f"€{entry.amount:,.2f}")
            amount_item.setForeground(color_green if entry.amount > 0 else color_red)
            self.table.setItem(row, 1, amount_item)
            
            # Sender/Receiver
            sender_receiver = getattr(entry, 'sender_receiver', None) or ""
            self.table.setItem(row, 2, QTableWidgetItem(sender_receiver))
            
            # Description
            self.table.setItem(row, 3, QTableWidgetItem(entry.description))
            
            # Source
            self.table.setItem(row, 4, QTableWidgetItem(entry.source))
            
            # Actions placeholder - use context menu instead of slow combobox
            self.table.setItem(row, 5, QTableWidgetItem("Right-click"))
        
        # Re-enable updates
        self.table.blockSignals(False)
        self.table.setUpdatesEnabled(True)
    
    def _quick_assign(self, entry_id: int, category_id: int | None):
        """Quick assign category to a single entry."""
        if category_id is None:
            return
        
        entry_service = EntryService(self.profile_id)
        entry_service.set_category(entry_id, category_id, is_manual=True)
        entry_service.close()
        
        self.refresh()
    
    def _show_context_menu(self, position):
        """Show context menu for quick category assignment."""
        selected_rows = set(item.row() for item in self.table.selectedItems())
        if not selected_rows:
            return
        
        menu = QMenu(self)
        
        # Add category options from cached categories
        categories = getattr(self, '_cached_categories', [])
        for cat in categories:
            action = QAction(f"Assign: {cat.name}", self)
            action.triggered.connect(
                lambda checked, c_id=cat.id: self._assign_to_selected(c_id)
            )
            menu.addAction(action)
        
        menu.exec(self.table.viewport().mapToGlobal(position))
    
    def _assign_to_selected(self, category_id: int):
        """Assign category to all selected rows."""
        selected_rows = set(item.row() for item in self.table.selectedItems())
        entry_service = EntryService(self.profile_id)
        
        for row in selected_rows:
            entry_id = self.table.item(row, 0).data(Qt.UserRole)
            entry_service.set_category(entry_id, category_id, is_manual=True)
        
        entry_service.close()
        self.refresh()
    
    def _assign_category(self):
        """Assign category to selected entries."""
        selected_rows = set(item.row() for item in self.table.selectedItems())
        if not selected_rows:
            QMessageBox.warning(self, "No Selection", "Please select entries to assign.")
            return
        
        category_id = self.category_combo.currentData()
        if category_id is None:
            QMessageBox.warning(self, "No Category", "Please select a category.")
            return
        
        entry_service = EntryService(self.profile_id)
        
        for row in selected_rows:
            entry_id = self.table.item(row, 0).data(Qt.UserRole)
            entry_service.set_category(entry_id, category_id, is_manual=True)
        
        entry_service.close()
        
        QMessageBox.information(
            self,
            "Categories Assigned",
            f"Assigned category to {len(selected_rows)} entries."
        )
        self.refresh()
