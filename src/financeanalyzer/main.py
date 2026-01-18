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
    
    # Apply modern dark theme styling with premium aesthetics
    app.setStyleSheet("""
        /* ========================================
           FINANCEANALYZER - MODERN DARK THEME
           Premium fintech-inspired design system
           ======================================== */
        
        /* === GLOBAL & MAIN WINDOW === */
        QMainWindow, QDialog, QWidget {
            background-color: #0d1117;
            color: #e6edf3;
            font-family: 'Segoe UI', 'SF Pro Display', system-ui, sans-serif;
            font-size: 13px;
        }
        
        QMainWindow {
            background: qlineargradient(x1:0, y1:0, x2:1, y2:1,
                stop:0 #0d1117, stop:1 #161b22);
        }
        
        /* === GROUP BOXES (Cards) === */
        QGroupBox {
            font-weight: 600;
            font-size: 13px;
            border: 1px solid #30363d;
            border-radius: 12px;
            margin-top: 16px;
            padding: 20px 16px 16px 16px;
            background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                stop:0 #161b22, stop:1 #0d1117);
        }
        QGroupBox::title {
            subcontrol-origin: margin;
            left: 16px;
            top: 4px;
            padding: 4px 12px;
            background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
                stop:0 #238636, stop:1 #2ea043);
            border-radius: 6px;
            color: #ffffff;
        }
        
        /* === BUTTONS - Primary (Gradient) === */
        QPushButton {
            padding: 10px 20px;
            border: none;
            border-radius: 8px;
            background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
                stop:0 #238636, stop:1 #2ea043);
            color: #ffffff;
            font-weight: 600;
            font-size: 13px;
            min-width: 80px;
        }
        QPushButton:hover {
            background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
                stop:0 #2ea043, stop:1 #3fb950);
        }
        QPushButton:pressed {
            background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
                stop:0 #196c2e, stop:1 #238636);
        }
        QPushButton:disabled {
            background: #21262d;
            color: #484f58;
        }
        
        /* === BUTTONS - Secondary/Clear === */
        QPushButton[flat="true"], QPushButton#clearBtn {
            background: #21262d;
            border: 1px solid #30363d;
            color: #c9d1d9;
        }
        QPushButton[flat="true"]:hover, QPushButton#clearBtn:hover {
            background: #30363d;
            border-color: #8b949e;
        }
        
        /* === BUTTONS - Danger === */
        QPushButton#deleteBtn {
            background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
                stop:0 #da3633, stop:1 #f85149);
        }
        QPushButton#deleteBtn:hover {
            background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
                stop:0 #f85149, stop:1 #ff7b72);
        }
        
        /* === BUTTONS - Success === */
        QPushButton#successBtn {
            background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
                stop:0 #238636, stop:1 #3fb950);
        }
        QPushButton#successBtn:hover {
            background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
                stop:0 #3fb950, stop:1 #56d364);
        }
        
        /* === TABLES === */
        QTableWidget, QTableView {
            gridline-color: #21262d;
            background-color: #0d1117;
            alternate-background-color: #161b22;
            border: 1px solid #30363d;
            border-radius: 8px;
            selection-background-color: #1f6feb;
            selection-color: #ffffff;
        }
        QTableWidget::item, QTableView::item {
            padding: 10px 8px;
            border-bottom: 1px solid #21262d;
        }
        QTableWidget::item:selected, QTableView::item:selected {
            background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
                stop:0 #1f6feb, stop:1 #388bfd);
            color: #ffffff;
        }
        QTableWidget::item:hover:!selected, QTableView::item:hover:!selected {
            background-color: #21262d;
        }
        QHeaderView::section {
            background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                stop:0 #21262d, stop:1 #161b22);
            padding: 12px 10px;
            border: none;
            border-bottom: 2px solid #30363d;
            font-weight: 600;
            color: #8b949e;
            text-transform: uppercase;
            font-size: 11px;
            letter-spacing: 0.5px;
        }
        
        /* === TAB WIDGET === */
        QTabWidget::pane {
            border: 1px solid #30363d;
            background: #0d1117;
            border-radius: 0 12px 12px 12px;
            top: -1px;
        }
        QTabBar::tab {
            padding: 12px 28px;
            margin-right: 4px;
            background: #21262d;
            border: 1px solid #30363d;
            border-bottom: none;
            border-radius: 10px 10px 0 0;
            color: #8b949e;
            font-weight: 500;
        }
        QTabBar::tab:selected {
            background: #0d1117;
            border-bottom: 3px solid #58a6ff;
            color: #58a6ff;
            font-weight: 600;
        }
        QTabBar::tab:hover:!selected {
            background: #30363d;
            color: #c9d1d9;
        }
        
        /* === COMBO BOXES === */
        QComboBox {
            padding: 8px 14px;
            border: 1px solid #30363d;
            border-radius: 8px;
            background: #21262d;
            color: #c9d1d9;
            min-width: 120px;
            font-size: 13px;
        }
        QComboBox:hover {
            border-color: #58a6ff;
            background: #30363d;
        }
        QComboBox:focus {
            border-color: #58a6ff;
            border-width: 2px;
        }
        QComboBox::drop-down {
            border: none;
            padding-right: 10px;
            width: 20px;
        }
        QComboBox::down-arrow {
            image: none;
            border-left: 5px solid transparent;
            border-right: 5px solid transparent;
            border-top: 6px solid #8b949e;
        }
        QComboBox QAbstractItemView {
            background: #21262d;
            border: 1px solid #30363d;
            border-radius: 8px;
            padding: 4px;
            selection-background-color: #1f6feb;
        }
        
        /* === LINE EDITS === */
        QLineEdit {
            padding: 10px 14px;
            border: 1px solid #30363d;
            border-radius: 8px;
            background: #21262d;
            color: #c9d1d9;
            font-size: 13px;
            selection-background-color: #1f6feb;
        }
        QLineEdit:focus {
            border-color: #58a6ff;
            border-width: 2px;
            background: #161b22;
        }
        QLineEdit:hover {
            border-color: #484f58;
        }
        QLineEdit::placeholder {
            color: #484f58;
        }
        
        /* === DATE EDITS === */
        QDateEdit {
            padding: 8px 12px;
            border: 1px solid #30363d;
            border-radius: 8px;
            background: #21262d;
            color: #c9d1d9;
        }
        QDateEdit:hover {
            border-color: #58a6ff;
        }
        QDateEdit:focus {
            border-color: #58a6ff;
            border-width: 2px;
        }
        QDateEdit::drop-down {
            border: none;
            padding-right: 8px;
        }
        QCalendarWidget {
            background: #21262d;
            border: 1px solid #30363d;
            border-radius: 8px;
        }
        QCalendarWidget QToolButton {
            color: #c9d1d9;
            background: transparent;
            border: none;
            padding: 6px;
        }
        QCalendarWidget QToolButton:hover {
            background: #30363d;
            border-radius: 4px;
        }
        
        /* === TOOLBAR === */
        QToolBar {
            background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                stop:0 #161b22, stop:1 #0d1117);
            border-bottom: 1px solid #30363d;
            padding: 8px 12px;
            spacing: 8px;
        }
        QToolBar QToolButton {
            padding: 8px 14px;
            border-radius: 6px;
            border: none;
            color: #c9d1d9;
            font-weight: 500;
        }
        QToolBar QToolButton:hover {
            background: #30363d;
        }
        QToolBar QToolButton:pressed {
            background: #21262d;
        }
        QToolBar::separator {
            width: 1px;
            background: #30363d;
            margin: 4px 8px;
        }
        
        /* === STATUS BAR === */
        QStatusBar {
            background: #161b22;
            border-top: 1px solid #30363d;
            padding: 6px 12px;
            color: #8b949e;
            font-size: 12px;
        }
        QStatusBar::item {
            border: none;
        }
        
        /* === TREE WIDGET === */
        QTreeWidget {
            background-color: #0d1117;
            alternate-background-color: #161b22;
            border: 1px solid #30363d;
            border-radius: 8px;
            selection-background-color: #1f6feb;
        }
        QTreeWidget::item {
            padding: 8px 6px;
            border-bottom: 1px solid #21262d;
        }
        QTreeWidget::item:hover {
            background-color: #21262d;
        }
        QTreeWidget::item:selected {
            background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
                stop:0 #1f6feb, stop:1 #388bfd);
            color: #ffffff;
        }
        QTreeWidget::branch {
            background: transparent;
        }
        QTreeWidget::branch:has-children:!has-siblings:closed,
        QTreeWidget::branch:closed:has-children:has-siblings {
            border-image: none;
            image: none;
        }
        QTreeWidget::branch:open:has-children:!has-siblings,
        QTreeWidget::branch:open:has-children:has-siblings {
            border-image: none;
            image: none;
        }
        
        /* === LIST WIDGET === */
        QListWidget {
            background-color: #0d1117;
            alternate-background-color: #161b22;
            border: 1px solid #30363d;
            border-radius: 8px;
            outline: none;
        }
        QListWidget::item {
            padding: 12px 16px;
            border-bottom: 1px solid #21262d;
            border-radius: 0;
        }
        QListWidget::item:hover {
            background-color: #21262d;
        }
        QListWidget::item:selected {
            background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
                stop:0 #1f6feb, stop:1 #388bfd);
            color: #ffffff;
            border-radius: 6px;
        }
        
        /* === SCROLLBARS - Vertical (Slim & Modern) === */
        QScrollBar:vertical {
            width: 10px;
            background: transparent;
            border-radius: 5px;
            margin: 2px;
        }
        QScrollBar::handle:vertical {
            background: #30363d;
            border-radius: 5px;
            min-height: 40px;
        }
        QScrollBar::handle:vertical:hover {
            background: #484f58;
        }
        QScrollBar::handle:vertical:pressed {
            background: #6e7681;
        }
        QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical,
        QScrollBar::add-page:vertical, QScrollBar::sub-page:vertical {
            height: 0px;
            background: transparent;
        }
        
        /* === SCROLLBARS - Horizontal === */
        QScrollBar:horizontal {
            height: 10px;
            background: transparent;
            border-radius: 5px;
            margin: 2px;
        }
        QScrollBar::handle:horizontal {
            background: #30363d;
            border-radius: 5px;
            min-width: 40px;
        }
        QScrollBar::handle:horizontal:hover {
            background: #484f58;
        }
        QScrollBar::handle:horizontal:pressed {
            background: #6e7681;
        }
        QScrollBar::add-line:horizontal, QScrollBar::sub-line:horizontal,
        QScrollBar::add-page:horizontal, QScrollBar::sub-page:horizontal {
            width: 0px;
            background: transparent;
        }
        
        /* === LABELS === */
        QLabel {
            color: #c9d1d9;
        }
        
        /* === MENU BAR === */
        QMenuBar {
            background: #161b22;
            border-bottom: 1px solid #30363d;
            padding: 4px;
        }
        QMenuBar::item {
            padding: 8px 14px;
            background: transparent;
            border-radius: 6px;
            color: #c9d1d9;
        }
        QMenuBar::item:selected {
            background: #30363d;
        }
        QMenu {
            background: #21262d;
            border: 1px solid #30363d;
            border-radius: 8px;
            padding: 6px;
        }
        QMenu::item {
            padding: 10px 30px 10px 20px;
            border-radius: 4px;
            color: #c9d1d9;
        }
        QMenu::item:selected {
            background: #1f6feb;
            color: #ffffff;
        }
        QMenu::separator {
            height: 1px;
            background: #30363d;
            margin: 6px 10px;
        }
        
        /* === CHECKBOXES === */
        QCheckBox {
            spacing: 8px;
            color: #c9d1d9;
        }
        QCheckBox::indicator {
            width: 18px;
            height: 18px;
            border: 2px solid #30363d;
            border-radius: 4px;
            background: #21262d;
        }
        QCheckBox::indicator:hover {
            border-color: #58a6ff;
        }
        QCheckBox::indicator:checked {
            background: qlineargradient(x1:0, y1:0, x2:1, y2:1,
                stop:0 #238636, stop:1 #3fb950);
            border-color: #238636;
        }
        
        /* === SPINBOX === */
        QSpinBox, QDoubleSpinBox {
            padding: 8px 12px;
            border: 1px solid #30363d;
            border-radius: 8px;
            background: #21262d;
            color: #c9d1d9;
        }
        QSpinBox:focus, QDoubleSpinBox:focus {
            border-color: #58a6ff;
        }
        
        /* === WIZARD === */
        QWizard {
            background: #0d1117;
        }
        QWizardPage {
            background: #0d1117;
        }
        
        /* === DIALOGS === */
        QDialog {
            background: #0d1117;
        }
        
        /* === FRAME === */
        QFrame[frameShape="4"], QFrame[frameShape="5"] {
            background: #30363d;
        }
        QFrame {
            border: none;
        }
        
        /* === MESSAGE BOX === */
        QMessageBox {
            background: #161b22;
        }
        QMessageBox QLabel {
            color: #c9d1d9;
            font-size: 13px;
        }
        
        /* === TOOLTIPS === */
        QToolTip {
            background: #21262d;
            border: 1px solid #30363d;
            border-radius: 6px;
            padding: 8px 12px;
            color: #c9d1d9;
            font-size: 12px;
        }
    """)
    
    # Initialize database
    get_database_service()
    
    # Main loop - allows returning to profile selection
    while True:
        # Show profile dialog
        profile_dialog = ProfileDialog()
        
        if profile_dialog.exec() and profile_dialog.selected_profile:
            # Show main window
            main_window = MainWindow(profile_dialog.selected_profile)
            
            # Track if user wants to switch profiles
            switch_requested = [False]  # Use list to modify in closure
            
            def on_switch_requested():
                switch_requested[0] = True
            
            main_window.switch_profile_requested.connect(on_switch_requested)
            main_window.show()
            
            app.exec()
            
            # If switch was requested, loop back to profile dialog
            if switch_requested[0]:
                continue
        
        # Exit the loop
        break
    
    return 0


if __name__ == "__main__":
    sys.exit(main())

