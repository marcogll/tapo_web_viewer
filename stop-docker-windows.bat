@echo off
cd /d "%~dp0"
where docker >nul 2>nul || (
  echo ERROR: Docker no esta en PATH.
  pause
  exit /b 1
)
docker compose down
taskkill /F /IM ffmpeg.exe >nul 2>nul
echo Contenedor RTSP Viewer detenido.
pause