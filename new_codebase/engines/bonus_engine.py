"""
BonusEngine - Centralized bonus calculation for the Corporate Decision Simulator.
Aggregates bonuses from personnel, internal tools, and player skills.
"""

from engines.bonus_definitions import (
    PERSONNEL_ROLE_BONUSES,
    INTERNAL_TOOL_BONUSES,
    PLAYER_SKILL_BONUSES,
    BonusType,
    is_valid_bonus_type
)

class BonusEngine:
    """
    Calculates and aggregates bonuses from all relevant sources in the simulation.
    """

    def calculate_bonuses(self, game_state, bonus_type):
        """
        Calculates the total bonus for a given type from all applicable sources.

        Args:
            game_state: The current GameState object.
            bonus_type (str): The type of bonus to calculate (e.g., BonusType.BUDGET_PER_TURN).

        Returns:
            dict: A dictionary containing the total bonus and a list of its sources.
        """
        if not is_valid_bonus_type(bonus_type):
            print(f"Warning: Invalid bonus type '{bonus_type}'")
            return {'total': 0, 'sources': [], 'multipliers': []}

        bonuses = {
            'total': 0,
            'sources': [],
            'multipliers': []
        }

        self._add_personnel_bonuses(game_state, bonus_type, bonuses)
        self._add_internal_tool_bonuses(game_state, bonus_type, bonuses)
        self._add_player_skill_bonuses(game_state, bonus_type, bonuses)
        self._add_department_bonuses(game_state, bonus_type, bonuses)

        bonuses['total'] = sum(value for _, _, value in bonuses['sources'])
        return bonuses

    def _add_personnel_bonuses(self, game_state, bonus_type, bonuses):
        """Adds bonuses from key personnel based on their roles."""
        if not hasattr(game_state, 'key_personnel'):
            return

        for person in game_state.key_personnel.get('personnel', []):
            role = person.get('person', {}).get('relationship_to_player')
            if not role:
                continue

            role_bonuses = PERSONNEL_ROLE_BONUSES.get(role, {})
            bonus_value = role_bonuses.get(bonus_type, 0)

            if bonus_value != 0:
                bonuses['sources'].append((
                    'Personnel',
                    person.get('person', {}).get('name', 'Unknown'),
                    bonus_value
                ))

    def _add_internal_tool_bonuses(self, game_state, bonus_type, bonuses):
        """Adds bonuses from the company's internal tools and assets."""
        tools = game_state.skills_and_assets['corporation'].get('internal_tools', [])
        for tool in tools:
            tool_bonuses = INTERNAL_TOOL_BONUSES.get(tool, {})
            bonus_value = tool_bonuses.get(bonus_type, 0)
            if bonus_value != 0:
                bonuses['sources'].append(('Internal Tool', tool, bonus_value))

    def _add_player_skill_bonuses(self, game_state, bonus_type, bonuses):
        """Adds bonuses from the player's own skills."""
        skills = game_state.player.get('skills', [])
        for skill in skills:
            skill_bonuses = PLAYER_SKILL_BONUSES.get(skill, {})
            bonus_value = skill_bonuses.get(bonus_type, 0)
            if bonus_value != 0:
                bonuses['sources'].append(('Player Skill', skill, bonus_value))

    def _add_department_bonuses(self, game_state, bonus_type, bonuses):
        """Adds multipliers from high-morale departments."""
        if not hasattr(game_state, 'department_manager'):
            return

        department_bonuses = game_state.department_manager.get_department_bonuses(game_state)
        if bonus_type == BonusType.BUDGET_MULTIPLIER:
            multiplier = department_bonuses.get('budget_multiplier', 1.0)
            if multiplier != 1.0:
                bonuses['multipliers'].append(('Department Morale', 'High-performing departments', multiplier))

    def get_all_active_bonuses(self, game_state):
        """Retrieves all active bonuses across every category."""
        all_bonus_types = [
            BonusType.BUDGET_PER_TURN,
            BonusType.POLITICAL_CAPITAL_PER_TURN,
            BonusType.INNOVATION_POINTS,
            BonusType.EMPLOYEE_MORALE
        ]
        active_bonuses = {}
        for bonus_type in all_bonus_types:
            result = self.calculate_bonuses(game_state, bonus_type)
            if result['total'] != 0 or result['sources']:
                active_bonuses[bonus_type] = result
        return active_bonuses
