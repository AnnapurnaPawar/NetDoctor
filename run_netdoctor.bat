@echo off
title NetDoctor - Real-Time Network Monitoring Dashboard
echo ========================================================
echo Starting NetDoctor Network Monitoring & Lab System...
echo ========================================================
echo.
cd /d "%~dp0"
streamlit run app.py
pause
