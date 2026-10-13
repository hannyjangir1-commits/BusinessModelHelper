@echo off
setlocal
title AI Business Architect v2.0 - Local Launcher

echo ==========================================================
echo       AI Business Architect v2.0 - Local Launcher
echo ==========================================================
echo.

:: 1. Derive repository root from batch file location and ensure correct CWD
set "REPO_ROOT=%~dp0"
cd /d "%REPO_ROOT%"

:: 2. Identify and select Python runtime
if exist "%REPO_ROOT%.venv\Scripts\python.exe" goto use_venv
where python >nul 2>nul
if not errorlevel 1 goto use_python_path
where py >nul 2>nul
if not errorlevel 1 goto use_py_launcher
goto no_python_found

:use_venv
set "PYTHON_EXE=%REPO_ROOT%.venv\Scripts\python.exe"
set "PYTHON_ARGS="
echo [INFO] Virtual environment detected: .venv
goto python_found

:use_python_path
set "PYTHON_EXE=python"
set "PYTHON_ARGS="
echo [INFO] Using system Python from PATH.
goto python_found

:use_py_launcher
set "PYTHON_EXE=py"
set "PYTHON_ARGS=-3"
echo [INFO] Using Windows Python Launcher (py -3).
goto python_found

:no_python_found
echo.
echo [ERROR] Python was not found on your system.
echo Please install Python 3.12+ from https://www.python.org/
echo Ensure you check "Add Python to PATH" during installation.
goto error_exit

:python_found
:: Activate virtual environment if script exists (sets VIRTUAL_ENV and updates PATH)
if exist "%REPO_ROOT%.venv\Scripts\activate.bat" (
    call "%REPO_ROOT%.venv\Scripts\activate.bat"
)

:: 3. Verify or initialize local environment file (.env)
if exist "%REPO_ROOT%.env" goto env_ready
if exist "%REPO_ROOT%.env.example" goto create_env_from_example

echo.
echo [ERROR] Neither .env nor .env.example was found in "%REPO_ROOT%".
goto error_exit

:create_env_from_example
echo [INFO] .env file not found. Creating default configuration from .env.example...
copy /y "%REPO_ROOT%.env.example" "%REPO_ROOT%.env" >nul
if errorlevel 1 (
    echo [ERROR] Failed to create .env file.
    goto error_exit
)
echo [INFO] Created .env configuration file.
echo [NOTICE] Please edit .env if you wish to configure a live GEMINI_API_KEY.

:env_ready
echo [INFO] Environment configuration .env is present.

:: 4. Run safety and dependency preflight checks
echo [INFO] Running preflight safety and dependency checks...
"%PYTHON_EXE%" %PYTHON_ARGS% "%REPO_ROOT%scripts\local_preflight.py" --check-safety
set "PREFLIGHT_CODE=%ERRORLEVEL%"
if "%PREFLIGHT_CODE%"=="2" goto error_exit
if "%PREFLIGHT_CODE%"=="3" goto install_dependencies
if not "%PREFLIGHT_CODE%"=="0" goto error_exit
goto preflight_safety_ok

:install_dependencies
echo [INFO] Installing missing Python runtime dependencies from backend\requirements.txt...
"%PYTHON_EXE%" %PYTHON_ARGS% -m pip install -r "%REPO_ROOT%backend\requirements.txt"
if errorlevel 1 (
    echo.
    echo [ERROR] Failed to install Python dependencies.
    goto error_exit
)
echo [INFO] Python dependencies installed successfully.

:preflight_safety_ok

:: 5. Port 8000 occupancy check and safe instance reuse
echo [INFO] Checking port 8000 status...
"%PYTHON_EXE%" %PYTHON_ARGS% "%REPO_ROOT%scripts\local_preflight.py" --check-port --host 127.0.0.1 --port 8000
set "PORT_CODE=%ERRORLEVEL%"
if "%PORT_CODE%"=="20" goto instance_already_running
if "%PORT_CODE%"=="21" goto error_exit
if not "%PORT_CODE%"=="0" goto error_exit
goto port_free

:instance_already_running
start "" http://127.0.0.1:8000
echo.
echo ==========================================================
echo [INFO] Reused active local instance at http://127.0.0.1:8000.
echo [INFO] To stop the server, locate its console window and press Ctrl+C.
echo ==========================================================
echo.
pause
exit /b 0

:port_free

:: 6. Check compiled frontend assets (build only if absent or stale)
echo [INFO] Verifying frontend production assets...
"%PYTHON_EXE%" %PYTHON_ARGS% "%REPO_ROOT%scripts\local_preflight.py" --check-frontend
set "FRONTEND_CODE=%ERRORLEVEL%"
if "%FRONTEND_CODE%"=="10" goto build_frontend
if not "%FRONTEND_CODE%"=="0" goto error_exit
goto frontend_ready

:build_frontend
echo [INFO] Frontend assets absent or stale. Building React frontend bundle...
where npm >nul 2>nul
if errorlevel 1 (
    echo.
    echo [ERROR] Node.js and npm are required to build frontend assets but were not found on PATH.
    echo Please install Node.js 20+ or 22 LTS from https://nodejs.org/
    goto error_exit
)

if exist "%REPO_ROOT%frontend\node_modules" goto run_npm_build
echo [INFO] Installing frontend dependencies (npm install)...
pushd "%REPO_ROOT%frontend"
call npm install
if errorlevel 1 (
    echo.
    echo [ERROR] Failed to install frontend npm packages.
    popd
    goto error_exit
)
popd

:run_npm_build
pushd "%REPO_ROOT%frontend"
call npm run build
if errorlevel 1 (
    echo.
    echo [ERROR] Frontend build failed.
    popd
    goto error_exit
)
popd
echo [INFO] Frontend build completed successfully.

:frontend_ready

:: 7. Apply database schema migrations via Alembic
echo [INFO] Applying additive database schema migrations via Alembic...
"%PYTHON_EXE%" %PYTHON_ARGS% -m alembic -c "%REPO_ROOT%backend\alembic.ini" upgrade head
if errorlevel 1 (
    echo.
    echo [ERROR] Database migration failed.
    echo Please verify database configuration in .env.
    echo If using SQLite: Ensure local_dev.db is writable.
    echo If using PostgreSQL: Ensure the local PostgreSQL service is running.
    goto error_exit
)
echo [INFO] Database schema verified and up to date.

echo.
echo ==========================================================
echo  AI Business Architect v2.0 is starting!
echo.
echo  Local Web App:       http://127.0.0.1:8000
echo  API Documentation:   http://127.0.0.1:8000/docs
echo  Liveness Check:      http://127.0.0.1:8000/health
echo  Database Readiness:  http://127.0.0.1:8000/ready
echo.
echo  Waiting for readiness probe before opening browser...
echo  Press Ctrl+C to stop the server at any time.
echo ==========================================================
echo.

:: 8. Launch background bounded readiness polling helper
start /b "" powershell.exe -NoProfile -ExecutionPolicy Bypass -File "%REPO_ROOT%scripts\wait_and_open_browser.ps1" -HealthUrl "http://127.0.0.1:8000/ready" -BrowserUrl "http://127.0.0.1:8000" -TimeoutSeconds 30

:: 9. Start FastAPI Server in foreground (Serves API + Built SPA from single origin)
"%PYTHON_EXE%" %PYTHON_ARGS% -m uvicorn app.main:app --app-dir "%REPO_ROOT%backend" --host 127.0.0.1 --port 8000 --reload
set "SERVER_EXIT=%ERRORLEVEL%"

if not "%SERVER_EXIT%"=="0" (
    echo.
    echo [ERROR] Server exited unexpectedly with code %SERVER_EXIT%.
    goto error_exit
)

echo.
echo [INFO] Server stopped gracefully.
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
