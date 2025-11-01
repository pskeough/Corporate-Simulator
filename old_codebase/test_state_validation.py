#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""Test script to verify state validation catches invalid AI updates."""

import sys
import io

# Force UTF-8 encoding for Windows console
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')

from game_state import GameState
from engines.state_validator import validate_updates

def test_invalid_updates():
    """Test that the validator properly rejects invalid update paths."""
    print("=" * 70)
    print("Testing State Validation - Invalid Updates")
    print("=" * 70)

    # Load game state
    game = GameState()

    # Test cases that should FAIL validation (these are the bugs we're fixing)
    invalid_test_cases = [
        {
            "name": "Invalid append - religion.traditions (doesn't exist in schema)",
            "updates": {"religion.traditions.append": "New Tradition"}
        },
        {
            "name": "Invalid append - religion.beliefs (doesn't exist in schema)",
            "updates": {"religion.beliefs.append": "Core Belief"}
        },
        {
            "name": "Invalid root key - narrative",
            "updates": {"narrative.append": "Some story"}
        },
        {
            "name": "Creating arbitrary civilization key",
            "updates": {"civilization.scouts_dispatched": 5}
        },
        {
            "name": "Wrong root key - population",
            "updates": {"population.change": 100}
        },
        {
            "name": "Wrong root key - food",
            "updates": {"food.change": -50}
        }
    ]

    print("\n[TEST 1] Invalid Updates (should all be REJECTED):\n")
    all_rejected = True
    for test in invalid_test_cases:
        is_valid, cleaned, errors = validate_updates(test["updates"], game)

        if is_valid or len(errors) == 0:
            print(f"  ❌ FAILED: {test['name']}")
            print(f"     Expected rejection but validation passed!")
            all_rejected = False
        else:
            print(f"  ✅ PASS: {test['name']}")
            print(f"     Error: {errors[0]}")

    # Test cases that should PASS validation
    valid_test_cases = [
        {
            "name": "Valid append - culture.traditions",
            "updates": {"culture.traditions.append": "Harvest Festival"}
        },
        {
            "name": "Valid append - religion.practices",
            "updates": {"religion.practices.append": "Lunar Worship"}
        },
        {
            "name": "Valid append - religion.core_tenets",
            "updates": {"religion.core_tenets.append": "Honor the Ancestors"}
        },
        {
            "name": "Valid append - religion.holy_sites",
            "updates": {"religion.holy_sites.append": "Sacred Grove"}
        },
        {
            "name": "Valid append - technology.discoveries",
            "updates": {"technology.discoveries.append": "Bronze Working"}
        },
        {
            "name": "Valid update - civilization.population",
            "updates": {"civilization.population": -50}
        },
        {
            "name": "Valid update - civilization.resources.food",
            "updates": {"civilization.resources.food": 100}
        },
        {
            "name": "Valid update - civilization.resources.wealth",
            "updates": {"civilization.resources.wealth": -200}
        }
    ]

    print("\n[TEST 2] Valid Updates (should all be ACCEPTED):\n")
    all_accepted = True
    for test in valid_test_cases:
        is_valid, cleaned, errors = validate_updates(test["updates"], game)

        if not is_valid or len(errors) > 0:
            print(f"  ❌ FAILED: {test['name']}")
            print(f"     Expected acceptance but got errors: {errors}")
            all_accepted = False
        else:
            print(f"  ✅ PASS: {test['name']}")

    print("\n" + "=" * 70)
    if all_rejected and all_accepted:
        print("✅ ALL TESTS PASSED - Validation is working correctly!")
        print("=" * 70)
        return True
    else:
        print("❌ SOME TESTS FAILED - Validation needs fixes")
        print("=" * 70)
        return False

if __name__ == '__main__':
    success = test_invalid_updates()
    sys.exit(0 if success else 1)
