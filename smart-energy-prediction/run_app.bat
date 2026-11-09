@echo off
title EnerSense - Smart Energy Intelligence Platform
color 0A
echo ==========================================================
echo   EnerSense - Smart Energy Intelligence Platform
echo   Physics (P = V x I) + Machine Learning
echo ==========================================================
echo.

cd /d "%~dp0"

echo Opening browser at http://127.0.0.1:5000 ...
start http://127.0.0.1:5000

echo Starting Flask web application...
if exist ".venv\Scripts\python.exe" (
    ".venv\Scripts\python.exe" app.py
) else (
    python app.py
)

pause
