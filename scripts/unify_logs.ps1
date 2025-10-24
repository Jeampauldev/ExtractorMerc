# Script para unificar y organizar todos los logs del proyecto
# Fecha: 2025-10-08

Write-Host "=== UNIFICACIÓN Y ORGANIZACIÓN DE LOGS ===" -ForegroundColor Green

# Crear estructura de carpetas organizadas
$logsMain = "logs"
$archivedDir = "$logsMain\archived"
$currentDir = "$logsMain\current"
$oldLogsDir = "n_logs_14"

Write-Host "Analizando estructura actual de logs..." -ForegroundColor Yellow

# Verificar contenido actual
Write-Host "`nCarpeta logs principal:" -ForegroundColor Cyan
Get-ChildItem -Path $logsMain -Force | ForEach-Object {
    Write-Host "  $($_.Name) - $($_.Length) bytes - $($_.LastWriteTime)" -ForegroundColor White
}

Write-Host "`nCarpeta n_logs_14:" -ForegroundColor Cyan
Get-ChildItem -Path $oldLogsDir -Force | ForEach-Object {
    Write-Host "  $($_.Name) - $($_.Length) bytes - $($_.LastWriteTime)" -ForegroundColor White
}

# Identificar logs activos (más recientes) vs históricos
Write-Host "`nIdentificando logs para unificar..." -ForegroundColor Yellow

# Logs que están duplicados entre carpetas
$duplicatedLogs = @()
Get-ChildItem -Path $logsMain -File -Force | ForEach-Object {
    $mainFile = $_
    $oldFile = Get-ChildItem -Path $oldLogsDir -File -Force | Where-Object {$_.Name -eq $mainFile.Name}
    if ($oldFile) {
        $duplicatedLogs += @{
            Name = $mainFile.Name
            MainSize = $mainFile.Length
            MainDate = $mainFile.LastWriteTime
            OldSize = $oldFile.Length
            OldDate = $oldFile.LastWriteTime
            KeepMain = $mainFile.LastWriteTime -gt $oldFile.LastWriteTime -or $mainFile.Length -gt $oldFile.Length
        }
    }
}

if ($duplicatedLogs.Count -gt 0) {
    Write-Host "`nLogs duplicados encontrados:" -ForegroundColor Red
    foreach ($dup in $duplicatedLogs) {
        Write-Host "  $($dup.Name):" -ForegroundColor White
        Write-Host "    logs/: $($dup.MainSize) bytes, $($dup.MainDate)" -ForegroundColor Gray
        Write-Host "    n_logs_14/: $($dup.OldSize) bytes, $($dup.OldDate)" -ForegroundColor Gray
        $keep = if ($dup.KeepMain) { "logs/" } else { "n_logs_14/" }
        Write-Host "    → Mantener: $keep" -ForegroundColor Green
    }
}

# Crear plan de unificación
Write-Host "`nPlan de unificación:" -ForegroundColor Yellow

# 1. Mover logs únicos de n_logs_14 a la estructura principal
$uniqueInOld = Get-ChildItem -Path $oldLogsDir -File -Force | Where-Object {
    $oldFile = $_
    -not (Get-ChildItem -Path $logsMain -File -Force | Where-Object {$_.Name -eq $oldFile.Name})
}

if ($uniqueInOld) {
    Write-Host "  1. Logs únicos en n_logs_14 a mover:" -ForegroundColor Cyan
    foreach ($file in $uniqueInOld) {
        $destDir = if ($file.LastWriteTime -lt (Get-Date).AddDays(-30)) { $archivedDir } else { $currentDir }
        Write-Host "    $($file.Name) → $destDir" -ForegroundColor White
    }
} else {
    Write-Host "  1. No hay logs únicos en n_logs_14" -ForegroundColor Green
}

# 2. Para logs duplicados, mantener el mejor y archivar el otro
if ($duplicatedLogs.Count -gt 0) {
    Write-Host "  2. Resolución de duplicados:" -ForegroundColor Cyan
    foreach ($dup in $duplicatedLogs) {
        if ($dup.KeepMain) {
            Write-Host "    $($dup.Name): Mantener logs/, archivar n_logs_14/ como $($dup.Name).old" -ForegroundColor White
        } else {
            Write-Host "    $($dup.Name): Mover n_logs_14/ → logs/, archivar actual como $($dup.Name).old" -ForegroundColor White
        }
    }
}

# 3. Organizar por fechas (current vs archived)
Write-Host "  3. Organización temporal:" -ForegroundColor Cyan
Write-Host "    - Logs recientes (< 30 días) → current/" -ForegroundColor White
Write-Host "    - Logs antiguos (> 30 días) → archived/" -ForegroundColor White

# Preguntar confirmación
Write-Host "`n¿Proceder con la unificación? (S/N): " -ForegroundColor Yellow -NoNewline
$confirm = Read-Host

if ($confirm -eq 'S' -or $confirm -eq 's' -or $confirm -eq 'Y' -or $confirm -eq 'y') {
    Write-Host "`nEjecutando unificación..." -ForegroundColor Green
    
    # Asegurar que existen las carpetas de destino
    if (-not (Test-Path $currentDir)) {
        New-Item -ItemType Directory -Path $currentDir -Force | Out-Null
    }
    if (-not (Test-Path $archivedDir)) {
        New-Item -ItemType Directory -Path $archivedDir -Force | Out-Null
    }
    
    $moved = 0
    $archived = 0
    $resolved = 0
    
    # Mover logs únicos de n_logs_14
    foreach ($file in $uniqueInOld) {
        $destDir = if ($file.LastWriteTime -lt (Get-Date).AddDays(-30)) { $archivedDir } else { $currentDir }
        $destPath = Join-Path $destDir $file.Name
        
        try {
            Move-Item -Path $file.FullName -Destination $destPath -Force
            Write-Host "[EMOJI_REMOVIDO] Movido: $($file.Name) → $destDir" -ForegroundColor Green
            $moved++
        } catch {
            Write-Host "[EMOJI_REMOVIDO] Error moviendo $($file.Name): $($_.Exception.Message)" -ForegroundColor Red
        }
    }
    
    # Resolver duplicados
    foreach ($dup in $duplicatedLogs) {
        $mainPath = Join-Path $logsMain $dup.Name
        $oldPath = Join-Path $oldLogsDir $dup.Name
        
        try {
            if ($dup.KeepMain) {
                # Mantener el de logs/, archivar el de n_logs_14
                $archiveName = "$($dup.Name).old_$(Get-Date -Format 'yyyyMMdd')"
                $archivePath = Join-Path $archivedDir $archiveName
                Move-Item -Path $oldPath -Destination $archivePath -Force
                Write-Host "[EMOJI_REMOVIDO] Duplicado resuelto: $($dup.Name) (mantenido logs/, archivado n_logs_14/)" -ForegroundColor Green
            } else {
                # Mantener el de n_logs_14, archivar el de logs/
                $archiveName = "$($dup.Name).old_$(Get-Date -Format 'yyyyMMdd')"
                $archivePath = Join-Path $archivedDir $archiveName
                Move-Item -Path $mainPath -Destination $archivePath -Force
                
                # Mover el de n_logs_14 a la ubicación correcta
                $destDir = if ((Get-Item $oldPath).LastWriteTime -lt (Get-Date).AddDays(-30)) { $archivedDir } else { $currentDir }
                $finalPath = Join-Path $destDir $dup.Name
                Move-Item -Path $oldPath -Destination $finalPath -Force
                Write-Host "[EMOJI_REMOVIDO] Duplicado resuelto: $($dup.Name) (mantenido n_logs_14/, archivado logs/)" -ForegroundColor Green
            }
            $resolved++
        } catch {
            Write-Host "[EMOJI_REMOVIDO] Error resolviendo duplicado $($dup.Name): $($_.Exception.Message)" -ForegroundColor Red
        }
    }
    
    # Organizar logs existentes en logs/ por fecha
    Get-ChildItem -Path $logsMain -File -Force | Where-Object {$_.Name -ne "HISTORIAL_COMPLETO.log"} | ForEach-Object {
        $destDir = if ($_.LastWriteTime -lt (Get-Date).AddDays(-30)) { $archivedDir } else { $currentDir }
        $destPath = Join-Path $destDir $_.Name
        
        if ($destDir -ne $logsMain) {  # Solo mover si no está ya en el lugar correcto
            try {
                Move-Item -Path $_.FullName -Destination $destPath -Force
                Write-Host "[EMOJI_REMOVIDO] Organizado: $($_.Name) → $destDir" -ForegroundColor Green
                $archived++
            } catch {
                Write-Host "[EMOJI_REMOVIDO] Error organizando $($_.Name): $($_.Exception.Message)" -ForegroundColor Red
            }
        }
    }
    
    # Actualizar log historial completo
    Write-Host "`nActualizando HISTORIAL_COMPLETO.log..." -ForegroundColor Yellow
    $historialPath = Join-Path $logsMain "HISTORIAL_COMPLETO.log"
    $updateEntry = "`n[$(Get-Date -Format 'yyyy-MM-dd HH:mm:ss')] UNIFICACIÓN DE LOGS COMPLETADA"
    $updateEntry += "`n- Logs únicos movidos: $moved"
    $updateEntry += "`n- Duplicados resueltos: $resolved" 
    $updateEntry += "`n- Logs organizados por fecha: $archived"
    $updateEntry += "`n- Estructura final: logs/current/, logs/archived/, logs/HISTORIAL_COMPLETO.log"
    Add-Content -Path $historialPath -Value $updateEntry -Encoding UTF8
    
    Write-Host "`n=== UNIFICACIÓN COMPLETADA ===" -ForegroundColor Green
    Write-Host "Resumen:" -ForegroundColor Yellow
    Write-Host "  [EMOJI_REMOVIDO] Logs únicos movidos: $moved" -ForegroundColor White
    Write-Host "  [EMOJI_REMOVIDO] Duplicados resueltos: $resolved" -ForegroundColor White
    Write-Host "  [EMOJI_REMOVIDO] Logs organizados: $archived" -ForegroundColor White
    
    # Verificar si n_logs_14 está vacía para eliminarla
    $remainingFiles = Get-ChildItem -Path $oldLogsDir -Force
    if ($remainingFiles.Count -eq 0) {
        Write-Host "`nEliminando carpeta vacía n_logs_14..." -ForegroundColor Yellow
        Remove-Item -Path $oldLogsDir -Force
        Write-Host "[EMOJI_REMOVIDO] Carpeta n_logs_14 eliminada" -ForegroundColor Green
    } else {
        Write-Host "`nAdvertencia: n_logs_14 aún contiene archivos:" -ForegroundColor Red
        $remainingFiles | ForEach-Object { Write-Host "  - $($_.Name)" -ForegroundColor Gray }
    }
    
    Write-Host "`nEstructura final de logs:" -ForegroundColor Cyan
    Get-ChildItem -Path $logsMain -Force -Recurse | Select-Object FullName, Length, LastWriteTime | Format-Table -AutoSize
    
} else {
    Write-Host "Operacion cancelada por el usuario." -ForegroundColor Red
}
