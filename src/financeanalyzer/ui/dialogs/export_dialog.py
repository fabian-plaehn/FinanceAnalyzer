"""Export dialog for FinanceAnalyzer."""

from datetime import date
from pathlib import Path

from PySide6.QtWidgets import (
    QDialog,
    QVBoxLayout,
    QHBoxLayout,
    QGroupBox,
    QRadioButton,
    QButtonGroup,
    QCheckBox,
    QLineEdit,
    QPushButton,
    QLabel,
    QFileDialog,
    QScrollArea,
    QWidget,
    QMessageBox,
)
from PySide6.QtCore import Qt

from ...services.category_service import CategoryService


class ExportDialog(QDialog):
    """Dialog for configuring and executing Excel export."""
    
    def __init__(self, profile_id: int, parent=None):
        super().__init__(parent)
        self.profile_id = profile_id
        self.selected_file_path: str | None = None
        self.category_checkboxes: list[tuple[QCheckBox, int | None]] = []
        
        self._setup_ui()
        self._load_categories()
    
    def _setup_ui(self):
        """Set up the dialog UI."""
        self.setWindowTitle("Export to Excel")
        self.setMinimumWidth(500)
        self.setMinimumHeight(450)
        
        layout = QVBoxLayout(self)
        
        # Format Selection
        format_group = QGroupBox("Export Format")
        format_layout = QVBoxLayout(format_group)
        
        self.format_button_group = QButtonGroup(self)
        
        self.category_tables_radio = QRadioButton("Category Tables - One table per category")
        self.category_tables_radio.setChecked(True)
        self.format_button_group.addButton(self.category_tables_radio, 0)
        format_layout.addWidget(self.category_tables_radio)
        
        self.all_in_one_radio = QRadioButton("All-In-One Table - All entries in one table with category column")
        self.format_button_group.addButton(self.all_in_one_radio, 1)
        format_layout.addWidget(self.all_in_one_radio)
        
        layout.addWidget(format_group)
        
        # Category Selection
        category_group = QGroupBox("Categories to Export")
        category_layout = QVBoxLayout(category_group)
        
        # Select/Deselect buttons
        btn_layout = QHBoxLayout()
        self.select_all_btn = QPushButton("Select All")
        self.select_all_btn.clicked.connect(self._select_all_categories)
        btn_layout.addWidget(self.select_all_btn)
        
        self.deselect_all_btn = QPushButton("Deselect All")
        self.deselect_all_btn.clicked.connect(self._deselect_all_categories)
        btn_layout.addWidget(self.deselect_all_btn)
        
        btn_layout.addStretch()
        category_layout.addLayout(btn_layout)
        
        # Scrollable checkbox list
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setMaximumHeight(150)
        
        self.category_container = QWidget()
        self.category_container_layout = QVBoxLayout(self.category_container)
        self.category_container_layout.setSpacing(4)
        scroll.setWidget(self.category_container)
        
        category_layout.addWidget(scroll)
        layout.addWidget(category_group)
        
        # File Selection
        file_group = QGroupBox("Output File")
        file_layout = QVBoxLayout(file_group)
        
        self.file_mode_group = QButtonGroup(self)
        
        self.new_file_radio = QRadioButton("Create new file")
        self.new_file_radio.setChecked(True)
        self.file_mode_group.addButton(self.new_file_radio, 0)
        file_layout.addWidget(self.new_file_radio)
        
        self.append_file_radio = QRadioButton("Append to existing file (adds new sheet)")
        self.file_mode_group.addButton(self.append_file_radio, 1)
        file_layout.addWidget(self.append_file_radio)
        
        # File path
        path_layout = QHBoxLayout()
        self.file_path_input = QLineEdit()
        self.file_path_input.setPlaceholderText("Select file path...")
        self.file_path_input.setReadOnly(True)
        path_layout.addWidget(self.file_path_input)
        
        self.browse_btn = QPushButton("Browse...")
        self.browse_btn.clicked.connect(self._browse_file)
        path_layout.addWidget(self.browse_btn)
        
        file_layout.addLayout(path_layout)
        layout.addWidget(file_group)
        
        # Sheet Name
        sheet_group = QGroupBox("Sheet Name")
        sheet_layout = QHBoxLayout(sheet_group)
        
        self.sheet_name_input = QLineEdit()
        self.sheet_name_input.setPlaceholderText("Financial Data")
        self.sheet_name_input.setText(f"Export_{date.today().strftime('%Y%m%d')}")
        sheet_layout.addWidget(self.sheet_name_input)
        
        layout.addWidget(sheet_group)
        
        # Buttons
        button_layout = QHBoxLayout()
        
        self.cancel_btn = QPushButton("Cancel")
        self.cancel_btn.clicked.connect(self.reject)
        button_layout.addWidget(self.cancel_btn)
        
        button_layout.addStretch()
        
        self.export_btn = QPushButton("Export")
        self.export_btn.setObjectName("successBtn")
        self.export_btn.clicked.connect(self._do_export)
        button_layout.addWidget(self.export_btn)
        
        layout.addLayout(button_layout)
    
    def _load_categories(self):
        """Load categories into checkbox list."""
        category_service = CategoryService(self.profile_id)
        categories = category_service.get_all_categories()
        category_service.close()
        
        # Add category checkboxes
        for cat in categories:
            cb = QCheckBox(cat.name)
            cb.setChecked(True)
            self.category_container_layout.addWidget(cb)
            self.category_checkboxes.append((cb, cat.id))
        
        # Add uncategorized option
        uncategorized_cb = QCheckBox("Uncategorized")
        uncategorized_cb.setChecked(False)
        self.category_container_layout.addWidget(uncategorized_cb)
        self.category_checkboxes.append((uncategorized_cb, None))
        
        self.category_container_layout.addStretch()
    
    def _select_all_categories(self):
        """Select all category checkboxes."""
        for cb, _ in self.category_checkboxes:
            cb.setChecked(True)
    
    def _deselect_all_categories(self):
        """Deselect all category checkboxes."""
        for cb, _ in self.category_checkboxes:
            cb.setChecked(False)
    
    def _browse_file(self):
        """Open file browser."""
        if self.new_file_radio.isChecked():
            file_path, _ = QFileDialog.getSaveFileName(
                self,
                "Save Export File",
                "",
                "Excel Files (*.xlsx)"
            )
        else:
            file_path, _ = QFileDialog.getOpenFileName(
                self,
                "Select Existing Excel File",
                "",
                "Excel Files (*.xlsx)"
            )
        
        if file_path:
            if not file_path.endswith('.xlsx'):
                file_path += '.xlsx'
            self.selected_file_path = file_path
            self.file_path_input.setText(file_path)
    
    def _do_export(self):
        """Execute the export."""
        # Validate
        if not self.selected_file_path:
            QMessageBox.warning(self, "No File", "Please select a file path.")
            return
        
        selected_categories = [
            cat_id for cb, cat_id in self.category_checkboxes if cb.isChecked()
        ]
        
        if not selected_categories and None not in selected_categories:
            QMessageBox.warning(self, "No Categories", "Please select at least one category.")
            return
        
        sheet_name = self.sheet_name_input.text().strip() or "Financial Data"
        
        # Determine format
        export_format = "category_tables" if self.category_tables_radio.isChecked() else "all_in_one"
        append_mode = self.append_file_radio.isChecked()
        
        # Filter out None for category_ids list, handle uncategorized separately
        include_uncategorized = None in selected_categories
        category_ids = [cid for cid in selected_categories if cid is not None]
        
        # Do export
        try:
            from ...export.excel_export import ExcelExporter
            
            exporter = ExcelExporter(self.profile_id)
            exporter.export(
                file_path=self.selected_file_path,
                export_format=export_format,
                category_ids=category_ids if category_ids else None,
                include_uncategorized=include_uncategorized,
                sheet_name=sheet_name,
                append_to_existing=append_mode
            )
            
            QMessageBox.information(
                self,
                "Export Complete",
                f"Data exported successfully to:\n{self.selected_file_path}"
            )
            self.accept()
            
        except Exception as e:
            QMessageBox.critical(
                self,
                "Export Error",
                f"Failed to export data:\n{str(e)}"
            )
    
    def get_export_settings(self) -> dict:
        """Get the current export settings."""
        selected_categories = [
            cat_id for cb, cat_id in self.category_checkboxes if cb.isChecked()
        ]
        
        return {
            "format": "category_tables" if self.category_tables_radio.isChecked() else "all_in_one",
            "category_ids": selected_categories,
            "file_path": self.selected_file_path,
            "sheet_name": self.sheet_name_input.text().strip() or "Financial Data",
            "append_mode": self.append_file_radio.isChecked()
        }
