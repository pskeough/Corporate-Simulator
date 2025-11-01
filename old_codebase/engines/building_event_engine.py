"""
BuildingEventEngine - Generates AI-driven building construction events.
"""

import google.generativeai as genai
import json
from json import JSONDecodeError
from model_config import TEXT_MODEL
from engines.building_manager import BuildingManager


def generate_building_event(game_state):
    """
    Generate an event offering building construction choices.

    Args:
        game_state: GameState instance

    Returns:
        Event data dictionary with building options
    """
    print("--- Generating building construction event ---")

    # Get available buildings
    building_manager = BuildingManager()
    available_buildings = building_manager.get_available(game_state)

    # If no buildings available, return a fallback event
    if not available_buildings:
        fallback_data = {
            "title": "Infrastructure Planning -- Building Event",
            "narrative": f"Your advisors gather to discuss future construction projects, {game_state.civilization['leader']['name']}. However, your civilization lacks the necessary knowledge and resources to build anything at this time. Perhaps focusing on technological advancement would open new possibilities.",
            "investigation_options": [
                "Ask what technologies would unlock new buildings",
                "Inquire about current resource limitations"
            ],
            "decision_options": [
                "Focus on accumulating wealth for future projects",
                "Prioritize technological research to unlock new construction"
            ],
            "event_type": "building_event"
        }

        # Initialize event state
        game_state.current_event = fallback_data
        game_state.event_stage = 0
        game_state.event_conversation = []

        return fallback_data

    # Select 2-3 buildings to offer as choices
    import random
    num_choices = min(3, len(available_buildings))
    selected_buildings = random.sample(available_buildings, num_choices)

    # Build context for AI
    civ_name = game_state.civilization.get('meta', {}).get('name', 'Your civilization')
    leader_name = game_state.civilization.get('leader', {}).get('name', 'Leader')
    era = game_state.civilization.get('meta', {}).get('era', 'stone_age')
    wealth = game_state.civilization.get('resources', {}).get('wealth', 0)
    population = game_state.civilization.get('population', 0)

    # Format building options for AI
    building_descriptions = []
    for building in selected_buildings:
        cost = building.get('cost', {})
        wealth_cost = cost.get('wealth', 0)
        turns = cost.get('turns', 1)
        description = building.get('description', 'A useful structure')

        building_descriptions.append(
            f"- {building['name']}: {description} (Cost: {wealth_cost} wealth, {turns} turns)"
        )

    # Generate AI event
    model = genai.GenerativeModel(TEXT_MODEL)

    # Contextualize wealth and population for narrative
    if wealth < 100:
        wealth_context = f"{wealth} gold (barely enough for construction)"
    elif wealth < 500:
        wealth_context = f"{wealth} gold (modest means)"
    elif wealth < 2000:
        wealth_context = f"{wealth} gold (healthy treasury)"
    else:
        wealth_context = f"{wealth} gold (overflowing coffers)"

    if population < 500:
        pop_context = "a small community"
    elif population < 2000:
        pop_context = "a growing town"
    elif population < 10000:
        pop_context = "a thriving settlement"
    else:
        pop_context = "a grand city"

    prompt = f"""You are the master storyteller for a civilization simulation game. Generate a building construction event with a clear character voice - the Master Architect or Chief Builder addressing the leader.

**NARRATIVE PURPOSE:** Make infrastructure construction feel meaningful and strategic. This isn't just spending resources - it's shaping the civilization's future. The player should feel the weight of choosing which building to prioritize.

**CHARACTER VOICE:** Embody the voice of the civilization's Master Architect or Chief Builder. They should:
- Speak with expertise and passion about construction
- Reference the civilization's specific needs (population growth, defense, culture, etc.)
- Show urgency or opportunity that makes NOW the right time to build

<CONTEXT>
Civilization: {civ_name} (Era: {era}, {pop_context})
Leader: {leader_name}
Population: {population:,} souls
Current Wealth: {wealth_context}

Available Buildings for Construction:
{chr(10).join(building_descriptions)}
</CONTEXT>

<TASK>
Create an event where the Master Architect or Chief Builder presents construction proposals to {leader_name}.

**REACTIVITY REQUIREMENTS:**
1. **Contextualize the opportunity**: Why is construction being discussed NOW?
   - Is population growing and needs housing/infrastructure?
   - Is wealth accumulated and burning a hole in the treasury?
   - Is there a specific need (defense, culture, economy)?
   - Does the {era} era make certain buildings particularly valuable?

2. **Give the architect personality**: Don't just list options - have them ADVOCATE
   - "My Lord, I have studied the plans for months..."
   - "The master masons stand ready, but we must choose wisely..."
   - "Our {pop_context} has outgrown its current infrastructure..."

3. **Connect buildings to civilization values/needs**:
   - If a Temple is available: "Our people's faith in [religion] grows stronger - a temple would honor this devotion"
   - If Military building: "Our defenses must match the ambitions of our enemies"
   - If Economic building: "Trade routes flourish, but we need the infrastructure to capitalize"

Output ONLY valid JSON:
{{
  "title": "A short, evocative title about construction (3-6 words)",
  "narrative": "2-3 sentences from the Master Architect presenting the opportunity. Address {leader_name} directly. Show expertise and urgency. Reference specific civilization context (population, wealth, era, needs).",
  "investigation_options": [
    "Ask the architect about the strategic benefits of [specific building type]",
    "Inquire which building addresses the most urgent need"
  ],
  "decision_options": [
    "Construct {selected_buildings[0]['name']} (exact building name - show the benefit)",
    "Construct {selected_buildings[1]['name'] if len(selected_buildings) > 1 else selected_buildings[0]['name']} (exact building name - show the benefit)"
  ]
}}

CRITICAL:
- Decision options MUST include exact building names from the available list
- Each decision should reference a different building
- Investigation options should be SPECIFIC (not generic "learn more")
- The narrative should make the player CARE about which building they choose
- Reference the civilization's current state: {pop_context}, wealth of {wealth}, {era} era technology
</TASK>"""

    try:
        response = model.generate_content(
            prompt,
            generation_config={
                "response_mime_type": "application/json",
                "temperature": 0.8
            }
        )
        event_data = json.loads(response.text)

        # Validate decision options contain building names
        decision_options = event_data.get('decision_options', [])
        validated_options = []

        for option in decision_options:
            # Check if option references a building
            matched = False
            for building in selected_buildings:
                if building['name'].lower() in option.lower():
                    # Ensure the option clearly indicates construction
                    if 'construct' not in option.lower() and 'build' not in option.lower():
                        option = f"Construct {building['name']}"
                    validated_options.append(option)
                    matched = True
                    break

            if not matched:
                # Fallback: Use first available building
                validated_options.append(f"Construct {selected_buildings[0]['name']}")

        # Add "delay construction" option
        validated_options.append("Delay construction and save resources")

        event_data['decision_options'] = validated_options[:3]  # Limit to 3 options

        # Add event type to title and set event_type field
        if 'title' in event_data:
            event_data['title'] = event_data['title'] + " -- Building Event"
        event_data['event_type'] = 'building_event'

        # Initialize event state
        game_state.current_event = event_data
        game_state.event_stage = 0
        game_state.event_conversation = []

        print(f"--- Building event '{event_data.get('title', 'Unknown')}' generated ---")
        return event_data

    except JSONDecodeError as e:
        print(f"Error parsing AI response: {e}")
        # Return fallback event
        fallback_data = {
            "title": "Infrastructure Development -- Building Event",
            "narrative": f"Your chief architect presents plans for new construction, {leader_name}. The people await your decision on what to build next.",
            "investigation_options": [
                "Ask about available building options",
                "Inquire about resource costs"
            ],
            "decision_options": [
                f"Construct {selected_buildings[0]['name']}",
                f"Construct {selected_buildings[1]['name']}" if len(selected_buildings) > 1 else "Save resources for later",
                "Delay construction"
            ],
            "event_type": "building_event"
        }

        # Initialize event state for fallback
        game_state.current_event = fallback_data
        game_state.event_stage = 0
        game_state.event_conversation = []

        return fallback_data

    except Exception as e:
        print(f"Error generating building event: {e}")
        # Return fallback event
        fallback_data = {
            "title": "Construction Planning -- Building Event",
            "narrative": "An opportunity arises to expand your civilization's infrastructure.",
            "investigation_options": [
                "Review building options",
                "Check available resources"
            ],
            "decision_options": [
                f"Construct {selected_buildings[0]['name']}",
                "Wait for a better time"
            ],
            "event_type": "building_event"
        }

        # Initialize event state for fallback
        game_state.current_event = fallback_data
        game_state.event_stage = 0
        game_state.event_conversation = []

        return fallback_data
