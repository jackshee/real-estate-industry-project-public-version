@echo off
REM MAST30034 Project 2 - Virtual Environment Setup Script for Windows
REM This script sets up a Python virtual environment for the project

echo 🏠 MAST30034 Project 2 - Virtual Environment Setup
echo ==================================================
echo.

REM Check if Python is installed
python --version >nul 2>&1
if errorlevel 1 (
    echo ❌ Error: Python is not installed or not in PATH
    echo Please install Python 3 from https://python.org
    echo Make sure to check "Add Python to PATH" during installation
    pause
    exit /b 1
)

REM Get Python version
for /f "tokens=2" %%i in ('python --version 2^>^&1') do set PYTHON_VERSION=%%i
echo ✅ Found Python %PYTHON_VERSION%

REM Check if we're in the project directory
if not exist "requirements.txt" (
    echo ❌ Error: requirements.txt not found
    echo Please run this script from the project root directory
    pause
    exit /b 1
)

echo ✅ Found requirements.txt

REM Remove existing virtual environment if it exists
if exist "venv" (
    echo 🔄 Removing existing virtual environment...
    rmdir /s /q venv
)

REM Create new virtual environment
echo 📦 Creating virtual environment...
python -m venv venv

REM Activate virtual environment
echo 🔧 Activating virtual environment...
call venv\Scripts\activate.bat

REM Upgrade pip
echo ⬆️  Upgrading pip...
python -m pip install --upgrade pip

REM Install requirements
echo 📚 Installing project dependencies...
pip install -r requirements.txt

echo.
echo 🎉 Setup completed successfully!
echo.
echo 📋 Next steps:
echo 1. Activate the virtual environment:
echo    venv\Scripts\activate
echo.
echo 2. Start Jupyter Lab:
echo    jupyter lab
echo.
echo 3. Or run notebooks directly:
echo    jupyter notebook
echo.
echo 4. When you're done, deactivate the environment:
echo    deactivate
echo.
echo 💡 Tip: You can also run 'venv\Scripts\activate' in any Command Prompt
echo    or PowerShell session to activate the environment for that session.
echo.
pause
