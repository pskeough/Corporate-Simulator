"""
Test script for apply_world_turn_updates function.
Tests faction, inner circle, and neighboring civilization updates.
"""

import sys
import os
sys.path.insert(0, os.path.dirname(__file__))

from game_state import GameState
from engines.state_updater import apply_world_turn_updates


def test_apply_world_turn_updates():
    """Test the apply_world_turn_updates function with various scenarios."""
    print("=" * 70)
    print("Testing apply_world_turn_updates Function")
    print("=" * 70)

    # Load game state
    game_state = GameState()

    # Test 1: Faction updates
    print("\n### TEST 1: Faction Approval Updates ###")
    print("Initial factions:")
    for faction in game_state.faction_manager.get_all():
        print(f"  - {faction['name']}: approval = {faction.get('approval', 'N/A')}")

    faction_test_updates = {
        'faction_updates': [
            {'name': "The Merchant's Guild", 'approval_change': 10},
            {'name': "The Warrior's Caste", 'approval_change': -5},
            {'name': "Nonexistent Faction", 'approval_change': 5}  # Should warn
        ]
    }

    print("\nApplying faction updates...")
    apply_world_turn_updates(game_state, faction_test_updates)

    print("\nFactions after update:")
    for faction in game_state.faction_manager.get_all():
        print(f"  - {faction['name']}: approval = {faction.get('approval', 'N/A')}")

    # Test 2: Inner Circle updates
    print("\n### TEST 2: Inner Circle Metrics Updates ###")
    print("Initial inner circle:")
    for character in game_state.inner_circle_manager.get_all():
        metrics = character.get('metrics', {})
        print(f"  - {character['name']}: relationship={metrics.get('relationship', 'N/A')}, "
              f"loyalty={metrics.get('loyalty', 'N/A')}")

    inner_circle_test_updates = {
        'inner_circle_updates': [
            {'name': 'Seraphina Vane', 'loyalty_change': 5, 'opinion_change': 10},
            {'name': 'General Kaelen', 'loyalty_change': -3, 'opinion_change': 7},
            {'name': 'Nonexistent Character', 'loyalty_change': 5, 'opinion_change': 5}  # Should warn
        ]
    }

    print("\nApplying inner circle updates...")
    apply_world_turn_updates(game_state, inner_circle_test_updates)

    print("\nInner circle after update:")
    for character in game_state.inner_circle_manager.get_all():
        metrics = character.get('metrics', {})
        print(f"  - {character['name']}: relationship={metrics.get('relationship', 'N/A')}, "
              f"loyalty={metrics.get('loyalty', 'N/A')}")

    # Test 3: Neighboring civilization updates
    print("\n### TEST 3: Neighboring Civilization Relationship Updates ###")
    print("Initial known peoples:")
    for people in game_state.world.get('known_peoples', []):
        print(f"  - {people['name']}: relationship = {people.get('relationship', 'N/A')}")

    neighbor_test_updates = {
        'neighboring_civilization_updates': [
            {'name': 'The Plains Riders', 'relationship_change': 10},  # neutral -> friendly
            {'name': 'The Forest Tribes', 'relationship_change': 10},  # allied -> allied (already max)
            {'name': 'The Stone Circle Clans', 'relationship_change': -10},  # hostile -> hostile (already min)
            {'name': 'Nonexistent Civilization', 'relationship_change': 5}  # Should warn
        ]
    }

    print("\nApplying neighboring civilization updates...")
    apply_world_turn_updates(game_state, neighbor_test_updates)

    print("\nKnown peoples after update:")
    for people in game_state.world.get('known_peoples', []):
        print(f"  - {people['name']}: relationship = {people.get('relationship', 'N/A')}")

    # Test 4: Combined updates
    print("\n### TEST 4: Combined Updates ###")
    combined_updates = {
        'faction_updates': [
            {'name': "The Priesthood of the Sun", 'approval_change': 15}
        ],
        'inner_circle_updates': [
            {'name': 'High Priestess Lyra', 'loyalty_change': 10, 'opinion_change': 5}
        ],
        'neighboring_civilization_updates': [
            {'name': 'The Plains Riders', 'relationship_change': 10}  # friendly -> allied
        ]
    }

    print("\nApplying combined updates...")
    apply_world_turn_updates(game_state, combined_updates)

    # Test 5: Edge cases
    print("\n### TEST 5: Edge Cases ###")

    # Invalid input
    print("\nTest with non-dict input:")
    apply_world_turn_updates(game_state, "not a dict")

    # Empty updates
    print("\nTest with empty updates:")
    apply_world_turn_updates(game_state, {})

    # Missing managers (simulate)
    print("\nTest with missing faction_manager:")
    original_manager = game_state.faction_manager
    delattr(game_state, 'faction_manager')
    apply_world_turn_updates(game_state, {'faction_updates': [{'name': 'Test', 'approval_change': 5}]})
    game_state.faction_manager = original_manager

    print("\n" + "=" * 70)
    print("All tests completed!")
    print("=" * 70)

    # Don't save changes - this is just a test
    print("\nNote: Changes not saved to preserve original game state.")


if __name__ == '__main__':
    test_apply_world_turn_updates()
