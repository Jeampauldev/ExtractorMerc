# Script simplificado para consolidar logs existentes
Write-Host "=== CONSOLIDACION DE LOGS EXISTENTES ===" -ForegroundColor Green

$logsDir = "logs\current"
$archiveDir = "logs\archived"

Write-Host "`nAnalizando logs actuales..." -ForegroundColor Yellow

# Obtener todos los logs actuales
$currentLogs = Get-ChildItem -Path $logsDir -File | Sort-Object Name

Write-Host "`nLogs encontrados:" -ForegroundColor Cyan
foreach ($log in $currentLogs) {
    $sizeKB = [math]::Round($log.Length / 1024, 2)
    Write-Host "  $($log.Name) - ${sizeKB}KB" -ForegroundColor White
}

Write-Host "`nPlan de consolidacion:" -ForegroundColor Yellow

# Archivos de Afinia para consolidar
$afiniaFiles = @(
    "afinia_ov_visual.log",
    "afinia_ov_visual2.log", 
    "oficina_virtual_afinia.log"
)

Write-Host "`n1. LOGS DE AFINIA -> afinia_history.log" -ForegroundColor Cyan
foreach ($file in $afiniaFiles) {
    if (Test-Path "$logsDir\$file") {
        $size = (Get-Item "$logsDir\$file").Length
        Write-Host "   + $file" -ForegroundColor White
    }
}

# Archivos de sesiones interactivas
$interactiveFiles = Get-ChildItem -Path $logsDir -File | Where-Object {$_.Name -like "extractor_interactive_*"} | Select-Object -ExpandProperty Name

Write-Host "`n2. SESIONES INTERACTIVAS -> interactive_history.log" -ForegroundColor Cyan
foreach ($file in $interactiveFiles) {
    Write-Host "   + $file" -ForegroundColor White
}

# Archivo de Aire
Write-Host "`n3. LOGS DE AIRE -> aire_history.log" -ForegroundColor Cyan
if (Test-Path "$logsDir\oficina_virtual_aire.log") {
    Write-Host "   + oficina_virtual_aire.log" -ForegroundColor White
}

# S3 Uploader
Write-Host "`n4. S3 UPLOADER -> s3_history.log" -ForegroundColor Cyan
if (Test-Path "$logsDir\s3_uploader.log") {
    Write-Host "   + s3_uploader.log" -ForegroundColor White
}

Write-Host "`n5. MANTENER:" -ForegroundColor Green
Write-Host "   - afinia_ov.log (nuevo sistema)" -ForegroundColor White
Write-Host "   - aire_ov.log (nuevo sistema)" -ForegroundColor White

Write-Host "`n¿Proceder? (Y/N): " -ForegroundColor Yellow -NoNewline
$response = Read-Host

if ($response -eq "Y" -or $response -eq "y") {
    Write-Host "`nEjecutando consolidacion..." -ForegroundColor Green
    
    $consolidated = 0
    
    # 1. Consolidar logs de Afinia
    $afiniaTarget = "$logsDir\afinia_history.log"
    $header = "# AFINIA LOGS CONSOLIDADOS - $(Get-Date)`n# ========================================`n`n"
    $header | Out-File -FilePath $afiniaTarget -Encoding UTF8
    
    foreach ($file in $afiniaFiles) {
        $filePath = "$logsDir\$file"
        if (Test-Path $filePath) {
            "`n# === $file ===" | Add-Content -Path $afiniaTarget -Encoding UTF8
            if ((Get-Item $filePath).Length -gt 0) {
                Get-Content -Path $filePath -Encoding UTF8 | Add-Content -Path $afiniaTarget -Encoding UTF8
            } else {
                "# [ARCHIVO VACIO]" | Add-Content -Path $afiniaTarget -Encoding UTF8
            }
            
            # Mover original a archived
            $timestamp = Get-Date -Format "yyyyMMdd_HHmmss"
            $archivedName = "$([System.IO.Path]::GetFileNameWithoutExtension($file))_$timestamp.log"
            Move-Item -Path $filePath -Destination "$archiveDir\$archivedName" -Force
            Write-Host "[EMOJI_REMOVIDO] $file -> $archivedName" -ForegroundColor Green
            $consolidated++
        }
    }
    
    # 2. Consolidar logs interactivos
    $interactiveTarget = "$logsDir\interactive_history.log"
    $header = "# SESIONES INTERACTIVAS CONSOLIDADAS - $(Get-Date)`n# ========================================`n`n"
    $header | Out-File -FilePath $interactiveTarget -Encoding UTF8
    
    foreach ($file in $interactiveFiles) {
        $filePath = "$logsDir\$file"
        if (Test-Path $filePath) {
            "`n# === $file ===" | Add-Content -Path $interactiveTarget -Encoding UTF8
            Get-Content -Path $filePath -Encoding UTF8 | Add-Content -Path $interactiveTarget -Encoding UTF8
            
            # Mover a archived
            $timestamp = Get-Date -Format "yyyyMMdd_HHmmss"
            $archivedName = "$([System.IO.Path]::GetFileNameWithoutExtension($file))_$timestamp.log"
            Move-Item -Path $filePath -Destination "$archiveDir\$archivedName" -Force
            Write-Host "[EMOJI_REMOVIDO] $file -> $archivedName" -ForegroundColor Green
            $consolidated++
        }
    }
    
    # 3. Consolidar Aire
    $airePath = "$logsDir\oficina_virtual_aire.log"
    if (Test-Path $airePath) {
        $aireTarget = "$logsDir\aire_history.log"
        $header = "# AIRE LOGS CONSOLIDADOS - $(Get-Date)`n# ========================================`n`n"
        $header | Out-File -FilePath $aireTarget -Encoding UTF8
        
        if ((Get-Item $airePath).Length -gt 0) {
            Get-Content -Path $airePath -Encoding UTF8 | Add-Content -Path $aireTarget -Encoding UTF8
        } else {
            "# [ARCHIVO VACIO]" | Add-Content -Path $aireTarget -Encoding UTF8
        }
        
        $timestamp = Get-Date -Format "yyyyMMdd_HHmmss"
        Move-Item -Path $airePath -Destination "$archiveDir\oficina_virtual_aire_$timestamp.log" -Force
        Write-Host "[EMOJI_REMOVIDO] oficina_virtual_aire.log -> archived" -ForegroundColor Green
        $consolidated++
    }
    
    # 4. Consolidar S3
    $s3Path = "$logsDir\s3_uploader.log"
    if (Test-Path $s3Path) {
        $s3Target = "$logsDir\s3_history.log"
        $header = "# S3 UPLOADER LOGS CONSOLIDADOS - $(Get-Date)`n# ========================================`n`n"
        $header | Out-File -FilePath $s3Target -Encoding UTF8
        Get-Content -Path $s3Path -Encoding UTF8 | Add-Content -Path $s3Target -Encoding UTF8
        
        $timestamp = Get-Date -Format "yyyyMMdd_HHmmss"
        Move-Item -Path $s3Path -Destination "$archiveDir\s3_uploader_$timestamp.log" -Force
        Write-Host "[EMOJI_REMOVIDO] s3_uploader.log -> archived" -ForegroundColor Green
        $consolidated++
    }
    
    # Actualizar historial
    $historialEntry = "`n[$(Get-Date -Format 'yyyy-MM-dd HH:mm:ss')] LOGS CONSOLIDADOS - $consolidated archivos procesados"
    Add-Content -Path "logs\HISTORIAL_COMPLETO.log" -Value $historialEntry -Encoding UTF8
    
    Write-Host "`n=== CONSOLIDACION COMPLETADA ===" -ForegroundColor Green
    Write-Host "Archivos consolidados: $consolidated" -ForegroundColor White
    
    Write-Host "`nEstructura final:" -ForegroundColor Cyan
    Get-ChildItem -Path $logsDir -File | Select-Object Name, @{Name='KB';Expression={[math]::Round($_.Length/1024,2)}} | Format-Table
    
} else {
    Write-Host "Operacion cancelada" -ForegroundColor Red
}