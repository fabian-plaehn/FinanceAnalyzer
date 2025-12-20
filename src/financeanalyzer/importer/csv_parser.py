"""Config-driven CSV parser for FinanceAnalyzer."""

from datetime import datetime, date
from decimal import Decimal, InvalidOperation
from typing import List, Optional, NamedTuple
from pathlib import Path
import csv
import re

from ..database.models import CSVConfiguration


class ParsedEntry(NamedTuple):
    """Represents a parsed CSV entry."""
    entry_date: date
    amount: Decimal
    description: str
    import_hash: str | None = None


class CSVParseError(Exception):
    """Raised when CSV parsing fails."""
    pass


class CSVParser:
    """Config-driven CSV parser.
    
    Parses CSV files using a CSVConfiguration that defines
    column mappings and parsing settings.
    """
    
    def __init__(self, config: CSVConfiguration):
        """Initialize the parser with a configuration.
        
        Args:
            config: The CSV configuration to use.
        """
        self.config = config
    
    def _parse_amount(self, value: str) -> Decimal:
        """Parse an amount string to Decimal.
        
        Handles German number formatting (comma as decimal separator).
        
        Args:
            value: The amount string (e.g., "1.234,56" or "-123,45").
        
        Returns:
            The parsed Decimal value.
        
        Raises:
            CSVParseError: If the amount cannot be parsed.
        """
        try:
            # Remove thousands separator and replace decimal separator
            cleaned = value.strip()
            
            # Handle German format: 1.234,56 -> 1234.56
            if self.config.thousands_separator:
                cleaned = cleaned.replace(self.config.thousands_separator, "")
            if self.config.decimal_separator:
                cleaned = cleaned.replace(self.config.decimal_separator, ".")
            
            return Decimal(cleaned)
        except InvalidOperation as e:
            raise CSVParseError(f"Could not parse amount '{value}': {e}")
    
    def _parse_date(self, value: str) -> date:
        """Parse a date string.
        
        Args:
            value: The date string.
        
        Returns:
            The parsed date.
        
        Raises:
            CSVParseError: If the date cannot be parsed.
        """
        try:
            dt = datetime.strptime(value.strip(), self.config.date_format)
            return dt.date()
        except ValueError as e:
            raise CSVParseError(f"Could not parse date '{value}' with format '{self.config.date_format}': {e}")
    
    def preview(self, file_path: str | Path, max_rows: int = 10) -> tuple[List[str], List[List[str]]]:
        """Preview a CSV file without full parsing.
        
        Args:
            file_path: Path to the CSV file.
            max_rows: Maximum number of data rows to preview.
        
        Returns:
            Tuple of (headers, rows) where rows is a list of row data.
        """
        file_path = Path(file_path)
        
        with open(file_path, "r", encoding=self.config.encoding, errors="replace") as f:
            # Skip rows if configured
            for _ in range(self.config.skip_rows):
                next(f, None)
            
            reader = csv.reader(f, delimiter=self.config.delimiter)
            
            # Get headers
            headers = next(reader, [])
            
            # Get preview rows
            rows = []
            for i, row in enumerate(reader):
                if i >= max_rows:
                    break
                rows.append(row)
            
            return headers, rows
    
    def parse(self, file_path: str | Path) -> List[ParsedEntry]:
        """Parse a CSV file into entries.
        
        Args:
            file_path: Path to the CSV file.
        
        Returns:
            List of ParsedEntry objects.
        
        Raises:
            CSVParseError: If parsing fails.
        """
        file_path = Path(file_path)
        entries: List[ParsedEntry] = []
        
        with open(file_path, "r", encoding=self.config.encoding, errors="replace") as f:
            # Skip rows if configured
            for _ in range(self.config.skip_rows):
                next(f, None)
            
            reader = csv.DictReader(f, delimiter=self.config.delimiter)
            
            # Validate required columns exist
            if reader.fieldnames is None:
                raise CSVParseError("CSV file has no headers")
            
            required_cols = [
                self.config.date_column,
                self.config.amount_column,
                self.config.description_column
            ]
            
            for col in required_cols:
                if col not in reader.fieldnames:
                    raise CSVParseError(
                        f"Required column '{col}' not found in CSV. "
                        f"Available columns: {reader.fieldnames}"
                    )
            
            # Parse rows
            for row_num, row in enumerate(reader, start=2):  # +2 for 1-indexed + header
                try:
                    entry_date = self._parse_date(row[self.config.date_column])
                    amount = self._parse_amount(row[self.config.amount_column])
                    description = row[self.config.description_column].strip()
                    
                    entries.append(ParsedEntry(
                        entry_date=entry_date,
                        amount=amount,
                        description=description
                    ))
                except CSVParseError as e:
                    raise CSVParseError(f"Error on row {row_num}: {e}")
                except KeyError as e:
                    raise CSVParseError(f"Error on row {row_num}: Missing column {e}")
        
        return entries


def detect_csv_settings(file_path: str | Path) -> dict:
    """Auto-detect CSV settings like delimiter and encoding.
    
    Args:
        file_path: Path to the CSV file.
    
    Returns:
        Dict with detected settings: delimiter, encoding, headers.
    """
    file_path = Path(file_path)
    
    # Try common encodings
    encodings = ["utf-8", "latin-1", "cp1252", "iso-8859-1"]
    
    for encoding in encodings:
        try:
            with open(file_path, "r", encoding=encoding) as f:
                sample = f.read(4096)
                
            # Detect delimiter
            delimiters = [";", ",", "\t", "|"]
            delimiter_counts = {d: sample.count(d) for d in delimiters}
            delimiter = max(delimiter_counts, key=delimiter_counts.get)
            
            # Parse first line as headers
            lines = sample.split("\n")
            if lines:
                headers = [h.strip().strip('"') for h in lines[0].split(delimiter)]
            else:
                headers = []
            
            return {
                "encoding": encoding,
                "delimiter": delimiter,
                "headers": headers
            }
        except UnicodeDecodeError:
            continue
    
    # Fallback
    return {
        "encoding": "utf-8",
        "delimiter": ",",
        "headers": []
    }
