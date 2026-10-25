@echo off
setlocal
cd /d "%~dp0"
if not exist ".venv\Scripts\python.exe" (
  echo Create .venv and install this project first. See README.md.
  exit /b 1
)
".venv\Scripts\python.exe" -m vela %*
