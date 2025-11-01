"""
Image Update Manager - Intelligent decision logic for when to regenerate images.

This module determines when character portraits and settlement images should be updated
based on significant game state changes, while avoiding excessive API calls.
"""

from typing import Dict, Any, Optional, Tuple
import copy


class ImageUpdateTracker:
    """Tracks the last state when images were generated to detect significant changes."""

    def __init__(self):
        self.last_portrait_state = {}
        self.last_settlement_state = {}

    def update_portrait_state(self, game_state):
        """Record current state after generating a portrait."""
        leader = game_state.civilization.get('leader', {})
        self.last_portrait_state = {
            'age': leader.get('age', 0),
            'traits': copy.deepcopy(leader.get('traits', [])),
            'wealth': game_state.civilization.get('resources', {}).get('wealth', 0),
            'turns_since_update': 0
        }

    def update_settlement_state(self, game_state):
        """Record current state after generating a settlement image."""
        civ = game_state.civilization
        self.last_settlement_state = {
            'population': civ.get('population', 0),
            'era': civ.get('meta', {}).get('era', 'stone_age'),
            'infrastructure': copy.deepcopy(civ.get('technology', {}).get('infrastructure', [])),
        }

    def increment_turns(self):
        """Increment turn counter for portrait updates."""
        if 'turns_since_update' in self.last_portrait_state:
            self.last_portrait_state['turns_since_update'] += 1


# Global tracker instance
_tracker = ImageUpdateTracker()


def should_update_leader_portrait(game_state,
                                  aging_changes: Optional[list] = None) -> Tuple[bool, str]:
    """
    Determine if the leader portrait should be regenerated.

    Returns:
        (should_update, reason) - Boolean and string explaining why
    """
    leader = game_state.civilization.get('leader', {})
    current_age = leader.get('age', 0)
    current_traits = leader.get('traits', [])
    current_wealth = game_state.civilization.get('resources', {}).get('wealth', 0)

    last_state = _tracker.last_portrait_state

    # First portrait generation (no previous state)
    if not last_state:
        return True, "Initial portrait generation"

    # Check 1: Every 10 turns (as requested)
    turns_since = last_state.get('turns_since_update', 0)
    if turns_since >= 10:
        return True, f"Regular update after {turns_since} turns"

    # Check 2: Trait changes (aging effects are significant)
    if aging_changes and len(aging_changes) > 0:
        # Only update for significant trait changes
        for change in aging_changes:
            if 'gained' in change.lower() or 'lost' in change.lower():
                return True, f"Trait change: {aging_changes[0]}"

    # Check 3: Significant age milestones (every 20% of life expectancy)
    last_age = last_state.get('age', 0)
    life_exp = leader.get('life_expectancy', 80)

    age_percent_now = (current_age / life_exp) * 100
    age_percent_last = (last_age / life_exp) * 100

    # Detect crossing 20% thresholds (0-20%, 20-40%, 40-60%, 60-80%, 80-100%)
    threshold_now = int(age_percent_now / 20)
    threshold_last = int(age_percent_last / 20)

    if threshold_now > threshold_last:
        return True, f"Age milestone: {threshold_now * 20}% of life expectancy"

    # Check 4: Wealth tier changes (major prosperity/poverty changes)
    last_wealth = last_state.get('wealth', 0)
    wealth_tier_now = _get_wealth_tier(current_wealth)
    wealth_tier_last = _get_wealth_tier(last_wealth)

    if wealth_tier_now != wealth_tier_last:
        return True, f"Wealth change: {wealth_tier_last} -> {wealth_tier_now}"

    # No significant changes detected
    return False, "No significant changes"


def should_update_settlement_image(game_state) -> Tuple[bool, str]:
    """
    Determine if the settlement image should be regenerated.

    Returns:
        (should_update, reason) - Boolean and string explaining why
    """
    civ = game_state.civilization
    current_pop = civ.get('population', 0)
    current_era = civ.get('meta', {}).get('era', 'stone_age')
    current_infra = civ.get('technology', {}).get('infrastructure', [])

    last_state = _tracker.last_settlement_state

    # First settlement generation (no previous state)
    if not last_state:
        return True, "Initial settlement generation"

    # Check 1: Era change (major visual impact)
    last_era = last_state.get('era', 'stone_age')
    if current_era != last_era:
        return True, f"Era change: {last_era} -> {current_era}"

    # Check 2: Population size category change
    last_pop = last_state.get('population', 0)
    size_cat_now = _get_settlement_size_category(current_pop)
    size_cat_last = _get_settlement_size_category(last_pop)

    if size_cat_now != size_cat_last:
        return True, f"Settlement growth: {size_cat_last} -> {size_cat_now}"

    # Check 3: Major infrastructure additions (only significant ones)
    last_infra = last_state.get('infrastructure', [])
    significant_infra = ['Walls', 'Great Temple', 'Grand Market', 'Palace', 'Observatory']

    for infra in current_infra:
        if infra in significant_infra and infra not in last_infra:
            return True, f"Major infrastructure: {infra} completed"

    # No significant changes detected
    return False, "No significant changes"


def _get_wealth_tier(wealth: int) -> str:
    """Categorize wealth into tiers for comparison."""
    if wealth < 50:
        return "impoverished"
    elif wealth < 200:
        return "modest"
    elif wealth < 500:
        return "prosperous"
    elif wealth < 1000:
        return "wealthy"
    else:
        return "opulent"


def _get_settlement_size_category(population: int) -> str:
    """Categorize population into settlement size categories."""
    if population < 100:
        return "camp"
    elif population < 500:
        return "village"
    elif population < 2000:
        return "town"
    elif population < 10000:
        return "city"
    else:
        return "metropolis"


def get_tracker() -> ImageUpdateTracker:
    """Get the global image update tracker."""
    return _tracker


def reset_tracker():
    """Reset the tracker (useful for testing or new games)."""
    global _tracker
    _tracker = ImageUpdateTracker()

