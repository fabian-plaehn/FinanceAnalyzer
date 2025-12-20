"""Rule management dialog for FinanceAnalyzer."""

from PySide6.QtWidgets import (
    QDialog,
    QVBoxLayout,
    QHBoxLayout,
    QTableWidget,
    QTableWidgetItem,
    QPushButton,
    QLabel,
    QLineEdit,
    QComboBox,
    QCheckBox,
    QMessageBox,
    QGroupBox,
    QFormLayout,
    QHeaderView,
    QAbstractItemView,
)
from PySide6.QtCore import Qt
from PySide6.QtGui import QColor

from ...services.rule_service import RuleService
from ...services.category_service import CategoryService


class RuleManagerDialog(QDialog):
    """Dialog for managing categorization rules."""
    
    def __init__(self, profile_id: int, parent=None):
        super().__init__(parent)
        self.profile_id = profile_id
        self._rule_service = RuleService(profile_id)
        self._category_service = CategoryService(profile_id)
        
        self._setup_ui()
        self._load_rules()
    
    def _setup_ui(self):
        """Set up the dialog UI."""
        self.setWindowTitle("Manage Rules")
        self.setMinimumSize(700, 500)
        
        layout = QVBoxLayout(self)
        
        # Rules table
        self.table = QTableWidget()
        self.table.setColumnCount(5)
        self.table.setHorizontalHeaderLabels([
            "Type", "Pattern", "Category", "Enabled", "Actions"
        ])
        self.table.setAlternatingRowColors(True)
        self.table.setSelectionBehavior(QAbstractItemView.SelectRows)
        
        header = self.table.horizontalHeader()
        header.setSectionResizeMode(0, QHeaderView.ResizeToContents)
        header.setSectionResizeMode(1, QHeaderView.Stretch)
        header.setSectionResizeMode(2, QHeaderView.ResizeToContents)
        header.setSectionResizeMode(3, QHeaderView.ResizeToContents)
        header.setSectionResizeMode(4, QHeaderView.ResizeToContents)
        
        layout.addWidget(self.table)
        
        # Add rule section
        add_group = QGroupBox("Add New Rule")
        add_layout = QFormLayout(add_group)
        
        self.type_combo = QComboBox()
        self.type_combo.addItem("Contains", "contains")
        self.type_combo.addItem("Regex", "regex")
        add_layout.addRow("Type:", self.type_combo)
        
        self.pattern_input = QLineEdit()
        self.pattern_input.setPlaceholderText("Enter pattern to match...")
        add_layout.addRow("Pattern:", self.pattern_input)
        
        self.category_combo = QComboBox()
        self._load_categories()
        add_layout.addRow("Category:", self.category_combo)
        
        btn_layout = QHBoxLayout()
        self.add_btn = QPushButton("Add Rule")
        self.add_btn.clicked.connect(self._add_rule)
        btn_layout.addWidget(self.add_btn)
        btn_layout.addStretch()
        add_layout.addRow(btn_layout)
        
        layout.addWidget(add_group)
        
        # Bottom buttons
        button_layout = QHBoxLayout()
        
        self.refresh_btn = QPushButton("🔄 Refresh")
        self.refresh_btn.clicked.connect(self._load_rules)
        button_layout.addWidget(self.refresh_btn)
        
        button_layout.addStretch()
        
        self.close_btn = QPushButton("Close")
        self.close_btn.clicked.connect(self.accept)
        button_layout.addWidget(self.close_btn)
        
        layout.addLayout(button_layout)
    
    def _load_categories(self):
        """Load categories into combo box."""
        self.category_combo.clear()
        for cat in self._category_service.get_all_categories():
            self.category_combo.addItem(cat.name, cat.id)
    
    def _load_rules(self):
        """Load rules into table."""
        self._load_categories()
        rules = self._rule_service.get_all_rules()
        
        self.table.setRowCount(len(rules))
        
        for row, rule in enumerate(rules):
            # Type
            type_item = QTableWidgetItem(rule.rule_type.title())
            type_item.setData(Qt.UserRole, rule.id)
            self.table.setItem(row, 0, type_item)
            
            # Pattern
            pattern_item = QTableWidgetItem(rule.pattern)
            self.table.setItem(row, 1, pattern_item)
            
            # Category
            cat_name = rule.target_category.name if rule.target_category else "?"
            cat_item = QTableWidgetItem(cat_name)
            self.table.setItem(row, 2, cat_item)
            
            # Enabled
            enabled_item = QTableWidgetItem("✓" if rule.enabled else "✗")
            enabled_item.setTextAlignment(Qt.AlignCenter)
            if rule.enabled:
                enabled_item.setForeground(QColor("#3fb950"))
            else:
                enabled_item.setForeground(QColor("#f85149"))
            self.table.setItem(row, 3, enabled_item)
            
            # Actions
            actions_widget = QHBoxLayout()
            
            toggle_btn = QPushButton("Toggle")
            toggle_btn.clicked.connect(lambda _, r_id=rule.id: self._toggle_rule(r_id))
            
            delete_btn = QPushButton("Delete")
            delete_btn.setObjectName("deleteBtn")
            delete_btn.clicked.connect(lambda _, r_id=rule.id: self._delete_rule(r_id))
            
            from PySide6.QtWidgets import QWidget
            container = QWidget()
            container_layout = QHBoxLayout(container)
            container_layout.setContentsMargins(2, 2, 2, 2)
            container_layout.addWidget(toggle_btn)
            container_layout.addWidget(delete_btn)
            
            self.table.setCellWidget(row, 4, container)
    
    def _add_rule(self):
        """Add a new rule."""
        pattern = self.pattern_input.text().strip()
        if not pattern:
            QMessageBox.warning(self, "Error", "Please enter a pattern.")
            return
        
        category_id = self.category_combo.currentData()
        if not category_id:
            QMessageBox.warning(self, "Error", "Please select a category.")
            return
        
        rule_type = self.type_combo.currentData()
        
        # Validate regex if needed
        if rule_type == "regex":
            import re
            try:
                re.compile(pattern)
            except re.error as e:
                QMessageBox.warning(self, "Invalid Regex", f"Invalid regex pattern: {e}")
                return
        
        self._rule_service.create_rule(
            target_category_id=category_id,
            rule_type=rule_type,
            pattern=pattern
        )
        
        self.pattern_input.clear()
        self._load_rules()
    
    def _toggle_rule(self, rule_id: int):
        """Toggle rule enabled state."""
        self._rule_service.toggle_rule(rule_id)
        self._load_rules()
    
    def _delete_rule(self, rule_id: int):
        """Delete a rule."""
        reply = QMessageBox.question(
            self,
            "Confirm Delete",
            "Are you sure you want to delete this rule?",
            QMessageBox.Yes | QMessageBox.No
        )
        
        if reply == QMessageBox.Yes:
            self._rule_service.delete_rule(rule_id)
            self._load_rules()
    
    def closeEvent(self, event):
        """Handle dialog close."""
        self._rule_service.close()
        self._category_service.close()
        super().closeEvent(event)
