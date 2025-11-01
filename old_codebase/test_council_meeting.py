"""
Test script for dynamic council meeting implementation.
Verifies the new central dilemma structure and advisor stances.
"""

import json
import sys
import io

# Fix encoding issues on Windows
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

from game_state import GameState
from engines.council_engine import generate_council_meeting

def test_council_meeting():
    print("=" * 60)
    print("TESTING DYNAMIC COUNCIL MEETING IMPLEMENTATION")
    print("=" * 60)

    # Load game state
    game_state = GameState()

    print("\n1. Testing Inner Circle Manager")
    print("-" * 60)
    if hasattr(game_state, 'inner_circle_manager'):
        advisors = game_state.inner_circle_manager.get_all()
        print(f"✓ Found {len(advisors)} advisors:")
        for advisor in advisors:
            print(f"  - {advisor['name']} ({advisor['role']})")
            print(f"    Personality: {', '.join(advisor.get('personality_traits', []))}")
            print(f"    Loyalty: {advisor.get('metrics', {}).get('loyalty', 50)}")
            print(f"    Relationship: {advisor.get('metrics', {}).get('relationship', 50)}")
    else:
        print("✗ No inner circle manager found!")
        return False

    print("\n2. Generating Council Meeting")
    print("-" * 60)

    council_data = generate_council_meeting(game_state)

    if not council_data:
        print("✗ Failed to generate council meeting!")
        return False

    print("✓ Council meeting generated successfully!")

    print("\n3. Verifying JSON Structure")
    print("-" * 60)

    # Check required fields
    required_fields = ['event_type', 'title', 'narrative', 'central_dilemma', 'advisor_stances']
    for field in required_fields:
        if field in council_data:
            print(f"✓ '{field}' present")
        else:
            print(f"✗ '{field}' MISSING!")
            return False

    print("\n4. Council Meeting Details")
    print("-" * 60)
    print(f"Event Type: {council_data.get('event_type')}")
    print(f"Title: {council_data.get('title')}")
    print(f"\nNarrative:\n{council_data.get('narrative')}")
    print(f"\nCentral Dilemma:\n{council_data.get('central_dilemma')}")

    print("\n5. Advisor Stances")
    print("-" * 60)
    advisor_stances = council_data.get('advisor_stances', [])
    if len(advisor_stances) >= 2:
        print(f"✓ Found {len(advisor_stances)} advisor stances (minimum 2)")
        for i, stance in enumerate(advisor_stances, 1):
            print(f"\nAdvisor {i}:")
            print(f"  Name: {stance.get('name')}")
            print(f"  Role: {stance.get('role')}")
            print(f"  Position: {stance.get('position')}")
            print(f"  Reasoning: {stance.get('reasoning')}")
    else:
        print(f"✗ Only {len(advisor_stances)} advisor stances (need at least 2)")
        return False

    print("\n6. Investigation Options")
    print("-" * 60)
    inv_options = council_data.get('investigation_options', [])
    if len(inv_options) == 2:
        print(f"✓ Found {len(inv_options)} investigation options")
        for i, option in enumerate(inv_options, 1):
            print(f"  {i}. {option}")
    else:
        print(f"✗ Found {len(inv_options)} investigation options (need exactly 2)")
        return False

    print("\n7. Decision Options")
    print("-" * 60)
    dec_options = council_data.get('decision_options', [])
    if len(dec_options) == 2:
        print(f"✓ Found {len(dec_options)} decision options")
        for i, option in enumerate(dec_options, 1):
            print(f"  {i}. {option}")
    else:
        print(f"✗ Found {len(dec_options)} decision options (need exactly 2)")
        return False

    print("\n8. Complete JSON Output")
    print("-" * 60)
    print(json.dumps(council_data, indent=2))

    print("\n" + "=" * 60)
    print("✓ ALL TESTS PASSED!")
    print("=" * 60)
    return True

if __name__ == "__main__":
    try:
        success = test_council_meeting()
        exit(0 if success else 1)
    except Exception as e:
        print(f"\n✗ TEST FAILED WITH ERROR:")
        print(f"  {e}")
        import traceback
        traceback.print_exc()
        exit(1)
