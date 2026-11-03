@echo off
rem drums4all for Windows: double-click this file.
rem The first time it installs what it needs, then it opens the app in the browser.
cd /d "%~dp0"
set PY=
where py >nul 2>nul && set PY=py -3
if not defined PY where python >nul 2>nul && set PY=python
if not defined PY goto nopython
if not exist .venv\Scripts\python.exe (
  echo First run: setting things up ^(this takes a minute^)...
  %PY% -m venv .venv || goto nopython
)
.venv\Scripts\python.exe -m pip install -q --disable-pip-version-check -r requirements.txt || goto failed
.venv\Scripts\python.exe app.py --open
goto :eof
:nopython
echo Python 3 is needed. Install it from https://www.python.org/downloads/
echo and tick "Add python.exe to PATH" during the installation, then run this file again.
pause
goto :eof
:failed
echo Something went wrong while installing. Check your internet connection and try again.
pause
