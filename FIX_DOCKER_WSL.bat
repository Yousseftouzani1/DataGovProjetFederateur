@echo off
REM Fix Docker WSL2 Integration Issue
echo ========================================
echo Docker WSL2 Fix Script
echo ========================================
echo.

echo Step 1: Stopping Docker Desktop...
wsl --shutdown
timeout /t 5 /nobreak >nul

echo Step 2: Restarting WSL...
wsl --list --verbose

echo.
echo Step 3: Manual steps required:
echo 1. Open Docker Desktop
echo 2. Go to Settings → Resources → WSL Integration
echo 3. Make sure "Enable integration with my default WSL distro" is ON
echo 4. Click "Apply & Restart"
echo.

echo Step 4: After Docker Desktop restarts, try:
echo docker-compose up -d
echo.

pause
