# Script de Ejecución Masiva - 4am
# Ejecutar flujo completo para ambas empresas

$ErrorActionPreference = "Stop"
$LogFile = "logs/scheduled_massive_$(Get-Date -Format 'yyyyMMdd_HHmmss').log"

try {
    Write-Output "$(Get-Date): Iniciando ejecución masiva programada" | Tee-Object -FilePath $LogFile -Append
    
    # Cambiar al directorio del proyecto
    Set-Location "C:\00_Project_Dev\ExtractorOV_Modular"
    
    # Ejecutar flujo completo automatizado
    python run_complete_flow_automated.py --mode sequential --companies afinia,aire --include-web-download --report-file "logs/massive_report_$(Get-Date -Format 'yyyyMMdd_HHmmss').json"
    
    Write-Output "$(Get-Date): Ejecución masiva completada exitosamente" | Tee-Object -FilePath $LogFile -Append
    
} catch {
    Write-Error "$(Get-Date): Error en ejecución masiva: $($_.Exception.Message)" | Tee-Object -FilePath $LogFile -Append
    exit 1
}
