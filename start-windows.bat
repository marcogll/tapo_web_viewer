@echo off
cd /d "%~dp0"
where python >nul 2>nul || (
  echo ERROR: falta Python 3.
  pause
  exit /b 1
)
where ffmpeg >nul 2>nul || (
  echo ERROR: falta FFmpeg en PATH.
  pause
  exit /b 1
)
python server.py
pause
