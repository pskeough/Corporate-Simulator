"""
World Modes Module

This module contains different world generation modes for the Civilization game.
Each mode provides unique world generation logic, faction templates, and historical frameworks.

Available modes:
- fantasy: Randomized fantasy setting (original behavior)
- historical_earth: Historical Earth simulation with butterfly effects
"""

from engines.world_modes.base_mode import WorldMode
from engines.world_modes.fantasy_mode import FantasyWorldMode
from engines.world_modes.historical_earth_mode import HistoricalEarthMode

__all__ = ['WorldMode', 'FantasyWorldMode', 'HistoricalEarthMode']

