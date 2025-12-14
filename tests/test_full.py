import pandas as pd
import pytest
import os
import io
from datetime import datetime
from finance_analyzer.core.data_manager import DataManager
from finance_analyzer.core.rules import RuleEngine
from finance_analyzer.core.parser import CSVParser
from finance_analyzer.core.db import Database
from finance_analyzer.models.transaction import Transaction

TEST_DB = "test_finance.db"

@pytest.fixture
def test_db():
    if os.path.exists(TEST_DB):
        os.remove(TEST_DB)
    db = Database(TEST_DB)
    yield db
    db.close()
    if os.path.exists(TEST_DB):
        os.remove(TEST_DB)

def test_dm_deduplication(test_db):
    dm = DataManager(db=test_db)
    txn = Transaction(date=datetime(2023, 5, 20), amount=-15.50, description="Pizza")
    dm.add_manual_entry(txn)
    
    # Add same again
    dm.add_manual_entry(txn) 
    
    df = dm.get_data()
    assert len(df) == 1

def test_rules_persistence(test_db):
    re = RuleEngine(db=test_db)
    re.add_rule("Pizza", "Food")
    
    # Reload engine
    re2 = RuleEngine(db=test_db)
    assert len(re2.rules) == 1
    assert re2.rules[0].category == "Food"
    
    re2.delete_rule(re2.rules[0].id)
    re3 = RuleEngine(db=test_db)
    assert len(re3.rules) == 0

def test_parser_german_complex():
    # User's header + integer formatted amount + generic date
    csv_raw = """Bezeichnung Auftragskonto;IBAN Auftragskonto;BIC Auftragskonto;Bankname Auftragskonto;Buchungstag;Valutadatum;Name Zahlungsbeteiligter;IBAN Zahlungsbeteiligter;BIC (SWIFT-Code) Zahlungsbeteiligter;Buchungstext;Verwendungszweck;Betrag;Waehrung;Saldo nach Buchung;Bemerkung;Gekennzeichneter Umsatz;Glaeubiger ID;Mandatsreferenz
MyAccount;DE123;BIC123;MyBank;14.12.2025;14.12.2025;Netflix;;;DD;Subscription;-15,99;EUR;1000,00;;;;"""
    
    with open("test_german.csv", "w", encoding="utf-8") as f:
        f.write(csv_raw)
        
    parser = CSVParser()
    df = parser.parse_csv("test_german.csv")
    
    assert len(df) == 1
    assert df.iloc[0]['amount'] == -15.99
    assert df.iloc[0]['date'].day == 14
    # Check combined description
    # Columns expected: Buchungstext(DD), Verwendungszweck(Subscription), Name(Netflix)
    # Parser combines variants: description_main (verwendungszweck, buchungstext) + description_extra (name...)
    desc = df.iloc[0]['description']
    assert "Netflix" in desc
    assert "Subscription" in desc
    
    os.remove("test_german.csv")
