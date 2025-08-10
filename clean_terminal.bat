@echo off
REM Force clean terminal environment

echo === FORCING CLEAN TERMINAL ENVIRONMENT ===
echo.

REM Clear all Python-related environment variables
set VIRTUAL_ENV=
set PYTHONPATH=
set PYTHON_PATH=
set CONDA_DEFAULT_ENV=
set CONDA_PREFIX=
set CONDA_PROMPT_MODIFIER=
set PIPENV_ACTIVE=

REM Clear VSCode terminal integration
set VSCODE_INJECTION=
set TERM_PROGRAM=

echo Environment variables cleared:
echo   VIRTUAL_ENV: %VIRTUAL_ENV%
echo   PYTHONPATH: %PYTHONPATH%
echo   PYTHON_PATH: %PYTHON_PATH%
echo.

echo To manually activate venv when needed:
echo   cd schedule_manage
echo   venv\Scripts\activate
echo   python manage.py runserver
echo.

echo Starting clean PowerShell session...
echo.

REM Start a clean PowerShell session
powershell -NoProfile -ExecutionPolicy Bypass

pause