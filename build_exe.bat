@echo off
setlocal
cd /d "%~dp0"

set "PYTHON_EXE="

if exist "%LocalAppData%\Programs\Python\Python312\python.exe" set "PYTHON_EXE=%LocalAppData%\Programs\Python\Python312\python.exe"

if not defined PYTHON_EXE (
  where python >nul 2>nul
  if not errorlevel 1 set "PYTHON_EXE=python"
)

if not defined PYTHON_EXE (
  where py >nul 2>nul
  if not errorlevel 1 set "PYTHON_EXE=py -3"
)

if not defined PYTHON_EXE (
  echo Python was not found. Please install Python 3.10+ first.
  pause
  exit /b 1
)

%PYTHON_EXE% -m PyInstaller --noconfirm --windowed --name "AI_Novel_Assistant" main.py
if errorlevel 1 (
  echo.
  echo Build failed. Please install PyInstaller first:
  echo %PYTHON_EXE% -m pip install pyinstaller
  pause
  exit /b 1
)

echo.
echo Build complete:
echo dist\AI_Novel_Assistant\AI_Novel_Assistant.exe
pause
endlocal
