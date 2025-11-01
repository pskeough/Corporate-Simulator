# engines/state_updater.py
"""
State Updater Module

This module handles applying updates to the game state, including
both regular turn updates and world turn updates from NPCs and factions.

Refactored from event_engine.py for better maintainability and separation of concerns.
"""

import re
from engines.state_validator import validate_updates

def calculate_life_expectancy(era):
    """Calculate realistic life expectancy based on civilization era."""
    era_life_expectancy = {
        'stone_age': 35,
        'bronze_age': 40,
        'iron_age': 45,
        'classical': 50,
        'medieval': 55,
        'renaissance': 60,
        'industrial': 65,
        'modern': 75
    }
    return era_life_expectancy.get(era.lower(), 50)

def apply_updates(game_state, updates, is_timeskip=False):
    """
    Robustly applies updates from the AI to the game state using dot notation,
    including list indices and a custom '.append' syntax.
    Now with validation for better error handling and automatic leader succession.

    Args:
        game_state: The game state object to modify
        updates: Dictionary of updates to apply
        is_timeskip: If True, numeric values are treated as absolute replacements,
                     not incremental changes. Also allows list replacements.
    """
    mode = "Timeskip" if is_timeskip else "Turn"
    print(f"--- Applying AI {mode} Updates ---")

    # Validate updates first (with context-appropriate rules)
    is_valid, cleaned_updates, errors = validate_updates(updates, game_state, is_timeskip=is_timeskip)

    if errors:
        print("--- Validation Warnings (Timeskip) ---")
        for error in errors:
            print(f"  - {error}")

    # Use cleaned updates if available, otherwise fall back to original
    updates_to_apply = cleaned_updates if cleaned_updates else updates

    # Check if new leader is being set - if so, ensure years_ruled resets
    leader_keys = [k for k in updates_to_apply.keys() if 'civilization.leader' in k]
    if 'civilization.leader.name' in updates_to_apply:
        # New leader succession - ensure proper reset
        if 'civilization.leader.years_ruled' not in updates_to_apply:
            updates_to_apply['civilization.leader.years_ruled'] = 0
            print("  ⚠ Auto-resetting years_ruled to 0 for new leader")

        # Get the era (either from updates or current state)
        era = updates_to_apply.get('civilization.meta.era') or game_state.civilization.get('meta', {}).get('era', 'stone_age')
        expected_life_exp = calculate_life_expectancy(era)

        # Validate and correct life expectancy
        if 'civilization.leader.life_expectancy' in updates_to_apply:
            ai_life_exp = updates_to_apply['civilization.leader.life_expectancy']
            # Check if AI value is realistic (within ±25 of expected)
            if abs(ai_life_exp - expected_life_exp) > 25:
                print(f"  ⚠ AI provided unrealistic life_expectancy ({ai_life_exp}) for {era} era. Correcting to {expected_life_exp}")
                updates_to_apply['civilization.leader.life_expectancy'] = expected_life_exp
        else:
            # No life expectancy provided - set it
            updates_to_apply['civilization.leader.life_expectancy'] = expected_life_exp
            print(f"  ⚠ Auto-setting life_expectancy to {expected_life_exp} based on {era} era")

    state_map = {
        "civilization": game_state.civilization,
        "culture": game_state.culture,
        "religion": game_state.religion,
        "technology": game_state.technology,
        "world": game_state.world
    }

    for key_path, value in updates_to_apply.items():
        try:
            is_append = key_path.endswith('.append')
            if is_append:
                key_path = key_path[:-7]

            parts = key_path.split('.')

            if parts[0] not in state_map:
                print(f"Warning: Invalid root key '{parts[0]}' in path. Skipping.")
                continue

            current_obj = state_map[parts[0]]

            # Traverse down to the object/list that needs modification
            for part in parts[1:-1]:
                match = re.match(r"(\w+)\[(\d+)\]", part)
                if match:
                    key, index = match.groups()
                    current_obj = current_obj[key][int(index)]
                else:
                    if part not in current_obj:
                        print(f"Warning: Path segment '{part}' not found in '{key_path}'. Skipping.")
                        break
                    current_obj = current_obj[part]
            else:
                last_part = parts[-1]

                if is_append:
                    if last_part not in current_obj:
                        print(f"Warning: Target list '{last_part}' not found in '{key_path}'. Skipping.")
                        continue

                    target_list = current_obj[last_part]
                    if isinstance(target_list, list):
                        if isinstance(value, str) and value not in target_list:
                            target_list.append(value)
                            print(f"  ✓ Appended '{value}' to {'.'.join(parts)}")
                        elif isinstance(value, dict):
                            target_list.append(value)
                            print(f"  ✓ Appended object to {'.'.join(parts)}")
                    else:
                        print(f"Warning: '{key_path}' is not a list, cannot append.")
                else:
                    # Handle assignment to a specific list index or a dictionary key
                    match = re.match(r"(\w+)\[(\d+)\]", last_part)
                    if match:
                        key, index = match.groups()
                        current_obj[key][int(index)] = value
                        print(f"  ✓ Set {key_path} = {value}")
                    else:
                        target = current_obj.get(last_part)

                        # Timeskip mode: always replace values (absolute assignment)
                        if is_timeskip:
                            old_value = current_obj[last_part]
                            current_obj[last_part] = value

                            # Show different formatting for different types
                            if isinstance(value, int) and isinstance(old_value, int):
                                print(f"  ✓ Set {'.'.join(parts)}: {old_value} → {value}")
                            elif isinstance(value, list):
                                print(f"  ✓ Replaced {'.'.join(parts)} with {len(value)} items")
                            else:
                                print(f"  ✓ Set {'.'.join(parts)} = {value}")

                        # Turn mode: add integers, replace everything else
                        else:
                            if isinstance(target, int) and isinstance(value, int):
                                old_value = current_obj[last_part]
                                current_obj[last_part] += value
                                print(f"  ✓ Updated {'.'.join(parts)}: {old_value} → {current_obj[last_part]} ({value:+d})")
                            else:
                                current_obj[last_part] = value
                                print(f"  ✓ Set {'.'.join(parts)} = {value}")
        except (KeyError, IndexError, TypeError, ValueError) as e:
            print(f"Error applying update '{key_path}': {e}. Path may be invalid or type mismatch. Skipping.")

    # Check if settlement image should be updated (after all updates applied)
    from engines.image_update_manager import should_update_settlement_image
    should_update, reason = should_update_settlement_image(game_state)
    if should_update:
        print(f"  🎨 Updating settlement image: {reason}")
        # Trigger background settlement update
        from engines.visual_engine import update_settlement_image_async
        update_settlement_image_async(game_state)

    # Prune lists to prevent infinite growth
    prune_cultural_lists(game_state)
    print("------------------------------------")

def prune_cultural_lists(game_state):
    """
    Prevents culture values, traditions, and discoveries from growing infinitely.
    Keeps only the most recent/relevant items (max 15 each).
    """
    max_items = 15

    # Prune culture values (keep last 15)
    if len(game_state.culture.get('values', [])) > max_items:
        original_len = len(game_state.culture['values'])
        game_state.culture['values'] = game_state.culture['values'][-max_items:]
        print(f"  ⚠ Pruned culture.values from {original_len} to {max_items} items")

    # Prune culture traditions (keep last 15)
    if len(game_state.culture.get('traditions', [])) > max_items:
        original_len = len(game_state.culture['traditions'])
        game_state.culture['traditions'] = game_state.culture['traditions'][-max_items:]
        print(f"  ⚠ Pruned culture.traditions from {original_len} to {max_items} items")

    # Prune technology discoveries (keep last 20 for tech)
    max_tech = 20
    if len(game_state.technology.get('discoveries', [])) > max_tech:
        original_len = len(game_state.technology['discoveries'])
        game_state.technology['discoveries'] = game_state.technology['discoveries'][-max_tech:]
        print(f"  ⚠ Pruned technology.discoveries from {original_len} to {max_tech} items")


def apply_world_turn_updates(game_state, world_updates):
    """Applies updates from the WorldTurnsEngine to the game state."""
    if not isinstance(world_updates, dict):
        print("Warning: world_updates is not a dictionary. Skipping.")
        return

    # Process faction updates using manager
    faction_updates = world_updates.get('faction_updates', [])
    if faction_updates:
        if not hasattr(game_state, 'faction_manager'):
            print("Warning: No faction manager available. Skipping faction updates.")
        else:
            for update in faction_updates:
                faction_name = update.get('name')
                if faction_name:
                    approval_change = update.get('approval_change', 0)
                    reason = update.get('reason', 'World events')
                    # Use manager for update (handles both ID and name lookups)
                    success = game_state.faction_manager.update_approval(faction_name, approval_change)
                    if success:
                        faction = game_state.faction_manager.get_by_name(faction_name)
                        # Add history entry for this change
                        game_state.faction_manager.add_history_entry(
                            faction_name,
                            reason,
                            approval_change,
                            game_state.turn_number
                        )
                        print(f"  - Faction '{faction_name}' approval changed by {approval_change:+d} to {faction['approval']}")
                    else:
                        print(f"  - Warning: Faction '{faction_name}' not found")

    # Process inner circle updates using manager
    inner_circle_updates = world_updates.get('inner_circle_updates', [])
    if inner_circle_updates:
        if not hasattr(game_state, 'inner_circle_manager'):
            print("Warning: No inner circle manager available. Skipping inner circle updates.")
        else:
            for update in inner_circle_updates:
                char_name = update.get('name')
                if char_name:
                    loyalty_change = update.get('loyalty_change', 0)
                    opinion_change = update.get('opinion_change', 0)
                    # Use manager for update (maps opinion_change to relationship)
                    success = game_state.inner_circle_manager.update_metrics(
                        char_name,
                        loyalty=loyalty_change,
                        relationship=opinion_change
                    )
                    if success:
                        print(f"  - Inner Circle '{char_name}' loyalty changed by {loyalty_change:+d}, opinion by {opinion_change:+d}")
                    else:
                        print(f"  - Warning: Character '{char_name}' not found")

                    # Add memory if provided (for council meetings)
                    if update.get('memory'):
                        mem_success = game_state.inner_circle_manager.add_memory(
                            char_name,
                            update['memory'],
                            game_state.turn_number
                        )
                        if mem_success:
                            print(f"  📝 Added memory for '{char_name}': {update['memory']}")
                        else:
                            print(f"  - Warning: Could not add memory for '{char_name}'")

    # Process neighboring civilization updates
    neighboring_civilization_updates = world_updates.get('neighboring_civilization_updates', [])
    if neighboring_civilization_updates:
        known_peoples = game_state.world.get('known_peoples', [])
        if not isinstance(known_peoples, list):
            print("Warning: known_peoples is not a list. Skipping neighbor updates.")
        else:
            # Relationship ladder: hostile → unfriendly → neutral → friendly → allied
            relationship_ladder = ["hostile", "unfriendly", "neutral", "friendly", "allied"]

            for update in neighboring_civilization_updates:
                civ_name = update.get('name')
                if civ_name:
                    # Find the civilization
                    civ = None
                    for people in known_peoples:
                        if people.get('name') == civ_name:
                            civ = people
                            break

                    if civ:
                        relationship_change = update.get('relationship_change', 0)
                        current_relationship = civ.get('relationship', 'neutral')

                        # Find current position on ladder
                        try:
                            current_index = relationship_ladder.index(current_relationship)
                        except ValueError:
                            # Default to neutral if current relationship not recognized
                            current_index = 2

                        # Calculate new position (clamped to ladder bounds)
                        # Each +/-10 points = one step on the ladder
                        steps = relationship_change // 10
                        new_index = max(0, min(len(relationship_ladder) - 1, current_index + steps))
                        new_relationship = relationship_ladder[new_index]

                        # Update the relationship
                        civ['relationship'] = new_relationship

                        if new_relationship != current_relationship:
                            print(f"  - Neighbor '{civ_name}' relationship changed from {current_relationship} to {new_relationship} (change: {relationship_change:+d})")
                        else:
                            print(f"  - Neighbor '{civ_name}' relationship unchanged ({current_relationship}, change: {relationship_change:+d})")
                    else:
                        print(f"  - Warning: Civilization '{civ_name}' not found in known_peoples")

