@echo off
chcp 65001 >nul 2>&1
title Volunteer+ Setup

cd /d "%~dp0"

echo ========================================
echo   Volunteer+ / Setup
echo ========================================
echo.

REM --- Check Python ---
where python >nul 2>&1
if %errorlevel% neq 0 (
    echo [ERROR] Python not found. Install Python 3.11+ and add to PATH.
    pause
    exit /b 1
)
echo [OK] Python found

REM --- Check Node.js ---
where node >nul 2>&1
if %errorlevel% neq 0 (
    echo [WARN] Node.js not found. Frontend build will be skipped.
    set NO_NODE=1
) else (
    echo [OK] Node.js found
    set NO_NODE=0
)

REM --- Create .env if missing ---
if not exist "%~dp0.env" (
    if exist "%~dp0.env.example" (
        echo [INFO] Creating .env from .env.example...
        copy "%~dp0.env.example" "%~dp0.env" >nul
        echo [WARN] Edit .env and set your BOT_TOKEN before running!
    ) else (
        echo [WARN] No .env file found. Create one with BOT_TOKEN=your_token
    )
) else (
    echo [OK] .env exists
)

REM --- Step 1: Python dependencies ---
echo.
echo [1/4] Installing Python dependencies...
pip install -r "%~dp0requirements.txt" --quiet
if %errorlevel% neq 0 (
    echo [ERROR] Failed to install Python dependencies.
    pause
    exit /b 1
)
echo [OK] Python dependencies installed

REM --- Step 2: Frontend build ---
echo.
if "%NO_NODE%"=="1" (
    echo [2/4] Skipping frontend build - Node.js not found
    goto :after_frontend
)
if exist "%~dp0frontend\dist\index.html" (
    echo [2/4] Frontend already built, skipping...
    goto :after_frontend
)
echo [2/4] Building frontend...
cd /d "%~dp0frontend"
call npm install --silent
call npm run build
cd /d "%~dp0"
if not exist "%~dp0frontend\dist\index.html" (
    echo [ERROR] Frontend build failed.
    pause
    exit /b 1
)
echo [OK] Frontend ready

:after_frontend

REM --- Step 3: Create data dir ---
echo.
echo [3/4] Preparing data directory...
if not exist "%~dp0data" mkdir "%~dp0data"
echo [OK] Data directory ready

REM --- Step 4: Launch ---
echo.
echo [4/4] Starting site (FastAPI + dashboard)...
echo ========================================
echo   Open:         http://localhost:8000
echo   API docs:     http://localhost:8000/docs
echo   Stop:         Ctrl+C
echo ========================================
echo.
cd /d "%~dp0"
python "%~dp0bot\main.py"

pause
