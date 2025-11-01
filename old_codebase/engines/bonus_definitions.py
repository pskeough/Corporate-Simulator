"""
Bonus Definitions - Central registry for all game bonuses.

Bonus Types:
- food_per_turn: Food production per turn
- wealth_per_turn: Wealth production per turn
- science_per_turn: Science points per turn
- culture_per_turn: Culture points per turn
- population_growth: Population growth rate modifier
- happiness: Happiness modifier

Bonus Sources:
- characters: Inner circle members by role
- buildings: Infrastructure by name (future)
- technologies: Discoveries by name (future)
- leader_traits: Leader traits (future)
"""

# Character role bonuses (migrated from world_turns_engine.py)
CHARACTER_ROLE_BONUSES = {
    'Leader': {
        'science_per_turn': 1,
        'culture_per_turn': 1,
        'description': 'Leaders provide baseline progress (temporary test bonus)'
    },
    'Scholar': {
        'science_per_turn': 5,
        'description': 'Scholars contribute to scientific advancement'
    },
    'Artisan': {
        'culture_per_turn': 5,
        'description': 'Artisans enrich cultural development'
    },
    'Spymaster': {
        'description': 'Spymasters provide intelligence advantages'
        # No numeric bonuses yet, but reserved for future
    },
    'Grand Marshal': {
        'food_per_turn': -5,
        'description': 'Military leaders strengthen defense but consume resources'
        # Future: 'military_strength': 10
    },
    'Chancellor': {
        'wealth_per_turn': 10,
        'description': 'Chancellors manage finances and boost economic output'
    },
    'High Priestess': {
        'description': 'Religious leaders boost faith'
        # Future: 'religious_influence': 5
    }
}

# Building bonuses (Phase 4 - populated from building_types.json)
# BALANCE CHANGE (2025-01): Added per-building maintenance costs
BUILDING_BONUSES = {
    'building_granary_001': {
        'food_per_turn': 10,
        'maintenance_cost': 8,      # NEW: Basic storage, low complexity
        'description': 'Granaries store surplus food'
    },
    'building_barracks_001': {
        'military_strength': 5,
        'maintenance_cost': 15,     # NEW: Soldiers expensive to maintain
        'description': 'Barracks train warriors'
    },
    'building_market_001': {
        'wealth_per_turn': 15,
        'maintenance_cost': 12,     # NEW: Trade infrastructure and staff
        'description': 'Markets facilitate trade'
    },
    'building_library_001': {
        'science_per_turn': 8,
        'maintenance_cost': 20,     # NEW: Scholars + rare books very expensive
        'description': 'Libraries preserve knowledge'
    },
    'building_temple_001': {
        'happiness': 5,
        'culture_per_turn': 5,
        'maintenance_cost': 18,     # NEW: Priests + rituals + upkeep
        'description': 'Temples strengthen faith'
    },
    'building_workshop_001': {
        'culture_per_turn': 3,
        'wealth_per_turn': 5,
        'maintenance_cost': 14,     # NEW: Artisans + materials
        'description': 'Workshops produce goods'
    }
}

# Technology bonuses (placeholder for future implementation)
TECHNOLOGY_BONUSES = {
    # Example structure for Phase 4:
    # 'Agriculture': {
    #     'food_production_multiplier': 1.2,
    #     'description': 'Improved farming techniques'
    # },
    # 'Writing': {
    #     'science_per_turn': 3,
    #     'culture_per_turn': 2,
    #     'description': 'Recording knowledge'
    # }
}

# Leader trait bonuses (integrated with BonusEngine)
LEADER_TRAIT_BONUSES = {
    'Wise': {
        'science_per_turn': 2,
        'description': 'Deep understanding and insight provides scientific progress'
    },
    'Scholar': {
        'science_per_turn': 3,
        'description': 'Devotion to knowledge accelerates technological advancement'
    },
    'Prosperous': {
        'wealth_per_turn': 5,
        'description': 'Brings wealth and abundance to the civilization'
    },
    'Mercantile': {
        'wealth_per_turn': 3,
        'description': 'Skilled in trade and commerce enhances economic output'
    },
    'Visionary': {
        'culture_per_turn': 2,
        'description': 'Sees beyond the present, inspiring cultural development'
    },
    'Charismatic': {
        'culture_per_turn': 1,
        'description': 'Natural inspiration encourages artistic expression'
    }
}

# Bonus type constants for type safety
class BonusType:
    FOOD_PER_TURN = 'food_per_turn'
    WEALTH_PER_TURN = 'wealth_per_turn'
    SCIENCE_PER_TURN = 'science_per_turn'
    CULTURE_PER_TURN = 'culture_per_turn'
    POPULATION_GROWTH = 'population_growth'
    HAPPINESS = 'happiness'

    # Future bonus types
    FOOD_MULTIPLIER = 'food_production_multiplier'
    WEALTH_MULTIPLIER = 'wealth_production_multiplier'
    MILITARY_STRENGTH = 'military_strength'
    MILITARY_EFFECTIVENESS_MULTIPLIER = 'military_effectiveness_multiplier'
    RELIGIOUS_INFLUENCE = 'religious_influence'

# Helper to validate bonus types
def is_valid_bonus_type(bonus_type):
    """Check if bonus type is valid."""
    valid_types = [
        BonusType.FOOD_PER_TURN,
        BonusType.WEALTH_PER_TURN,
        BonusType.SCIENCE_PER_TURN,
        BonusType.CULTURE_PER_TURN,
        BonusType.POPULATION_GROWTH,
        BonusType.HAPPINESS,
        BonusType.FOOD_MULTIPLIER,
        BonusType.WEALTH_MULTIPLIER,
        BonusType.MILITARY_STRENGTH,
        BonusType.MILITARY_EFFECTIVENESS_MULTIPLIER,
        BonusType.RELIGIOUS_INFLUENCE
    ]
    return bonus_type in valid_types
