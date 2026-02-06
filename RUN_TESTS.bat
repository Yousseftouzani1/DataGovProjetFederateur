@echo off
REM Quick test runner for Windows
echo ========================================
echo DataGov Testing Suite
echo ========================================

REM Check if Docker services are running
echo.
echo Checking if Docker services are running...
docker-compose ps | findstr "Up" >nul
if %errorlevel% neq 0 (
    echo ERROR: Docker services are not running!
    echo Please start services first with: docker-compose up -d
    pause
    exit /b 1
)

echo Services are running!
echo.

REM Install test dependencies if needed
echo Installing test dependencies...
pip install pytest pytest-asyncio pytest-cov requests pytest-html >nul 2>&1

REM Wait for services to be ready
echo Waiting for services to be ready...
timeout /t 10 /nobreak >nul

REM Run tests
echo.
echo ========================================
echo Running Tests...
echo ========================================
python run_tests.py

echo.
echo ========================================
echo Test Results
echo ========================================
echo Check tests/results/ folder for detailed HTML reports
echo.

pause
