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
    
    def clone_profile(self, source_profile_id: int, new_name: str) -> Optional[Profile]:
        """Clone a profile, copying categories, rules, and CSV configs.
        
        Args:
            source_profile_id: The source profile ID to clone from.
            new_name: Name for the new cloned profile.
        
        Returns:
            The new Profile object, or None if source not found.
        """
        from ..database.models import Category, Rule, CSVConfiguration
        
        session = self._get_session()
        source = session.get(Profile, source_profile_id)
        if not source:
            return None
        
        # Create new profile
        new_profile = Profile(name=new_name)
        session.add(new_profile)
        session.flush()  # Get the new ID
        
        # Clone categories and build ID mapping
        category_map = {}  # old_id -> new_id
        for old_cat in session.query(Category).filter(Category.profile_id == source_profile_id).all():
            new_cat = Category(
                profile_id=new_profile.id,
                name=old_cat.name
            )
            session.add(new_cat)
            session.flush()
            category_map[old_cat.id] = new_cat.id
        
        # Clone rules with updated category references
        for old_rule in session.query(Rule).filter(Rule.profile_id == source_profile_id).all():
            new_rule = Rule(
                profile_id=new_profile.id,
                pattern=old_rule.pattern,
                is_regex=old_rule.is_regex,
                target_category_id=category_map.get(old_rule.target_category_id),
                priority=old_rule.priority,
                match_field=getattr(old_rule, 'match_field', 'description')
            )
            session.add(new_rule)
        
        # Clone CSV configs
        for old_config in session.query(CSVConfiguration).filter(
            CSVConfiguration.profile_id == source_profile_id
        ).all():
            new_config = CSVConfiguration(
                profile_id=new_profile.id,
                name=old_config.name,
                date_column=old_config.date_column,
                amount_column=old_config.amount_column,
                description_column=old_config.description_column,
                date_format=old_config.date_format,
                delimiter=old_config.delimiter,
                skip_rows=old_config.skip_rows,
                encoding=old_config.encoding,
                sender_receiver_column=getattr(old_config, 'sender_receiver_column', None)
            )
            session.add(new_config)
        
        session.commit()
        session.refresh(new_profile)
        return new_profile
    
    def close(self) -> None:
        """Close the session if we own it."""
        if self._owns_session and self._session is not None:
            self._session.close()
            self._session = None
