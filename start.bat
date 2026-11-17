@echo off
rem Start the Flask dev server, then open the calculator once it is listening.
rem Usage: double-click this file, or run "start.bat" from a terminal.
cd /d "%~dp0"
start "" /min powershell -NoProfile -WindowStyle Hidden -Command "Start-Sleep -Seconds 3; Start-Process 'http://127.0.0.1:5000/'"
python app.py
echo.
echo Server stopped. Press any key to close.
pause >nul
