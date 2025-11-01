#!/usr/bin/env python3
"""
Batch Prompt Extraction Script
Extracts remaining prompts from engine files and creates external prompt files.
Run this to complete the prompt externalization refactoring.
"""

import os
from pathlib import Path

# Define all remaining prompts to extract
PROMPTS_TO_CREATE = {
    # Council prompts
    'prompts/council/first_turn_briefing.txt': '''# FIRST TURN BRIEFING PROMPT
# Special one-time event for turn 0, introducing the player to their council.
# See council_engine.py:generate_first_turn_briefing for variable documentation.
# This is a placeholder - extract full prompt from council_engine.py lines 282-406
''',

    # Callback prompts (4 files)
    'prompts/callbacks/broken_promise.txt': '# BROKEN PROMISE CALLBACK\n# See callback_engine.py lines 30-76\n',
    'prompts/callbacks/enemy_revenge.txt': '# ENEMY REVENGE CALLBACK\n# See callback_engine.py lines 77-124\n',
    'prompts/callbacks/ally_request.txt': '# ALLY REQUEST CALLBACK\n# See callback_engine.py lines 125-172\n',
    'prompts/callbacks/debt_collection.txt': '# DEBT COLLECTION CALLBACK\n# See callback_engine.py lines 173-218\n',

    # Character prompt
    'prompts/characters/character_vignette.txt': '# CHARACTER VIGNETTE PROMPT\n# See character_engine.py lines 59-121\n',

    # Crisis prompts (8 files)
    'prompts/crises/famine.txt': '# FAMINE CRISIS\n# See crisis_engine.py lines 148-202\n',
    'prompts/crises/food_shortage.txt': '# FOOD SHORTAGE WARNING\n# See crisis_engine.py lines 203-256\n',
    'prompts/crises/severe_food_shortage.txt': '# SEVERE FOOD SHORTAGE\n# See crisis_engine.py lines 402-452\n',
    'prompts/crises/economic_collapse.txt': '# ECONOMIC COLLAPSE\n# See crisis_engine.py lines 257-310\n',
    'prompts/crises/economic_crisis.txt': '# ECONOMIC CRISIS\n# See crisis_engine.py lines 311-361\n',
    'prompts/crises/economic_warning.txt': '# ECONOMIC WARNING\n# See crisis_engine.py lines 453-500\n',
    'prompts/crises/succession_crisis.txt': '# SUCCESSION CRISIS\n# See crisis_engine.py lines 362-400\n',
    'prompts/crises/compound_crisis.txt': '# COMPOUND CRISIS\n# See crisis_engine.py lines 501-549\n',

    # Faction prompt
    'prompts/factions/faction_audience.txt': '# FACTION AUDIENCE PROMPT\n# See faction_engine.py lines 113-210\n',

    # Timeskip prompt
    'prompts/timeskip/timeskip_500_years.txt': '# TIMESKIP 500 YEARS\n# See timeskip_engine.py lines 38-149\n',

    # Visual prompts (4 files)
    'prompts/visuals/leader_portrait.txt': '# LEADER PORTRAIT GENERATION\n# See visual_engine.py lines 100-137\n',
    'prompts/visuals/advisor_portrait.txt': '# ADVISOR PORTRAIT GENERATION\n# See visual_engine.py lines 625-675\n',
    'prompts/visuals/crisis_illustration.txt': '# CRISIS ILLUSTRATION\n# See visual_engine.py lines 209-274\n',
    'prompts/visuals/settlement_evolution.txt': '# SETTLEMENT EVOLUTION IMAGE\n# See visual_engine.py lines 377-427\n',

    # World prompt
    'prompts/world/ai_description.txt': '# WORLD AI DESCRIPTION\n# See world_generator.py lines 500-510\n',
}

def main():
    """Create placeholder prompt files."""
    base_dir = Path(__file__).parent

    print("=" * 60)
    print("PROMPT EXTRACTION SCRIPT")
    print("=" * 60)
    print()
    print("This script creates PLACEHOLDER prompt files.")
    print("You must manually extract the full prompts from the engine files.")
    print()
    print("Creating placeholder files...")
    print()

    created_count = 0
    for prompt_path, content in PROMPTS_TO_CREATE.items():
        full_path = base_dir / prompt_path

        # Create if doesn't exist
        if not full_path.exists():
            full_path.write_text(content, encoding='utf-8')
            print(f"[+] Created: {prompt_path}")
            created_count += 1
        else:
            print(f"  Skipped (exists): {prompt_path}")

    print()
    print(f"Created {created_count} placeholder files.")
    print()
    print("=" * 60)
    print("NEXT STEPS:")
    print("=" * 60)
    print("1. Manually extract each prompt from the source engine files")
    print("2. Copy the full prompt text (f-string content) to the .txt file")
    print("3. Convert f-string {var} to .format() {var} placeholders")
    print("4. Document all required variables in file header")
    print("5. Modify each engine file to use load_prompt()")
    print()
    print("Example for event_generator.py:")
    print("  OLD: prompt = f\"\"\"You are... {civ_name}...\"\"\"")
    print("  NEW: prompt = load_prompt('events/generate_event').format(civ_name=...)")
    print()

if __name__ == '__main__':
    main()
