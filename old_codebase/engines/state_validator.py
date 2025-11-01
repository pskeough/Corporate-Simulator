# engines/state_validator.py
"""
Validates AI-generated state updates before applying them.
Prevents invalid paths, out-of-bounds values, and malformed updates.

SCHEMA DOCUMENTATION:
---------------------
Valid update paths for AI:

NUMERIC UPDATES (incremental changes):
  - civilization.population: ±1000 (change to population)
  - civilization.resources.food: ±2000 (change to food stores)
  - civilization.resources.wealth: ±5000 (change to wealth)
  - civilization.leader.age: +0 to +2 (automatic aging, rarely modified)

APPEND OPERATIONS (add new items to lists):
  - culture.values.append: string (new cultural value)
  - culture.traditions.append: string (new tradition)
  - culture.taboos.append: string (new taboo)
  - religion.practices.append: string (new religious practice)
  - religion.core_tenets.append: string (new core belief)
  - religion.holy_sites.append: string (new sacred location)
  - technology.discoveries.append: string (new discovery)
  - technology.infrastructure.append: string (new infrastructure)

RESTRICTIONS:
  - Cannot create new keys at civilization root (e.g., civilization.scouts_dispatched)
  - Cannot use invalid root keys (e.g., population.change, food.change, narrative.append)
  - Cannot append to lists that don't exist in schema
  - Values are clamped to reasonable bounds
  - Duplicates are automatically filtered
"""

def validate_updates(updates, game_state, is_timeskip=False):
    """
    Validates AI update object before application.
    Returns (is_valid, cleaned_updates, errors)

    Args:
        updates: Dictionary of updates to validate
        game_state: The current game state
        is_timeskip: If True, uses more lenient validation rules for 500-year jumps
    """
    errors = []
    cleaned_updates = {}

    state_map = {
        "civilization": game_state.civilization,
        "culture": game_state.culture,
        "religion": game_state.religion,
        "technology": game_state.technology,
        "world": game_state.world
    }

    for key_path, value in updates.items():
        # Skip empty or invalid paths
        if not key_path or not isinstance(key_path, str):
            errors.append(f"Invalid key path: {key_path}")
            continue

        # Parse path
        keys = key_path.split('.')

        # Validate root key
        if keys[0] not in state_map:
            errors.append(f"Invalid root key '{keys[0]}' in path '{key_path}'")
            continue

        # Check if this is an append operation
        is_append = keys[-1] == 'append'

        # Validate path exists
        try:
            current_level = state_map[keys[0]]

            # For append operations, we need to navigate to the parent dict containing the list
            # For "culture.traditions.append": navigate through [] (nothing), final_key = "traditions"
            # For "culture.subkey.traditions.append": navigate through ["subkey"], final_key = "traditions"
            if is_append:
                path_keys = keys[1:-2] if len(keys) > 2 else []
                final_key = keys[-2]
            else:
                path_keys = keys[1:-1]
                final_key = keys[-1]

            # Navigate to the parent level
            for key in path_keys:
                if isinstance(current_level, dict) and key not in current_level:
                    errors.append(f"Path not found: '{key_path}' (missing '{key}')")
                    break
                current_level = current_level[key]
            else:
                # For append operations, verify the target is a list
                if is_append:
                    if isinstance(current_level, dict) and final_key in current_level:
                        if not isinstance(current_level[final_key], list):
                            errors.append(f"Cannot append to non-list at '{key_path}' (target is {type(current_level[final_key]).__name__})")
                            continue
                    else:
                        # List doesn't exist - reject the append
                        valid_append_paths = [
                            'culture.values.append', 'culture.traditions.append', 'culture.taboos.append',
                            'religion.practices.append', 'religion.core_tenets.append', 'religion.holy_sites.append',
                            'technology.discoveries.append', 'technology.infrastructure.append'
                        ]
                        errors.append(f"List path not found: '{key_path}' - '{final_key}' does not exist. Valid append paths: {', '.join(valid_append_paths)}")
                        continue
                # For regular operations, STRICTLY block creating new keys
                elif isinstance(current_level, dict) and final_key not in current_level:
                    # Block all new key creation - the schema must already have the key
                    errors.append(f"Cannot create new key '{final_key}' at '{key_path}'. Key does not exist in schema. Only existing keys can be updated.")
                    continue

                # Validate value bounds
                if isinstance(current_level, dict):
                    target = current_level.get(final_key)
                elif isinstance(current_level, list):
                    # For list operations, target is the list itself
                    target = current_level
                else:
                    errors.append(f"Invalid path type at '{key_path}'")
                    continue

                validated_value = validate_value(key_path, target, value, is_timeskip=is_timeskip)

                if validated_value is not None:
                    cleaned_updates[key_path] = validated_value
                else:
                    errors.append(f"Invalid value for '{key_path}': {value}")

        except (KeyError, TypeError) as e:
            errors.append(f"Path validation error for '{key_path}': {str(e)}")
            continue

    is_valid = len(errors) == 0
    return is_valid, cleaned_updates, errors

def validate_value(key_path, target, value, is_timeskip=False):
    """
    Validates individual values with bounds checking.
    Returns cleaned value or None if invalid.

    Args:
        key_path: The dot-notation path being validated
        target: The current value at that path
        value: The new value to validate
        is_timeskip: If True, uses absolute value validation for 500-year jumps
    """
    # Numeric bounds checking
    if isinstance(target, int) and isinstance(value, int):
        # Specific bounds for different fields
        if 'population' in key_path:
            if is_timeskip:
                # Timeskip: absolute population value (0 to 100,000)
                if value < 10:  # Minimum viable population
                    return 10
                if value > 100000:  # Reasonable cap for ancient/medieval era
                    return 100000
                return value
            else:
                # Turn: incremental change (±1000 max)
                if value < -target + 10:  # Prevent negative population
                    return max(-target + 10, -1000)
                if value > 1000:  # Limit population increase
                    return 1000
                return value

        elif 'food' in key_path:
            if is_timeskip:
                # Timeskip: absolute food value (-5000 to 20000)
                if value < -5000:
                    return -5000
                if value > 20000:
                    return 20000
                return value
            else:
                # Turn: incremental change (±2000 max)
                if value < -2000:
                    return -2000
                if value > 2000:
                    return 2000
                return value

        elif 'wealth' in key_path:
            if is_timeskip:
                # Timeskip: absolute wealth value (-10000 to 50000)
                if value < -10000:
                    return -10000
                if value > 50000:
                    return 50000
                return value
            else:
                # Turn: incremental change (±5000 max)
                if value < -5000:
                    return -5000
                if value > 5000:
                    return 5000
                return value

        elif 'age' in key_path:
            if is_timeskip:
                # Timeskip: absolute age value (0 to 100)
                if value < 0:
                    return 0
                if value > 100:
                    return 100
                return value
            else:
                # Turn: age increase (+0 to +2 per turn)
                if value < 0:
                    return 0
                if value > 2:
                    return 2
                return value

        elif 'year' in key_path:
            # Year advancement validation
            if 'meta.year' in key_path:
                if is_timeskip:
                    # Timeskip: must be exactly +500
                    if value != 500:
                        return 500
                else:
                    # Regular turn: must be exactly +1
                    if value != 1:
                        return 1
            return value

        return value

    # List validation
    elif isinstance(target, list):
        if is_timeskip and isinstance(value, list):
            # Timeskip: allow full list replacement
            if len(value) > 20:  # Reasonable max length
                return value[:20]  # Truncate if too long
            return value
        elif isinstance(value, str):
            # Append operation: add single string item
            if value in target:
                return None  # Skip duplicates
            if len(target) >= 20:
                return None  # Prevent infinite list growth
            return value
        else:
            return None

    # String/boolean - pass through
    elif isinstance(value, (str, bool)):
        return value

    # Type mismatch
    else:
        return None


def get_validation_summary(errors):
    """
    Creates a human-readable summary of validation errors.
    Useful for logging and debugging.

    Args:
        errors: List of error messages from validate_updates

    Returns:
        Formatted string summarizing the errors
    """
    if not errors:
        return "✓ All updates valid"

    summary = [f"⚠️ Found {len(errors)} validation error(s):"]

    # Categorize errors
    invalid_roots = []
    invalid_paths = []
    invalid_values = []
    new_keys = []

    for error in errors:
        if "Invalid root key" in error:
            invalid_roots.append(error)
        elif "Path not found" in error or "List path not found" in error:
            invalid_paths.append(error)
        elif "Cannot create new key" in error:
            new_keys.append(error)
        else:
            invalid_values.append(error)

    if invalid_roots:
        summary.append(f"\n  Invalid Root Keys ({len(invalid_roots)}):")
        for err in invalid_roots[:3]:  # Show first 3
            summary.append(f"    - {err}")
        if len(invalid_roots) > 3:
            summary.append(f"    ... and {len(invalid_roots) - 3} more")

    if invalid_paths:
        summary.append(f"\n  Invalid Paths ({len(invalid_paths)}):")
        for err in invalid_paths[:3]:
            summary.append(f"    - {err}")
        if len(invalid_paths) > 3:
            summary.append(f"    ... and {len(invalid_paths) - 3} more")

    if new_keys:
        summary.append(f"\n  Attempted New Key Creation ({len(new_keys)}):")
        for err in new_keys[:3]:
            summary.append(f"    - {err}")
        if len(new_keys) > 3:
            summary.append(f"    ... and {len(new_keys) - 3} more")

    if invalid_values:
        summary.append(f"\n  Invalid Values ({len(invalid_values)}):")
        for err in invalid_values[:3]:
            summary.append(f"    - {err}")
        if len(invalid_values) > 3:
            summary.append(f"    ... and {len(invalid_values) - 3} more")

    summary.append("\n  Refer to state_validator.py SCHEMA DOCUMENTATION for valid paths.")

    return "\n".join(summary)


def print_schema_help():
    """
    Prints the valid schema paths for reference.
    Useful for debugging and documentation.
    """
    print("=" * 60)
    print("STATE VALIDATOR - VALID UPDATE PATHS")
    print("=" * 60)
    print()
    print("NUMERIC UPDATES (incremental changes):")
    print("  civilization.population: ±1000")
    print("  civilization.resources.food: ±2000")
    print("  civilization.resources.wealth: ±5000")
    print()
    print("APPEND OPERATIONS (add to lists):")
    print("  culture.values.append")
    print("  culture.traditions.append")
    print("  culture.taboos.append")
    print("  religion.practices.append")
    print("  religion.core_tenets.append")
    print("  religion.holy_sites.append")
    print("  technology.discoveries.append")
    print("  technology.infrastructure.append")
    print()
    print("RESTRICTIONS:")
    print("  - No arbitrary key creation")
    print("  - No invalid root keys (must be: civilization, culture, religion, technology, world)")
    print("  - Values clamped to reasonable bounds")
    print("  - Duplicates filtered automatically")
    print("=" * 60)
