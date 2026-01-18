"""Clone profile dialog for FinanceAnalyzer."""

from PySide6.QtWidgets import (
    QDialog,
    QVBoxLayout,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QPushButton,
    QMessageBox,
)
from PySide6.QtCore import Qt

from ...services.profile_service import ProfileService


class CloneProfileDialog(QDialog):
    """Dialog for cloning the current profile."""
    
    def __init__(self, source_profile_id: int, source_profile_name: str, parent=None):
        super().__init__(parent)
        self.source_profile_id = source_profile_id
        self.source_profile_name = source_profile_name
        self.new_profile = None
        
        self._setup_ui()
    
    def _setup_ui(self):
        """Set up the dialog UI."""
        self.setWindowTitle("Clone Profile")
        self.setMinimumWidth(400)
        
        layout = QVBoxLayout(self)
        layout.setSpacing(16)
        
        # Info label
        info_label = QLabel(
            f"Clone profile '<b>{self.source_profile_name}</b>' to create a new profile.\n\n"
            "The following will be copied:\n"
            "  ✓ All categories\n"
            "  ✓ All categorization rules\n"
            "  ✓ CSV import configurations\n\n"
            "Entries will NOT be copied (fresh start)."
        )
        info_label.setWordWrap(True)
        info_label.setStyleSheet("padding: 10px; background: #21262d; border-radius: 8px;")
        layout.addWidget(info_label)
        
        # New name input
        name_layout = QHBoxLayout()
        name_layout.addWidget(QLabel("New profile name:"))
        
        self.name_input = QLineEdit()
        self.name_input.setPlaceholderText(f"{self.source_profile_name} (Copy)")
        self.name_input.setText(f"{self.source_profile_name} 2025")
        name_layout.addWidget(self.name_input)
        
        layout.addLayout(name_layout)
        
        # Buttons
        button_layout = QHBoxLayout()
        
        cancel_btn = QPushButton("Cancel")
        cancel_btn.clicked.connect(self.reject)
        button_layout.addWidget(cancel_btn)
        
        button_layout.addStretch()
        
        clone_btn = QPushButton("Clone Profile")
        clone_btn.setObjectName("successBtn")
        clone_btn.clicked.connect(self._do_clone)
        button_layout.addWidget(clone_btn)
        
        layout.addLayout(button_layout)
    
    def _do_clone(self):
        """Execute the clone operation."""
        new_name = self.name_input.text().strip()
        if not new_name:
            QMessageBox.warning(self, "No Name", "Please enter a name for the new profile.")
            return
        
        # Check if name already exists
        profile_service = ProfileService()
        existing = profile_service.get_profile_by_name(new_name)
        if existing:
            QMessageBox.warning(
                self, "Name Exists", 
                f"A profile named '{new_name}' already exists. Please choose a different name."
            )
            profile_service.close()
            return
        
        # Clone
        try:
            self.new_profile = profile_service.clone_profile(
                self.source_profile_id, 
                new_name
            )
            profile_service.close()
            
            if self.new_profile:
                QMessageBox.information(
                    self, "Profile Cloned",
                    f"Profile '{new_name}' created successfully!\n\n"
                    "You can switch to it using the profile dropdown in the toolbar."
                )
                self.accept()
            else:
                QMessageBox.critical(self, "Error", "Failed to clone profile.")
                
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Failed to clone profile:\n{str(e)}")
