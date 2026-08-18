# Instala RTSP Viewer (modo Docker) como tarea de inicio de sesion en Windows.
# Requiere Docker Desktop instalado.
# Uso:  powershell -ExecutionPolicy Bypass -File install-autostart-windows-docker.ps1

$ErrorActionPreference = "Stop"
$DIR = Split-Path -Parent $MyInvocation.MyCommand.Path

if (-not (Get-Command docker -ErrorAction SilentlyContinue)) {
    Write-Host "ERROR: Docker no esta en PATH. Instala Docker Desktop primero." -ForegroundColor Red
    Read-Host "Pulsa Enter para cerrar"
    exit 1
}

$action = New-ScheduledTaskAction `
    -Execute "powershell.exe" `
    -Argument "-NoProfile -WindowStyle Hidden -Command `"Start-Process -FilePath 'docker' -ArgumentList 'desktop','start'; Start-Sleep -Seconds 30; Set-Location '$DIR'; docker compose up -d`""

$trigger = New-ScheduledTaskTrigger -AtLogOn
$settings = New-ScheduledTaskSettingsSet `
    -AllowStartIfOnBatteries `
    -DontStopIfGoingOnBatteries `
    -ExecutionTimeLimit ([TimeSpan]::Zero)

Register-ScheduledTask -TaskName "RTSPViewer" `
    -Action $action -Trigger $trigger -Settings $settings `
    -Description "RTSP Viewer Multicam (Docker) - visor de camaras al iniciar sesion" `
    -Force

Write-Host ""
Write-Host "Tarea RTSPViewer (Docker) creada: se ejecutara al iniciar sesion." -ForegroundColor Green
Write-Host ""
Write-Host "Notas:"
Write-Host "  - Abre Docker Desktop una vez manualmente y acepta el firewall."
Write-Host "  - El contenedor tiene 'restart: unless-stopped' en docker-compose.yml."
Write-Host "  - Visor: http://localhost:8765/   Config: http://localhost:8765/config.html"
Write-Host ""
Write-Host "Para eliminar:"
Write-Host "  powershell -ExecutionPolicy Bypass -File uninstall-autostart-windows.ps1"
Read-Host "Pulsa Enter para cerrar"