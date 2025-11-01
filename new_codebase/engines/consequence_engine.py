# engines/consequence_engine.py
"""
Tracks long-term consequences of player decisions and manages corporate reputation.
Enables callback events based on past actions and policy changes.
"""

import re

def initialize_consequences(game_state):
    """Initializes consequence tracking in the game state if not present."""
    if 'consequences' not in game_state.corporation:
        game_state.corporation['consequences'] = {
            'policies': [],        # List of enacted corporate policies
            'promises': [],        # Promises made to departments or personnel
            'broken_promises': [],
            'department_relations': {}, # Tracks sentiment between departments
            'reputation': {
                'employee_trust': 50,
                'market_prestige': 50,
                'investor_confidence': 50
            }
        }

def detect_major_policy_change(action_text, event_title, outcome_text):
    """
    Detects if a player's action constitutes a major, lasting policy change.
    """
    combined_text = (action_text + ' ' + event_title + ' ' + outcome_text).lower()

    policy_keywords = ['new policy', 'mandate', 'company-wide', 'protocol', 'reform']
    permanence_keywords = ['permanently', 'henceforth', 'effective immediately']

    significance_score = 0
    policy_type = 'operational'

    for keyword in policy_keywords:
        if keyword in combined_text:
            significance_score += 15

    for keyword in permanence_keywords:
        if keyword in combined_text:
            significance_score += 10

    if significance_score >= 15:
        importance = 'major' if significance_score >= 25 else 'significant'
        return {
            'type': policy_type,
            'importance': importance,
            'significance_score': significance_score,
            'action_text': action_text,
            'event_title': event_title
        }
    return None

def analyze_action_for_consequences(action_text, event_title, outcome_text):
    """
    Analyzes a player's action to detect promises, changes in inter-departmental
    relations, and shifts in corporate reputation.
    """
    action_lower = action_text.lower()
    consequences = {
        'promises': [],
        'reputation_changes': {}
    }

    promise_keywords = ['promise', 'commit to', 'guarantee', 'assure']
    for keyword in promise_keywords:
        if keyword in action_lower:
            consequences['promises'].append({
                'text': action_text,
                'event': event_title,
                'fulfilled': False
            })
            break

    if 'trust' in outcome_text.lower() or 'confidence' in outcome_text.lower():
        if 'increased' in outcome_text.lower():
            consequences['reputation_changes']['employee_trust'] = 5
        elif 'decreased' in outcome_text.lower() or 'eroded' in outcome_text.lower():
            consequences['reputation_changes']['employee_trust'] = -10

    return consequences

def apply_consequences(game_state, action_text, event_title, outcome_text):
    """
    Applies the detected consequences of an action to the game state.
    """
    initialize_consequences(game_state)
    detected = analyze_action_for_consequences(action_text, event_title, outcome_text)

    for promise in detected['promises']:
        game_state.corporation['consequences']['promises'].append(promise)
        print(f"  📜 Promise recorded: '{promise['text'][:50]}...'")

    for rep_type, change in detected['reputation_changes'].items():
        old_rep = game_state.corporation['consequences']['reputation'][rep_type]
        new_rep = max(0, min(100, old_rep + change))
        game_state.corporation['consequences']['reputation'][rep_type] = new_rep
        print(f"  📊 {rep_type.replace('_', ' ').title()} reputation: {old_rep} → {new_rep} ({change:+d})")

def get_consequence_context(game_state):
    """
    Builds a summary of the current corporate climate based on past consequences.
    """
    initialize_consequences(game_state)
    conseq = game_state.corporation['consequences']
    context_parts = []

    unfulfilled_promises = [p for p in conseq.get('promises', []) if not p.get('fulfilled')]
    if unfulfilled_promises:
        context_parts.append(f"Unfulfilled promises to stakeholders: {len(unfulfilled_promises)}")

    rep = conseq.get('reputation', {})
    rep_summary = f"Reputation - Employee Trust: {rep.get('employee_trust', 50)}, Market Prestige: {rep.get('market_prestige', 50)}"
    context_parts.append(rep_summary)

    return "\n".join(context_parts) if context_parts else "No significant long-term consequences yet."

def check_for_callback_opportunity(game_state):
    """
    Checks if a past decision should trigger a new follow-up event.
    """
    initialize_consequences(game_state)
    conseq = game_state.corporation['consequences']
    import random

    # Check for callbacks related to old, unfulfilled promises
    unfulfilled_promises = [p for p in conseq.get('promises', []) if not p.get('fulfilled')]
    if len(unfulfilled_promises) >= 1:
        old_promises = [p for p in unfulfilled_promises if game_state.turn_number - p.get('turn', 0) >= 4]
        if old_promises and random.random() < 0.50:
            return True, 'broken_promise', old_promises[0]

    return False, None, None
