# Script para limpiar carpetas problemáticas y verificar estructura
Write-Host "=== LIMPIEZA DE CARPETAS PROBLEMATICAS ===" -ForegroundColor Green

Write-Host "`nAnalizando problemas encontrados..." -ForegroundColor Yellow

# 1. Verificar carpeta downloads problemática
Write-Host "`n1. CARPETA DOWNLOADS PROBLEMÁTICA:" -ForegroundColor Red
if (Test-Path "downloads") {
    Write-Host "   [ERROR] Carpeta 'downloads' encontrada (no debería existir)" -ForegroundColor Red
    Write-Host "   [EMOJI_REMOVIDO] Contenido:" -ForegroundColor Cyan
    Get-ChildItem -Path "downloads" -Force | ForEach-Object {
        Write-Host "      - $($_.Name)" -ForegroundColor White
    }
    Write-Host "   [EXITOSO] SOLUCION: Eliminar y usar m_downloads_13/" -ForegroundColor Green
} else {
    Write-Host "   [EXITOSO] No hay carpeta downloads problemática" -ForegroundColor Green
}

# 2. Verificar estructura de logs
Write-Host "`n2. VERIFICAR LOGS:" -ForegroundColor Cyan
$logsHidden = (Get-Item "logs" -Force).Attributes -match "Hidden"
if ($logsHidden) {
    Write-Host "   [ERROR] Carpeta logs está oculta" -ForegroundColor Red
    Write-Host "   [EXITOSO] SOLUCION: Hacer visible" -ForegroundColor Green
} else {
    Write-Host "   [EXITOSO] Carpeta logs es visible" -ForegroundColor Green
}

# 3. Verificar archivos .env
Write-Host "`n3. VERIFICAR ARCHIVOS .ENV:" -ForegroundColor Cyan
if (Test-Path ".env") {
    Write-Host "   [ERROR] Archivo .env en raíz (debería estar en p16_env/)" -ForegroundColor Red
    Write-Host "   [EXITOSO] SOLUCION: Mover a p16_env/" -ForegroundColor Green
} else {
    Write-Host "   [EXITOSO] No hay .env en raíz" -ForegroundColor Green
}

# Verificar p16_env
if (Test-Path "p16_env\.env") {
    Write-Host "   [EXITOSO] .env está correctamente en p16_env/" -ForegroundColor Green
} else {
    Write-Host "   [ADVERTENCIA] No hay .env en p16_env/" -ForegroundColor Yellow
}

# 4. Verificar otras carpetas ocultas
Write-Host "`n4. ARCHIVOS/CARPETAS OCULTAS INNECESARIAS:" -ForegroundColor Cyan
$hiddenItems = Get-ChildItem -Force | Where-Object {
    ($_.Attributes -match "Hidden") -and 
    ($_.Name -ne ".git") -and 
    ($_.Name -ne ".venv")
}

if ($hiddenItems.Count -gt 0) {
    Write-Host "   [ERROR] Elementos ocultos innecesarios encontrados:" -ForegroundColor Red
    $hiddenItems | ForEach-Object {
        Write-Host "      - $($_.Name)" -ForegroundColor White
    }
} else {
    Write-Host "   [EXITOSO] Solo .git y .venv están ocultos (correcto)" -ForegroundColor Green
}

Write-Host "`n¿Proceder con la limpieza? (S/N): " -ForegroundColor Yellow -NoNewline
$confirm = Read-Host

if ($confirm -eq 'S' -or $confirm -eq 's' -or $confirm -eq 'Y' -or $confirm -eq 'y') {
    Write-Host "`nEjecutando limpieza..." -ForegroundColor Green
    
    $cleaned = 0
    
    # 1. Eliminar carpeta downloads problemática
    if (Test-Path "downloads") {
        Write-Host "[EMOJI_REMOVIDO] Eliminando carpeta downloads problemática..." -ForegroundColor Yellow
        
        # Verificar si hay contenido importante
        $hasContent = (Get-ChildItem -Path "downloads" -Recurse -Force).Count -gt 0
        if ($hasContent) {
            # Hacer backup antes de eliminar
            $backupDir = "m_downloads_13\backup_downloads_$(Get-Date -Format 'yyyyMMdd_HHmmss')"
            New-Item -ItemType Directory -Path $backupDir -Force | Out-Null
            Copy-Item -Path "downloads\*" -Destination $backupDir -Recurse -Force
            Write-Host "   [EXITOSO] Backup creado en: $backupDir" -ForegroundColor Green
        }
        
        Remove-Item -Path "downloads" -Recurse -Force
        Write-Host "   [EXITOSO] Carpeta downloads eliminada" -ForegroundColor Green
        $cleaned++
    }
    
    # 2. Asegurar que logs sea visible
    if (Test-Path "logs") {
        $logsAttribs = (Get-Item "logs" -Force).Attributes
        if ($logsAttribs -match "Hidden") {
            Write-Host "[EMOJI_REMOVIDO] Haciendo visible la carpeta logs..." -ForegroundColor Yellow
            (Get-Item "logs" -Force).Attributes = 'Directory'
            Write-Host "   [EXITOSO] Carpeta logs ahora es visible" -ForegroundColor Green
            $cleaned++
        }
    }
    
    # 3. Mover .env si está en lugar incorrecto
    if (Test-Path ".env") {
        Write-Host "[ARCHIVO] Moviendo .env a p16_env/..." -ForegroundColor Yellow
        
        # Backup del archivo actual en p16_env si existe
        if (Test-Path "p16_env\.env") {
            $timestamp = Get-Date -Format "yyyyMMdd_HHmmss"
            Copy-Item "p16_env\.env" "p16_env\.env.backup_$timestamp"
            Write-Host "   [EMOJI_REMOVIDO] Backup del .env actual creado" -ForegroundColor Cyan
        }
        
        Move-Item ".env" "p16_env\.env" -Force
        Write-Host "   [EXITOSO] .env movido a p16_env/" -ForegroundColor Green
        $cleaned++
    }
    
    # 4. Limpiar archivos ocultos innecesarios
    $hiddenToClean = Get-ChildItem -Force | Where-Object {
        ($_.Attributes -match "Hidden") -and 
        ($_.Name -ne ".git") -and 
        ($_.Name -ne ".venv") -and
        ($_.Name -ne "logs")  # Por si logs estaba oculto
    }
    
    foreach ($item in $hiddenToClean) {
        Write-Host "[ARCHIVO] Limpiando elemento oculto: $($item.Name)..." -ForegroundColor Yellow
        
        if ($item.PSIsContainer) {
            Remove-Item -Path $item.FullName -Recurse -Force
        } else {
            Remove-Item -Path $item.FullName -Force
        }
        Write-Host "   [EXITOSO] $($item.Name) eliminado" -ForegroundColor Green
        $cleaned++
    }
    
    # 5. Verificar estructura final
    Write-Host "`nVerificando estructura final..." -ForegroundColor Cyan
    
    # Verificar que m_downloads_13 existe y es la carpeta correcta
    if (Test-Path "m_downloads_13") {
        Write-Host "   [EXITOSO] m_downloads_13/ existe (carpeta correcta para descargas)" -ForegroundColor Green
    } else {
        Write-Host "   [ADVERTENCIA] m_downloads_13/ no existe, creando..." -ForegroundColor Yellow
        New-Item -ItemType Directory -Path "m_downloads_13" -Force | Out-Null
        New-Item -ItemType Directory -Path "m_downloads_13\afinia" -Force | Out-Null
        New-Item -ItemType Directory -Path "m_downloads_13\aire" -Force | Out-Null
        Write-Host "   [EXITOSO] m_downloads_13/ creado con subdirectorios" -ForegroundColor Green
    }
    
    # Verificar p16_env
    if (Test-Path "p16_env\.env") {
        Write-Host "   [EXITOSO] p16_env/.env existe" -ForegroundColor Green
    } else {
        Write-Host "   [ADVERTENCIA] p16_env/.env no existe" -ForegroundColor Yellow
    }
    
    # Verificar logs
    if (Test-Path "logs" -and -not ((Get-Item "logs" -Force).Attributes -match "Hidden")) {
        Write-Host "   [EXITOSO] logs/ existe y es visible" -ForegroundColor Green
    }
    
    Write-Host "`n=== LIMPIEZA COMPLETADA ===" -ForegroundColor Green
    Write-Host "Elementos limpiados: $cleaned" -ForegroundColor White
    
    Write-Host "`nESTRUCTURA CORREGIDA:" -ForegroundColor Cyan
    Write-Host "  [EMOJI_REMOVIDO] logs/ - Visible, organizada" -ForegroundColor Green
    Write-Host "  [EMOJI_REMOVIDO] m_downloads_13/ - Carpeta correcta para descargas" -ForegroundColor Green
    Write-Host "  [EMOJI_REMOVIDO] p16_env/ - Contiene .env y configuraciones" -ForegroundColor Green
    Write-Host "  [EMOJI_REMOVIDO] .git/ - Oculta (correcto)" -ForegroundColor Green
    Write-Host "  [EMOJI_REMOVIDO] .venv/ - Entorno virtual (correcto)" -ForegroundColor Green
    
    # Actualizar historial
    $historialEntry = "`n[$(Get-Date -Format 'yyyy-MM-dd HH:mm:ss')] LIMPIEZA DE ESTRUCTURA - $cleaned elementos corregidos"
    $historialEntry += "`n- Carpetas problemáticas eliminadas"
    $historialEntry += "`n- Archivos .env ubicados correctamente"
    $historialEntry += "`n- Carpetas visibles donde corresponde"
    Add-Content -Path "logs\HISTORIAL_COMPLETO.log" -Value $historialEntry -Encoding UTF8
    
} else {
    Write-Host "Operacion cancelada por el usuario." -ForegroundColor Red
}
