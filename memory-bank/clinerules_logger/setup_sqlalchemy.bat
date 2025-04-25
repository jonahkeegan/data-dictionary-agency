@echo off
REM Setup script for clinerules_logger SQLAlchemy integration on Windows
ECHO Setting up SQLAlchemy integration for clinerules_logger...

REM Check if Python is installed
python --version >nul 2>&1
IF %ERRORLEVEL% NEQ 0 (
    ECHO Error: Python is not installed or not in PATH.
    ECHO Please install Python 3.7 or later and try again.
    EXIT /B 1
)

REM Run the Python setup script
python setup_sqlalchemy.py
IF %ERRORLEVEL% NEQ 0 (
    ECHO Setup failed. Please check the error messages above.
    EXIT /B 1
)

ECHO.
ECHO Setup completed successfully!
ECHO.
ECHO To use the enhanced clinerules logger, you need to:
ECHO 1. Activate the virtual environment: .\venv\Scripts\activate
ECHO 2. Run the logger: python main.py
ECHO.
ECHO Press any key to exit...
PAUSE >nul
