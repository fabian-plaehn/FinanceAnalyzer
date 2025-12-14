import pandas as pd
import pytest
import os
from datetime import datetime
from finance_analyzer.core.data_manager import DataManager
from finance_analyzer.core.exporter import export_to_excel
from finance_analyzer.core.db import Database
from finance_analyzer.models.transaction import Transaction

TEST_DB = "test_ux.db"
TEST_EXCEL = "test_export.xlsx"

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

def test_update_category(test_db):
    dm = DataManager(db=test_db)
    txn = Transaction(date=datetime(2025, 1, 1), amount=100.0, description="Test Item")
    dm.add_manual_entry(txn)
    
    # Get ID
    df = dm.get_data()
    txn_id = df.iloc[0]['id']
    
    # Update
    dm.update_category(txn_id, "New Category")
    
    # Verify
    df_new = dm.get_data()
    assert df_new.iloc[0]['category'] == "New Category"

def test_excel_export_logic(test_db, cleanup_excel):
    dm = DataManager(db=test_db)
    # Add categorized
    dm.add_manual_entry(Transaction(date=datetime(2025,1,1), amount=-50, description="Groceries", category="Food"))
    # Add uncategorized
    dm.add_manual_entry(Transaction(date=datetime(2025,1,2), amount=-20, description="Unknown"))
    
    df = dm.get_data()
    success, msg = export_to_excel(df, TEST_EXCEL)
    
    assert success
    assert os.path.exists(TEST_EXCEL)
    
    # Read back to verify contents
    # Sheet Summary
    df_sum = pd.read_excel(TEST_EXCEL, sheet_name='Summary')
    assert len(df_sum) == 1
    assert df_sum.iloc[0]['Category'] == 'Food'
    
    # Sheet Details
    df_det = pd.read_excel(TEST_EXCEL, sheet_name='Details')
    assert len(df_det) == 1
    assert df_det.iloc[0]['description'] == 'Groceries'
