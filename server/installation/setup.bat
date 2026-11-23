@echo off
setlocal

set "INSTALL_DIR=%~dp0"
for %%I in ("%INSTALL_DIR%..") do set "SERVER_DIR=%%~fI"
set "VENV_DIR=%SERVER_DIR%\.venv"
set "VENV_PYTHON=%VENV_DIR%\Scripts\python.exe"
set "REQ_FILE=%INSTALL_DIR%requirements.txt"

REM Verify requirements.txt exists in server\installation\
if not exist "%REQ_FILE%" (
    echo requirements.txt not found in %INSTALL_DIR%
    exit /b 1
)

REM Create .venv in server\ if it does not exist
if not exist "%VENV_PYTHON%" (
    if defined VIRTUAL_ENV (
        echo Deactivate the current virtual environment before creating .venv.
        exit /b 1
    )
    if defined CONDA_PREFIX (
        echo Deactivate the current Conda environment before creating .venv.
        exit /b 1
    )

    python -c "import sys; sys.exit(0 if sys.version_info >= (3, 11) else 1)" >nul 2>&1
    if errorlevel 1 (
        echo Python 3.11 or higher is required.
        exit /b 1
    )

    python -m venv "%VENV_DIR%"
    if errorlevel 1 exit /b 1

    set "PIP_REQUIRE_VIRTUALENV=true"
    "%VENV_PYTHON%" -m pip install --upgrade pip
    if errorlevel 1 exit /b 1
)

REM Enforce virtual-environment-only pip execution
set "PIP_REQUIRE_VIRTUALENV=true"

REM Install missing or updated packages strictly inside .venv
"%VENV_PYTHON%" -m pip install -r "%REQ_FILE%"
if errorlevel 1 exit /b 1

REM Uninstall packages inside .venv that are no longer listed in requirements.txt
"%VENV_PYTHON%" -c "import re, subprocess, sys; from importlib import metadata; from pathlib import Path; norm = lambda s: re.sub(r'[-_.]+', '-', s).lower(); get_name = lambda s: (m.group(0) if (m := re.match(r'[A-Za-z0-9._-]+', s.strip())) else ''); lines = [l.split('#', 1)[0].strip() for l in Path(sys.argv[1]).read_text(encoding='utf-8').splitlines()]; roots = {'pip', 'setuptools', 'wheel'} | {norm(get_name(l)) for l in lines if l and not l.startswith('-')} - {''}; dists = {norm(d.metadata['Name']): d for d in metadata.distributions() if d.metadata['Name']}; keep = set(roots); [keep.update({norm(get_name(r)) for p in list(keep) if p in dists and dists[p].requires for r in dists[p].requires} - {''}) for _ in range(len(dists) + 1)]; extra = sorted(set(dists) - keep); subprocess.check_call([sys.executable, '-m', 'pip', 'uninstall', '-y', *extra]) if extra else None" "%REQ_FILE%"
if errorlevel 1 exit /b 1