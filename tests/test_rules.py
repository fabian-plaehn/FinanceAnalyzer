import pandas as pd
from finance_analyzer.core.rules import RuleEngine

def test_rule_keyword():
    df = pd.DataFrame({
        'description': ['Supermarket A', 'Gas Station', 'Supermarket B', 'Rent'],
        'amount': [-50, -60, -20, -1000]
    })
    
    re = RuleEngine()
    re.add_rule('Supermarket', 'Groceries')
    
    df = re.apply_rules(df)
    
    assert df.loc[0, 'category'] == 'Groceries'
    assert df.loc[2, 'category'] == 'Groceries'
    assert df.loc[1, 'category'] is None

def test_rule_regex():
    df = pd.DataFrame({
        'description': ['PAYPAL *Netflix', 'PAYPAL *Spotify'], 
        'category': [None, None]
    })
    
    re = RuleEngine()
    re.add_rule('PAYPAL .*', 'Entertainment', is_regex=True)
    
    df = re.apply_rules(df)
    
    assert df.loc[0, 'category'] == 'Entertainment'
    assert df.loc[1, 'category'] == 'Entertainment'

def test_rule_overwrite():
    df = pd.DataFrame({'description': ['Amazon Marketplace']})
    
    re = RuleEngine()
    re.add_rule('Amazon', 'Shopping')
    re.add_rule('Marketplace', 'Online Services')
    
    df = re.apply_rules(df)
    
    # 'Amazon Marketplace' matches both. 'Marketplace' was added last.
    assert df.loc[0, 'category'] == 'Online Services'
