@echo off
setlocal

cd /d "%~dp0"

set "VENV_PY="
if exist "venv\Scripts\python.exe" set "VENV_PY=venv\Scripts\python.exe"
if not defined VENV_PY if exist ".venv\Scripts\python.exe" set "VENV_PY=.venv\Scripts\python.exe"

if not defined VENV_PY (
  echo [ERROR] Python venv not found.
  echo Expected one of:
  echo   venv\Scripts\python.exe
  echo   .venv\Scripts\python.exe
  pause
  exit /b 1
)

if not exist ".deps_ready" (
  "%VENV_PY%" -m pip install -r requirements.txt
  if errorlevel 1 (
    echo [ERROR] Failed to install dependencies.
    pause
    exit /b 1
  )
  > ".deps_ready" echo ready
)

"%VENV_PY%" manage.py migrate
if errorlevel 1 (
  echo [ERROR] Failed to apply migrations.
  pause
  exit /b 1
)

start "" powershell -NoProfile -WindowStyle Hidden -Command "Start-Sleep -Seconds 3; Start-Process 'http://127.0.0.1:8000/'"
"%VENV_PY%" manage.py runserver 127.0.0.1:8000
