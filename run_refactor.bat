@echo off
echo.
echo =======================================================
echo    JULES AUTONOMOUS REFACTOR BOT LAUNCHER
echo =======================================================
echo.
echo This will start the Gemini CLI in YOLO (auto-approve) mode
echo and pass it your main refactor prompt.
echo.
echo Jules will run in the background via your GitHub integration.
echo.
echo Press Ctrl+C to cancel
echo.
pause
echo Launching...
echo.

:: This is the key:
:: 1. `gemini` - Starts the CLI.
:: 2. `--yolo` - Enables YOLO mode, auto-approving all actions.
:: 3. `-p "jules_refactor_prompt.txt"` - Passes your entire prompt file non-interactively.

gemini --yolo -p "jules_refactor_prompt.txt"

echo.
echo =======================================================
echo Task has been sent to Jules.
echo You can now check its status with 'gemini' and then:
echo /jules what is the status of my last task?
echo =======================================================
echo.
pause