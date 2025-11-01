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
from engines import character_engine
from world_generator import WorldGenerator

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

def generate_advisor_portraits_sync(game_state):
    """
    Generate portraits for all advisors synchronously.
    This ensures portraits are available immediately when the game loads.
    """
    from engines.visual_engine import generate_advisor_portrait

    print("--- Starting advisor portrait generation ---")

    # Get era and culture context
    era = game_state.civilization.get('meta', {}).get('era', 'classical')
    culture_values = game_state.culture.get('values', [])
    civ_context = {
        'era': era,
        'culture_values': culture_values
    }

    # Get all advisors
    if hasattr(game_state, 'inner_circle_manager'):
        advisors = game_state.inner_circle_manager.get_all()
    else:
        advisors = game_state.inner_circle.get('characters', [])

    # Generate portrait for each advisor
    for advisor in advisors:
        try:
            print(f"Generating portrait for {advisor.get('name', 'Unknown')}...")
            portrait_result = generate_advisor_portrait(advisor, civ_context)

            if portrait_result.get('success'):
                advisor['portrait'] = portrait_result.get('filename', 'placeholder.png')
                print(f"✓ Portrait generated for {advisor.get('name')}")
            else:
                print(f"✗ Portrait generation failed for {advisor.get('name')}")
        except Exception as e:
            print(f"Error generating portrait for {advisor.get('name', 'Unknown')}: {e}")

    print("--- Advisor portrait generation complete ---")

def generate_advisor_portraits_async(game_state):
    """
    Generate portraits for all advisors in the background.
    This runs asynchronously so it doesn't block game creation.
    DEPRECATED: Use generate_advisor_portraits_sync for initial generation.
    """
    def _generate():
        generate_advisor_portraits_sync(game_state)
        # Save after all portraits generated
        game_state.save()

    # Start generation in background thread
    thread = threading.Thread(target=_generate, daemon=True)
    thread.start()

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
            "civilization_name": temp_game.civilization.get('meta', {}).get('name', 'Unknown'),
            "year": temp_game.civilization.get('meta', {}).get('year', 0),
            "era": temp_game.civilization.get('meta', {}).get('era', 'Unknown'),
            "leader_name": temp_game.civilization.get('leader', {}).get('name', 'Unknown')
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

        # Generate initial leader portrait
        from engines.visual_engine import generate_leader_portrait
        leader = game.civilization.get('leader', {})
        civ_context = {
            'era': game.civilization.get('meta', {}).get('era', 'stone_age'),
            'culture_values': game.culture.get('values', [])
        }
        portrait_result = generate_leader_portrait(leader, civ_context)

        # Store portrait path in leader data
        if portrait_result.get('success'):
            game.civilization['leader']['portrait'] = portrait_result.get('filename', 'placeholder.png')

            # Initialize the image update tracker with initial state
            from engines.image_update_manager import get_tracker
            tracker = get_tracker()
            tracker.update_portrait_state(game)

        # Generate advisor portraits synchronously for immediate availability
        generate_advisor_portraits_sync(game)

        game.save()

        return jsonify({"status": "success"})
    except Exception as e:
        print(f"Error creating new game: {e}")
        return jsonify({"status": "error", "message": str(e)}), 500

@app.route('/api/custom_game', methods=['POST'])
def custom_game():
    """Creates a new game with custom world generation."""
    global game
    try:
        # Get custom configuration from request
        config = request.get_json()

        # Initialize world generator
        generator = WorldGenerator()

        # Generate world data
        world_data = generator.generate_world(config)

        # Initialize or reinitialize game
        if game is None:
            game = GameState()

        # Apply custom world data
        game.apply_custom_world(world_data)

        # Generate opening description (optional)
        description = generator.generate_ai_description(world_data)

        # Generate leader portrait
        from engines.visual_engine import generate_leader_portrait
        leader = game.civilization.get('leader', {})
        civ_context = {
            'era': game.civilization.get('meta', {}).get('era', 'stone_age'),
            'culture_values': game.culture.get('values', [])
        }
        portrait_result = generate_leader_portrait(leader, civ_context)

        if portrait_result.get('success'):
            game.civilization['leader']['portrait'] = portrait_result.get('filename', 'placeholder.png')

            # Initialize the image update tracker with initial state
            from engines.image_update_manager import get_tracker
            tracker = get_tracker()
            tracker.update_portrait_state(game)

        # Generate advisor portraits synchronously for immediate availability
        generate_advisor_portraits_sync(game)

        game.save()

        return jsonify({
            "status": "success",
            "description": description
        })
    except Exception as e:
        print(f"Error creating custom game: {e}")
        import traceback
        traceback.print_exc()
        return jsonify({"status": "error", "message": str(e)}), 500

@app.route('/api/game_state')
def get_game_state():
    """Returns the complete current game state."""
    global game
    if game is None:
        initialize_game()
    if game is None:
        return jsonify({"status": "error", "message": "Game not initialized"}), 500

    return jsonify({
        "civilization": game.civilization,
        "culture": game.culture,
        "religion": game.religion,
        "technology": game.technology,
        "world": game.world
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
        # Check for victory or failure before generating event
        from engines.victory_engine import check_victory, check_failure

        # Check failure first (higher priority)
        is_failed, failure_type, failure_desc = check_failure(game)
        if is_failed:
            return jsonify({
                "game_over": True,
                "outcome": "defeat",
                "type": failure_type,
                "title": f"Civilization Fallen: {failure_type.replace('_', ' ').title()}",
                "narrative": failure_desc
            })

        # Check victory
        is_victory, victory_type, victory_desc = check_victory(game)
        if is_victory:
            return jsonify({
                "game_over": True,
                "outcome": "victory",
                "type": victory_type,
                "title": f"Victory Achieved: {victory_type.replace('_', ' ').title()}",
                "narrative": victory_desc
            })

        # No game over, generate normal event
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

@app.route('/api/die', methods=['POST'])
def handle_death():
    """
    Generates successor candidates for the player to choose from using the high-stakes succession crisis system.
    """
    global game
    if game is None:
        initialize_game()
    if game is None:
        return jsonify({"status": "error", "message": "Game not initialized"}), 500

    print("--- Player has chosen to abdicate. Triggering succession crisis. ---")
    from engines.leader_engine import trigger_succession_crisis, apply_legacy_bonus
    from engines.visual_engine import generate_leader_portrait

    leader = game.civilization.get('leader', {})

    # Trigger high-stakes succession crisis with faction-backed candidates
    succession_data = trigger_succession_crisis(game)
    candidates = succession_data['candidates']

    # Generate portraits for each candidate
    era = game.civilization.get('meta', {}).get('era', 'classical')
    culture_values = game.culture.get('values', [])

    for candidate in candidates:
        civ_context = {
            'era': era,
            'culture_values': culture_values
        }
        # Create a temporary leader dict for portrait generation
        temp_leader = {
            'name': candidate['name'],
            'age': candidate['age'],
            'traits': candidate['traits'],
            'role': 'Candidate'
        }
        portrait_result = generate_leader_portrait(temp_leader, civ_context)
        candidate['portrait'] = portrait_result.get('filename', 'placeholder.png')

    # Create summary of current leader
    summary = (
        f"The reign of {leader.get('name', 'a forgotten leader')} has come to an end. "
        f"They ruled for {leader.get('years_ruled', 0)} years, reaching the age of {leader.get('age', 'unknown')}. "
        f"Their legacy, marked by traits of '{', '.join(leader.get('traits', ['mystery']))}', will be remembered."
    )

    return jsonify({
        "status": "success",
        "summary": summary,
        "candidates": candidates,
        "requires_choice": True,
        "succession_crisis": True,  # Flag to indicate high-stakes succession
        "transition_crisis_duration": succession_data.get('transition_crisis_duration', 10),
        "rival_claimant_chance": succession_data.get('rival_claimant_chance', 0.40)
    })

@app.route('/api/choose_successor', methods=['POST'])
def choose_successor():
    """
    Apply chosen successor and legacy bonuses, including faction approval changes.
    """
    data = request.get_json()
    chosen_index = data.get('successor_index')

    if chosen_index is None:
        return jsonify({"status": "error", "message": "No successor chosen"}), 400

    from engines.leader_engine import trigger_succession_crisis, apply_legacy_bonus
    from engines.timeskip_engine import calculate_life_expectancy

    # Store old leader for legacy
    old_leader = game.civilization['leader'].copy()

    # Generate candidates again using trigger_succession_crisis (same logic as /api/die)
    succession_data = trigger_succession_crisis(game)
    candidates = succession_data['candidates']

    if chosen_index < 0 or chosen_index >= len(candidates):
        return jsonify({"status": "error", "message": "Invalid successor index"}), 400

    chosen = candidates[chosen_index]

    # Apply legacy bonuses
    legacy = apply_legacy_bonus(game, old_leader)

    # Apply faction approval changes from succession choice
    approval_changes = chosen.get('approval_changes', {})
    if hasattr(game, 'faction_manager'):
        for faction_key, change in approval_changes.items():
            # Find matching faction by id
            factions = game.faction_manager.get_all()
            for faction in factions:
                if faction_key in faction.get('id', '').lower():
                    current_approval = faction.get('approval', 50)
                    faction['approval'] = max(0, min(100, current_approval + change))
                    print(f"  Faction {faction['name']} approval: {faction['approval']} ({change:+d})")

    # Apply special effects (e.g., populist happiness boost)
    if chosen.get('special') == 'happiness_boost':
        game.population_happiness = min(100, game.population_happiness + 20)
        legacy['bonuses_applied'].append("+20 immediate happiness (people's champion)")

    # Set new leader
    era = game.civilization['meta']['era']
    game.civilization['leader'] = {
        'name': chosen['name'],
        'age': chosen.get('age', 30),
        'life_expectancy': calculate_life_expectancy(era),
        'role': 'Leader',
        'traits': chosen['traits'],
        'years_ruled': 0,
        'archetype': chosen.get('archetype', 'Unknown'),
        'backing_faction': chosen.get('backing_faction', 'None'),
        'demands': chosen.get('demands', 'None')
    }

    print(f"  👑 New leader: {chosen['name']} ({chosen.get('archetype', 'Unknown')})")
    print(f"  Backed by: {chosen.get('backing_faction', 'None')}")

    # Generate portrait for new leader
    from engines.visual_engine import generate_leader_portrait
    civ_context = {
        'era': era,
        'culture_values': game.culture.get('values', [])
    }
    portrait_result = generate_leader_portrait(game.civilization['leader'], civ_context)

    if portrait_result.get('success'):
        game.civilization['leader']['portrait'] = portrait_result.get('filename', 'placeholder.png')

        # Reset the image update tracker for the new leader
        from engines.image_update_manager import get_tracker
        tracker = get_tracker()
        tracker.update_portrait_state(game)

    # Store succession crisis state for future events (rival claimants, etc.)
    if not hasattr(game, 'succession_state'):
        game.succession_state = {}
    game.succession_state['recent_succession'] = True
    game.succession_state['chosen_candidate'] = chosen['name']
    game.succession_state['rival_claimant_chance'] = succession_data.get('rival_claimant_chance', 0.40)
    game.succession_state['transition_crisis_duration'] = succession_data.get('transition_crisis_duration', 10)
    game.succession_state['turns_since_succession'] = 0

    game.save()

    return jsonify({
        "status": "success",
        "new_leader": game.civilization['leader'],
        "legacy": legacy,
        "faction_changes": approval_changes
    })
@app.route('/api/context/culture')
def get_culture():
    """Returns the culture context."""
    return jsonify(game.culture)

@app.route('/api/context/religion')
def get_religion():
    """Returns the religion context."""
    return jsonify(game.religion)

@app.route('/api/context/technology')
def get_technology():
    """Returns the technology context."""
    return jsonify(game.technology)

@app.route('/api/context/history_recent')
def get_history_recent():
    """Returns recent history."""
    return jsonify(game.history_long)

@app.route('/api/context/history_ancient')
def get_history_ancient():
    """Returns compressed ancient history."""
    return jsonify(game.history_compressed)

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

    # Combine recent history from both sources
    recent_events = []
    if game.history_long and 'events' in game.history_long:
        recent_events = game.history_long['events'][-10:]  # Last 10 events

    # Analyze player tendency for dashboard display
    primary_tendency, secondary_tendency = analyze_player_tendency(game.history_long, num_events=10)
    tendency_desc = get_tendency_description(primary_tendency, secondary_tendency)

    # Calculate active bonuses for display
    bonus_engine = BonusEngine()
    active_bonuses = bonus_engine.get_all_active_bonuses(game)

    # Format for frontend
    bonus_summary = {}
    for bonus_type, result in active_bonuses.items():
        bonus_summary[bonus_type] = {
            'total': result['total'],
            'sources': [
                {'type': src_type, 'name': src_name, 'value': value}
                for src_type, src_name, value in result['sources']
            ]
        }

    # Calculate faction bonuses for UI display
    faction_bonuses = {}
    if hasattr(game, 'faction_manager'):
        raw_bonuses = game.faction_manager.get_faction_bonuses(game)

        # Format for frontend display
        faction_bonuses = {
            'wealth_multiplier': raw_bonuses.get('wealth_multiplier', 1.0),
            'military_effectiveness': raw_bonuses.get('military_effectiveness', 1.0),
            'happiness_modifier': raw_bonuses.get('happiness_modifier', 0)
        }

    return jsonify({
        "civilization": {
            "name": game.civilization.get('meta', {}).get('name', 'Unknown'),
            "year": game.civilization.get('meta', {}).get('year', 0),
            "era": game.civilization.get('meta', {}).get('era', 'Unknown'),
            "founding_date": game.civilization.get('meta', {}).get('founding_date', 0),
            "population": game.civilization.get('population', 0),
            "resources": game.civilization.get('resources', {}),
            "leader": game.civilization.get('leader', {})
        },
        "culture": {
            "values": game.culture.get('values', []),
            "traditions": game.culture.get('traditions', []),
            "taboos": game.culture.get('taboos', []),
            "social_structure": game.culture.get('social_structure', 'Unknown'),
            "recent_changes": game.culture.get('recent_changes', [])
        },
        "religion": {
            "name": game.religion.get('name', 'Unknown'),
            "type": game.religion.get('type', 'Unknown'),
            "primary_deity": game.religion.get('primary_deity', 'Unknown'),
            "core_tenets": game.religion.get('core_tenets', []),
            "practices": game.religion.get('practices', []),
            "holy_sites": game.religion.get('holy_sites', []),
            "influence": game.religion.get('influence', 'Unknown')
        },
        "technology": {
            "current_tier": game.technology.get('current_tier', 'Unknown'),
            "discoveries": game.technology.get('discoveries', []),
            "in_progress": game.technology.get('in_progress', []),
            "infrastructure": game.technology.get('infrastructure', [])
        },
        "history": {
            "recent_events": recent_events,
            "age": abs(game.civilization.get('meta', {}).get('year', 0) - game.civilization.get('meta', {}).get('founding_date', 0))
        },
        "player_tendency": {
            "primary": primary_tendency,
            "secondary": secondary_tendency,
            "description": tendency_desc
        },
        "active_policy": game.active_policy or "general_governance",
        "inner_circle": game.inner_circle,
        "factions": game.faction_manager.get_all() if hasattr(game, 'faction_manager') else (game.factions.get('factions', []) if isinstance(game.factions, dict) else []),
        "faction_bonuses": faction_bonuses,
        "active_bonuses": bonus_summary,
        "population_happiness": game.population_happiness
    })

@app.route('/api/victory_status')
def get_victory_status():
    """Returns current victory progress and status."""
    from engines.victory_engine import get_victory_status_summary

    status = get_victory_status_summary(game)
    return jsonify(status)

@app.route('/api/settlement_gallery')
def get_settlement_gallery():
    """Returns list of settlement evolution images."""
    from engines.visual_engine import get_settlement_gallery

    gallery = get_settlement_gallery(limit=5)
    return jsonify({"gallery": gallery})

@app.route('/api/start_character_vignette', methods=['POST'])
def start_character_vignette():
    """
    Starts a character vignette event.
    """
    data = request.get_json()
    character_name = data.get('character_name')

    if not character_name:
        return jsonify({"status": "error", "message": "Missing character_name."}), 400

    # Generate the character vignette event
    event_data = character_engine.generate_character_vignette(game, character_name)

    if not event_data:
        return jsonify({"status": "error", "message": f"Could not generate vignette for {character_name}."}), 500

    # Reset event state and set new character vignette as current event
    game.current_event = event_data
    game.event_stage = 0
    game.event_conversation = []

    return jsonify(event_data)

@app.route('/api/buildings')
def get_buildings():
    """Returns building information including available and constructed buildings."""
    from engines.building_manager import BuildingManager

    building_manager = BuildingManager()

    # Get available buildings (can construct)
    available = building_manager.get_available(game)

    # Get constructed buildings
    constructed = game.buildings.get('constructed_buildings', [])

    # Get buildings in construction
    in_construction = game.buildings.get('available_buildings', [])

    return jsonify({
        "available": available,
        "constructed": constructed,
        "in_construction": in_construction
    })

@app.route('/api/technologies')
def get_technologies():
    """Returns discovered technologies."""
    return jsonify({
        "discovered": game.civilization.get('discovered_technologies', []),
        "era": game.civilization.get('meta', {}).get('era', 'stone_age')
    })

# --- Main Execution ---
if __name__ == '__main__':
    app.run(debug=True)

