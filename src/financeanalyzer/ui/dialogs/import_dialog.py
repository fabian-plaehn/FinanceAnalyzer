"""Import dialog for FinanceAnalyzer."""

from pathlib import Path
from decimal import Decimal

from PySide6.QtWidgets import (
    QDialog,
    QVBoxLayout,
    QHBoxLayout,
    QWizard,
    QWizardPage,
    QLabel,
    QPushButton,
    QLineEdit,
    QComboBox,
    QTableWidget,
    QTableWidgetItem,
    QFileDialog,
    QMessageBox,
    QGroupBox,
    QFormLayout,
    QSpinBox,
    QHeaderView,
    QCheckBox,
)
from PySide6.QtCore import Qt

from ...database.models import CSVConfiguration
from ...database.service import get_database_service
from ...services.entry_service import EntryService
from ...services.categorization_engine import CategorizationEngine
from ...importer.csv_parser import CSVParser, detect_csv_settings, CSVParseError


class ImportDialog(QWizard):
    """Wizard for importing CSV files."""
    
    def __init__(self, profile_id: int, parent=None):
        super().__init__(parent)
        self.profile_id = profile_id
        self.file_path: str | None = None
        self.config: CSVConfiguration | None = None
        self.parsed_entries = []
        
        self.setWindowTitle("Import CSV")
        self.setMinimumSize(800, 600)
        
        # Add pages
        self.addPage(FileSelectionPage(self))
        self.addPage(ConfigurationPage(self))
        self.addPage(PreviewPage(self))
        self.addPage(ImportPage(self))
    
    def get_saved_configs(self):
        """Get saved CSV configurations for the profile."""
        db = get_database_service()
        with db.get_session() as session:
            configs = session.query(CSVConfiguration).filter(
                CSVConfiguration.profile_id == self.profile_id
            ).all()
            # Detach from session
            return [(c.id, c.name, c.delimiter, c.date_column, c.amount_column, 
                     c.description_column, c.date_format, c.encoding, c.skip_rows,
                     c.decimal_separator, c.thousands_separator, c.sender_receiver_column) for c in configs]
    
    def save_config(self, name: str, config_data: dict) -> int:
        """Save a new CSV configuration."""
        db = get_database_service()
        with db.get_session() as session:
            config = CSVConfiguration(
                profile_id=self.profile_id,
                name=name,
                **config_data
            )
            session.add(config)
            session.commit()
            return config.id


class FileSelectionPage(QWizardPage):
    """Page for selecting CSV file."""
    
    def __init__(self, wizard: ImportDialog):
        super().__init__()
        self.wizard_ref = wizard
        self.setTitle("Select CSV File")
        self.setSubTitle("Choose a CSV file to import")
        
        layout = QVBoxLayout(self)
        
        # File selection
        file_layout = QHBoxLayout()
        
        self.file_input = QLineEdit()
        self.file_input.setPlaceholderText("Select a CSV file...")
        self.file_input.setReadOnly(True)
        file_layout.addWidget(self.file_input)
        
        self.browse_btn = QPushButton("Browse...")
        self.browse_btn.clicked.connect(self._browse)
        file_layout.addWidget(self.browse_btn)
        
        layout.addLayout(file_layout)
        
        # File info
        self.info_label = QLabel()
        self.info_label.setWordWrap(True)
        layout.addWidget(self.info_label)
        
        layout.addStretch()
        
        self.registerField("file_path*", self.file_input)
    
    def _browse(self):
        """Browse for CSV file."""
        file_path, _ = QFileDialog.getOpenFileName(
            self,
            "Select CSV File",
            "",
            "CSV Files (*.csv);;All Files (*)"
        )
        
        if file_path:
            self.file_input.setText(file_path)
            self.wizard_ref.file_path = file_path
            
            # Show file info
            path = Path(file_path)
            settings = detect_csv_settings(file_path)
            self.info_label.setText(
                f"File: {path.name}\n"
                f"Size: {path.stat().st_size:,} bytes\n"
                f"Detected delimiter: {repr(settings['delimiter'])}\n"
                f"Detected encoding: {settings['encoding']}\n"
                f"Columns found: {len(settings['headers'])}"
            )


class ConfigurationPage(QWizardPage):
    """Page for configuring column mappings."""
    
    def __init__(self, wizard: ImportDialog):
        super().__init__()
        self.wizard_ref = wizard
        self.setTitle("Configure Column Mapping")
        self.setSubTitle("Map CSV columns to entry fields")
        
        layout = QVBoxLayout(self)
        
        # Saved configs
        saved_group = QGroupBox("Use Saved Configuration")
        saved_layout = QHBoxLayout(saved_group)
        
        self.saved_combo = QComboBox()
        self.saved_combo.addItem("-- Create New --", None)
        saved_layout.addWidget(self.saved_combo)
        
        self.load_btn = QPushButton("Load")
        self.load_btn.clicked.connect(self._load_config)
        saved_layout.addWidget(self.load_btn)
        
        layout.addWidget(saved_group)
        
        # Configuration form
        config_group = QGroupBox("Column Mapping")
        form = QFormLayout(config_group)
        
        self.delimiter_combo = QComboBox()
        self.delimiter_combo.addItem("Semicolon (;)", ";")
        self.delimiter_combo.addItem("Comma (,)", ",")
        self.delimiter_combo.addItem("Tab", "\t")
        form.addRow("Delimiter:", self.delimiter_combo)
        
        self.encoding_combo = QComboBox()
        self.encoding_combo.addItems(["utf-8", "latin-1", "cp1252", "iso-8859-1"])
        form.addRow("Encoding:", self.encoding_combo)
        
        self.skip_rows = QSpinBox()
        self.skip_rows.setMinimum(0)
        self.skip_rows.setMaximum(100)
        form.addRow("Skip rows:", self.skip_rows)
        
        self.date_col = QComboBox()
        form.addRow("Date column:", self.date_col)
        
        self.date_format = QComboBox()
        self.date_format.setEditable(True)
        self.date_format.addItems(["%d.%m.%Y", "%Y-%m-%d", "%m/%d/%Y", "%d/%m/%Y"])
        form.addRow("Date format:", self.date_format)
        
        self.amount_col = QComboBox()
        form.addRow("Amount column:", self.amount_col)
        
        self.decimal_sep = QComboBox()
        self.decimal_sep.addItem("Comma (,)", ",")
        self.decimal_sep.addItem("Period (.)", ".")
        form.addRow("Decimal separator:", self.decimal_sep)
        
        self.thousands_sep = QComboBox()
        self.thousands_sep.addItem("Period (.)", ".")
        self.thousands_sep.addItem("Comma (,)", ",")
        self.thousands_sep.addItem("None", "")
        form.addRow("Thousands separator:", self.thousands_sep)
        
        self.desc_col = QComboBox()
        form.addRow("Description column:", self.desc_col)
        
        self.sender_receiver_col = QComboBox()
        form.addRow("Sender/Receiver column (optional):", self.sender_receiver_col)
        
        layout.addWidget(config_group)
        
        # Reload columns button
        self.reload_btn = QPushButton("Reload Columns")
        self.reload_btn.clicked.connect(self._reload_columns)
        layout.addWidget(self.reload_btn)
        
        # Save config option
        save_layout = QHBoxLayout()
        self.save_check = QCheckBox("Save this configuration as:")
        save_layout.addWidget(self.save_check)
        
        self.save_name = QLineEdit()
        self.save_name.setPlaceholderText("Configuration name...")
        save_layout.addWidget(self.save_name)
        
        layout.addLayout(save_layout)
    
    def initializePage(self):
        """Initialize page when shown."""
        self._load_saved_configs()
        self._reload_columns()
    
    def _load_saved_configs(self):
        """Load saved configurations."""
        self.saved_combo.clear()
        self.saved_combo.addItem("-- Create New --", None)
        
        for config in self.wizard_ref.get_saved_configs():
            self.saved_combo.addItem(config[1], config)  # name, full config
    
    def _load_config(self):
        """Load a saved configuration."""
        config_data = self.saved_combo.currentData()
        if not config_data:
            return
        
        # Unpack: id, name, delimiter, date_column, amount_column, 
        #         description_column, date_format, encoding, skip_rows,
        #         decimal_separator, thousands_separator, sender_receiver_column
        _, name, delimiter, date_col, amount_col, desc_col, date_fmt, encoding, skip, dec_sep, thou_sep, sender_receiver_col = config_data
        
        # Set delimiter
        for i in range(self.delimiter_combo.count()):
            if self.delimiter_combo.itemData(i) == delimiter:
                self.delimiter_combo.setCurrentIndex(i)
                break
        
        # Set encoding
        idx = self.encoding_combo.findText(encoding)
        if idx >= 0:
            self.encoding_combo.setCurrentIndex(idx)
        
        self.skip_rows.setValue(skip)
        
        # Reload columns with new settings
        self._reload_columns()
        
        # Set column mappings
        idx = self.date_col.findText(date_col)
        if idx >= 0:
            self.date_col.setCurrentIndex(idx)
        
        idx = self.amount_col.findText(amount_col)
        if idx >= 0:
            self.amount_col.setCurrentIndex(idx)
        
        idx = self.desc_col.findText(desc_col)
        if idx >= 0:
            self.desc_col.setCurrentIndex(idx)
        
        self.date_format.setCurrentText(date_fmt)
        
        # Set separators
        for i in range(self.decimal_sep.count()):
            if self.decimal_sep.itemData(i) == dec_sep:
                self.decimal_sep.setCurrentIndex(i)
                break
        
        for i in range(self.thousands_sep.count()):
            if self.thousands_sep.itemData(i) == thou_sep:
                self.thousands_sep.setCurrentIndex(i)
                break
        
        # Set sender/receiver column if present
        if sender_receiver_col:
            idx = self.sender_receiver_col.findText(sender_receiver_col)
            if idx >= 0:
                self.sender_receiver_col.setCurrentIndex(idx)
    
    def _reload_columns(self):
        """Reload column headers from file."""
        if not self.wizard_ref.file_path:
            return
        
        try:
            settings = detect_csv_settings(self.wizard_ref.file_path)
            headers = settings["headers"]
            
            # Update column combos
            for combo in [self.date_col, self.amount_col, self.desc_col]:
                combo.clear()
                combo.addItems(headers)
            
            # Sender/receiver is optional - add "None" option
            self.sender_receiver_col.clear()
            self.sender_receiver_col.addItem("-- None --", None)
            for h in headers:
                self.sender_receiver_col.addItem(h, h)
            
            # Try to auto-detect common column names
            for i, h in enumerate(headers):
                h_lower = h.lower()
                if "buchungstag" in h_lower or "date" in h_lower or "datum" in h_lower:
                    self.date_col.setCurrentIndex(i)
                if "betrag" in h_lower or "amount" in h_lower:
                    self.amount_col.setCurrentIndex(i)
                if "verwendungszweck" in h_lower or "description" in h_lower or "zweck" in h_lower:
                    self.desc_col.setCurrentIndex(i)
                # Auto-detect sender/receiver column
                if "zahlungsbeteiligter" in h_lower or "sender" in h_lower or "empfänger" in h_lower or "partner" in h_lower:
                    idx = self.sender_receiver_col.findData(h)
                    if idx >= 0:
                        self.sender_receiver_col.setCurrentIndex(idx)
                    
        except Exception as e:
            QMessageBox.warning(self, "Error", f"Could not read file: {e}")
    
    def validatePage(self):
        """Validate page before continuing."""
        # Get sender/receiver column if selected
        sender_receiver_col = self.sender_receiver_col.currentData()
        
        # Build config
        config = CSVConfiguration(
            profile_id=self.wizard_ref.profile_id,
            name="temp",
            delimiter=self.delimiter_combo.currentData(),
            encoding=self.encoding_combo.currentText(),
            skip_rows=self.skip_rows.value(),
            date_column=self.date_col.currentText(),
            date_format=self.date_format.currentText(),
            amount_column=self.amount_col.currentText(),
            description_column=self.desc_col.currentText(),
            decimal_separator=self.decimal_sep.currentData(),
            thousands_separator=self.thousands_sep.currentData() or "",
            sender_receiver_column=sender_receiver_col
        )
        self.wizard_ref.config = config
        
        # Save config if requested
        if self.save_check.isChecked() and self.save_name.text().strip():
            self.wizard_ref.save_config(
                self.save_name.text().strip(),
                {
                    "delimiter": config.delimiter,
                    "encoding": config.encoding,
                    "skip_rows": config.skip_rows,
                    "date_column": config.date_column,
                    "date_format": config.date_format,
                    "amount_column": config.amount_column,
                    "description_column": config.description_column,
                    "decimal_separator": config.decimal_separator,
                    "thousands_separator": config.thousands_separator,
                    "sender_receiver_column": config.sender_receiver_column
                }
            )
        
        return True


class PreviewPage(QWizardPage):
    """Page for previewing parsed data."""
    
    def __init__(self, wizard: ImportDialog):
        super().__init__()
        self.wizard_ref = wizard
        self.setTitle("Preview Data")
        self.setSubTitle("Review the parsed entries before importing")
        
        layout = QVBoxLayout(self)
        
        self.status_label = QLabel()
        layout.addWidget(self.status_label)
        
        self.table = QTableWidget()
        self.table.setColumnCount(4)
        self.table.setHorizontalHeaderLabels(["Date", "Amount", "Sender/Receiver", "Description"])
        self.table.setAlternatingRowColors(True)
        
        header = self.table.horizontalHeader()
        header.setSectionResizeMode(0, QHeaderView.ResizeToContents)
        header.setSectionResizeMode(1, QHeaderView.ResizeToContents)
        header.setSectionResizeMode(2, QHeaderView.ResizeToContents)
        header.setSectionResizeMode(3, QHeaderView.Stretch)
        
        layout.addWidget(self.table)
    
    def initializePage(self):
        """Parse and preview data."""
        if not self.wizard_ref.file_path or not self.wizard_ref.config:
            self.status_label.setText("Error: No file or configuration")
            return
        
        try:
            parser = CSVParser(self.wizard_ref.config)
            entries = parser.parse(self.wizard_ref.file_path)
            self.wizard_ref.parsed_entries = entries
            
            self.table.setRowCount(len(entries))
            
            for row, entry in enumerate(entries):
                self.table.setItem(row, 0, QTableWidgetItem(entry.entry_date.strftime("%d.%m.%Y")))
                self.table.setItem(row, 1, QTableWidgetItem(f"€{entry.amount:,.2f}"))
                self.table.setItem(row, 2, QTableWidgetItem(entry.sender_receiver or ""))
                self.table.setItem(row, 3, QTableWidgetItem(entry.description))
            
            self.status_label.setText(f"✓ Successfully parsed {len(entries)} entries")
            self.status_label.setStyleSheet("color: green;")
            
        except CSVParseError as e:
            self.status_label.setText(f"✗ Parse error: {e}")
            self.status_label.setStyleSheet("color: red;")
            self.wizard_ref.parsed_entries = []


class ImportPage(QWizardPage):
    """Final page for importing data."""
    
    def __init__(self, wizard: ImportDialog):
        super().__init__()
        self.wizard_ref = wizard
        self.setTitle("Import")
        self.setSubTitle("Importing entries into the database")
        
        layout = QVBoxLayout(self)
        
        self.source_label = QLabel("Source name for these entries:")
        layout.addWidget(self.source_label)
        
        self.source_input = QLineEdit()
        self.source_input.setText("Bank Import")
        layout.addWidget(self.source_input)
        
        self.status_label = QLabel()
        layout.addWidget(self.status_label)
        
        self.result_label = QLabel()
        self.result_label.setWordWrap(True)
        layout.addWidget(self.result_label)
        
        layout.addStretch()
        
        self.registerField("source_name", self.source_input)
    
    def initializePage(self):
        """Perform the import."""
        entries = self.wizard_ref.parsed_entries
        if not entries:
            self.status_label.setText("No entries to import")
            return
        
        source = self.source_input.text().strip() or "Bank Import"
        
        entry_service = EntryService(self.wizard_ref.profile_id)
        
        imported = 0
        duplicates = 0
        
        for parsed in entries:
            # Generate hash for duplicate detection
            import_hash = EntryService.generate_import_hash(
                parsed.entry_date, parsed.amount, parsed.description, source, parsed.sender_receiver
            )
            
            if entry_service.entry_exists(import_hash):
                duplicates += 1
                continue
            
            entry_service.create_entry(
                entry_date=parsed.entry_date,
                amount=parsed.amount,
                description=parsed.description,
                sender_receiver=parsed.sender_receiver,
                source=source,
                import_hash=import_hash
            )
            imported += 1
        
        entry_service.close()
        
        # Run categorization
        engine = CategorizationEngine(self.wizard_ref.profile_id)
        cat_count, conflict_count, uncat_count = engine.reapply_rules()
        engine.close()
        
        self.status_label.setText("✓ Import complete!")
        self.status_label.setStyleSheet("color: green; font-weight: bold;")
        
        self.result_label.setText(
            f"Results:\n"
            f"• Imported: {imported} entries\n"
            f"• Skipped (duplicates): {duplicates}\n"
            f"• Auto-categorized: {cat_count}\n"
            f"• Conflicts: {conflict_count}\n"
            f"• Uncategorized: {uncat_count}"
        )
