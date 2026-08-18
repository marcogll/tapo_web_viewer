# Instala RTSP Viewer (modo Python directo) como tarea de inicio de sesion en Windows.
# Requiere Python 3 y FFmpeg instalados y en PATH.
# Uso:  powershell -ExecutionPolicy Bypass -File install-autostart-windows-nodocker.ps1

$ErrorActionPreference = "Stop"
$DIR = Split-Path -Parent $MyInvocation.MyCommand.Path

if (-not (Get-Command python -ErrorAction SilentlyContinue)) {
    Write-Host "ERROR: Python no esta en PATH. Instala Python 3 primero." -ForegroundColor Red
    Read-Host "Pulsa Enter para cerrar"
    exit 1
}
if (-not (Get-Command ffmpeg -ErrorAction SilentlyContinue)) {
    Write-Host "ERROR: FFmpeg no esta en PATH. Instala FFmpeg primero." -ForegroundColor Red
    Read-Host "Pulsa Enter para cerrar"
    exit 1
}

$action = New-ScheduledTaskAction `
    -Execute "cmd.exe" `
    -Argument "/c `"$DIR\start-windows.bat`"" `
    -WorkingDirectory $DIR

$trigger = New-ScheduledTaskTrigger -AtLogOn
$settings = New-ScheduledTaskSettingsSet `
    -AllowStartIfOnBatteries `
    -DontStopIfGoingOnBatteries `
    -ExecutionTimeLimit ([TimeSpan]::Zero)

Register-ScheduledTask -TaskName "RTSPViewer" `
    -Action $action -Trigger $trigger -Settings $settings `
    -Description "RTSP Viewer Multicam (Python) - visor de camaras al iniciar sesion" `
    -Force

Write-Host ""
Write-Host "Tarea RTSPViewer (Python) creada: se ejecutara al iniciar sesion." -ForegroundColor Green
Write-Host ""
Write-Host "Notas:"
Write-Host "  - El servidor abre una ventana con los logs del visor."
Write-Host "  - Visor: http://localhost:8765/   Config: http://localhost:8765/config.html"
Write-Host ""
Write-Host "Para eliminar:"
Write-Host "  powershell -ExecutionPolicy Bypass -File uninstall-autostart-windows.ps1"
Read-Host "Pulsa Enter para cerrar"