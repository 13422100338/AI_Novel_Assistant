@echo off
setlocal
cd /d "%~dp0"

set "LOG=%~dp0launcher.log"
echo ==== AI Novel Assistant Launcher ==== > "%LOG%"
echo Workdir: %cd% >> "%LOG%"

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
  echo Python was not found. Please install Python 3.10+ first. >> "%LOG%"
  echo Python was not found. Please install Python 3.10+ first.
  pause
  exit /b 1
)

echo Using: %PYTHON_EXE% >> "%LOG%"
%PYTHON_EXE% main.py >> "%LOG%" 2>&1

if errorlevel 1 (
  echo.
  echo Startup failed. Log:
  echo %LOG%
  echo.
  type "%LOG%"
  pause
  exit /b 1
)

endlocal
