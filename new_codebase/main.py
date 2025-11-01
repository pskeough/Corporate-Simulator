import os
import json
import threading
from flask import Flask, jsonify, render_template, request
from dotenv import load_dotenv
import google.generativeai as genai

# Our custom modules
from game_state import GameState
from engines.event_generator import generate_event, generate_event_stage
from engines.action_processor import process_player_action
from engines.state_updater import apply_world_turn_updates
from engines.timeskip_engine import perform_timeskip, apply_updates as apply_timeskip_updates
from engines.world_turns_engine import WorldTurnsEngine
from engines import personnel_engine as character_engine # Use alias for compatibility
#from world_generator import WorldGenerator # World generator is not part of the corporate simulator

# --- Initialization ---
load_dotenv()
api_key = os.getenv("GEMINI_API_KEY")
if not api_key:
    print("WARNING: GEMINI_API_KEY not found in .env file. Please create a .env file with your key.")
    exit()
genai.configure(api_key=api_key)

app = Flask(__name__)

# Global game instance - will be initialized when needed
game = None
world_turns_engine = WorldTurnsEngine()

def initialize_game():
    """Initializes or reloads the game state."""
    global game
    try:
        game = GameState()
        # Reset event state
        game.current_event = None
        game.event_stage = 0
        game.event_conversation = []
        return True
    except FileNotFoundError:
        print("ERROR: Context files not found. Make sure you have the 'context' directory with all JSON files.")
        return False

# Portrait generation is part of the discarded visual engine.
# These functions are no longer needed.

# --- Web Routes ---
@app.route('/')
def index():
    """Renders the main menu."""
    return render_template('menu.html')

@app.route('/custom')
def custom_page():
    """Renders the custom world creation page."""
    return render_template('custom_world.html')

@app.route('/game')
def game_page():
    """Renders the main game interface."""
    global game
    if game is None:
        initialize_game()
    return render_template('index.html')

# --- API Routes ---
@app.route('/api/check_save')
def check_save():
    """Checks if a saved game exists and returns save info."""
    try:
        # Try to load game state to check if valid save exists
        temp_game = GameState()

        # If we can load it, extract info
        save_info = {
            "corporation_name": temp_game.corporation.get('name', 'Unknown Corp'),
            "fiscal_quarter": temp_game.simulation.get('current_fiscal_quarter', 'Q1'),
            "player_name": temp_game.player.get('name', 'Unknown'),
            "player_title": temp_game.player.get('title', 'Employee')
        }

        return jsonify({
            "has_save": True,
            "save_info": save_info
        })
    except (FileNotFoundError, json.JSONDecodeError, KeyError):
        return jsonify({
            "has_save": False
        })

@app.route('/api/new_game', methods=['POST'])
def new_game():
    """Creates a new game by resetting all context files to defaults."""
    global game
    try:
        # Initialize if needed
        if game is None:
            if not initialize_game():
                return jsonify({"status": "error", "message": "Failed to initialize game"}), 500

        # Reset to defaults
        game.reset_to_defaults()

        # Reset event state
        game.current_event = None
        game.event_stage = 0
        game.event_conversation = []

        # Visual engine components are removed. No portraits are generated.
        game.save()

        return jsonify({"status": "success"})
    except Exception as e:
        print(f"Error creating new game: {e}")
        return jsonify({"status": "error", "message": str(e)}), 500

# The custom_game route is removed as it depends on the discarded world_generator.

@app.route('/api/game_state')
def get_game_state():
    """Returns the complete current game state."""
    global game
    if game is None:
        initialize_game()
    if game is None:
        return jsonify({"status": "error", "message": "Game not initialized"}), 500

    return jsonify({
        "corporation": game.corporation,
        "player": game.player,
        "company_culture": game.company_culture,
        "corporate_mission": game.corporate_mission,
        "skills_and_assets": game.skills_and_assets,
        "market_and_competitors": game.market_and_competitors
    })

@app.route('/api/event')
def get_event():
    """Generates and returns a new event for the player."""
    global game
    if game is None:
        initialize_game()
    if game is None:
        return jsonify({"status": "error", "message": "Game not initialized"}), 500

    try:
        # The corporate simulation does not have victory or failure conditions in the same way.
        # Game over conditions might be implemented later (e.g., getting fired).
        # For now, we just generate a new event.
        event_data = generate_event(game)
        return jsonify(event_data)
    except Exception as e:
        print(f"ERROR generating event: {e}")
        return jsonify({"error": "Failed to generate event"}), 500

@app.route('/api/event_interaction', methods=['POST'])
def handle_event_interaction():
    """
    Handles mid-event interactions (investigation, questions, etc.)
    Does NOT finalize the event or apply consequences.
    """
    global game
    if game is None:
        initialize_game()
    if game is None:
        return jsonify({"status": "error", "message": "Game not initialized"}), 500

    data = request.get_json()
    player_response = data.get('response')

    if not player_response:
        return jsonify({"status": "error", "message": "Missing player response."}), 400

    if not game.current_event:
        return jsonify({"status": "error", "message": "No active event to interact with."}), 400

    print(f"--- Received event interaction: '{player_response}' (Stage {game.event_stage}) ---")

    try:
        stage_data = generate_event_stage(game, player_response)
        return jsonify({
            "status": "success",
            "stage": game.event_stage,
            "response": stage_data
        })
    except Exception as e:
        print(f"Error in event interaction: {e}")
        return jsonify({"status": "error", "message": str(e)}), 500

@app.route('/api/action', methods=['POST'])
def handle_action():
    """
    Receives a player's FINAL action, processes outcome, applies state changes,
    saves the game, and returns the narrative outcome.
    """
    global game
    if game is None:
        initialize_game()
    if game is None:
        return jsonify({"status": "error", "message": "Game not initialized"}), 500

    data = request.get_json()
    player_action = data.get('action')
    event_title = data.get('event_title')
    event_narrative = data.get('event_narrative')

    if not all([player_action, event_title, event_narrative]):
        return jsonify({"status": "error", "message": "Missing action or event context."}), 400

    print(f"--- Received FINAL action '{player_action}' for event '{event_title}' ---")

    try:
        outcome = process_player_action(game, player_action, event_title, event_narrative)

        if outcome.get("status") == "error":
            return jsonify({"status": "error", "message": outcome.get("narrative")})

        # Capture event details before resetting (for world turn analysis)
        event_type = game.current_event.get('event_type') if game.current_event else None
        conversation = list(game.event_conversation)  # Copy before clearing

        # Reset event state after resolution
        game.current_event = None
        game.event_stage = 0
        game.event_conversation = []

        # Simulate the world's reaction to the player's action
        world_updates = world_turns_engine.simulate_turn(game, {
            "action": player_action,
            "outcome": outcome,
            "event_type": event_type,
            "conversation": conversation
        })
        if world_updates:
            apply_world_turn_updates(game, world_updates)

        game.save()
        return jsonify({"status": "success", "outcome": outcome})
    except Exception as e:
        print(f"ERROR processing action: {e}")
        import traceback
        traceback.print_exc()
        return jsonify({"status": "error", "message": f"Failed to process action: {str(e)}"}), 500

@app.route('/api/timeskip', methods=['POST'])
def handle_timeskip():
    """
    Initiates a timeskip, processes the outcome, saves the game,
    and returns the narrative.
    """
    global game
    if game is None:
        initialize_game()
    if game is None:
        return jsonify({"status": "error", "message": "Game not initialized"}), 500

    print("--- Initiating Timeskip ---")

    timeskip_outcome = perform_timeskip(game)

    if "updates" in timeskip_outcome and timeskip_outcome["updates"]:
        apply_timeskip_updates(game, timeskip_outcome["updates"], is_timeskip=True)

    game.save()

    return jsonify({
        "status": "success",
        "narrative": timeskip_outcome.get("narrative", "Time marches on.")
    })

# The /api/die and /api/choose_successor routes are removed as they are part of the
# discarded succession crisis and leader mechanics.
@app.route('/api/context/company_culture')
def get_company_culture():
    """Returns the company culture context."""
    return jsonify(game.company_culture)

@app.route('/api/context/corporate_mission')
def get_corporate_mission():
    """Returns the corporate mission context."""
    return jsonify(game.corporate_mission)

@app.route('/api/context/skills_and_assets')
def get_skills_and_assets():
    """Returns the skills and assets context."""
    return jsonify(game.skills_and_assets)

@app.route('/api/context/history')
def get_history():
    """Returns recent corporate history."""
    return jsonify(game.history_long)

@app.route('/api/dashboard')
def get_dashboard():
    """Returns comprehensive dashboard data for the stats panel."""
    global game
    if game is None:
        initialize_game()
    if game is None:
        return jsonify({"status": "error", "message": "Game not initialized"}), 500

    from engines.tendency_analyzer import analyze_player_tendency, get_tendency_description
    from engines.bonus_engine import BonusEngine

    recent_events = game.history_long.get('events', [])[-10:]

    primary_tendency, secondary_tendency = analyze_player_tendency(game.history_long, num_events=10)
    tendency_desc = get_tendency_description(primary_tendency, secondary_tendency)

    bonus_engine = BonusEngine()
    active_bonuses = bonus_engine.get_all_active_bonuses(game)

    bonus_summary = {
        bonus_type: {
            'total': result['total'],
            'sources': [{'type': src_type, 'name': src_name, 'value': value} for src_type, src_name, value in result['sources']]
        } for bonus_type, result in active_bonuses.items()
    }

    department_bonuses = game.department_manager.get_department_bonuses(game) if hasattr(game, 'department_manager') else {}

    return jsonify({
        "corporation": game.corporation,
        "player": game.player,
        "company_culture": game.company_culture,
        "corporate_mission": game.corporate_mission,
        "skills_and_assets": game.skills_and_assets,
        "history": {"recent_events": recent_events},
        "player_tendency": {
            "primary": primary_tendency,
            "secondary": secondary_tendency,
            "description": tendency_desc
        },
        "strategic_focus": game.strategic_focus or "general_operations",
        "key_personnel": game.key_personnel,
        "departments": game.department_manager.get_all() if hasattr(game, 'department_manager') else [],
        "department_bonuses": department_bonuses,
        "active_bonuses": bonus_summary,
        "company_morale": game.company_morale
    })

@app.route('/api/start_personnel_vignette', methods=['POST'])
def start_personnel_vignette():
    """Starts a personnel vignette event."""
    data = request.get_json()
    person_name = data.get('person_name')
    if not person_name:
        return jsonify({"status": "error", "message": "Missing person_name."}), 400

    event_data = character_engine.generate_character_vignette(game, person_name)
    if not event_data:
        return jsonify({"status": "error", "message": f"Could not generate vignette for {person_name}."}), 500

    game.current_event = event_data
    game.event_stage = 0
    game.event_conversation = []

    return jsonify(event_data)

# --- Main Execution ---
if __name__ == '__main__':
    app.run(debug=True)
