@echo off
title GridLock AI - Traffic Simulation
echo ========================================================
echo        Starting GridLock AI - Command Center
echo ========================================================
echo.

if exist .venv\Scripts\python.exe (
    .venv\Scripts\python.exe main.py
) else (
    echo Virtual environment not found, trying system Python...
    python main.py
)

pause
