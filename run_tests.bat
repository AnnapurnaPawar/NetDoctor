@echo off
title NetDoctor - Automated Pytest Unit Tests
echo ========================================================
echo Running NetDoctor Automated Unit Tests...
echo ========================================================
echo.
cd /d "%~dp0"
pytest -v
echo.
pause
