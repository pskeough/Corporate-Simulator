#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""Test script to verify the data validation system works correctly."""

import sys
import io

# Force UTF-8 encoding for Windows console
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')

from game_state import GameState
from engines.data_validator import validate_faction_references, validate_all

def main():
    print("=" * 60)
    print("Testing Data Validation System")
    print("=" * 60)

    try:
        # Load game state
        print("\n[1] Loading game state...")
        game = GameState()
        print("    SUCCESS: Game state loaded")

        # Check factions structure
        print("\n[2] Checking factions data...")
        if isinstance(game.factions, dict):
            factions_list = game.factions.get('factions', [])
        elif isinstance(game.factions, list):
            factions_list = game.factions
        else:
            print("    ERROR: Invalid factions structure")
            return False

        print(f"    Found {len(factions_list)} factions")

        # Verify faction IDs exist
        faction_ids = [f.get('id') for f in factions_list if f.get('id')]
        print(f"    Factions with IDs: {len(faction_ids)}")
        for faction in factions_list:
            print(f"      - {faction.get('name')}: {faction.get('id', 'NO ID')}")

        # Check inner circle
        print("\n[3] Checking inner circle data...")
        print(f"    Found {len(game.inner_circle)} characters")
        for char in game.inner_circle:
            faction_link = char.get('faction_link', 'N/A')
            faction_id = char.get('faction_id', 'NO ID')
            print(f"      - {char.get('name')}: {faction_link} -> {faction_id}")

        # Run validation
        print("\n[4] Running validation checks...")
        validation_result = validate_all(game)

        if validation_result['valid']:
            print("    SUCCESS: All validation checks passed!")
        else:
            print("    WARNINGS FOUND:")
            for error in validation_result['errors']:
                print(f"      - {error}")

        print("\n" + "=" * 60)
        print("Test completed successfully!")
        print("=" * 60)
        return True

    except Exception as e:
        print(f"\n    ERROR: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == '__main__':
    success = main()
    sys.exit(0 if success else 1)
