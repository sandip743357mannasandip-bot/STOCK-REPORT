@echo off
cd /d "%~dp0"
py -m pip install -r requirements-dashboard.txt
if errorlevel 1 pause & exit /b 1
py -m streamlit run dashboard.py
pause
