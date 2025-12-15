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
    
    # Apply basic styling
    app.setStyleSheet("""
        QMainWindow {
            background-color: #f5f5f5;
        }
        QGroupBox {
            font-weight: bold;
            border: 1px solid #ccc;
            border-radius: 5px;
            margin-top: 10px;
            padding-top: 10px;
        }
        QGroupBox::title {
            subcontrol-origin: margin;
            left: 10px;
            padding: 0 5px;
        }
        QPushButton {
            padding: 5px 15px;
            border-radius: 3px;
        }
        QTableWidget {
            gridline-color: #ddd;
        }
        QTableWidget::item:selected {
            background-color: #4472C4;
            color: white;
        }
        QTabWidget::pane {
            border: 1px solid #ccc;
            background: white;
        }
        QTabBar::tab {
            padding: 8px 20px;
            margin-right: 2px;
        }
        QTabBar::tab:selected {
            background: white;
            border-bottom: 2px solid #4472C4;
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
