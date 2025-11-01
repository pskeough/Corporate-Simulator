# engines/resource_engine.py
"""
Resource Engine for Corporate Decision Simulator

Handles the management of corporate resources, primarily budget and political capital.
This engine calculates and applies company overhead, revenue generation, and detects
financial crises like budget freezes or bankruptcy warnings.
"""

def calculate_overhead(game_state):
    """
    Calculates the per-turn overhead (consumption) of corporate resources.
    Overhead is driven by headcount (salaries) and corporate assets (maintenance).

    Returns:
        dict: A dictionary containing the calculated 'budget' and 'political_capital' overhead.
    """
    headcount = game_state.corporation.get('headcount', 0)
    maturity_stage = game_state.corporation.get('maturity_stage', 'startup')

    # Base budget overhead: Average cost per employee (salary, benefits, etc.)
    # This is a simplified model; a more complex version could have departmental salary differences.
    avg_cost_per_employee = 8000 # Example: $8,000 per employee per quarter
    base_budget_overhead = headcount * avg_cost_per_employee

    # Corporate maturity affects efficiency. Startups are lean, mature companies have more bloat.
    maturity_inefficiency = {
        'startup': 1.0,
        'growth_phase': 1.2,
        'mature': 1.5,
        'decline': 1.8
    }
    inefficiency_multiplier = maturity_inefficiency.get(maturity_stage, 1.2)

    # Asset maintenance: Internal tools, office space, etc., add to overhead.
    asset_count = len(game_state.skills_and_assets['corporation'].get('internal_tools', []))
    asset_scaling = 1 + (asset_count * 0.05) # Each internal tool increases overhead by 5%

    budget_overhead = int(base_budget_overhead * inefficiency_multiplier * asset_scaling)

    # Political capital doesn't have a direct overhead but could decay over time if not used.
    # For now, we model this as a small, flat decay to encourage its use.
    political_capital_decay = 5 # Lose 5 capital per turn from inaction

    return {
        'budget': budget_overhead,
        'political_capital': political_capital_decay
    }

def apply_overhead(game_state):
    """
    Applies the calculated overhead to the game state and returns a status report,
    including any warnings for financial distress.

    Returns:
        dict: A status dictionary with details of consumed resources and any warnings.
    """
    overhead = calculate_overhead(game_state)

    current_budget = game_state.corporation['budget']
    current_political_capital = game_state.player['political_capital']

    # Apply overhead
    new_budget = current_budget - overhead['budget']
    new_political_capital = current_political_capital - overhead['political_capital']

    game_state.corporation['budget'] = max(0, new_budget)
    game_state.player['political_capital'] = max(0, new_political_capital)

    status = {
        'budget_consumed': overhead['budget'],
        'political_capital_consumed': overhead['political_capital'],
        'budget_remaining': game_state.corporation['budget'],
        'political_capital_remaining': game_state.player['political_capital'],
        'warnings': []
    }

    # Financial crisis detection
    headcount = game_state.corporation['headcount']

    if new_budget < 0:
        status['warnings'].append('BUDGET_FREEZE')
        # A negative budget triggers layoffs to cut costs
        layoff_percentage = 0.10 # Lay off 10% of staff
        layoffs = int(headcount * layoff_percentage)
        game_state.corporation['headcount'] = max(10, headcount - layoffs)
        status['layoffs'] = layoffs
    elif game_state.corporation['budget'] < (headcount * 1000): # Less than $1k buffer per employee
        status['warnings'].append('BUDGET_WARNING')

    if new_political_capital < 50:
        status['warnings'].append('LOW_INFLUENCE')

    return status

def calculate_financial_morale_impact(game_state):
    """
    Calculates the impact on company-wide morale based on financial health.
    A healthy budget and strong growth boost morale, while financial trouble causes anxiety.

    Returns:
        int: The change in company morale (can be positive or negative).
    """
    morale_change = 0
    headcount = game_state.corporation.get('headcount', 1)
    budget = game_state.corporation['budget']

    budget_per_employee = budget / headcount

    if budget_per_employee < 500:
        morale_change -= 20  # Severe financial distress
    elif budget_per_employee < 2000:
        morale_change -= 10 # Financial uncertainty

    # Prosperity bonus
    if budget_per_employee > 20000:
        morale_change += 5

    return morale_change

def check_resource_constraints(game_state, required_resources):
    """
    Checks if the corporation and player have the required resources for a decision.

    Args:
        required_resources (dict): A dict like {'budget': 50000, 'political_capital': 100}.

    Returns:
        tuple: (can_afford, list_of_missing_resources)
    """
    missing = []

    if 'budget' in required_resources:
        if game_state.corporation['budget'] < required_resources['budget']:
            missing.append('budget')

    if 'political_capital' in required_resources:
        if game_state.player['political_capital'] < required_resources['political_capital']:
            missing.append('political_capital')

    return len(missing) == 0, missing

def generate_revenue_generation(game_state):
    """
    Calculates passive revenue (budget) and influence (political capital) generation.
    This represents the company's baseline performance between major events.
    """
    headcount = game_state.corporation['headcount']
    maturity_stage = game_state.corporation.get('maturity_stage', 'startup')

    # Revenue is generated by a percentage of the workforce
    revenue_generating_percentage = {
        'startup': 0.60, # Most people are in product/sales
        'growth_phase': 0.50,
        'mature': 0.40, # More overhead, less direct revenue generators
        'decline': 0.30
    }
    revenue_generators = int(headcount * revenue_generating_percentage.get(maturity_stage, 0.4))

    # Productivity varies by company maturity
    revenue_per_employee = {
        'startup': 12000,
        'growth_phase': 15000,
        'mature': 18000,
        'decline': 9000
    }

    budget_generation = int(revenue_generators * revenue_per_employee.get(maturity_stage, 15000))

    # Political capital is generated passively through networking and visibility
    political_capital_generation = 10 + (game_state.player.get('years_at_company', 0) // 2)

    return {
        'budget': budget_generation,
        'political_capital': political_capital_generation
    }

def apply_revenue_generation(game_state):
    """
    Applies passive resource generation, factoring in player effectiveness and morale.
    """
    production = generate_revenue_generation(game_state)

    from engines.player_engine import calculate_player_effectiveness
    effectiveness = calculate_player_effectiveness(game_state.player)

    # Company morale impacts productivity
    company_morale = game_state.company_morale
    if company_morale >= 80:
        morale_multiplier = 1.15  # High morale: +15% productivity
    elif company_morale >= 60:
        morale_multiplier = 1.0   # Normal
    else:
        morale_multiplier = 0.80  # Low morale: -20% productivity

    effectiveness *= morale_multiplier

    final_budget = int(production['budget'] * effectiveness)
    final_political_capital = int(production['political_capital'] * effectiveness)

    # Add department-based bonuses
    if hasattr(game_state, 'department_manager'):
        department_bonuses = game_state.department_manager.get_department_bonuses(game_state)
        final_budget = int(final_budget * department_bonuses['budget_multiplier'])

    # Integrate with the Bonus Engine for skill/asset-based bonuses
    from engines.bonus_engine import BonusEngine
    from engines.bonus_definitions import BonusType

    bonus_engine = BonusEngine()
    budget_bonuses = bonus_engine.calculate_bonuses(game_state, BonusType.BUDGET_PER_TURN)
    capital_bonuses = bonus_engine.calculate_bonuses(game_state, BonusType.POLITICAL_CAPITAL_PER_TURN)

    final_budget += budget_bonuses['total']
    final_political_capital += capital_bonuses['total']

    game_state.corporation['budget'] += final_budget
    game_state.player['political_capital'] += final_political_capital

    return {
        'budget': final_budget,
        'political_capital': final_political_capital
    }
