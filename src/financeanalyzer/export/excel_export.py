"""Excel export service for FinanceAnalyzer."""

from datetime import date
from decimal import Decimal
from pathlib import Path
from typing import Optional

from openpyxl import Workbook
from openpyxl.styles import Font, Alignment, Border, Side, PatternFill
from openpyxl.utils import get_column_letter

from ..services.entry_service import EntryService
from ..services.category_service import CategoryService


class ExcelExporter:
    """Service for exporting entries to Excel."""
    
    def __init__(self, profile_id: int):
        """Initialize the exporter.
        
        Args:
            profile_id: The profile ID to export from.
        """
        self.profile_id = profile_id
    
    def export(
        self,
        file_path: str | Path,
        start_date: Optional[date] = None,
        end_date: Optional[date] = None,
        include_uncategorized: bool = False
    ) -> None:
        """Export entries to an Excel file.
        
        Args:
            file_path: Path to save the Excel file.
            start_date: Filter entries on or after this date.
            end_date: Filter entries on or before this date.
            include_uncategorized: Whether to include uncategorized entries.
        """
        file_path = Path(file_path)
        
        # Get data
        entry_service = EntryService(self.profile_id)
        category_service = CategoryService(self.profile_id)
        
        entries = entry_service.get_all_entries(
            start_date=start_date,
            end_date=end_date
        )
        categories = {c.id: c for c in category_service.get_all_categories()}
        
        entry_service.close()
        category_service.close()
        
        # Group entries by category
        grouped: dict[int | None, list] = {}
        for entry in entries:
            # Skip uncategorized if not included
            if entry.category_id is None and not include_uncategorized:
                continue
            
            cat_id = entry.category_id
            if cat_id not in grouped:
                grouped[cat_id] = []
            grouped[cat_id].append(entry)
        
        # Create workbook
        wb = Workbook()
        ws = wb.active
        ws.title = "Financial Overview"
        
        # Styles
        header_font = Font(bold=True, size=12)
        header_fill = PatternFill(start_color="4472C4", end_color="4472C4", fill_type="solid")
        header_font_white = Font(bold=True, size=12, color="FFFFFF")
        
        category_font = Font(bold=True, size=11)
        category_fill = PatternFill(start_color="D9E2F3", end_color="D9E2F3", fill_type="solid")
        
        sum_font = Font(bold=True, italic=True)
        sum_fill = PatternFill(start_color="E2EFDA", end_color="E2EFDA", fill_type="solid")
        
        border = Border(
            left=Side(style='thin'),
            right=Side(style='thin'),
            top=Side(style='thin'),
            bottom=Side(style='thin')
        )
        
        money_positive = Font(color="006400")  # Dark green
        money_negative = Font(color="8B0000")  # Dark red
        
        current_row = 1
        grand_total = Decimal("0")
        
        # Sort categories: named categories first (alphabetically), then uncategorized
        sorted_cats = sorted(
            grouped.items(),
            key=lambda x: (x[0] is None, categories.get(x[0], type('', (), {'name': 'ZZZ'})()).name if x[0] else "ZZZ")
        )
        
        for cat_id, cat_entries in sorted_cats:
            # Category header
            if cat_id is None:
                cat_name = "Uncategorized"
            else:
                cat = categories.get(cat_id)
                cat_name = cat.name if cat else f"Unknown ({cat_id})"
            
            ws.cell(row=current_row, column=1, value=f"📁 {cat_name}")
            ws.merge_cells(start_row=current_row, start_column=1, end_row=current_row, end_column=4)
            
            for col in range(1, 5):
                cell = ws.cell(row=current_row, column=col)
                cell.font = category_font
                cell.fill = category_fill
                cell.border = border
            
            current_row += 1
            
            # Column headers
            headers = ["Date", "Description", "Source", "Amount"]
            for col, header in enumerate(headers, 1):
                cell = ws.cell(row=current_row, column=col, value=header)
                cell.font = header_font_white
                cell.fill = header_fill
                cell.border = border
                cell.alignment = Alignment(horizontal='center')
            
            current_row += 1
            
            # Entries
            cat_total = Decimal("0")
            for entry in sorted(cat_entries, key=lambda e: e.entry_date):
                ws.cell(row=current_row, column=1, value=entry.entry_date.strftime("%d.%m.%Y"))
                ws.cell(row=current_row, column=2, value=entry.description[:100])
                ws.cell(row=current_row, column=3, value=entry.source)
                
                amount_cell = ws.cell(row=current_row, column=4, value=float(entry.amount))
                amount_cell.number_format = '#,##0.00 €'
                amount_cell.alignment = Alignment(horizontal='right')
                
                if entry.amount >= 0:
                    amount_cell.font = money_positive
                else:
                    amount_cell.font = money_negative
                
                for col in range(1, 5):
                    ws.cell(row=current_row, column=col).border = border
                
                cat_total += entry.amount
                current_row += 1
            
            # Category subtotal
            ws.cell(row=current_row, column=1, value="Subtotal")
            ws.merge_cells(start_row=current_row, start_column=1, end_row=current_row, end_column=3)
            
            subtotal_cell = ws.cell(row=current_row, column=4, value=float(cat_total))
            subtotal_cell.number_format = '#,##0.00 €'
            subtotal_cell.alignment = Alignment(horizontal='right')
            
            for col in range(1, 5):
                cell = ws.cell(row=current_row, column=col)
                cell.font = sum_font
                cell.fill = sum_fill
                cell.border = border
            
            grand_total += cat_total
            current_row += 2  # Empty row between categories
        
        # Grand total
        if grouped:
            ws.cell(row=current_row, column=1, value="GRAND TOTAL")
            ws.merge_cells(start_row=current_row, start_column=1, end_row=current_row, end_column=3)
            
            grand_cell = ws.cell(row=current_row, column=4, value=float(grand_total))
            grand_cell.number_format = '#,##0.00 €'
            grand_cell.alignment = Alignment(horizontal='right')
            
            for col in range(1, 5):
                cell = ws.cell(row=current_row, column=col)
                cell.font = Font(bold=True, size=12)
                cell.fill = PatternFill(start_color="FFC000", end_color="FFC000", fill_type="solid")
                cell.border = border
        
        # Adjust column widths
        ws.column_dimensions['A'].width = 12
        ws.column_dimensions['B'].width = 50
        ws.column_dimensions['C'].width = 15
        ws.column_dimensions['D'].width = 15
        
        # Save
        wb.save(file_path)
