@echo off
REM Setup script for the Enhanced .clinerules Logger System on Windows

echo Setting up the Enhanced .clinerules Logger System...
echo.

REM Get the project root directory
set SCRIPT_DIR=%~dp0
set PROJECT_ROOT=%SCRIPT_DIR%..\..

echo Project root directory: %PROJECT_ROOT%
echo.

REM Make sure we're in the project root for proper module imports
cd "%PROJECT_ROOT%"

echo Installing dependencies...
REM Run the installation script as a module
python -m memory_bank.clinerules_logger.install

echo.
echo To test the system, run:
echo python -m memory_bank.clinerules_logger.examples
echo.
echo To use the enhanced logger:
echo python -m memory_bank.clinerules_logger.main [command]
echo.
echo Or use the backward-compatible interface:
echo python memory-bank\clinerules_logger.py
