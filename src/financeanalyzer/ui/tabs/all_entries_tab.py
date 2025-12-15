"""All entries tab for FinanceAnalyzer."""

from PySide6.QtWidgets import (
    QWidget,
    QVBoxLayout,
    QHBoxLayout,
    QTableWidget,
    QTableWidgetItem,
    QPushButton,
    QLabel,
    QComboBox,
    QLineEdit,
    QDateEdit,
    QHeaderView,
    QAbstractItemView,
    QMessageBox,
    QGroupBox,
    QMenu,
)
from PySide6.QtCore import Qt, QDate
from PySide6.QtGui import QColor, QAction

from ...services.entry_service import EntryService
from ...services.category_service import CategoryService


class AllEntriesTab(QWidget):
    """Tab for viewing and managing all entries."""
    
    def __init__(self, profile_id: int, parent=None):
        super().__init__(parent)
        self.profile_id = profile_id
        
        self._setup_ui()
        self.refresh()
    
    def _setup_ui(self):
        """Set up the tab UI."""
        layout = QVBoxLayout(self)
        layout.setContentsMargins(10, 10, 10, 10)
        
        # Filters
        filter_group = QGroupBox("Filters")
        filter_layout = QHBoxLayout(filter_group)
        
        # Date range
        filter_layout.addWidget(QLabel("From:"))
        self.start_date = QDateEdit()
        self.start_date.setCalendarPopup(True)
        self.start_date.setDate(QDate.currentDate().addYears(-1))
        filter_layout.addWidget(self.start_date)
        
        filter_layout.addWidget(QLabel("To:"))
        self.end_date = QDateEdit()
        self.end_date.setCalendarPopup(True)
        self.end_date.setDate(QDate.currentDate())
        filter_layout.addWidget(self.end_date)
        
        # Category filter
        filter_layout.addWidget(QLabel("Category:"))
        self.category_filter = QComboBox()
        self.category_filter.setMinimumWidth(120)
        filter_layout.addWidget(self.category_filter)
        
        # Source filter
        filter_layout.addWidget(QLabel("Source:"))
        self.source_filter = QComboBox()
        self.source_filter.setMinimumWidth(100)
        filter_layout.addWidget(self.source_filter)
        
        # Search
        filter_layout.addWidget(QLabel("Search:"))
        self.search_input = QLineEdit()
        self.search_input.setPlaceholderText("Search description...")
        self.search_input.setMinimumWidth(150)
        filter_layout.addWidget(self.search_input)
        
        self.filter_btn = QPushButton("Apply")
        self.filter_btn.clicked.connect(self.refresh)
        filter_layout.addWidget(self.filter_btn)
        
        self.clear_btn = QPushButton("Clear")
        self.clear_btn.setObjectName("clearBtn")
        self.clear_btn.clicked.connect(self._clear_filters)
        filter_layout.addWidget(self.clear_btn)
        
        layout.addWidget(filter_group)
        
        # Count label
        self.count_label = QLabel("0 entries")
        self.count_label.setStyleSheet("font-size: 12px;")
        layout.addWidget(self.count_label)
        
        # Table
        self.table = QTableWidget()
        self.table.setColumnCount(6)
        self.table.setHorizontalHeaderLabels([
            "Date", "Amount", "Description", "Category", "Source", "Manual"
        ])
        self.table.setAlternatingRowColors(True)
        self.table.setSelectionBehavior(QAbstractItemView.SelectRows)
        self.table.setEditTriggers(QAbstractItemView.NoEditTriggers)
        self.table.setContextMenuPolicy(Qt.CustomContextMenu)
        self.table.customContextMenuRequested.connect(self._show_context_menu)
        
        header = self.table.horizontalHeader()
        header.setSectionResizeMode(0, QHeaderView.ResizeToContents)
        header.setSectionResizeMode(1, QHeaderView.ResizeToContents)
        header.setSectionResizeMode(2, QHeaderView.Stretch)
        header.setSectionResizeMode(3, QHeaderView.ResizeToContents)
        header.setSectionResizeMode(4, QHeaderView.ResizeToContents)
        header.setSectionResizeMode(5, QHeaderView.ResizeToContents)
        
        layout.addWidget(self.table)
        
        # Footer
        footer_layout = QHBoxLayout()
        
        self.refresh_btn = QPushButton("🔄 Refresh")
        self.refresh_btn.clicked.connect(self.refresh)
        footer_layout.addWidget(self.refresh_btn)
        
        footer_layout.addStretch()
        
        self.delete_btn = QPushButton("🗑️ Delete Selected")
        self.delete_btn.setObjectName("deleteBtn")
        self.delete_btn.clicked.connect(self._delete_selected)
        footer_layout.addWidget(self.delete_btn)
        
        layout.addLayout(footer_layout)
    
    def set_profile(self, profile_id: int):
        """Set the current profile."""
        self.profile_id = profile_id
        self._filters_dirty = True
        self.refresh()
    
    def _load_filters_if_needed(self):
        """Load filter options only if needed."""
        if not getattr(self, '_filters_dirty', True):
            return
        
        # Categories
        self.category_filter.clear()
        self.category_filter.addItem("All", None)
        self.category_filter.addItem("Uncategorized", -1)
        
        category_service = CategoryService(self.profile_id)
        for cat in category_service.get_all_categories():
            self.category_filter.addItem(cat.name, cat.id)
        category_service.close()
        
        # Sources
        self.source_filter.clear()
        self.source_filter.addItem("All", None)
        
        entry_service = EntryService(self.profile_id)
        for source in entry_service.get_sources():
            self.source_filter.addItem(source, source)
        entry_service.close()
        
        self._filters_dirty = False
    
    def _clear_filters(self):
        """Clear all filters."""
        self.start_date.setDate(QDate.currentDate().addYears(-1))
        self.end_date.setDate(QDate.currentDate())
        self.category_filter.setCurrentIndex(0)
        self.source_filter.setCurrentIndex(0)
        self.search_input.clear()
        self.refresh()
    
    def refresh(self):
        """Refresh the table data."""
        import time
        t0 = time.perf_counter()
        
        self._load_filters_if_needed()
        t1 = time.perf_counter()
        print(f"[PROFILE] _load_filters_if_needed: {(t1-t0)*1000:.1f}ms")
        
        entry_service = EntryService(self.profile_id)
        
        # Get filter values
        start = self.start_date.date().toPython()
        end = self.end_date.date().toPython()
        category_id = self.category_filter.currentData()
        source = self.source_filter.currentData()
        search = self.search_input.text().strip().lower()
        
        # Handle special category filters
        if category_id == -1:  # Uncategorized
            entries = entry_service.get_all_entries(
                start_date=start, end_date=end, source=source, uncategorized_only=True
            )
        elif category_id:
            entries = entry_service.get_all_entries(
                start_date=start, end_date=end, category_id=category_id, source=source
            )
        else:
            entries = entry_service.get_all_entries(
                start_date=start, end_date=end, source=source
            )
        
        entry_service.close()
        t2 = time.perf_counter()
        print(f"[PROFILE] get_all_entries ({len(entries)} entries): {(t2-t1)*1000:.1f}ms")
        
        # Apply search filter
        if search:
            entries = [e for e in entries if search in e.description.lower()]
        
        # Get categories for display (cached if available)
        category_service = CategoryService(self.profile_id)
        categories = {c.id: c.name for c in category_service.get_all_categories()}
        category_service.close()
        t3 = time.perf_counter()
        print(f"[PROFILE] get_categories: {(t3-t2)*1000:.1f}ms")
        
        # Pre-create colors once (huge performance gain)
        color_green = QColor("green")
        color_red = QColor("red")
        color_orange = QColor("orange")
        
        # Disable ALL updates for faster rendering
        self.table.setUpdatesEnabled(False)
        self.table.blockSignals(True)
        self.table.setSortingEnabled(False)
        
        # Clear and resize
        self.table.setRowCount(0)  # Clear first
        self.table.setRowCount(len(entries))
        self.count_label.setText(f"{len(entries)} entries")
        
        for row, entry in enumerate(entries):
            # Date
            date_item = QTableWidgetItem(entry.entry_date.strftime("%d.%m.%Y"))
            date_item.setData(Qt.UserRole, entry.id)
            self.table.setItem(row, 0, date_item)
            
            # Amount - use pre-created colors
            amount_item = QTableWidgetItem(f"€{entry.amount:,.2f}")
            amount_item.setForeground(color_green if entry.amount > 0 else color_red)
            self.table.setItem(row, 1, amount_item)
            
            # Description
            self.table.setItem(row, 2, QTableWidgetItem(entry.description))
            
            # Category
            if entry.category_id:
                cat_name = categories.get(entry.category_id, f"? ({entry.category_id})")
            else:
                cat_name = "—"
            cat_item = QTableWidgetItem(cat_name)
            if entry.has_conflict:
                cat_item.setForeground(color_orange)
                cat_item.setText("Conflict")
            self.table.setItem(row, 3, cat_item)
            
            # Source
            self.table.setItem(row, 4, QTableWidgetItem(entry.source))
            
            # Manual flag
            manual_item = QTableWidgetItem("Y" if entry.is_manual_category else "")
            manual_item.setTextAlignment(Qt.AlignCenter)
            self.table.setItem(row, 5, manual_item)
        
        # Re-enable everything after batch insert
        self.table.blockSignals(False)
        self.table.setUpdatesEnabled(True)
        
        t4 = time.perf_counter()
        print(f"[PROFILE] table population: {(t4-t3)*1000:.1f}ms")
        print(f"[PROFILE] TOTAL refresh: {(t4-t0)*1000:.1f}ms")
        print("---")
    
    def _show_context_menu(self, position):
        """Show context menu for table."""
        menu = QMenu(self)
        
        # Get selected rows
        selected_rows = set(item.row() for item in self.table.selectedItems())
        if not selected_rows:
            return
        
        # Add category submenu
        category_menu = menu.addMenu("Set Category")
        
        category_service = CategoryService(self.profile_id)
        for cat in category_service.get_all_categories():
            action = QAction(cat.name, self)
            action.triggered.connect(
                lambda checked, c_id=cat.id: self._set_category_for_selected(c_id)
            )
            category_menu.addAction(action)
        category_service.close()
        
        # Clear category option
        menu.addSeparator()
        clear_action = QAction("Clear Category", self)
        clear_action.triggered.connect(self._clear_category_for_selected)
        menu.addAction(clear_action)
        
        # Delete option
        menu.addSeparator()
        delete_action = QAction("Delete", self)
        delete_action.triggered.connect(self._delete_selected)
        menu.addAction(delete_action)
        
        menu.exec(self.table.viewport().mapToGlobal(position))
    
    def _set_category_for_selected(self, category_id: int):
        """Set category for selected entries."""
        selected_rows = set(item.row() for item in self.table.selectedItems())
        if not selected_rows:
            return
        
        entry_service = EntryService(self.profile_id)
        for row in selected_rows:
            entry_id = self.table.item(row, 0).data(Qt.UserRole)
            entry_service.set_category(entry_id, category_id, is_manual=True)
        entry_service.close()
        
        self.refresh()
    
    def _clear_category_for_selected(self):
        """Clear category for selected entries."""
        selected_rows = set(item.row() for item in self.table.selectedItems())
        if not selected_rows:
            return
        
        entry_service = EntryService(self.profile_id)
        for row in selected_rows:
            entry_id = self.table.item(row, 0).data(Qt.UserRole)
            entry_service.update_entry(entry_id, clear_category=True, is_manual_category=False)
        entry_service.close()
        
        self.refresh()
    
    def _delete_selected(self):
        """Delete selected entries."""
        selected_rows = set(item.row() for item in self.table.selectedItems())
        if not selected_rows:
            QMessageBox.warning(self, "No Selection", "Please select entries to delete.")
            return
        
        reply = QMessageBox.question(
            self,
            "Confirm Delete",
            f"Are you sure you want to delete {len(selected_rows)} entries?",
            QMessageBox.Yes | QMessageBox.No
        )
        
        if reply == QMessageBox.Yes:
            entry_service = EntryService(self.profile_id)
            for row in selected_rows:
                entry_id = self.table.item(row, 0).data(Qt.UserRole)
                entry_service.delete_entry(entry_id)
            entry_service.close()
            
            self.refresh()
