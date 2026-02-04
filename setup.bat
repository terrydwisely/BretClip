@echo off
echo ========================================
echo BretClip Setup
echo ========================================
echo.

cd /d "%~dp0"

echo [1/5] Creating virtual environment...
python -m venv venv
if errorlevel 1 (
    echo ERROR: Failed to create virtual environment
    pause
    exit /b 1
)

echo [2/5] Activating virtual environment...
call venv\Scripts\activate.bat

echo [3/5] Installing dependencies...
pip install -r requirements.txt
if errorlevel 1 (
    echo ERROR: Failed to install dependencies
    pause
    exit /b 1
)

echo [4/5] Generating icon...
python assets\create_icon.py

echo [5/5] Creating desktop shortcut...
python create_shortcut.py

echo.
echo ========================================
echo Setup complete!
echo ========================================
echo.
echo To start BretClip:
echo   - Double-click the desktop shortcut, OR
echo   - Run: venv\Scripts\pythonw.exe bretclip.py
echo.
echo Press Ctrl+Alt+B anytime to capture!
echo.
pause
