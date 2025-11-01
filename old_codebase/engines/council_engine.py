import json
import google.generativeai as genai
from model_config import TEXT_MODEL
from engines.prompt_loader import load_prompt


def normalize_options(options, option_type="option"):
    """
    Robustly normalize option arrays to ensure they're clean string arrays.

    Args:
        options: Raw options from AI (may be strings, objects, or mixed)
        option_type: Type of option for logging (e.g., "investigation", "decision")

    Returns:
        List of validated string options
    """
    if not options:
        print(f"  ⚠️ Warning: Empty {option_type} options array")
        return []

    if not isinstance(options, list):
        print(f"  ⚠️ Warning: {option_type} options is not a list, converting to list")
        options = [options]

    normalized = []
    for idx, opt in enumerate(options):
        try:
            # Handle string (ideal case)
            if isinstance(opt, str):
                if opt.strip():  # Non-empty string
                    normalized.append(opt.strip())
                else:
                    print(f"  ⚠️ Warning: Empty string in {option_type} options at index {idx}, skipping")

            # Handle dict/object
            elif isinstance(opt, dict):
                # Try multiple possible key names
                text_value = (opt.get('text') or
                             opt.get('action') or
                             opt.get('option') or
                             opt.get('description') or
                             opt.get('label'))

                if text_value and isinstance(text_value, str):
                    normalized.append(str(text_value).strip())
                else:
                    # Last resort: stringify the entire object
                    fallback = str(opt)
                    print(f"  ⚠️ Warning: Could not extract text from {option_type} object at index {idx}, using: {fallback[:50]}")
                    normalized.append(fallback)

            # Handle None
            elif opt is None:
                print(f"  ⚠️ Warning: None value in {option_type} options at index {idx}, skipping")

            # Handle other types (int, bool, etc.)
            else:
                str_value = str(opt)
                print(f"  ⚠️ Warning: Non-string {option_type} option at index {idx} (type: {type(opt).__name__}), converted to: {str_value}")
                normalized.append(str_value)

        except Exception as e:
            print(f"  ❌ Error normalizing {option_type} option at index {idx}: {e}, skipping")
            continue

    # Ensure we have at least 2 options (requirement for UI)
    if len(normalized) < 2:
        print(f"  ⚠️ Warning: Only {len(normalized)} {option_type} option(s) found, expected 2+")

    return normalized


def generate_council_meeting(game_state):
    """
    Generates a council meeting event by calling the AI model.

    The prompt instructs the AI to:
    1. Analyze the entire game_state.
    2. Generate 2-3 "advisor reports" summarizing key stats.
    3. Synthesize these reports into 2-3 "pressing matters" for the player to address as a new policy.

    Args:
        game_state (dict): The current state of the game.

    Returns:
        dict: The generated council meeting event as a JSON object.
    """
    game_state_dict = game_state.to_dict()
    game_state_json = json.dumps(game_state_dict, indent=2)

    # Parse some key context for narrative enhancement
    game_dict = game_state.to_dict()
    pop = game_dict.get('civilization', {}).get('population', 0)
    food = game_dict.get('civilization', {}).get('resources', {}).get('food', 0)
    wealth = game_dict.get('civilization', {}).get('resources', {}).get('wealth', 0)
    leader_name = game_dict.get('civilization', {}).get('leader', {}).get('name', 'Leader')

    # Get inner circle advisors for more accurate personas
    advisor_names = []
    advisor_details = []
    if hasattr(game_state, 'inner_circle_manager'):
        for char in game_state.inner_circle_manager.get_all():
            advisor_names.append(char['name'])
            advisor_details.append({
                'name': char['name'],
                'role': char['role'],
                'personality': ', '.join(char.get('personality_traits', [])),
                'recent_history': char.get('history', [])[-3:] if char.get('history') else []
            })

    advisor_context = "\n".join([
        f"- {a['name']} ({a['role']}): {a['personality']}"
        for a in advisor_details
    ]) if advisor_details else "Generic advisors"

    # Build advisor memory context for AI prompt
    advisor_memories = "\n".join([
        f"- {a['name']} ({a['role']}): Last remembers \"{a['recent_history'][-1]}\"" if a['recent_history'] else f"- {a['name']} ({a['role']}): No recent memories"
        for a in advisor_details
    ]) if advisor_details else "No memories available"

    # Pre-calculate formatted values
    pop_formatted = f"{pop:,}"
    food_formatted = f"{food:,}"
    wealth_formatted = f"{wealth:,}"
    food_per_capita = food / max(pop, 1)

    # Load prompt template and fill in variables
    prompt_template = load_prompt('council/council_meeting')
    prompt = prompt_template.format(
        leader_name=leader_name,
        game_state_json=game_state_json,
        advisor_context=advisor_context,
        advisor_memories=advisor_memories,
        population=pop_formatted,
        food=food_formatted,
        wealth=wealth_formatted,
        food_per_capita=food_per_capita
    )
    try:
        model = genai.GenerativeModel(TEXT_MODEL)
        response = model.generate_content(
            prompt,
            generation_config={"response_mime_type": "application/json"},
        )
        council_meeting_data = json.loads(response.text)

        # Normalize options to ensure they're arrays of strings
        council_meeting_data['investigation_options'] = normalize_options(
            council_meeting_data.get('investigation_options', []),
            "investigation"
        )
        council_meeting_data['decision_options'] = normalize_options(
            council_meeting_data.get('decision_options', []),
            "decision"
        )

        # Ensure event_type is set (in case AI doesn't include it)
        if 'event_type' not in council_meeting_data:
            council_meeting_data['event_type'] = 'council_meeting'

        # Add event type to title
        if 'title' in council_meeting_data:
            council_meeting_data['title'] = council_meeting_data['title'] + " -- Council Meeting"

        # Initialize event state
        game_state.current_event = council_meeting_data
        game_state.event_stage = 0
        game_state.event_conversation = []

        return council_meeting_data
    except Exception as e:
        print(f"Error generating council meeting: {e}")
        return None

def generate_first_turn_briefing(game_state):
    """
    Generates a special one-time "First Council Briefing" event for turn 0.
    Introduces the player to their council and presents the first major choice.
    """
    game_state_json = json.dumps(game_state.to_dict(), indent=2)

    # Extract key context from game state
    game_dict = json.loads(game_state_json)
    civ_name = game_dict.get('civilization', {}).get('meta', {}).get('name', 'Your Civilization')
    leader_name = game_dict.get('civilization', {}).get('leader', {}).get('name', 'Leader')
    era = game_dict.get('civilization', {}).get('meta', {}).get('era', 'ancient times')
    culture_values = game_dict.get('culture', {}).get('values', [])

    # Pre-calculate formatted values
    population_formatted = f"{game_dict.get('civilization', {}).get('population', 0):,}"
    food_formatted = f"{game_dict.get('civilization', {}).get('resources', {}).get('food', 0):,}"
    wealth_formatted = f"{game_dict.get('civilization', {}).get('resources', {}).get('wealth', 0):,}"
    culture_values_str = ', '.join(culture_values[:3]) if culture_values else 'being forged'

    # Load prompt template and fill in variables
    prompt_template = load_prompt('council/first_turn_briefing')
    prompt = prompt_template.format(
        leader_name=leader_name,
        civ_name=civ_name,
        era=era,
        culture_values=culture_values_str,
        game_state_json=game_state_json,
        population=population_formatted,
        food=food_formatted,
        wealth=wealth_formatted
    )
    try:
        model = genai.GenerativeModel(TEXT_MODEL)
        response = model.generate_content(
            prompt,
            generation_config={"response_mime_type": "application/json"},
        )
        briefing_data = json.loads(response.text)
        briefing_data["event_type"] = "council_meeting" # Use same type for UI handling

        # Normalize options to ensure they're arrays of strings
        briefing_data['investigation_options'] = normalize_options(
            briefing_data.get('investigation_options', []),
            "investigation (first turn)"
        )
        briefing_data['decision_options'] = normalize_options(
            briefing_data.get('decision_options', []),
            "decision (first turn)"
        )

        # Add event type to title
        if 'title' in briefing_data:
            briefing_data['title'] = briefing_data['title'] + " -- Council Meeting"

        # Initialize event state
        game_state.current_event = briefing_data
        game_state.event_stage = 0
        game_state.event_conversation = []

        return briefing_data
    except Exception as e:
        print(f"Error generating first turn briefing: {e}")
        # Return a hardcoded fallback event
        fallback_data = {
            "title": "A Leader's First Council -- Council Meeting",
            "narrative": "Your advisors gather. It is time to set the course for your civilization.",
            "state_of_realm": "Your people look to you with hope and uncertainty. The path ahead is unclear, but destiny awaits.",
            "advisor_reports": [{"advisor_title": "Elder", "summary": "Our people look to you for guidance."}],
            "pressing_matters": "You must choose a path.",
            "investigation_options": ["Ask the Elder for wisdom", "Consult with the council"],
            "decision_options": ["Focus on Growth", "Focus on Defense"],
            "event_type": "council_meeting"
        }

        # Initialize event state for fallback too
        game_state.current_event = fallback_data
        game_state.event_stage = 0
        game_state.event_conversation = []

        return fallback_data
