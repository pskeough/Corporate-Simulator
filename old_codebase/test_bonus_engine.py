#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Test script for BonusEngine - Verify bonus calculations match expected behavior.
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
from engines.bonus_engine import BonusEngine
from engines.bonus_definitions import BonusType

print("=" * 60)
print("TESTING BONUS ENGINE")
print("=" * 60)

# Load actual game state
print("\n1. Loading game state...")
game = GameState()
print("   ✓ Game state loaded successfully")

# Create bonus engine
print("\n2. Initializing BonusEngine...")
engine = BonusEngine()
print("   ✓ BonusEngine initialized")

# Test science bonuses (should find Scholar in inner circle)
print("\n3. Testing Science Bonuses...")
science = engine.calculate_bonuses(game, BonusType.SCIENCE_PER_TURN)
print(f"   Total science bonus: +{science['total']}")
if science['sources']:
    for source_type, source_name, value in science['sources']:
        print(f"     +{value} from {source_type}: {source_name}")
else:
    print("     (No science bonuses found)")

# Test culture bonuses (should find Artisan in inner circle)
print("\n4. Testing Culture Bonuses...")
culture = engine.calculate_bonuses(game, BonusType.CULTURE_PER_TURN)
print(f"   Total culture bonus: +{culture['total']}")
if culture['sources']:
    for source_type, source_name, value in culture['sources']:
        print(f"     +{value} from {source_type}: {source_name}")
else:
    print("     (No culture bonuses found)")

# Test food bonuses (should be 0 currently)
print("\n5. Testing Food Bonuses...")
food = engine.calculate_bonuses(game, BonusType.FOOD_PER_TURN)
print(f"   Total food bonus: +{food['total']}")
if food['sources']:
    for source_type, source_name, value in food['sources']:
        print(f"     +{value} from {source_type}: {source_name}")
else:
    print("     (No food bonuses found - expected)")

# Test full summary
print("\n6. Full Bonus Summary:")
print("=" * 60)
summary = engine.format_bonus_summary(game)
print(summary)
print("=" * 60)

# Verify against world_turns_engine current logic
print("\n7. Verification Against Expected Values:")
print("   Expected science: 5 per Scholar in inner circle")
print(f"   Actual science: {science['total']}")
print("   Expected culture: 5 per Artisan in inner circle")
print(f"   Actual culture: {culture['total']}")

# Check if we found the expected bonuses
success = True
scholar_found = any(role == 'Scholar' for char in game.inner_circle_manager for role in [char.get('role')])
artisan_found = any(role == 'Artisan' for char in game.inner_circle_manager for role in [char.get('role')])

print("\n8. Inner Circle Analysis:")
print(f"   Total characters: {len(game.inner_circle_manager)}")
for char in game.inner_circle_manager:
    print(f"     - {char.get('name')}: {char.get('role', 'No role')}")

print("\n9. Test Results:")
if scholar_found and science['total'] >= 5:
    print("   ✓ Science bonus working correctly (Scholar found)")
elif not scholar_found and science['total'] == 0:
    print("   ✓ Science bonus working correctly (no Scholar present)")
else:
    print("   ⚠ Science bonus mismatch")
    success = False

if artisan_found and culture['total'] >= 5:
    print("   ✓ Culture bonus working correctly (Artisan found)")
elif not artisan_found and culture['total'] == 0:
    print("   ✓ Culture bonus working correctly (no Artisan present)")
else:
    print("   ⚠ Culture bonus mismatch")
    success = False

# Test invalid bonus type handling
print("\n10. Testing Invalid Bonus Type Handling...")
invalid = engine.calculate_bonuses(game, 'invalid_bonus_type')
if invalid['total'] == 0 and not invalid['sources']:
    print("   ✓ Invalid bonus type handled gracefully")
else:
    print("   ⚠ Invalid bonus type not handled properly")
    success = False

print("\n" + "=" * 60)
if success:
    print("✅ ALL BONUS ENGINE TESTS PASSED!")
else:
    print("⚠ SOME TESTS FAILED - CHECK OUTPUT ABOVE")
print("=" * 60)

sys.exit(0 if success else 1)
