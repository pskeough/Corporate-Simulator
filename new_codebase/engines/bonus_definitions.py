"""
Bonus Definitions for Corporate Decision Simulator

Central registry for all business-related bonuses and their sources.

Bonus Types:
- budget_per_turn: Bonus to quarterly budget generation (revenue).
- political_capital_per_turn: Bonus to player's influence generation.
- innovation_points: Represents R&D and product development progress.
- employee_morale: Company-wide morale modifier.

Bonus Sources:
- personnel_roles: Bonuses from key personnel based on their roles.
- internal_tools: Bonuses from corporate assets and software.
- player_skills: Bonuses derived from the player's professional skills.
"""

# Bonuses from key personnel roles
PERSONNEL_ROLE_BONUSES = {
    'CFO': {
        'budget_per_turn': 50000,
        'description': 'An effective CFO optimizes finances and increases revenue.'
    },
    'CTO': {
        'innovation_points': 20,
        'description': 'A skilled CTO drives technological advancement.'
    },
    'COO': {
        'budget_per_turn': -10000, # Represents operational costs
        'employee_morale': 5,
        'description': 'A COO streamlines operations, improving morale at a cost.'
    },
    'Chief People Officer': {
        'employee_morale': 10,
        'description': 'Boosts company-wide morale and employee satisfaction.'
    }
}

# Bonuses from internal tools and corporate assets
INTERNAL_TOOL_BONUSES = {
    'Custom CRM "OmniLeads"': {
        'budget_per_turn': 25000,
        'maintenance_cost': 5000,
        'description': 'A custom CRM improves sales efficiency.'
    },
    'JIRA': {
        'innovation_points': 5,
        'maintenance_cost': 2000,
        'description': 'JIRA improves project tracking for development teams.'
    }
}

# Bonuses from player's professional skills
PLAYER_SKILL_BONUSES = {
    'Data Analysis': {
        'budget_per_turn': 10000,
        'description': 'Data analysis skills help identify revenue opportunities.'
    },
    'Project Management': {
        'innovation_points': 5,
        'description': 'Efficiently managed projects yield faster innovation.'
    },
    'Negotiation': {
        'political_capital_per_turn': 10,
        'description': 'Skilled negotiation builds influence.'
    }
}

# Bonus type constants for clarity and type safety
class BonusType:
    BUDGET_PER_TURN = 'budget_per_turn'
    POLITICAL_CAPITAL_PER_TURN = 'political_capital_per_turn'
    INNOVATION_POINTS = 'innovation_points'
    EMPLOYEE_MORALE = 'employee_morale'

    # Multipliers
    BUDGET_MULTIPLIER = 'budget_multiplier'

def is_valid_bonus_type(bonus_type):
    """Checks if a given bonus type is a valid, defined bonus."""
    valid_types = [
        BonusType.BUDGET_PER_TURN,
        BonusType.POLITICAL_CAPITAL_PER_TURN,
        BonusType.INNOVATION_POINTS,
        BonusType.EMPLOYEE_MORALE,
        BonusType.BUDGET_MULTIPLIER
    ]
    return bonus_type in valid_types
