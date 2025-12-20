"""Conflicts tab for FinanceAnalyzer."""

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
    QGroupBox,
)
from PySide6.QtCore import Qt
from PySide6.QtGui import QColor

from ...services.entry_service import EntryService
from ...services.category_service import CategoryService
from ...services.categorization_engine import CategorizationEngine


class ConflictsTab(QWidget):
    """Tab for resolving entries with multiple matching rules."""
    
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
        info_box = QGroupBox("About Conflicts")
        info_layout = QVBoxLayout(info_box)
        info_label = QLabel(
            "These entries matched multiple categorization rules that point to different categories. "
            "Please manually select the correct category for each entry."
        )
        info_label.setWordWrap(True)
        info_layout.addWidget(info_label)
        layout.addWidget(info_box)
        
        # Count label
        header_layout = QHBoxLayout()
        self.count_label = QLabel("0 entries with conflicts")
        self.count_label.setStyleSheet("font-size: 14px; font-weight: bold; color: #f0883e;")
        header_layout.addWidget(self.count_label)
        header_layout.addStretch()
        layout.addLayout(header_layout)
        
        # Table
        self.table = QTableWidget()
        self.table.setColumnCount(6)
        self.table.setHorizontalHeaderLabels([
            "Date", "Amount", "Description", "Matching Rules", "Source", "Assign Category"
        ])
        self.table.setAlternatingRowColors(True)
        self.table.setSelectionBehavior(QAbstractItemView.SelectRows)
        self.table.setEditTriggers(QAbstractItemView.NoEditTriggers)
        
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
        layout.addLayout(footer_layout)
    
    def set_profile(self, profile_id: int):
        """Set the current profile."""
        self.profile_id = profile_id
        self.refresh()
    
    def refresh(self):
        """Refresh the table data."""
        entry_service = EntryService(self.profile_id)
        entries = entry_service.get_all_entries(conflicts_only=True)
        
        category_service = CategoryService(self.profile_id)
        categories = category_service.get_all_categories()
        category_service.close()
        
        engine = CategorizationEngine(self.profile_id)
        
        self.table.setRowCount(len(entries))
        self.count_label.setText(f"{len(entries)} entries with conflicts")
        
        for row, entry in enumerate(entries):
            # Date
            date_item = QTableWidgetItem(entry.entry_date.strftime("%d.%m.%Y"))
            date_item.setData(Qt.UserRole, entry.id)
            self.table.setItem(row, 0, date_item)
            
            # Amount
            amount_item = QTableWidgetItem(f"€{entry.amount:,.2f}")
            if entry.amount > 0:
                amount_item.setForeground(QColor("#3fb950"))
            else:
                amount_item.setForeground(QColor("#f85149"))
            self.table.setItem(row, 1, amount_item)
            
            # Description
            desc_item = QTableWidgetItem(entry.description)
            self.table.setItem(row, 2, desc_item)
            
            # Matching rules
            matching_rules = engine.find_matching_rules(entry)
            rule_texts = []
            for rule in matching_rules:
                cat_name = rule.target_category.name if rule.target_category else "?"
                rule_texts.append(f"'{rule.pattern}' → {cat_name}")
            
            rules_item = QTableWidgetItem("\n".join(rule_texts))
            rules_item.setForeground(QColor("#f0883e"))
            self.table.setItem(row, 3, rules_item)
            
            # Source
            source_item = QTableWidgetItem(entry.source)
            self.table.setItem(row, 4, source_item)
            
            # Assign combo
            action_combo = QComboBox()
            action_combo.addItem("-- Select Category --", None)
            
            for cat in categories:
                action_combo.addItem(cat.name, cat.id)
            
            action_combo.currentIndexChanged.connect(
                lambda idx, e_id=entry.id, combo=action_combo: 
                self._assign_category(e_id, combo.currentData())
            )
            self.table.setCellWidget(row, 5, action_combo)
        
        engine.close()
        entry_service.close()
    
    def _assign_category(self, entry_id: int, category_id: int | None):
        """Assign category to resolve conflict."""
        if category_id is None:
            return
        
        entry_service = EntryService(self.profile_id)
        entry_service.set_category(entry_id, category_id, is_manual=True)
        entry_service.close()
        
        self.refresh()
