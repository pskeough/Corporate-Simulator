# engines/crisis_engine.py
"""
Crisis Event Engine for Corporate Decision Simulator

Triggers high-stakes corporate crisis events based on the company's financial
health, employee morale, and other critical business metrics.
"""

import google.generativeai as genai
import json
from model_config import TEXT_MODEL
from engines.prompt_loader import load_prompt

def detect_crisis(game_state):
    """
    Detects if the corporation is in a crisis state based on key metrics.

    Returns:
        str: The type of crisis detected, or None if conditions are stable.
    """
    if not hasattr(game_state, 'crisis_momentum'):
        game_state.crisis_momentum = 0
    if not hasattr(game_state, 'crisis_recovery_timer'):
        game_state.crisis_recovery_timer = 0

    budget = game_state.corporation.get('budget', 0)
    headcount = game_state.corporation.get('headcount', 1)
    morale = game_state.company_morale

    crisis_type = None

    # Priority 1: Catastrophic Financial Failure
    if budget <= 0:
        crisis_type = 'BankruptcyWarning'
    # Priority 2: Severe Budget Shortfall
    elif budget < (headcount * 1000): # Threshold for severe strain
        crisis_type = 'BudgetFreeze'
    # Priority 3: Company-wide Morale Collapse
    elif morale < 20:
        crisis_type = 'MassResignationRisk'
    # Priority 4: Market Disruption
    elif "Disruptive new technology" in game_state.market_and_competitors.get('market_landscape', {}).get('risks', []):
         crisis_type = 'MarketDisruption'

    if crisis_type:
        game_state.crisis_momentum += 1
        game_state.crisis_recovery_timer = 0
        return crisis_type

    # If no primary crisis, check for cascading issues
    active_crises = []
    if budget < (headcount * 5000): # Less severe budget warning
        active_crises.append('financial_strain')
    if morale < 40:
        active_crises.append('low_morale')

    if len(active_crises) >= 2:
        import random
        if random.random() < 0.33: # 33% chance of a compound crisis
            game_state.crisis_momentum += 1
            return 'CompoundCrisis' # e.g., Low morale AND financial problems

    # If no crisis, manage recovery timer
    if game_state.crisis_recovery_timer < 5:
        game_state.crisis_recovery_timer += 1
    else:
        game_state.crisis_momentum = 0 # Fully recovered after 5 stable turns

    return None

def generate_crisis_event(game_state, crisis_type):
    """
    Generates a targeted corporate crisis event with high stakes.
    """
    print(f"--- Generating CRISIS event: {crisis_type} ---")
    model = genai.GenerativeModel(TEXT_MODEL)

    # Context for the AI prompt
    corporation_name = game_state.corporation.get('name')
    player_name = game_state.player.get('name')
    player_title = game_state.player.get('title')
    headcount = game_state.corporation.get('headcount')
    budget = game_state.corporation.get('budget')

    # Load the appropriate prompt template for the crisis
    prompt_template = load_prompt(f'crises/{crisis_type}')

    prompt = prompt_template.format(
        corporation_name=corporation_name,
        player_name=player_name,
        player_title=player_title,
        headcount=headcount,
        budget=f"${budget:,.2f}"
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

        crisis_label = crisis_type.replace('_', ' ').title()
        if 'title' in event_data:
            event_data['title'] += f" -- Crisis: {crisis_label}"

        print(f"--- Crisis event '{event_data.get('title', 'Unknown')}' generated ---")
        return event_data
    except Exception as e:
        print(f"Error generating crisis event: {e}")
        # Return a generic fallback crisis if the AI fails
        return {
            "title": f"A Major Business Crisis Looms",
            "narrative": "The company is facing a severe and unexpected challenge that threatens its stability. Tough decisions must be made immediately.",
            "investigation_options": ["Review the latest financial reports.", "Call an emergency meeting with department heads."],
            "decision_options": ["Implement immediate, drastic cost-cutting measures.", "Seek external consulting at a high cost to find a solution."],
            "is_crisis": True,
            "crisis_type": crisis_type
        }

def should_generate_crisis(game_state):
    """
    Determines if the next event should be a crisis, based on detected conditions.

    Returns:
        tuple: (bool, str or None) - Whether to generate a crisis and the crisis type.
    """
    crisis_type = detect_crisis(game_state)

    if crisis_type:
        import random
        # Catastrophic crises are almost certain to trigger
        if crisis_type in ['BankruptcyWarning', 'MassResignationRisk']:
            return random.random() < 0.95, crisis_type # 95% chance
        # Severe crises are very likely
        elif crisis_type in ['BudgetFreeze', 'CompoundCrisis']:
            return random.random() < 0.85, crisis_type # 85% chance
        # Warnings are less likely but still significant
        else:
            return random.random() < 0.60, crisis_type # 60% chance

    return False, None
