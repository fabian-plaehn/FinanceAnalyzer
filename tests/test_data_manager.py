import pandas as pd
import pytest
from datetime import datetime
from finance_analyzer.core.data_manager import DataManager
from finance_analyzer.models.transaction import Transaction

def test_dm_add_manual():
    dm = DataManager()
    txn = Transaction(date=datetime(2023, 5, 20), amount=-15.50, description="Pizza", category="Food")
    dm.add_manual_entry(txn)
    
    assert len(dm.df) == 1
    assert dm.df.iloc[0]['description'] == "Pizza"
    assert dm.df.iloc[0]['source'] == "Manual"

def test_dm_deduplication():
    dm = DataManager()
    txn = Transaction(date=datetime(2023, 5, 20), amount=-15.50, description="Pizza")
    dm.add_manual_entry(txn)
    dm.add_manual_entry(txn) # Add same again
    
    dm._deduplicate()
    assert len(dm.df) == 1

def test_dm_load_file():
    csv_data = "Date,Description,Amount\n2023-01-01,Shop,-10"
    import os
    with open("test_dm.csv", "w") as f:
        f.write(csv_data)
        
    dm = DataManager()
    dm.add_transactions_from_file("test_dm.csv")
    
    assert len(dm.df) == 1
    assert dm.df.iloc[0]['amount'] == -10
    
    os.remove("test_dm.csv")
