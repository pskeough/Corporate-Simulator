import json
import google.generativeai as genai
from model_config import TEXT_MODEL
from engines.prompt_loader import load_prompt


def apply_faction_decision_consequences(game_state, chosen_faction, affected_factions):
    """
    BALANCE_OVERHAUL: Apply asymmetric faction approval changes based on petition decisions.
    Favored faction gets moderate bonus, opposed factions get larger penalties (2:1 ratio).

    Args:
        chosen_faction: Faction ID that was favored
        affected_factions: List of faction IDs that were opposed
    """
    if not hasattr(game_state, 'faction_manager'):
        return

    # Favor chosen faction: +20 approval
    game_state.faction_manager.update_approval(chosen_faction, 20)
    game_state.faction_manager.add_history_entry(
        chosen_faction,
        "Decision favored your petition",
        20,
        game_state.turn_number
    )
    print(f"  ✓ {chosen_faction}: +20 approval (decision favored them)")

    # Penalize opposed factions asymmetrically (2:1 ratio)
    for opposed_faction in affected_factions:
        # Calculate penalty based on faction relationships
        base_penalty = -40  # Base 2:1 ratio

        # Check if this faction has low approval (they hold grudges)
        faction_data = game_state.faction_manager.get_by_id(opposed_faction)
        if faction_data and faction_data.get('approval', 60) < 40:
            base_penalty = -50  # Already angry factions react worse

        game_state.faction_manager.update_approval(opposed_faction, base_penalty)
        game_state.faction_manager.add_history_entry(
            opposed_faction,
            "Decision opposed your interests",
            base_penalty,
            game_state.turn_number
        )
        print(f"  ✗ {opposed_faction}: {base_penalty} approval (decision opposed them)")

    # Check for conspiracy conditions (2+ factions below 30 approval)
    low_approval_factions = [
        f for f in game_state.faction_manager.get_all()
        if f.get('approval', 60) < 30
    ]

    if len(low_approval_factions) >= 2:
        print(f"  ⚠️ WARNING: {len(low_approval_factions)} factions below 30 approval - CONSPIRACY RISK HIGH")
        # This will trigger conspiracy events in event_engine.py


def generate_faction_audience(game_state):
    """
    Generates faction petitions by calling a generative AI model.

    Constructs a prompt with faction data, sends it to the AI, and processes
    the JSON response to create a faction audience event.

    Args:
        game_state (dict): The current state of the game.

    Returns:
        dict: A dictionary representing the faction audience event,
              or an empty dictionary if an error occurs.
    """
    # Access factions through manager
    if not hasattr(game_state, 'faction_manager'):
        print("Warning: No faction manager available. Skipping faction audience.")
        return {}

    factions = game_state.faction_manager.get_all()
    if not factions:
        print("Warning: No factions available. Skipping faction audience.")
        return {}

    # Contextualize faction approval levels
    faction_contexts = []
    for faction in factions:
        faction_name = faction.get('name', 'Unknown')
        goals = ", ".join(faction.get("goals", []))
        approval = faction.get("approval", 50)

        # Add approval context
        if approval >= 75:
            approval_desc = f"{approval} (Loyal and supportive)"
        elif approval >= 50:
            approval_desc = f"{approval} (Pleased)"
        elif approval >= 25:
            approval_desc = f"{approval} (Discontent)"
        else:
            approval_desc = f"{approval} (Angry and hostile)"

        faction_contexts.append({
            'name': faction_name,
            'goals': goals,
            'approval': approval,
            'approval_desc': approval_desc
        })

    # Build faction list for prompt
    faction_list = ""
    for fc in faction_contexts:
        faction_list += f"- {fc['name']}:\n"
        faction_list += f"  - Goals: {fc['goals']}\n"
        faction_list += f"  - Approval: {fc['approval_desc']}\n"
    prompt = load_prompt('factions/faction_audience').format(
        faction_list=faction_list
    )

    try:
        model = genai.GenerativeModel(TEXT_MODEL)
        response = model.generate_content(
            prompt,
            generation_config={"response_mime_type": "application/json"},
        )
        result = json.loads(response.text)
        result["event_type"] = "faction_audience"

        # Add event type to title
        if 'title' in result:
            result['title'] = result['title'] + " -- Faction Audience"

        # Initialize event state
        game_state.current_event = result
        game_state.event_stage = 0
        game_state.event_conversation = []

        return result
    except Exception as e:
        print(f"Error generating faction audience: {e}")
        return {}
