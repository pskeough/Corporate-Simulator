# engines/prompt_loader.py
"""
Prompt Loader Utility

Centralized system for loading AI prompts from external text files.
Separates prompt content from application logic for easier maintenance.
"""

import os
from pathlib import Path

# Cache for loaded prompts (avoids repeated file I/O)
_prompt_cache = {}


def load_prompt(prompt_path, use_cache=True):
    """
    Load a prompt from the /prompts directory.

    Args:
        prompt_path: Relative path within /prompts (e.g., 'events/generate_event')
        use_cache: Whether to use the in-memory cache (default: True)

    Returns:
        String containing the prompt template with {variables} for .format()

    Example:
        prompt = load_prompt('events/generate_event')
        filled = prompt.format(civ_name="Rome", leader_name="Caesar")
    """
    # Check cache first
    if use_cache and prompt_path in _prompt_cache:
        return _prompt_cache[prompt_path]

    # Construct full path
    base_dir = Path(__file__).parent.parent  # Go up to civilization_game/
    prompt_file = base_dir / 'prompts' / f'{prompt_path}.txt'

    try:
        with open(prompt_file, 'r', encoding='utf-8') as f:
            content = f.read()

        # Cache the loaded prompt
        if use_cache:
            _prompt_cache[prompt_path] = content

        return content

    except FileNotFoundError:
        error_msg = (
            f"⚠️ PROMPT FILE NOT FOUND: {prompt_file}\n"
            f"Expected location: prompts/{prompt_path}.txt\n"
            f"This is a critical error - the prompt file is missing."
        )
        print(error_msg)
        raise FileNotFoundError(error_msg)

    except Exception as e:
        error_msg = f"⚠️ ERROR LOADING PROMPT '{prompt_path}': {e}"
        print(error_msg)
        raise


def clear_cache():
    """Clear the prompt cache. Useful for reloading prompts during development."""
    global _prompt_cache
    _prompt_cache = {}
    print("✓ Prompt cache cleared")


def get_cached_prompts():
    """Return list of currently cached prompt paths. Useful for debugging."""
    return list(_prompt_cache.keys())

