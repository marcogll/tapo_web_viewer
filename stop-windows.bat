@echo off
taskkill /F /IM ffmpeg.exe >nul 2>nul
for /f "tokens=5" %%a in ('netstat -ano ^| findstr ":8765" ^| findstr "LISTENING"') do taskkill /F /PID %%a >nul 2>nul
echo Procesos RTSP Viewer detenidos.
pause
