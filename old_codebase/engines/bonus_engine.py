"""
BonusEngine - Centralized bonus calculation and aggregation.
Collects bonuses from characters, buildings, technologies, and leader traits.
"""

from engines.bonus_definitions import (
    CHARACTER_ROLE_BONUSES,
    BUILDING_BONUSES,
    TECHNOLOGY_BONUSES,
    LEADER_TRAIT_BONUSES,
    BonusType,
    is_valid_bonus_type
)


class BonusEngine:
    """
    Aggregates bonuses from all sources in the game.

    Usage:
        engine = BonusEngine()
        science = engine.calculate_bonuses(game_state, BonusType.SCIENCE_PER_TURN)
        print(f"Total science bonus: {science['total']}")
        for source_type, source_name, value in science['sources']:
            print(f"  +{value} from {source_type}: {source_name}")
    """

    def __init__(self):
        """Initialize bonus engine."""
        pass

    def calculate_bonuses(self, game_state, bonus_type):
        """
        Calculate total bonuses for a given type from all sources.

        Args:
            game_state: GameState instance
            bonus_type: Bonus type string (use BonusType constants)

        Returns:
            Dictionary with:
            - 'total': Total bonus value (int)
            - 'sources': List of (source_type, source_name, value) tuples
            - 'multipliers': List of (source_type, source_name, multiplier) tuples
        """
        if not is_valid_bonus_type(bonus_type):
            print(f"Warning: Invalid bonus type '{bonus_type}'")
            return {'total': 0, 'sources': [], 'multipliers': []}

        bonuses = {
            'total': 0,
            'sources': [],
            'multipliers': []
        }

        # Collect bonuses from all sources
        self._add_character_bonuses(game_state, bonus_type, bonuses)
        self._add_building_bonuses(game_state, bonus_type, bonuses)
        self._add_technology_bonuses(game_state, bonus_type, bonuses)
        self._add_leader_trait_bonuses(game_state, bonus_type, bonuses)
        self._add_faction_bonuses(game_state, bonus_type, bonuses)

        # Sum up all bonuses
        bonuses['total'] = sum(value for _, _, value in bonuses['sources'])

        return bonuses

    def _add_character_bonuses(self, game_state, bonus_type, bonuses):
        """Add bonuses from inner circle characters and the civilization leader."""
        # Check civilization leader first
        leader = game_state.civilization.get('leader', {})
        if leader:
            leader_role = leader.get('role')
            if leader_role:
                role_bonuses = CHARACTER_ROLE_BONUSES.get(leader_role, {})
                bonus_value = role_bonuses.get(bonus_type, 0)

                if bonus_value > 0:
                    bonuses['sources'].append((
                        'leader',
                        leader.get('name', 'Unknown Leader'),
                        bonus_value
                    ))

        # Check inner circle characters
        if not hasattr(game_state, 'inner_circle_manager'):
            return

        for character in game_state.inner_circle_manager:
            role = character.get('role')
            if not role:
                continue

            role_bonuses = CHARACTER_ROLE_BONUSES.get(role, {})
            bonus_value = role_bonuses.get(bonus_type, 0)

            if bonus_value > 0:
                bonuses['sources'].append((
                    'character',
                    character.get('name', 'Unknown'),
                    bonus_value
                ))

    def _add_building_bonuses(self, game_state, bonus_type, bonuses):
        """
        Add bonuses from constructed buildings with diminishing returns.

        BALANCE CHANGE (2025-01): Duplicate buildings provide reduced bonuses.
        Formula: 1 / (1 + (count - 1) * 0.3)
        - 1st building: 100% effectiveness
        - 2nd building: 77% effectiveness
        - 3rd building: 63% effectiveness
        - 5th building: 45% effectiveness

        This encourages diversification over spamming one building type.
        """
        # Count buildings by type
        building_counts = {}
        building_base_bonuses = {}

        # Phase 4: Use buildings from game state
        if hasattr(game_state, 'buildings'):
            constructed = game_state.buildings.get('constructed_buildings', [])

            for building in constructed:
                building_id = building.get('id')
                building_name = building.get('name', building_id)

                # Count this building type
                building_counts[building_id] = building_counts.get(building_id, 0) + 1

                # Store base bonus for this type
                if building_id not in building_base_bonuses:
                    building_bonuses_def = BUILDING_BONUSES.get(building_id, {})
                    building_base_bonuses[building_id] = {
                        'bonus': building_bonuses_def.get(bonus_type, 0),
                        'name': building_name
                    }

        # Legacy: Also check infrastructure (backward compatibility)
        infrastructure = game_state.technology.get('infrastructure', [])
        for building_name in infrastructure:
            building_counts[building_name] = building_counts.get(building_name, 0) + 1

            if building_name not in building_base_bonuses:
                building_bonuses_def = BUILDING_BONUSES.get(building_name, {})
                building_base_bonuses[building_name] = {
                    'bonus': building_bonuses_def.get(bonus_type, 0),
                    'name': building_name
                }

        # Apply diminishing returns and add to bonuses
        for building_id, count in building_counts.items():
            base_data = building_base_bonuses.get(building_id, {})
            base_bonus = base_data.get('bonus', 0)

            if base_bonus > 0:
                # Calculate total bonus with diminishing returns
                total_bonus = 0
                for i in range(count):
                    diminishing_factor = 1.0 / (1 + i * 0.3)
                    total_bonus += base_bonus * diminishing_factor

                total_bonus = int(total_bonus)

                # Format name to show count
                display_name = base_data.get('name', building_id)
                if count > 1:
                    display_name = f"{display_name} (x{count})"

                bonuses['sources'].append((
                    'building',
                    display_name,
                    total_bonus
                ))

    def _add_technology_bonuses(self, game_state, bonus_type, bonuses):
        """Add bonuses from discovered technologies."""
        discoveries = game_state.technology.get('discoveries', [])

        for tech_name in discoveries:
            tech_bonuses = TECHNOLOGY_BONUSES.get(tech_name, {})
            bonus_value = tech_bonuses.get(bonus_type, 0)

            if bonus_value > 0:
                bonuses['sources'].append((
                    'technology',
                    tech_name,
                    bonus_value
                ))

            # Handle multipliers (e.g., +20% food production)
            multiplier_key = bonus_type.replace('_per_turn', '_multiplier')
            multiplier_value = tech_bonuses.get(multiplier_key, 0)

            if multiplier_value > 0:
                bonuses['multipliers'].append((
                    'technology',
                    tech_name,
                    multiplier_value
                ))

    def _add_leader_trait_bonuses(self, game_state, bonus_type, bonuses):
        """Add bonuses from leader traits."""
        leader = game_state.civilization.get('leader', {})
        traits = leader.get('traits', [])

        for trait in traits:
            trait_bonuses = LEADER_TRAIT_BONUSES.get(trait, {})
            bonus_value = trait_bonuses.get(bonus_type, 0)

            if bonus_value > 0:
                bonuses['sources'].append((
                    'leader_trait',
                    trait,
                    bonus_value
                ))

    def _add_faction_bonuses(self, game_state, bonus_type, bonuses):
        """Add bonuses/multipliers from faction approval levels."""
        if not hasattr(game_state, 'faction_manager'):
            return

        faction_bonuses = game_state.faction_manager.get_faction_bonuses(game_state)

        # Check if this is the military effectiveness multiplier
        if bonus_type == BonusType.MILITARY_EFFECTIVENESS_MULTIPLIER:
            multiplier_value = faction_bonuses.get('military_effectiveness', 1.0)

            if multiplier_value != 1.0:
                bonuses['multipliers'].append((
                    'faction_approval',
                    'Overall Faction Standing',
                    multiplier_value
                ))

    def get_all_active_bonuses(self, game_state):
        """
        Get all active bonuses across all types.
        Useful for debugging and UI display.

        Returns:
            Dictionary mapping bonus_type -> bonus result
        """
        all_bonus_types = [
            BonusType.FOOD_PER_TURN,
            BonusType.WEALTH_PER_TURN,
            BonusType.SCIENCE_PER_TURN,
            BonusType.CULTURE_PER_TURN,
            BonusType.POPULATION_GROWTH,
            BonusType.HAPPINESS
        ]

        active_bonuses = {}
        for bonus_type in all_bonus_types:
            result = self.calculate_bonuses(game_state, bonus_type)
            if result['total'] > 0 or result['sources']:
                active_bonuses[bonus_type] = result

        return active_bonuses

    def format_bonus_summary(self, game_state):
        """
        Create human-readable summary of all active bonuses.
        Useful for logging and debugging.
        """
        active = self.get_all_active_bonuses(game_state)

        if not active:
            return "No active bonuses"

        lines = ["Active Bonuses:"]
        for bonus_type, result in active.items():
            lines.append(f"  {bonus_type}: +{result['total']}")
            for source_type, source_name, value in result['sources']:
                lines.append(f"    +{value} from {source_type}: {source_name}")

        return "\n".join(lines)
