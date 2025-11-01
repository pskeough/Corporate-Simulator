# engines/victory_engine.py
"""
Victory condition and failure state detection.
Tracks progress toward different win conditions and checks for game-ending failures.
"""

def initialize_victory_tracking(game_state):
    """Initialize victory tracking if not present."""
    if 'victory_progress' not in game_state.civilization:
        game_state.civilization['victory_progress'] = {
            'cultural': 0,      # 0-100
            'technological': 0, # 0-100
            'military': 0,      # 0-100
            'spiritual': 0,     # 0-100
            'diplomatic': 0     # 0-100 (bonus path)
        }

def calculate_victory_progress(game_state):
    """
    Calculate progress toward each victory condition.
    Returns dict with progress percentages and thresholds.
    """
    initialize_victory_tracking(game_state)

    progress = game_state.civilization['victory_progress']
    population = game_state.civilization['population']
    era = game_state.civilization['meta']['era']

    # Cultural Victory: Based on traditions, values, cultural influence
    cultural_factors = 0
    cultural_factors += min(len(game_state.culture.get('values', [])) * 3, 30)  # Max 30 from values
    cultural_factors += min(len(game_state.culture.get('traditions', [])) * 4, 40)  # Max 40 from traditions
    cultural_factors += min(game_state.civilization.get('consequences', {}).get('reputation', {}).get('diplomatic', 0) // 3, 30)  # Max 30 from reputation

    progress['cultural'] = min(100, cultural_factors)

    # Technological Victory: Based on discoveries, infrastructure, era
    tech_factors = 0
    tech_factors += min(len(game_state.technology.get('discoveries', [])) * 2, 40)  # Max 40 from discoveries
    tech_factors += min(len(game_state.technology.get('infrastructure', [])) * 3, 30)  # Max 30 from infrastructure

    # Era bonus (progression through ages)
    era_values = {
        'stone_age': 0, 'bronze_age': 10, 'iron_age': 20, 'classical': 30,
        'medieval': 40, 'renaissance': 50, 'industrial': 60, 'modern': 80
    }
    tech_factors += era_values.get(era, 0)

    progress['technological'] = min(100, tech_factors)

    # Military Victory: Based on enemies defeated, military reputation, population strength
    military_factors = 0
    enemies = game_state.civilization.get('consequences', {}).get('enemies', [])
    military_factors += min(len(enemies) * 15, 45)  # Max 45 from having enemies (shows conflict)

    military_rep = game_state.civilization.get('consequences', {}).get('reputation', {}).get('military', 0)
    military_factors += min(military_rep // 2, 50)  # Max 50 from military reputation

    # Population shows strength
    if population > 5000:
        military_factors += 10

    progress['military'] = min(100, military_factors)

    # Spiritual Victory: Based on religious influence, holy sites, religious reputation
    spiritual_factors = 0
    spiritual_factors += min(len(game_state.religion.get('holy_sites', [])) * 15, 45)  # Max 45 from holy sites
    spiritual_factors += min(len(game_state.religion.get('practices', [])) * 5, 25)  # Max 25 from practices

    religious_rep = game_state.civilization.get('consequences', {}).get('reputation', {}).get('religious', 0)
    spiritual_factors += min(religious_rep // 3, 30)  # Max 30 from religious reputation

    progress['spiritual'] = min(100, spiritual_factors)

    # Diplomatic Victory: Based on alliances, promises kept, diplomatic reputation
    diplomatic_factors = 0
    alliances = game_state.civilization.get('consequences', {}).get('alliances', [])
    strong_alliances = [a for a in alliances if a.get('strength', 0) > 70]
    diplomatic_factors += min(len(strong_alliances) * 20, 40)  # Max 40 from strong alliances

    diplomatic_rep = game_state.civilization.get('consequences', {}).get('reputation', {}).get('diplomatic', 0)
    diplomatic_factors += min(diplomatic_rep // 2, 50)  # Max 50 from diplomatic reputation

    # Penalty for broken promises
    broken_promises = len(game_state.civilization.get('consequences', {}).get('broken_promises', []))
    diplomatic_factors -= broken_promises * 10

    progress['diplomatic'] = max(0, min(100, diplomatic_factors))

    # Save progress
    game_state.civilization['victory_progress'] = progress

    return progress

def check_victory(game_state):
    """
    Check if any victory condition has been met.
    Returns (bool, victory_type, description) or (False, None, None)
    """
    progress = calculate_victory_progress(game_state)

    # Check each victory type (threshold: 100)
    for victory_type, score in progress.items():
        if score >= 100:
            descriptions = {
                'cultural': f"Your civilization's cultural influence has spread far and wide! With {len(game_state.culture.get('traditions', []))} unique traditions and {len(game_state.culture.get('values', []))} core values, your society has become the cultural beacon of the age!",
                'technological': f"Your civilization has achieved technological supremacy! Through {len(game_state.technology.get('discoveries', []))} groundbreaking discoveries, you've propelled humanity into the {game_state.civilization['meta']['era']} era!",
                'military': f"Your military might is unmatched! Through strength and conquest, your civilization has dominated all rivals. None dare oppose you now!",
                'spiritual': f"Your civilization has achieved spiritual enlightenment! With {len(game_state.religion.get('holy_sites', []))} sacred sites, {game_state.religion['name']} has become the guiding light for all people!",
                'diplomatic': f"Through masterful diplomacy and {len(game_state.civilization.get('consequences', {}).get('alliances', []))} strong alliances, your civilization has unified the known world in peace!"
            }

            return True, victory_type, descriptions.get(victory_type, "Victory achieved!")

    return False, None, None

def check_failure(game_state):
    """
    Check if any failure condition has been met.
    Returns (bool, failure_type, description) or (False, None, None)
    """
    population = game_state.civilization['population']
    food = game_state.civilization['resources']['food']
    wealth = game_state.civilization['resources']['wealth']

    # Starvation Collapse: Population too low + no food
    if population < 100 and food <= 0:
        return True, 'starvation', f"Your civilization has collapsed from starvation. The few survivors scatter to the winds, and {game_state.civilization['meta']['name']} fades into forgotten history."

    # Population Extinction
    if population <= 50:
        return True, 'extinction', f"Your people have dwindled to nothing. {game_state.civilization['meta']['name']} is no more, its memory lost to time."

    # Total Economic Collapse (sustained bankruptcy with infrastructure lost)
    # Tightened threshold from pop<500 to pop<200 for more realistic failure
    infrastructure = game_state.technology.get('infrastructure', [])
    if wealth <= 0 and len(infrastructure) == 0 and population < 200:
        return True, 'collapse', f"Economic ruin and infrastructure decay have brought {game_state.civilization['meta']['name']} to its knees. Your civilization crumbles into chaos and is absorbed by neighboring powers."

    # Conquered (too many powerful enemies)
    enemies = game_state.civilization.get('consequences', {}).get('enemies', [])
    powerful_enemies = [e for e in enemies if e.get('hostility', 0) > 80]
    if len(powerful_enemies) >= 3 and population < 1000:
        return True, 'conquest', f"Surrounded by hostile enemies and weakened by conflict, {game_state.civilization['meta']['name']} has been conquered and absorbed into rival civilizations."

    return False, None, None

def get_victory_status_summary(game_state):
    """
    Get a summary of current victory progress for UI display.
    """
    progress = calculate_victory_progress(game_state)

    # Find closest to victory
    sorted_progress = sorted(progress.items(), key=lambda x: x[1], reverse=True)

    summary = {
        'closest_victory': sorted_progress[0][0],
        'closest_progress': sorted_progress[0][1],
        'all_progress': progress,
        'recommendations': []
    }

    # Add recommendations based on current state
    if progress['cultural'] > 60:
        summary['recommendations'].append("Focus on cultural traditions and values")
    if progress['technological'] > 60:
        summary['recommendations'].append("Continue technological advancement")
    if progress['military'] > 60:
        summary['recommendations'].append("Build military strength and conquer enemies")
    if progress['spiritual'] > 60:
        summary['recommendations'].append("Establish holy sites and spread faith")
    if progress['diplomatic'] > 60:
        summary['recommendations'].append("Strengthen alliances and diplomatic ties")

    return summary
