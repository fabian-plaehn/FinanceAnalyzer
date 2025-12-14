import pandas as pd
from datetime import datetime
from typing import List, Optional, Dict
import io

class CSVParser:
    """
    Parses CSV files into a standardized pandas DataFrame.
    Expected output columns: ['date', 'amount', 'description', 'source', 'category']
    """
    
    REQUIRED_COLUMNS = ['date', 'amount'] # Desc can be constructed
    
    # default mappings to look for
    COLUMN_MAPPINGS = {
        'date': ['date', 'datum', 'buchungstag', 'valuta'],
        'amount': ['amount', 'betrag', 'wert', 'umsatz'],
        # We will try to find these specific ones first, otherwise fallback to generic
        'description_main': ['description', 'desc', 'verwendungszweck', 'buchungstext'],
        'description_extra': ['name zahlungsbeteiligter', 'beguenstigter', 'bemerkung', 'info']
    }

    def parse_csv(self, file_path: str, source_name: str = "Unknown") -> pd.DataFrame:
        try:
            # 1. Detect Separator
            sep = self._detect_separator(file_path)
            
            # 2. Read CSV
            # Keep original headers to check for german mapping
            df = pd.read_csv(file_path, sep=sep)
            
            # Normalize column names for mapping
            normalized_cols = {c: c.lower().strip() for c in df.columns}
            df.rename(columns=normalized_cols, inplace=True)
            
            # 3. Map Columns
            mapped_cols = {}
            for target, candidates in self.COLUMN_MAPPINGS.items():
                for col in df.columns:
                    if any(cand in col for cand in candidates):
                        # Store map: normalized_col -> internal_target
                        # Actually we want: internal_target -> normalized_col
                        # Use list because we might have multiple matches for desc
                        if target not in mapped_cols:
                            mapped_cols[target] = []
                        mapped_cols[target].append(col)
                        
            # Validate
            missing = [req for req in self.REQUIRED_COLUMNS if req not in mapped_cols]
            if missing:
                # If 'date' is missing but 'valuta' exists under 'date' mapping, we are good.
                # Logic above maps them to 'date' key.
                raise ValueError(f"Could not automatically map columns: {missing}. Found: {df.columns.tolist()}")

            # 4. Construct Data
            final_df = pd.DataFrame()
            
            # Date
            date_col = mapped_cols['date'][0] # Take first match
            final_df['date'] = pd.to_datetime(df[date_col], dayfirst=True, errors='coerce')
            
            # Amount
            amt_col = mapped_cols['amount'][0]
            final_df['amount'] = df[amt_col].apply(self._parse_amount)

            # Description
            # Combine all found description columns
            desc_cols = mapped_cols.get('description_main', []) + mapped_cols.get('description_extra', [])
            if desc_cols:
                # Join non-null values
                final_df['description'] = df[desc_cols].apply(
                    lambda row: ' | '.join(row.dropna().astype(str)), axis=1
                )
            else:
                final_df['description'] = "No Description"

            # Metadata
            final_df['source'] = source_name
            final_df['category'] = None
            
            # Remove invalid rows (no date or no amount)
            final_df.dropna(subset=['date', 'amount'], inplace=True)
            
            return final_df[self.REQUIRED_COLUMNS + ['description', 'source', 'category']]
            
        except Exception as e:
            print(f"Error parsing {file_path}: {e}")
            return pd.DataFrame()

    def _detect_separator(self, file_path: str) -> str:
        with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
            line = f.readline()
            if ';' in line:
                return ';'
            return ','

    def _parse_amount(self, value):
        if pd.isna(value):
            return 0.0
        if isinstance(value, (int, float)):
            return float(value)
        if isinstance(value, str):
            # German 1.000,00 -> 1000.00
            # Common 1,000.00 -> 1000.00
            
            # Heuristic: if ',' is last separator, it's decimal (European)
            # unless it's like 1,000 (US). 
            # If both . and , exist:
            # 1.234,56 (German) -> remove ., replace ,
            # 1,234.56 (US) -> remove ,
            
            val = value.strip()
            # Remove currency symbols if present? (e.g. €)
            val = val.replace('€', '').replace('EUR', '').strip()
            
            if ',' in val and '.' in val:
                if val.rfind(',') > val.rfind('.'):
                    # German 1.234,56
                    val = val.replace('.', '').replace(',', '.')
                else:
                    # US 1,234.56
                    val = val.replace(',', '')
            elif ',' in val:
                # 12,34 or 1,234 ?
                # If many digits after comma, probably US grouping. 
                # If 2 digits, decimal.
                # Safety for german banking: usually comma is decimal.
                if len(val.split(',')[-1]) == 2:
                     val = val.replace(',', '.')
                else:
                     # ambiguous, assume German for now given context
                     val = val.replace(',', '.')
                     
            return float(val)
        return 0.0
