@echo off
cd /d "%~dp0"
where python >nul 2>nul || (echo Install Python 3.10+ and tick "Add to PATH" & pause & exit)
python app.py
pause
