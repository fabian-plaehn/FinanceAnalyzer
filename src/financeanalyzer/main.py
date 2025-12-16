"""Main entry point for FinanceAnalyzer."""

import sys

from PySide6.QtWidgets import QApplication
from PySide6.QtCore import Qt

from .database.service import get_database_service
from .ui.profile_dialog import ProfileDialog
from .ui.main_window import MainWindow


def main():
    """Main entry point for the application."""
    # Enable high DPI scaling
    QApplication.setHighDpiScaleFactorRoundingPolicy(
        Qt.HighDpiScaleFactorRoundingPolicy.PassThrough
    )
    
    app = QApplication(sys.argv)
    app.setApplicationName("FinanceAnalyzer")
    app.setOrganizationName("FinanceAnalyzer")
    
    # Apply modern styling with hover effects
    app.setStyleSheet("""
        /* Main window */
        QMainWindow {
            background-color: #f0f2f5;
        }
        
        /* Group boxes */
        QGroupBox {
            font-weight: bold;
            border: 1px solid #d0d0d0;
            border-radius: 8px;
            margin-top: 12px;
            padding: 15px 10px 10px 10px;
            background-color: #ffffff;
        }
        QGroupBox::title {
            subcontrol-origin: margin;
            left: 12px;
            padding: 0 8px;
            color: #333;
        }
        
        /* Buttons - modern style with hover */
        QPushButton {
            padding: 8px 16px;
            border: 1px solid #4472C4;
            border-radius: 6px;
            background-color: #4472C4;
            color: white;
            font-weight: 500;
            min-width: 70px;
        }
        QPushButton:hover {
            background-color: #3461b3;
            border-color: #3461b3;
        }
        QPushButton:pressed {
            background-color: #2d5299;
            border-color: #2d5299;
        }
        QPushButton:disabled {
            background-color: #cccccc;
            border-color: #bbbbbb;
            color: #888888;
        }
        
        /* Secondary/Clear buttons */
        QPushButton[flat="true"], QPushButton#clearBtn {
            background-color: #f8f9fa;
            border-color: #dee2e6;
            color: #495057;
        }
        QPushButton[flat="true"]:hover, QPushButton#clearBtn:hover {
            background-color: #e9ecef;
            border-color: #ced4da;
        }
        
        /* Danger buttons (delete) */
        QPushButton#deleteBtn {
            background-color: #dc3545;
            border-color: #dc3545;
        }
        QPushButton#deleteBtn:hover {
            background-color: #c82333;
            border-color: #bd2130;
        }
        
        /* Success buttons */
        QPushButton#successBtn {
            background-color: #28a745;
            border-color: #28a745;
        }
        QPushButton#successBtn:hover {
            background-color: #218838;
            border-color: #1e7e34;
        }
        
        /* Tables */
        QTableWidget {
            gridline-color: #e9ecef;
            background-color: white;
            border: 1px solid #dee2e6;
            border-radius: 4px;
        }
        QTableWidget::item {
            padding: 8px;
        }
        QTableWidget::item:selected {
            background-color: #4472C4;
            color: white;
        }
        QTableWidget::item:selected:hover {
            background-color: #3461b3;
            color: white;
        }
        QTableWidget::item:hover:!selected {
            background-color: #e8f0fe;
        }
        QHeaderView::section {
            background-color: #f8f9fa;
            padding: 10px 8px;
            border: none;
            border-bottom: 2px solid #dee2e6;
            font-weight: 600;
            color: #495057;
        }
        
        /* Tab widget */
        QTabWidget::pane {
            border: 1px solid #dee2e6;
            background: white;
            border-radius: 0 8px 8px 8px;
        }
        QTabBar::tab {
            padding: 10px 24px;
            margin-right: 4px;
            background-color: #e9ecef;
            border: 1px solid #dee2e6;
            border-bottom: none;
            border-radius: 8px 8px 0 0;
            color: #495057;
        }
        QTabBar::tab:selected {
            background: white;
            border-bottom: 2px solid #4472C4;
            color: #4472C4;
            font-weight: 600;
        }
        QTabBar::tab:hover:!selected {
            background-color: #f8f9fa;
        }
        
        /* Combo boxes */
        QComboBox {
            padding: 6px 12px;
            border: 1px solid #ced4da;
            border-radius: 6px;
            background-color: white;
            min-width: 100px;
        }
        QComboBox:hover {
            border-color: #4472C4;
        }
        QComboBox::drop-down {
            border: none;
            padding-right: 8px;
        }
        
        /* Line edits */
        QLineEdit {
            padding: 8px 12px;
            border: 1px solid #ced4da;
            border-radius: 6px;
            background-color: white;
        }
        QLineEdit:focus {
            border-color: #4472C4;
            outline: none;
        }
        QLineEdit:hover {
            border-color: #adb5bd;
        }
        
        /* Date edits */
        QDateEdit {
            padding: 6px 10px;
            border: 1px solid #ced4da;
            border-radius: 6px;
            background-color: white;
        }
        QDateEdit:hover {
            border-color: #4472C4;
        }
        
        /* Toolbar */
        QToolBar {
            background-color: #ffffff;
            border-bottom: 1px solid #dee2e6;
            padding: 6px;
            spacing: 6px;
        }
        QToolBar QToolButton {
            padding: 6px 12px;
            border-radius: 4px;
            border: none;
        }
        QToolBar QToolButton:hover {
            background-color: #e9ecef;
        }
        
        /* Status bar */
        QStatusBar {
            background-color: #f8f9fa;
            border-top: 1px solid #dee2e6;
            padding: 4px;
        }
        
        /* Tree widget */
        QTreeWidget {
            background-color: white;
            border: 1px solid #dee2e6;
            border-radius: 4px;
        }
        QTreeWidget::item {
            padding: 6px;
        }
        QTreeWidget::item:hover {
            background-color: #e8f0fe;
        }
        QTreeWidget::item:selected {
            background-color: #4472C4;
            color: white;
        }
        
        /* List widget */
        QListWidget {
            background-color: white;
            border: 1px solid #dee2e6;
            border-radius: 4px;
        }
        QListWidget::item {
            padding: 8px;
        }
        QListWidget::item:hover {
            background-color: #e8f0fe;
        }
        QListWidget::item:selected {
            background-color: #4472C4;
            color: white;
        }
        
        /* Scrollbars - vertical */
        QScrollBar:vertical {
            width: 14px;
            background: #f8f9fa;
            border-radius: 7px;
            margin: 2px;
        }
        QScrollBar::handle:vertical {
            background: #adb5bd;
            border-radius: 6px;
            min-height: 30px;
        }
        QScrollBar::handle:vertical:hover {
            background: #868e96;
        }
        QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {
            height: 0px;
        }
        
        /* Scrollbars - horizontal */
        QScrollBar:horizontal {
            height: 14px;
            background: #f8f9fa;
            border-radius: 7px;
            margin: 2px;
        }
        QScrollBar::handle:horizontal {
            background: #adb5bd;
            border-radius: 6px;
            min-width: 30px;
        }
        QScrollBar::handle:horizontal:hover {
            background: #868e96;
        }
        QScrollBar::add-line:horizontal, QScrollBar::sub-line:horizontal {
            width: 0px;
        }
    """)
    
    # Initialize database
    get_database_service()
    
    # Show profile dialog
    profile_dialog = ProfileDialog()
    
    if profile_dialog.exec() and profile_dialog.selected_profile:
        # Show main window
        main_window = MainWindow(profile_dialog.selected_profile)
        main_window.show()
        
        return app.exec()
    
    return 0


if __name__ == "__main__":
    sys.exit(main())
