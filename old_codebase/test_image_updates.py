"""
Test script to verify image update logic works correctly.
Run this before playing to ensure the system is working.
"""

from engines.image_update_manager import (
    should_update_leader_portrait,
    should_update_settlement_image,
    get_tracker,
    reset_tracker
)


def test_portrait_updates():
    """Test leader portrait update detection logic."""
    print("\n=== Testing Leader Portrait Updates ===\n")

    # Reset tracker for clean test
    reset_tracker()
    tracker = get_tracker()

    # Mock game state
    game_state = {
        'civilization': {
            'leader': {
                'age': 25,
                'life_expectancy': 80,
                'traits': ['Brave', 'Warrior'],
            },
            'resources': {
                'wealth': 100
            }
        }
    }

    # Test 1: Initial generation
    should_update, reason = should_update_leader_portrait(game_state)
    print(f"Test 1 - Initial: {should_update} ({reason})")
    assert should_update, "Should update on first call"

    # Initialize tracker
    tracker.update_portrait_state(game_state)

    # Test 2: No changes (same turn)
    should_update, reason = should_update_leader_portrait(game_state)
    print(f"Test 2 - No changes: {should_update} ({reason})")
    assert not should_update, "Should not update immediately"

    # Test 3: After 10 turns
    for _ in range(10):
        tracker.increment_turns()
    should_update, reason = should_update_leader_portrait(game_state)
    print(f"Test 3 - After 10 turns: {should_update} ({reason})")
    assert should_update, "Should update after 10 turns"
    tracker.update_portrait_state(game_state)

    # Test 4: Age milestone (cross 20% threshold)
    game_state['civilization']['leader']['age'] = 16  # 20% of 80
    should_update, reason = should_update_leader_portrait(game_state)
    print(f"Test 4 - Age milestone (20%): {should_update} ({reason})")
    # Note: Won't trigger since we just updated, unless 10 turns passed

    # Test 5: Trait change
    aging_changes = ["Leader gained trait: Experienced"]
    should_update, reason = should_update_leader_portrait(game_state, aging_changes)
    print(f"Test 5 - Trait change: {should_update} ({reason})")
    assert should_update, "Should update on trait change"
    tracker.update_portrait_state(game_state)

    # Test 6: Wealth tier change
    game_state['civilization']['resources']['wealth'] = 600  # Move to "prosperous" tier
    should_update, reason = should_update_leader_portrait(game_state)
    print(f"Test 6 - Wealth change: {should_update} ({reason})")
    assert should_update, "Should update on wealth tier change"

    print("\n[PASS] All portrait update tests passed!\n")


def test_settlement_updates():
    """Test settlement image update detection logic."""
    print("\n=== Testing Settlement Image Updates ===\n")

    # Reset tracker for clean test
    reset_tracker()
    tracker = get_tracker()

    # Mock game state
    game_state = {
        'civilization': {
            'population': 50,
            'meta': {
                'era': 'stone_age'
            },
            'technology': {
                'infrastructure': ['Huts', 'Fire Pit']
            }
        }
    }

    # Test 1: Initial generation
    should_update, reason = should_update_settlement_image(game_state)
    print(f"Test 1 - Initial: {should_update} ({reason})")
    assert should_update, "Should update on first call"

    # Initialize tracker
    tracker.update_settlement_state(game_state)

    # Test 2: No changes
    should_update, reason = should_update_settlement_image(game_state)
    print(f"Test 2 - No changes: {should_update} ({reason})")
    assert not should_update, "Should not update with no changes"

    # Test 3: Population crosses size threshold (100 = village)
    game_state['civilization']['population'] = 150
    should_update, reason = should_update_settlement_image(game_state)
    print(f"Test 3 - Population growth (camp -> village): {should_update} ({reason})")
    assert should_update, "Should update when crossing size threshold"
    tracker.update_settlement_state(game_state)

    # Test 4: Era change
    game_state['civilization']['meta']['era'] = 'bronze_age'
    should_update, reason = should_update_settlement_image(game_state)
    print(f"Test 4 - Era change: {should_update} ({reason})")
    assert should_update, "Should update on era change"
    tracker.update_settlement_state(game_state)

    # Test 5: Major infrastructure
    game_state['civilization']['technology']['infrastructure'].append('Walls')
    should_update, reason = should_update_settlement_image(game_state)
    print(f"Test 5 - Major infrastructure (Walls): {should_update} ({reason})")
    assert should_update, "Should update for major infrastructure"
    tracker.update_settlement_state(game_state)

    # Test 6: Minor infrastructure (should NOT trigger)
    game_state['civilization']['technology']['infrastructure'].append('Granary')
    should_update, reason = should_update_settlement_image(game_state)
    print(f"Test 6 - Minor infrastructure (Granary): {should_update} ({reason})")
    assert not should_update, "Should NOT update for minor infrastructure"

    print("\n[PASS] All settlement update tests passed!\n")


if __name__ == "__main__":
    print("\n" + "="*60)
    print("IMAGE UPDATE SYSTEM TEST")
    print("="*60)

    try:
        test_portrait_updates()
        test_settlement_updates()

        print("\n" + "="*60)
        print("[SUCCESS] ALL TESTS PASSED!")
        print("="*60 + "\n")

    except AssertionError as e:
        print(f"\n[FAIL] TEST FAILED: {e}\n")
    except Exception as e:
        print(f"\n[ERROR] {e}\n")
        import traceback
        traceback.print_exc()

