"""
FactionManager - Centralized faction access with ID and name-based lookups.
Provides backward compatibility while enabling ID-based references.
"""

class FactionManager:
    def __init__(self, factions_data):
        """
        Initialize faction manager.

        Args:
            factions_data: Dictionary with 'factions' key containing list of faction dicts
                         OR a list of faction dicts directly (backward compat)
        """
        # Handle both dict and list formats
        if isinstance(factions_data, dict):
            self._factions = factions_data.get('factions', [])
        elif isinstance(factions_data, list):
            self._factions = factions_data
        else:
            self._factions = []

        # Build indices for fast lookups
        self._id_index = {}
        self._name_index = {}

        for faction in self._factions:
            if 'id' in faction:
                self._id_index[faction['id']] = faction
            if 'name' in faction:
                self._name_index[faction['name']] = faction

    def get_by_id(self, faction_id):
        """
        Get faction by ID (preferred method).

        Args:
            faction_id: Faction ID string (e.g., 'faction_merchants_guild_001')

        Returns:
            Faction dict or None if not found
        """
        return self._id_index.get(faction_id)

    def get_by_name(self, faction_name):
        """
        Get faction by name (legacy compatibility).

        Args:
            faction_name: Faction name string (e.g., 'The Merchant\'s Guild')

        Returns:
            Faction dict or None if not found
        """
        return self._name_index.get(faction_name)

    def get_all(self):
        """
        Get all factions as a list.

        Returns:
            List of faction dicts
        """
        return self._factions

    def to_dict(self):
        """
        Convert to dictionary format for JSON serialization.

        Returns:
            Dictionary with 'factions' key
        """
        return {"factions": self._factions}

    def update_approval(self, faction_id, change):
        """
        Update faction approval rating.

        Args:
            faction_id: Faction ID or name (checks both)
            change: Integer change to apply (can be negative)

        Returns:
            True if updated, False if faction not found
        """
        # Try ID first, then name
        faction = self.get_by_id(faction_id)
        if not faction:
            faction = self.get_by_name(faction_id)

        if faction:
            current = faction.get('approval', 60)
            faction['approval'] = max(0, min(100, current + change))
            return True
        return False

    def __len__(self):
        """Return number of factions."""
        return len(self._factions)

    def __iter__(self):
        """Allow iteration over factions."""
        return iter(self._factions)

    def get_faction_bonuses(self, game_state):
        """
        BALANCE_OVERHAUL: Calculate passive mechanical effects from faction approval levels.
        Returns dict of bonuses/penalties to apply to game state.
        """
        bonuses = {
            'wealth_multiplier': 1.0,
            'military_effectiveness': 1.0,
            'happiness_modifier': 0
        }

        for faction in self._factions:
            faction_id = faction.get('id', '')
            approval = faction.get('approval', 60)

            # Merchant's Guild effects
            if 'merchant' in faction_id.lower():
                if approval >= 75:
                    bonuses['wealth_multiplier'] *= 1.10  # +10% wealth
                elif approval < 50 and approval >= 25:
                    bonuses['wealth_multiplier'] *= 0.90  # -10% wealth
                elif approval < 25:
                    bonuses['wealth_multiplier'] *= 0.75  # -25% wealth

            # Warrior Caste effects
            elif 'warrior' in faction_id.lower() or 'military' in faction_id.lower():
                if approval >= 75:
                    bonuses['military_effectiveness'] *= 1.15  # +15% military
                elif approval < 50 and approval >= 25:
                    bonuses['military_effectiveness'] *= 0.85  # -15% military
                elif approval < 25:
                    bonuses['military_effectiveness'] *= 0.70  # -30% military

            # Priest Order effects
            elif 'priest' in faction_id.lower() or 'religious' in faction_id.lower():
                if approval >= 75:
                    bonuses['happiness_modifier'] += 10
                elif approval < 50 and approval >= 25:
                    bonuses['happiness_modifier'] -= 10
                elif approval < 25:
                    bonuses['happiness_modifier'] -= 20

        return bonuses

    def add_history_entry(self, faction_id, reason, change, turn_number):
        """
        Add history entry to faction for context and UI display.

        Args:
            faction_id: Faction ID or name
            reason: Human-readable reason for the change
            change: Integer change to approval (can be negative)
            turn_number: Current turn number for indexing

        Returns:
            True if added, False if faction not found
        """
        # Try ID first, then name
        faction = self.get_by_id(faction_id)
        if not faction:
            faction = self.get_by_name(faction_id)

        if faction:
            history = faction.setdefault('history', [])
            entry = f"Turn {turn_number}: {reason} ({change:+d} approval)"
            history.append(entry)

            # Keep last 10 entries to avoid JSON bloat
            if len(history) > 10:
                faction['history'] = history[-10:]

            return True
        return False

