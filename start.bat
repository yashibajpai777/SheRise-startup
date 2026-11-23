@echo off
title SheRise - Startup Web Platform
echo ============================================================
echo   SheRise - Empowering Women Entrepreneurs Platform
echo ============================================================
echo.

REM Look for Python in standard path or user AppData
set "PY_EXE=python"
where %PY_EXE% >nul 2>nul
if %errorlevel% neq 0 (
    set "PY_EXE=%LOCALAPPDATA%\Programs\Python\Python313\python.exe"
)

if not exist "%PY_EXE%" (
    where py >nul 2>nul
    if %errorlevel% equ 0 (
        set "PY_EXE=py -3"
    )
)

echo Starting SheRise application...
echo Open your browser at: http://127.0.0.1:8000
echo.
"%PY_EXE%" run.py
pause
