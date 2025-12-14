import pandas as pd
import hashlib
from datetime import datetime
from typing import List, Optional
from finance_analyzer.core.parser import CSVParser
from finance_analyzer.models.transaction import Transaction
from finance_analyzer.core.db import Database

class DataManager:
    def __init__(self, db: Database = None):
        self.db = db if db else Database()
        self.parser = CSVParser()

    def _generate_hash(self, row: dict) -> str:
        date_str = str(row['date'])
        raw_str = f"{date_str}{row['amount']}{row['description']}".encode('utf-8')
        return hashlib.sha256(raw_str).hexdigest()

    def add_transactions_from_file(self, file_path: str, source_name: str = None) -> int:
        if source_name is None:
            source_name = file_path.split("\\")[-1]

        df = self.parser.parse_csv(file_path, source_name=source_name)
        if df.empty:
            return 0

        count = 0
        conn = self.db.get_connection()
        try:
            for _, row in df.iterrows():
                data = row.to_dict()
                txn_hash = self._generate_hash(data)
                
                date_val = data['date'].strftime('%Y-%m-%d') if isinstance(data['date'], datetime) else str(data['date']).split(' ')[0]
                
                # is_manual = 0 for imports
                cur = conn.execute("""
                    INSERT OR IGNORE INTO transactions (date, amount, description, source, category, txn_hash, is_manual)
                    VALUES (?, ?, ?, ?, ?, ?, 0)
                """, (date_val, data['amount'], data['description'], data['source'], data['category'], txn_hash))
                
                if cur.rowcount > 0:
                    count += 1
            
            conn.commit()
        except Exception as e:
            print(f"Error inserting transactions: {e}")
            conn.rollback()
            
        return count

    def add_manual_entry(self, txn: Transaction):
        conn = self.db.get_connection()
        try:
            data = {
                'date': txn.date,
                'amount': txn.amount,
                'description': txn.description
            }
            txn_hash = self._generate_hash(data)
            date_val = txn.date.strftime('%Y-%m-%d')
            
            # is_manual = 1 for manual entry (though these are usually raw input, user defines cat here)
            # If cat is provided, it's manual. If empty, it's manual entry but uncategorized.
            # Generally manual entry implies user intent, so is_manual=1 sounds right.
            
            conn.execute("""
                INSERT OR IGNORE INTO transactions (date, amount, description, source, category, txn_hash, is_manual)
                VALUES (?, ?, ?, ?, ?, ?, 1)
            """, (date_val, txn.amount, txn.description, txn.source or 'Manual', txn.category, txn_hash))
            conn.commit()
        except Exception as e:
            print(f"Error adding manual entry: {e}")

    def get_data(self) -> pd.DataFrame:
        try:
            df = pd.read_sql_query("SELECT * FROM transactions ORDER BY date DESC", self.db.get_connection())
            if not df.empty:
                df['date'] = pd.to_datetime(df['date'])
            return df
        except Exception as e:
            print(f"Error fetch data: {e}")
            return pd.DataFrame()

    def update_category(self, txn_id: int, category: str):
        conn = self.db.get_connection()
        try:
            # is_manual = 1 for user edits
            cur = conn.execute("UPDATE transactions SET category = ?, is_manual = 1 WHERE id = ?", (category, int(txn_id)))
            conn.commit()
            if cur.rowcount == 0:
                print(f"Update failed: No transaction found with ID {txn_id}")
        except Exception as e:
            print(f"Error updating category: {e}")
            
    def get_all_categories(self) -> List[str]:
        """Returns a list of unique categories from rules and transactions."""
        conn = self.db.get_connection()
        cats = set()
        
        rows = conn.execute("SELECT DISTINCT category FROM rules").fetchall()
        for r in rows:
            if r['category']: cats.add(r['category'])
            
        rows = conn.execute("SELECT DISTINCT category FROM transactions").fetchall()
        for r in rows:
            if r['category']: cats.add(r['category'])
            
        return sorted(list(cats))

    def clear_data(self):
        conn = self.db.get_connection()
        conn.execute("DELETE FROM transactions")
        conn.commit()
