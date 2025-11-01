# engines/context_builder.py
"""
Centralized context management for AI prompts.
Reduces token usage and provides smart, targeted context for each engine.
"""
import json

def get_recent_history_summary(history_long, num_events=5):
    """
    Returns only the most recent N events from history.
    Drastically reduces token usage vs sending full history.
    """
    events = history_long.get("events", [])[-num_events:]
    return {"events": events}

def get_civilization_snapshot(game_state):
    """Returns core civilization data without redundancies."""
    return {
        "meta": game_state.civilization['meta'],
        "leader": game_state.civilization['leader'],
        "population": game_state.civilization['population'],
        "resources": game_state.civilization['resources']
    }

def get_cultural_context(game_state):
    """Returns streamlined cultural data."""
    return {
        "values": game_state.culture.get('values', [])[:10],  # Limit to prevent duplicates
        "traditions": game_state.culture.get('traditions', [])[:10],
        "taboos": game_state.culture.get('taboos', []),
        "social_structure": game_state.culture.get('social_structure', 'Unknown')
    }

def get_religious_context(game_state):
    """Returns streamlined religious data."""
    return {
        "name": game_state.religion.get('name', 'Unknown'),
        "type": game_state.religion.get('type', 'Unknown'),
        "primary_deity": game_state.religion.get('primary_deity', 'Unknown'),
        "core_tenets": game_state.religion.get('core_tenets', []),
        "influence": game_state.religion.get('influence', 'moderate')
    }

def get_technology_context(game_state):
    """Returns technology state without redundancy."""
    return {
        "current_tier": game_state.technology.get('current_tier', 'stone_age'),
        "recent_discoveries": game_state.technology.get('discoveries', [])[-8:],  # Last 8 discoveries
        "infrastructure": game_state.technology.get('infrastructure', [])[-6:]  # Last 6 infrastructure
    }

def get_world_context(game_state):
    """Returns world/geography context."""
    return game_state.world

def build_event_context(game_state):
    """
    Builds optimized context for event generation.
    ~60% token reduction vs sending everything.
    """
    return {
        "civilization": get_civilization_snapshot(game_state),
        "culture": get_cultural_context(game_state),
        "religion": get_religious_context(game_state),
        "technology": get_technology_context(game_state),
        "world": get_world_context(game_state),
        "recent_history": get_recent_history_summary(game_state.history_long, num_events=6)
    }

def build_action_context(game_state):
    """
    Builds optimized context for action processing.
    Includes all relevant state for determining consequences.
    """
    return {
        "civilization": get_civilization_snapshot(game_state),
        "culture": get_cultural_context(game_state),
        "religion": get_religious_context(game_state),
        "technology": get_technology_context(game_state),
        "world": get_world_context(game_state)
    }

def build_timeskip_context(game_state):
    """
    Builds context for timeskip (needs more history for 500-year jump).
    """
    return {
        "civilization": get_civilization_snapshot(game_state),
        "culture": get_cultural_context(game_state),
        "religion": get_religious_context(game_state),
        "technology": get_technology_context(game_state),
        "world": get_world_context(game_state),
        "recent_history": get_recent_history_summary(game_state.history_long, num_events=12)
    }

def build_image_context(game_state):
    """
    Builds context for image generation.
    Focuses on visual/aesthetic elements.
    """
    return {
        "civilization": {
            "name": game_state.civilization['meta']['name'],
            "era": game_state.civilization['meta']['era'],
            "population": game_state.civilization['population'],
            "tech_tier": game_state.civilization['resources']['tech_tier']
        },
        "culture": {
            "values": game_state.culture.get('values', [])[:5],
            "social_structure": game_state.culture.get('social_structure', 'Unknown')
        },
        "religion": {
            "name": game_state.religion.get('name', 'Unknown'),
            "holy_sites": game_state.religion.get('holy_sites', [])
        },
        "world": game_state.world['geography'],
        "recent_major_events": get_recent_history_summary(game_state.history_long, num_events=3)
    }

def get_last_event_summary(history_long):
    """
    Returns a brief summary of the last event for consequence chaining.
    """
    events = history_long.get("events", [])
    if not events:
        return None

    last_event = events[-1]
    return {
        "title": last_event.get("title", "Unknown Event"),
        "action": last_event.get("action", "Unknown Action"),
        "outcome": last_event.get("narrative", "Unknown Outcome")
    }

def get_recent_event_titles(history_long, num=3):
    """
    Returns titles of recent events to avoid repetition.
    """
    events = history_long.get("events", [])[-num:]
    return [event.get("title", "") for event in events]
