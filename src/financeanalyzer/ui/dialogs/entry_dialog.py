"""Manual entry dialog for FinanceAnalyzer."""

from datetime import date
from decimal import Decimal, InvalidOperation

from PySide6.QtWidgets import (
    QDialog,
    QVBoxLayout,
    QFormLayout,
    QLineEdit,
    QDateEdit,
    QComboBox,
    QPushButton,
    QMessageBox,
    QHBoxLayout,
)
from PySide6.QtCore import QDate

from ...services.entry_service import EntryService
from ...services.category_service import CategoryService


class EntryDialog(QDialog):
    """Dialog for adding a manual entry."""
    
    def __init__(self, profile_id: int, parent=None):
        super().__init__(parent)
        self.profile_id = profile_id
        
        self._setup_ui()
    
    def _setup_ui(self):
        """Set up the dialog UI."""
        self.setWindowTitle("Add Manual Entry")
        self.setMinimumWidth(400)
        
        layout = QVBoxLayout(self)
        
        form = QFormLayout()
        
        self.date_input = QDateEdit()
        self.date_input.setCalendarPopup(True)
        self.date_input.setDate(QDate.currentDate())
        form.addRow("Date:", self.date_input)
        
        self.amount_input = QLineEdit()
        self.amount_input.setPlaceholderText("e.g., 123.45 or -50.00")
        form.addRow("Amount (€):", self.amount_input)
        
        self.description_input = QLineEdit()
        self.description_input.setPlaceholderText("Description...")
        form.addRow("Description:", self.description_input)
        
        self.source_input = QLineEdit()
        self.source_input.setText("Cash")
        form.addRow("Source:", self.source_input)
        
        self.category_combo = QComboBox()
        self.category_combo.addItem("-- No Category --", None)
        self._load_categories()
        form.addRow("Category:", self.category_combo)
        
        layout.addLayout(form)
        
        # Buttons
        button_layout = QHBoxLayout()
        
        self.cancel_btn = QPushButton("Cancel")
        self.cancel_btn.clicked.connect(self.reject)
        button_layout.addWidget(self.cancel_btn)
        
        button_layout.addStretch()
        
        self.save_btn = QPushButton("Save")
        self.save_btn.clicked.connect(self._save)
        self.save_btn.setObjectName("successBtn")
        button_layout.addWidget(self.save_btn)
        
        layout.addLayout(button_layout)
    
    def _load_categories(self):
        """Load categories into combo box."""
        category_service = CategoryService(self.profile_id)
        for cat in category_service.get_all_categories():
            self.category_combo.addItem(cat.name, cat.id)
        category_service.close()
    
    def _save(self):
        """Save the entry."""
        # Validate
        description = self.description_input.text().strip()
        if not description:
            QMessageBox.warning(self, "Error", "Please enter a description.")
            return
        
        try:
            amount_text = self.amount_input.text().strip().replace(",", ".")
            amount = Decimal(amount_text)
        except (InvalidOperation, ValueError):
            QMessageBox.warning(self, "Error", "Please enter a valid amount.")
            return
        
        source = self.source_input.text().strip() or "Cash"
        entry_date = self.date_input.date().toPython()
        category_id = self.category_combo.currentData()
        
        entry_service = EntryService(self.profile_id)
        entry_service.create_entry(
            entry_date=entry_date,
            amount=amount,
            description=description,
            source=source,
            category_id=category_id,
            is_manual_category=category_id is not None
        )
        entry_service.close()
        
        self.accept()
