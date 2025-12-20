"""Profile management service for FinanceAnalyzer."""

from typing import List, Optional

from sqlalchemy.orm import Session

from ..database.models import Profile
from ..database.service import get_database_service


class ProfileService:
    """Service for managing business profiles."""
    
    def __init__(self, session: Session | None = None):
        """Initialize the profile service.
        
        Args:
            session: Optional SQLAlchemy session. If not provided, creates a new one.
        """
        self._session = session
        self._owns_session = session is None
    
    def _get_session(self) -> Session:
        """Get or create a session."""
        if self._session is None:
            self._session = get_database_service().create_session()
        return self._session
    
    def create_profile(self, name: str) -> Profile:
        """Create a new business profile.
        
        Args:
            name: Name of the profile.
        
        Returns:
            The created Profile object.
        """
        session = self._get_session()
        profile = Profile(name=name)
        session.add(profile)
        session.commit()
        session.refresh(profile)
        return profile
    
    def get_profile(self, profile_id: int) -> Optional[Profile]:
        """Get a profile by ID.
        
        Args:
            profile_id: The profile ID.
        
        Returns:
            The Profile object, or None if not found.
        """
        session = self._get_session()
        return session.get(Profile, profile_id)
    
    def get_profile_by_name(self, name: str) -> Optional[Profile]:
        """Get a profile by name.
        
        Args:
            name: The profile name.
        
        Returns:
            The Profile object, or None if not found.
        """
        session = self._get_session()
        return session.query(Profile).filter(Profile.name == name).first()
    
    def get_all_profiles(self) -> List[Profile]:
        """Get all profiles.
        
        Returns:
            List of all Profile objects.
        """
        session = self._get_session()
        return session.query(Profile).order_by(Profile.name).all()
    
    def update_profile(self, profile_id: int, name: str) -> Optional[Profile]:
        """Update a profile's name.
        
        Args:
            profile_id: The profile ID.
            name: The new name.
        
        Returns:
            The updated Profile object, or None if not found.
        """
        session = self._get_session()
        profile = session.get(Profile, profile_id)
        if profile:
            profile.name = name
            session.commit()
            session.refresh(profile)
        return profile
    
    def delete_profile(self, profile_id: int) -> bool:
        """Delete a profile and all its associated data.
        
        Args:
            profile_id: The profile ID.
        
        Returns:
            True if deleted, False if not found.
        """
        session = self._get_session()
        profile = session.get(Profile, profile_id)
        if profile:
            session.delete(profile)
            session.commit()
            return True
        return False
    
    def close(self) -> None:
        """Close the session if we own it."""
        if self._owns_session and self._session is not None:
            self._session.close()
            self._session = None
