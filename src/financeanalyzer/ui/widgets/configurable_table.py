"""Configurable table widget with column visibility and management."""

import json
from pathlib import Path

from PySide6.QtWidgets import (
    QTableWidget,
    QHeaderView,
    QMenu,
    QAbstractItemView,
)
from PySide6.QtCore import Qt
from PySide6.QtGui import QAction


class ConfigurableTable(QTableWidget):
    """A table widget with column visibility toggles, auto-sizing, and persistence."""
    
    # Column configuration: (key, display_name, default_visible, resize_mode)
    # resize_mode: 'stretch', 'content', 'fixed', or 'interactive'
    
    def __init__(
        self,
        columns: list[tuple[str, str, bool, str]],
        table_id: str,
        parent=None
    ):
        """Initialize the configurable table.
        
        Args:
            columns: List of (key, display_name, default_visible, resize_mode) tuples.
            table_id: Unique identifier for persisting column settings.
            parent: Parent widget.
        """
        super().__init__(parent)
        self.columns = columns
        self.table_id = table_id
        self._column_visibility = {col[0]: col[2] for col in columns}
        
        self._setup_table()
        self._load_settings()
        self._apply_column_visibility()
    
    def _get_settings_path(self) -> Path:
        """Get the path to settings file."""
        settings_dir = Path.home() / ".financeanalyzer"
        settings_dir.mkdir(parents=True, exist_ok=True)
        return settings_dir / "table_settings.json"
    
    def _load_settings(self):
        """Load column settings from disk."""
        try:
            settings_path = self._get_settings_path()
            if settings_path.exists():
                with open(settings_path, "r", encoding="utf-8") as f:
                    all_settings = json.load(f)
                    if self.table_id in all_settings:
                        saved = all_settings[self.table_id]
                        for key, visible in saved.get("visibility", {}).items():
                            if key in self._column_visibility:
                                self._column_visibility[key] = visible
        except (OSError, json.JSONDecodeError, KeyError):
            pass  # Use defaults on error
    
    def _save_settings(self):
        """Save column settings to disk."""
        try:
            settings_path = self._get_settings_path()
            all_settings = {}
            if settings_path.exists():
                with open(settings_path, "r", encoding="utf-8") as f:
                    all_settings = json.load(f)
            
            all_settings[self.table_id] = {
                "visibility": self._column_visibility
            }
            
            with open(settings_path, "w", encoding="utf-8") as f:
                json.dump(all_settings, f, indent=2)
        except (OSError, json.JSONDecodeError):
            pass  # Silently fail - not critical
    
    def _setup_table(self):
        """Set up the table structure."""
        self.setColumnCount(len(self.columns))
        self.setHorizontalHeaderLabels([col[1] for col in self.columns])
        self.setAlternatingRowColors(True)
        self.setSelectionBehavior(QAbstractItemView.SelectRows)
        self.setEditTriggers(QAbstractItemView.NoEditTriggers)
        
        # Enable header context menu
        header = self.horizontalHeader()
        header.setContextMenuPolicy(Qt.CustomContextMenu)
        header.customContextMenuRequested.connect(self._show_header_menu)
        header.setSectionsMovable(True)
        
        # Set resize modes
        for i, col in enumerate(self.columns):
            resize_mode = col[3]
            if resize_mode == 'stretch':
                header.setSectionResizeMode(i, QHeaderView.Stretch)
            elif resize_mode == 'content':
                header.setSectionResizeMode(i, QHeaderView.ResizeToContents)
            elif resize_mode == 'interactive':
                header.setSectionResizeMode(i, QHeaderView.Interactive)
            else:  # 'fixed' or default
                header.setSectionResizeMode(i, QHeaderView.Fixed)
    
    def _apply_column_visibility(self):
        """Apply current visibility settings to columns."""
        for i, col in enumerate(self.columns):
            is_visible = self._column_visibility.get(col[0], True)
            self.setColumnHidden(i, not is_visible)
    
    def _show_header_menu(self, position):
        """Show column visibility menu."""
        menu = QMenu(self)
        
        menu.addSection("Show/Hide Columns")
        
        for i, col in enumerate(self.columns):
            action = QAction(col[1], self)
            action.setCheckable(True)
            action.setChecked(self._column_visibility.get(col[0], True))
            action.triggered.connect(lambda checked, key=col[0]: self._toggle_column(key, checked))
            menu.addAction(action)
        
        menu.addSeparator()
        
        # Auto-fit action
        autofit_action = QAction("Auto-fit All Columns", self)
        autofit_action.triggered.connect(self._autofit_columns)
        menu.addAction(autofit_action)
        
        # Reset action
        reset_action = QAction("Reset to Defaults", self)
        reset_action.triggered.connect(self._reset_columns)
        menu.addAction(reset_action)
        
        menu.exec(self.horizontalHeader().mapToGlobal(position))
    
    def _toggle_column(self, key: str, visible: bool):
        """Toggle column visibility."""
        self._column_visibility[key] = visible
        self._apply_column_visibility()
        self._save_settings()
    
    def _autofit_columns(self):
        """Auto-fit all columns to content."""
        self.resizeColumnsToContents()
    
    def _reset_columns(self):
        """Reset columns to default visibility."""
        self._column_visibility = {col[0]: col[2] for col in self.columns}
        self._apply_column_visibility()
        self._save_settings()
    
    def get_column_index(self, key: str) -> int:
        """Get the index of a column by its key."""
        for i, col in enumerate(self.columns):
            if col[0] == key:
                return i
        return -1
