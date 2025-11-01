"""
InnerCircleManager - Centralized character access and relationship tracking.
"""

class InnerCircleManager:
    def __init__(self, characters_data):
        """
        Initialize inner circle manager.

        Args:
            characters_data: List of character dicts OR dict with 'characters' key
        """
        # Handle both list and dict formats
        if isinstance(characters_data, dict):
            self._characters = characters_data.get('characters', [])
        elif isinstance(characters_data, list):
            self._characters = characters_data
        else:
            self._characters = []

        # Build name index for fast lookups
        self._name_index = {char['name']: char for char in self._characters}

    def get_by_name(self, character_name):
        """
        Get character by name.

        Args:
            character_name: Character name string

        Returns:
            Character dict or None if not found
        """
        return self._name_index.get(character_name)

    def get_by_faction_id(self, faction_id):
        """
        Get all characters linked to a faction.

        Args:
            faction_id: Faction ID string

        Returns:
            List of character dicts
        """
        return [char for char in self._characters
                if char.get('faction_id') == faction_id]

    def get_all(self):
        """
        Get all characters as a list.

        Returns:
            List of character dicts
        """
        return self._characters

    def to_dict(self):
        """
        Convert to dictionary format for JSON serialization.

        Returns:
            Dictionary with 'characters' key
        """
        return {"characters": self._characters}

    def update_metrics(self, character_name, relationship=0, influence=0, loyalty=0):
        """
        Update character metrics.

        Args:
            character_name: Character name
            relationship: Change to relationship metric
            influence: Change to influence metric
            loyalty: Change to loyalty metric

        Returns:
            True if updated, False if character not found
        """
        character = self.get_by_name(character_name)
        if not character:
            return False

        metrics = character.setdefault('metrics', {})

        if relationship != 0:
            current = metrics.get('relationship', 50)
            metrics['relationship'] = max(0, min(100, current + relationship))

        if influence != 0:
            current = metrics.get('influence', 50)
            metrics['influence'] = max(0, min(100, current + influence))

        if loyalty != 0:
            current = metrics.get('loyalty', 50)
            metrics['loyalty'] = max(0, min(100, current + loyalty))

        return True

    def add_memory(self, character_name, memory_text, turn_number):
        """
        Add memory to character history for context indexing.

        Args:
            character_name: Character name
            memory_text: Description of the memory/event
            turn_number: Current turn number for indexing

        Returns:
            True if added, False if character not found
        """
        character = self.get_by_name(character_name)
        if not character:
            return False

        history = character.setdefault('history', [])
        memory = f"Turn {turn_number}: {memory_text}"
        history.append(memory)

        # Keep last 10 memories to avoid JSON bloat
        if len(history) > 10:
            character['history'] = history[-10:]

        return True

    def __len__(self):
        """Return number of characters."""
        return len(self._characters)

    def __iter__(self):
        """Allow iteration over characters."""
        return iter(self._characters)
