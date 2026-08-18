@echo off
cd /d "%~dp0"
where docker >nul 2>nul || (
  echo ERROR: Docker no esta en PATH. Instala Docker Desktop.
  pause
  exit /b 1
)
docker compose up -d --build
echo.
echo Visor:  http://localhost:8765/
echo Config: http://localhost:8765/config.html
pause