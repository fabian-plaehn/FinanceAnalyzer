"""Category management dialog for FinanceAnalyzer."""

from PySide6.QtWidgets import (
    QDialog,
    QVBoxLayout,
    QHBoxLayout,
    QListWidget,
    QListWidgetItem,
    QPushButton,
    QLabel,
    QLineEdit,
    QMessageBox,
)
from PySide6.QtCore import Qt

from ...services.category_service import CategoryService


class CategoryManagerDialog(QDialog):
    """Dialog for managing categories."""
    
    def __init__(self, profile_id: int, parent=None):
        super().__init__(parent)
        self.profile_id = profile_id
        self._service = CategoryService(profile_id)
        
        self._setup_ui()
        self._load_categories()
    
    def _setup_ui(self):
        """Set up the dialog UI."""
        self.setWindowTitle("Manage Categories")
        self.setMinimumSize(400, 400)
        
        layout = QVBoxLayout(self)
        
        # Category list
        self.category_list = QListWidget()
        self.category_list.setAlternatingRowColors(True)
        self.category_list.itemSelectionChanged.connect(self._on_selection_changed)
        self.category_list.itemDoubleClicked.connect(self._edit_category)
        layout.addWidget(self.category_list)
        
        # Add category section
        add_layout = QHBoxLayout()
        
        self.name_input = QLineEdit()
        self.name_input.setPlaceholderText("New category name...")
        self.name_input.returnPressed.connect(self._add_category)
        add_layout.addWidget(self.name_input)
        
        self.add_btn = QPushButton("Add")
        self.add_btn.clicked.connect(self._add_category)
        add_layout.addWidget(self.add_btn)
        
        layout.addLayout(add_layout)
        
        # Action buttons
        button_layout = QHBoxLayout()
        
        self.edit_btn = QPushButton("Edit")
        self.edit_btn.setEnabled(False)
        self.edit_btn.clicked.connect(self._edit_category)
        button_layout.addWidget(self.edit_btn)
        
        self.delete_btn = QPushButton("Delete")
        self.delete_btn.setEnabled(False)
        self.delete_btn.clicked.connect(self._delete_category)
        self.delete_btn.setObjectName("deleteBtn")
        button_layout.addWidget(self.delete_btn)
        
        button_layout.addStretch()
        
        self.close_btn = QPushButton("Close")
        self.close_btn.clicked.connect(self.accept)
        button_layout.addWidget(self.close_btn)
        
        layout.addLayout(button_layout)
    
    def _load_categories(self):
        """Load categories into the list."""
        self.category_list.clear()
        
        for cat in self._service.get_all_categories():
            item = QListWidgetItem(cat.name)
            item.setData(Qt.UserRole, cat.id)
            self.category_list.addItem(item)
    
    def _on_selection_changed(self):
        """Handle selection change."""
        has_selection = len(self.category_list.selectedItems()) > 0
        self.edit_btn.setEnabled(has_selection)
        self.delete_btn.setEnabled(has_selection)
    
    def _add_category(self):
        """Add a new category."""
        name = self.name_input.text().strip()
        if not name:
            QMessageBox.warning(self, "Error", "Please enter a category name.")
            return
        
        # Check for duplicate
        existing = self._service.get_category_by_name(name)
        if existing:
            QMessageBox.warning(self, "Error", f"Category '{name}' already exists.")
            return
        
        self._service.create_category(name)
        self.name_input.clear()
        self._load_categories()
    
    def _edit_category(self):
        """Edit selected category."""
        items = self.category_list.selectedItems()
        if not items:
            return
        
        current_name = items[0].text()
        category_id = items[0].data(Qt.UserRole)
        
        from PySide6.QtWidgets import QInputDialog
        new_name, ok = QInputDialog.getText(
            self,
            "Edit Category",
            "Category name:",
            text=current_name
        )
        
        if ok and new_name.strip():
            self._service.update_category(category_id, new_name.strip())
            self._load_categories()
    
    def _delete_category(self):
        """Delete selected category."""
        items = self.category_list.selectedItems()
        if not items:
            return
        
        category_name = items[0].text()
        category_id = items[0].data(Qt.UserRole)
        
        reply = QMessageBox.question(
            self,
            "Confirm Delete",
            f"Are you sure you want to delete category '{category_name}'?\n\n"
            "This will also delete all associated rules.",
            QMessageBox.Yes | QMessageBox.No
        )
        
        if reply == QMessageBox.Yes:
            self._service.delete_category(category_id)
            self._load_categories()
    
    def closeEvent(self, event):
        """Handle dialog close."""
        self._service.close()
        super().closeEvent(event)
