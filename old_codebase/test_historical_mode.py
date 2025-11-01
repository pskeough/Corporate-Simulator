"""
Quick test script for historical_earth mode
"""

from world_generator import WorldGenerator
import json

def test_stone_age_generation():
    print("=" * 60)
    print("Testing Stone Age Historical Generation")
    print("=" * 60)

    generator = WorldGenerator()
    config = {
        "world_mode": "historical_earth",
        "starting_era": "stone_age",
        "earth_region": "mediterranean",
        "civilization_name": "The Mediterranean People",
        "population_size": "medium",
        "cultural_focus": "agricultural",
        "religion_type": "animism",
        "social_structure": "tribal_council",
        "difficulty": "balanced",
        "neighbor_count": "few",
        "resource_abundance": "moderate"
    }

    world_data = generator.generate_world(config)

    print("\n--- Civilization Info ---")
    print(f"Name: {world_data['civilization']['meta']['name']}")
    print(f"Year: {world_data['civilization']['meta']['year']}")
    print(f"Era: {world_data['civilization']['meta']['era']}")
    print(f"World Mode: {world_data['civilization']['meta']['world_mode']}")
    print(f"Region: {world_data['civilization']['meta']['earth_region']}")
    print(f"Butterfly Effects Enabled: {world_data['civilization']['meta']['butterfly_effects_enabled']}")
    print(f"Leader: {world_data['civilization']['leader']['name']}")
    print(f"Population: {world_data['civilization']['population']}")

    print("\n--- World Geography ---")
    print(f"Region: {world_data['world']['geography']['region']}")
    print(f"Terrain: {world_data['world']['geography']['terrain']}")
    print(f"Climate: {world_data['world']['geography']['climate']}")
    print(f"Resources: {', '.join(world_data['world']['geography']['resources'][:5])}")

    print("\n--- Factions ---")
    for faction in world_data['factions']['factions']:
        print(f"  - {faction['name']} (Leader: {faction['leader']})")

    print("\n--- Inner Circle ---")
    for member in world_data['inner_circle']['characters']:
        print(f"  - {member['name']} ({member['role']})")

    print("\n" + "=" * 60)
    print("Stone Age test PASSED!")
    print("=" * 60 + "\n")


def test_classical_generation():
    print("=" * 60)
    print("Testing Classical Era Historical Generation")
    print("=" * 60)

    generator = WorldGenerator()
    config = {
        "world_mode": "historical_earth",
        "starting_era": "classical",
        "earth_region": "mediterranean",
        "civilization_name": "Custom Name",  # Should be overridden
        "population_size": "large",
        "cultural_focus": "martial",
        "religion_type": "polytheism",
        "social_structure": "republic",
        "difficulty": "balanced",
        "neighbor_count": "several",
        "resource_abundance": "moderate"
    }

    world_data = generator.generate_world(config)

    print("\n--- Civilization Info ---")
    print(f"Name: {world_data['civilization']['meta']['name']}")
    print(f"Year: {world_data['civilization']['meta']['year']}")
    print(f"Era: {world_data['civilization']['meta']['era']}")
    print(f"World Mode: {world_data['civilization']['meta']['world_mode']}")
    print(f"Region: {world_data['civilization']['meta']['earth_region']}")
    print(f"Historical Factions Enabled: {world_data['civilization']['meta']['historical_factions_enabled']}")
    print(f"Leader: {world_data['civilization']['leader']['name']}")
    print(f"Population: {world_data['civilization']['population']}")

    print("\n--- Historical Factions ---")
    for faction in world_data['factions']['factions']:
        print(f"  - {faction['name']}")
        print(f"    Leader: {faction['leader']}")
        print(f"    Goals: {', '.join(faction['goals'][:2])}")

    print("\n--- Known Peoples (Neighbors) ---")
    for neighbor in world_data['world']['known_peoples']:
        print(f"  - {neighbor['name']} ({neighbor['relationship']})")

    print("\n" + "=" * 60)
    print("Classical Era test PASSED!")
    print("=" * 60 + "\n")


def test_fantasy_mode():
    print("=" * 60)
    print("Testing Fantasy Mode (Backward Compatibility)")
    print("=" * 60)

    generator = WorldGenerator()
    config = {
        "world_mode": "fantasy",
        "starting_era": "bronze_age",
        "terrain": "forest",
        "civilization_name": "The Forest Folk",
        "population_size": "medium",
        "cultural_focus": "spiritual",
        "religion_type": "animism",
        "social_structure": "egalitarian",
        "difficulty": "balanced",
        "neighbor_count": "few",
        "resource_abundance": "moderate"
    }

    world_data = generator.generate_world(config)

    print("\n--- Civilization Info ---")
    print(f"Name: {world_data['civilization']['meta']['name']}")
    print(f"Year: {world_data['civilization']['meta']['year']}")
    print(f"Era: {world_data['civilization']['meta']['era']}")
    print(f"World Mode: {world_data['civilization']['meta']['world_mode']}")
    print(f"Leader: {world_data['civilization']['leader']['name']}")

    print("\n--- World Geography ---")
    print(f"Terrain: {world_data['world']['geography']['terrain']}")
    print(f"Climate: {world_data['world']['geography']['climate']}")

    print("\n--- Factions ---")
    for faction in world_data['factions']['factions']:
        print(f"  - {faction['name']}")

    print("\n" + "=" * 60)
    print("Fantasy Mode test PASSED!")
    print("=" * 60 + "\n")


if __name__ == "__main__":
    try:
        test_stone_age_generation()
        test_classical_generation()
        test_fantasy_mode()

        print("\n" + "=" * 60)
        print("ALL TESTS PASSED! ✓")
        print("=" * 60)
    except Exception as e:
        print(f"\n❌ TEST FAILED: {e}")
        import traceback
        traceback.print_exc()

