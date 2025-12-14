import pandas as pd
import pytest
import os
from datetime import datetime
from finance_analyzer.core.data_manager import DataManager
from finance_analyzer.core.rules import RuleEngine
from finance_analyzer.core.exporter import export_to_excel
from finance_analyzer.core.db import Database
from finance_analyzer.models.transaction import Transaction

TEST_DB = "test_clash.db"
TEST_EXCEL = "test_export_v2.xlsx"

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

def test_clash_detection(test_db):
    dm = DataManager(db=test_db)
    re = RuleEngine(db=test_db)
    
    # Conflicting Rules
    re.add_rule("Pizza", "Food")
    re.add_rule("Pizza", "Party")
    
    # Txn
    dm.add_manual_entry(Transaction(date=datetime(2025,1,1), amount=-10, description="Pizza Hut"))
    
    # Apply
    re.apply_rules_to_db()
    
    # Verify
    df = dm.get_data()
    # Should have no category (or first one depending on logic, but clash detected)
    # Logic was: if unique_cats > 1 -> category=None, clash_info set.
    row = df.iloc[0]
    assert row['category'] is None
    assert "Clash" in row['clash_info']
    assert "Food" in row['clash_info']
    assert "Party" in row['clash_info']

def test_excel_export_v2(test_db, cleanup_excel):
    dm = DataManager(db=test_db)
    dm.add_manual_entry(Transaction(date=datetime(2025,1,1), amount=-50, description="A", category="Food"))
    dm.add_manual_entry(Transaction(date=datetime(2025,1,2), amount=-20, description="B", category="Travel"))
    
    df = dm.get_data()
    success, msg = export_to_excel(df, TEST_EXCEL)
    assert success

def test_get_distinct_categories(test_db):
    dm = DataManager(db=test_db)
    re = RuleEngine(db=test_db)
    re.add_rule("A", "Cat1")
    dm.add_manual_entry(Transaction(date=datetime(2025,1,1), amount=0, description="..", category="Cat2"))
    
    cats = dm.get_all_categories()
    assert "Cat1" in cats
    assert "Cat2" in cats
