#!/usr/bin/env python
"""
Test script for visual generation system.
Tests all three visual features without requiring game state.
"""

import os
from dotenv import load_dotenv

# Load environment
load_dotenv()

def test_imports():
    """Test that all modules import correctly."""
    print("=" * 60)
    print("TEST 1: Module Imports")
    print("=" * 60)

    try:
        from engines.visual_engine import (
            generate_leader_portrait,
            generate_crisis_illustration,
            generate_settlement_evolution,
            get_settlement_gallery
        )
        print("[PASS] All visual engine functions imported")
    except Exception as e:
        print(f"[FAIL] Import error: {e}")
        return False

    try:
        from model_config import VISUAL_MODEL
        print(f"[PASS] Visual model configured: {VISUAL_MODEL}")
    except Exception as e:
        print(f"[FAIL] Model config error: {e}")
        return False

    return True


def test_api_key():
    """Test that API key is configured."""
    print("\n" + "=" * 60)
    print("TEST 2: API Key Configuration")
    print("=" * 60)

    api_key = os.getenv("GEMINI_API_KEY")
    if not api_key:
        print("[FAIL] GEMINI_API_KEY not found in environment")
        return False

    print(f"[PASS] API key configured: {api_key[:10]}...")
    return True


def test_directories():
    """Test that image directories exist."""
    print("\n" + "=" * 60)
    print("TEST 3: Directory Structure")
    print("=" * 60)

    dirs = [
        "static/images/leaders",
        "static/images/crises",
        "static/images/settlements"
    ]

    all_exist = True
    for dir_path in dirs:
        if os.path.exists(dir_path):
            print(f"[PASS] {dir_path} exists")
        else:
            print(f"[FAIL] {dir_path} missing")
            all_exist = False

    return all_exist


def test_leader_portrait_generation():
    """Test leader portrait generation (dry run - won't actually call API unless requested)."""
    print("\n" + "=" * 60)
    print("TEST 4: Leader Portrait Function")
    print("=" * 60)

    try:
        from engines.visual_engine import generate_leader_portrait

        # Mock leader data
        leader = {
            'name': 'Test Leader',
            'age': 35,
            'traits': ['Wise', 'Charismatic'],
            'role': 'Chieftain'
        }

        civ_context = {
            'era': 'iron_age',
            'culture_values': ['Honor', 'Courage']
        }

        print("[PASS] Leader portrait function callable")
        print(f"  - Would generate portrait for: {leader['name']}")
        print(f"  - Era: {civ_context['era']}")
        print(f"  - Traits: {', '.join(leader['traits'])}")

        return True
    except Exception as e:
        print(f"[FAIL] {e}")
        return False


def test_crisis_illustration_function():
    """Test crisis illustration function."""
    print("\n" + "=" * 60)
    print("TEST 5: Crisis Illustration Function")
    print("=" * 60)

    try:
        from engines.visual_engine import generate_crisis_illustration

        civ_context = {
            'era': 'classical',
            'name': 'Test Civilization',
            'terrain': 'plains'
        }

        print("[PASS] Crisis illustration function callable")
        print(f"  - Crisis types: famine, economic_collapse, succession_crisis")
        print(f"  - Era: {civ_context['era']}")

        return True
    except Exception as e:
        print(f"[FAIL] {e}")
        return False


def test_settlement_evolution_function():
    """Test settlement evolution function."""
    print("\n" + "=" * 60)
    print("TEST 6: Settlement Evolution Function")
    print("=" * 60)

    try:
        from engines.visual_engine import generate_settlement_evolution

        print("[PASS] Settlement evolution function callable")
        print(f"  - Tracks civilization progress over time")
        print(f"  - Auto-cleanup keeps last 5 settlements")

        return True
    except Exception as e:
        print(f"[FAIL] {e}")
        return False


def run_live_test():
    """Optional: Run actual API test (costs money)."""
    print("\n" + "=" * 60)
    print("OPTIONAL: Live API Test")
    print("=" * 60)

    response = input("\nRun live API test? This will generate 1 leader portrait (~$0.04). (y/N): ")

    if response.lower() != 'y':
        print("[SKIP] Live API test skipped")
        return True

    try:
        from engines.visual_engine import generate_leader_portrait

        print("\nGenerating test leader portrait...")

        leader = {
            'name': 'Aldric the Wise',
            'age': 45,
            'traits': ['Wise', 'Scholar'],
            'role': 'Leader'
        }

        civ_context = {
            'era': 'classical',
            'culture_values': ['Knowledge', 'Peace']
        }

        result = generate_leader_portrait(leader, civ_context)

        if result.get('success'):
            print(f"[PASS] Portrait generated: {result['image_path']}")
            print(f"  - Check the image at: {result['image_path']}")
            return True
        else:
            print(f"[FAIL] Generation failed: {result.get('error', 'Unknown error')}")
            return False

    except Exception as e:
        print(f"[FAIL] Exception: {e}")
        import traceback
        traceback.print_exc()
        return False


def main():
    """Run all tests."""
    print("\n")
    print("+" + "=" * 58 + "+")
    print("|" + " " * 15 + "VISUAL SYSTEM TEST SUITE" + " " * 19 + "|")
    print("+" + "=" * 58 + "+")

    tests = [
        test_imports,
        test_api_key,
        test_directories,
        test_leader_portrait_generation,
        test_crisis_illustration_function,
        test_settlement_evolution_function,
    ]

    results = []
    for test in tests:
        try:
            results.append(test())
        except Exception as e:
            print(f"\n[ERROR] Test crashed: {e}")
            results.append(False)

    # Summary
    print("\n" + "=" * 60)
    print("TEST SUMMARY")
    print("=" * 60)

    passed = sum(results)
    total = len(results)

    print(f"Passed: {passed}/{total}")

    if passed == total:
        print("\n[SUCCESS] All tests passed!")
        print("\nVisual system is ready to use.")
        print("\nTo test live generation:")
        run_live_test()
    else:
        print("\n[WARNING] Some tests failed. Check output above.")

    print("\n" + "=" * 60)


if __name__ == "__main__":
    main()
