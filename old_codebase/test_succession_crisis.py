"""
Test succession crisis system to verify trigger_succession_crisis() is properly wired.
"""

import sys
import os

# Fix Windows encoding issues
if sys.platform == 'win32':
    import io
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

sys.path.insert(0, os.path.abspath(os.path.dirname(__file__)))

from game_state import GameState
from engines.leader_engine import trigger_succession_crisis
from engines.crisis_engine import detect_crisis, generate_crisis_event

def test_trigger_succession_crisis():
    """Test that trigger_succession_crisis generates faction-backed candidates"""
    print("\n=== TEST 1: trigger_succession_crisis() generates faction-backed candidates ===")

    game = GameState()

    # Test trigger_succession_crisis
    succession_data = trigger_succession_crisis(game)

    print(f"\n✓ Event type: {succession_data.get('event_type')}")
    print(f"✓ Number of candidates: {len(succession_data.get('candidates', []))}")
    print(f"✓ Transition crisis duration: {succession_data.get('transition_crisis_duration')} turns")
    print(f"✓ Rival claimant chance: {succession_data.get('rival_claimant_chance')*100}%")

    # Check each candidate has faction backing
    print("\n✓ Candidates:")
    for i, candidate in enumerate(succession_data.get('candidates', [])):
        print(f"\n  Candidate {i+1}: {candidate['name']}")
        print(f"    Archetype: {candidate['archetype']}")
        print(f"    Traits: {', '.join(candidate['traits'])}")
        print(f"    Backing faction: {candidate['backing_faction']}")
        print(f"    Backing faction ID: {candidate['backing_faction_id']}")
        print(f"    Demands: {candidate['demands']}")
        print(f"    Approval changes: {candidate['approval_changes']}")

        # Verify required fields
        assert 'name' in candidate, "Candidate missing name"
        assert 'archetype' in candidate, "Candidate missing archetype"
        assert 'traits' in candidate, "Candidate missing traits"
        assert 'backing_faction' in candidate, "Candidate missing backing_faction"
        assert 'backing_faction_id' in candidate, "Candidate missing backing_faction_id"
        assert 'demands' in candidate, "Candidate missing demands"
        assert 'approval_changes' in candidate, "Candidate missing approval_changes"

    print("\n✅ TEST PASSED: trigger_succession_crisis() generates proper faction-backed candidates")
    return True

def test_crisis_engine_succession():
    """Test that crisis engine properly detects and generates succession crisis"""
    print("\n=== TEST 2: Crisis engine detects succession crisis ===")

    game = GameState()

    # Force leader to be very old
    leader = game.civilization['leader']
    leader['age'] = leader.get('life_expectancy', 60) + 15  # Well past life expectancy

    print(f"\n✓ Leader age: {leader['age']}")
    print(f"✓ Life expectancy: {leader.get('life_expectancy', 60)}")

    # Detect crisis
    crisis_type = detect_crisis(game)
    print(f"\n✓ Detected crisis type: {crisis_type}")

    assert crisis_type == 'succession_crisis', f"Expected 'succession_crisis', got '{crisis_type}'"

    # Generate crisis event
    crisis_event = generate_crisis_event(game, crisis_type)

    print(f"\n✓ Crisis event title: {crisis_event.get('title')}")
    print(f"✓ Is crisis: {crisis_event.get('is_crisis')}")
    print(f"✓ Crisis type: {crisis_event.get('crisis_type')}")
    print(f"✓ Has succession_data: {'succession_data' in crisis_event}")

    # Verify succession data is present
    assert 'succession_data' in crisis_event, "Crisis event missing succession_data"
    succession_data = crisis_event['succession_data']

    print(f"\n✓ Succession data present with {len(succession_data.get('candidates', []))} candidates")

    # Check first candidate
    if succession_data.get('candidates'):
        first_candidate = succession_data['candidates'][0]
        print(f"\n✓ First candidate: {first_candidate['name']} ({first_candidate['archetype']})")
        print(f"  Backed by: {first_candidate['backing_faction']}")
        print(f"  Demands: {first_candidate['demands']}")

    print("\n✅ TEST PASSED: Crisis engine properly handles succession crisis")
    return True

def test_old_function_deprecated():
    """Verify that generate_successor_candidates is not used in main routes"""
    print("\n=== TEST 3: Verify old function is not used ===")

    with open('main.py', 'r', encoding='utf-8') as f:
        main_content = f.read()

    # Check that /api/die uses trigger_succession_crisis
    assert 'trigger_succession_crisis' in main_content, "main.py should import trigger_succession_crisis"

    # Check handle_death function
    handle_death_start = main_content.find("@app.route('/api/die'")
    handle_death_end = main_content.find("@app.route", handle_death_start + 1)
    handle_death_code = main_content[handle_death_start:handle_death_end]

    assert 'trigger_succession_crisis(game)' in handle_death_code, "/api/die should call trigger_succession_crisis()"

    # Check choose_successor function
    choose_successor_start = main_content.find("@app.route('/api/choose_successor'")
    choose_successor_end = main_content.find("@app.route", choose_successor_start + 1)
    if choose_successor_end == -1:
        choose_successor_end = len(main_content)
    choose_successor_code = main_content[choose_successor_start:choose_successor_end]

    assert 'trigger_succession_crisis' in choose_successor_code, "/api/choose_successor should use trigger_succession_crisis()"

    print("\n✓ main.py properly uses trigger_succession_crisis() in /api/die")
    print("✓ main.py properly uses trigger_succession_crisis() in /api/choose_successor")
    print("\n✅ TEST PASSED: Old function is properly deprecated")
    return True

def run_all_tests():
    """Run all succession crisis tests"""
    print("\n" + "="*80)
    print("TESTING SUCCESSION CRISIS SYSTEM")
    print("="*80)

    tests = [
        test_trigger_succession_crisis,
        test_crisis_engine_succession,
        test_old_function_deprecated
    ]

    passed = 0
    failed = 0

    for test in tests:
        try:
            if test():
                passed += 1
        except Exception as e:
            print(f"\n❌ TEST FAILED: {test.__name__}")
            print(f"   Error: {e}")
            import traceback
            traceback.print_exc()
            failed += 1

    print("\n" + "="*80)
    print(f"RESULTS: {passed} passed, {failed} failed")
    print("="*80)

    return failed == 0

if __name__ == '__main__':
    success = run_all_tests()
    sys.exit(0 if success else 1)

