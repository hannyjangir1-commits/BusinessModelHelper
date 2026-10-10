@echo off
title AI Business Architect

echo ==========================================================
echo           AI Business Architect - Local Launcher
echo ==========================================================
echo.

REM Navigate to project root directory
cd /d "%~dp0"

REM 1. Verify / Setup Environment File
if exist ".env" goto env_ok
echo [INFO] .env not found. Creating from .env.example...
copy .env.example .env >nul
echo [INFO] Created .env file.
:env_ok

REM 2. Activate Python Virtual Environment
if not exist ".venv\Scripts\activate.bat" goto no_venv
echo [INFO] Activating virtual environment...
call ".venv\Scripts\activate.bat"
goto venv_ok
:no_venv
echo [WARNING] Virtual environment (.venv) not found. Using system Python.
:venv_ok

REM 3. Run Database Migrations
echo [INFO] Applying database migrations...
python -m alembic upgrade head

REM 4. Verify Built Frontend Dist
if exist "frontend\dist\index.html" goto frontend_ok
echo [INFO] Compiled frontend assets not found. Building frontend...
pushd "%~dp0frontend"
call npm run build
popd
:frontend_ok

echo.
echo ==========================================================
echo  Application is running on: http://localhost:8000
echo  Press Ctrl+C to stop the server
echo ==========================================================
echo.

REM 5. Open browser in background after 2 seconds
start /b "" cmd /c "ping -n 3 127.0.0.1 >nul & start "" http://localhost:8000"

REM 6. Launch FastAPI Backend + Production Frontend (Single Origin)
python -m uvicorn app.main:app --app-dir backend --host 127.0.0.1 --port 8000 --reload

echo.
echo [INFO] Server stopped.
pause
