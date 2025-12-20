"""Database service for FinanceAnalyzer.

Handles database session management and provides a central point
for database operations.
"""

import os
from pathlib import Path
from contextlib import contextmanager
from typing import Generator

from sqlalchemy import create_engine, text, inspect
from sqlalchemy.orm import sessionmaker, Session

from .models import Base


# Current schema version - increment when adding migrations
SCHEMA_VERSION = 2


class DatabaseService:
    """Service for managing database connections and sessions."""
    
    def __init__(self, db_path: str | None = None):
        """Initialize the database service.
        
        Args:
            db_path: Path to the SQLite database file. If None, uses default location.
        """
        if db_path is None:
            # Default: store in user's app data directory
            app_data_dir = Path.home() / ".financeanalyzer"
            app_data_dir.mkdir(parents=True, exist_ok=True)
            db_path = str(app_data_dir / "financeanalyzer.db")
        
        self.db_path = db_path
        self.engine = create_engine(f"sqlite:///{db_path}", echo=False)
        self._session_factory = sessionmaker(bind=self.engine)
        
        # Create all tables and run migrations
        self._create_tables()
        self._run_migrations()
    
    def _create_tables(self) -> None:
        """Create all database tables if they don't exist."""
        Base.metadata.create_all(self.engine)
        
        # Create schema_info table if it doesn't exist
        with self.engine.connect() as conn:
            conn.execute(text("""
                CREATE TABLE IF NOT EXISTS schema_info (
                    id INTEGER PRIMARY KEY,
                    version INTEGER NOT NULL,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """))
            conn.commit()
    
    def _get_schema_version(self) -> int:
        """Get the current schema version from the database."""
        with self.engine.connect() as conn:
            result = conn.execute(text("SELECT version FROM schema_info ORDER BY id DESC LIMIT 1"))
            row = result.fetchone()
            return row[0] if row else 0
    
    def _set_schema_version(self, version: int) -> None:
        """Set the schema version in the database."""
        with self.engine.connect() as conn:
            conn.execute(text("INSERT INTO schema_info (version) VALUES (:version)"), {"version": version})
            conn.commit()
    
    def _column_exists(self, table: str, column: str) -> bool:
        """Check if a column exists in a table."""
        inspector = inspect(self.engine)
        columns = [c['name'] for c in inspector.get_columns(table)]
        return column in columns
    
    def _run_migrations(self) -> None:
        """Run any pending database migrations."""
        current_version = self._get_schema_version()
        
        if current_version >= SCHEMA_VERSION:
            return  # Already up to date
        
        with self.engine.connect() as conn:
            # Migration 1 -> 2: Add sender/receiver and match_field columns
            if current_version < 2:
                # Add sender_receiver column to entries table
                if not self._column_exists('entries', 'sender_receiver'):
                    conn.execute(text("ALTER TABLE entries ADD COLUMN sender_receiver TEXT"))
                
                # Add match_field column to rules table
                if not self._column_exists('rules', 'match_field'):
                    conn.execute(text("ALTER TABLE rules ADD COLUMN match_field VARCHAR(50) DEFAULT 'description'"))
                
                # Add sender_receiver_column to csv_configurations table
                if not self._column_exists('csv_configurations', 'sender_receiver_column'):
                    conn.execute(text("ALTER TABLE csv_configurations ADD COLUMN sender_receiver_column VARCHAR(255)"))
                
                conn.commit()
        
        # Update schema version
        self._set_schema_version(SCHEMA_VERSION)
    
    @contextmanager
    def get_session(self) -> Generator[Session, None, None]:
        """Get a database session as a context manager.
        
        Usage:
            with db_service.get_session() as session:
                # do stuff with session
                session.add(...)
                session.commit()
        
        Yields:
            A SQLAlchemy Session object.
        """
        session = self._session_factory()
        try:
            yield session
        except Exception:
            session.rollback()
            raise
        finally:
            session.close()
    
    def create_session(self) -> Session:
        """Create a new database session.
        
        Note: The caller is responsible for closing the session.
        Prefer using get_session() context manager when possible.
        
        Returns:
            A new SQLAlchemy Session object.
        """
        return self._session_factory()


# Global database service instance
_db_service: DatabaseService | None = None


def get_database_service(db_path: str | None = None) -> DatabaseService:
    """Get or create the global database service instance.
    
    Args:
        db_path: Path to the SQLite database file. Only used on first call.
    
    Returns:
        The global DatabaseService instance.
    """
    global _db_service
    if _db_service is None:
        _db_service = DatabaseService(db_path)
    return _db_service


def reset_database_service() -> None:
    """Reset the global database service instance.
    
    Useful for testing or when switching databases.
    """
    global _db_service
    _db_service = None

