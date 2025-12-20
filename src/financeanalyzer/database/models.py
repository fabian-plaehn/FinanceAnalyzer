"""SQLAlchemy models for FinanceAnalyzer."""

from datetime import datetime, date
from decimal import Decimal
from typing import Optional, List

from sqlalchemy import (
    String,
    Integer,
    Boolean,
    Date,
    DateTime,
    Numeric,
    Text,
    ForeignKey,
    create_engine,
)
from sqlalchemy.orm import (
    DeclarativeBase,
    Mapped,
    mapped_column,
    relationship,
)


class Base(DeclarativeBase):
    """Base class for all models."""
    pass


class Profile(Base):
    """Business profile model.
    
    Each profile has its own entries, categories, and rules.
    """
    __tablename__ = "profiles"
    
    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    name: Mapped[str] = mapped_column(String(255), nullable=False, unique=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.now)
    
    # Relationships
    categories: Mapped[List["Category"]] = relationship(
        "Category", back_populates="profile", cascade="all, delete-orphan"
    )
    rules: Mapped[List["Rule"]] = relationship(
        "Rule", back_populates="profile", cascade="all, delete-orphan"
    )
    entries: Mapped[List["Entry"]] = relationship(
        "Entry", back_populates="profile", cascade="all, delete-orphan"
    )
    csv_configurations: Mapped[List["CSVConfiguration"]] = relationship(
        "CSVConfiguration", back_populates="profile", cascade="all, delete-orphan"
    )
    
    def __repr__(self) -> str:
        return f"<Profile(id={self.id}, name='{self.name}')>"


class Category(Base):
    """Category model for transaction categorization.
    
    Flat list of categories (no hierarchy).
    """
    __tablename__ = "categories"
    
    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    profile_id: Mapped[int] = mapped_column(ForeignKey("profiles.id"), nullable=False)
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    
    # Relationships
    profile: Mapped["Profile"] = relationship("Profile", back_populates="categories")
    rules: Mapped[List["Rule"]] = relationship(
        "Rule", back_populates="target_category", cascade="all, delete-orphan"
    )
    entries: Mapped[List["Entry"]] = relationship(
        "Entry", back_populates="category"
    )
    
    def __repr__(self) -> str:
        return f"<Category(id={self.id}, name='{self.name}')>"


class Rule(Base):
    """Categorization rule model.
    
    Maps entries to categories using pattern matching.
    Rule types: "contains" or "regex"
    """
    __tablename__ = "rules"
    
    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    profile_id: Mapped[int] = mapped_column(ForeignKey("profiles.id"), nullable=False)
    target_category_id: Mapped[int] = mapped_column(
        ForeignKey("categories.id"), nullable=False
    )
    rule_type: Mapped[str] = mapped_column(String(50), nullable=False)  # "contains" | "regex"
    pattern: Mapped[str] = mapped_column(Text, nullable=False)
    match_field: Mapped[str] = mapped_column(String(50), default="description")  # "description" | "sender_receiver" | "any"
    enabled: Mapped[bool] = mapped_column(Boolean, default=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.now)
    
    # Relationships
    profile: Mapped["Profile"] = relationship("Profile", back_populates="rules")
    target_category: Mapped["Category"] = relationship("Category", back_populates="rules")
    
    def __repr__(self) -> str:
        return f"<Rule(id={self.id}, type='{self.rule_type}', pattern='{self.pattern}')>"


class Entry(Base):
    """Transaction entry model.
    
    Represents a single financial transaction (bank or cash).
    """
    __tablename__ = "entries"
    
    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    profile_id: Mapped[int] = mapped_column(ForeignKey("profiles.id"), nullable=False)
    category_id: Mapped[Optional[int]] = mapped_column(
        ForeignKey("categories.id"), nullable=True
    )
    
    # Transaction data
    entry_date: Mapped[date] = mapped_column(Date, nullable=False)
    amount: Mapped[Decimal] = mapped_column(Numeric(12, 2), nullable=False)
    sender_receiver: Mapped[Optional[str]] = mapped_column(Text, nullable=True)  # Name Zahlungsbeteiligter
    description: Mapped[str] = mapped_column(Text, nullable=False)
    source: Mapped[str] = mapped_column(String(255), nullable=False)  # e.g., "VR Bank", "Cash"
    
    # Categorization metadata
    is_manual_category: Mapped[bool] = mapped_column(Boolean, default=False)
    has_conflict: Mapped[bool] = mapped_column(Boolean, default=False)  # Multiple rules matched
    
    # Import tracking
    import_hash: Mapped[str] = mapped_column(String(64), nullable=True, unique=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.now)
    
    # Relationships
    profile: Mapped["Profile"] = relationship("Profile", back_populates="entries")
    category: Mapped[Optional["Category"]] = relationship("Category", back_populates="entries")
    
    def __repr__(self) -> str:
        return f"<Entry(id={self.id}, date={self.entry_date}, amount={self.amount})>"


class CSVConfiguration(Base):
    """CSV import configuration model.
    
    Stores column mappings and parsing settings for different bank CSV formats.
    Allows users to save and reuse configurations.
    """
    __tablename__ = "csv_configurations"
    
    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    profile_id: Mapped[int] = mapped_column(ForeignKey("profiles.id"), nullable=False)
    
    # Configuration metadata
    name: Mapped[str] = mapped_column(String(255), nullable=False)  # e.g., "VR Bank"
    
    # CSV parsing settings
    delimiter: Mapped[str] = mapped_column(String(10), default=";")
    encoding: Mapped[str] = mapped_column(String(50), default="utf-8")
    skip_rows: Mapped[int] = mapped_column(Integer, default=0)
    
    # Column mappings (column names from CSV)
    date_column: Mapped[str] = mapped_column(String(255), nullable=False)
    date_format: Mapped[str] = mapped_column(String(50), default="%d.%m.%Y")
    amount_column: Mapped[str] = mapped_column(String(255), nullable=False)
    description_column: Mapped[str] = mapped_column(String(255), nullable=False)
    sender_receiver_column: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)  # Optional
    
    # Optional: decimal separator for amount parsing
    decimal_separator: Mapped[str] = mapped_column(String(5), default=",")
    thousands_separator: Mapped[str] = mapped_column(String(5), default=".")
    
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.now)
    
    # Relationships
    profile: Mapped["Profile"] = relationship("Profile", back_populates="csv_configurations")
    
    def __repr__(self) -> str:
        return f"<CSVConfiguration(id={self.id}, name='{self.name}')>"
