"""Database service for FinanceAnalyzer.

Handles database session management and provides a central point
for database operations.
"""

import os
from pathlib import Path
from contextlib import contextmanager
from typing import Generator

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, Session

from .models import Base


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
        
        # Create all tables
        self._create_tables()
    
    def _create_tables(self) -> None:
        """Create all database tables if they don't exist."""
        Base.metadata.create_all(self.engine)
    
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
