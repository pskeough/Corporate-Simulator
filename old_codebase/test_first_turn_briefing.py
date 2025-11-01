"""
Test script for enhanced first turn briefing.
Verifies the new longer, more immersive opening event.
"""

import json
import sys
import io

# Fix encoding issues on Windows
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

from game_state import GameState
from engines.council_engine import generate_first_turn_briefing

def test_first_turn_briefing():
    print("=" * 80)
    print("TESTING ENHANCED FIRST TURN BRIEFING")
    print("=" * 80)

    # Load game state (or create fresh one)
    print("\n1. Loading/Creating Game State")
    print("-" * 80)
    try:
        game_state = GameState()
        # Reset to turn 0 to simulate first turn
        game_state.turn_number = 0
        print(f"✓ Game state loaded successfully")
        print(f"  Civilization: {game_state.civilization.get('meta', {}).get('name', 'Unknown')}")
        print(f"  Leader: {game_state.civilization.get('leader', {}).get('name', 'Unknown')}")
        print(f"  Era: {game_state.civilization.get('meta', {}).get('era', 'Unknown')}")
    except Exception as e:
        print(f"✗ Failed to load game state: {e}")
        return False

    print("\n2. Checking Inner Circle Advisors")
    print("-" * 80)
    if hasattr(game_state, 'inner_circle_manager'):
        advisors = game_state.inner_circle_manager.get_all()
        print(f"✓ Found {len(advisors)} advisors:")
        for advisor in advisors:
            print(f"  - {advisor['name']} ({advisor['role']})")
            traits = advisor.get('personality_traits', [])
            if traits:
                print(f"    Personality: {', '.join(traits[:3])}")
    else:
        print("⚠ No inner circle manager found")

    print("\n3. Generating First Turn Briefing")
    print("-" * 80)
    print("⏳ Calling Gemini API to generate opening event...")
    print("   This may take 10-20 seconds for the enhanced prompt...")

    try:
        briefing_data = generate_first_turn_briefing(game_state)
    except Exception as e:
        print(f"✗ Failed to generate briefing: {e}")
        import traceback
        traceback.print_exc()
        return False

    if not briefing_data:
        print("✗ Briefing generation returned None!")
        return False

    print("✓ Briefing generated successfully!")

    print("\n4. Verifying JSON Structure")
    print("-" * 80)

    # Check required fields
    required_fields = ['title', 'narrative', 'state_of_realm', 'advisor_reports',
                      'pressing_matters', 'investigation_options', 'decision_options']
    missing_fields = []
    for field in required_fields:
        if field in briefing_data:
            print(f"✓ '{field}' present")
        else:
            print(f"✗ '{field}' MISSING!")
            missing_fields.append(field)

    if missing_fields:
        print(f"\n⚠ Missing fields: {', '.join(missing_fields)}")
        print("   Note: 'state_of_realm' is a new field added in Phase 1")

    print("\n5. Analyzing Content Length and Quality")
    print("-" * 80)

    narrative = briefing_data.get('narrative', '')
    state_of_realm = briefing_data.get('state_of_realm', '')
    advisor_reports = briefing_data.get('advisor_reports', [])

    # Count sentences in narrative
    narrative_sentences = narrative.count('.') + narrative.count('!') + narrative.count('?')
    print(f"Narrative length:")
    print(f"  - Characters: {len(narrative)}")
    print(f"  - Sentences (approx): {narrative_sentences}")
    if narrative_sentences >= 12:
        print(f"  ✓ Meets minimum 12 sentence target")
    else:
        print(f"  ⚠ Below target of 12 sentences (got {narrative_sentences})")

    # Count sentences in state_of_realm
    if state_of_realm:
        realm_sentences = state_of_realm.count('.') + state_of_realm.count('!') + state_of_realm.count('?')
        print(f"\nState of Realm length:")
        print(f"  - Characters: {len(state_of_realm)}")
        print(f"  - Sentences (approx): {realm_sentences}")
        if realm_sentences >= 5:
            print(f"  ✓ Meets minimum 5 sentence target")
        else:
            print(f"  ⚠ Below target of 5 sentences (got {realm_sentences})")
    else:
        print(f"\n⚠ State of Realm field is empty or missing")

    # Check advisor reports
    print(f"\nAdvisor Reports:")
    print(f"  - Count: {len(advisor_reports)}")
    if len(advisor_reports) >= 3:
        print(f"  ✓ Has at least 3 advisor reports")
    else:
        print(f"  ⚠ Expected at least 3 reports (got {len(advisor_reports)})")

    for i, report in enumerate(advisor_reports, 1):
        advisor_name = report.get('advisor_title', 'Unknown')
        summary = report.get('summary', '')
        summary_sentences = summary.count('.') + summary.count('!') + summary.count('?')
        print(f"  Report {i} ({advisor_name}):")
        print(f"    - Characters: {len(summary)}")
        print(f"    - Sentences: {summary_sentences}")
        if summary_sentences >= 2:
            print(f"    ✓ Meets 2-3 sentence target")

    print("\n6. Displaying Full Opening Event")
    print("=" * 80)
    print(f"\n📜 {briefing_data.get('title', 'UNTITLED')}\n")
    print("─" * 80)
    print("OPENING NARRATIVE:")
    print("─" * 80)
    print(narrative)

    if state_of_realm:
        print("\n" + "─" * 80)
        print("STATE OF THE REALM:")
        print("─" * 80)
        print(state_of_realm)

    print("\n" + "─" * 80)
    print("ADVISOR REPORTS:")
    print("─" * 80)
    for report in advisor_reports:
        advisor_title = report.get('advisor_title', 'Unknown Advisor')
        summary = report.get('summary', 'No report available')
        print(f"\n{advisor_title}:")
        print(f'"{summary}"')

    print("\n" + "─" * 80)
    print("PRESSING MATTERS:")
    print("─" * 80)
    print(briefing_data.get('pressing_matters', 'No pressing matters listed'))

    print("\n" + "─" * 80)
    print("YOUR OPTIONS:")
    print("─" * 80)

    inv_options = briefing_data.get('investigation_options', [])
    print("\nInvestigation Options:")
    for i, option in enumerate(inv_options, 1):
        print(f"  {i}. {option}")

    dec_options = briefing_data.get('decision_options', [])
    print("\nDecision Options:")
    for i, option in enumerate(dec_options, 1):
        print(f"  {i}. {option}")

    print("\n" + "=" * 80)

    # Verify options
    print("\n7. Verifying Options Arrays")
    print("-" * 80)
    if len(inv_options) == 2:
        print(f"✓ Investigation options: {len(inv_options)} (correct)")
    else:
        print(f"✗ Investigation options: {len(inv_options)} (expected 2)")
        return False

    if len(dec_options) == 2:
        print(f"✓ Decision options: {len(dec_options)} (correct)")
    else:
        print(f"✗ Decision options: {len(dec_options)} (expected 2)")
        return False

    print("\n8. Complete JSON Output")
    print("-" * 80)
    print(json.dumps(briefing_data, indent=2, ensure_ascii=False))

    print("\n" + "=" * 80)
    print("✓ FIRST TURN BRIEFING TEST COMPLETE!")
    print("=" * 80)

    # Summary stats
    total_length = len(narrative) + len(state_of_realm) + sum(len(r.get('summary', '')) for r in advisor_reports)
    print(f"\n📊 CONTENT STATISTICS:")
    print(f"  Total text length: {total_length:,} characters")
    print(f"  Narrative: {len(narrative):,} chars (~{narrative_sentences} sentences)")
    print(f"  State of Realm: {len(state_of_realm):,} chars")
    print(f"  Advisor Reports: {sum(len(r.get('summary', '')) for r in advisor_reports):,} chars")
    print(f"  Quality: {'✓ ENHANCED' if narrative_sentences >= 12 else '⚠ STANDARD'}")

    return True

if __name__ == "__main__":
    try:
        success = test_first_turn_briefing()
        exit(0 if success else 1)
    except Exception as e:
        print(f"\n✗ TEST FAILED WITH ERROR:")
        print(f"  {e}")
        import traceback
        traceback.print_exc()
        exit(1)
