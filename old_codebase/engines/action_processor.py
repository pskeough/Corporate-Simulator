# engines/action_processor.py
"""
Action Processor Module

This module handles processing player actions, determining outcomes,
and managing the consequences of decisions in the game.

Refactored from event_engine.py for better maintainability and separation of concerns.
"""

import google.generativeai as genai
import json
from json import JSONDecodeError
import re
from engines.context_builder import build_action_context
from engines.state_validator import validate_updates, get_validation_summary
from engines.event_generator import api_call_with_retry
from engines.state_updater import apply_updates
from engines.prompt_loader import load_prompt
from model_config import TEXT_MODEL

def process_player_action(game_state, action, event_title, event_narrative):
    """Determines the outcome of a player's FINAL action and applies it (ends the event)."""
    print(f"--- Asking Gemini for outcome of '{action}' (FINAL RESOLUTION) ---")
    model = genai.GenerativeModel(TEXT_MODEL)

    # Build optimized action context
    context = build_action_context(game_state)

    # Build conversation history for context
    conversation_summary = ""
    if game_state.event_conversation:
        conversation_summary = "\n".join([
            f"- Player {entry['player']}: {entry['ai']}"
            for entry in game_state.event_conversation
        ])
        conversation_summary = f"\n<CONVERSATION_HISTORY>\nThe player investigated before deciding:\n{conversation_summary}\n</CONVERSATION_HISTORY>\n"

    # Contextualize the civilization state for outcomes
    pop = context['civilization']['population']
    food = context['civilization']['resources']['food']
    wealth = context['civilization']['resources']['wealth']
    leader_age = context['civilization']['leader']['age']

    # Determine if resources are strained
    food_per_capita = food / max(pop, 1)
    resource_state = ""
    if food_per_capita < 0.5:
        resource_state = "Your people are starving. "
    elif wealth < 50:
        resource_state = "Your treasury is nearly empty. "
    elif food_per_capita > 3.0 and wealth > 3000:
        resource_state = "Your civilization is wealthy and well-fed. "

    # Pre-calculate all formatted values before loading the prompt
    pop_formatted = f"{pop:,}"
    food_formatted = f"{food:,}"
    wealth_formatted = f"{wealth:,}"
    culture_values = ', '.join(context['culture']['values'][:5])
    culture_values_short = ', '.join(context['culture']['values'][:3])
    leader_traits = ', '.join(context['civilization']['leader']['traits'])
    recent_discoveries = ', '.join(context['technology']['recent_discoveries'][-3:])

    # Load prompt template and fill in variables
    prompt_template = load_prompt('actions/process_player_action')
    prompt = prompt_template.format(
        event_title=event_title,
        event_narrative=event_narrative,
        conversation_summary=conversation_summary,
        action=action,
        civ_name=context['civilization']['meta']['name'],
        year=context['civilization']['meta']['year'],
        leader_name=context['civilization']['leader']['name'],
        leader_age=leader_age,
        population=pop_formatted,
        food=food_formatted,
        wealth=wealth_formatted,
        resource_state=resource_state,
        tech_tier=context['civilization']['resources']['tech_tier'],
        culture_values=culture_values,
        culture_values_short=culture_values_short,
        leader_traits=leader_traits,
        religion_name=context['religion']['name'],
        religion_influence=context['religion']['influence'],
        recent_discoveries=recent_discoveries,
        terrain=context['world']['geography']['terrain']
    )

    try:
        # Use retry wrapper for API call
        def make_api_call():
            response = model.generate_content(
                prompt,
                generation_config={
                    "response_mime_type": "application/json",
                    "temperature": 0.7  # Balanced creativity for outcomes
                }
            )
            return response

        response = api_call_with_retry(make_api_call, max_retries=3, initial_delay=2.0)

        # FIX: Sanitize response to remove XML tags, Markdown code fences, and reasoning blocks
        raw_text = response.text.strip()

        # Remove XML-style wrapper tags (e.g., <reasoning>, <thinking>, etc.)
        raw_text = re.sub(r'^<[^>]+>.*?</[^>]+>\s*', '', raw_text, flags=re.DOTALL)

        # Extract JSON from code fences if present
        json_match = re.search(r'```json\s*(\{.*?\})\s*```', raw_text, re.DOTALL)
        if json_match:
            raw_text = json_match.group(1)
        else:
            # Fallback: Remove any remaining code fences
            if raw_text.startswith("```json"):
                raw_text = raw_text[7:]
            elif raw_text.startswith("```"):
                raw_text = raw_text[3:]
            if raw_text.endswith("```"):
                raw_text = raw_text[:-3]

        raw_text = raw_text.strip()
        print(f"DEBUG: Sanitized response (first 200 chars): {raw_text[:200]}")

        outcome = json.loads(raw_text)

        # FIX: Handle nested 'output' key if AI wraps response
        if "output" in outcome and isinstance(outcome["output"], dict):
            outcome = outcome["output"]

        print(f"--- Gemini Outcome Received ---\n{json.dumps(outcome, indent=2)}\n-----------------------------")
    except JSONDecodeError as e:
        print(f"!!!!!!!!!! JSON PARSING ERROR (Outcome) !!!!!!!!!!!\nFailed to parse AI response: {e}")
        print(f"Raw response: {response.text if 'response' in locals() else 'No response'}")
        return {
            "narrative": "The consequences of your action are unclear. The spirits speak in riddles, but the world endures.",
            "updates": {},
            "status": "error"
        }
    except Exception as e:
        error_msg = str(e).lower()
        print(f"!!!!!!!!!! GEMINI API ERROR (Outcome) !!!!!!!!!!!\n{e}")

        # Provide specific, actionable error messages
        if "oauth" in error_msg or "token" in error_msg or "authentication" in error_msg:
            narrative = "⚠️ Authentication Error: Your API credentials have expired. Please update your GEMINI_API_KEY and restart the game."
        elif "404" in error_msg or "not found" in error_msg:
            narrative = "⚠️ API Error: The AI model is not available. Please check your GEMINI_API_KEY and model configuration."
        elif "quota" in error_msg or "rate limit" in error_msg:
            narrative = "⚠️ Rate Limit: API quota exceeded. Please wait a few minutes before continuing."
        else:
            narrative = f"⚠️ API Error: Unable to process your action due to a technical issue. The world holds its breath... (Error: {str(e)[:100]})"

        print(f"NOTE: {narrative}")
        return {
            "narrative": narrative,
            "updates": {},
            "status": "error"
        }

    try:
        # Validate updates before applying
        if "updates" in outcome and outcome["updates"]:
            is_valid, cleaned_updates, errors = validate_updates(outcome["updates"], game_state)

            if errors:
                print(f"--- Validation Warnings ---")
                validation_summary = get_validation_summary(errors)
                print(validation_summary)

            if cleaned_updates:
                print("--- Applying Validated Updates ---")
                apply_updates(game_state, cleaned_updates)
            else:
                print("--- No valid updates to apply ---")
        else:
            print("--- No updates from AI ---")

        # Check if this was a building construction decision
        if "construct" in action.lower() or "build" in action.lower():
            from engines.building_manager import BuildingManager
            building_manager = BuildingManager()

            # Try to match action to a building
            for building_id, building_def in building_manager.get_all_building_types().items():
                if building_def['name'].lower() in action.lower():
                    # Attempt to start construction
                    success, msg = building_manager.start_construction(building_id, game_state)
                    if success:
                        print(f"  🏗️ {msg}")
                    else:
                        print(f"  ⚠️ Building construction failed: {msg}")
                    break

        # Check if this was a character vignette completion (grant faction approval bonus)
        if hasattr(game_state, 'current_event') and game_state.current_event.get('event_type') == 'character_vignette':
            character_name = game_state.current_event.get('character_name')
            if character_name and hasattr(game_state, 'inner_circle_manager') and hasattr(game_state, 'faction_manager'):
                # Look up the character
                character = game_state.inner_circle_manager.get_by_name(character_name)
                if character:
                    faction_id = character.get('faction_id')
                    if faction_id:
                        # Apply approval bonus for personal relationship building
                        approval_change = 5
                        success = game_state.faction_manager.update_approval(faction_id, approval_change)
                        if success:
                            # Add history entry
                            game_state.faction_manager.add_history_entry(
                                faction_id,
                                f"Personal conversation with {character_name}",
                                approval_change,
                                game_state.turn_number
                            )
                            faction = game_state.faction_manager.get_by_id(faction_id)
                            faction_name = faction.get('name', 'Unknown Faction') if faction else 'Unknown Faction'
                            print(f"  💬 Vignette completed: {faction_name} approval +{approval_change} (now {faction['approval']})")
                        else:
                            print(f"  ⚠️ Warning: Failed to update approval for faction {faction_id}")
                    else:
                        print(f"  ℹ️ Character {character_name} has no faction affiliation")
                else:
                    print(f"  ⚠️ Warning: Character {character_name} not found")

        # Check if this was a faction audience decision (BALANCE_OVERHAUL: Apply asymmetric consequences)
        if hasattr(game_state, 'current_event') and game_state.current_event.get('event_type') == 'faction_audience':
            # Parse which faction was chosen and which were opposed from the action text
            # Extract faction names from the petitions
            petitions = game_state.current_event.get('petitions', [])

            # Identify chosen faction by matching action text to faction names
            chosen_faction = None
            for petition in petitions:
                faction_name = petition.get('faction', '')
                if faction_name.lower() in action.lower():
                    chosen_faction = faction_name
                    break

            if chosen_faction:
                # All other factions in the petition are opposed
                opposed_factions = [p.get('faction') for p in petitions if p.get('faction') != chosen_faction]
                print(f"--- Applying faction decision consequences: {chosen_faction} favored ---")
                from engines.faction_engine import apply_faction_decision_consequences
                apply_faction_decision_consequences(game_state, chosen_faction, opposed_factions)

        # Track consequences of this action
        from engines.consequence_engine import apply_consequences, detect_major_declaration

        consequences = apply_consequences(game_state, action, event_title, outcome.get("narrative", ""))

        # Check if this is a major declaration that should become a permanent decree
        major_declaration = detect_major_declaration(action, event_title, outcome.get("narrative", ""))
        if major_declaration:
            print(f"\n🏛️ MAJOR DECLARATION DETECTED: {major_declaration['type']} ({major_declaration['importance']})")
            print(f"   Significance Score: {major_declaration['significance_score']}")

            # Create permanent decree
            from engines.law_engine import LawEngine
            from engines.history_compression_engine import HistoryCompressionEngine

            law_engine = LawEngine(game_state)

            # Infer effects from the declaration text
            effects = _infer_decree_effects(major_declaration, game_state)

            # Create the decree
            decree = law_engine.create_decree(
                decree_type=major_declaration['type'],
                title=_generate_decree_title(major_declaration),
                declaration_text=major_declaration['action_text'],
                declared_by=game_state.civilization['leader']['name'],
                effects=effects,
                importance=major_declaration['importance']
            )

            # Add to state and apply effects
            impact_narrative = law_engine.add_decree_to_state(decree)
            print(f"   📜 Permanent decree created: {decree['title']}")
            print(f"   ⚖️ {impact_narrative}")

            # Archive in compressed history
            if major_declaration['importance'] == 'civilization_defining':
                history_engine = HistoryCompressionEngine(game_state)
                history_engine.archive_decree(decree)
                print(f"   📚 Archived as civilization-defining moment")

        # Check faction goals against turn outcome (passive faction simulation)
        _check_faction_goals(game_state, outcome, action, event_title)

        # Extract and save policy from council meetings
        if "council" in event_title.lower() or "briefing" in event_title.lower():
            # Parse policy from player's action
            policy_keywords = {
                'military': 'military_expansion',
                'defense': 'military_expansion',
                'war': 'military_expansion',
                'army': 'military_expansion',
                'trade': 'economic_growth',
                'merchant': 'economic_growth',
                'commerce': 'economic_growth',
                'wealth': 'economic_growth',
                'temple': 'religious_devotion',
                'faith': 'religious_devotion',
                'prayer': 'religious_devotion',
                'divine': 'religious_devotion',
                'knowledge': 'scientific_advancement',
                'research': 'scientific_advancement',
                'scholar': 'scientific_advancement',
                'discovery': 'scientific_advancement',
                'culture': 'cultural_development',
                'art': 'cultural_development',
                'tradition': 'cultural_development',
                'expand': 'territorial_expansion',
                'settle': 'territorial_expansion',
                'explore': 'exploration'
            }

            # Check action text for policy keywords
            action_lower = action.lower()
            detected_policy = None
            for keyword, policy in policy_keywords.items():
                if keyword in action_lower:
                    detected_policy = policy
                    break

            # Default to general governance if no specific policy detected
            if detected_policy:
                game_state.active_policy = detected_policy
                print(f"  📜 Active policy set to: {detected_policy}")
            elif game_state.active_policy is None:
                game_state.active_policy = "general_governance"
                print(f"  📜 Active policy defaulted to: general_governance")

        # Log event to history
        log_entry = {
            "year": game_state.civilization['meta']['year'],
            "title": event_title,
            "action": action,
            "narrative": outcome.get("narrative", "The consequences are unclear.")
        }
        game_state.history_long["events"].append(log_entry)

        # Apply resource consumption
        from engines.resource_engine import apply_consumption, apply_passive_generation

        # First, apply passive generation (civilization produces resources)
        production = apply_passive_generation(game_state)
        print(f"  📈 Passive production: +{production['food']} food, +{production['wealth']} wealth")

        # Then apply consumption
        consumption_status = apply_consumption(game_state)
        print(f"  📉 Consumption: -{consumption_status['food_consumed']} food, -{consumption_status['wealth_consumed']} wealth")

        # Apply automatic happiness changes from resource scarcity (Fix #6)
        from engines.resource_engine import calculate_resource_happiness_impact
        happiness_impact = calculate_resource_happiness_impact(game_state)
        if happiness_impact != 0:
            game_state.population_happiness = max(0, min(100, game_state.population_happiness + happiness_impact))
            if happiness_impact < 0:
                print(f"  😞 Happiness decreased by {abs(happiness_impact)} (resource scarcity)")
            else:
                print(f"  😊 Happiness increased by {happiness_impact} (prosperity)")

        # Apply faction approval happiness modifier
        faction_bonuses = game_state.faction_manager.get_faction_bonuses(game_state)
        game_state.population_happiness += faction_bonuses['happiness_modifier']
        game_state.population_happiness = max(0, min(100, game_state.population_happiness))
        if faction_bonuses['happiness_modifier'] != 0:
            print(f"  🙂 Faction approval changed happiness by {faction_bonuses['happiness_modifier']:+d}")

        # Add consumption warnings to outcome if any
        if consumption_status['warnings']:
            outcome['resource_warnings'] = consumption_status['warnings']
            outcome['consumption_effects'] = {}

            if 'starvation_deaths' in consumption_status:
                outcome['consumption_effects']['population_loss'] = consumption_status['starvation_deaths']
                print(f"  ☠️ Starvation! Population loss: -{consumption_status['starvation_deaths']}")

            if 'infrastructure_lost' in consumption_status:
                outcome['consumption_effects']['infrastructure_lost'] = consumption_status['infrastructure_lost']
                print(f"  🏚️ Bankruptcy! Infrastructure lost: {', '.join(consumption_status['infrastructure_lost'])}")

        # Process building construction (Phase 4)
        from engines.building_manager import BuildingManager
        building_manager = BuildingManager()
        completed_buildings = building_manager.process_turn(game_state)
        if completed_buildings:
            for building_name in completed_buildings:
                print(f"  🏛️ Construction complete: {building_name}")
                outcome['construction_complete'] = completed_buildings

        # Automatic state progression
        game_state.civilization['leader']['age'] += 1
        game_state.civilization['leader']['years_ruled'] += 1
        game_state.civilization['meta']['year'] += 1
        game_state.turn_number += 1

        # Apply aging effects and trait changes
        from engines.leader_engine import apply_aging_effects, calculate_leader_effectiveness

        aging_changes = apply_aging_effects(game_state)
        if aging_changes:
            for change in aging_changes:
                print(f"  👤 Leader {change}")

        # Check if leader portrait should be updated
        from engines.image_update_manager import should_update_leader_portrait, get_tracker
        tracker = get_tracker()
        tracker.increment_turns()

        should_update, reason = should_update_leader_portrait(game_state, aging_changes)
        if should_update:
            print(f"  🎨 Updating leader portrait: {reason}")
            # Trigger background portrait update
            from engines.visual_engine import update_leader_portrait_async
            update_leader_portrait_async(game_state)

        # Calculate leader effectiveness for bonuses
        effectiveness = calculate_leader_effectiveness(game_state.civilization['leader'])
        print(f"  💪 Leader effectiveness: {effectiveness:.2f}x")

        # Check if leader exceeds life expectancy and warn
        leader_age = game_state.civilization['leader']['age']
        life_exp = game_state.civilization['leader'].get('life_expectancy', 60)
        if leader_age > life_exp:
            print(f"  ⚠ Warning: Leader age ({leader_age}) exceeds life expectancy ({life_exp}). Consider abdication.")

        # Process science and culture progression
        from engines.bonus_engine import BonusEngine
        from engines.bonus_definitions import BonusType

        bonus_engine = BonusEngine()
        science_result = bonus_engine.calculate_bonuses(game_state, BonusType.SCIENCE_PER_TURN)
        culture_result = bonus_engine.calculate_bonuses(game_state, BonusType.CULTURE_PER_TURN)

        science_income = int(science_result['total'])
        culture_income = int(culture_result['total'])

        # Apply science progression
        if science_income > 0:
            # Initialize science_points if not present (backwards compatibility)
            if 'science_points' not in game_state.technology:
                game_state.technology['science_points'] = 0

            game_state.technology['science_points'] += science_income
            print(f"  🔬 Science: +{science_income} points (Total: {game_state.technology['science_points']})")

            current_research_id = game_state.technology.get('current_research_id')
            if current_research_id:
                # Load tech tree to get cost
                try:
                    import os
                    tech_tree_path = os.path.join('data', 'tech_tree.json')
                    if os.path.exists(tech_tree_path):
                        with open(tech_tree_path, 'r') as f:
                            tech_tree_data = json.load(f)
                            technologies = tech_tree_data.get('technologies', [])

                            # Find the current research node
                            current_tech = None
                            for tech in technologies:
                                if tech.get('id') == current_research_id:
                                    current_tech = tech
                                    break

                            if current_tech:
                                tech_cost = current_tech.get('cost', 999)
                                game_state.technology['research_progress'] += science_income

                                print(f"  📖 Researching '{current_tech['name']}': {game_state.technology['research_progress']}/{tech_cost}")

                                if game_state.technology['research_progress'] >= tech_cost:
                                    # Technology unlocked!
                                    tech_name = current_tech['name']
                                    print(f"  ✨ TECHNOLOGY UNLOCKED: {tech_name}!")

                                    # Add to discoveries if not already present
                                    if tech_name not in game_state.technology.get('discoveries', []):
                                        game_state.technology['discoveries'].append(tech_name)

                                    # Clear current research
                                    game_state.technology['current_research_id'] = None
                                    game_state.technology['research_progress'] = 0

                                    # Add to outcome for visibility
                                    outcome['tech_unlocked'] = tech_name
                except Exception as e:
                    print(f"  ⚠️ Error processing tech progression: {e}")

        # Apply culture progression
        if culture_income > 0:
            # Initialize culture_points if not present (backwards compatibility)
            if 'culture_points' not in game_state.culture:
                game_state.culture['culture_points'] = 0

            game_state.culture['culture_points'] += culture_income
            print(f"  🎭 Culture: +{culture_income} points (Total: {game_state.culture['culture_points']})")

            current_civic_id = game_state.culture.get('current_civic_id')
            if current_civic_id:
                # For MVP, use a placeholder cost since civics tree doesn't exist yet
                # In future, this will load from data/civics_tree.json
                civic_cost = 30  # Placeholder cost for test civic
                civic_name = "Tribal Code"  # Placeholder name

                game_state.culture['civic_progress'] += culture_income

                print(f"  📜 Adopting '{civic_name}': {game_state.culture['civic_progress']}/{civic_cost}")

                if game_state.culture['civic_progress'] >= civic_cost:
                    # Civic unlocked!
                    print(f"  ✨ CIVIC ADOPTED: {civic_name}!")

                    # Add to traditions if not already present
                    if civic_name not in game_state.culture.get('traditions', []):
                        game_state.culture['traditions'].append(civic_name)

                    # Clear current civic
                    game_state.culture['current_civic_id'] = None
                    game_state.culture['civic_progress'] = 0

                    # Add to outcome for visibility
                    outcome['civic_adopted'] = civic_name

        return outcome
    except Exception as e:
        print(f"!!!!!!!!!! STATE UPDATE ERROR !!!!!!!!!!!\n{e}")
        return {"narrative": f"A critical error occurred while applying updates: {e}", "updates": {}, "status": "error"}

def generate_interpretation_event(completed_item):
    """
    Generates a special "Interpretation Event" when a new technology or civic is discovered.
    This event prompts the player to decide how to apply the new discovery.
    """
    item_name = completed_item.get("name", "a new discovery")
    item_description = completed_item.get("description", "a significant breakthrough")

    # This prompt is sent to an AI to generate the event details.
    # For now, we are just constructing the prompt and returning a placeholder.
    prompt = f"""
You are the master storyteller for a civilization simulation game.
The player's civilization has just discovered "{item_name}": {item_description}.

<TASK>
Generate a special "Interpretation Event" to reflect this discovery. The event should offer the player a choice on how to interpret and apply this new knowledge.

The event must include:
1.  A `title`: A short, evocative title related to the discovery (e.g., "The Iron Age Dawns," "A New Philosophy").
2.  A `narrative`: 2-3 sentences describing the breakthrough and the new possibilities it opens up for the civilization.
3.  `decision_options`: 2-3 distinct strategic choices for how to apply "{item_name}". Each option should represent a different focus.

<EXAMPLE for "Iron Working">
{{
  "title": "The Age of Iron",
  "narrative": "Our blacksmiths have unlocked the secrets of iron, a metal far stronger than bronze. This discovery could reshape our society, from the tools in our fields to the swords in our soldiers' hands. How shall we direct this newfound power?",
  "decision_options": [
    "Focus on military tools (Forge superior weapons and armor)",
    "Develop agricultural implements (Create better plows and tools for farming)",
    "Promote artisan metalworking (Encourage the creation of iron goods and crafts)"
  ]
}}
</EXAMPLE>

<YOUR_TASK>
Now, generate a similar event for the discovery of "{item_name}".

Output ONLY valid JSON with the fields: "title", "narrative", and "decision_options".
"""

    # In a real implementation, we would call the AI model here with the prompt.
    # For now, we return a placeholder.
    print(f"--- Interpretation Event prompt generated for: {item_name} ---")
    # print(prompt) # Uncomment for debugging the prompt

    return {
        "title": f"The Dawn of {item_name}",
        "narrative": f"The discovery of {item_name} has unlocked new potential for our civilization. Now we must decide how to best utilize this knowledge.",
        "decision_options": []
    }

def _check_faction_goals(game_state, outcome, action='', event_title=''):
    """
    Analyzes turn outcome against faction goals and updates approval.
    Passive faction simulation - factions react to turn outcomes based on their goals.

    Args:
        game_state: Current game state with faction_manager
        outcome: Dictionary with 'updates' and 'narrative' from process_player_action
        action: Player action string
        event_title: Event title string
    """
    # Extract updates from outcome
    updates = outcome.get('updates', {})
    if not updates:
        return  # No changes to evaluate

    # Get event context for richer analysis
    event_action = action
    event_narrative = outcome.get('narrative', '')

    print("--- Checking Faction Goals Against Turn Outcome ---")

    # Iterate through all factions
    for faction in game_state.faction_manager.get_all():
        faction_name = faction.get('name', 'Unknown Faction')
        faction_id = faction.get('id', '')
        goals = faction.get('goals', [])

        if not goals:
            continue  # Skip factions with no goals

        # Track approval changes for this faction
        approval_change = 0
        reasons = []

        # Analyze each goal against the turn outcome
        for goal in goals:
            goal_lower = goal.lower()

            # === WEALTH/TRADE/ECONOMIC GOALS ===
            if any(keyword in goal_lower for keyword in ['wealth', 'trade', 'commerce', 'merchant', 'economic', 'prosperity']):
                wealth_change = updates.get('civilization.resources.wealth', 0)
                if wealth_change > 0:
                    approval_change += 5
                    reasons.append(f"Wealth increased by {wealth_change}, advancing economic goals")
                elif wealth_change < -100:
                    approval_change -= 5
                    reasons.append(f"Wealth decreased by {abs(wealth_change)}, hindering economic goals")

            # === MILITARY/EXPANSION GOALS ===
            if any(keyword in goal_lower for keyword in ['military', 'expand', 'army', 'war', 'conquest', 'territory', 'soldiers']):
                # Check for military-related keywords in action/narrative
                military_keywords = ['attack', 'strike', 'army', 'soldiers', 'war', 'conquest', 'victory', 'defeat']
                action_lower = event_action.lower()
                narrative_lower = event_narrative.lower()

                military_success = any(kw in action_lower or kw in narrative_lower for kw in ['victory', 'conquest', 'expand'])
                military_action = any(kw in action_lower or kw in narrative_lower for kw in military_keywords)

                if military_success:
                    approval_change += 5
                    reasons.append("Military success aligns with expansion goals")
                elif military_action and 'defeat' not in narrative_lower:
                    approval_change += 3
                    reasons.append("Military action taken")

                # Population increase could indicate successful expansion
                population_change = updates.get('civilization.population', 0)
                if population_change > 100:
                    approval_change += 3
                    reasons.append("Population growth suggests successful expansion")

            # === STABILITY/PEACE/TRADITION GOALS ===
            if any(keyword in goal_lower for keyword in ['stability', 'peace', 'tradition', 'order', 'maintain']):
                population_change = updates.get('civilization.population', 0)
                if population_change < -50:
                    approval_change -= 5
                    reasons.append("Population loss threatens stability")
                elif population_change > 0:
                    approval_change += 3
                    reasons.append("Population stability maintained")

                # Check for new traditions added
                if any('culture.traditions.append' in key for key in updates.keys()):
                    approval_change += 5
                    reasons.append("New traditions preserve cultural heritage")

            # === RELIGIOUS/FAITH GOALS ===
            if any(keyword in goal_lower for keyword in ['faith', 'temple', 'divine', 'prayer', 'religion', 'spiritual']):
                # Check for religious infrastructure or practices
                religious_building = any('temple' in str(updates.get(key, '')).lower() for key in updates.keys() if 'infrastructure.append' in key)
                religious_practice = any('religion.practices.append' in key for key in updates.keys())

                if religious_building:
                    approval_change += 5
                    reasons.append("Religious construction advances faith")
                if religious_practice:
                    approval_change += 5
                    reasons.append("New religious practices strengthen devotion")

            # === CULTURAL/ARTISTIC GOALS ===
            if any(keyword in goal_lower for keyword in ['culture', 'art', 'tradition', 'heritage']):
                # Check for cultural developments
                if any('culture.' in key for key in updates.keys()):
                    approval_change += 3
                    reasons.append("Cultural development aligns with goals")

            # === SCIENTIFIC/KNOWLEDGE GOALS ===
            if any(keyword in goal_lower for keyword in ['knowledge', 'research', 'scholar', 'discovery', 'science']):
                # Check for technology discoveries
                if any('technology.discoveries.append' in key for key in updates.keys()):
                    approval_change += 5
                    reasons.append("New discoveries advance knowledge")

        # Apply approval changes if any
        if approval_change != 0:
            success = game_state.faction_manager.update_approval(faction_name, approval_change)
            if success:
                # Add history entry
                reason_text = "; ".join(reasons) if reasons else "Turn outcome affected faction goals"
                game_state.faction_manager.add_history_entry(
                    faction_name,
                    reason_text,
                    approval_change,
                    game_state.turn_number
                )
                print(f"  📊 {faction_name}: {approval_change:+d} approval ({reason_text[:60]}...)")
            else:
                print(f"  ⚠️ Failed to update approval for {faction_name}")

    print("--- Faction Goal Check Complete ---")

def _generate_decree_title(major_declaration):
    """Generate a suitable title for a decree based on the declaration"""
    title = major_declaration.get('event_title', 'Unknown Event')
    action_text = major_declaration.get('action_text', '')

    # Try to extract a pithy title from the action
    action_lower = action_text.lower()

    # Common patterns
    if 'women' in action_lower and ('dominate' in action_lower or 'supreme' in action_lower or 'greater' in action_lower):
        return "The Divine Mandate of Female Supremacy"
    elif 'men' in action_lower and ('dominate' in action_lower or 'supreme' in action_lower):
        return "The Patriarchal Decree"
    elif 'holy law' in action_lower or 'divine law' in action_lower:
        # Extract first few words after "holy law" or similar
        return f"Holy Law of {title.split()[-2]} {title.split()[-1]}"
    elif 'constitution' in action_lower:
        return f"The Constitutional Reforms of {title}"
    elif 'decree' in action_lower or 'mandate' in action_lower:
        # Use the event title
        return f"The {title} Decree"
    else:
        # Default: use event title
        return f"The {title} Proclamation"

def _infer_decree_effects(major_declaration, game_state):
    """
    Infer the effects of a decree from its text and context

    Args:
        major_declaration: Dict with type, importance, action_text
        game_state: Current game state

    Returns:
        Dict of effects to apply
    """
    action_text = major_declaration.get('action_text', '').lower()
    decree_type = major_declaration.get('type', 'cultural')

    effects = {}

    # Social structure changes
    if 'matriarch' in action_text or ('women' in action_text and 'dominate' in action_text):
        effects['social_structure'] = 'matriarchy'
        effects['governance_structure'] = 'matriarchal_theocracy' if decree_type == 'holy_law' else 'matriarchy'
    elif 'patriarch' in action_text or ('men' in action_text and 'dominate' in action_text):
        effects['social_structure'] = 'patriarchy'
        effects['governance_structure'] = 'patriarchal_theocracy' if decree_type == 'holy_law' else 'patriarchy'
    elif 'democracy' in action_text or 'equal voice' in action_text:
        effects['governance_structure'] = 'democracy'
    elif 'theocra' in action_text or 'priest' in action_text and 'rule' in action_text:
        effects['governance_structure'] = 'theocracy'

    # Military composition
    if 'women' in action_text and ('army' in action_text or 'military' in action_text or 'soldier' in action_text):
        effects['military_composition'] = 'female_dominated'
    elif 'men' in action_text and ('army' in action_text or 'military' in action_text):
        effects['military_composition'] = 'male_dominated'

    # Property rights
    if 'women' in action_text and ('property' in action_text or 'own' in action_text):
        effects['property_rights'] = 'female_only'
    elif 'men' in action_text and ('property' in action_text or 'own' in action_text):
        effects['property_rights'] = 'male_only'
    elif 'equal' in action_text and 'property' in action_text:
        effects['property_rights'] = 'equal'

    # Cultural values (infer from text)
    cultural_values = []
    if 'divine' in action_text or 'sacred' in action_text or 'holy' in action_text:
        if 'women' in action_text:
            cultural_values.append('Female Divinity')
        elif 'men' in action_text:
            cultural_values.append('Male Divinity')
        cultural_values.append('Religious Authority')

    if 'martial' in action_text or 'warrior' in action_text or 'military training' in action_text:
        if 'women' in action_text:
            cultural_values.append('Martial Women')
        else:
            cultural_values.append('Warrior Culture')

    if 'hierarchy' in action_text or 'greater' in action_text or 'dominate' in action_text:
        cultural_values.append('Gender Hierarchy' if 'women' in action_text or 'men' in action_text else 'Social Hierarchy')

    if 'knowledge' in action_text or 'wisdom' in action_text or 'scholar' in action_text:
        cultural_values.append('Pursuit of Knowledge')

    if cultural_values:
        effects['cultural_values'] = cultural_values

    # Taboos (infer opposites)
    taboos = []
    if 'women' in action_text and 'dominate' in action_text:
        taboos.extend(['Male Leadership', 'Gender Equality', 'Male Property Ownership'])
    elif 'men' in action_text and 'dominate' in action_text:
        taboos.extend(['Female Leadership', 'Gender Equality', 'Female Property Ownership'])

    if 'forbidden' in action_text or 'banned' in action_text or 'illegal' in action_text:
        # Try to extract what's forbidden
        if 'dissent' in action_text or 'opposition' in action_text:
            taboos.append('Political Dissent')

    if taboos:
        effects['taboos'] = taboos

    # Traditions
    traditions = []
    if 'women' in action_text and 'army' in action_text and 'training' in action_text:
        traditions.append('Universal Female Military Training')
    if 'women' in action_text and 'police' in action_text:
        traditions.append('Female Police Force')
    if 'matriarch' in action_text and 'succession' in action_text:
        traditions.append('Matriarchal Succession')
    elif 'patriarch' in action_text and 'succession' in action_text:
        traditions.append('Patriarchal Succession')

    if traditions:
        effects['traditions'] = traditions

    # Religious effects (for holy laws)
    if decree_type == 'holy_law':
        religious_effects = {}

        # Divine authority
        religious_effects['divine_authority'] = game_state.religion.get('primary_deity', 'The Divine')

        # Core tenets
        core_tenets = []
        if 'women' in action_text and 'dominate' in action_text:
            core_tenets.append('Women are divinely ordained to rule')
            core_tenets.append('Male subordination is sacred law')
        elif 'men' in action_text and 'dominate' in action_text:
            core_tenets.append('Men are divinely ordained to rule')
            core_tenets.append('Female subordination is sacred law')

        if core_tenets:
            religious_effects['core_tenets'] = core_tenets

        # Practices
        practices = []
        if 'women' in action_text and ('priest' in action_text or 'temple' in action_text):
            practices.append('Female-only priesthood')
        if 'hierarchy' in action_text:
            practices.append('Ritual enforcement of gender hierarchy')

        if practices:
            religious_effects['practices'] = practices

        if religious_effects:
            effects['religious_effects'] = religious_effects

    return effects
