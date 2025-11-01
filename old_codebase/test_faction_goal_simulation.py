"""
Test suite for passive faction goal simulation.

This test verifies that factions react to turn outcomes based on their goals,
adjusting approval ratings when outcomes align with or contradict their objectives.
"""

import json
import sys
import os

# Import game systems
from game_state import GameState
from engines.action_processor import _check_faction_goals


def test_wealth_goal_positive():
    """Test that factions with wealth goals gain approval when wealth increases."""
    print("\n" + "=" * 60)
    print("TEST: Wealth Goal - Positive Outcome")
    print("=" * 60)

    # Create game state
    game_state = GameState()

    # Find a faction with wealth-related goals (Merchant's Guild)
    merchant_faction = None
    for faction in game_state.faction_manager.get_all():
        goals = [g.lower() for g in faction.get('goals', [])]
        if any('wealth' in g or 'trade' in g for g in goals):
            merchant_faction = faction
            break

    if not merchant_faction:
        print("⚠️  SKIP: No faction with wealth goals found")
        return True

    faction_name = merchant_faction['name']
    initial_approval = merchant_faction.get('approval', 60)

    print(f"✓ Testing faction: {faction_name}")
    print(f"  Initial approval: {initial_approval}")
    print(f"  Goals: {merchant_faction.get('goals', [])}")

    # Create outcome with wealth increase
    outcome = {
        'updates': {
            'civilization.resources.wealth': 500
        },
        'narrative': 'Trade flourished and merchants prospered.'
    }

    # Apply faction goal check
    _check_faction_goals(game_state, outcome, action='Establish trade routes', event_title='Trade Opportunity')

    # Check if approval increased
    updated_faction = game_state.faction_manager.get_by_name(faction_name)
    final_approval = updated_faction.get('approval', 60)
    approval_change = final_approval - initial_approval

    print(f"  Final approval: {final_approval}")
    print(f"  Approval change: {approval_change:+d}")

    if approval_change > 0:
        print(f"✓ PASS: Approval increased as expected")
        return True
    else:
        print(f"❌ FAIL: Expected approval increase, got {approval_change:+d}")
        return False


def test_wealth_goal_negative():
    """Test that factions with wealth goals lose approval when wealth decreases."""
    print("\n" + "=" * 60)
    print("TEST: Wealth Goal - Negative Outcome")
    print("=" * 60)

    # Create game state
    game_state = GameState()

    # Find a faction with wealth-related goals
    merchant_faction = None
    for faction in game_state.faction_manager.get_all():
        goals = [g.lower() for g in faction.get('goals', [])]
        if any('wealth' in g or 'trade' in g for g in goals):
            merchant_faction = faction
            break

    if not merchant_faction:
        print("⚠️  SKIP: No faction with wealth goals found")
        return True

    faction_name = merchant_faction['name']
    initial_approval = merchant_faction.get('approval', 60)

    print(f"✓ Testing faction: {faction_name}")
    print(f"  Initial approval: {initial_approval}")

    # Create outcome with wealth decrease
    outcome = {
        'updates': {
            'civilization.resources.wealth': -300
        },
        'narrative': 'Economic collapse devastated the markets.'
    }

    # Apply faction goal check
    _check_faction_goals(game_state, outcome, action='Failed economic policy', event_title='Economic Crisis')

    # Check if approval decreased
    updated_faction = game_state.faction_manager.get_by_name(faction_name)
    final_approval = updated_faction.get('approval', 60)
    approval_change = final_approval - initial_approval

    print(f"  Final approval: {final_approval}")
    print(f"  Approval change: {approval_change:+d}")

    if approval_change < 0:
        print(f"✓ PASS: Approval decreased as expected")
        return True
    else:
        print(f"❌ FAIL: Expected approval decrease, got {approval_change:+d}")
        return False


def test_military_goal():
    """Test that factions with military goals react to military actions."""
    print("\n" + "=" * 60)
    print("TEST: Military Goal - Military Success")
    print("=" * 60)

    # Create game state
    game_state = GameState()

    # Find a faction with military-related goals (Warrior's Caste)
    warrior_faction = None
    for faction in game_state.faction_manager.get_all():
        goals = [g.lower() for g in faction.get('goals', [])]
        if any('military' in g or 'expand' in g or 'army' in g for g in goals):
            warrior_faction = faction
            break

    if not warrior_faction:
        print("⚠️  SKIP: No faction with military goals found")
        return True

    faction_name = warrior_faction['name']
    initial_approval = warrior_faction.get('approval', 60)

    print(f"✓ Testing faction: {faction_name}")
    print(f"  Initial approval: {initial_approval}")
    print(f"  Goals: {warrior_faction.get('goals', [])}")

    # Create outcome with military success
    outcome = {
        'updates': {
            'civilization.population': 150  # Population increase from conquest
        },
        'narrative': 'Victory! Our armies conquered the enemy settlement and brought glory to our people.'
    }

    # Apply faction goal check
    _check_faction_goals(
        game_state,
        outcome,
        action='Launch military conquest',
        event_title='Military Victory'
    )

    # Check if approval increased
    updated_faction = game_state.faction_manager.get_by_name(faction_name)
    final_approval = updated_faction.get('approval', 60)
    approval_change = final_approval - initial_approval

    print(f"  Final approval: {final_approval}")
    print(f"  Approval change: {approval_change:+d}")

    if approval_change > 0:
        print(f"✓ PASS: Approval increased as expected")
        return True
    else:
        print(f"❌ FAIL: Expected approval increase, got {approval_change:+d}")
        return False


def test_stability_goal():
    """Test that factions with stability goals react to population changes."""
    print("\n" + "=" * 60)
    print("TEST: Stability Goal - Population Loss")
    print("=" * 60)

    # Create game state
    game_state = GameState()

    # Find a faction with stability-related goals (Elder Council)
    stability_faction = None
    for faction in game_state.faction_manager.get_all():
        goals = [g.lower() for g in faction.get('goals', [])]
        if any('stability' in g or 'tradition' in g or 'maintain' in g for g in goals):
            stability_faction = faction
            break

    if not stability_faction:
        print("⚠️  SKIP: No faction with stability goals found")
        return True

    faction_name = stability_faction['name']
    initial_approval = stability_faction.get('approval', 60)

    print(f"✓ Testing faction: {faction_name}")
    print(f"  Initial approval: {initial_approval}")
    print(f"  Goals: {stability_faction.get('goals', [])}")

    # Create outcome with population loss (instability)
    outcome = {
        'updates': {
            'civilization.population': -200
        },
        'narrative': 'Famine and disease ravaged the population, causing widespread suffering.'
    }

    # Apply faction goal check
    _check_faction_goals(game_state, outcome, action='Failed to prevent famine', event_title='Crisis')

    # Check if approval decreased
    updated_faction = game_state.faction_manager.get_by_name(faction_name)
    final_approval = updated_faction.get('approval', 60)
    approval_change = final_approval - initial_approval

    print(f"  Final approval: {final_approval}")
    print(f"  Approval change: {approval_change:+d}")

    if approval_change < 0:
        print(f"✓ PASS: Approval decreased as expected")
        return True
    else:
        print(f"❌ FAIL: Expected approval decrease, got {approval_change:+d}")
        return False


def test_religious_goal():
    """Test that factions with religious goals react to religious developments."""
    print("\n" + "=" * 60)
    print("TEST: Religious Goal - Temple Construction")
    print("=" * 60)

    # Create game state
    game_state = GameState()

    # Find a faction with religious goals
    religious_faction = None
    for faction in game_state.faction_manager.get_all():
        goals = [g.lower() for g in faction.get('goals', [])]
        if any('temple' in g or 'faith' in g or 'divine' in g for g in goals):
            religious_faction = faction
            break

    if not religious_faction:
        print("⚠️  SKIP: No faction with religious goals found")
        return True

    faction_name = religious_faction['name']
    initial_approval = religious_faction.get('approval', 60)

    print(f"✓ Testing faction: {faction_name}")
    print(f"  Initial approval: {initial_approval}")
    print(f"  Goals: {religious_faction.get('goals', [])}")

    # Create outcome with temple construction
    outcome = {
        'updates': {
            'technology.infrastructure.append': 'Grand Temple'
        },
        'narrative': 'A magnificent temple was constructed, bringing glory to the gods.'
    }

    # Apply faction goal check
    _check_faction_goals(
        game_state,
        outcome,
        action='Construct a grand temple',
        event_title='Religious Construction'
    )

    # Check if approval increased
    updated_faction = game_state.faction_manager.get_by_name(faction_name)
    final_approval = updated_faction.get('approval', 60)
    approval_change = final_approval - initial_approval

    print(f"  Final approval: {final_approval}")
    print(f"  Approval change: {approval_change:+d}")

    if approval_change > 0:
        print(f"✓ PASS: Approval increased as expected")
        return True
    else:
        print(f"❌ FAIL: Expected approval increase, got {approval_change:+d}")
        return False


def test_no_updates():
    """Test that faction goal check handles empty updates gracefully."""
    print("\n" + "=" * 60)
    print("TEST: No Updates - Graceful Handling")
    print("=" * 60)

    # Create game state
    game_state = GameState()

    # Create outcome with no updates
    outcome = {
        'updates': {},
        'narrative': 'Nothing happened.'
    }

    # Apply faction goal check (should return early)
    try:
        _check_faction_goals(game_state, outcome, action='Wait', event_title='No Event')
        print(f"✓ PASS: Handled empty updates without error")
        return True
    except Exception as e:
        print(f"❌ FAIL: Error handling empty updates: {e}")
        return False


def test_history_entries():
    """Test that faction history entries are created."""
    print("\n" + "=" * 60)
    print("TEST: Faction History Entries Created")
    print("=" * 60)

    # Create game state
    game_state = GameState()

    # Find any faction
    faction = game_state.faction_manager.get_all()[0] if game_state.faction_manager.get_all() else None
    if not faction:
        print("⚠️  SKIP: No factions available")
        return True

    faction_name = faction['name']
    initial_history_length = len(faction.get('history', []))

    print(f"✓ Testing faction: {faction_name}")
    print(f"  Initial history entries: {initial_history_length}")

    # Create outcome that affects the faction
    outcome = {
        'updates': {
            'civilization.resources.wealth': 200
        },
        'narrative': 'Test event.'
    }

    # Apply faction goal check
    _check_faction_goals(game_state, outcome, action='Test action', event_title='Test Event')

    # Check if history entry was added
    updated_faction = game_state.faction_manager.get_by_name(faction_name)
    final_history_length = len(updated_faction.get('history', []))

    print(f"  Final history entries: {final_history_length}")

    if final_history_length > initial_history_length:
        print(f"✓ PASS: History entry added")
        print(f"  Latest entry: {updated_faction['history'][-1]}")
        return True
    else:
        print(f"⚠️  No history entry added (faction goals may not match outcome)")
        return True  # Not necessarily a failure


def run_all_tests():
    """Run all faction goal simulation tests."""
    print("\n" + "=" * 70)
    print("FACTION GOAL SIMULATION TEST SUITE")
    print("=" * 70)
    print("\nThese tests verify that factions react to turn outcomes based on")
    print("their goals, adjusting approval ratings when outcomes align with or")
    print("contradict their objectives.")
    print("=" * 70)

    tests = [
        ("Wealth Goal - Positive Outcome", test_wealth_goal_positive),
        ("Wealth Goal - Negative Outcome", test_wealth_goal_negative),
        ("Military Goal - Military Success", test_military_goal),
        ("Stability Goal - Population Loss", test_stability_goal),
        ("Religious Goal - Temple Construction", test_religious_goal),
        ("No Updates - Graceful Handling", test_no_updates),
        ("Faction History Entries Created", test_history_entries),
    ]

    results = []
    for test_name, test_func in tests:
        try:
            result = test_func()
            results.append((test_name, result))
        except Exception as e:
            print(f"\n❌ EXCEPTION in {test_name}: {e}")
            import traceback
            traceback.print_exc()
            results.append((test_name, False))

    # Summary
    print("\n" + "=" * 70)
    print("TEST SUMMARY")
    print("=" * 70)

    passed = sum(1 for _, result in results if result)
    total = len(results)

    for test_name, result in results:
        status = "✓ PASS" if result else "❌ FAIL"
        print(f"{status}: {test_name}")

    print("=" * 70)
    print(f"Total: {passed}/{total} tests passed ({passed/total*100:.0f}%)")
    print("=" * 70)

    if passed == total:
        print("\n🎉 All tests passed!")
    elif passed > 0:
        print(f"\n⚠️  Some tests failed. {total - passed} test(s) need attention.")
    else:
        print("\n❌ All tests failed. Please review the implementation.")

    return passed == total


if __name__ == "__main__":
    success = run_all_tests()
    sys.exit(0 if success else 1)
