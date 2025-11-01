# engines/crisis_engine.py
"""
Crisis event generation based on resource states and civilization conditions.
Triggers special events when civilization is in danger.
"""

import google.generativeai as genai
import json
from model_config import TEXT_MODEL
from engines.prompt_loader import load_prompt

def detect_crisis(game_state):
    """
    Detect if civilization is in a crisis state.
    Returns crisis type or None.
    """
    # BALANCE_OVERHAUL: Initialize crisis momentum tracking if not present
    if not hasattr(game_state, 'crisis_momentum'):
        game_state.crisis_momentum = 0
    if not hasattr(game_state, 'crisis_recovery_timer'):
        game_state.crisis_recovery_timer = 0

    population = game_state.civilization['population']
    food = game_state.civilization['resources']['food']
    wealth = game_state.civilization['resources']['wealth']

    # Calculate food per capita
    food_per_capita = food / max(population, 1)

    # BALANCE_OVERHAUL: Tightened crisis thresholds with earlier warnings
    # Crisis priority (most severe first)
    crisis_type = None

    if food <= 0 or food_per_capita < 0.5:
        crisis_type = 'famine'  # Catastrophic - severe malnutrition
    elif wealth <= 0:
        crisis_type = 'economic_collapse'
    elif food_per_capita < 0.8:
        crisis_type = 'severe_food_shortage'  # Active crisis tier
    elif food_per_capita < 1.8:
        crisis_type = 'food_shortage'  # Warning tier (increased from 1.0)
    elif wealth < 100:
        crisis_type = 'economic_crisis'
    elif wealth < 300:
        crisis_type = 'economic_warning'  # New warning tier

    # Check leader age crisis
    leader = game_state.civilization.get('leader', {})
    if leader.get('age', 0) > leader.get('life_expectancy', 60) + 10:
        crisis_type = 'succession_crisis'

    # If a crisis was detected by thresholds, track momentum and return it
    if crisis_type:
        game_state.crisis_momentum += 1
        game_state.crisis_recovery_timer = 0
        return crisis_type

    # BALANCE_OVERHAUL: CRISIS CASCADING - Multiple crises increase probability of others
    active_crises = []

    # Detect all active crisis conditions
    if food_per_capita < 1.8:
        active_crises.append('food_crisis')
    if wealth < 300:
        active_crises.append('economic_crisis')
    if game_state.population_happiness < 40:
        active_crises.append('happiness_crisis')

    # Cascade logic: if multiple crises, increase severity
    if len(active_crises) >= 2:
        import random

        # Food crisis increases economic crisis chance
        if 'food_crisis' in active_crises and wealth < 500:
            if random.random() < 0.40:  # 40% cascade chance
                return 'economic_crisis'

        # Economic crisis increases food shortage chance
        if 'economic_crisis' in active_crises and food_per_capita < 2.0:
            if random.random() < 0.30:  # 30% cascade chance
                return 'food_shortage'

        # Multiple crises trigger faction betrayal checks
        if len(active_crises) >= 2:
            if random.random() < 0.25:  # 25% compound crisis
                game_state.crisis_momentum += 1
                game_state.crisis_recovery_timer = 0
                return 'compound_crisis'  # New crisis type - multi-system failure

    # BALANCE_OVERHAUL: No crisis - decrement recovery timer
    if game_state.crisis_recovery_timer < 5:
        game_state.crisis_recovery_timer += 1
    else:
        # Full recovery after 5 turns without crisis
        game_state.crisis_momentum = 0

    return None

def generate_crisis_event(game_state, crisis_type):
    """
    Generate a targeted crisis event with high stakes.
    These events demand immediate attention and have severe consequences.
    """
    print(f"--- Generating CRISIS event: {crisis_type} ---")

    # Special handling for succession crisis - use the new high-stakes system
    if crisis_type == 'succession_crisis':
        from engines.leader_engine import trigger_succession_crisis
        succession_data = trigger_succession_crisis(game_state)
        # Convert succession data to event format
        candidates_text = "\n".join([
            f"- **{c['name']}** ({c['archetype']}): Backed by {c['backing_faction']}. Traits: {', '.join(c['traits'])}. Demands: {c['demands']}"
            for c in succession_data['candidates']
        ])
        return {
            "title": "The Throne Lies Empty: A Succession Crisis -- Crisis: Succession",
            "narrative": f"The ancient {game_state.civilization['leader']['name']} has passed beyond mortal years. "
                        f"The throne stands empty, and powerful factions circle with their own candidates. "
                        f"This is not a simple choice of successor - this is a political crisis that will reshape your civilization.\n\n"
                        f"**Candidates:**\n{candidates_text}",
            "investigation_options": [
                "Assess each faction's strength and their candidate's true capabilities",
                "Investigate what concessions each faction might demand if their candidate is chosen"
            ],
            "decision_options": [
                "Choose a successor (opens succession selection)",
                "Delay the decision and let factions struggle (increases instability)"
            ],
            "is_crisis": True,
            "crisis_type": crisis_type,
            "succession_data": succession_data
        }

    model = genai.GenerativeModel(TEXT_MODEL)

    # Build context
    civ_name = game_state.civilization['meta']['name']
    leader_name = game_state.civilization['leader']['name']
    population = game_state.civilization['population']
    food = game_state.civilization['resources']['food']
    wealth = game_state.civilization['resources']['wealth']
    era = game_state.civilization['meta']['era']

    # Calculate severity context
    food_per_capita = food / max(population, 1)
    days_of_food = int(food_per_capita * 30) if food > 0 else 0

    # Load crisis prompt templates (cached after first load)
    crisis_prompts = {
        'famine': load_prompt('crises/famine'),
        'food_shortage': load_prompt('crises/food_shortage'),
        'severe_food_shortage': load_prompt('crises/severe_food_shortage'),
        'economic_collapse': load_prompt('crises/economic_collapse'),
        'economic_crisis': load_prompt('crises/economic_crisis'),
        'economic_warning': load_prompt('crises/economic_warning'),
        'succession_crisis': load_prompt('crises/succession_crisis'),
        'compound_crisis': load_prompt('crises/compound_crisis')
    }

    # Get the appropriate prompt template
    prompt_template = crisis_prompts.get(crisis_type, crisis_prompts['famine'])

    # Format the prompt with variable substitution
    # For succession_crisis, we need leader-specific variables
    if crisis_type == 'succession_crisis':
        prompt = prompt_template.format(
            civ_name=civ_name,
            leader_name=leader_name,
            leader_age=game_state.civilization['leader']['age'],
            leader_life_expectancy=game_state.civilization['leader']['life_expectancy'],
            leader_years_ruled=game_state.civilization['leader'].get('years_ruled', 0),
            era=era
        )
    elif crisis_type == 'compound_crisis':
        prompt = prompt_template.format(
            civ_name=civ_name,
            leader_name=leader_name,
            population=population,
            food=food,
            wealth=wealth,
            happiness=game_state.population_happiness
        )
    elif crisis_type in ['economic_collapse', 'economic_crisis', 'economic_warning']:
        # Economic crises don't need population/food variables
        prompt = prompt_template.format(
            civ_name=civ_name,
            leader_name=leader_name,
            wealth=wealth,
            era=era
        )
    else:
        # Food-related crises need all standard variables
        prompt = prompt_template.format(
            civ_name=civ_name,
            leader_name=leader_name,
            population=population,
            food=food,
            days_of_food=days_of_food,
            era=era
        )

    try:
        response = model.generate_content(
            prompt,
            generation_config={
                "response_mime_type": "application/json",
                "temperature": 0.8
            }
        )
        event_data = json.loads(response.text)
        event_data['is_crisis'] = True
        event_data['crisis_type'] = crisis_type

        # Add event type to title
        crisis_type_label = crisis_type.replace('_', ' ').title()
        if 'title' in event_data:
            event_data['title'] = event_data['title'] + f" -- Crisis: {crisis_type_label}"

        print(f"--- Crisis event '{event_data.get('title', 'Unknown')}' generated ---")
        return event_data

    except Exception as e:
        print(f"Error generating crisis event: {e}")
        # Return emergency fallback
        crisis_type_label = crisis_type.replace('_', ' ').title()
        return {
            "title": f"A Dire Situation -- Crisis: {crisis_type_label}",
            "narrative": "Your civilization faces a grave crisis. Immediate action is required.",
            "investigation_options": ["Assess the situation", "Consult advisors"],
            "decision_options": ["Take emergency action", "Attempt desperate measures"],
            "is_crisis": True,
            "crisis_type": crisis_type
        }

def should_generate_crisis(game_state):
    """
    Determine if next event should be a crisis event.
    Returns (bool, crisis_type or None)
    """
    crisis_type = detect_crisis(game_state)

    if crisis_type:
        # Crisis events have high priority
        # Catastrophic crises trigger 100%
        if crisis_type in ['famine', 'economic_collapse', 'succession_crisis', 'compound_crisis']:
            return True, crisis_type
        # Active crisis tier: high trigger rates
        # Severe food shortage: 90% chance (active suffering)
        elif crisis_type == 'severe_food_shortage':
            import random
            return random.random() < 0.90, crisis_type
        # Warning tier: increased trigger rates to enforce new balance
        # Food shortage: 85% chance, Economic crisis: 80% chance
        elif crisis_type == 'food_shortage':
            import random
            return random.random() < 0.85, crisis_type
        elif crisis_type == 'economic_crisis':
            import random
            return random.random() < 0.80, crisis_type
        # Early warning tier: lower but significant rates
        # Economic warning: 75% chance (early warning)
        elif crisis_type == 'economic_warning':
            import random
            return random.random() < 0.75, crisis_type

    return False, None

