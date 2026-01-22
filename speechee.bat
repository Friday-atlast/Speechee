@echo off
REM Speechee CLI Launcher for Windows
REM Usage: speechee.bat listen -d 5

setlocal

REM Get the directory where this script is located
set "SCRIPT_DIR=%~dp0"

REM Activate virtual environment and run CLI
call "%SCRIPT_DIR%venv\Scripts\activate.bat"
python "%SCRIPT_DIR%cli\speechee.py" %*

endlocal