# engines/leader_engine.py
"""
Leader mechanics: traits, aging, succession, legacy bonuses.
Adds personality and strategic depth to leadership.
"""

# BALANCE_OVERHAUL: Comprehensive trait definitions with real trade-offs
# Every trait now has penalties as well as bonuses for strategic depth
TRAIT_EFFECTS = {
    # Combat/Military Traits - powerful but socially/economically costly
    'Brave': {
        'description': 'Fearless in battle, inspires troops',
        'bonuses': {'military_reputation': 5, 'combat_success': 0.15},
        'penalties': {'diplomatic_reputation': -5, 'wealth_generation': -0.05},
        'event_tags': ['military', 'warfare', 'defense']
    },
    'Warrior': {
        'description': 'Skilled in combat and strategy',
        'bonuses': {'military_reputation': 10, 'combat_success': 0.20},
        'penalties': {'wealth_generation': -0.15, 'economic_reputation': -10},
        'event_tags': ['military', 'warfare', 'conquest']
    },
    'Ruthless': {
        'description': 'Willing to do whatever it takes',
        'bonuses': {'military_reputation': 15, 'harsh_success': 0.20},
        'penalties': {'diplomatic_reputation': -15, 'happiness': -10, 'unrest_chance': 0.20},
        'event_tags': ['cruelty', 'pragmatism', 'conquest']
    },

    # Wisdom/Intelligence Traits - great for knowledge, poor for practical matters
    'Wise': {
        'description': 'Deep understanding and insight',
        'bonuses': {'investigation_depth': 1, 'advisor_quality': 0.15},
        'penalties': {'military_reputation': -5},
        'event_tags': ['wisdom', 'learning', 'teaching']
    },
    'Scholar': {
        'description': 'Devoted to knowledge and learning',
        'bonuses': {'tech_progress': 0.15, 'discovery_chance': 0.15},
        'penalties': {'practical_resource_generation': -0.15, 'military_reputation': -10},
        'event_tags': ['technology', 'learning', 'discovery']
    },

    # Spiritual/Religious Traits - powerful for faith, antagonizes secular factions
    'Pious': {
        'description': 'Deeply religious and faithful',
        'bonuses': {'religious_reputation': 15, 'priest_faction_approval': 10},
        'penalties': {'merchant_faction_approval': -20, 'tech_progress': -0.10},
        'event_tags': ['religion', 'faith', 'ritual']
    },
    'Mystic': {
        'description': 'Connected to spiritual forces',
        'bonuses': {'religious_reputation': 10, 'ritual_power': 0.20},
        'penalties': {'diplomatic_reputation': -10, 'economic_reputation': -5},
        'event_tags': ['religion', 'magic', 'spirits']
    },
    'Visionary': {
        'description': 'Sees beyond the present',
        'bonuses': {'cultural_progress': 0.10, 'prophecy_bonus': 0.15},
        'penalties': {},
        'event_tags': ['culture', 'vision', 'prophecy']
    },

    # Social/Diplomatic Traits - excellent for peace, weak in crisis
    'Charismatic': {
        'description': 'Naturally inspiring and persuasive',
        'bonuses': {'diplomatic_reputation': 10, 'alliance_strength': 0.15},
        'penalties': {'military_effectiveness': -0.10},
        'event_tags': ['diplomacy', 'persuasion', 'leadership']
    },
    'Diplomatic': {
        'description': 'Skilled negotiator and peacemaker',
        'bonuses': {'diplomatic_reputation': 15, 'peace_bonus': 0.20},
        'penalties': {'military_reputation': -10, 'warrior_faction_approval': -15},
        'event_tags': ['diplomacy', 'peace', 'negotiation']
    },
    'Just': {
        'description': 'Fair and honorable in all things',
        'bonuses': {'diplomatic_reputation': 6, 'promise_weight': 0.15},
        'penalties': {},
        'event_tags': ['justice', 'honor', 'law']
    },

    # Economic Traits - wealthy but politically divisive
    'Prosperous': {
        'description': 'Brings wealth and abundance',
        'bonuses': {'economic_reputation': 10, 'wealth_generation': 0.15},
        'penalties': {'warrior_faction_approval': -10, 'military_effectiveness': -0.10},
        'event_tags': ['economy', 'trade', 'wealth']
    },
    'Mercantile': {
        'description': 'Skilled in trade and commerce',
        'bonuses': {'economic_reputation': 15, 'trade_bonus': 0.20, 'merchant_faction_approval': 15},
        'penalties': {'warrior_faction_approval': -20, 'military_effectiveness': -0.15},
        'event_tags': ['trade', 'commerce', 'market']
    },

    # Negative/Complex Traits
    'Tactical': {
        'description': 'Master strategist and planner',
        'bonuses': {'military_reputation': 6, 'defensive_bonus': 0.15},
        'penalties': {},
        'event_tags': ['military', 'strategy', 'planning']
    },
    'Cunning': {
        'description': 'Clever and resourceful',
        'bonuses': {'diplomatic_reputation': 5, 'negotiation_bonus': 0.15},
        'penalties': {},
        'event_tags': ['diplomacy', 'intrigue', 'negotiation']
    },
    'Ambitious': {
        'description': 'Driven to achieve greatness',
        'bonuses': {'all_progress': 0.10, 'risk_events': 0.15},
        'penalties': {},
        'event_tags': ['ambition', 'risk', 'growth']
    },
    'Paranoid': {
        'description': 'Distrustful but vigilant',
        'bonuses': {'defensive_bonus': 0.20},
        'penalties': {'diplomatic_reputation': -5},
        'event_tags': ['suspicion', 'defense', 'isolation']
    },

    # Age-Related Traits (gained through aging)
    'Ancient': {
        'description': 'Lived far beyond normal years',
        'bonuses': {'wisdom_bonus': 0.15},
        'penalties': {'health_penalty': 0.30, 'effectiveness': -0.20},
        'event_tags': ['wisdom', 'age', 'legacy']
    },
    'Experienced': {
        'description': 'Seasoned by years of rule',
        'bonuses': {'all_reputation': 5, 'decision_quality': 0.10},
        'penalties': {},
        'event_tags': ['experience', 'wisdom', 'leadership']
    }
}

def get_trait_bonus(leader, bonus_type):
    """
    BALANCE_OVERHAUL: Calculate total bonus from all leader traits for a specific type.
    Now handles both bonuses and penalties.

    Args:
        leader: Leader dict with 'traits' list
        bonus_type: Type of bonus (e.g., 'military_reputation', 'combat_success')

    Returns:
        Total bonus value (additive, can be negative)
    """
    traits = leader.get('traits', [])
    total_bonus = 0

    for trait in traits:
        trait_data = TRAIT_EFFECTS.get(trait, {})

        # Add bonuses
        bonuses = trait_data.get('bonuses', {})
        if bonus_type in bonuses:
            total_bonus += bonuses[bonus_type]

        # Apply penalties (penalties are stored as negative values or subtracted)
        penalties = trait_data.get('penalties', {})
        if bonus_type in penalties:
            penalty_value = penalties[bonus_type]
            # If penalty is stored as positive (e.g., 15), make it negative
            if penalty_value > 0:
                total_bonus -= penalty_value
            else:
                # If penalty is already negative (e.g., -15), add it directly
                total_bonus += penalty_value

    return total_bonus

def get_leader_event_tags(leader):
    """
    Get all event tags from leader traits.
    These can be used to weight event generation toward leader's strengths.
    """
    traits = leader.get('traits', [])
    tags = []

    for trait in traits:
        trait_data = TRAIT_EFFECTS.get(trait, {})
        tags.extend(trait_data.get('event_tags', []))

    return list(set(tags))  # Remove duplicates

def apply_aging_effects(game_state):
    """
    Apply age-based trait modifications and health effects.
    As leaders age, they gain wisdom but lose health.
    """
    leader = game_state.civilization['leader']
    age = leader.get('age', 0)
    life_exp = leader.get('life_expectancy', 60)
    traits = leader.get('traits', [])

    changes = []

    # Age milestones
    age_percent = (age / life_exp) * 100

    # Young leader (< 40% of life expectancy) - no changes

    # Middle age (40-70% of life expectancy) - gain Experienced
    if 40 <= age_percent < 70 and 'Experienced' not in traits and 'Ancient' not in traits:
        traits.append('Experienced')
        changes.append("gained 'Experienced' trait")

    # Old age (70-90% of life expectancy) - no new traits, just slower

    # Ancient age (> 90% of life expectancy) - gain Ancient, lose some traits
    if age_percent > 90 and 'Ancient' not in traits:
        # Remove Experienced if present
        if 'Experienced' in traits:
            traits.remove('Experienced')

        # Remove physically demanding traits
        physical_traits = ['Warrior', 'Brave']
        for trait in physical_traits:
            if trait in traits:
                traits.remove(trait)
                changes.append(f"lost '{trait}' trait (too old)")

        # Add Ancient
        traits.append('Ancient')
        changes.append("gained 'Ancient' trait")

    # Update traits
    leader['traits'] = traits[:5]  # Max 5 traits

    return changes

def calculate_leader_effectiveness(leader, game_state=None):
    """
    Calculate overall leader effectiveness with crisis momentum penalty.
    This is a wrapper that applies crisis penalties if game_state is provided.
    """
    # Calculate base effectiveness using age and traits
    age = leader.get('age', 0)
    life_exp = leader.get('life_expectancy', 60)
    traits = leader.get('traits', [])

    # Base effectiveness: 1.0
    effectiveness = 1.0

    # BALANCE_OVERHAUL: Aggressive age-based decline with event triggers
    age_percent = (age / life_exp) * 100
    if age_percent < 30:
        # Youth: inexperienced
        effectiveness *= 0.90
    elif 30 <= age_percent < 60:
        # Prime: peak performance
        effectiveness *= 1.10
    elif 60 <= age_percent < 80:
        # Aging: slight decline
        effectiveness *= 1.05
        # 10% chance of health concern events (implement in event_engine.py)
    elif 80 <= age_percent < 90:
        # Elderly: noticeable decline
        effectiveness *= 0.95
        # 25% chance of "Questioning Authority" events
    elif 90 <= age_percent < 100:
        # Ancient: severe decline
        effectiveness *= 0.80
        # 40% chance of succession crisis events
    else:
        # Death's door: imminent death
        effectiveness *= 0.70
        # 50% chance of sudden death each turn

    # Trait bonuses
    if 'Wise' in traits or 'Scholar' in traits:
        effectiveness *= 1.05
    if 'Charismatic' in traits:
        effectiveness *= 1.05
    if 'Ancient' in traits:
        effectiveness *= 0.9  # Health penalty

    # BALANCE_OVERHAUL: Apply crisis momentum penalty if game_state provided
    if game_state and hasattr(game_state, 'crisis_momentum') and game_state.crisis_momentum > 0:
        momentum_penalty = min(0.20, game_state.crisis_momentum * 0.02)  # Max -20%
        effectiveness *= (1.0 - momentum_penalty)

    return max(0.5, min(1.5, effectiveness))  # Clamp between 0.5 and 1.5

def generate_successor_candidates(game_state):
    """
    Generate 3 potential successors with different trait combinations.
    Player will choose during succession event.
    """
    import random

    current_leader = game_state.civilization['leader']
    civ_name = game_state.civilization['meta']['name']

    # Get civilization's dominant characteristics for successor generation
    cultural_values = game_state.culture.get('values', [])[:3]

    candidates = []

    # Candidate archetypes
    archetypes = [
        {
            'type': 'Military',
            'traits': ['Warrior', 'Brave', 'Tactical'],
            'age_range': (25, 40),
            'description': 'A proven military leader'
        },
        {
            'type': 'Diplomatic',
            'traits': ['Charismatic', 'Diplomatic', 'Just'],
            'age_range': (30, 50),
            'description': 'A skilled negotiator and peacemaker'
        },
        {
            'type': 'Spiritual',
            'traits': ['Pious', 'Visionary', 'Mystic'],
            'age_range': (28, 45),
            'description': 'A devout religious leader'
        },
        {
            'type': 'Scholar',
            'traits': ['Scholar', 'Wise', 'Cunning'],
            'age_range': (32, 48),
            'description': 'A brilliant mind and strategist'
        },
        {
            'type': 'Merchant',
            'traits': ['Mercantile', 'Prosperous', 'Charismatic'],
            'age_range': (30, 45),
            'description': 'A wealthy trader and economist'
        }
    ]

    # Select 3 random archetypes
    selected = random.sample(archetypes, 3)

    # Name pools (simple for now)
    name_pool = [
        'Aldric', 'Beatrix', 'Cedric', 'Diana', 'Elara', 'Finn', 'Gaia', 'Hector',
        'Iris', 'Jareth', 'Kira', 'Lorian', 'Maya', 'Nero', 'Orin', 'Petra',
        'Quinn', 'Raven', 'Silas', 'Thora', 'Uma', 'Victor', 'Wren', 'Xander',
        'Yara', 'Zephyr', 'Aria', 'Bram', 'Cora', 'Dax'
    ]

    for archetype in selected:
        # Generate random name
        name = random.choice([n for n in name_pool if n != current_leader.get('name')])

        # Random age in range
        age = random.randint(*archetype['age_range'])

        # Select 2-3 traits from archetype
        trait_count = random.randint(2, 3)
        traits = random.sample(archetype['traits'], trait_count)

        candidates.append({
            'name': name,
            'age': age,
            'type': archetype['type'],
            'traits': traits,
            'description': archetype['description']
        })

    return candidates

def trigger_succession_crisis(game_state):
    """
    BALANCE_OVERHAUL: Generate high-stakes succession event with faction-backed candidates.
    This is a political crisis, not a menu choice.
    """
    import random

    print("=" * 60)
    print("SUCCESSION CRISIS: THE THRONE LIES EMPTY")
    print("=" * 60)

    # Generate 3-5 candidates backed by different factions
    candidates = []

    # Get factions to back candidates
    factions = game_state.faction_manager.get_all() if hasattr(game_state, 'faction_manager') else []

    # Candidate 1: Merchant-backed (economic focus)
    merchant_faction = next((f for f in factions if 'merchant' in f.get('id', '').lower()), None)
    candidates.append({
        'name': random.choice(['Aldric the Wealthy', 'Beatrix the Prosperous', 'Cedric the Trader']),
        'archetype': 'Merchant',
        'traits': ['Mercantile', 'Charismatic'],
        'backing_faction': merchant_faction.get('name') if merchant_faction else 'Merchant Guild',
        'backing_faction_id': merchant_faction.get('id') if merchant_faction else 'merchants',
        'approval_changes': {
            'merchant': +30,
            'warrior': -35,
            'priest': -20
        },
        'demands': 'Reduce tariffs and expand trade routes within 5 turns'
    })

    # Candidate 2: Warrior-backed (military focus)
    warrior_faction = next((f for f in factions if 'warrior' in f.get('id', '').lower() or 'military' in f.get('id', '').lower()), None)
    candidates.append({
        'name': random.choice(['Diana the Bold', 'Hector the Conqueror', 'Thora the Fierce']),
        'archetype': 'Warrior',
        'traits': ['Warrior', 'Brave'],
        'backing_faction': warrior_faction.get('name') if warrior_faction else 'Warrior Caste',
        'backing_faction_id': warrior_faction.get('id') if warrior_faction else 'warriors',
        'approval_changes': {
            'merchant': -40,
            'warrior': +35,
            'priest': -15
        },
        'demands': 'Increase military funding by 30% within 5 turns'
    })

    # Candidate 3: Priest-backed (spiritual focus)
    priest_faction = next((f for f in factions if 'priest' in f.get('id', '').lower() or 'religious' in f.get('id', '').lower()), None)
    candidates.append({
        'name': random.choice(['Elara the Devout', 'Silas the Blessed', 'Maya the Prophet']),
        'archetype': 'Priest',
        'traits': ['Pious', 'Visionary'],
        'backing_faction': priest_faction.get('name') if priest_faction else 'Priest Order',
        'backing_faction_id': priest_faction.get('id') if priest_faction else 'priests',
        'approval_changes': {
            'merchant': -25,
            'warrior': -20,
            'priest': +30
        },
        'demands': 'Fund temple construction and religious festivals within 5 turns'
    })

    # Candidate 4: People's candidate (if happiness low)
    if game_state.population_happiness < 50:
        candidates.append({
            'name': random.choice(['Finn the Common', 'Kira the Voice', 'Orin the Just']),
            'archetype': 'Populist',
            'traits': ['Just', 'Charismatic'],
            'backing_faction': 'The Common People',
            'backing_faction_id': 'people',
            'approval_changes': {
                'merchant': -30,
                'warrior': -30,
                'priest': -30
            },
            'demands': 'Increase happiness by 20 points within 5 turns or face riots',
            'special': 'happiness_boost'  # +20 happiness immediately if chosen
        })

    return {
        'event_type': 'succession_crisis',
        'candidates': candidates,
        'transition_crisis_duration': 10,  # 10 turns of instability
        'rival_claimant_chance': 0.40  # 40% chance of coup attempt from losing faction
    }

def apply_legacy_bonus(game_state, previous_leader):
    """
    Apply legacy bonuses from previous leader to civilization.
    Well-ruled civilizations carry forward benefits.
    """
    years_ruled = previous_leader.get('years_ruled', 0)
    traits = previous_leader.get('traits', [])

    legacy = {
        'bonuses_applied': [],
        'narrative': ''
    }

    # Long reign bonus
    if years_ruled > 50:
        bonus_rep = min(years_ruled // 10, 20)  # Max +20
        for rep_type in ['diplomatic', 'military', 'religious', 'economic']:
            current = game_state.civilization.get('consequences', {}).get('reputation', {}).get(rep_type, 50)
            game_state.civilization['consequences']['reputation'][rep_type] = min(100, current + bonus_rep)

        legacy['bonuses_applied'].append(f"+{bonus_rep} to all reputations (long reign)")
        legacy['narrative'] = f"The long and stable {years_ruled}-year reign leaves a lasting positive legacy."

    # Trait-specific legacies
    if 'Wise' in traits or 'Scholar' in traits:
        # Technology boost
        legacy['bonuses_applied'].append("Cultural wisdom preserved")
        legacy['narrative'] += " The leader's wisdom is preserved in the teachings of the next generation."

    if 'Warrior' in traits or 'Brave' in traits:
        # Military tradition
        legacy['bonuses_applied'].append("Military tradition strengthened")
        legacy['narrative'] += " A martial legacy inspires future warriors."

    if 'Pious' in traits or 'Visionary' in traits:
        # Religious influence
        legacy['bonuses_applied'].append("Spiritual foundation deepened")
        legacy['narrative'] += " The leader's faith becomes a cornerstone of society."

    return legacy

