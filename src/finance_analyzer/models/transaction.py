from dataclasses import dataclass
from datetime import datetime
from typing import Optional

@dataclass
class Transaction:
    date: datetime
    amount: float
    description: str
    category: Optional[str] = None
    source: Optional[str] = None
    id: Optional[str] = None # Unique ID if available
