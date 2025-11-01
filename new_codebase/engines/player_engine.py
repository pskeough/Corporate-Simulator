# engines/player_engine.py
"""
Player Engine for Corporate Decision Simulator

Handles player-specific mechanics such as career progression, skill-based
effectiveness, and performance reviews.
"""

# Professional skills and their effects on the simulation
SKILL_EFFECTS = {
    'Data Analysis': {
        'description': 'Proficient in analyzing data to derive insights.',
        'bonuses': {'investigation_depth': 1, 'budget_optimization': 0.05},
        'event_tags': ['data', 'finance', 'strategy']
    },
    'Project Management': {
        'description': 'Skilled in organizing projects and leading teams to meet deadlines.',
        'bonuses': {'project_success_chance': 0.15, 'team_efficiency': 0.10},
        'event_tags': ['project', 'team', 'deadline']
    },
    'Public Speaking': {
        'description': 'A confident and persuasive communicator.',
        'bonuses': {'negotiation_bonus': 0.10, 'political_capital_gain': 0.05},
        'event_tags': ['communication', 'negotiation', 'presentation']
    },
    'Negotiation': {
        'description': 'Adept at finding mutually beneficial agreements.',
        'bonuses': {'negotiation_bonus': 0.20, 'cross_department_collaboration': 0.10},
        'penalties': {'direct_confrontation_success': -0.05},
        'event_tags': ['negotiation', 'deal', 'conflict_resolution']
    },
    # Gained through career progression
    'Experienced Manager': {
        'description': 'Seasoned by years of management.',
        'bonuses': {'team_efficiency': 0.15, 'decision_quality': 0.10},
        'penalties': {},
        'event_tags': ['management', 'leadership', 'mentorship']
    }
}

def get_skill_bonus(player, bonus_type):
    """
    Calculates the total bonus from a player's skills for a specific bonus type.
    """
    skills = player.get('skills', [])
    total_bonus = 0

    for skill in skills:
        skill_data = SKILL_EFFECTS.get(skill, {})
        bonuses = skill_data.get('bonuses', {})
        if bonus_type in bonuses:
            total_bonus += bonuses[bonus_type]

        penalties = skill_data.get('penalties', {})
        if bonus_type in penalties:
            total_bonus += penalties[bonus_type]

    return total_bonus

def apply_career_progression_effects(game_state):
    """
    Applies effects based on the player's career stage, such as gaining new skills.
    """
    player = game_state.player
    years_in_role = player.get('years_in_role', 0)
    skills = player.get('skills', [])
    changes = []

    # Gain "Experienced Manager" skill after 3 years in a management role
    if "Manager" in player.get('title', '') and years_in_role >= 3 and 'Experienced Manager' not in skills:
        skills.append('Experienced Manager')
        changes.append("gained 'Experienced Manager' skill")

    player['skills'] = skills
    return changes

def calculate_player_effectiveness(player, game_state=None):
    """
    Calculates the player's overall effectiveness based on their experience and skills.
    This multiplier can affect resource generation, project success, etc.
    """
    years_at_company = player.get('years_at_company', 0)
    skills = player.get('skills', [])
    effectiveness = 1.0

    # Experience-based effectiveness
    if years_at_company < 1:
        effectiveness *= 0.85 # New hire, still learning
    elif 1 <= years_at_company < 5:
        effectiveness *= 1.0  # Established employee
    else:
        effectiveness *= 1.15 # Veteran employee

    # Skill-based bonuses
    if 'Project Management' in skills:
        effectiveness *= 1.05
    if 'Experienced Manager' in skills:
        effectiveness *= 1.10

    # Apply penalty if the company is in a crisis state
    if game_state and hasattr(game_state, 'crisis_momentum') and game_state.crisis_momentum > 0:
        crisis_penalty = min(0.25, game_state.crisis_momentum * 0.05) # Max 25% penalty
        effectiveness *= (1.0 - crisis_penalty)

    return max(0.5, min(2.0, effectiveness)) # Clamp between 0.5x and 2.0x
