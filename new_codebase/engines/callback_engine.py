# engines/callback_engine.py
"""
Generates callback events based on past player decisions and their consequences
within the corporate simulation, creating a persistent and reactive world.
"""

import google.generativeai as genai
import json
from model_config import TEXT_MODEL
from engines.prompt_loader import load_prompt

def generate_callback_event(game_state, callback_type, callback_data):
    """
    Generates an event that directly references a past player decision or its consequences.
    """
    print(f"--- Generating CALLBACK event: {callback_type} ---")
    model = genai.GenerativeModel(TEXT_MODEL)

    # Corporate context
    corporation_name = game_state.corporation.get('name')
    player_name = game_state.player.get('name')
    player_title = game_state.player.get('title')

    # Time context
    current_quarter = game_state.simulation.get('current_fiscal_quarter')
    event_turn = callback_data.get('turn', game_state.turn_number - 2)
    quarters_passed = game_state.turn_number - event_turn

    # Load appropriate prompt template
    template = load_prompt(f'callbacks/{callback_type}')

    format_kwargs = {
        'corporation_name': corporation_name,
        'player_name': player_name,
        'player_title': player_title,
        'quarters_passed': quarters_passed
    }

    if callback_type == 'broken_promise':
        format_kwargs['promise_text'] = callback_data.get('text', 'a previous commitment')
        format_kwargs['promise_event'] = callback_data.get('event', 'a past meeting')

    prompt = template.format(**format_kwargs)

    try:
        response = model.generate_content(
            prompt,
            generation_config={
                "response_mime_type": "application/json",
                "temperature": 0.75
            }
        )
        event_data = json.loads(response.text)
        event_data['is_callback'] = True
        event_data['callback_type'] = callback_type
        event_data['callback_data'] = callback_data

        callback_label = callback_type.replace('_', ' ').title()
        if 'title' in event_data:
            event_data['title'] += f" -- Follow-up: {callback_label}"

        print(f"--- Callback event '{event_data.get('title', 'Unknown')}' generated ---")
        return event_data

    except Exception as e:
        print(f"Error generating callback event: {e}")
        return {
            "title": f"A Past Decision Revisited",
            "narrative": "Someone is following up on a decision you made in a previous quarter. They are looking for answers.",
            "investigation_options": ["Review the history of the decision.", "Ask them for their specific concerns."],
            "decision_options": ["Address their concerns directly.", "Delegate the issue to a subordinate."],
            "is_callback": True,
            "callback_type": callback_type
        }
