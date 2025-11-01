# engines/consequence_engine.py
"""
Tracks consequences of player decisions and manages civilization reputation.
Enables callback events based on past actions.
"""

import re

def initialize_consequences(game_state):
    """Initialize consequence tracking if not present."""
    if 'consequences' not in game_state.civilization:
        game_state.civilization['consequences'] = {
            'promises': [],        # List of promises made
            'broken_promises': [], # List of broken promises
            'alliances': [],       # List of allied groups/civilizations
            'enemies': [],         # List of hostile groups/civilizations
            'reputation': {
                'diplomatic': 50,  # 0-100 scale
                'military': 50,
                'religious': 50,
                'economic': 50
            },
            'debts': [],          # Outstanding debts or obligations
            'favors_owed': [],    # Favors owed to others
            'favors_held': []     # Favors others owe to you
        }

def detect_major_declaration(action_text, event_title, outcome_text):
    """
    Detect if the action is a major declaration (law, decree, constitutional change, etc.)
    Returns dict with declaration details or None
    """
    action_lower = action_text.lower()
    combined = (action_text + ' ' + event_title + ' ' + outcome_text).lower()

    # Keywords indicating major declarations
    holy_law_keywords = ['holy law', 'divine law', 'sacred mandate', 'religious decree', 'god commands', 'divine mandate']
    constitutional_keywords = ['constitution', 'fundamental law', 'government reform', 'restructure government', 'new order']
    cultural_keywords = ['forever', 'eternal', 'all time', 'never forget', 'law stands', 'decree', 'mandate', 'proclaim']
    permanence_keywords = ['forever', 'eternal', 'permanently', 'all time', 'eternity', 'everlasting', 'always']
    authority_keywords = ['decree', 'declare', 'proclaim', 'mandate', 'establish', 'ordain', 'command']

    # Calculate significance score
    significance_score = 0
    decree_type = 'cultural'  # Default

    # Check for holy law indicators (highest weight)
    for keyword in holy_law_keywords:
        if keyword in combined:
            significance_score += 30
            decree_type = 'holy_law'
            break

    # Check for constitutional indicators
    for keyword in constitutional_keywords:
        if keyword in combined:
            significance_score += 25
            decree_type = 'constitutional'
            break

    # Check for permanence language (strong indicator)
    permanence_count = sum(1 for keyword in permanence_keywords if keyword in combined)
    significance_score += permanence_count * 10

    # Check for authority language
    authority_count = sum(1 for keyword in authority_keywords if keyword in combined)
    significance_score += authority_count * 5

    # Check for scope indicators (affects entire civilization)
    scope_keywords = ['all', 'every', 'entire', 'civilization', 'nation', 'people', 'society', 'everyone']
    scope_count = sum(1 for keyword in scope_keywords if keyword in combined)
    significance_score += scope_count * 3

    # Check for enforcement language
    enforcement_keywords = ['enforce', 'punish', 'execute', 'killed', 'death', 'forbidden', 'banned', 'illegal']
    enforcement_count = sum(1 for keyword in enforcement_keywords if keyword in combined)
    significance_score += enforcement_count * 5

    # Length check - declarations are usually substantial
    if len(action_text) > 200:
        significance_score += 10

    # Categorize importance based on score
    importance = 'minor'
    if significance_score >= 50:
        importance = 'civilization_defining'
    elif significance_score >= 30:
        importance = 'major'
    elif significance_score >= 15:
        importance = 'significant'

    # Only return if this seems like a major declaration (score >= 15)
    if significance_score >= 15:
        return {
            'type': decree_type,
            'importance': importance,
            'significance_score': significance_score,
            'action_text': action_text,
            'event_title': event_title
        }

    return None

def analyze_action_for_consequences(action_text, event_title, outcome_text):
    """
    Analyze player action to detect promises, alliances, conflicts, etc.
    Returns dict of detected consequences.
    """
    action_lower = action_text.lower()
    event_lower = event_title.lower()
    outcome_lower = outcome_text.lower()

    consequences = {
        'promises': [],
        'alliances': [],
        'enemies': [],
        'debts': [],
        'reputation_changes': {},
        'major_declaration': None  # For civilization-defining decrees
    }

    # Detect major declarations (holy laws, constitutional changes, major decrees)
    major_declaration = detect_major_declaration(action_text, event_title, outcome_text)
    if major_declaration:
        consequences['major_declaration'] = major_declaration

    # Detect promises (keywords: promise, swear, vow, guarantee, agree to)
    promise_keywords = ['promise', 'swear', 'vow', 'guarantee', 'pledge', 'agree to', 'commit to']
    for keyword in promise_keywords:
        if keyword in action_lower:
            # Extract what was promised
            promise = {
                'text': action_text,
                'event': event_title,
                'fulfilled': False
            }
            consequences['promises'].append(promise)
            break

    # Detect alliances (keywords: ally, alliance, unite, join forces, peace treaty)
    alliance_keywords = ['ally', 'alliance', 'unite', 'join forces', 'peace treaty', 'pact', 'partner']
    for keyword in alliance_keywords:
        if keyword in action_lower or keyword in outcome_lower:
            # Try to extract ally name from event or action
            ally_match = re.search(r'(?:with |to )(the )?([\w\s]+?)(?:\s+clan|\s+tribe|\s+people|\s+nation|\.|\,)', action_lower + ' ' + event_lower)
            ally_name = ally_match.group(2).strip().title() if ally_match else "Unknown Ally"

            alliance = {
                'name': ally_name,
                'event': event_title,
                'strength': 50  # 0-100, starts at neutral alliance
            }
            consequences['alliances'].append(alliance)
            consequences['reputation_changes']['diplomatic'] = 10
            break

    # Detect enemies (keywords: attack, reject, insult, war, hostile, refuse)
    enemy_keywords = ['attack', 'declare war', 'reject', 'insult', 'hostile', 'refuse', 'betray', 'raid']
    for keyword in enemy_keywords:
        if keyword in action_lower:
            # Try to extract enemy name
            enemy_match = re.search(r'(?:against |the )?([\w\s]+?)(?:\s+clan|\s+tribe|\s+people|\s+nation|\.|\,)', action_lower + ' ' + event_lower)
            enemy_name = enemy_match.group(1).strip().title() if enemy_match else "Unknown Enemy"

            enemy = {
                'name': enemy_name,
                'event': event_title,
                'hostility': 50  # 0-100, higher = more hostile
            }
            consequences['enemies'].append(enemy)
            consequences['reputation_changes']['military'] = 10
            consequences['reputation_changes']['diplomatic'] = -10
            break

    # Detect debts/obligations (keywords: borrow, debt, owe, loan, pay later)
    debt_keywords = ['borrow', 'debt', 'owe', 'loan', 'pay later', 'on credit']
    for keyword in debt_keywords:
        if keyword in action_lower or keyword in outcome_lower:
            debt = {
                'description': action_text,
                'event': event_title,
                'repaid': False
            }
            consequences['debts'].append(debt)
            consequences['reputation_changes']['economic'] = -5
            break

    # Reputation changes based on action type
    if 'help' in action_lower or 'aid' in action_lower or 'assist' in action_lower:
        consequences['reputation_changes']['diplomatic'] = consequences['reputation_changes'].get('diplomatic', 0) + 5

    if 'trade' in action_lower or 'merchant' in action_lower or 'sell' in action_lower:
        consequences['reputation_changes']['economic'] = consequences['reputation_changes'].get('economic', 0) + 5

    if 'pray' in action_lower or 'ritual' in action_lower or 'temple' in action_lower or 'sacred' in action_lower:
        consequences['reputation_changes']['religious'] = consequences['reputation_changes'].get('religious', 0) + 5

    if 'defend' in action_lower or 'fortify' in action_lower or 'military' in action_lower:
        consequences['reputation_changes']['military'] = consequences['reputation_changes'].get('military', 0) + 5

    return consequences

def apply_consequences(game_state, action_text, event_title, outcome_text):
    """
    Apply detected consequences to game state.
    """
    initialize_consequences(game_state)

    detected = analyze_action_for_consequences(action_text, event_title, outcome_text)

    # Apply promises
    for promise in detected['promises']:
        game_state.civilization['consequences']['promises'].append(promise)
        print(f"  📜 Promise recorded: '{promise['text'][:50]}...'")

    # Apply alliances
    for alliance in detected['alliances']:
        # Check if ally already exists
        existing = next((a for a in game_state.civilization['consequences']['alliances'] if a['name'] == alliance['name']), None)
        if existing:
            existing['strength'] = min(100, existing['strength'] + 10)
            print(f"  🤝 Alliance strengthened: {alliance['name']} (strength: {existing['strength']})")
        else:
            game_state.civilization['consequences']['alliances'].append(alliance)
            print(f"  🤝 New alliance formed: {alliance['name']}")

    # Apply enemies
    for enemy in detected['enemies']:
        # Check if enemy already exists
        existing = next((e for e in game_state.civilization['consequences']['enemies'] if e['name'] == enemy['name']), None)
        if existing:
            existing['hostility'] = min(100, existing['hostility'] + 10)
            print(f"  ⚔️ Hostility increased: {enemy['name']} (hostility: {existing['hostility']})")
        else:
            game_state.civilization['consequences']['enemies'].append(enemy)
            print(f"  ⚔️ New enemy made: {enemy['name']}")

    # Apply debts
    for debt in detected['debts']:
        game_state.civilization['consequences']['debts'].append(debt)
        print(f"  💳 Debt incurred: {debt['description'][:50]}...")

    # Apply reputation changes
    for rep_type, change in detected['reputation_changes'].items():
        old_rep = game_state.civilization['consequences']['reputation'][rep_type]
        new_rep = max(0, min(100, old_rep + change))
        game_state.civilization['consequences']['reputation'][rep_type] = new_rep

        if change != 0:
            direction = "+" if change > 0 else ""
            print(f"  📊 {rep_type.title()} reputation: {old_rep} → {new_rep} ({direction}{change})")

    # BALANCE_OVERHAUL: Broken promises incur severe penalties
    if 'broken_promise' in action_text.lower() or 'betrayed' in action_text.lower():
        # Triple the diplomatic penalty
        old_rep = game_state.civilization['consequences']['reputation']['diplomatic']
        new_rep = max(0, old_rep - 30)  # -30 instead of -10
        game_state.civilization['consequences']['reputation']['diplomatic'] = new_rep
        print(f"  💔 BROKEN PROMISE: Diplomatic reputation crashed by -30 (now {new_rep})")

def get_consequence_context(game_state):
    """
    Build a summary of consequences for event generation.
    Returns formatted string for AI prompt.
    """
    initialize_consequences(game_state)
    conseq = game_state.civilization['consequences']

    context_parts = []

    # Active promises
    active_promises = [p for p in conseq['promises'] if not p.get('fulfilled', False)]
    if active_promises:
        context_parts.append(f"Unfulfilled promises: {len(active_promises)}")

    # Broken promises (trust issues)
    if conseq['broken_promises']:
        context_parts.append(f"Broken promises: {len(conseq['broken_promises'])} (reputation damaged)")

    # Alliances
    if conseq['alliances']:
        strong_allies = [a['name'] for a in conseq['alliances'] if a.get('strength', 0) > 70]
        if strong_allies:
            context_parts.append(f"Strong allies: {', '.join(strong_allies[:3])}")

    # Enemies
    if conseq['enemies']:
        hostile_enemies = [e['name'] for e in conseq['enemies'] if e.get('hostility', 0) > 70]
        if hostile_enemies:
            context_parts.append(f"Hostile enemies: {', '.join(hostile_enemies[:3])}")

    # Outstanding debts
    unpaid_debts = [d for d in conseq['debts'] if not d.get('repaid', False)]
    if unpaid_debts:
        context_parts.append(f"Unpaid debts: {len(unpaid_debts)}")

    # Reputation summary
    rep = conseq['reputation']
    rep_summary = f"Reputation - Diplomatic: {rep['diplomatic']}, Military: {rep['military']}, Religious: {rep['religious']}, Economic: {rep['economic']}"
    context_parts.append(rep_summary)

    return "\n".join(context_parts) if context_parts else "No significant consequences yet."

def check_for_callback_opportunity(game_state):
    """
    BALANCE_OVERHAUL: Check if there's an opportunity for a callback event.
    Increased probabilities to make consequences return more frequently.
    Returns (bool, callback_type, callback_data) or (False, None, None)
    """
    initialize_consequences(game_state)
    conseq = game_state.civilization['consequences']
    import random

    # BALANCE_OVERHAUL: Broken promise callback - dramatically increased
    active_promises = [p for p in conseq['promises'] if not p.get('fulfilled', False)]
    if len(active_promises) >= 2:
        # Old promises (5+ turns) have 70% callback chance
        old_promises = [p for p in active_promises if game_state.turn_number - p.get('turn', 0) >= 5]
        if old_promises and random.random() < 0.70:  # Increased from 0.30
            return True, 'broken_promise', old_promises[0]

    # BALANCE_OVERHAUL: Enemy revenge - increased
    hostile_enemies = [e for e in conseq['enemies'] if e.get('hostility', 0) > 60]
    if hostile_enemies:
        if random.random() < 0.40:  # Increased from 0.25
            return True, 'enemy_revenge', hostile_enemies[0]

    # BALANCE_OVERHAUL: Ally request - increased
    strong_allies = [a for a in conseq['alliances'] if a.get('strength', 0) > 50]
    if strong_allies:
        if random.random() < 0.35:  # Increased from 0.20
            return True, 'ally_request', strong_allies[0]

    # BALANCE_OVERHAUL: Debt collection - increased
    unpaid_debts = [d for d in conseq['debts'] if not d.get('repaid', False)]
    if unpaid_debts:
        old_debts = [d for d in unpaid_debts if game_state.turn_number - d.get('turn', 0) >= 3]
        if old_debts and random.random() < 0.50:  # Increased from 0.30
            return True, 'debt_collection', old_debts[0]

    return False, None, None

