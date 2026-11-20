@echo off
title Hospital Clinical RAG RBAC Server
echo =====================================================================
echo  HOSPITAL RAG ROLE-BASED ACCESS CONTROL - PRODUCTION SERVER
echo  Capstone CSA4706 - Saveetha Institute of Medical and Technical Sciences
echo =====================================================================
echo.

cd /d "%~dp0Capstone"

if exist "..\.venv\Scripts\python.exe" (
    set "PYTHON_EXE=..\.venv\Scripts\python.exe"
) else if exist ".venv\Scripts\python.exe" (
    set "PYTHON_EXE=.venv\Scripts\python.exe"
) else (
    set "PYTHON_EXE=python"
)

echo [INFO] Using Python: %PYTHON_EXE%
echo [INFO] Starting FastAPI server on http://127.0.0.1:8000 ...
echo [INFO] Press Ctrl+C to stop the server.
echo.

"%PYTHON_EXE%" -m uvicorn src.api.app:app --host 127.0.0.1 --port 8000 --reload
pause
