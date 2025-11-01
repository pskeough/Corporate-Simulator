import json
import os
import shutil
import tempfile

class GameState:
    """
    Manages loading, accessing, and saving the corporate simulation's state from JSON files.
    Provides access to managers for departments and key personnel.
    """

    def __init__(self, context_dir='new_codebase/context'):
        self.context_dir = context_dir
        self.defaults_dir = os.path.join(context_dir, 'defaults')

        self.paths = {
            'corporation_profile': os.path.join(context_dir, 'corporate_and_player_profile.json'),
            'company_culture': os.path.join(context_dir, 'company_culture.json'),
            'corporate_mission': os.path.join(context_dir, 'corporate_mission.json'),
            'skills_and_assets': os.path.join(context_dir, 'skills_and_assets.json'),
            'market_and_competitors': os.path.join(context_dir, 'market_and_competitors.json'),
            'history_long': os.path.join(context_dir, 'history_long.json'),
            'departments': os.path.join(context_dir, 'departments.json'),
            'key_personnel': os.path.join(context_dir, 'key_personnel.json'),
            'metadata': os.path.join(context_dir, 'game_metadata.json'),
        }

        self.strategic_focus = None
        self.company_morale = 70
        self.turn_number = 0

        self.load()

        # Session-only state for event interactions
        self.current_event = None
        self.event_stage = 0
        self.event_conversation = []

    def reset_to_defaults(self):
        """Resets all game files to their default starting state by copying from the defaults directory."""
        print("Resetting game state to defaults...")
        for key in self.paths:
            default_path = os.path.join(self.defaults_dir, os.path.basename(self.paths[key]))
            if os.path.exists(default_path):
                shutil.copy(default_path, self.paths[key])
                print(f"  - Reset {os.path.basename(self.paths[key])}")

        self.load() # Reload the newly reset state
        self.save() # Save to ensure consistency
        print("Game state has been reset.")

    def load(self):
        """Loads all JSON files into memory."""
        print("Loading game state from context files...")

        profile = self._load_json(self.paths['corporation_profile'])
        self.corporation = profile.get('corporation', {})
        self.player = profile.get('player', {})
        self.simulation = profile.get('simulation', {})

        self.company_culture = self._load_json(self.paths['company_culture'])
        self.corporate_mission = self._load_json(self.paths['corporate_mission'])
        self.skills_and_assets = self._load_json(self.paths['skills_and_assets'])
        self.market_and_competitors = self._load_json(self.paths['market_and_competitors'])
        self.history_long = self._load_json(self.paths['history_long'], default={"events": []})

        departments_data = self._load_json(self.paths['departments'], default={'departments': []})
        self.departments = departments_data

        from engines.department_manager import DepartmentManager
        self.department_manager = DepartmentManager(departments_data)

        personnel_data = self._load_json(self.paths['key_personnel'], default={'personnel': []})
        self.key_personnel = personnel_data

        # NOTE: A KeyPersonnelManager would be implemented here if needed for more complex logic.

        metadata = self._load_json(self.paths['metadata'], default={
            'turn_number': 0,
            'strategic_focus': "general_operations",
            'company_morale': 70
        })
        self.turn_number = metadata.get('turn_number', 0)
        self.strategic_focus = metadata.get('strategic_focus', "general_operations")
        self.company_morale = metadata.get('company_morale', 70)

        print("Game state loaded successfully.")

    def _load_json(self, file_path, default=None):
        """Helper to load a single JSON file, creating it from a default if it doesn't exist."""
        if not os.path.exists(file_path):
            if default is not None:
                print(f"  [OK] Creating default file for {os.path.basename(file_path)}")
                with open(file_path, 'w', encoding='utf-8') as f:
                    json.dump(default, f, indent=4)
                return default
            else:
                raise FileNotFoundError(f"Required game state file not found: {file_path}")

        with open(file_path, 'r', encoding='utf-8') as f:
            return json.load(f)

    def save(self):
        """Saves all in-memory game state back to their respective JSON files."""
        print("Saving game state...")

        # Combine corporation, player, and simulation into one profile file
        profile_data = {
            "corporation": self.corporation,
            "player": self.player,
            "simulation": self.simulation
        }
        self._save_atomic(self.paths['corporation_profile'], profile_data)

        self._save_atomic(self.paths['company_culture'], self.company_culture)
        self._save_atomic(self.paths['corporate_mission'], self.corporate_mission)
        self._save_atomic(self.paths['skills_and_assets'], self.skills_and_assets)
        self._save_atomic(self.paths['market_and_competitors'], self.market_and_competitors)
        self._save_atomic(self.paths['history_long'], self.history_long)

        if hasattr(self, 'department_manager'):
            self._save_atomic(self.paths['departments'], self.department_manager.to_dict())

        self._save_atomic(self.paths['key_personnel'], self.key_personnel)

        metadata = {
            "turn_number": self.turn_number,
            "strategic_focus": self.strategic_focus,
            "company_morale": self.company_morale
        }
        self._save_atomic(self.paths['metadata'], metadata)
        print("Game state saved.")

    def _save_atomic(self, file_path, data):
        """Atomically saves a JSON file to prevent data corruption."""
        try:
            temp_fd, temp_path = tempfile.mkstemp(dir=self.context_dir)
            with os.fdopen(temp_fd, 'w', encoding='utf-8') as temp_file:
                json.dump(data, temp_file, indent=4)
            os.replace(temp_path, file_path)
        except Exception as e:
            print(f"Error saving file {file_path}: {e}")
            if 'temp_path' in locals() and os.path.exists(temp_path):
                os.remove(temp_path)

    def to_dict(self):
        """Serializes the entire game state into a dictionary."""
        return {
            'corporation': self.corporation,
            'player': self.player,
            'simulation': self.simulation,
            'company_culture': self.company_culture,
            'corporate_mission': self.corporate_mission,
            'skills_and_assets': self.skills_and_assets,
            'market_and_competitors': self.market_and_competitors,
            'history_long': self.history_long,
            'departments': self.department_manager.to_dict() if hasattr(self, 'department_manager') else self.departments,
            'key_personnel': self.key_personnel,
            'strategic_focus': self.strategic_focus,
            'company_morale': self.company_morale,
            'turn_number': self.turn_number,
        }
