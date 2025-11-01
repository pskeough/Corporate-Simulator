import json
import os
import tempfile
import shutil

class GameState:
    """
    Manages loading, accessing, and saving the game's state from JSON files.

    Access Patterns:
    - Factions: Use game_state.faction_manager (preferred) or game_state.factions (legacy)
    - Inner Circle: Use game_state.inner_circle_manager (preferred) or game_state.inner_circle (legacy)
    - Both managers support ID-based (preferred) and name-based (legacy) lookups

    Manager Methods:
    - faction_manager.get_by_id(faction_id) - Get faction by ID
    - faction_manager.get_by_name(faction_name) - Get faction by name (legacy)
    - faction_manager.update_approval(faction_id, change) - Update faction approval
    - inner_circle_manager.get_by_name(character_name) - Get character by name
    - inner_circle_manager.get_by_faction_id(faction_id) - Get all characters in a faction
    - inner_circle_manager.update_metrics(name, relationship=0, influence=0, loyalty=0) - Update metrics
    """

    def __init__(self, context_dir='context'):
        self.context_dir = context_dir
        self.defaults_dir = os.path.join(context_dir, 'defaults')
        # Define paths for all context files
        self.paths = {
            'civilization': os.path.join(context_dir, 'civilization_state.json'),
            'culture': os.path.join(context_dir, 'culture.json'),
            'religion': os.path.join(context_dir, 'religion.json'),
            'technology': os.path.join(context_dir, 'technology.json'),
            'world': os.path.join(context_dir, 'world_context.json'),
            'history_long': os.path.join(context_dir, 'history_long.json'),
            'history_compressed': os.path.join(context_dir, 'history_compressed.json'),
            'factions': os.path.join(context_dir, 'factions.json'),
            'inner_circle': os.path.join(context_dir, 'inner_circle.json'),
            'metadata': os.path.join(context_dir, 'game_metadata.json'),
            'buildings': os.path.join(context_dir, 'buildings.json'),
        }
        self.factions = None
        self.inner_circle = None

        # Add new state variables
        self.active_policy = None
        self.population_happiness = 70
        self.turn_number = 0

        # BALANCE_OVERHAUL: Crisis momentum tracking
        self.crisis_momentum = 0  # Tracks consecutive turns in crisis
        self.crisis_recovery_timer = 0  # Tracks turns since crisis ended

        # Butterfly effect tracker for historical_earth mode
        self.butterfly_tracker = None

        self.load()

        # Event interaction state (not persisted, session-only)
        self.current_event = None
        self.event_stage = 0
        self.event_conversation = []

    def reset_to_defaults(self):
        """Resets all game files to a fresh, randomized starting state."""
        self.turn_number = 0
        print("Generating new random civilization...")

        # Import WorldGenerator here to avoid circular imports
        from world_generator import WorldGenerator
        import random

        # Generate random configuration for a new game
        generator = WorldGenerator()

        # Randomize all starting parameters
        config = {
            "world_mode": "historical_earth",  # Default to historical_earth mode
            "starting_era": random.choice(["stone_age", "bronze_age", "iron_age", "classical"]),
            "earth_region": random.choice(["mediterranean", "mesopotamia", "nile_valley", "yellow_river", "indus_valley"]),
            "civilization_name": self._generate_random_civ_name(),
            "population_size": random.choice(["small", "medium", "large"]),
            "leader_name": "",  # Let the generator create a random leader name
            "cultural_focus": random.choice(["martial", "spiritual", "agricultural", "mercantile", "scholarly", "artistic"]),
            "religion_type": random.choice(["animism", "polytheism", "ancestor_worship"]),
            "social_structure": random.choice(["egalitarian", "hierarchical", "tribal_council", "city_state"]),
            "difficulty": "balanced",
            "neighbor_count": random.choice(["few", "several"]),
            "resource_abundance": "moderate"
        }

        # Generate fresh world data
        world_data = generator.generate_world(config)

        # Apply the new world data
        self.apply_custom_world(world_data)

        print(f"New civilization '{world_data['civilization']['meta']['name']}' created!")
        print(f"Leader: {world_data['civilization']['leader']['name']}")
        print(f"Era: {world_data['civilization']['meta']['era']}")

    def _generate_random_civ_name(self):
        """Generate a random civilization name."""
        import random

        prefixes = [
            "The", "The Great", "The Ancient", "The Free", "The United",
            "The Sacred", "The Eternal", "The Golden", "The Silver", "The Rising"
        ]

        names = [
            "Lumina", "Aethera", "Verdant", "Crimson", "Azure", "Storm",
            "Dawn", "Twilight", "Star", "Moon", "Sun", "Earth", "Sky",
            "River", "Mountain", "Forest", "Ocean", "Desert", "Valley"
        ]

        suffixes = [
            "Tribe", "People", "Clan", "Nation", "Empire", "Kingdom",
            "Confederation", "Alliance", "League", "Union", "Society"
        ]

        return f"{random.choice(prefixes)} {random.choice(names)} {random.choice(suffixes)}"

    def apply_custom_world(self, world_data):
        """
        Applies a custom world configuration to the game state.

        Args:
            world_data: Dictionary containing all game state data
        """
        print("Applying custom world configuration...")

        # Update in-memory state
        self.civilization = world_data.get('civilization', {})
        self.culture = world_data.get('culture', {})
        self.religion = world_data.get('religion', {})
        self.technology = world_data.get('technology', {})
        self.world = world_data.get('world', {})
        self.history_long = world_data.get('history_long', {"events": []})
        self.history_compressed = world_data.get('history_compressed', {"eras": []})
        self.factions = world_data.get('factions', {"factions": []})
        # Handle both nested and flat inner circle formats
        inner_circle_data = world_data.get('inner_circle', {})
        if isinstance(inner_circle_data, dict):
            self.inner_circle = inner_circle_data.get('characters', [])
        else:
            self.inner_circle = inner_circle_data

        # Recreate managers with new data
        from engines.faction_manager import FactionManager
        from engines.inner_circle_manager import InnerCircleManager

        self.faction_manager = FactionManager(self.factions)
        self.inner_circle_manager = InnerCircleManager({'characters': self.inner_circle})

        print(f"  [OK] FactionManager reinitialized with {len(self.faction_manager)} factions")
        print(f"  [OK] InnerCircleManager reinitialized with {len(self.inner_circle_manager)} characters")

        # Initialize butterfly tracker for new world
        self._initialize_butterfly_tracker()

        # Save the new state
        self.save()
        print("Custom world applied and saved.")

    def load(self):
        """Loads all JSON files into memory."""
        print("Loading game state from context files...")
        self.civilization = self._load_json(self.paths['civilization'])
        self.culture = self._load_json(self.paths['culture'])
        self.religion = self._load_json(self.paths['religion'])
        self.technology = self._load_json(self.paths['technology'])
        self.world = self._load_json(self.paths['world'])
        self.history_long = self._load_json(self.paths['history_long'])
        self.history_compressed = self._load_json(self.paths['history_compressed'])
        # Load faction data
        factions_data = self._load_json(self.paths['factions'], default={'factions': []})
        # TODO: Remove direct access after full migration (Phase 4)
        self.factions = factions_data  # Keep for backward compatibility

        # Create faction manager (new way)
        from engines.faction_manager import FactionManager
        self.faction_manager = FactionManager(factions_data)

        # Load inner circle data
        circle_data = self._load_json(self.paths['inner_circle'], default={'characters': []})
        # TODO: Remove direct access after full migration (Phase 4)
        self.inner_circle = circle_data.get('characters', [])  # Keep for backward compatibility

        # Create inner circle manager (new way)
        from engines.inner_circle_manager import InnerCircleManager
        self.inner_circle_manager = InnerCircleManager(circle_data)
        print(f"  [OK] FactionManager initialized with {len(self.faction_manager)} factions")
        print(f"  [OK] InnerCircleManager initialized with {len(self.inner_circle_manager)} characters")

        # Load buildings data (Phase 4)
        self.buildings = self._load_json(self.paths['buildings'], default={
            'available_buildings': [],
            'constructed_buildings': []
        })
        print(f"  [OK] Buildings loaded: {len(self.buildings.get('constructed_buildings', []))} constructed")

        # Load metadata (turn_number, active_policy, etc.)
        metadata = self._load_json(self.paths['metadata'], default={
            'turn_number': 0,
            'active_policy': None,
            'population_happiness': 70
        })
        self.turn_number = metadata.get('turn_number', 0)
        self.active_policy = metadata.get('active_policy', None)
        self.population_happiness = metadata.get('population_happiness', 70)

        # Validate and fix leader data
        self._validate_leader()

        # Initialize new systems for backwards compatibility
        self._initialize_new_systems()

        # Initialize butterfly tracker for historical_earth mode
        self._initialize_butterfly_tracker()

        # Validate data integrity
        self._validate_data_integrity()

        print("Game state loaded successfully.")

    def _initialize_new_systems(self):
        """Initialize new Phase 1/2 systems if not present (backwards compatibility)."""
        # Initialize consequences system
        if 'consequences' not in self.civilization:
            from engines.consequence_engine import initialize_consequences
            initialize_consequences(self)
            print("  [OK] Initialized consequence tracking system")

        # Initialize victory progress
        if 'victory_progress' not in self.civilization:
            from engines.victory_engine import initialize_victory_tracking
            initialize_victory_tracking(self)
            print("  [OK] Initialized victory tracking system")

        # Initialize discovered technologies (Phase 4)
        if 'discovered_technologies' not in self.civilization:
            # Grant basic techs based on era for backwards compatibility
            era = self.civilization.get('meta', {}).get('era', 'stone_age')
            basic_techs = []

            # Grant techs based on era
            if era in ['bronze_age', 'iron_age', 'classical', 'medieval']:
                basic_techs.extend(['tech_agriculture', 'tech_writing', 'tech_metalworking', 'tech_currency', 'tech_masonry'])

            self.civilization['discovered_technologies'] = basic_techs
            if basic_techs:
                print(f"  [OK] Initialized discovered technologies: {len(basic_techs)} techs")

    def _validate_leader(self):
        """Validates and corrects leader life expectancy based on current era."""
        leader = self.civilization.get('leader', {})

        # Ensure leader has traits (backwards compatibility)
        if 'traits' not in leader or not leader['traits']:
            # Assign default traits based on era/context
            import random
            default_traits = ['Wise', 'Just', 'Brave']
            leader['traits'] = random.sample(default_traits, 2)
            print(f"  [OK] Assigned default traits to leader: {', '.join(leader['traits'])}")
        era = self.civilization.get('meta', {}).get('era', 'stone_age')

        # Import here to avoid circular dependency
        from engines.timeskip_engine import calculate_life_expectancy

        expected_life_exp = calculate_life_expectancy(era)
        current_life_exp = leader.get('life_expectancy', 0)

        # Check if life expectancy is unrealistic (more than ±10 from expected)
        # Tightened from ±25 to ±10 for better accuracy
        if abs(current_life_exp - expected_life_exp) > 10:
            print(f"  WARNING: Correcting leader life_expectancy from {current_life_exp} to {expected_life_exp} for {era} era")
            self.civilization['leader']['life_expectancy'] = expected_life_exp
            # Save the corrected state
            self.save()

    def _initialize_butterfly_tracker(self):
        """Initialize butterfly effect tracker for historical_earth mode."""
        meta = self.civilization.get('meta', {})
        world_mode = meta.get('world_mode', 'fantasy')

        # Only initialize for historical_earth mode
        if world_mode == 'historical_earth' and meta.get('butterfly_effects_enabled', False):
            from engines.world_modes.historical_earth_mode import ButterflyEffectTracker

            # Check if we have existing tracker data
            if 'butterfly_tracker' in meta:
                tracker_data = meta['butterfly_tracker']
                # Recreate tracker from saved data
                self.butterfly_tracker = ButterflyEffectTracker(
                    starting_era=meta.get('era', 'bronze_age'),
                    starting_year=meta.get('founding_date', -3000)
                )
                self.butterfly_tracker.divergence_score = tracker_data.get('divergence_score', 0)
                self.butterfly_tracker.key_divergences = tracker_data.get('key_divergences', [])
                self.butterfly_tracker.timeline_altered = tracker_data.get('timeline_altered', False)
                print(f"  [OK] Butterfly tracker loaded: {self.butterfly_tracker.get_timeline_name()}")
            else:
                # Create new tracker
                self.butterfly_tracker = ButterflyEffectTracker(
                    starting_era=meta.get('era', 'bronze_age'),
                    starting_year=meta.get('founding_date', -3000)
                )
                print("  [OK] Butterfly tracker initialized for historical_earth mode")

    def _validate_data_integrity(self):
        """Validates referential integrity of game data."""
        from engines.data_validator import validate_all

        validation_result = validate_all(self)

        # Print any errors or warnings
        if validation_result['errors']:
            print("  WARNING: DATA INTEGRITY WARNINGS:")
            for error in validation_result['errors']:
                print(f"    - {error}")

        if validation_result['warnings']:
            for warning in validation_result['warnings']:
                print(f"  WARNING: {warning}")

    def _load_json(self, file_path, default=None):
        """
        Helper to load a single JSON file.
        If the file doesn't exist and a default is provided,
        creates the file with the default content.
        """
        if not os.path.exists(file_path) and default is not None:
            print(f"  [OK] Creating default file for {os.path.basename(file_path)}")
            with open(file_path, 'w', encoding='utf-8') as f:
                json.dump(default, f, indent=4)
            return default
        
        with open(file_path, 'r', encoding='utf-8') as f:
            return json.load(f)

    def save(self):
        """Saves all in-memory game state back to their respective JSON files."""
        print("Saving game state...")
        self._save_atomic(self.paths['civilization'], self.civilization)
        self._save_atomic(self.paths['culture'], self.culture)
        self._save_atomic(self.paths['religion'], self.religion)
        self._save_atomic(self.paths['technology'], self.technology)
        self._save_atomic(self.paths['world'], self.world)
        self._save_atomic(self.paths['history_long'], self.history_long)
        self._save_atomic(self.paths['history_compressed'], self.history_compressed)
        # Save from managers if they exist (preferred), otherwise use direct attributes
        if hasattr(self, 'faction_manager'):
            self._save_atomic(self.paths['factions'], self.faction_manager.to_dict())
        else:
            self._save_atomic(self.paths['factions'], self.factions)

        if hasattr(self, 'inner_circle_manager'):
            self._save_atomic(self.paths['inner_circle'], self.inner_circle_manager.to_dict())
        else:
            self._save_atomic(self.paths['inner_circle'], {"characters": self.inner_circle})

        # Save buildings (Phase 4)
        self._save_atomic(self.paths['buildings'], self.buildings)

        self._save_atomic(self.paths['metadata'], {
            "turn_number": self.turn_number,
            "active_policy": self.active_policy,
            "population_happiness": self.population_happiness
        })
        print("Game state saved.")

    def _save_atomic(self, file_path, data):
        """
        Atomically saves a JSON file by writing to a temporary file 
        and then renaming it to prevent data corruption.
        """
        try:
            # Create a temporary file in the same directory
            temp_fd, temp_path = tempfile.mkstemp(dir=self.context_dir)
            with os.fdopen(temp_fd, 'w', encoding='utf-8') as temp_file:
                json.dump(data, temp_file, indent=4)
            
            # Atomically replace the original file with the new one
            os.replace(temp_path, file_path)
        except Exception as e:
            print(f"Error saving file {file_path}: {e}")
            # If an error occurs, try to clean up the temporary file
            if os.path.exists(temp_path):
                os.remove(temp_path)
    def to_dict(self):
        """Serializes the entire game state into a dictionary."""
        return {
            'civilization': self.civilization,
            'culture': self.culture,
            'religion': self.religion,
            'technology': self.technology,
            'world': self.world,
            'history_long': self.history_long,
            'history_compressed': self.history_compressed,
            'factions': self.faction_manager.to_dict() if hasattr(self, 'faction_manager') else self.factions,
            'inner_circle': self.inner_circle_manager.to_dict() if hasattr(self, 'inner_circle_manager') else {"characters": self.inner_circle},
            'buildings': self.buildings,
            'active_policy': self.active_policy,
            'population_happiness': self.population_happiness,
            'turn_number': self.turn_number,
        }
