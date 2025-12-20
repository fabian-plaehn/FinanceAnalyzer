"""Profile selection dialog for FinanceAnalyzer."""

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
    QFrame,
)
from PySide6.QtCore import Qt
from PySide6.QtGui import QFont

from ..database.models import Profile
from ..services.profile_service import ProfileService


class ProfileDialog(QDialog):
    """Dialog for selecting or creating a profile at startup."""
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.selected_profile: Profile | None = None
        self._profile_service = ProfileService()
        
        self._setup_ui()
        self._load_profiles()
    
    def _setup_ui(self):
        """Set up the dialog UI."""
        self.setWindowTitle("Select Business Profile")
        self.setMinimumSize(400, 350)
        self.setModal(True)
        
        layout = QVBoxLayout(self)
        layout.setSpacing(15)
        layout.setContentsMargins(20, 20, 20, 20)
        
        # Title
        title = QLabel("FinanceAnalyzer")
        title.setFont(QFont("Segoe UI", 24, QFont.Bold))
        title.setAlignment(Qt.AlignCenter)
        title.setStyleSheet("color: #58a6ff;")
        layout.addWidget(title)
        
        subtitle = QLabel("Select a business profile to continue")
        subtitle.setAlignment(Qt.AlignCenter)
        subtitle.setStyleSheet("color: #8b949e; font-size: 13px;")
        layout.addWidget(subtitle)
        
        # Separator
        line = QFrame()
        line.setFrameShape(QFrame.HLine)
        line.setFrameShadow(QFrame.Sunken)
        layout.addWidget(line)
        
        # Profile list
        self.profile_list = QListWidget()
        self.profile_list.setAlternatingRowColors(True)
        self.profile_list.itemDoubleClicked.connect(self._on_select)
        self.profile_list.itemSelectionChanged.connect(self._on_selection_changed)
        layout.addWidget(self.profile_list)
        
        # New profile section
        new_profile_layout = QHBoxLayout()
        self.new_profile_input = QLineEdit()
        self.new_profile_input.setPlaceholderText("Enter new profile name...")
        self.new_profile_input.returnPressed.connect(self._create_profile)
        new_profile_layout.addWidget(self.new_profile_input)
        
        self.create_btn = QPushButton("Create")
        self.create_btn.clicked.connect(self._create_profile)
        new_profile_layout.addWidget(self.create_btn)
        layout.addLayout(new_profile_layout)
        
        # Buttons
        button_layout = QHBoxLayout()
        
        self.delete_btn = QPushButton("Delete")
        self.delete_btn.setObjectName("deleteBtn")
        self.delete_btn.setEnabled(False)
        self.delete_btn.clicked.connect(self._delete_profile)
        button_layout.addWidget(self.delete_btn)
        
        button_layout.addStretch()
        
        self.select_btn = QPushButton("Select")
        self.select_btn.setObjectName("successBtn")
        self.select_btn.setEnabled(False)
        self.select_btn.clicked.connect(self._on_select)
        button_layout.addWidget(self.select_btn)
        
        layout.addLayout(button_layout)
    
    def _load_profiles(self):
        """Load profiles into the list."""
        self.profile_list.clear()
        profiles = self._profile_service.get_all_profiles()
        
        for profile in profiles:
            item = QListWidgetItem(profile.name)
            item.setData(Qt.UserRole, profile.id)
            self.profile_list.addItem(item)
    
    def _on_selection_changed(self):
        """Handle selection change."""
        has_selection = len(self.profile_list.selectedItems()) > 0
        self.select_btn.setEnabled(has_selection)
        self.delete_btn.setEnabled(has_selection)
    
    def _on_select(self):
        """Handle profile selection."""
        items = self.profile_list.selectedItems()
        if items:
            profile_id = items[0].data(Qt.UserRole)
            self.selected_profile = self._profile_service.get_profile(profile_id)
            self.accept()
    
    def _create_profile(self):
        """Create a new profile."""
        name = self.new_profile_input.text().strip()
        if not name:
            QMessageBox.warning(self, "Error", "Please enter a profile name.")
            return
        
        # Check for duplicate
        existing = self._profile_service.get_profile_by_name(name)
        if existing:
            QMessageBox.warning(self, "Error", f"Profile '{name}' already exists.")
            return
        
        profile = self._profile_service.create_profile(name)
        self.new_profile_input.clear()
        self._load_profiles()
        
        # Select the new profile
        for i in range(self.profile_list.count()):
            item = self.profile_list.item(i)
            if item.data(Qt.UserRole) == profile.id:
                item.setSelected(True)
                break
    
    def _delete_profile(self):
        """Delete the selected profile."""
        items = self.profile_list.selectedItems()
        if not items:
            return
        
        profile_id = items[0].data(Qt.UserRole)
        profile_name = items[0].text()
        
        reply = QMessageBox.question(
            self,
            "Confirm Delete",
            f"Are you sure you want to delete profile '{profile_name}'?\n\n"
            "This will delete all entries, categories, and rules.",
            QMessageBox.Yes | QMessageBox.No
        )
        
        if reply == QMessageBox.Yes:
            self._profile_service.delete_profile(profile_id)
            self._load_profiles()
    
    def closeEvent(self, event):
        """Handle dialog close."""
        self._profile_service.close()
        super().closeEvent(event)
