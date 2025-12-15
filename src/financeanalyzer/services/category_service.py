"""Category management service for FinanceAnalyzer."""

from typing import List, Optional

from sqlalchemy.orm import Session

from ..database.models import Category
from ..database.service import get_database_service


class CategoryService:
    """Service for managing categories within a profile."""
    
    def __init__(self, profile_id: int, session: Session | None = None):
        """Initialize the category service.
        
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
    
    def create_category(self, name: str) -> Category:
        """Create a new category.
        
        Args:
            name: Name of the category.
        
        Returns:
            The created Category object.
        """
        session = self._get_session()
        category = Category(profile_id=self.profile_id, name=name)
        session.add(category)
        session.commit()
        session.refresh(category)
        return category
    
    def get_category(self, category_id: int) -> Optional[Category]:
        """Get a category by ID.
        
        Args:
            category_id: The category ID.
        
        Returns:
            The Category object, or None if not found.
        """
        session = self._get_session()
        category = session.get(Category, category_id)
        if category and category.profile_id == self.profile_id:
            return category
        return None
    
    def get_category_by_name(self, name: str) -> Optional[Category]:
        """Get a category by name.
        
        Args:
            name: The category name.
        
        Returns:
            The Category object, or None if not found.
        """
        session = self._get_session()
        return session.query(Category).filter(
            Category.profile_id == self.profile_id,
            Category.name == name
        ).first()
    
    def get_all_categories(self) -> List[Category]:
        """Get all categories for the profile.
        
        Returns:
            List of all Category objects.
        """
        session = self._get_session()
        return session.query(Category).filter(
            Category.profile_id == self.profile_id
        ).order_by(Category.name).all()
    
    def update_category(self, category_id: int, name: str) -> Optional[Category]:
        """Update a category's name.
        
        Args:
            category_id: The category ID.
            name: The new name.
        
        Returns:
            The updated Category object, or None if not found.
        """
        session = self._get_session()
        category = self.get_category(category_id)
        if category:
            category.name = name
            session.commit()
            session.refresh(category)
        return category
    
    def delete_category(self, category_id: int) -> bool:
        """Delete a category.
        
        Note: This will also delete associated rules and un-categorize entries.
        
        Args:
            category_id: The category ID.
        
        Returns:
            True if deleted, False if not found.
        """
        session = self._get_session()
        category = self.get_category(category_id)
        if category:
            session.delete(category)
            session.commit()
            return True
        return False
    
    def close(self) -> None:
        """Close the session if we own it."""
        if self._owns_session and self._session is not None:
            self._session.close()
            self._session = None
