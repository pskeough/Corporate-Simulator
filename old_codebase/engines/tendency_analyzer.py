# engines/tendency_analyzer.py
"""
Advanced player tendency analysis for event generation.
Analyzes player behavior patterns to create personalized events.
"""

def analyze_player_tendency(history_long, num_events=5):
    """
    Analyzes recent player actions and outcomes to determine behavioral tendencies.
    Returns primary tendency and secondary tendency for richer event generation.
    """
    tendencies = {
        "culture": 0,
        "religion": 0,
        "technology": 0,
        "survival": 0,
        "diplomacy": 0,
        "warfare": 0,
        "exploration": 0,
        "chaos": 0
    }

    # Keyword mappings with weighted importance
    keyword_map = {
        "culture": ["culture", "tradition", "value", "art", "festival", "pottery", "craft", "story"],
        "religion": ["faith", "spirit", "ritual", "pray", "deity", "sacred", "divine", "shaman", "worship"],
        "technology": ["tool", "discover", "build", "invent", "construct", "forge", "craft", "innovate", "improve"],
        "survival": ["food", "hunt", "gather", "survive", "shelter", "winter", "famine", "harvest"],
        "diplomacy": ["clan", "stranger", "trade", "ally", "peace", "negotiate", "treaty", "gift"],
        "warfare": ["attack", "defend", "raid", "battle", "weapon", "enemy", "conquer", "blood"],
        "exploration": ["scout", "explore", "venture", "journey", "discover", "cave", "unknown", "map"],
        "chaos": ["burn", "destroy", "mad", "chaos", "wild", "reckless", "desperate", "abandon"]
    }

    events = history_long.get("events", [])[-num_events:]

    if not events:
        return "survival", "balanced"

    # Analyze both actions and outcomes with recency weighting
    for i, event in enumerate(events):
        # More recent events weighted higher
        recency_weight = (i + 1) / len(events)

        action = event.get("action", "").lower()
        outcome = event.get("narrative", "").lower()

        # Analyze action (player intent)
        for tendency, keywords in keyword_map.items():
            for keyword in keywords:
                if keyword in action:
                    tendencies[tendency] += 2.0 * recency_weight  # Actions weighted more than outcomes
                if keyword in outcome:
                    tendencies[tendency] += 1.0 * recency_weight

    # If no clear tendency, return survival
    if max(tendencies.values()) == 0:
        return "survival", "balanced"

    # Get primary tendency
    primary = max(tendencies, key=tendencies.get)

    # Get secondary tendency (second highest, but must be significant)
    sorted_tendencies = sorted(tendencies.items(), key=lambda x: x[1], reverse=True)
    secondary = sorted_tendencies[1][0] if sorted_tendencies[1][1] > sorted_tendencies[0][1] * 0.5 else None

    return primary, secondary if secondary else "balanced"

def get_tendency_description(primary, secondary):
    """Returns a human-readable description of player tendencies."""
    desc_map = {
        "culture": "cultural development and artistic expression",
        "religion": "spiritual matters and religious devotion",
        "technology": "technological advancement and innovation",
        "survival": "ensuring survival and resource management",
        "diplomacy": "diplomatic relations and trade",
        "warfare": "military strength and conquest",
        "exploration": "exploration and discovery",
        "chaos": "unpredictable and risky decisions"
    }

    primary_desc = desc_map.get(primary, "balanced survival")

    if secondary and secondary != "balanced":
        secondary_desc = desc_map.get(secondary, "")
        return f"{primary_desc}, with secondary focus on {secondary_desc}"
    else:
        return primary_desc

