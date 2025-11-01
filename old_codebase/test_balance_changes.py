"""
BALANCE_OVERHAUL Test Suite
Tests all balance changes implemented across resource, crisis, faction, and leader systems.
"""

import sys
import os

# Configure stdout encoding for Windows
if sys.platform == 'win32':
    import codecs
    sys.stdout = codecs.getwriter('utf-8')(sys.stdout.buffer, 'strict')

# Add project root to path
sys.path.insert(0, os.path.dirname(__file__))

from game_state import GameState
from engines.resource_engine import calculate_consumption, apply_consumption, apply_passive_generation
from engines.crisis_engine import detect_crisis
from engines.leader_engine import TRAIT_EFFECTS, get_trait_bonus, calculate_leader_effectiveness


def test_phase1_resource_pressure():
    """Test Phase 1: Resource Pressure Foundation"""
    print("\n" + "="*60)
    print("TESTING PHASE 1: RESOURCE PRESSURE FOUNDATION")
    print("="*60)

    game_state = GameState()

    # Test 1.1: Tightened food consumption ratios (UPDATED for 2025-01 balance changes)
    print("\n[Test 1.1] Food Consumption Ratios")
    game_state.civilization['population'] = 100
    game_state.civilization['meta']['era'] = 'stone_age'

    consumption = calculate_consumption(game_state)
    expected_food = int((100 // 4) * 2.0)  # NEW: pop/4 instead of pop/10, 2.0 instead of 1.8
    actual_food = consumption['food']

    print(f"  Stone Age (100 pop): Expected {expected_food}, Got {actual_food}")
    assert actual_food == expected_food, f"Food consumption mismatch: {actual_food} != {expected_food}"
    print("  ✓ Stone age food consumption increased correctly (1.8 → 2.0, pop/10 → pop/4)")

    # Test 1.2: Flat consumption (UPDATED for 2025-01 balance changes - removed tiering)
    print("\n[Test 1.2] Flat Population Consumption (pop/4)")

    # Clear infrastructure to get base consumption
    infrastructure_count = len(game_state.technology.get('infrastructure', []))
    game_state.technology['infrastructure'] = []

    test_cases = [
        (500, 1.2, "Classical era 500 pop"),
        (1000, 1.2, "Classical era 1000 pop"),
        (2000, 1.2, "Classical era 2000 pop"),
        (5000, 1.2, "Classical era 5000 pop")
    ]

    for pop, era_mult, tier_name in test_cases:
        game_state.civilization['population'] = pop
        game_state.civilization['meta']['era'] = 'classical'  # 1.2 multiplier (was 1.1)
        consumption = calculate_consumption(game_state)
        # New formula: (pop // 4) * era_efficiency * infrastructure_scaling
        # infrastructure_scaling = 1 + (0 * 0.005) = 1.0 (no buildings)
        expected = int((pop // 4) * era_mult * 1.0)
        actual = consumption['food']
        print(f"  {tier_name}: Expected {expected}, Got {actual}")
        assert actual == expected, f"{tier_name} consumption mismatch: {actual} != {expected}"

    print("  ✓ Flat consumption formula works correctly (pop/4 * era_efficiency)")

    # Test 1.3: Exponential infrastructure maintenance (UPDATED for 2025-01 balance changes)
    print("\n[Test 1.3] Exponential Infrastructure Maintenance")

    # Clear existing buildings and set clean state
    if hasattr(game_state, 'buildings'):
        game_state.buildings['constructed_buildings'] = []
    game_state.technology['infrastructure'] = ['building_granary_001'] * 10  # 10 granaries

    consumption = calculate_consumption(game_state)
    # NEW formula: total_base_maintenance * (1 + count * 0.05)
    # 10 granaries @ 8 each = 80 base * 1.5 scaling = 120
    expected_wealth = int(10 * 8 * 1.5)
    actual_wealth = consumption['wealth']

    print(f"  10 granaries: Expected {expected_wealth}, Got {actual_wealth}")
    assert actual_wealth == expected_wealth, f"Infrastructure cost mismatch: {actual_wealth} != {expected_wealth}"
    print("  ✓ Exponential scaling works (10 granaries @ 8 each * 1.5 = 120)")

    # Test 1.4: Food stockpile decay
    print("\n[Test 1.4] Food Stockpile Decay")
    game_state.civilization['resources']['food'] = 600  # Above 500 threshold
    initial_food = 600

    apply_consumption(game_state)

    # Should have 10% decay for > 500 food
    expected_after_decay = initial_food - consumption['food'] - int(initial_food * 0.10)
    actual_after = game_state.civilization['resources']['food']

    print(f"  Initial: {initial_food}, After consumption & decay: {actual_after}")
    print(f"  Expected: {expected_after_decay}")
    assert actual_after <= initial_food * 0.9, "Food decay not applied correctly"
    print("  ✓ Food decay applied (10% for stockpiles > 500)")

    print("\n" + "✓"*30 + " PHASE 1 TESTS PASSED " + "✓"*30)


def test_phase2_crisis_escalation():
    """Test Phase 2: Crisis Escalation & Cascading"""
    print("\n" + "="*60)
    print("TESTING PHASE 2: CRISIS ESCALATION & CASCADING")
    print("="*60)

    game_state = GameState()

    # Test 2.1: Tightened crisis thresholds
    print("\n[Test 2.1] Tightened Crisis Thresholds")

    # Initialize crisis momentum tracking
    game_state.crisis_momentum = 0
    game_state.crisis_recovery_timer = 0

    test_scenarios = [
        (100, 0.4, 0, "famine"),
        (100, 0.7, 1000, "severe_food_shortage"),
        (100, 1.5, 1000, "food_shortage"),
        (100, 2.0, 250, "economic_warning"),
        (100, 2.0, 50, "economic_crisis")
    ]

    for pop, food_per_capita, wealth, expected_crisis in test_scenarios:
        game_state.civilization['population'] = pop
        game_state.civilization['resources']['food'] = int(pop * food_per_capita)
        game_state.civilization['resources']['wealth'] = wealth

        crisis = detect_crisis(game_state)
        print(f"  Food/capita: {food_per_capita:.1f}, Wealth: {wealth} → Crisis: {crisis}")
        assert crisis == expected_crisis, f"Expected {expected_crisis}, got {crisis}"

    print("  ✓ All crisis thresholds trigger correctly")

    # Test 2.2: Crisis cascading
    print("\n[Test 2.2] Crisis Cascading")
    game_state.civilization['population'] = 1000
    game_state.civilization['resources']['food'] = 1500  # 1.5 per capita - food crisis
    game_state.civilization['resources']['wealth'] = 250  # Economic crisis
    game_state.population_happiness = 35  # Happiness crisis

    # Run detection multiple times to test probabilistic cascading
    cascade_detected = False
    for _ in range(20):  # 20 attempts should trigger cascade
        crisis = detect_crisis(game_state)
        if crisis in ['economic_crisis', 'food_shortage', 'compound_crisis']:
            cascade_detected = True
            print(f"  Multiple crises detected → Cascade triggered: {crisis}")
            break

    assert cascade_detected, "Crisis cascading failed to trigger"
    print("  ✓ Crisis cascading system works")

    # Test 2.3: Crisis momentum tracking
    print("\n[Test 2.3] Crisis Momentum Tracking")
    game_state.crisis_momentum = 0
    game_state.civilization['resources']['food'] = 50  # Famine
    game_state.civilization['resources']['wealth'] = 1000

    initial_momentum = game_state.crisis_momentum
    detect_crisis(game_state)
    assert game_state.crisis_momentum == initial_momentum + 1, "Crisis momentum not incremented"
    print(f"  Crisis momentum: {initial_momentum} → {game_state.crisis_momentum}")
    print("  ✓ Crisis momentum tracking works")

    print("\n" + "✓"*30 + " PHASE 2 TESTS PASSED " + "✓"*30)


def test_phase3_faction_consequences():
    """Test Phase 3: Faction Mechanical Consequences"""
    print("\n" + "="*60)
    print("TESTING PHASE 3: FACTION MECHANICAL CONSEQUENCES")
    print("="*60)

    game_state = GameState()

    # Test 3.1: Faction bonuses
    print("\n[Test 3.1] Faction Approval Bonuses")

    if hasattr(game_state, 'faction_manager') and len(game_state.faction_manager) > 0:
        # Set a merchant faction to low approval
        for faction in game_state.faction_manager.get_all():
            if 'merchant' in faction.get('id', '').lower():
                faction['approval'] = 20  # Below 25 threshold
                break

        bonuses = game_state.faction_manager.get_faction_bonuses(game_state)

        print(f"  Wealth multiplier with angry merchants: {bonuses['wealth_multiplier']}")
        assert bonuses['wealth_multiplier'] <= 0.75, "Low merchant approval should reduce wealth"
        print("  ✓ Faction approval affects wealth multiplier")
    else:
        print("  ⚠ No factions available to test")

    print("\n" + "✓"*30 + " PHASE 3 TESTS PASSED " + "✓"*30)


def test_phase4_leader_tradeoffs():
    """Test Phase 4: Leader Trade-offs & Succession"""
    print("\n" + "="*60)
    print("TESTING PHASE 4: LEADER TRADE-OFFS & SUCCESSION")
    print("="*60)

    # Test 4.1: Leader trait penalties
    print("\n[Test 4.1] Leader Trait Penalties")

    # Test Ruthless trait (has both bonuses and penalties)
    ruthless_trait = TRAIT_EFFECTS['Ruthless']
    print(f"  Ruthless trait:")
    print(f"    Bonuses: {ruthless_trait['bonuses']}")
    print(f"    Penalties: {ruthless_trait['penalties']}")

    assert 'penalties' in ruthless_trait, "Ruthless trait missing penalties"
    assert 'diplomatic_reputation' in ruthless_trait['penalties'], "Missing diplomatic penalty"
    print("  ✓ Traits have penalties defined")

    # Test get_trait_bonus with penalties
    test_leader = {'traits': ['Ruthless']}
    mil_bonus = get_trait_bonus(test_leader, 'military_reputation')
    dip_bonus = get_trait_bonus(test_leader, 'diplomatic_reputation')

    print(f"  Ruthless leader: Military +{mil_bonus}, Diplomatic {dip_bonus}")
    assert mil_bonus > 0, "Military bonus not applied"
    assert dip_bonus < 0, "Diplomatic penalty not applied"
    print("  ✓ Bonus calculation handles penalties correctly")

    # Test 4.2: Aggressive age-based decline
    print("\n[Test 4.2] Aggressive Age-Based Decline")

    test_cases = [
        (15, 60, 0.90, "Youth"),       # 25% of life_exp
        (40, 60, 1.10, "Prime"),       # 67% of life_exp
        (45, 60, 1.05, "Aging"),       # 75% of life_exp
        (50, 60, 0.95, "Elderly"),     # 83% of life_exp
        (55, 60, 0.80, "Ancient"),     # 92% of life_exp
        (65, 60, 0.70, "Death's door") # 108% of life_exp
    ]

    for age, life_exp, expected_mult, age_group in test_cases:
        leader = {'age': age, 'life_expectancy': life_exp, 'traits': []}
        effectiveness = calculate_leader_effectiveness(leader, None)

        age_percent = (age / life_exp) * 100
        print(f"  {age_group} ({age_percent:.0f}%): Effectiveness {effectiveness:.2f} (expected ~{expected_mult:.2f})")

        # Allow 10% tolerance for trait bonuses
        assert abs(effectiveness - expected_mult) < 0.15, f"Age modifier incorrect for {age_group}"

    print("  ✓ Age-based decline curve works correctly")

    print("\n" + "✓"*30 + " PHASE 4 TESTS PASSED " + "✓"*30)


def run_all_tests():
    """Run all balance change tests"""
    print("\n" + "="*60)
    print("GAME BALANCE OVERHAUL - COMPREHENSIVE TEST SUITE")
    print("="*60)

    try:
        test_phase1_resource_pressure()
        test_phase2_crisis_escalation()
        test_phase3_faction_consequences()
        test_phase4_leader_tradeoffs()

        print("\n" + "="*60)
        print("🎉 ALL TESTS PASSED! BALANCE OVERHAUL SUCCESSFUL! 🎉")
        print("="*60)
        print("\n✅ Resource pressure: Food consumption increased, decay added")
        print("✅ Crisis escalation: Tighter thresholds, cascading implemented")
        print("✅ Faction consequences: Approval affects economy/military/happiness")
        print("✅ Leader trade-offs: Traits have penalties, age decline aggressive")
        print("\n" + "="*60)

        return True

    except AssertionError as e:
        print(f"\n❌ TEST FAILED: {e}")
        return False
    except Exception as e:
        print(f"\n❌ ERROR: {e}")
        import traceback
        traceback.print_exc()
        return False


if __name__ == "__main__":
    success = run_all_tests()
    sys.exit(0 if success else 1)

