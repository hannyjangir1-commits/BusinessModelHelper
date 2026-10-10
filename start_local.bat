@echo off
setlocal
title AI Business Architect v2.0

echo ==========================================================
echo       AI Business Architect v2.0 - Local Launcher
echo ==========================================================
echo.

REM 1. Always switch to project root directory
cd /d "%~dp0"

REM 2. Identify Python Executable
set "PYTHON_CMD="

if exist "%~dp0.venv\Scripts\python.exe" (
    set "PYTHON_CMD=%~dp0.venv\Scripts\python.exe"
    echo [INFO] Virtual environment detected: .venv
    goto python_found
)

where python >nul 2>nul
if not errorlevel 1 (
    set "PYTHON_CMD=python"
    echo [INFO] Using system Python from PATH.
    goto python_found
)

where py >nul 2>nul
if not errorlevel 1 (
    set "PYTHON_CMD=py -3"
    echo [INFO] Using Windows Python Launcher py -3.
    goto python_found
)

echo [ERROR] Python was not found on your system.
echo Please install Python 3.12+ from https://www.python.org/
echo Make sure to check "Add Python to PATH" during installation.
goto error_exit

:python_found

REM 3. Activate Virtual Environment if available
if exist "%~dp0.venv\Scripts\activate.bat" (
    echo [INFO] Activating virtual environment...
    call "%~dp0.venv\Scripts\activate.bat"
)

REM 4. Verify / Setup Environment File (.env)
if exist ".env" goto env_ready

if exist ".env.example" (
    echo [INFO] .env file not found. Creating default configuration from .env.example...
    copy .env.example .env >nul
    echo [INFO] Created .env file.
    echo [IMPORTANT] Please edit .env if you wish to configure a live GEMINI_API_KEY.
    goto env_ready
)

echo [ERROR] Neither .env nor .env.example was found in this directory.
goto error_exit

:env_ready
echo [INFO] Environment configuration .env is present.

REM 5. Apply Additive Database Migrations
echo [INFO] Applying database migrations via Alembic...
"%PYTHON_CMD%" -m alembic -c backend\alembic.ini upgrade head
if errorlevel 1 (
    echo.
    echo [ERROR] Database migration failed.
    echo Please verify your database configuration in .env.
    echo If using SQLite: check that local_dev.db is writable.
    echo If using PostgreSQL: check that the PostgreSQL server is running.
    goto error_exit
)
echo [INFO] Database schema verified and up to date.

REM 6. Verify Compiled Frontend Assets
if exist "frontend\dist\index.html" goto frontend_ready

echo [INFO] Compiled frontend bundle not found. Building React frontend...
pushd "%~dp0frontend"
call npm run build
if errorlevel 1 (
    echo.
    echo [ERROR] Frontend build failed.
    echo Please ensure Node.js and npm are installed and run "npm install" inside the frontend directory.
    popd
    goto error_exit
)
popd

:frontend_ready
echo [INFO] Frontend production assets verified.

echo.
echo ==========================================================
echo  AI Business Architect v2.0 is starting!
echo.
echo  Application URL:   http://localhost:8000
echo  API Documentation: http://localhost:8000/docs
echo  Health Liveness:   http://localhost:8000/health
echo  Database Status:   http://localhost:8000/ready
echo.
echo  Press Ctrl+C to stop the server.
echo ==========================================================
echo.

REM 7. Launch default browser after server warmup (3 seconds)
start /b "" cmd /c "ping -n 4 127.0.0.1 >nul & start "" http://localhost:8000"

REM 8. Start FastAPI Server (Serves API + Built SPA from single origin)
"%PYTHON_CMD%" -m uvicorn app.main:app --app-dir backend --host 127.0.0.1 --port 8000 --reload

echo.
echo [INFO] Server stopped.
pause
exit /b 0

:error_exit
echo.
echo ==========================================================
echo [ERROR] Startup could not be completed.
echo Please review the diagnostic messages above.
echo ==========================================================
echo.
pause
exit /b 1
