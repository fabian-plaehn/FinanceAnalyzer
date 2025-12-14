from dataclasses import dataclass
from typing import List, Dict, Set
import pandas as pd
import re
from finance_analyzer.core.db import Database

@dataclass
class Rule:
    id: int
    keyword: str
    category: str
    is_regex: bool = False

class RuleEngine:
    def __init__(self, db: Database = None):
        self.db = db if db else Database()
        self.rules: List[Rule] = []
        self.load_rules()

    def load_rules(self):
        """Reloads rules from DB."""
        self.rules = []
        conn = self.db.get_connection()
        rows = conn.execute("SELECT * FROM rules").fetchall()
        for row in rows:
            self.rules.append(Rule(
                id=row['id'],
                keyword=row['keyword'],
                category=row['category'],
                is_regex=bool(row['is_regex'])
            ))

    def add_rule(self, keyword: str, category: str, is_regex: bool = False):
        conn = self.db.get_connection()
        conn.execute("INSERT INTO rules (keyword, category, is_regex) VALUES (?, ?, ?)", 
                     (keyword, category, 1 if is_regex else 0))
        conn.commit()
        self.load_rules()
        self.reapply_all()

    def delete_rule(self, rule_id: int):
        conn = self.db.get_connection()
        conn.execute("DELETE FROM rules WHERE id = ?", (rule_id,))
        conn.commit()
        self.load_rules()
        self.reapply_all()

    def reapply_all(self):
        """
        Resets all auto-categorized transactions and re-applies rules.
        """
        conn = self.db.get_connection()
        # Reset where is_manual is false or null
        conn.execute("UPDATE transactions SET category = NULL, clash_info = NULL WHERE is_manual = 0 OR is_manual IS NULL")
        conn.commit()
        
        # Apply rules again
        self.apply_rules_to_db()

    def apply_rules_to_db(self):
        """
        Applies rules to DB transactions.
        Detects clashes (multiple rules with DIFFERENT categories).
        """
        conn = self.db.get_connection()
        
        # Optimziation: Only fetch where category IS NULL? 
        # But we might want to overwrite if we are re-running?
        # reapply_all() handles the reset. So here we just apply to NULLs effectively.
        # But let's check everything just in case logic changes.
        
        rows = conn.execute("SELECT id, description FROM transactions WHERE category IS NULL").fetchall()
        
        updates = [] 
        count_updated = 0
        count_clashes = 0
        
        if not self.rules:
             return 0

        for row in rows:
            txn_id = row['id']
            desc = row['description']
            
            matches = []   
            
            for rule in self.rules:
                matched = False
                if rule.is_regex:
                    try:
                        if re.search(rule.keyword, desc, re.IGNORECASE):
                            matched = True
                    except:
                        pass
                else:
                    if rule.keyword.lower() in desc.lower():
                        matched = True
                
                if matched:
                    matches.append((rule.category, rule.keyword))
            
            if not matches:
                continue
                
            unique_cats = sorted(list(set(m[0] for m in matches)))
            
            if len(unique_cats) == 1:
                updates.append((unique_cats[0], None, txn_id))
                count_updated += 1
            else:
                clash_desc = " | ".join([f"{m[0]} ('{m[1]}')" for m in matches])
                updates.append((None, f"Clash: {clash_desc}", txn_id))
                count_clashes += 1
        
        if updates:
            # is_manual remains 0 (since rule engine did it)
            conn.executemany("UPDATE transactions SET category = ?, clash_info = ? WHERE id = ?", updates)
            conn.commit()
            
        print(f"Applied rules: {count_updated} categorized, {count_clashes} clashes detected.")
        return count_updated

    def apply_rules(self, df: pd.DataFrame) -> pd.DataFrame:
         return df

    def get_rules_as_dict(self) -> List[Dict]:
        return [{'id': r.id, 'keyword': r.keyword, 'category': r.category, 'is_regex': r.is_regex} for r in self.rules]
