"""
Test script to verify that faction decision consequences are properly applied.
Tests the fix for Issue #2: Asymmetric Faction Consequences Are Never Applied
"""

import sys
import os
import io

# Fix encoding for Windows console
if sys.platform == 'win32':
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8', errors='replace')

sys.path.insert(0, os.path.abspath(os.path.dirname(__file__)))

from engines.faction_manager import FactionManager
from engines.faction_engine import apply_faction_decision_consequences

class MockGameState:
    """Mock game state for testing"""
    def __init__(self):
        # Create initial faction data
        self.faction_manager = FactionManager({
            "factions": [
                {
                    "id": "faction_merchants_guild_001",
                    "name": "The Merchant's Guild",
                    "approval": 60,
                },
                {
                    "id": "faction_warriors_caste_001",
                    "name": "The Warrior's Caste",
                    "approval": 60,
                },
                {
                    "id": "faction_priesthood_sun_001",
                    "name": "The Priesthood of the Sun",
                    "approval": 60,
                }
            ]
        })

def test_faction_consequences():
    """Test that faction consequences are properly applied"""
    print("=" * 60)
    print("TEST: Faction Decision Consequences")
    print("=" * 60)

    # Create mock game state
    game_state = MockGameState()

    # Get initial approval ratings
    merchants = game_state.faction_manager.get_by_name("The Merchant's Guild")
    warriors = game_state.faction_manager.get_by_name("The Warrior's Caste")
    priesthood = game_state.faction_manager.get_by_name("The Priesthood of the Sun")

    print("\n--- INITIAL APPROVAL RATINGS ---")
    print(f"Merchants: {merchants['approval']}")
    print(f"Warriors: {warriors['approval']}")
    print(f"Priesthood: {priesthood['approval']}")

    # Simulate a faction decision: Side with Merchants
    print("\n--- PLAYER DECISION: Side with The Merchant's Guild ---")
    chosen_faction = "The Merchant's Guild"
    opposed_factions = ["The Warrior's Caste", "The Priesthood of the Sun"]

    apply_faction_decision_consequences(game_state, chosen_faction, opposed_factions)

    # Get updated approval ratings
    print("\n--- UPDATED APPROVAL RATINGS ---")
    print(f"Merchants: {merchants['approval']} (expected: 80, change: +20)")
    print(f"Warriors: {warriors['approval']} (expected: 20, change: -40)")
    print(f"Priesthood: {priesthood['approval']} (expected: 20, change: -40)")

    # Verify the changes
    print("\n--- VERIFICATION ---")
    success = True

    if merchants['approval'] == 80:
        print("✓ Merchants approval correctly increased by +20")
    else:
        print(f"✗ Merchants approval incorrect: {merchants['approval']} (expected 80)")
        success = False

    if warriors['approval'] == 20:
        print("✓ Warriors approval correctly decreased by -40")
    else:
        print(f"✗ Warriors approval incorrect: {warriors['approval']} (expected 20)")
        success = False

    if priesthood['approval'] == 20:
        print("✓ Priesthood approval correctly decreased by -40")
    else:
        print(f"✗ Priesthood approval incorrect: {priesthood['approval']} (expected 20)")
        success = False

    print("\n" + "=" * 60)
    if success:
        print("TEST PASSED: Faction consequences are working correctly!")
    else:
        print("TEST FAILED: Faction consequences are not working as expected")
    print("=" * 60)

    return success

if __name__ == "__main__":
    success = test_faction_consequences()
    sys.exit(0 if success else 1)

