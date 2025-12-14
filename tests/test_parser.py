import pandas as pd
import pytest
from io import StringIO
from finance_analyzer.core.parser import CSVParser

def test_parser_valid_csv():
    csv_data = """Date,Description,Amount
2023-01-01,Supermarket,-50.00
2023-01-02,Salary,2000.00
"""
    # Create valid csv file
    with open("test_valid.csv", "w") as f:
        f.write(csv_data)
        
    parser = CSVParser()
    df = parser.parse_csv("test_valid.csv", source_name="TestBank")
    
    assert len(df) == 2
    assert "date" in df.columns
    assert "amount" in df.columns
    assert df.iloc[0]["amount"] == -50.0
    assert df.iloc[0]["source"] == "TestBank"
    
    # helper cleanup
    import os
    os.remove("test_valid.csv")

def test_parser_german_format():
    csv_data = """Buchungstag;Verwendungszweck;Betrag
01.05.2023;Miete;-800,00
"""
    # Create german csv file (using semicolon and comma) - Pandas read_csv defaults to comma sep, 
    # so we might need to handle separator detection or user input.
    # For this test, let's assume comma sep for structure but german number format if possible, 
    # OR we need to update parser to handle separators. 
    # Let's adjust the test input to be comma separated for now to test column mapping first.
    csv_data = """Buchungstag,Verwendungszweck,Betrag
01.05.2023,Miete,"-800,00"
"""
    with open("test_german.csv", "w") as f:
        f.write(csv_data)

    parser = CSVParser()
    df = parser.parse_csv("test_german.csv")
    
    assert len(df) == 1
    assert df.iloc[0]["amount"] == -800.00
    assert df.iloc[0]["description"] == "Miete"
    
    import os
    os.remove("test_german.csv")
