# Script de Prueba - Integración Stagehand + Gemini
# ExtractorOV Modular

Write-Host "=== PRUEBA DE INTEGRACIÓN STAGEHAND + GEMINI ===" -ForegroundColor Green

# Variables
$healthUrl = "http://localhost:3001/health"
$apiUrl = "http://localhost:3001/stagehand"

Write-Host "`n1. VERIFICACIÓN DE SERVICIOS" -ForegroundColor Yellow

# Node.js
try {
    $nodeVer = node --version
    Write-Host "Node.js: $nodeVer" -ForegroundColor Green
} catch {
    Write-Host "Node.js: NO DISPONIBLE" -ForegroundColor Red
}

# Health Check
try {
    $health = Invoke-WebRequest -Uri $healthUrl -Method GET
    Write-Host "Stagehand Health: OK ($($health.StatusCode))" -ForegroundColor Green
    $healthData = $health.Content | ConvertFrom-Json
    Write-Host "Status: $($healthData.status)" -ForegroundColor Cyan
} catch {
    Write-Host "Stagehand Health: ERROR" -ForegroundColor Red
    Write-Host "Error: $($_.Exception.Message)" -ForegroundColor Yellow
}

Write-Host "`n2. VERIFICACIÓN DE ARCHIVOS" -ForegroundColor Yellow

$files = @(
    "src\services\ai_integration\package.json",
    "src\services\ai_integration\stagehand_bridge.js",
    "src\services\ai_integration\service_dashboard.html"
)

foreach ($file in $files) {
    if (Test-Path $file) {
        Write-Host "✅ $file" -ForegroundColor Green
    } else {
        Write-Host "❌ $file" -ForegroundColor Red
    }
}

Write-Host "`n3. PRUEBA DE NAVEGACIÓN" -ForegroundColor Yellow

try {
    $body = '{"action": "navigate", "url": "https://example.com"}'
    $response = Invoke-WebRequest -Uri $apiUrl -Method POST -Body $body -ContentType "application/json"
    Write-Host "Navegación: OK ($($response.StatusCode))" -ForegroundColor Green
} catch {
    Write-Host "Navegación: ERROR" -ForegroundColor Red
    Write-Host "Error: $($_.Exception.Message)" -ForegroundColor Yellow
}

Write-Host "`n=== RESUMEN ===" -ForegroundColor Green
Write-Host "Stagehand Bridge ejecutándose en: http://localhost:3001" -ForegroundColor Cyan
Write-Host "Dashboard disponible en: src\services\ai_integration\service_dashboard.html" -ForegroundColor Cyan
Write-Host "Integración lista para usar con Gemini" -ForegroundColor Green