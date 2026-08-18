# Elimina la tarea de arranque automatico RTSPViewer.
# Uso:  powershell -ExecutionPolicy Bypass -File uninstall-autostart-windows.ps1

$ErrorActionPreference = "Continue"

Unregister-ScheduledTask -TaskName "RTSPViewer" -Confirm:$false

Write-Host "Tarea RTSPViewer eliminada." -ForegroundColor Green
Read-Host "Pulsa Enter para cerrar"