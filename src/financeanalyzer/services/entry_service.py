"""Entry management service for FinanceAnalyzer."""

from datetime import date
from decimal import Decimal
from typing import List, Optional, Tuple
import hashlib

from sqlalchemy.orm import Session
from sqlalchemy import and_, or_

from ..database.models import Entry
from ..database.service import get_database_service


class EntryService:
    """Service for managing transaction entries within a profile."""
    
    def __init__(self, profile_id: int, session: Session | None = None):
        """Initialize the entry service.
        
        Args:
            profile_id: The profile ID to operate on.
            session: Optional SQLAlchemy session.
        """
        self.profile_id = profile_id
        self._session = session
        self._owns_session = session is None
    
    def _get_session(self) -> Session:
        """Get or create a session."""
        if self._session is None:
            self._session = get_database_service().create_session()
        return self._session
    
    @staticmethod
    def generate_import_hash(
        entry_date: date,
        amount: Decimal,
        description: str,
        source: str
    ) -> str:
        """Generate a unique hash for duplicate detection.
        
        Args:
            entry_date: The transaction date.
            amount: The transaction amount.
            description: The transaction description.
            source: The transaction source.
        
        Returns:
            A SHA-256 hash string.
        """
        content = f"{entry_date.isoformat()}|{amount}|{description}|{source}"
        return hashlib.sha256(content.encode()).hexdigest()

    def create_entry(
        self,
        entry_date: date,
        amount: Decimal,
        description: str,
        source: str,
        sender_receiver: str | None = None,
        category_id: int | None = None,
        is_manual_category: bool = False,
        has_conflict: bool = False,
        import_hash: str | None = None
    ) -> Entry:
        """Create a new transaction entry.
        
        Args:
            entry_date: The transaction date.
            amount: The transaction amount.
            description: The transaction description.
            source: The transaction source (e.g., "VR Bank", "Cash").
            sender_receiver: Optional sender/receiver name.
            category_id: Optional category ID.
            is_manual_category: Whether category was manually assigned.
            has_conflict: Whether multiple rules matched.
            import_hash: Optional import hash for duplicate detection.
        
        Returns:
            The created Entry object.
        """
        session = self._get_session()
        
        if import_hash is None:
            import_hash = self.generate_import_hash(entry_date, amount, description, source)
        
        entry = Entry(
            profile_id=self.profile_id,
            entry_date=entry_date,
            amount=amount,
            description=description,
            sender_receiver=sender_receiver,
            source=source,
            category_id=category_id,
            is_manual_category=is_manual_category,
            has_conflict=has_conflict,
            import_hash=import_hash
        )
        session.add(entry)
        session.commit()
        session.refresh(entry)
        return entry
    
    def entry_exists(self, import_hash: str) -> bool:
        """Check if an entry with the given import hash exists.
        
        Args:
            import_hash: The import hash to check.
        
        Returns:
            True if entry exists, False otherwise.
        """
        session = self._get_session()
        return session.query(Entry).filter(
            Entry.profile_id == self.profile_id,
            Entry.import_hash == import_hash
        ).first() is not None
    
    def get_entry(self, entry_id: int) -> Optional[Entry]:
        """Get an entry by ID.
        
        Args:
            entry_id: The entry ID.
        
        Returns:
            The Entry object, or None if not found.
        """
        session = self._get_session()
        entry = session.get(Entry, entry_id)
        if entry and entry.profile_id == self.profile_id:
            return entry
        return None
    
    def get_all_entries(
        self,
        start_date: date | None = None,
        end_date: date | None = None,
        category_id: int | None = None,
        source: str | None = None,
        uncategorized_only: bool = False,
        conflicts_only: bool = False
    ) -> List[Entry]:
        """Get entries with optional filters.
        
        Args:
            start_date: Filter entries on or after this date.
            end_date: Filter entries on or before this date.
            category_id: Filter by category ID.
            source: Filter by source.
            uncategorized_only: Only return uncategorized entries.
            conflicts_only: Only return entries with conflicts.
        
        Returns:
            List of Entry objects matching the filters.
        """
        session = self._get_session()
        query = session.query(Entry).filter(Entry.profile_id == self.profile_id)
        
        if start_date:
            query = query.filter(Entry.entry_date >= start_date)
        if end_date:
            query = query.filter(Entry.entry_date <= end_date)
        if category_id:
            query = query.filter(Entry.category_id == category_id)
        if source:
            query = query.filter(Entry.source == source)
        if uncategorized_only:
            query = query.filter(Entry.category_id == None, Entry.has_conflict == False)
        if conflicts_only:
            query = query.filter(Entry.has_conflict == True)
        
        return query.order_by(Entry.entry_date.desc()).all()
    
    def get_entry_count(self) -> int:
        """Get the total number of entries.
        
        Returns:
            Total number of entries.
        """
        session = self._get_session()
        return session.query(Entry).filter(Entry.profile_id == self.profile_id).count()
    
    def get_uncategorized_count(self) -> int:
        """Get the number of uncategorized entries.
        
        Returns:
            Number of uncategorized entries.
        """
        session = self._get_session()
        return session.query(Entry).filter(
            Entry.profile_id == self.profile_id,
            Entry.category_id == None,
            Entry.has_conflict == False
        ).count()
    
    def get_conflict_count(self) -> int:
        """Get the number of entries with conflicts.
        
        Returns:
            Number of entries with conflicts.
        """
        session = self._get_session()
        return session.query(Entry).filter(
            Entry.profile_id == self.profile_id,
            Entry.has_conflict == True
        ).count()
    
    def get_sources(self) -> List[str]:
        """Get all unique sources.
        
        Returns:
            List of unique source strings.
        """
        session = self._get_session()
        result = session.query(Entry.source).filter(
            Entry.profile_id == self.profile_id
        ).distinct().all()
        return [r[0] for r in result]
    
    def update_entry(
        self,
        entry_id: int,
        entry_date: date | None = None,
        amount: Decimal | None = None,
        description: str | None = None,
        source: str | None = None,
        category_id: int | None = None,
        is_manual_category: bool | None = None,
        has_conflict: bool | None = None,
        clear_category: bool = False
    ) -> Optional[Entry]:
        """Update an entry.
        
        Args:
            entry_id: The entry ID.
            entry_date: New date (optional).
            amount: New amount (optional).
            description: New description (optional).
            source: New source (optional).
            category_id: New category ID (optional).
            is_manual_category: New manual category flag (optional).
            has_conflict: New conflict flag (optional).
            clear_category: If True, explicitly set category_id to None.
        
        Returns:
            The updated Entry object, or None if not found.
        """
        session = self._get_session()
        entry = self.get_entry(entry_id)
        if entry:
            if entry_date is not None:
                entry.entry_date = entry_date
            if amount is not None:
                entry.amount = amount
            if description is not None:
                entry.description = description
            if source is not None:
                entry.source = source
            if category_id is not None:
                entry.category_id = category_id
            if clear_category:
                entry.category_id = None
            if is_manual_category is not None:
                entry.is_manual_category = is_manual_category
            if has_conflict is not None:
                entry.has_conflict = has_conflict
            session.commit()
            session.refresh(entry)
        return entry
    
    def set_category(
        self,
        entry_id: int,
        category_id: int | None,
        is_manual: bool = True
    ) -> Optional[Entry]:
        """Set an entry's category.
        
        Args:
            entry_id: The entry ID.
            category_id: The new category ID (or None to un-categorize).
            is_manual: Whether this is a manual assignment.
        
        Returns:
            The updated Entry object, or None if not found.
        """
        return self.update_entry(
            entry_id,
            category_id=category_id,
            is_manual_category=is_manual,
            has_conflict=False,
            clear_category=category_id is None
        )
    
    def delete_entry(self, entry_id: int) -> bool:
        """Delete an entry.
        
        Args:
            entry_id: The entry ID.
        
        Returns:
            True if deleted, False if not found.
        """
        session = self._get_session()
        entry = self.get_entry(entry_id)
        if entry:
            session.delete(entry)
            session.commit()
            return True
        return False
    
    def get_entries_by_category(self) -> dict[int | None, List[Entry]]:
        """Get all entries grouped by category.
        
        Returns:
            Dict mapping category_id (or None) to list of entries.
        """
        entries = self.get_all_entries()
        result: dict[int | None, List[Entry]] = {}
        for entry in entries:
            cat_id = entry.category_id
            if cat_id not in result:
                result[cat_id] = []
            result[cat_id].append(entry)
        return result
    
    def get_category_totals(
        self,
        start_date: date | None = None,
        end_date: date | None = None
    ) -> dict[int | None, Decimal]:
        """Get total amounts per category.
        
        Args:
            start_date: Filter entries on or after this date.
            end_date: Filter entries on or before this date.
        
        Returns:
            Dict mapping category_id (or None) to total amount.
        """
        entries = self.get_all_entries(start_date=start_date, end_date=end_date)
        result: dict[int | None, Decimal] = {}
        for entry in entries:
            cat_id = entry.category_id
            if cat_id not in result:
                result[cat_id] = Decimal("0")
            result[cat_id] += entry.amount
        return result
    
    def close(self) -> None:
        """Close the session if we own it."""
        if self._owns_session and self._session is not None:
            self._session.close()
            self._session = None
