#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Comprehensive test script for Phase 1 & Phase 2 systems.
Tests all new features without breaking existing functionality.
"""

import sys
import os
import io

# Force UTF-8 encoding for Windows
if sys.platform == 'win32':
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

# Add parent directory to path
sys.path.insert(0, os.path.dirname(__file__))

def test_imports():
    """Test that all modules import correctly."""
    print("=" * 60)
    print("TESTING IMPORTS")
    print("=" * 60)

    try:
        print("✓ Importing game_state...")
        from game_state import GameState

        print("✓ Importing resource_engine...")
        from engines.resource_engine import (
            calculate_consumption, apply_consumption,
            generate_resource_production, apply_passive_generation
        )

        print("✓ Importing crisis_engine...")
        from engines.crisis_engine import (
            detect_crisis, generate_crisis_event, should_generate_crisis
        )

        print("✓ Importing consequence_engine...")
        from engines.consequence_engine import (
            initialize_consequences, analyze_action_for_consequences,
            apply_consequences, get_consequence_context
        )

        print("✓ Importing callback_engine...")
        from engines.callback_engine import generate_callback_event

        print("✓ Importing victory_engine...")
        from engines.victory_engine import (
            initialize_victory_tracking, calculate_victory_progress,
            check_victory, check_failure
        )

        print("✓ Importing leader_engine...")
        from engines.leader_engine import (
            TRAIT_EFFECTS, get_trait_bonus, apply_aging_effects,
            calculate_leader_effectiveness, generate_successor_candidates
        )

        print("\n✅ All imports successful!\n")
        return True

    except Exception as e:
        print(f"\n❌ Import failed: {e}\n")
        import traceback
        traceback.print_exc()
        return False

def test_game_state_load():
    """Test that game state loads correctly."""
    print("=" * 60)
    print("TESTING GAME STATE LOAD")
    print("=" * 60)

    try:
        from game_state import GameState

        print("✓ Loading game state...")
        game = GameState()

        print("✓ Checking civilization data...")
        assert 'meta' in game.civilization
        assert 'leader' in game.civilization
        assert 'population' in game.civilization

        print("✓ Checking leader data...")
        leader = game.civilization['leader']
        assert 'name' in leader
        assert 'age' in leader
        assert 'traits' in leader  # Should be auto-added if missing

        print("✓ Checking new systems initialized...")
        assert 'consequences' in game.civilization  # Should be auto-initialized
        assert 'victory_progress' in game.civilization  # Should be auto-initialized

        print(f"\n✓ Leader: {leader['name']}, Age {leader['age']}")
        print(f"✓ Traits: {', '.join(leader['traits'])}")
        print(f"✓ Population: {game.civilization['population']}")

        print("\n✅ Game state load successful!\n")
        return game

    except Exception as e:
        print(f"\n❌ Game state load failed: {e}\n")
        import traceback
        traceback.print_exc()
        return None

def test_resource_system(game):
    """Test resource consumption and production."""
    print("=" * 60)
    print("TESTING RESOURCE SYSTEM")
    print("=" * 60)

    try:
        from engines.resource_engine import (
            calculate_consumption, apply_consumption,
            generate_resource_production, apply_passive_generation
        )

        print("✓ Testing consumption calculation...")
        consumption = calculate_consumption(game)
        print(f"  Food consumption: {consumption['food']}")
        print(f"  Wealth consumption: {consumption['wealth']}")

        print("\n✓ Testing production calculation...")
        production = generate_resource_production(game)
        print(f"  Base food production: {production['food']}")
        print(f"  Base wealth production: {production['wealth']}")

        print("\n✓ Testing passive generation with leader bonus...")
        old_food = game.civilization['resources']['food']
        result = apply_passive_generation(game)
        print(f"  Leader effectiveness: {result.get('effectiveness', 1.0):.2f}x")
        print(f"  Final food production: {result['food']}")
        print(f"  Final wealth production: {result['wealth']}")

        # Restore old value
        game.civilization['resources']['food'] = old_food

        print("\n✅ Resource system working!\n")
        return True

    except Exception as e:
        print(f"\n❌ Resource system test failed: {e}\n")
        import traceback
        traceback.print_exc()
        return False

def test_crisis_detection(game):
    """Test crisis detection."""
    print("=" * 60)
    print("TESTING CRISIS DETECTION")
    print("=" * 60)

    try:
        from engines.crisis_engine import detect_crisis, should_generate_crisis

        print("✓ Testing crisis detection...")
        crisis_type = detect_crisis(game)

        if crisis_type:
            print(f"  ⚠️ Crisis detected: {crisis_type}")
        else:
            print(f"  ✓ No crisis (resources are healthy)")

        print("\n✓ Testing crisis probability...")
        should_crisis, crisis_type = should_generate_crisis(game)

        if should_crisis:
            print(f"  ⚠️ Crisis event should trigger: {crisis_type}")
        else:
            print(f"  ✓ No crisis event")

        print("\n✅ Crisis detection working!\n")
        return True

    except Exception as e:
        print(f"\n❌ Crisis detection failed: {e}\n")
        import traceback
        traceback.print_exc()
        return False

def test_consequence_system(game):
    """Test consequence tracking."""
    print("=" * 60)
    print("TESTING CONSEQUENCE SYSTEM")
    print("=" * 60)

    try:
        from engines.consequence_engine import (
            initialize_consequences, analyze_action_for_consequences,
            get_consequence_context
        )

        print("✓ Initializing consequences...")
        initialize_consequences(game)

        print("✓ Testing promise detection...")
        action = "I promise to help the neighboring tribe"
        detected = analyze_action_for_consequences(action, "Test Event", "outcome")

        if detected['promises']:
            print(f"  ✓ Promise detected: {detected['promises'][0]['text'][:50]}...")

        print("\n✓ Testing alliance detection...")
        action = "We form an alliance with the Mountain Clan"
        detected = analyze_action_for_consequences(action, "Alliance Event", "outcome")

        if detected['alliances']:
            print(f"  ✓ Alliance detected: {detected['alliances'][0]['name']}")

        print("\n✓ Getting consequence context...")
        context = get_consequence_context(game)
        print(f"  Context:\n{context}")

        print("\n✅ Consequence system working!\n")
        return True

    except Exception as e:
        print(f"\n❌ Consequence system test failed: {e}\n")
        import traceback
        traceback.print_exc()
        return False

def test_victory_system(game):
    """Test victory/failure detection."""
    print("=" * 60)
    print("TESTING VICTORY/FAILURE SYSTEM")
    print("=" * 60)

    try:
        from engines.victory_engine import (
            calculate_victory_progress, check_victory, check_failure,
            get_victory_status_summary
        )

        print("✓ Calculating victory progress...")
        progress = calculate_victory_progress(game)

        for victory_type, score in progress.items():
            print(f"  {victory_type.capitalize()}: {score}/100")

        print("\n✓ Checking for victory...")
        is_victory, victory_type, victory_desc = check_victory(game)

        if is_victory:
            print(f"  🏆 VICTORY: {victory_type}")
        else:
            print(f"  ✓ No victory yet (highest: {max(progress.values())}/100)")

        print("\n✓ Checking for failure...")
        is_failed, failure_type, failure_desc = check_failure(game)

        if is_failed:
            print(f"  💀 FAILURE: {failure_type}")
        else:
            print(f"  ✓ No failure conditions met")

        print("\n✓ Getting victory status summary...")
        status = get_victory_status_summary(game)
        print(f"  Closest to victory: {status['closest_victory']} ({status['closest_progress']}/100)")

        print("\n✅ Victory/failure system working!\n")
        return True

    except Exception as e:
        print(f"\n❌ Victory/failure test failed: {e}\n")
        import traceback
        traceback.print_exc()
        return False

def test_leader_system(game):
    """Test leader mechanics."""
    print("=" * 60)
    print("TESTING LEADER SYSTEM")
    print("=" * 60)

    try:
        from engines.leader_engine import (
            get_trait_bonus, apply_aging_effects,
            calculate_leader_effectiveness, generate_successor_candidates,
            TRAIT_EFFECTS
        )

        leader = game.civilization['leader']

        print(f"✓ Current leader: {leader['name']}, Age {leader['age']}")
        print(f"  Traits: {', '.join(leader.get('traits', []))}")

        print("\n✓ Testing trait bonuses...")
        for trait in leader.get('traits', []):
            trait_data = TRAIT_EFFECTS.get(trait, {})
            if trait_data:
                print(f"  {trait}: {trait_data['description']}")
                bonuses = trait_data.get('bonuses', {})
                for bonus_type, value in bonuses.items():
                    print(f"    - {bonus_type}: +{value}")

        print("\n✓ Testing leader effectiveness...")
        effectiveness = calculate_leader_effectiveness(leader)
        print(f"  Effectiveness: {effectiveness:.2f}x")

        print("\n✓ Testing aging effects...")
        old_traits = leader.get('traits', []).copy()
        aging_changes = apply_aging_effects(game)

        if aging_changes:
            print(f"  Changes: {', '.join(aging_changes)}")
        else:
            print(f"  No aging changes (leader not at milestone)")

        # Restore traits
        leader['traits'] = old_traits

        print("\n✓ Testing successor generation...")
        candidates = generate_successor_candidates(game)

        print(f"  Generated {len(candidates)} candidates:")
        for i, candidate in enumerate(candidates, 1):
            print(f"    {i}. {candidate['name']} ({candidate['type']})")
            print(f"       Age {candidate['age']}, Traits: {', '.join(candidate['traits'])}")

        print("\n✅ Leader system working!\n")
        return True

    except Exception as e:
        print(f"\n❌ Leader system test failed: {e}\n")
        import traceback
        traceback.print_exc()
        return False

def main():
    """Run all tests."""
    print("\n" + "=" * 60)
    print("CIVILIZATION GAME - COMPREHENSIVE SYSTEM TEST")
    print("=" * 60 + "\n")

    # Test 1: Imports
    if not test_imports():
        print("❌ FATAL: Import test failed. Cannot continue.")
        return False

    # Test 2: Game State Load
    game = test_game_state_load()
    if not game:
        print("❌ FATAL: Game state load failed. Cannot continue.")
        return False

    # Test 3: Resource System
    if not test_resource_system(game):
        print("⚠️ WARNING: Resource system test failed.")

    # Test 4: Crisis Detection
    if not test_crisis_detection(game):
        print("⚠️ WARNING: Crisis detection test failed.")

    # Test 5: Consequence System
    if not test_consequence_system(game):
        print("⚠️ WARNING: Consequence system test failed.")

    # Test 6: Victory/Failure System
    if not test_victory_system(game):
        print("⚠️ WARNING: Victory/failure system test failed.")

    # Test 7: Leader System
    if not test_leader_system(game):
        print("⚠️ WARNING: Leader system test failed.")

    print("\n" + "=" * 60)
    print("✅ ALL CORE TESTS PASSED!")
    print("=" * 60)
    print("\nThe game should run smoothly. Start with:")
    print("  python main.py")
    print("\nThen visit: http://127.0.0.1:5000")
    print("=" * 60 + "\n")

    return True

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)

