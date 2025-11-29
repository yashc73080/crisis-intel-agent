@echo off
REM Crisis Intel Agent - Decoupled Architecture Launcher
REM This script helps launch the different components

echo.
echo =========================================================
echo   Crisis Intel Agent - Decoupled Architecture
echo =========================================================
echo.
echo Select a component to run:
echo.
echo   1. Coordinator (Interactive Menu)
echo   2. Data Collection Scheduler (Continuous)
echo   3. Event Processor (Continuous)
echo   4. Quick Start Demo (One-time demo)
echo   5. View Firestore Events (Query Tool)
echo   6. Exit
echo.
echo =========================================================

set /p choice="Enter your choice (1-6): "

if "%choice%"=="1" (
    echo.
    echo Starting Coordinator...
    echo.
    cd backend
    python coordinator\main.py
) else if "%choice%"=="2" (
    echo.
    echo Starting Data Collection Scheduler...
    echo Press Ctrl+C to stop
    echo.
    cd backend
    python services\data_collector_scheduler.py
) else if "%choice%"=="3" (
    echo.
    echo Starting Event Processor...
    echo Press Ctrl+C to stop
    echo.
    cd backend
    python services\event_processor.py
) else if "%choice%"=="4" (
    echo.
    echo Running Quick Start Demo...
    echo.
    cd backend
    python quickstart_decoupled.py
) else if "%choice%"=="5" (
    echo.
    echo This feature requires a custom script.
    echo You can query Firestore directly from:
    echo https://console.cloud.google.com/firestore
    echo.
    pause
) else if "%choice%"=="6" (
    echo.
    echo Goodbye!
    exit /b 0
) else (
    echo.
    echo Invalid choice. Please run the script again.
    pause
)

echo.
pause
