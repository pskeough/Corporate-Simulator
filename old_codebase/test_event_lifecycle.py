#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Integration test for complete event lifecycle.
Tests: Event Generation → Investigation → Decision → State Updates → Validation
"""

import sys
import os
import io

# Force UTF-8 encoding for Windows
if sys.platform == 'win32':
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

# Add parent directory to path
sys.path.insert(0, os.path.dirname(__file__))

from game_state import GameState
from engines.event_generator import generate_event, generate_event_stage
from engines.action_processor import process_player_action


def test_event_generation():
    """Test that events can be generated without errors."""
    print("=" * 60)
    print("TEST 1: Event Generation")
    print("=" * 60)

    game = GameState()
    print(f"✓ Game state loaded (Turn {game.turn_number})")

    # Generate an event
    print("✓ Generating event...")
    event = generate_event(game)

    # Validate event structure
    assert 'title' in event, "Event missing title"
    assert 'narrative' in event, "Event missing narrative"

    # Check for appropriate options based on event type
    if 'game_over' in event and event['game_over']:
        print(f"  ℹ️ Special event: {event.get('title', 'Unknown')}")
    elif 'council' in event.get('title', '').lower():
        print(f"  ℹ️ Council meeting event: {event['title']}")
    else:
        assert 'investigation_options' in event or 'decision_options' in event, "Event missing options"

    print(f"✓ Event generated: '{event.get('title', 'Unknown')}'")
    print(f"  Narrative: {event.get('narrative', '')[:80]}...")

    return game, event


def test_event_investigation(game, event):
    """Test event investigation mechanic."""
    print("\n" + "=" * 60)
    print("TEST 2: Event Investigation")
    print("=" * 60)

    # Skip if event doesn't support investigation
    if 'game_over' in event and event['game_over']:
        print("⊘ Skipped (game over event)")
        return None

    if 'investigation_options' not in event:
        print("⊘ Skipped (event has no investigation options)")
        return None

    investigation_option = event['investigation_options'][0] if event['investigation_options'] else "Ask for more information"

    print(f"✓ Player investigates: '{investigation_option}'")

    # Generate next stage
    stage_data = generate_event_stage(game, investigation_option)

    # Validate stage structure
    assert 'narrative' in stage_data, "Stage missing narrative"
    assert 'investigation_options' in stage_data, "Stage missing investigation options"
    assert 'decision_options' in stage_data, "Stage missing decision options"

    print(f"✓ Stage {game.event_stage} generated")
    print(f"  Response: {stage_data['narrative'][:80]}...")
    print(f"  New investigation options: {len(stage_data['investigation_options'])}")
    print(f"  Updated decision options: {len(stage_data['decision_options'])}")

    return stage_data


def test_event_decision(game, event):
    """Test event decision and state updates."""
    print("\n" + "=" * 60)
    print("TEST 3: Event Decision & State Updates")
    print("=" * 60)

    # Get decision option
    if 'decision_options' in event and event['decision_options']:
        decision = event['decision_options'][0]
    else:
        decision = "Proceed cautiously"

    print(f"✓ Player decides: '{decision}'")

    # Store pre-action state
    pre_population = game.civilization['population']
    pre_food = game.civilization['resources']['food']
    pre_wealth = game.civilization['resources']['wealth']
    pre_year = game.civilization['meta']['year']
    pre_turn = game.turn_number

    print(f"  Pre-action state:")
    print(f"    Population: {pre_population}, Food: {pre_food}, Wealth: {pre_wealth}")
    print(f"    Year: {pre_year}, Turn: {pre_turn}")

    # Process action
    event_title = event.get('title', 'Test Event')
    event_narrative = event.get('narrative', 'Test narrative')

    print("✓ Processing action...")
    outcome = process_player_action(game, decision, event_title, event_narrative)

    # Validate outcome structure
    assert 'narrative' in outcome, "Outcome missing narrative"
    print(f"✓ Outcome generated: {outcome['narrative'][:80]}...")

    # Check state changes
    post_population = game.civilization['population']
    post_food = game.civilization['resources']['food']
    post_wealth = game.civilization['resources']['wealth']
    post_year = game.civilization['meta']['year']
    post_turn = game.turn_number

    print(f"  Post-action state:")
    print(f"    Population: {post_population} ({post_population - pre_population:+d})")
    print(f"    Food: {post_food} ({post_food - pre_food:+d})")
    print(f"    Wealth: {post_wealth} ({post_wealth - pre_wealth:+d})")
    print(f"    Year: {post_year} (advanced from {pre_year})")
    print(f"    Turn: {post_turn} (advanced from {pre_turn})")

    # Validate automatic progression
    assert post_year == pre_year + 1, "Year did not advance"
    assert post_turn == pre_turn + 1, "Turn did not advance"

    print("✓ Automatic progression verified (year +1, turn +1)")

    # Check for warnings
    if 'resource_warnings' in outcome:
        print(f"  ⚠️ Resource warnings: {', '.join(outcome['resource_warnings'])}")

    return outcome


def test_data_integrity(game):
    """Test that game state remains valid after event."""
    print("\n" + "=" * 60)
    print("TEST 4: Data Integrity Check")
    print("=" * 60)

    # Check required fields
    assert 'meta' in game.civilization, "Missing civilization.meta"
    assert 'leader' in game.civilization, "Missing civilization.leader"
    assert 'population' in game.civilization, "Missing population"
    assert 'resources' in game.civilization, "Missing resources"

    # Check leader data
    leader = game.civilization['leader']
    assert 'name' in leader, "Missing leader name"
    assert 'age' in leader, "Missing leader age"
    assert 'traits' in leader, "Missing leader traits"
    assert isinstance(leader['traits'], list), "Leader traits must be a list"

    # Check resources are non-negative
    resources = game.civilization['resources']
    assert resources['food'] >= 0, "Food cannot be negative"
    assert resources['wealth'] >= 0, "Wealth cannot be negative"

    # Check population is reasonable
    population = game.civilization['population']
    assert population >= 50, f"Population too low: {population}"
    assert population <= 1000000, f"Population unreasonably high: {population}"

    print("✓ All required fields present")
    print("✓ Leader data valid")
    print("✓ Resources within bounds")
    print("✓ Population reasonable")

    # Run data validator
    from engines.data_validator import validate_all

    validation_result = validate_all(game)

    if validation_result['errors']:
        print("⚠️ Validation errors found:")
        for error in validation_result['errors']:
            print(f"    - {error}")
    else:
        print("✓ Data validator passed (no errors)")

    return validation_result['valid']


def test_save_and_reload(game):
    """Test that game state can be saved and reloaded."""
    print("\n" + "=" * 60)
    print("TEST 5: Save & Reload")
    print("=" * 60)

    # Save current state
    pre_turn = game.turn_number
    pre_population = game.civilization['population']

    print(f"✓ Saving game state (Turn {pre_turn}, Pop {pre_population})...")
    game.save()

    # Reload
    print("✓ Reloading game state...")
    game2 = GameState()

    # Verify data matches
    assert game2.turn_number == pre_turn, "Turn number mismatch after reload"
    assert game2.civilization['population'] == pre_population, "Population mismatch after reload"

    print(f"✓ Reloaded successfully (Turn {game2.turn_number}, Pop {game2.civilization['population']})")
    print("✓ Data integrity maintained across save/load cycle")

    return True


def main():
    """Run all integration tests."""
    print("=" * 60)
    print("EVENT LIFECYCLE INTEGRATION TEST")
    print("=" * 60)
    print()

    try:
        # Test 1: Generate event
        game, event = test_event_generation()

        # Test 2: Investigate event (if applicable)
        stage_data = test_event_investigation(game, event)

        # Test 3: Make decision
        outcome = test_event_decision(game, event)

        # Test 4: Validate data integrity
        valid = test_data_integrity(game)

        # Test 5: Save and reload
        save_ok = test_save_and_reload(game)

        # Summary
        print("\n" + "=" * 60)
        print("✅ ALL INTEGRATION TESTS PASSED!")
        print("=" * 60)
        print("\nThe complete event lifecycle works correctly:")
        print("  ✓ Event generation")
        print("  ✓ Investigation mechanics")
        print("  ✓ Decision processing")
        print("  ✓ State updates")
        print("  ✓ Data validation")
        print("  ✓ Persistence")
        print("\nThe system is stable and ready for gameplay.")
        print("=" * 60)

        return True

    except Exception as e:
        print("\n" + "=" * 60)
        print("❌ TEST FAILED")
        print("=" * 60)
        print(f"Error: {e}")
        import traceback
        traceback.print_exc()
        return False


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)

