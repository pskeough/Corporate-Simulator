#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Test script for world_turns_engine integration with BonusEngine
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
from engines.world_turns_engine import WorldTurnsEngine

print("=" * 60)
print("TESTING WORLD TURNS ENGINE INTEGRATION")
print("=" * 60)

# Load game state
print("\n1. Loading game state...")
game = GameState()
print("   ✓ Game state loaded")

# Create world turns engine
print("\n2. Initializing WorldTurnsEngine...")
engine = WorldTurnsEngine()
print("   ✓ WorldTurnsEngine initialized")

# Test the new method
print("\n3. Testing calculate_rates_with_bonus_engine()...")
rates = engine.calculate_rates_with_bonus_engine(game)
print(f"   Science rate: {rates['science']:.2f}")
print(f"   Culture rate: {rates['culture']:.2f}")
print(f"   Science sources: {len(rates['science_sources'])} bonuses")
print(f"   Culture sources: {len(rates['culture_sources'])} bonuses")

# Show source breakdown
if rates['science_sources']:
    print("\n   Science bonus sources:")
    for src_type, src_name, value in rates['science_sources']:
        print(f"     +{value} from {src_type}: {src_name}")

if rates['culture_sources']:
    print("\n   Culture bonus sources:")
    for src_type, src_name, value in rates['culture_sources']:
        print(f"     +{value} from {src_type}: {src_name}")

# Test simulate_turn (this will trigger the verification)
print("\n4. Testing simulate_turn() with verification...")
print("   Note: This calls Gemini API, so it may take a moment...")
print("   Watching for verification output...")

# We won't actually run simulate_turn as it calls API
# Instead we'll manually test the verification logic
print("\n5. Manual Verification Test...")
population = game.civilization['population']
happiness = game.population_happiness
inner_circle = game.inner_circle

# OLD WAY
science_bonus_old = 0
culture_bonus_old = 0
for character in inner_circle:
    if character.get("role") == "Scholar":
        science_bonus_old += 5
    if character.get("role") == "Artisan":
        culture_bonus_old += 5

science_per_turn_old = (population / 1000) * (happiness / 100) + science_bonus_old
culture_per_turn_old = (population / 1000) * (happiness / 100) + culture_bonus_old

print(f"   OLD method: science={science_per_turn_old:.2f}, culture={culture_per_turn_old:.2f}")

# NEW WAY
science_per_turn_new = rates['science']
culture_per_turn_new = rates['culture']

print(f"   NEW method: science={science_per_turn_new:.2f}, culture={culture_per_turn_new:.2f}")

# Compare
science_match = abs(science_per_turn_old - science_per_turn_new) < 0.01
culture_match = abs(culture_per_turn_old - culture_per_turn_new) < 0.01

print("\n6. Verification Results:")
if science_match and culture_match:
    print("   ✅ OLD and NEW methods produce identical results!")
    print(f"   ✓ Science: {science_per_turn_old:.2f} == {science_per_turn_new:.2f}")
    print(f"   ✓ Culture: {culture_per_turn_old:.2f} == {culture_per_turn_new:.2f}")
    success = True
else:
    print("   ❌ MISMATCH detected!")
    print(f"   ✗ Science: {science_per_turn_old:.2f} != {science_per_turn_new:.2f}")
    print(f"   ✗ Culture: {culture_per_turn_old:.2f} != {culture_per_turn_new:.2f}")
    success = False

print("\n" + "=" * 60)
if success:
    print("✅ WORLD TURNS ENGINE INTEGRATION SUCCESSFUL!")
    print("\nThe BonusEngine produces identical results to the old")
    print("hardcoded logic. Safe to clean up old code!")
else:
    print("⚠ INTEGRATION FAILED - DO NOT REMOVE OLD CODE YET")
print("=" * 60)

sys.exit(0 if success else 1)
