# Script para solucionar el problema de npm permanentemente
# Este script debe ejecutarse como administrador

Write-Host "=== Solucionador de NPM - Eliminación de archivo conflictivo ===" -ForegroundColor Green

# Verificar si se ejecuta como administrador
$isAdmin = ([Security.Principal.WindowsPrincipal] [Security.Principal.WindowsIdentity]::GetCurrent()).IsInRole([Security.Principal.WindowsBuiltInRole] "Administrator")

if (-not $isAdmin) {
    Write-Host "ERROR: Este script debe ejecutarse como administrador" -ForegroundColor Red
    Write-Host "Haz clic derecho en PowerShell y selecciona 'Ejecutar como administrador'" -ForegroundColor Yellow
    Read-Host "Presiona Enter para salir"
    exit 1
}

# Verificar si existe el archivo conflictivo
$conflictFile = "C:\Windows\system32\npm"
if (Test-Path $conflictFile) {
    Write-Host "Archivo conflictivo encontrado: $conflictFile" -ForegroundColor Yellow
    
    try {
        # Tomar propiedad del archivo
        Write-Host "Tomando propiedad del archivo..." -ForegroundColor Cyan
        takeown /f $conflictFile /a
        
        # Dar permisos completos
        Write-Host "Asignando permisos..." -ForegroundColor Cyan
        icacls $conflictFile /grant administrators:F
        
        # Eliminar el archivo
        Write-Host "Eliminando archivo conflictivo..." -ForegroundColor Cyan
        Remove-Item $conflictFile -Force
        
        Write-Host "✓ Archivo conflictivo eliminado exitosamente" -ForegroundColor Green
    }
    catch {
        Write-Host "ERROR: No se pudo eliminar el archivo: $($_.Exception.Message)" -ForegroundColor Red
        exit 1
    }
} else {
    Write-Host "✓ No se encontró archivo conflictivo" -ForegroundColor Green
}

# Verificar que npm funciona correctamente
Write-Host "`nVerificando npm..." -ForegroundColor Cyan
try {
    $npmVersion = npm --version
    Write-Host "✓ NPM funciona correctamente. Versión: $npmVersion" -ForegroundColor Green
}
catch {
    Write-Host "ERROR: NPM aún no funciona correctamente" -ForegroundColor Red
    Write-Host "Verifica que Node.js esté instalado correctamente" -ForegroundColor Yellow
}

Write-Host "`n=== Solución completada ===" -ForegroundColor Green
Write-Host "Ahora puedes usar npm normalmente en cualquier proyecto" -ForegroundColor White
Read-Host "Presiona Enter para salir"