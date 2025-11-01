"""
BuildingManager - Manages building construction, requirements, and availability.
"""

import json
import os


class BuildingManager:
    """
    Manages building construction and availability based on era and technology.

    Usage:
        manager = BuildingManager()
        available = manager.get_available(game_state)
        if manager.can_construct('building_granary_001', game_state):
            manager.start_construction('building_granary_001', game_state)
        manager.process_turn(game_state)
    """

    def __init__(self, building_types_path='data/building_types.json'):
        """Initialize the building manager and load building definitions."""
        self.building_types = self._load_building_types(building_types_path)

    def _load_building_types(self, path):
        """Load building type definitions from JSON file."""
        if not os.path.exists(path):
            print(f"Warning: Building types file not found at {path}")
            return {}

        with open(path, 'r', encoding='utf-8') as f:
            data = json.load(f)

        # Convert list to dict keyed by building id
        building_dict = {}
        for building in data.get('buildings', []):
            building_dict[building['id']] = building

        return building_dict

    def get_available(self, game_state):
        """
        Get list of buildings available for construction based on era and technologies.

        Args:
            game_state: GameState instance

        Returns:
            List of building definitions that can be constructed
        """
        available = []
        current_era = game_state.civilization.get('meta', {}).get('era', 'stone_age')
        discovered_techs = game_state.civilization.get('discovered_technologies', [])
        constructed_ids = [b.get('id') for b in game_state.buildings.get('constructed_buildings', [])]

        # Era progression for comparison
        era_order = ['stone_age', 'bronze_age', 'iron_age', 'classical', 'medieval']
        current_era_index = era_order.index(current_era) if current_era in era_order else 0

        for building_id, building in self.building_types.items():
            # Skip if already constructed
            if building_id in constructed_ids:
                continue

            # Check era requirement
            required_era = building.get('requirements', {}).get('era', 'stone_age')
            required_era_index = era_order.index(required_era) if required_era in era_order else 0

            if current_era_index < required_era_index:
                continue

            # Check technology requirements
            required_techs = building.get('requirements', {}).get('technologies', [])
            if required_techs:
                if not all(tech in discovered_techs for tech in required_techs):
                    continue

            available.append(building)

        return available

    def can_construct(self, building_id, game_state):
        """
        Check if a specific building can be constructed (has resources and meets requirements).

        Args:
            building_id: Building ID to check
            game_state: GameState instance

        Returns:
            tuple: (can_construct: bool, reason: str)
        """
        building = self.building_types.get(building_id)

        if not building:
            return (False, f"Unknown building: {building_id}")

        # Check if already constructed
        constructed_ids = [b.get('id') for b in game_state.buildings.get('constructed_buildings', [])]
        if building_id in constructed_ids:
            return (False, f"{building['name']} already constructed")

        # Check if already in construction queue
        in_progress_ids = [b.get('id') for b in game_state.buildings.get('available_buildings', [])]
        if building_id in in_progress_ids:
            return (False, f"{building['name']} already under construction")

        # Check if available (era/tech requirements)
        available_buildings = self.get_available(game_state)
        if building not in available_buildings:
            return (False, f"{building['name']} not yet available (check era/technology requirements)")

        # Check wealth cost
        cost = building.get('cost', {})
        wealth_cost = cost.get('wealth', 0)
        current_wealth = game_state.civilization.get('resources', {}).get('wealth', 0)

        if current_wealth < wealth_cost:
            return (False, f"Insufficient wealth (need {wealth_cost}, have {current_wealth})")

        return (True, "Can construct")

    def start_construction(self, building_id, game_state):
        """
        Start construction of a building (deduct cost, add to queue).

        Args:
            building_id: Building ID to construct
            game_state: GameState instance

        Returns:
            tuple: (success: bool, message: str)
        """
        can_build, reason = self.can_construct(building_id, game_state)

        if not can_build:
            return (False, reason)

        building = self.building_types[building_id]

        # Deduct wealth cost
        cost = building.get('cost', {})
        wealth_cost = cost.get('wealth', 0)
        game_state.civilization['resources']['wealth'] -= wealth_cost

        # Add to construction queue
        turns_to_complete = cost.get('turns', 1)
        construction_entry = {
            'id': building_id,
            'name': building['name'],
            'turns_remaining': turns_to_complete
        }

        game_state.buildings['available_buildings'].append(construction_entry)

        return (True, f"Started construction of {building['name']} (will complete in {turns_to_complete} turns)")

    def process_turn(self, game_state):
        """
        Process one turn of construction (decrement timers, complete buildings).

        Args:
            game_state: GameState instance

        Returns:
            List of completed building names
        """
        completed = []
        still_building = []

        for building in game_state.buildings.get('available_buildings', []):
            building['turns_remaining'] -= 1

            if building['turns_remaining'] <= 0:
                # Building complete!
                completed_entry = {
                    'id': building['id'],
                    'name': building['name'],
                    'turns_remaining': 0
                }
                game_state.buildings['constructed_buildings'].append(completed_entry)
                completed.append(building['name'])
            else:
                # Still building
                still_building.append(building)

        # Update queue (remove completed buildings)
        game_state.buildings['available_buildings'] = still_building

        return completed

    def get_building_by_id(self, building_id):
        """
        Get building definition by ID.

        Args:
            building_id: Building ID

        Returns:
            Building definition dict or None
        """
        return self.building_types.get(building_id)

    def get_all_building_types(self):
        """
        Get all building type definitions.

        Returns:
            Dict of building_id -> building definition
        """
        return self.building_types
