# engines/event_generator.py
"""
Event Generator Module

This module handles all event generation logic for the civilization game.
It generates initial events and subsequent event stages based on player interactions.

Refactored from event_engine.py for better maintainability and separation of concerns.
"""

import google.generativeai as genai
import json
from json import JSONDecodeError
import time
from engines.context_builder import build_event_context
from engines.tendency_analyzer import analyze_player_tendency, get_tendency_description
from model_config import TEXT_MODEL
from engines.prompt_loader import load_prompt

def api_call_with_retry(func, max_retries=3, initial_delay=1.0):
    """
    Wrapper for API calls with exponential backoff retry logic.

    Args:
        func: Callable that makes the API call
        max_retries: Maximum number of retry attempts
        initial_delay: Initial delay in seconds (doubles on each retry)

    Returns:
        API response or raises last exception
    """
    for attempt in range(max_retries):
        try:
            return func()
        except Exception as e:
            error_msg = str(e).lower()

            # Check for specific error types
            is_rate_limit = 'rate limit' in error_msg or 'quota' in error_msg
            is_auth_error = 'oauth' in error_msg or 'token' in error_msg or 'authentication' in error_msg or '401' in error_msg
            is_network_error = 'network' in error_msg or 'timeout' in error_msg or 'connection' in error_msg

            # Don't retry auth errors - they need user intervention
            if is_auth_error:
                print(f"⚠️ AUTHENTICATION ERROR: {e}")
                print("   Your API credentials may have expired. Please check your GEMINI_API_KEY.")
                raise

            # Last attempt - raise the error
            if attempt == max_retries - 1:
                print(f"⚠️ API call failed after {max_retries} attempts: {e}")
                raise

            # Calculate delay with exponential backoff
            delay = initial_delay * (2 ** attempt)

            # Add extra delay for rate limiting
            if is_rate_limit:
                delay *= 3
                print(f"⏳ Rate limit hit. Waiting {delay:.1f}s before retry {attempt + 2}/{max_retries}...")
            elif is_network_error:
                print(f"🌐 Network error. Retrying in {delay:.1f}s (attempt {attempt + 2}/{max_retries})...")
            else:
                print(f"🔄 API error. Retrying in {delay:.1f}s (attempt {attempt + 2}/{max_retries})...")

            time.sleep(delay)

    # Should never reach here, but just in case
    raise Exception("API call failed after all retries")

def generate_event(game_state):
    """Generates a contextually appropriate event with multi-stage interaction design."""
    # Priority 0: First Turn Council Briefing (one-time event)
    if game_state.turn_number == 0:
        print("--- Triggering First Turn Council Briefing ---")
        from engines.council_engine import generate_first_turn_briefing
        return generate_first_turn_briefing(game_state)

    # Check for other special, turn-based events
    # Council meetings: every 7 turns (7, 14, 21, 28...)
    # Faction audiences: every 4 turns (4, 8, 12, 16...)
    # Building events: every 5 turns (5, 10, 15, 20...)
    # These intervals don't heavily overlap, minimizing event collisions
    if game_state.turn_number > 0 and game_state.turn_number % 7 == 0:
        print("--- Triggering Council Meeting Event ---")
        from engines.council_engine import generate_council_meeting
        return generate_council_meeting(game_state)
    elif game_state.turn_number > 0 and game_state.turn_number % 4 == 0:
        print("--- Triggering Faction Audience Event ---")
        from engines.faction_engine import generate_faction_audience
        return generate_faction_audience(game_state)
    elif game_state.turn_number > 0 and game_state.turn_number % 5 == 0:
        print("--- Triggering Building Event ---")
        from engines.building_event_engine import generate_building_event
        return generate_building_event(game_state)

    # Priority 1: Check for crisis events (highest priority)
    from engines.crisis_engine import should_generate_crisis, generate_crisis_event

    is_crisis, crisis_type = should_generate_crisis(game_state)
    if is_crisis:
        print(f"🚨 CRISIS DETECTED: {crisis_type.upper()} - Generating crisis event")
        event_data = generate_crisis_event(game_state, crisis_type)

        # Apply crisis updates immediately if present
        if "updates" in event_data and event_data["updates"]:
            from engines.state_validator import validate_updates
            from engines.state_updater import apply_updates
            is_valid, cleaned_updates, errors = validate_updates(event_data["updates"], game_state)

            if errors:
                print(f"--- Crisis Update Validation Warnings ---")
                for error in errors:
                    print(f"  - {error}")

            if cleaned_updates:
                print("--- Applying Crisis Mechanical Consequences ---")
                apply_updates(game_state, cleaned_updates)
            else:
                print("--- No valid crisis updates to apply ---")

        # Initialize event state
        game_state.current_event = event_data
        game_state.event_stage = 0
        game_state.event_conversation = []
        return event_data
    else:
        # Debug logging for crisis detection
        pop = game_state.civilization['population']
        food = game_state.civilization['resources']['food']
        wealth = game_state.civilization['resources']['wealth']
        food_pc = food / max(pop, 1)
        print(f"--- Crisis check: pop={pop}, food={food} ({food_pc:.2f} per capita), wealth={wealth} - No crisis ---")

    # Priority 2: Check for callback events (past consequences return)
    from engines.consequence_engine import check_for_callback_opportunity
    from engines.callback_engine import generate_callback_event

    has_callback, callback_type, callback_data = check_for_callback_opportunity(game_state)
    if has_callback:
        print(f"📜 CALLBACK EVENT: {callback_type} - Generating consequence event")
        event_data = generate_callback_event(game_state, callback_type, callback_data)
        # Initialize event state
        game_state.current_event = event_data
        game_state.event_stage = 0
        game_state.event_conversation = []
        return event_data

    # Priority 3: Generate normal event
    print("--- Generating new multi-stage event via Gemini API ---")
    model = genai.GenerativeModel(TEXT_MODEL)

    # Build optimized context (60% token reduction)
    context = build_event_context(game_state)

    # Enhanced tendency analysis
    primary_tendency, secondary_tendency = analyze_player_tendency(game_state.history_long)
    tendency_desc = get_tendency_description(primary_tendency, secondary_tendency)
    print(f"--- Player Tendency: {primary_tendency.upper()} (secondary: {secondary_tendency}) ---")

    # Get leader traits and event tags
    from engines.leader_engine import get_leader_event_tags, TRAIT_EFFECTS

    leader_tags = get_leader_event_tags(context['civilization']['leader'])
    trait_descriptions = []
    leader_traits = context['civilization']['leader'].get('traits', [])
    for trait in leader_traits:
        trait_data = TRAIT_EFFECTS.get(trait, {})
        if trait_data:
            trait_descriptions.append(f"{trait} ({trait_data.get('description', '')})")

    # Get last event for consequence chaining
    from engines.context_builder import get_last_event_summary, get_recent_event_titles
    last_event = get_last_event_summary(game_state.history_long)

    # Get recent event titles to avoid repetition
    recent_titles = get_recent_event_titles(game_state.history_long, num=4)

    # DEBUG: Log and handle active_policy
    print(f"--- DEBUG: Active policy before event generation: {game_state.active_policy} ---")
    active_policy_str = game_state.active_policy or "general_governance"
    active_policy_display = active_policy_str.replace('_', ' ').title()


    # Enhanced prompt for multi-stage events
    # Contextualize resource levels for AI
    pop = context['civilization']['population']
    food = context['civilization']['resources']['food']
    wealth = context['civilization']['resources']['wealth']
    happiness = game_state.population_happiness

    # Add contextual qualifiers to stats
    food_per_capita = food / max(pop, 1)
    if food_per_capita < 0.5:
        food_context = "critically low - starvation looms"
    elif food_per_capita < 1.0:
        food_context = "dangerously low for this population"
    elif food_per_capita < 2.0:
        food_context = "adequate but tight"
    else:
        food_context = "abundant stockpiles"

    if wealth < 100:
        wealth_context = "nearly bankrupt"
    elif wealth < 500:
        wealth_context = "meager reserves"
    elif wealth < 2000:
        wealth_context = "moderate treasury"
    else:
        wealth_context = "overflowing coffers"

    if happiness < 40:
        happiness_context = "widespread discontent and unrest"
    elif happiness < 60:
        happiness_context = "simmering tensions among the populace"
    elif happiness < 80:
        happiness_context = "cautious contentment"
    else:
        happiness_context = "joyous and thriving populace"

    # Add leader age context
    leader_age = context['civilization']['leader']['age']
    life_exp = context['civilization']['leader'].get('life_expectancy', 60)
    if leader_age > life_exp + 10:
        age_context = f"ancient and frail (far beyond the expected {life_exp} years)"
    elif leader_age > life_exp:
        age_context = f"elderly and weathered (past the expected {life_exp} years)"
    elif leader_age > life_exp - 10:
        age_context = "aging but still vigorous"
    elif leader_age < 30:
        age_context = "young and inexperienced"
    else:
        age_context = "in their prime"

    # Pre-calculate all formatted values and strings for the prompt
    pop_formatted = f"{pop:,}"
    food_formatted = f"{food:,}"
    wealth_formatted = f"{wealth:,}"
    happiness_formatted = f"{happiness:.1f}"
    trait_descriptions_str = ', '.join(trait_descriptions) if trait_descriptions else 'No special traits'
    culture_values_str = ', '.join(context['culture']['values'][:5])
    recent_discoveries_str = ', '.join(context['technology']['recent_discoveries'][-3:])
    recent_infrastructure_str = ', '.join(context['technology']['infrastructure'][-3:])
    leader_traits_str = ', '.join(context['civilization']['leader']['traits'])
    leader_tags_str = ', '.join(leader_tags[:5]) if leader_tags else 'General'
    recent_titles_str = ', '.join(recent_titles)
    infrastructure_recent_str = ', '.join(context['technology']['infrastructure'][-2:]) if context['technology']['infrastructure'] else 'none yet'
    primary_value = context['culture']['values'][0] if context['culture']['values'] else 'survival'

    # Format last_event as string
    if last_event:
        last_event_str = f"Previous event: '{last_event['title']}' - Player chose to '{last_event['action']}'. Result: {last_event['outcome']}"
    else:
        last_event_str = "This is the first event."

    # Load prompt template and fill in variables
    prompt_template = load_prompt('events/generate_event')
    prompt = prompt_template.format(
        era=context['civilization']['meta']['era'],
        civ_name=context['civilization']['meta']['name'],
        year=context['civilization']['meta']['year'],
        leader_name=context['civilization']['leader']['name'],
        leader_age=leader_age,
        age_context=age_context,
        trait_descriptions=trait_descriptions_str,
        population=pop_formatted,
        happiness=happiness_formatted,
        happiness_context=happiness_context,
        food=food_formatted,
        food_context=food_context,
        wealth=wealth_formatted,
        wealth_context=wealth_context,
        active_policy_display=active_policy_display,
        tech_tier=context['civilization']['resources']['tech_tier'],
        terrain=context['world']['geography']['terrain'],
        climate=context['world']['geography']['climate'],
        culture_values=culture_values_str,
        religion_name=context['religion']['name'],
        religion_type=context['religion']['type'],
        religion_influence=context['religion']['influence'],
        recent_discoveries=recent_discoveries_str,
        recent_infrastructure=recent_infrastructure_str,
        leader_traits=leader_traits_str,
        leader_tags=leader_tags_str,
        tendency_desc=tendency_desc,
        recent_titles=recent_titles_str,
        last_event=last_event_str,
        infrastructure_recent=infrastructure_recent_str,
        primary_value=primary_value
    )

    try:
        response = model.generate_content(
            prompt,
            generation_config={
                "response_mime_type": "application/json",
                "temperature": 0.9,
                "top_p": 0.95
            }
        )
        event_data = json.loads(response.text)

        # Add event type to title
        if 'title' in event_data:
            event_data['title'] = event_data['title'] + " -- Event"

        print(f"--- Event '{event_data.get('title', 'Unknown')}' successfully generated (Stage 0) ---")

        # Initialize event state
        game_state.current_event = event_data
        game_state.event_stage = 0
        game_state.event_conversation = []

        return event_data
    except JSONDecodeError as e:
        print(f"!!!!!!!!!! JSON PARSING ERROR !!!!!!!!!!!\nFailed to parse AI response: {e}")
        print(f"Raw response: {response.text if 'response' in locals() else 'No response'}")
        return {
            "title": "A Moment of Confusion -- Event",
            "narrative": "The spirits spoke in riddles that could not be understood. The chronicler needs to rest.",
            "suggested_actions": ["Wait for clarity", "Try again", "Check the server console"]
        }
    except Exception as e:
        error_msg = str(e)
        print(f"!!!!!!!!!! GEMINI API ERROR !!!!!!!!!!!\nError generating event: {e}")

        if "404" in error_msg or "not found" in error_msg.lower():
            print("NOTE: The AI model may not be available. Check your GEMINI_API_KEY and model name.")
        elif "quota" in error_msg.lower() or "rate limit" in error_msg.lower():
            print("NOTE: API quota exceeded. Please wait a moment before trying again.")
        elif "permission" in error_msg.lower() or "forbidden" in error_msg.lower():
            print("NOTE: API key may not have permission to use this model.")

        return {
            "title": "A Moment of Silence -- Event",
            "narrative": "The spirits are quiet, and the world feels still. An error prevented a new story from unfolding.",
            "suggested_actions": ["Wait for a sign", "Check the server console", "Restart the simulation", "Try a different approach"]
        }

def generate_event_stage(game_state, player_response):
    """Generates the next stage of an event based on player's investigation/question."""
    print(f"--- Generating event stage {game_state.event_stage + 1} based on '{player_response}' ---")
    model = genai.GenerativeModel(TEXT_MODEL)

    context = build_event_context(game_state)

    # Check if this is a council meeting
    is_council = game_state.current_event.get('event_type') == 'council_meeting'

    # Build conversation history
    conversation_history = "\n".join([
        f"Player: {entry['player']}\nResponse: {entry['ai']}"
        for entry in game_state.event_conversation
    ])

    # Contextualize resources for stage generation
    pop = context['civilization']['population']
    food = context['civilization']['resources']['food']
    wealth = context['civilization']['resources']['wealth']
    food_per_capita = food / max(pop, 1)

    if food_per_capita < 1.0:
        resource_mood = "hunger gnaws at the people's resolve"
    elif wealth < 100:
        resource_mood = "empty coffers weigh on every decision"
    elif food_per_capita > 3.0 and wealth > 2000:
        resource_mood = "prosperity emboldens the populace"
    else:
        resource_mood = "cautious stability prevails"

    if is_council:
        # COUNCIL MEETING: Conversational dialogue format
        advisor_stances = game_state.current_event.get('advisor_stances', [])
        advisor_list = "\n".join([
            f"- {a['name']} ({a['role']}): {a['position']}"
            for a in advisor_stances
        ])

        # Pre-calculate values for prompt
        central_dilemma = game_state.current_event.get('central_dilemma', 'Strategic decision needed')
        conversation_history_str = conversation_history if conversation_history else "This is the first question."

        # Load prompt template and fill in variables
        prompt_template = load_prompt('events/generate_event_stage_council')
        prompt = prompt_template.format(
            central_dilemma=central_dilemma,
            advisor_list=advisor_list,
            conversation_history=conversation_history_str,
            player_response=player_response
        )
    else:
        # NON-COUNCIL EVENTS: Keep existing narrative format
        # Pre-calculate values for prompt
        event_title = game_state.current_event['title']
        event_narrative = game_state.current_event['narrative']
        current_stage = game_state.event_stage + 1
        leader_name = context['civilization']['leader']['name']
        leader_age = context['civilization']['leader']['age']
        population_formatted = f"{pop:,}"
        food_formatted = f"{food:,}"
        wealth_formatted = f"{wealth:,}"
        tech_tier = context['civilization']['resources']['tech_tier']
        culture_values_str = ', '.join(context['culture']['values'][:5])
        religion_name = context['religion']['name']
        religion_influence = context['religion']['influence']
        conversation_history_str = conversation_history if conversation_history else "This is the first interaction."

        # Load prompt template and fill in variables
        prompt_template = load_prompt('events/generate_event_stage_regular')
        prompt = prompt_template.format(
            event_title=event_title,
            event_narrative=event_narrative,
            current_stage=current_stage,
            leader_name=leader_name,
            leader_age=leader_age,
            population=population_formatted,
            resource_mood=resource_mood,
            food=food_formatted,
            wealth=wealth_formatted,
            tech_tier=tech_tier,
            culture_values=culture_values_str,
            religion_name=religion_name,
            religion_influence=religion_influence,
            conversation_history=conversation_history_str,
            player_response=player_response
        )

    # Hard stage limit check
    if game_state.event_stage >= 6:
        print(f"--- Stage limit reached ({game_state.event_stage + 1}) ---")
        return {
            "narrative": "You've investigated thoroughly. The information swirls in your mind as you consider your options.",
            "investigation_options": [
                "Reflect on all you've learned one more time",
                "Seek final counsel from your closest advisor"
            ],
            "decision_options": [
                "Make the best decision with what you know",
                "Trust your instincts and act decisively"
            ]
        }

    try:
        response = model.generate_content(
            prompt,
            generation_config={
                "response_mime_type": "application/json",
                "temperature": 0.8
            }
        )
        stage_data = json.loads(response.text)

        print(f"--- Event stage {game_state.event_stage + 1} successfully generated ---")

        # Update event state
        # For council meetings, extract dialogue; for others, use narrative
        if is_council and "response" in stage_data:
            speaker = stage_data["response"].get("speaker", "Advisor")
            dialogue = stage_data["response"].get("dialogue", "...")
            ai_response = f"{speaker}: {dialogue}"

            # Add interjections if present
            if "interjections" in stage_data and stage_data["interjections"]:
                for interj in stage_data["interjections"]:
                    ai_response += f"\n{interj.get('speaker', 'Advisor')}: {interj.get('dialogue', '...')}"

            # Ensure narrative field exists at top level for frontend compatibility
            stage_data["narrative"] = ai_response
        else:
            ai_response = stage_data.get("narrative", "...")

        game_state.event_conversation.append({
            "player": player_response,
            "ai": ai_response
        })
        game_state.event_stage += 1

        # Validate we have all required fields
        if "investigation_options" not in stage_data or len(stage_data.get("investigation_options", [])) < 2:
            print("WARNING: Missing investigation_options. Adding fallback.")
            stage_data["investigation_options"] = [
                "Ask for more details",
                "Seek another perspective"
            ]

        if "decision_options" not in stage_data or len(stage_data.get("decision_options", [])) < 2:
            print("WARNING: Missing decision_options. Adding fallback.")
            stage_data["decision_options"] = [
                "Make a cautious decision",
                "Act boldly on current information"
            ]

        return stage_data
    except JSONDecodeError as e:
        print(f"!!!!!!!!!! JSON PARSING ERROR (Event Stage) !!!!!!!!!!!\n{e}")
        print(f"Raw response: {response.text if 'response' in locals() else 'No response'}")
        return {
            "narrative": "The situation grows unclear as you ponder your next move.",
            "investigation_options": ["Try a different approach", "Ask something else"],
            "decision_options": ["Proceed cautiously", "Act boldly"]
        }
    except Exception as e:
        print(f"!!!!!!!!!! GEMINI API ERROR (Event Stage) !!!!!!!!!!!\n{e}")
        return {
            "narrative": "An error clouds your vision, but you must continue.",
            "investigation_options": ["Try again", "Ask differently"],
            "decision_options": ["Trust your judgment", "Act with caution"]
        }

