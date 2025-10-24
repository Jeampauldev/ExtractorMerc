# Script simplificado para unificar logs
Write-Host "=== UNIFICACION DE LOGS ===" -ForegroundColor Green

# Analizar la situacion actual
Write-Host "`nAnalizando logs actuales..." -ForegroundColor Yellow

Write-Host "`nCarpeta logs/:" -ForegroundColor Cyan
Get-ChildItem -Path "logs" -Force | ForEach-Object {
    Write-Host "  $($_.Name) - $($_.Length) bytes - $($_.LastWriteTime)" -ForegroundColor White
}

Write-Host "`nCarpeta n_logs_14/:" -ForegroundColor Cyan
Get-ChildItem -Path "n_logs_14" -Force | ForEach-Object {
    Write-Host "  $($_.Name) - $($_.Length) bytes - $($_.LastWriteTime)" -ForegroundColor White
}

# Identificar duplicados
Write-Host "`nIdentificando duplicados..." -ForegroundColor Yellow
$logsInMain = Get-ChildItem -Path "logs" -File -Force
$logsInOld = Get-ChildItem -Path "n_logs_14" -File -Force

$duplicates = @()
foreach ($mainFile in $logsInMain) {
    $oldFile = $logsInOld | Where-Object {$_.Name -eq $mainFile.Name}
    if ($oldFile) {
        $duplicates += [PSCustomObject]@{
            Name = $mainFile.Name
            MainSize = $mainFile.Length
            MainDate = $mainFile.LastWriteTime
            OldSize = $oldFile.Length
            OldDate = $oldFile.LastWriteTime
        }
    }
}

if ($duplicates.Count -gt 0) {
    Write-Host "`nDuplicados encontrados:" -ForegroundColor Red
    $duplicates | Format-Table -AutoSize
}

# Identificar unicos en n_logs_14
$uniqueInOld = $logsInOld | Where-Object {
    $fileName = $_.Name
    -not ($logsInMain | Where-Object {$_.Name -eq $fileName})
}

if ($uniqueInOld) {
    Write-Host "`nLogs unicos en n_logs_14:" -ForegroundColor Cyan
    $uniqueInOld | ForEach-Object {
        Write-Host "  $($_.Name) - $($_.Length) bytes - $($_.LastWriteTime)" -ForegroundColor White
    }
}

Write-Host "`n¿Proceder con la unificacion? (Y/N): " -ForegroundColor Yellow -NoNewline
$response = Read-Host

if ($response -eq "Y" -or $response -eq "y") {
    Write-Host "`nEjecutando unificacion..." -ForegroundColor Green
    
    # Crear carpetas si no existen
    if (-not (Test-Path "logs\current")) {
        New-Item -ItemType Directory -Path "logs\current" -Force | Out-Null
        Write-Host "Creada carpeta logs\current" -ForegroundColor Green
    }
    
    if (-not (Test-Path "logs\archived")) {
        New-Item -ItemType Directory -Path "logs\archived" -Force | Out-Null
        Write-Host "Creada carpeta logs\archived" -ForegroundColor Green
    }
    
    $moved = 0
    $resolved = 0
    
    # Mover logs unicos de n_logs_14
    foreach ($file in $uniqueInOld) {
        $isRecent = $file.LastWriteTime -gt (Get-Date).AddDays(-30)
        $destFolder = if ($isRecent) {"logs\current"} else {"logs\archived"}
        $destPath = Join-Path $destFolder $file.Name
        
        Move-Item -Path $file.FullName -Destination $destPath -Force
        Write-Host "Movido: $($file.Name) -> $destFolder" -ForegroundColor Green
        $moved++
    }
    
    # Resolver duplicados - mantener el mas reciente/grande
    foreach ($dup in $duplicates) {
        $mainPath = "logs\$($dup.Name)"
        $oldPath = "n_logs_14\$($dup.Name)"
        
        $keepMain = ($dup.MainDate -gt $dup.OldDate) -or 
                   (($dup.MainDate -eq $dup.OldDate) -and ($dup.MainSize -ge $dup.OldSize))
        
        if ($keepMain) {
            # Mantener el de logs/, eliminar el de n_logs_14
            Remove-Item -Path $oldPath -Force
            Write-Host "Duplicado resuelto: $($dup.Name) (mantenido logs/, eliminado n_logs_14/)" -ForegroundColor Green
        } else {
            # Mantener el de n_logs_14, reemplazar el de logs/
            Move-Item -Path $oldPath -Destination $mainPath -Force
            Write-Host "Duplicado resuelto: $($dup.Name) (reemplazado logs/ con n_logs_14/)" -ForegroundColor Green
        }
        $resolved++
    }
    
    # Organizar logs en logs/ por fecha
    $logsToOrganize = Get-ChildItem -Path "logs" -File -Force | Where-Object {$_.Name -ne "HISTORIAL_COMPLETO.log"}
    foreach ($file in $logsToOrganize) {
        $isRecent = $file.LastWriteTime -gt (Get-Date).AddDays(-30)
        $destFolder = if ($isRecent) {"logs\current"} else {"logs\archived"}
        
        if ($file.Directory.Name -eq "logs") {
            $destPath = Join-Path $destFolder $file.Name
            Move-Item -Path $file.FullName -Destination $destPath -Force
            Write-Host "Organizado: $($file.Name) -> $destFolder" -ForegroundColor Green
        }
    }
    
    # Verificar si n_logs_14 esta vacia
    $remaining = Get-ChildItem -Path "n_logs_14" -Force
    if ($remaining.Count -eq 0) {
        Remove-Item -Path "n_logs_14" -Force
        Write-Host "Eliminada carpeta vacia n_logs_14" -ForegroundColor Green
    } else {
        Write-Host "Archivos restantes en n_logs_14:" -ForegroundColor Yellow
        $remaining | ForEach-Object { Write-Host "  - $($_.Name)" }
    }
    
    # Actualizar historial
    $historialEntry = "`n[$(Get-Date -Format 'yyyy-MM-dd HH:mm:ss')] LOGS UNIFICADOS - Unicos movidos: $moved, Duplicados resueltos: $resolved"
    Add-Content -Path "logs\HISTORIAL_COMPLETO.log" -Value $historialEntry -Encoding UTF8
    
    Write-Host "`n=== UNIFICACION COMPLETADA ===" -ForegroundColor Green
    Write-Host "Logs unicos movidos: $moved" -ForegroundColor White  
    Write-Host "Duplicados resueltos: $resolved" -ForegroundColor White
    
    Write-Host "`nEstructura final:" -ForegroundColor Cyan
    Get-ChildItem -Path "logs" -Force -Recurse | Select-Object FullName
    
} else {
    Write-Host "Operacion cancelada" -ForegroundColor Red
}