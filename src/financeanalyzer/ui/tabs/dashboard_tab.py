"""Dashboard tab for FinanceAnalyzer."""

from datetime import date, timedelta
from decimal import Decimal

from PySide6.QtWidgets import (
    QWidget,
    QVBoxLayout,
    QHBoxLayout,
    QTreeWidget,
    QTreeWidgetItem,
    QDateEdit,
    QPushButton,
    QLabel,
    QGroupBox,
    QHeaderView,
)
from PySide6.QtCore import Qt, QDate
from PySide6.QtGui import QFont, QColor

from ...services.entry_service import EntryService
from ...services.category_service import CategoryService


class DashboardTab(QWidget):
    """Dashboard tab showing entries grouped by category."""
    
    def __init__(self, profile_id: int, parent=None):
        super().__init__(parent)
        self.profile_id = profile_id
        
        self._setup_ui()
        self.refresh()
    
    def _setup_ui(self):
        """Set up the tab UI."""
        layout = QVBoxLayout(self)
        layout.setContentsMargins(10, 10, 10, 10)
        
        # Filter section
        filter_group = QGroupBox("Date Filter")
        filter_layout = QHBoxLayout(filter_group)
        
        filter_layout.addWidget(QLabel("From:"))
        self.start_date = QDateEdit()
        self.start_date.setCalendarPopup(True)
        self.start_date.setDate(QDate.currentDate().addMonths(-1))
        filter_layout.addWidget(self.start_date)
        
        filter_layout.addWidget(QLabel("To:"))
        self.end_date = QDateEdit()
        self.end_date.setCalendarPopup(True)
        self.end_date.setDate(QDate.currentDate())
        filter_layout.addWidget(self.end_date)
        
        self.filter_btn = QPushButton("Apply Filter")
        self.filter_btn.clicked.connect(self.refresh)
        filter_layout.addWidget(self.filter_btn)
        
        # Quick filters
        self.this_month_btn = QPushButton("This Month")
        self.this_month_btn.clicked.connect(self._set_this_month)
        filter_layout.addWidget(self.this_month_btn)
        
        self.this_year_btn = QPushButton("This Year")
        self.this_year_btn.clicked.connect(self._set_this_year)
        filter_layout.addWidget(self.this_year_btn)
        
        filter_layout.addStretch()
        layout.addWidget(filter_group)
        
        # Tree view
        self.tree = QTreeWidget()
        self.tree.setHeaderLabels(["Category / Description", "Sender/Receiver", "Date", "Amount"])
        self.tree.setAlternatingRowColors(True)
        self.tree.setRootIsDecorated(True)
        
        header = self.tree.header()
        header.setSectionResizeMode(0, QHeaderView.Stretch)
        header.setSectionResizeMode(1, QHeaderView.ResizeToContents)
        header.setSectionResizeMode(2, QHeaderView.ResizeToContents)
        header.setSectionResizeMode(3, QHeaderView.ResizeToContents)
        
        layout.addWidget(self.tree)
        
        # Summary section
        summary_layout = QHBoxLayout()
        
        self.total_income_label = QLabel("Total Income: €0.00")
        self.total_income_label.setStyleSheet("color: #3fb950; font-weight: bold; font-size: 14px;")
        summary_layout.addWidget(self.total_income_label)
        
        self.total_expense_label = QLabel("Total Expenses: €0.00")
        self.total_expense_label.setStyleSheet("color: #f85149; font-weight: bold; font-size: 14px;")
        summary_layout.addWidget(self.total_expense_label)
        
        self.net_label = QLabel("Net: €0.00")
        self.net_label.setStyleSheet("font-weight: bold; font-size: 14px; color: #c9d1d9;")
        summary_layout.addWidget(self.net_label)
        
        summary_layout.addStretch()
        layout.addLayout(summary_layout)
    
    def set_profile(self, profile_id: int):
        """Set the current profile."""
        self.profile_id = profile_id
        self.refresh()
    
    def _set_this_month(self):
        """Set filter to current month."""
        today = QDate.currentDate()
        self.start_date.setDate(QDate(today.year(), today.month(), 1))
        self.end_date.setDate(today)
        self.refresh()
    
    def _set_this_year(self):
        """Set filter to current year."""
        today = QDate.currentDate()
        self.start_date.setDate(QDate(today.year(), 1, 1))
        self.end_date.setDate(today)
        self.refresh()
    
    def refresh(self):
        """Refresh the dashboard data."""
        self.tree.clear()
        
        start = self.start_date.date().toPython()
        end = self.end_date.date().toPython()
        
        entry_service = EntryService(self.profile_id)
        category_service = CategoryService(self.profile_id)
        
        # Get entries grouped by category
        entries = entry_service.get_all_entries(start_date=start, end_date=end)
        categories = {c.id: c for c in category_service.get_all_categories()}
        
        # Group by category
        grouped: dict[int | None, list] = {}
        for entry in entries:
            cat_id = entry.category_id
            if cat_id not in grouped:
                grouped[cat_id] = []
            grouped[cat_id].append(entry)
        
        total_income = Decimal("0")
        total_expense = Decimal("0")
        
        # Add categorized entries
        for cat_id, cat_entries in sorted(grouped.items(), key=lambda x: (x[0] is None, x[0])):
            if cat_id is None:
                cat_name = "⚠️ Uncategorized"
            else:
                cat = categories.get(cat_id)
                cat_name = cat.name if cat else f"Unknown ({cat_id})"
            
            # Calculate category total
            cat_total = sum(e.amount for e in cat_entries)
            
            # Create category item
            cat_item = QTreeWidgetItem([
                f"📁 {cat_name} ({len(cat_entries)})",
                "",
                "",
                f"€{cat_total:,.2f}"
            ])
            cat_item.setFont(0, QFont("Arial", 10, QFont.Bold))
            
            # Color based on total
            if cat_total > 0:
                cat_item.setForeground(3, QColor("#3fb950"))
            else:
                cat_item.setForeground(3, QColor("#f85149"))
            
            # Add entries as children
            for entry in sorted(cat_entries, key=lambda e: e.entry_date, reverse=True):
                sender_receiver = getattr(entry, 'sender_receiver', None) or ""
                entry_item = QTreeWidgetItem([
                    entry.description[:100],
                    sender_receiver[:50] if sender_receiver else "",
                    entry.entry_date.strftime("%d.%m.%Y"),
                    f"€{entry.amount:,.2f}"
                ])
                
                if entry.amount > 0:
                    entry_item.setForeground(3, QColor("#3fb950"))
                    total_income += entry.amount
                else:
                    entry_item.setForeground(3, QColor("#f85149"))
                    total_expense += entry.amount
                
                cat_item.addChild(entry_item)
            
            self.tree.addTopLevelItem(cat_item)
        
        # Expand all by default
        self.tree.expandAll()
        
        # Update summary
        net = total_income + total_expense  # expense is negative
        self.total_income_label.setText(f"Total Income: €{total_income:,.2f}")
        self.total_expense_label.setText(f"Total Expenses: €{abs(total_expense):,.2f}")
        self.net_label.setText(f"Net: €{net:,.2f}")
        
        if net >= 0:
            self.net_label.setStyleSheet("color: #3fb950; font-weight: bold; font-size: 14px;")
        else:
            self.net_label.setStyleSheet("color: #f85149; font-weight: bold; font-size: 14px;")
        
        entry_service.close()
        category_service.close()
