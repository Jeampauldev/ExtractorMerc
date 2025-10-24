# Script de Verificación Horaria
# Verificar estado S3 y subir archivos pendientes

$ErrorActionPreference = "Stop"
$LogFile = "logs/scheduled_verification_$(Get-Date -Format 'yyyyMMdd_HHmmss').log"

try {
    Write-Output "$(Get-Date): Iniciando verificación horaria" | Tee-Object -FilePath $LogFile -Append
    
    # Cambiar al directorio del proyecto
    Set-Location "C:\00_Project_Dev\ExtractorOV_Modular"
    
    # Ejecutar verificación y subida
    python scripts/implement_missing_steps.py --step 20 --step 21 --companies afinia,aire --limit 50
    
    Write-Output "$(Get-Date): Verificación horaria completada" | Tee-Object -FilePath $LogFile -Append
    
} catch {
    Write-Error "$(Get-Date): Error en verificación horaria: $($_.Exception.Message)" | Tee-Object -FilePath $LogFile -Append
    exit 1
}
