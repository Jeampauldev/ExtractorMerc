# Script para consolidar y renombrar logs existentes
# Fecha: 2025-10-08

Write-Host "=== CONSOLIDACIÓN DE LOGS EXISTENTES ===" -ForegroundColor Green

$logsDir = "logs\current"
$archiveDir = "logs\archived"

Write-Host "`nAnalizando logs actuales..." -ForegroundColor Yellow

# Obtener todos los logs actuales
$currentLogs = Get-ChildItem -Path $logsDir -File | Sort-Object Name

Write-Host "`nLogs encontrados:" -ForegroundColor Cyan
foreach ($log in $currentLogs) {
    $sizeKB = [math]::Round($log.Length / 1024, 2)
    Write-Host "  [ARCHIVO] $($log.Name) - ${sizeKB}KB - $($log.LastWriteTime)" -ForegroundColor White
}

Write-Host "`nPlan de consolidación:" -ForegroundColor Yellow

# Definir categorías de consolidación
$consolidationPlan = @{
    "afinia_consolidated.log" = @(
        "afinia_ov_visual.log",
        "afinia_ov_visual2.log", 
        "oficina_virtual_afinia.log"
    )
    "aire_consolidated.log" = @(
        "oficina_virtual_aire.log"
    )
    "interactive_sessions_consolidated.log" = @(
        "extractor_interactive_20251001_170326.log",
        "extractor_interactive_20251001_170600.log",
        "extractor_interactive_20251001_170753.log",
        "extractor_interactive_20251003_124142.log",
        "extractor_interactive_20251003_124337.log",
        "extractor_interactive_20251003_124544.log",
        "extractor_interactive_20251003_124732.log",
        "extractor_interactive_20251003_124847.log"
    )
    "s3_uploader_consolidated.log" = @(
        "s3_uploader.log"
    )
}

Write-Host "`n1. LOGS DE AFINIA → afinia_consolidated.log" -ForegroundColor Cyan
foreach ($file in $consolidationPlan["afinia_consolidated.log"]) {
    if (Test-Path "$logsDir\$file") {
        $size = (Get-Item "$logsDir\$file").Length
        Write-Host "   + $file ($size bytes)" -ForegroundColor White
    }
}

Write-Host "`n2. LOGS DE AIRE → aire_consolidated.log" -ForegroundColor Cyan
foreach ($file in $consolidationPlan["aire_consolidated.log"]) {
    if (Test-Path "$logsDir\$file") {
        $size = (Get-Item "$logsDir\$file").Length
        Write-Host "   + $file ($size bytes)" -ForegroundColor White
    }
}

Write-Host "`n3. SESIONES INTERACTIVAS → interactive_sessions_consolidated.log" -ForegroundColor Cyan
foreach ($file in $consolidationPlan["interactive_sessions_consolidated.log"]) {
    if (Test-Path "$logsDir\$file") {
        $size = (Get-Item "$logsDir\$file").Length
        Write-Host "   + $file ($size bytes)" -ForegroundColor White
    }
}

Write-Host "`n4. S3 UPLOADER → s3_uploader_consolidated.log" -ForegroundColor Cyan
foreach ($file in $consolidationPlan["s3_uploader_consolidated.log"]) {
    if (Test-Path "$logsDir\$file") {
        $size = (Get-Item "$logsDir\$file").Length
        Write-Host "   + $file ($size bytes)" -ForegroundColor White
    }
}

Write-Host "`n5. MANTENER SIN CAMBIOS:" -ForegroundColor Green
Write-Host "   [EMOJI_REMOVIDO] afinia_ov.log (nuevo sistema unificado)" -ForegroundColor White
Write-Host "   [EMOJI_REMOVIDO] aire_ov.log (nuevo sistema unificado)" -ForegroundColor White

Write-Host "`n¿Proceder con la consolidación? (S/N): " -ForegroundColor Yellow -NoNewline
$confirm = Read-Host

if ($confirm -eq 'S' -or $confirm -eq 's' -or $confirm -eq 'Y' -or $confirm -eq 'y') {
    Write-Host "`nEjecutando consolidación..." -ForegroundColor Green
    
    $consolidated = 0
    $totalSize = 0
    
    foreach ($targetFile in $consolidationPlan.Keys) {
        $targetPath = "$logsDir\$targetFile"
        $sourceFiles = $consolidationPlan[$targetFile]
        
        # Crear encabezado del archivo consolidado
        $header = @"
# ========================================
# LOG CONSOLIDADO: $targetFile
# Fecha de consolidación: $(Get-Date -Format 'yyyy-MM-dd HH:mm:ss')
# Archivos originales consolidados:
$(foreach ($file in $sourceFiles) { if (Test-Path "$logsDir\$file") { "# - $file" } })
# ========================================

"@
        
        # Escribir encabezado
        $header | Out-File -FilePath $targetPath -Encoding UTF8
        
        $filesToConsolidate = @()
        
        # Consolidar cada archivo fuente
        foreach ($sourceFile in $sourceFiles) {
            $sourcePath = "$logsDir\$sourceFile"
            
            if (Test-Path $sourcePath) {
                $filesToConsolidate += $sourceFile
                
                # Añadir separador y contenido
                $separator = "`n`n# ==================== INICIO: $sourceFile ===================="
                $separator | Out-File -FilePath $targetPath -Append -Encoding UTF8
                
                # Agregar contenido del archivo
                if ((Get-Item $sourcePath).Length -gt 0) {
                    Get-Content -Path $sourcePath -Encoding UTF8 | Out-File -FilePath $targetPath -Append -Encoding UTF8
                } else {
                    "# [ARCHIVO VACÍO]" | Out-File -FilePath $targetPath -Append -Encoding UTF8
                }
                
                $endSeparator = "# ==================== FIN: $sourceFile ===================="
                $endSeparator | Out-File -FilePath $targetPath -Append -Encoding UTF8
                
                $totalSize += (Get-Item $sourcePath).Length
            }
        }
        
        if ($filesToConsolidate.Count -gt 0) {
            Write-Host "[EMOJI_REMOVIDO] Consolidado: $targetFile ($($filesToConsolidate.Count) archivos)" -ForegroundColor Green
            $consolidated += $filesToConsolidate.Count
            
            # Mover archivos originales a archived con timestamp
            $timestamp = Get-Date -Format "yyyyMMdd_HHmmss"
            foreach ($file in $filesToConsolidate) {
                $sourcePath = "$logsDir\$file"
                $archivedName = "$([System.IO.Path]::GetFileNameWithoutExtension($file))_original_$timestamp$([System.IO.Path]::GetExtension($file))"
                $archivedPath = "$archiveDir\$archivedName"
                
                Move-Item -Path $sourcePath -Destination $archivedPath -Force
                Write-Host "  → $file archivado como $archivedName" -ForegroundColor Gray
            }
        }
    }
    
    # Actualizar historial
    $historialPath = "logs\HISTORIAL_COMPLETO.log"
    $updateEntry = "`n[$(Get-Date -Format 'yyyy-MM-dd HH:mm:ss')] CONSOLIDACIÓN DE LOGS COMPLETADA"
    $updateEntry += "`n- Archivos consolidados: $consolidated"
    $updateEntry += "`n- Tamaño total procesado: $([math]::Round($totalSize / 1024, 2)) KB"
    $updateEntry += "`n- Archivos consolidados creados: $($consolidationPlan.Keys.Count)"
    $updateEntry += "`n- Estructura final simplificada y organizada"
    Add-Content -Path $historialPath -Value $updateEntry -Encoding UTF8
    
    Write-Host "`n=== CONSOLIDACIÓN COMPLETADA ===" -ForegroundColor Green
    Write-Host "Resumen:" -ForegroundColor Yellow
    Write-Host "  [EMOJI_REMOVIDO] Archivos consolidados: $consolidated" -ForegroundColor White
    Write-Host "  [EMOJI_REMOVIDO] Tamaño total: $([math]::Round($totalSize / 1024, 2)) KB" -ForegroundColor White
    Write-Host "  [EMOJI_REMOVIDO] Archivos originales archivados" -ForegroundColor White
    
    Write-Host "`nEstructura final en logs/current/:" -ForegroundColor Cyan
    Get-ChildItem -Path $logsDir -File | Select-Object Name, @{Name='Size(KB)';Expression={[math]::Round($_.Length/1024,2)}} | Format-Table -AutoSize
    
} else {
    Write-Host "Operación cancelada por el usuario." -ForegroundColor Red
}