import json
import google.generativeai as genai
from model_config import TEXT_MODEL
from engines.prompt_loader import load_prompt

def generate_character_vignette(game_state, character_id):
    """
    Creates a prompt for the AI to start a multi-stage conversation with a character.

    Args:
        game_state: The main game state object.
        character_id: The name of the character to generate the vignette for.

    Returns:
        A dictionary containing the vignette, or None if an error occurs.
    """
    character = None

    # Check if the character is the leader
    if game_state.civilization.get('leader', {}).get('name') == character_id:
        character = game_state.civilization['leader']
    else:
        # Search for the character in the inner circle via manager
        if not hasattr(game_state, 'inner_circle_manager'):
            print(f"Warning: No inner circle manager available. Cannot find character {character_id}.")
            return None

        character = game_state.inner_circle_manager.get_by_name(character_id)

    if not character:
        return None

    # Extract context for richer prompts
    civ_name = game_state.civilization.get('meta', {}).get('name', 'the realm')
    char_name = character.get('name', 'Unknown')
    char_role = character.get('role', 'advisor')
    loyalty = character.get('loyalty', 50)
    relationship = character.get('relationship', 50)

    # Contextualize loyalty and relationship
    if loyalty < 25:
        loyalty_desc = "wavering and doubtful (loyalty: {})".format(loyalty)
    elif loyalty < 50:
        loyalty_desc = "uncertain and conflicted (loyalty: {})".format(loyalty)
    elif loyalty < 75:
        loyalty_desc = "steadfast but tested (loyalty: {})".format(loyalty)
    else:
        loyalty_desc = "unwavering and true (loyalty: {})".format(loyalty)

    if relationship < 25:
        relationship_desc = "distrustful and distant"
    elif relationship < 50:
        relationship_desc = "cautiously respectful"
    elif relationship < 75:
        relationship_desc = "warmly cordial"
    else:
        relationship_desc = "deeply trusting"

    # Load and format the character vignette prompt
    character_json = json.dumps(character, indent=2)
    personality_traits = ', '.join(character.get('personality_traits', []))

    prompt = load_prompt('characters/character_vignette').format(
        char_name=char_name,
        char_role=char_role,
        civ_name=civ_name,
        loyalty_desc=loyalty_desc,
        relationship_desc=relationship_desc,
        character_json=character_json,
        personality_traits=personality_traits
    )

    try:
        model = genai.GenerativeModel(TEXT_MODEL)
        response = model.generate_content(
            prompt,
            generation_config={"response_mime_type": "application/json"},
        )
        raw_data = json.loads(response.text)

        # Validate that AI generated all required fields
        investigation_opts = raw_data.get("investigation_options", [])
        decision_opts = raw_data.get("decision_options", [])

        # Fallback to generic options only if AI completely failed to generate them
        if not investigation_opts or len(investigation_opts) < 2:
            print(f"⚠️ Warning: AI did not generate investigation_options for {char_name}, using fallback")
            investigation_opts = [
                "Ask about the specific details of their dilemma",
                "Inquire about what they've tried so far"
            ]

        if not decision_opts or len(decision_opts) < 2:
            print(f"⚠️ Warning: AI did not generate decision_options for {char_name}, using fallback")
            decision_opts = [
                "Offer counsel on one path forward",
                "Advise a different course of action"
            ]

        # Transform AI response into proper event format expected by frontend
        event_data = {
            "title": f"Audience with {character.get('name')}",
            "narrative": raw_data.get("dialogue", "The character greets you warmly."),
            "investigation_options": investigation_opts,
            "decision_options": decision_opts,
            "event_type": "character_vignette",
            "character_name": character.get('name'),
            "dilemma_summary": raw_data.get("dilemma_summary", "")
        }
        return event_data
    except Exception as e:
        print(f"Error generating character vignette for {character_id}: {e}")
        return None