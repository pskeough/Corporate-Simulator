# engines/resource_engine.py
"""
Resource management and consumption mechanics.
Handles food/wealth depletion, crisis detection, and resource constraints.
"""

def calculate_consumption(game_state):
    """
    Calculate per-turn resource consumption based on population and infrastructure.

    BALANCE CHANGES (2025-01):
    - Increased base food consumption from pop/10 to pop/4 (2.5x increase)
    - Restored harsh stone age inefficiency (1.3x -> 2.0x)
    - Added infrastructure scaling to food consumption (+0.5% per building)

    Returns dict with consumption rates.
    """
    population = game_state.civilization.get('population', 0)
    era = game_state.civilization.get('meta', {}).get('era', 'stone_age')

    # Base food consumption: 1 food per 4 people (was 1 per 10)
    base_food_consumption = population // 4  # CHANGED: 2.5x increase

    # Era affects efficiency (better eras consume less per capita due to tech)
    # Stone age is harsh subsistence living, players should want to advance
    era_efficiency = {
        'stone_age': 2.0,      # CHANGED: Restored harsh inefficiency (was 1.8)
        'bronze_age': 1.7,     # CHANGED: Still inefficient (was 1.5)
        'iron_age': 1.4,       # CHANGED: Improving (was 1.3)
        'classical': 1.2,      # CHANGED: Getting better (was 1.1)
        'medieval': 1.0,       # CHANGED: Efficient (was 1.0)
        'renaissance': 0.9,    # CHANGED: Advanced techniques (was 0.9)
        'industrial': 0.8,     # CHANGED: Mechanization (was 0.8)
        'modern': 0.7         # CHANGED: High-tech (was 0.7)
    }

    efficiency_multiplier = era_efficiency.get(era, 1.0)

    # Infrastructure scaling: more buildings = larger urban population = more consumption
    infrastructure_count = len(game_state.technology.get('infrastructure', []))
    infrastructure_scaling = 1 + (infrastructure_count * 0.005)  # +0.5% per building

    food_consumption = int(base_food_consumption * efficiency_multiplier * infrastructure_scaling)

    # Wealth consumption from infrastructure maintenance
    # BALANCE CHANGE: Different buildings have different costs (Fix #7)
    from engines.bonus_definitions import BUILDING_BONUSES

    total_base_maintenance = 0
    infrastructure_count = 0

    # Calculate maintenance from modern building system
    if hasattr(game_state, 'buildings'):
        constructed = game_state.buildings.get('constructed_buildings', [])
        infrastructure_count += len(constructed)

        for building in constructed:
            building_id = building.get('id')
            building_def = BUILDING_BONUSES.get(building_id, {})
            total_base_maintenance += building_def.get('maintenance_cost', 10)

    # Legacy infrastructure support (backward compatibility)
    legacy_infrastructure = game_state.technology.get('infrastructure', [])
    infrastructure_count += len(legacy_infrastructure)
    for building_name in legacy_infrastructure:
        building_def = BUILDING_BONUSES.get(building_name, {})
        total_base_maintenance += building_def.get('maintenance_cost', 10)

    if infrastructure_count == 0:
        wealth_consumption = 0
    else:
        # Apply exponential scaling (Fix #3)
        scaling_factor = 1 + (infrastructure_count * 0.05)  # +5% per building
        wealth_consumption = int(total_base_maintenance * scaling_factor)

    return {
        'food': food_consumption,
        'wealth': wealth_consumption
    }

def apply_consumption(game_state):
    """
    Apply resource consumption and return status.
    Returns dict with consumption details and warnings.
    """
    consumption = calculate_consumption(game_state)

    current_food = game_state.civilization['resources']['food']
    current_wealth = game_state.civilization['resources']['wealth']

    # Apply consumption
    new_food = current_food - consumption['food']
    new_wealth = current_wealth - consumption['wealth']

    game_state.civilization['resources']['food'] = max(0, new_food)
    game_state.civilization['resources']['wealth'] = max(0, new_wealth)

    # Detect crisis conditions
    status = {
        'food_consumed': consumption['food'],
        'wealth_consumed': consumption['wealth'],
        'food_remaining': game_state.civilization['resources']['food'],
        'wealth_remaining': game_state.civilization['resources']['wealth'],
        'warnings': []
    }

    # Food crisis levels
    population = game_state.civilization['population']
    food_per_capita = game_state.civilization['resources']['food'] / max(population, 1)

    if new_food < 0:
        status['warnings'].append('FAMINE_CRITICAL')
        # Starvation causes population loss
        starvation_deaths = abs(new_food) * 5  # 5 deaths per missing food unit
        game_state.civilization['population'] = max(50, population - starvation_deaths)
        status['starvation_deaths'] = starvation_deaths
    elif food_per_capita < 0.5:
        status['warnings'].append('FAMINE_WARNING')
    elif food_per_capita < 1.0:
        status['warnings'].append('FOOD_LOW')

    # Wealth crisis
    if new_wealth < 0:
        status['warnings'].append('BANKRUPTCY')
        # Bankruptcy causes infrastructure decay
        decay_count = min(len(game_state.technology.get('infrastructure', [])), 2)
        if decay_count > 0:
            decayed = game_state.technology['infrastructure'][-decay_count:]
            game_state.technology['infrastructure'] = game_state.technology['infrastructure'][:-decay_count]
            status['infrastructure_lost'] = decayed
    elif new_wealth < 100:
        status['warnings'].append('WEALTH_LOW')

    # BALANCE_OVERHAUL: Food stockpile decay (spoilage, pests, waste)
    # Prevents infinite stockpile turtling and encourages active resource management
    current_food = game_state.civilization['resources']['food']
    if current_food > 0:
        if current_food > 500:
            # Excessive stockpile decays faster (10% per turn)
            decay_amount = int(current_food * 0.10)
            game_state.civilization['resources']['food'] = max(0, current_food - decay_amount)
            status['food_decay'] = decay_amount
        else:
            # Normal decay (5% per turn)
            decay_amount = int(current_food * 0.05)
            game_state.civilization['resources']['food'] = max(0, current_food - decay_amount)
            status['food_decay'] = decay_amount

    return status

def calculate_resource_happiness_impact(game_state):
    """
    Calculate happiness change based on resource scarcity.

    Low food/wealth automatically reduces happiness, creating feedback loop:
    Scarcity → Unhappiness → Lower productivity (Fix #2) → Worse scarcity

    This is applied automatically each turn after consumption.

    Returns: happiness delta (positive or negative integer)
    """
    happiness_change = 0
    population = game_state.civilization.get('population', 0)
    food = game_state.civilization['resources']['food']
    wealth = game_state.civilization['resources']['wealth']

    # Food scarcity penalties (scaled by severity)
    food_per_capita = food / max(population, 1)
    if food_per_capita < 0.3:
        happiness_change -= 20  # Starvation: massive penalty
    elif food_per_capita < 0.6:
        happiness_change -= 10  # Hunger: major penalty
    elif food_per_capita < 1.0:
        happiness_change -= 5   # Food insecurity: minor penalty

    # Wealth scarcity penalties (can't pay workers, maintain services)
    if wealth < 50:
        happiness_change -= 15  # Bankrupt: major penalty
    elif wealth < 200:
        happiness_change -= 8   # Poor: moderate penalty
    elif wealth < 500:
        happiness_change -= 3   # Tight: minor penalty

    # Abundance bonuses (prosperity breeds contentment)
    if food_per_capita > 5.0 and wealth > 2000:
        happiness_change += 5   # Prosperous: bonus

    return happiness_change

def check_resource_constraints(game_state, required_resources):
    """
    Check if civilization has required resources for an action.

    Args:
        game_state: Current game state
        required_resources: dict like {'food': 500, 'wealth': 200}

    Returns:
        (bool, list): (can_afford, list_of_missing_resources)
    """
    missing = []

    for resource, amount in required_resources.items():
        current = game_state.civilization['resources'].get(resource, 0)
        if current < amount:
            missing.append(f"{resource} (need {amount}, have {current})")

    return len(missing) == 0, missing

def generate_resource_production(game_state):
    """
    Calculate passive resource generation based on civ state.
    This represents natural growth between events.
    """
    population = game_state.civilization['population']
    era = game_state.civilization.get('meta', {}).get('era', 'stone_age')

    # Food production from population (farmers)
    # Stone age is subsistence society - higher farmer percentage
    farmer_percentage = {
        'stone_age': 0.45,      # 45% farmers (subsistence)
        'bronze_age': 0.40,     # 40% farmers
        'iron_age': 0.35,       # 35% farmers
        'classical': 0.30,      # 30% farmers
        'medieval': 0.30,
        'renaissance': 0.25,
        'industrial': 0.20,
        'modern': 0.15
    }
    farmers = int(population * farmer_percentage.get(era, 0.3))

    # Era affects productivity (rebalanced for stone age)
    era_productivity = {
        'stone_age': 1.5,       # Increased from 1 to 1.5 for survivability
        'bronze_age': 2,
        'iron_age': 3,
        'classical': 4,
        'medieval': 5,
        'renaissance': 7,
        'industrial': 10,
        'modern': 15
    }

    food_production = int(farmers * era_productivity.get(era, 1))

    # Wealth production from trade/economy (remaining population)
    trader_percentage = {
        'stone_age': 0.25,      # Increased from 0.20 for better wealth generation
        'bronze_age': 0.25,
        'iron_age': 0.30,
        'classical': 0.35,
        'medieval': 0.35,
        'renaissance': 0.40,
        'industrial': 0.45,
        'modern': 0.50
    }
    traders = int(population * trader_percentage.get(era, 0.2))
    wealth_production = traders * era_productivity.get(era, 1) // 2

    return {
        'food': food_production,
        'wealth': wealth_production
    }

def apply_passive_generation(game_state):
    """Apply passive resource generation with leader effectiveness bonus."""
    production = generate_resource_production(game_state)

    # Apply leader effectiveness multiplier
    from engines.leader_engine import calculate_leader_effectiveness

    effectiveness = calculate_leader_effectiveness(game_state.civilization.get('leader', {}))

    # BALANCE_OVERHAUL: Apply happiness productivity penalty
    # Low happiness mechanically hurts economy, not just narrative flavor
    # Updated thresholds and multipliers (2025-01 balance changes)
    happiness = game_state.population_happiness
    if happiness >= 80:
        happiness_multiplier = 1.15  # Thriving: +15% productivity
    elif happiness >= 60:
        happiness_multiplier = 1.0   # Content: normal productivity
    elif happiness >= 40:
        happiness_multiplier = 0.85  # Discontent: -15% productivity
    elif happiness >= 20:
        happiness_multiplier = 0.65  # Unrest: -35% productivity
    else:
        happiness_multiplier = 0.5   # Rebellion: -50% productivity

    effectiveness = effectiveness * happiness_multiplier

    # Apply bonus to production
    final_food = int(production['food'] * effectiveness)
    final_wealth = int(production['wealth'] * effectiveness)

    # BALANCE_OVERHAUL: Apply faction approval bonuses/penalties
    if hasattr(game_state, 'faction_manager'):
        faction_bonuses = game_state.faction_manager.get_faction_bonuses(game_state)
        final_wealth = int(final_wealth * faction_bonuses['wealth_multiplier'])

    # BONUS_ENGINE_INTEGRATION: Add bonuses from characters, buildings, etc.
    from engines.bonus_engine import BonusEngine
    from engines.bonus_definitions import BonusType

    bonus_engine = BonusEngine()
    food_bonuses = bonus_engine.calculate_bonuses(game_state, BonusType.FOOD_PER_TURN)
    wealth_bonuses = bonus_engine.calculate_bonuses(game_state, BonusType.WEALTH_PER_TURN)

    final_food += food_bonuses['total']
    final_wealth += wealth_bonuses['total']

    game_state.civilization['resources']['food'] += final_food
    game_state.civilization['resources']['wealth'] += final_wealth

    return {
        'food': final_food,
        'wealth': final_wealth,
        'base_food': production['food'],
        'base_wealth': production['wealth'],
        'effectiveness': effectiveness
    }
