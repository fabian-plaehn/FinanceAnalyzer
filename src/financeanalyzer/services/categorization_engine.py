"""Categorization engine for FinanceAnalyzer."""

import re
from typing import List, Optional, Tuple

from sqlalchemy.orm import Session

from ..database.models import Entry, Rule, Category
from ..database.service import get_database_service


class CategorizationResult:
    """Result of categorizing an entry."""
    
    def __init__(
        self,
        entry: Entry,
        matching_rules: List[Rule],
        assigned_category: Optional[Category] = None,
        has_conflict: bool = False
    ):
        self.entry = entry
        self.matching_rules = matching_rules
        self.assigned_category = assigned_category
        self.has_conflict = has_conflict


class CategorizationEngine:
    """Engine for categorizing entries based on rules."""
    
    def __init__(self, profile_id: int, session: Session | None = None):
        """Initialize the categorization engine.
        
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
    
    def _get_enabled_rules(self) -> List[Rule]:
        """Get all enabled rules for the profile.
        
        Returns:
            List of enabled Rule objects.
        """
        session = self._get_session()
        return session.query(Rule).filter(
            Rule.profile_id == self.profile_id,
            Rule.enabled == True
        ).all()
    
    def _rule_matches(self, rule: Rule, description: str) -> bool:
        """Check if a rule matches the description.
        
        Args:
            rule: The rule to check.
            description: The entry description to match against.
        
        Returns:
            True if the rule matches, False otherwise.
        """
        if rule.rule_type == "contains":
            # Case-insensitive contains match
            return rule.pattern.lower() in description.lower()
        elif rule.rule_type == "regex":
            try:
                return bool(re.search(rule.pattern, description, re.IGNORECASE))
            except re.error:
                # Invalid regex, don't match
                return False
        return False
    
    def find_matching_rules(self, entry: Entry) -> List[Rule]:
        """Find all rules that match an entry.
        
        Args:
            entry: The entry to match against.
        
        Returns:
            List of matching Rule objects.
        """
        rules = self._get_enabled_rules()
        return [r for r in rules if self._rule_matches(r, entry.description)]
    
    def categorize_entry(self, entry: Entry, force: bool = False) -> CategorizationResult:
        """Categorize a single entry.
        
        Args:
            entry: The entry to categorize.
            force: If True, re-categorize even if manually categorized.
        
        Returns:
            CategorizationResult with the outcome.
        """
        session = self._get_session()
        
        # Skip if manually categorized (unless forced)
        if entry.is_manual_category and not force:
            return CategorizationResult(
                entry=entry,
                matching_rules=[],
                assigned_category=entry.category,
                has_conflict=False
            )
        
        matching_rules = self.find_matching_rules(entry)
        
        if len(matching_rules) == 0:
            # No matches - uncategorized
            entry.category_id = None
            entry.has_conflict = False
            session.commit()
            return CategorizationResult(
                entry=entry,
                matching_rules=[],
                assigned_category=None,
                has_conflict=False
            )
        
        elif len(matching_rules) == 1:
            # Single match - assign category
            rule = matching_rules[0]
            entry.category_id = rule.target_category_id
            entry.has_conflict = False
            entry.is_manual_category = False
            session.commit()
            session.refresh(entry)
            return CategorizationResult(
                entry=entry,
                matching_rules=matching_rules,
                assigned_category=entry.category,
                has_conflict=False
            )
        
        else:
            # Multiple matches - conflict
            # Check if all rules point to the same category
            categories = set(r.target_category_id for r in matching_rules)
            
            if len(categories) == 1:
                # All rules point to same category - no real conflict
                rule = matching_rules[0]
                entry.category_id = rule.target_category_id
                entry.has_conflict = False
                entry.is_manual_category = False
                session.commit()
                session.refresh(entry)
                return CategorizationResult(
                    entry=entry,
                    matching_rules=matching_rules,
                    assigned_category=entry.category,
                    has_conflict=False
                )
            else:
                # Real conflict - different categories
                entry.category_id = None
                entry.has_conflict = True
                entry.is_manual_category = False
                session.commit()
                return CategorizationResult(
                    entry=entry,
                    matching_rules=matching_rules,
                    assigned_category=None,
                    has_conflict=True
                )
    
    def categorize_all_entries(self, force: bool = False) -> List[CategorizationResult]:
        """Categorize all entries in the profile.
        
        Args:
            force: If True, re-categorize even manually categorized entries.
        
        Returns:
            List of CategorizationResult objects.
        """
        session = self._get_session()
        
        query = session.query(Entry).filter(Entry.profile_id == self.profile_id)
        if not force:
            query = query.filter(Entry.is_manual_category == False)
        
        entries = query.all()
        results = []
        
        for entry in entries:
            result = self.categorize_entry(entry, force=force)
            results.append(result)
        
        return results
    
    def reapply_rules(self) -> Tuple[int, int, int]:
        """Reapply all rules to non-manually categorized entries.
        
        Returns:
            Tuple of (categorized_count, conflict_count, uncategorized_count).
        """
        results = self.categorize_all_entries(force=False)
        
        categorized = sum(1 for r in results if r.assigned_category and not r.has_conflict)
        conflicts = sum(1 for r in results if r.has_conflict)
        uncategorized = sum(1 for r in results if not r.assigned_category and not r.has_conflict)
        
        return categorized, conflicts, uncategorized
    
    def close(self) -> None:
        """Close the session if we own it."""
        if self._owns_session and self._session is not None:
            self._session.close()
            self._session = None
