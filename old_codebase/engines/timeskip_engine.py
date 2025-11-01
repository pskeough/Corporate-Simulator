# engines/timeskip_engine.py
import google.generativeai as genai
import json
from json import JSONDecodeError
import re
from engines.image_engine import generate_settlement_image
from engines.context_builder import build_timeskip_context
from engines.tendency_analyzer import analyze_player_tendency, get_tendency_description
from engines.state_validator import validate_updates
from engines.state_updater import apply_updates, calculate_life_expectancy
from engines.prompt_loader import load_prompt
from model_config import TIMESKIP_MODEL

def perform_timeskip(game_state):
    """
    Performs a ~500 year timeskip by calling the Gemini API to generate
    a narrative and a set of impactful game state updates.
    Optimized for faster response by deferring image generation.
    Integrates permanent decrees and their evolution over time.
    """
    print("--- Performing 500-Year Timeskip via Gemini API ---")
    model = genai.GenerativeModel(TIMESKIP_MODEL)

    # Build expanded context for 500-year jump (12 events)
    context = build_timeskip_context(game_state)

    # Analyze trajectory
    primary_tendency, secondary_tendency = analyze_player_tendency(game_state.history_long, num_events=10)
    tendency_desc = get_tendency_description(primary_tendency, secondary_tendency)
    print(f"--- Civilization Trajectory: {tendency_desc} ---")

    # Get permanent decrees summary for AI context
    from engines.law_engine import LawEngine
    law_engine = LawEngine(game_state)
    decrees_summary = law_engine.get_all_decrees_summary()
    print(f"--- Active Permanent Decrees: {len(law_engine.get_active_decrees())} ---")

    # Extract key narrative elements from player's history
    recent_events = context['recent_history']['events'][-8:]
    event_themes = [e.get('title', 'Unknown') for e in recent_events]

    # Determine dominant cultural values that should continue
    primary_values = ', '.join(context['culture']['values'][:3]) if context['culture']['values'] else 'survival and strength'

    prompt = load_prompt('timeskip/timeskip_500_years').format(
        civ_name=context['civilization']['meta']['name'],
        civ_year=context['civilization']['meta']['year'],
        civ_era=context['civilization']['meta']['era'],
        founding_leader_name=context['civilization']['leader']['name'],
        leader_age=context['civilization']['leader']['age'],
        population=f"{context['civilization']['population']:,}",
        food=f"{context['civilization']['resources']['food']:,}",
        wealth=f"{context['civilization']['resources']['wealth']:,}",
        tech_tier=context['civilization']['resources']['tech_tier'],
        primary_values=primary_values,
        religion_name=context['religion']['name'],
        religion_influence=context['religion']['influence'],
        primary_tendency=primary_tendency,
        tendency_desc=tendency_desc,
        event_themes='\n'.join([f"• {title}" for title in event_themes]),
        decrees_summary=decrees_summary
    )

    try:
        response = model.generate_content(
            prompt,
            generation_config={
                "response_mime_type": "application/json",
                "temperature": 0.7  # Reduced for faster, more focused generation
            }
        )
        outcome = json.loads(response.text)
        print(f"--- Gemini Timeskip Outcome Received ---\n{json.dumps(outcome, indent=2)}\n-----------------------------")

        # Process decree evolution over 500 years
        print("--- Processing Decree Evolution ---")
        decree_results = law_engine.process_timeskip(years_passed=500)

        # Add decree narratives to the outcome if they exist
        if decree_results['decree_narratives']:
            print(f"  • {len(decree_results['evolved_decrees'])} decrees evolved")
            if decree_results['defunct_decrees']:
                print(f"  • {len(decree_results['defunct_decrees'])} decrees became defunct")
            if decree_results['new_schisms']:
                print(f"  • {len(decree_results['new_schisms'])} religious schisms occurred")

        # Enforce active decrees on current state
        law_engine.enforce_active_decrees()
        print("--- Active decrees enforced on civilization state ---")

        # Generate settlement evolution image (shows civilization progress)
        try:
            from engines.visual_engine import generate_settlement_evolution
            year = outcome.get('updates', {}).get('civilization.meta.year', 0)
            print("--- Generating settlement evolution image ---")
            import threading
            threading.Thread(
                target=generate_settlement_evolution,
                args=(game_state, year),
                daemon=True
            ).start()
        except Exception as img_error:
            print(f"Note: Settlement evolution image generation skipped: {img_error}")

        return outcome
    except JSONDecodeError as e:
        print(f"!!!!!!!!!! JSON PARSING ERROR (Timeskip) !!!!!!!!!!!\nFailed to parse AI response: {e}")
        print(f"Raw response: {response.text if 'response' in locals() else 'No response'}")
        return {
            "narrative": "The chronicler's records have become muddled. Five centuries pass, but the details are unclear.",
            "updates": {"civilization.meta.year": 500}
        }
    except Exception as e:
        error_msg = str(e)
        print(f"!!!!!!!!!! GEMINI API ERROR (Timeskip) !!!!!!!!!!!\n{e}")

        # Provide specific guidance for common errors
        if "404" in error_msg or "not found" in error_msg.lower():
            print("NOTE: The AI model may not be available. Check your GEMINI_API_KEY and model name.")
            print("SUGGESTION: Update the model name in timeskip_engine.py line 15 to 'gemini-1.5-flash' or another available model.")
        elif "quota" in error_msg.lower() or "rate limit" in error_msg.lower():
            print("NOTE: API quota exceeded. Please wait before trying again.")
        elif "permission" in error_msg.lower() or "forbidden" in error_msg.lower():
            print("NOTE: API key may not have permission to use this model.")

        return {
            "narrative": "The ages blur into a confusing haze, and the thread of history is lost. (An API error occurred during the timeskip.)",
            "updates": {"civilization.meta.year": 500}
        }

