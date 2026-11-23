@echo off
setlocal

set "INSTALL_DIR=%~dp0"
for %%I in ("%INSTALL_DIR%..") do set "SERVER_DIR=%%~fI"
set "VENV_PYTHON=%SERVER_DIR%\.venv\Scripts\python.exe"
set "REQ_FILE=%INSTALL_DIR%requirements.txt"
set "TMP_FILE=%INSTALL_DIR%requirements.txt.tmp"

REM Ensure .venv exists in server\ before exporting packages
if not exist "%VENV_PYTHON%" (
    echo .venv not found. Run '.\installation\setup.bat' first.
    exit /b 1
)

REM Enforce virtual-environment-only pip execution
set "PIP_REQUIRE_VIRTUALENV=true"

REM Export packages installed inside .venv to a temporary file first
"%VENV_PYTHON%" -m pip freeze > "%TMP_FILE%"
if errorlevel 1 (
    if exist "%TMP_FILE%" del /f /q "%TMP_FILE%"
    exit /b 1
)

REM Replace requirements.txt only after pip freeze succeeds
move /y "%TMP_FILE%" "%REQ_FILE%" >nul
if errorlevel 1 (
    if exist "%TMP_FILE%" del /f /q "%TMP_FILE%"
    exit /b 1
)