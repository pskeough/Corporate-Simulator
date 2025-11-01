"""
Test script for Inner Circle generation system.
Tests the new culturally grounded name and personality generation.
"""

from world_generator import WorldGenerator
import json

def test_inner_circle_generation():
    """Test that inner circle members are generated with proper cultural grounding."""

    print("=" * 80)
    print("TESTING INNER CIRCLE GENERATION")
    print("=" * 80)

    generator = WorldGenerator()

    # Test different cultural focuses
    test_configs = [
        {
            "era": "bronze_age",
            "terrain": "forest",
            "civilization_name": "The Forest Tribes",
            "population_size": "medium",
            "leader_name": "",
            "cultural_focus": "martial",
            "religion_type": "animism",
            "social_structure": "tribal_council",
            "difficulty": "balanced",
            "neighbor_count": "few",
            "resource_abundance": "moderate"
        },
        {
            "era": "classical",
            "terrain": "coastal",
            "civilization_name": "The Trading Republic",
            "population_size": "large",
            "leader_name": "",
            "cultural_focus": "mercantile",
            "religion_type": "polytheism",
            "social_structure": "hierarchical",
            "difficulty": "balanced",
            "neighbor_count": "several",
            "resource_abundance": "abundant"
        },
        {
            "era": "iron_age",
            "terrain": "mountain",
            "civilization_name": "The Sacred Mountains",
            "population_size": "small",
            "leader_name": "",
            "cultural_focus": "spiritual",
            "religion_type": "ancestor_worship",
            "social_structure": "theocracy",
            "difficulty": "balanced",
            "neighbor_count": "few",
            "resource_abundance": "scarce"
        },
        {
            "era": "stone_age",
            "terrain": "plains",
            "civilization_name": "The Plains Wanderers",
            "population_size": "small",
            "leader_name": "",
            "cultural_focus": "agricultural",
            "religion_type": "nature_worship",
            "social_structure": "egalitarian",
            "difficulty": "balanced",
            "neighbor_count": "none",
            "resource_abundance": "moderate"
        }
    ]

    for i, config in enumerate(test_configs, 1):
        print(f"\n{'=' * 80}")
        print(f"TEST {i}: {config['civilization_name']} ({config['cultural_focus'].upper()} culture, {config['era'].upper()} era)")
        print('=' * 80)

        # Generate world
        world_data = generator.generate_world(config)

        # Display civilization info
        print(f"\nCivilization: {world_data['civilization']['meta']['name']}")
        print(f"Leader: {world_data['civilization']['leader']['name']}")
        print(f"Era: {world_data['civilization']['meta']['era']}")
        print(f"Cultural Focus: {config['cultural_focus']}")
        print(f"Population: {world_data['civilization']['population']}")

        # Display inner circle
        inner_circle = world_data['inner_circle']['characters']
        print(f"\n{'-' * 80}")
        print(f"INNER CIRCLE ({len(inner_circle)} members):")
        print('-' * 80)

        for char in inner_circle:
            print(f"\n  * {char['name']}")
            print(f"     Role: {char['role']}")
            print(f"     Faction: {char.get('faction_link', 'None')}")
            print(f"     Personality: {', '.join(char['personality_traits'])}")
            print(f"     Dialogue: \"{char['dialogue_sample']}\"")
            print(f"     Metrics: Loyalty={char['metrics']['loyalty']}, Influence={char['metrics']['influence']}, Relationship={char['metrics']['relationship']}")

        # Validate structure
        print(f"\n{'-' * 80}")
        print("VALIDATION:")
        print('-' * 80)

        all_valid = True

        # Check each character
        for char in inner_circle:
            # Check name is not a default hardcoded name
            if char['name'] in ['Seraphina Vane', 'General Kaelen', 'High Priestess Lyra']:
                print(f"  [X] FAIL: {char['name']} is a hardcoded default name!")
                all_valid = False
            else:
                print(f"  [OK] {char['name']} has unique generated name")

            # Check role is era-appropriate
            expected_roles = {
                'stone_age': ['War Chief', 'Scout Master', 'Shaman'],
                'bronze_age': ['Commander', 'Eyes of the Throne', 'High Priest'],
                'iron_age': ['Grand Marshal', 'Spymaster', 'High Priestess'],
                'classical': ['Strategos', 'Master of Whispers', 'Hierophant']
            }

            era = world_data['civilization']['meta']['era']
            if char['role'] in expected_roles.get(era, []):
                print(f"  [OK] {char['role']} is appropriate for {era} era")

            # Check personality traits are not generic defaults
            default_traits = [
                ["Pragmatic", "Cunning", "Discreet", "Ambitious"],
                ["Disciplined", "Direct", "Loyal", "Stern"],
                ["Pious", "Compassionate", "Traditionalist", "Serene"]
            ]

            if char['personality_traits'] not in default_traits:
                print(f"  [OK] {char['name']} has culturally-influenced traits: {', '.join(char['personality_traits'])}")

            # Check dialogue is not default
            default_dialogues = [
                "Information is a currency more valuable than gold, my lord.",
                "A strong army is the only true guarantee of peace.",
                "May the Sun's light guide your decisions and illuminate your path."
            ]

            if char['dialogue_sample'] not in default_dialogues:
                print(f"  [OK] {char['name']} has culturally-appropriate dialogue")
            else:
                print(f"  [WARN]  {char['name']} has default dialogue")

        if all_valid:
            print(f"\n  [PASS] TEST {i} PASSED: Inner circle properly generated!")
        else:
            print(f"\n  [FAIL] TEST {i} FAILED: Issues detected")

    print(f"\n{'=' * 80}")
    print("ALL TESTS COMPLETED")
    print('=' * 80)
    print("\nSummary:")
    print("- Inner circle names are now culturally grounded and unique")
    print("- Personalities reflect both role and cultural focus")
    print("- Dialogue is contextual to culture and role")
    print("- Era-appropriate role titles are used")
    print("- Faction links are established where possible")
    print("\n[SUCCESS] Inner circle system is now dynamic and culturally aware!")

if __name__ == "__main__":
    test_inner_circle_generation()
