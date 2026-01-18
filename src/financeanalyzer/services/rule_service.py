"""Rule management service for FinanceAnalyzer."""

from typing import List, Optional

from sqlalchemy.orm import Session

from ..database.models import Rule
from ..database.service import get_database_service


class RuleService:
    """Service for managing categorization rules within a profile."""
    
    def __init__(self, profile_id: int, session: Session | None = None):
        """Initialize the rule service.
        
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
    
    def create_rule(
        self,
        target_category_id: int,
        rule_type: str,
        pattern: str,
        match_field: str = "description",
        enabled: bool = True
    ) -> Rule:
        """Create a new categorization rule.
        
        Args:
            target_category_id: The category ID to assign when rule matches.
            rule_type: Type of rule ("contains" or "regex").
            pattern: The pattern to match against.
            match_field: Field to match against ("description", "sender_receiver", or "any").
            enabled: Whether the rule is enabled.
        
        Returns:
            The created Rule object.
        """
        session = self._get_session()
        rule = Rule(
            profile_id=self.profile_id,
            target_category_id=target_category_id,
            rule_type=rule_type,
            pattern=pattern,
            match_field=match_field,
            enabled=enabled
        )
        session.add(rule)
        session.commit()
        session.refresh(rule)
        return rule
    
    def get_rule(self, rule_id: int) -> Optional[Rule]:
        """Get a rule by ID.
        
        Args:
            rule_id: The rule ID.
        
        Returns:
            The Rule object, or None if not found.
        """
        session = self._get_session()
        rule = session.get(Rule, rule_id)
        if rule and rule.profile_id == self.profile_id:
            return rule
        return None
    
    def get_all_rules(self, enabled_only: bool = False) -> List[Rule]:
        """Get all rules for the profile.
        
        Args:
            enabled_only: If True, only return enabled rules.
        
        Returns:
            List of all Rule objects.
        """
        session = self._get_session()
        query = session.query(Rule).filter(Rule.profile_id == self.profile_id)
        if enabled_only:
            query = query.filter(Rule.enabled == True)
        return query.order_by(Rule.created_at).all()
    
    def get_rules_for_category(self, category_id: int) -> List[Rule]:
        """Get all rules for a specific category.
        
        Args:
            category_id: The category ID.
        
        Returns:
            List of Rule objects for that category.
        """
        session = self._get_session()
        return session.query(Rule).filter(
            Rule.profile_id == self.profile_id,
            Rule.target_category_id == category_id
        ).all()
    
    def update_rule(
        self,
        rule_id: int,
        target_category_id: int | None = None,
        rule_type: str | None = None,
        pattern: str | None = None,
        enabled: bool | None = None
    ) -> Optional[Rule]:
        """Update a rule.
        
        Args:
            rule_id: The rule ID.
            target_category_id: New category ID (optional).
            rule_type: New rule type (optional).
            pattern: New pattern (optional).
            enabled: New enabled state (optional).
        
        Returns:
            The updated Rule object, or None if not found.
        """
        session = self._get_session()
        rule = self.get_rule(rule_id)
        if rule:
            if target_category_id is not None:
                rule.target_category_id = target_category_id
            if rule_type is not None:
                rule.rule_type = rule_type
            if pattern is not None:
                rule.pattern = pattern
            if enabled is not None:
                rule.enabled = enabled
            session.commit()
            session.refresh(rule)
        return rule
    
    def delete_rule(self, rule_id: int) -> bool:
        """Delete a rule.
        
        Args:
            rule_id: The rule ID.
        
        Returns:
            True if deleted, False if not found.
        """
        session = self._get_session()
        rule = self.get_rule(rule_id)
        if rule:
            session.delete(rule)
            session.commit()
            return True
        return False
    
    def toggle_rule(self, rule_id: int) -> Optional[Rule]:
        """Toggle a rule's enabled state.
        
        Args:
            rule_id: The rule ID.
        
        Returns:
            The updated Rule object, or None if not found.
        """
        rule = self.get_rule(rule_id)
        if rule:
            return self.update_rule(rule_id, enabled=not rule.enabled)
        return None
    
    def close(self) -> None:
        """Close the session if we own it."""
        if self._owns_session and self._session is not None:
            self._session.close()
            self._session = None
