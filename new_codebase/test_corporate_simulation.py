#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Test script for the Corporate Decision Simulator.
"""

import sys
import os
import io
import unittest

# Force UTF-8 encoding for Windows
if sys.platform == 'win32':
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

# Add parent directory to path
sys.path.insert(0, os.path.dirname(__file__))

class TestCorporateSimulation(unittest.TestCase):
    def test_game_state_load(self):
        """Test that the game state loads correctly with corporate data."""
        from game_state import GameState
        game = GameState()

        self.assertIn('name', game.corporation)
        self.assertIn('headcount', game.corporation)
        self.assertIn('name', game.player)
        self.assertIn('title', game.player)
        self.assertIn('skills', game.player)
        self.assertIn('stated_values', game.company_culture)
        self.assertIn('mission_statement_name', game.corporate_mission)
        self.assertIn('player', game.skills_and_assets)
        self.assertIn('competitors', game.market_and_competitors)

    def test_resource_engine(self):
        """Test the corporate resource engine."""
        from game_state import GameState
        from engines.resource_engine import calculate_overhead, generate_revenue_generation
        game = GameState()

        overhead = calculate_overhead(game)
        self.assertGreater(overhead['budget'], 0)
        self.assertEqual(overhead['political_capital'], 5)

        revenue = generate_revenue_generation(game)
        self.assertGreater(revenue['budget'], 0)
        self.assertGreater(revenue['political_capital'], 0)

    def test_crisis_engine(self):
        """Test the corporate crisis engine."""
        from game_state import GameState
        from engines.crisis_engine import detect_crisis
        game = GameState()

        # Normal state
        crisis = detect_crisis(game)
        self.assertIsNone(crisis)

        # Trigger a crisis
        game.corporation['budget'] = 0
        crisis = detect_crisis(game)
        self.assertEqual(crisis, 'BankruptcyWarning')

    def test_consequence_engine(self):
        """Test the corporate consequence engine."""
        from game_state import GameState
        from engines.consequence_engine import analyze_action_for_consequences
        game = GameState()

        action = "I promise the sales team a bonus if they hit their targets."
        consequences = analyze_action_for_consequences(action, "Sales Meeting", "outcome")
        self.assertEqual(len(consequences['promises']), 1)
        self.assertEqual(consequences['promises'][0]['text'], action)

if __name__ == "__main__":
    unittest.main()
