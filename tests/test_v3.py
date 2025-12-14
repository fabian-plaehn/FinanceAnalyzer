import pandas as pd
import pytest
import os
from datetime import datetime
from finance_analyzer.core.data_manager import DataManager
from finance_analyzer.core.rules import RuleEngine
from finance_analyzer.core.exporter import export_to_excel
from finance_analyzer.core.db import Database
from finance_analyzer.models.transaction import Transaction

TEST_DB = "test_reapply.db"
TEST_EXCEL = "test_export_v3.xlsx"

@pytest.fixture
def test_db():
    if os.path.exists(TEST_DB):
        os.remove(TEST_DB)
    db = Database(TEST_DB)
    yield db
    db.close()
    if os.path.exists(TEST_DB):
        os.remove(TEST_DB)
        
@pytest.fixture
def cleanup_excel():
    yield
    if os.path.exists(TEST_EXCEL):
        os.remove(TEST_EXCEL)

def test_reapply_logic(test_db):
    dm = DataManager(db=test_db)
    re = RuleEngine(db=test_db)
    
    # 1. Add Rule
    re.add_rule("Netflix", "Streaming")
    
    # 2. Add Auto Txn
    # 2. Add Auto Txn
    # Simulate import (is_manual=0)
    conn = test_db.get_connection()
    conn.execute("INSERT INTO transactions (date, amount, description, source, category, is_manual) VALUES (?, ?, ?, ?, ?, ?)", 
                 ('2025-01-01', -15.0, 'Netflix Subscription', 'Bank', None, 0))
    conn.commit()
    
    # Apply Rules
    re.apply_rules_to_db()
    
    # Check Auto
    df = dm.get_data()
    row_auto = df[df['description'] == 'Netflix Subscription'].iloc[0]
    assert row_auto['category'] == "Streaming"
    
    # 3. Add Manual Txn
    dm.add_manual_entry(Transaction(date=datetime(2025,1,2), amount=-50, description="Gym", category="Health"))
    # (add_manual_entry sets is_manual=1)
    
    # 4. Delete Rule -> Should reset Auto but keep Manual
    rule_id = re.rules[0].id
    re.delete_rule(rule_id)
    
    df = dm.get_data()
    row_auto = df[df['description'] == 'Netflix Subscription'].iloc[0]
    row_manual = df[df['description'] == 'Gym'].iloc[0]
    
    assert row_auto['category'] is None # Ghost gone!
    assert row_manual['category'] == "Health" # Manual stayed!

def test_export_v3(test_db, cleanup_excel):
    dm = DataManager(db=test_db)
    dm.add_manual_entry(Transaction(date=datetime(2025,1,1), amount=-50, description="A", category="Food"))
    df = dm.get_data()
    success, msg = export_to_excel(df, TEST_EXCEL)
    assert success
