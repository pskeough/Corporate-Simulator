@echo off
echo ============================================================
echo PHASE 3 COMPREHENSIVE TEST SUITE
echo ============================================================
echo.

echo [1/3] Running BonusEngine Unit Tests...
echo ============================================================
python test_bonus_engine.py
if %errorlevel% neq 0 (
    echo FAILED: BonusEngine tests failed!
    exit /b 1
)
echo.

echo [2/3] Running World Turns Integration Tests...
echo ============================================================
python test_world_turns_integration.py
if %errorlevel% neq 0 (
    echo FAILED: Integration tests failed!
    exit /b 1
)
echo.

echo [3/3] Running Full System Regression Tests...
echo ============================================================
python test_systems.py
if %errorlevel% neq 0 (
    echo FAILED: Regression tests failed!
    exit /b 1
)
echo.

echo ============================================================
echo ALL PHASE 3 TESTS PASSED SUCCESSFULLY!
echo ============================================================
echo.
echo Phase 3: Bonus Aggregation System is COMPLETE and VERIFIED
echo.
echo Next steps:
echo   1. Review PHASE_3_COMPLETE.md for summary
echo   2. Check docs/bonus_system.md for documentation
echo   3. See examples/add_building_bonus.md for usage
echo.
echo Ready for Phase 4: Building and Technology Systems!
echo ============================================================
