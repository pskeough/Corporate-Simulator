# engines/callback_engine.py
"""
Generates callback events based on past player decisions and consequences.
Makes the world feel alive and reactive.
"""

import google.generativeai as genai
import json
from model_config import TEXT_MODEL
from engines.prompt_loader import load_prompt

def generate_callback_event(game_state, callback_type, callback_data):
    """
    Generate an event that references past player decisions.
    """
    print(f"--- Generating CALLBACK event: {callback_type} ---")
    model = genai.GenerativeModel(TEXT_MODEL)

    civ_name = game_state.civilization['meta']['name']
    leader_name = game_state.civilization['leader']['name']
    era = game_state.civilization['meta']['era']

    # Calculate time passed for narrative context
    current_year = game_state.civilization['meta']['year']
    event_year = callback_data.get('year', current_year - 10)
    years_passed = current_year - event_year

    # Load callback prompt templates (cached after first load)
    callback_prompts = {
        'broken_promise': load_prompt('callbacks/broken_promise'),
        'enemy_revenge': load_prompt('callbacks/enemy_revenge'),
        'ally_request': load_prompt('callbacks/ally_request'),
        'debt_collection': load_prompt('callbacks/debt_collection')
    }

    # Select the appropriate template
    template = callback_prompts.get(callback_type, callback_prompts['broken_promise'])

    # Build format kwargs based on callback type
    format_kwargs = {
        'civ_name': civ_name,
        'leader_name': leader_name,
        'era': era,
        'years_passed': years_passed
    }

    if callback_type == 'broken_promise':
        format_kwargs['promise_text'] = callback_data.get('text', 'Unknown promise')
        format_kwargs['promise_event'] = callback_data.get('event', 'Unknown event')
    elif callback_type == 'enemy_revenge':
        hostility = callback_data.get('hostility', 50)
        format_kwargs['enemy_name'] = callback_data.get('name', 'Unknown Enemy')
        format_kwargs['hostility_level'] = hostility
        format_kwargs['hostility_description'] = (
            'seething with rage' if hostility > 75 else
            'deeply hostile' if hostility > 50 else
            'harboring grudges'
        )
        format_kwargs['enemy_event'] = callback_data.get('event', 'Unknown conflict')
    elif callback_type == 'ally_request':
        strength = callback_data.get('strength', 50)
        format_kwargs['ally_name'] = callback_data.get('name', 'Unknown Ally')
        format_kwargs['alliance_strength'] = strength
        format_kwargs['alliance_description'] = (
            'unbreakable bond' if strength > 75 else
            'strong friendship' if strength > 50 else
            'tentative alliance'
        )
        format_kwargs['ally_event'] = callback_data.get('event', 'Unknown alliance')
    elif callback_type == 'debt_collection':
        format_kwargs['debt_description'] = callback_data.get('description', 'Unknown debt')
        format_kwargs['debt_event'] = callback_data.get('event', 'Unknown event')

    prompt = template.format(**format_kwargs)

    try:
        response = model.generate_content(
            prompt,
            generation_config={
                "response_mime_type": "application/json",
                "temperature": 0.8
            }
        )
        event_data = json.loads(response.text)
        event_data['is_callback'] = True
        event_data['callback_type'] = callback_type
        event_data['callback_data'] = callback_data

        # Add event type to title
        callback_type_label = callback_type.replace('_', ' ').title()
        if 'title' in event_data:
            event_data['title'] = event_data['title'] + f" -- Callback: {callback_type_label}"

        print(f"--- Callback event '{event_data.get('title', 'Unknown')}' generated ---")
        return event_data

    except Exception as e:
        print(f"Error generating callback event: {e}")
        callback_type_label = callback_type.replace('_', ' ').title()
        return {
            "title": f"The Past Returns -- Callback: {callback_type_label}",
            "narrative": "Your past decisions have caught up with you. Someone has returned seeking resolution.",
            "investigation_options": ["Learn what they want", "Assess the situation"],
            "decision_options": ["Face the consequences", "Try to negotiate"],
            "is_callback": True,
            "callback_type": callback_type
        }

