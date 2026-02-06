@echo off
REM Quick rebuild script for DataGov services (optimized for speed)
REM CPU-only builds - no NVIDIA/CUDA dependencies

echo ========================================
echo DataGov Quick Build (CPU-Only)
echo ========================================
echo.

REM Stop existing services
echo [1/4] Stopping existing services...
docker-compose down
echo.

REM Remove old images to save space (optional - comment out if you want to keep them)
echo [2/4] Cleaning old images...
docker system prune -f
echo.

REM Build services with no cache (ensures clean build)
echo [3/4] Building services (CPU-only, no CUDA)...
echo This will take 5-8 minutes (much faster than CUDA builds!)
echo.
docker-compose build --no-cache
echo.

REM Start services
echo [4/4] Starting services...
docker-compose up -d
echo.

REM Wait for services to be ready
echo Waiting 20 seconds for services to initialize...
timeout /t 20 /nobreak >nul

REM Show status
echo.
echo ========================================
echo Build Complete! Service Status:
echo ========================================
docker-compose ps
echo.

echo ========================================
echo Next Steps:
echo ========================================
echo 1. Test services: RUN_TESTS.bat
echo 2. View logs: docker-compose logs -f [service-name]
echo 3. Stop services: docker-compose down
echo.
echo Build time saved: ~10-12 minutes (no CUDA downloads!)
echo Image size saved: ~2GB (no NVIDIA drivers!)
echo ========================================

pause
