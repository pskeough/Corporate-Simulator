import json
import google.generativeai as genai
from model_config import TEXT_MODEL
from engines.prompt_loader import load_prompt

def generate_character_vignette(game_state, person_name):
    """
    Creates a prompt for the AI to start a multi-stage conversation with a key person.
    """
    person = None
    if game_state.player.get('name') == person_name:
        person = game_state.player
    else:
        # Assumes a key_personnel_manager would exist for more complex scenarios
        for p in game_state.key_personnel.get('personnel', []):
            if p.get('person', {}).get('name') == person_name:
                person = p.get('person')
                break

    if not person:
        print(f"Warning: Could not find person named {person_name}.")
        return None

    corporation_name = game_state.corporation.get('name', 'the company')
    person_name = person.get('name', 'Unknown')
    person_relationship = person.get('relationship_to_player', 'colleague')
    rapport = person.get('metrics', {}).get('rapport', 50)

    if rapport < 25:
        rapport_desc = f"strained and difficult (Rapport: {rapport})"
    elif rapport < 50:
        rapport_desc = f"professional but distant (Rapport: {rapport})"
    else:
        rapport_desc = f"positive and collaborative (Rapport: {rapport})"

    person_json = json.dumps(person, indent=2)
    work_style = ', '.join(person.get('work_style', []))

    prompt = load_prompt('characters/character_vignette').format(
        person_name=person_name,
        person_relationship=person_relationship,
        corporation_name=corporation_name,
        rapport_desc=rapport_desc,
        person_json=person_json,
        work_style=work_style
    )

    try:
        model = genai.GenerativeModel(TEXT_MODEL)
        response = model.generate_content(
            prompt,
            generation_config={"response_mime_type": "application/json"},
        )
        raw_data = json.loads(response.text)

        event_data = {
            "title": f"Conversation with {person.get('name')}",
            "narrative": raw_data.get("dialogue", f"{person.get('name')} approaches you with a concerned look."),
            "investigation_options": raw_data.get("investigation_options", ["Ask for more details.", "Ask what they've tried so far."]),
            "decision_options": raw_data.get("decision_options", ["Offer your support.", "Suggest they handle it themselves."]),
            "event_type": "personnel_vignette",
            "person_name": person.get('name'),
            "dilemma_summary": raw_data.get("dilemma_summary", "A professional challenge that needs to be addressed.")
        }
        return event_data
    except Exception as e:
        print(f"Error generating personnel vignette for {person_name}: {e}")
        return None
