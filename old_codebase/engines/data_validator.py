# engines/data_validator.py
"""
Data integrity validation for game state.
Checks referential integrity without modifying data.
"""

def validate_faction_references(game_state):
    """
    Validates that all faction_id references in inner_circle point to valid factions.

    Args:
        game_state: The GameState object containing all game data

    Returns:
        list: List of validation error messages (empty if all valid)
    """
    errors = []

    # Get factions data - handle both dict and list formats for backward compatibility
    factions_data = game_state.factions
    if isinstance(factions_data, dict):
        factions_list = factions_data.get('factions', [])
    elif isinstance(factions_data, list):
        factions_list = factions_data
    else:
        return ["ERROR: Invalid factions data structure"]

    # Build set of valid faction IDs
    valid_faction_ids = set()
    for faction in factions_list:
        if isinstance(faction, dict) and 'id' in faction:
            valid_faction_ids.add(faction['id'])

    # If no faction IDs found, system not yet migrated - skip validation
    if not valid_faction_ids:
        return []

    # Check inner circle references
    inner_circle = game_state.inner_circle
    if not isinstance(inner_circle, list):
        return ["ERROR: Invalid inner_circle data structure"]

    for character in inner_circle:
        if not isinstance(character, dict):
            continue

        char_name = character.get('name', 'Unknown')
        faction_id = character.get('faction_id')

        # Only validate if faction_id exists (backward compatibility)
        if faction_id:
            if faction_id not in valid_faction_ids:
                errors.append(
                    f"Character '{char_name}' references invalid faction_id: '{faction_id}'"
                )

    return errors


def validate_all(game_state):
    """
    Runs all validation checks on the game state.

    Args:
        game_state: The GameState object containing all game data

    Returns:
        dict: Dictionary with validation results
            {
                'valid': bool,
                'errors': list of error messages,
                'warnings': list of warning messages
            }
    """
    all_errors = []
    warnings = []

    # Check faction references
    faction_errors = validate_faction_references(game_state)
    all_errors.extend(faction_errors)

    # Add more validators here as they are created
    # e.g., validate_building_references(game_state)
    # e.g., validate_tech_references(game_state)

    return {
        'valid': len(all_errors) == 0,
        'errors': all_errors,
        'warnings': warnings
    }
