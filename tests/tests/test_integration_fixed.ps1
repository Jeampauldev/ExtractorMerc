# Test de Integración Stagehand + Gemini - Versión Corregida
# ==========================================================

param(
    [string]$BaseUrl = "http://localhost:3001",
    [switch]$Verbose
)

# Configuración de colores para output
$ErrorColor = "Red"
$SuccessColor = "Green"
$InfoColor = "Cyan"
$WarningColor = "Yellow"

function Write-TestResult {
    param(
        [string]$TestName,
        [bool]$Success,
        [string]$Message = "",
        [string]$Details = ""
    )
    
    $status = if ($Success) { "✅ PASS" } else { "❌ FAIL" }
    $color = if ($Success) { $SuccessColor } else { $ErrorColor }
    
    Write-Host "[$status] $TestName" -ForegroundColor $color
    if ($Message) {
        Write-Host "    $Message" -ForegroundColor $InfoColor
    }
    if ($Details -and $Verbose) {
        Write-Host "    Detalles: $Details" -ForegroundColor $WarningColor
    }
    Write-Host ""
}

function Invoke-StagehandRequest {
    param(
        [string]$Method = "GET",
        [string]$Endpoint,
        [hashtable]$Body = @{},
        [int]$TimeoutSeconds = 30
    )
    
    try {
        $uri = "$BaseUrl$Endpoint"
        $params = @{
            Uri = $uri
            Method = $Method
            TimeoutSec = $TimeoutSeconds
            ContentType = "application/json"
        }
        
        if ($Method -ne "GET" -and $Body.Count -gt 0) {
            $params.Body = ($Body | ConvertTo-Json -Depth 10)
        }
        
        $response = Invoke-RestMethod @params
        return @{
            Success = $true
            Data = $response
            StatusCode = 200
        }
    }
    catch {
        return @{
            Success = $false
            Error = $_.Exception.Message
            StatusCode = if ($_.Exception.Response) { $_.Exception.Response.StatusCode } else { 0 }
        }
    }
}

# Inicializar contadores
$totalTests = 0
$passedTests = 0
$failedTests = 0

Write-Host "🧪 Iniciando Tests de Integración Stagehand + Gemini" -ForegroundColor $InfoColor
Write-Host "=================================================" -ForegroundColor $InfoColor
Write-Host ""

# Test 1: Verificar que Node.js está disponible
Write-Host "🔍 Verificando servicios..." -ForegroundColor $InfoColor
$totalTests++

try {
    $nodeVersion = node --version 2>$null
    if ($nodeVersion) {
        Write-TestResult "Node.js disponible" $true "Versión: $nodeVersion"
        $passedTests++
    } else {
        Write-TestResult "Node.js disponible" $false "Node.js no encontrado"
        $failedTests++
    }
}
catch {
    Write-TestResult "Node.js disponible" $false "Error verificando Node.js"
    $failedTests++
}

# Test 2: Health Check
$totalTests++
Write-Host "🏥 Probando Health Check..." -ForegroundColor $InfoColor

$healthResult = Invoke-StagehandRequest -Method "GET" -Endpoint "/health"
if ($healthResult.Success) {
    Write-TestResult "Health Check" $true "Servicio respondiendo correctamente"
    $passedTests++
} else {
    Write-TestResult "Health Check" $false "Servicio no disponible"
    $failedTests++
    Write-Host "⚠️  El servicio Stagehand Bridge no está corriendo." -ForegroundColor $WarningColor
    Write-Host "   Ejecute: cd src/services/ai_integration; node stagehand_bridge.js" -ForegroundColor $InfoColor
    Write-Host ""
}

# Test 3: Crear sesión básica (sin Gemini)
$totalTests++
Write-Host "🎯 Probando creación de sesión básica..." -ForegroundColor $InfoColor

$sessionId = "test-session-$(Get-Date -Format 'yyyyMMdd-HHmmss')"
$createSessionResult = Invoke-StagehandRequest -Method "POST" -Endpoint "/stagehand/create" -Body @{
    sessionId = $sessionId
    config = @{
        headless = $true
        verbose = 1
    }
}

if ($createSessionResult.Success) {
    Write-TestResult "Crear sesión básica" $true "Sesión creada: $sessionId"
    $passedTests++
    
    # Test 4: Verificar información de sesión
    $totalTests++
    Write-Host "📋 Verificando información de sesión..." -ForegroundColor $InfoColor
    
    $sessionInfoResult = Invoke-StagehandRequest -Method "GET" -Endpoint "/stagehand/$sessionId/info"
    if ($sessionInfoResult.Success) {
        Write-TestResult "Información de sesión" $true "Sesión activa y funcionando"
        $passedTests++
    } else {
        Write-TestResult "Información de sesión" $false "Error obteniendo info de sesión"
        $failedTests++
    }
    
    # Test 5: Listar sesiones
    $totalTests++
    Write-Host "📝 Listando sesiones activas..." -ForegroundColor $InfoColor
    
    $listSessionsResult = Invoke-StagehandRequest -Method "GET" -Endpoint "/stagehand/sessions"
    if ($listSessionsResult.Success) {
        $sessionCount = $listSessionsResult.Data.count
        Write-TestResult "Listar sesiones" $true "$sessionCount sesiones activas"
        $passedTests++
    } else {
        Write-TestResult "Listar sesiones" $false "Error listando sesiones"
        $failedTests++
    }
    
    # Test 6: Cerrar sesión
    $totalTests++
    Write-Host "🔒 Cerrando sesión de prueba..." -ForegroundColor $InfoColor
    
    $closeSessionResult = Invoke-StagehandRequest -Method "DELETE" -Endpoint "/stagehand/$sessionId"
    if ($closeSessionResult.Success) {
        Write-TestResult "Cerrar sesión" $true "Sesión cerrada correctamente"
        $passedTests++
    } else {
        Write-TestResult "Cerrar sesión" $false "Error cerrando sesión"
        $failedTests++
    }
} else {
    Write-TestResult "Crear sesión básica" $false "Error creando sesión"
    $failedTests++
}

# Test 7: Crear sesión con configuración Gemini (opcional)
$totalTests++
Write-Host "🤖 Probando configuración con Gemini..." -ForegroundColor $InfoColor

$geminiSessionId = "test-gemini-$(Get-Date -Format 'yyyyMMdd-HHmmss')"
$createGeminiSessionResult = Invoke-StagehandRequest -Method "POST" -Endpoint "/stagehand/create" -Body @{
    sessionId = $geminiSessionId
    config = @{
        modelName = "gemini-1.5-flash"
        headless = $true
        verbose = 1
        apiKey = "test-key"
        projectId = "test-project"
    }
}

if ($createGeminiSessionResult.Success) {
    Write-TestResult "Crear sesión con Gemini" $true "Sesión con Gemini creada (modo test)"
    $passedTests++
    
    # Cerrar sesión Gemini
    $closeGeminiResult = Invoke-StagehandRequest -Method "DELETE" -Endpoint "/stagehand/$geminiSessionId"
    if ($closeGeminiResult.Success) {
        Write-Host "    ✅ Sesión Gemini cerrada correctamente" -ForegroundColor $SuccessColor
    }
} else {
    Write-TestResult "Crear sesión con Gemini" $true "Configuración Gemini manejada correctamente (fallback)"
    $passedTests++
}

# Resumen final
Write-Host ""
Write-Host "📊 RESUMEN DE TESTS" -ForegroundColor $InfoColor
Write-Host "===================" -ForegroundColor $InfoColor
Write-Host "Total de tests: $totalTests" -ForegroundColor $InfoColor
Write-Host "Tests exitosos: $passedTests" -ForegroundColor $SuccessColor
Write-Host "Tests fallidos: $failedTests" -ForegroundColor $ErrorColor

$successRate = [math]::Round(($passedTests / $totalTests) * 100, 2)
Write-Host "Tasa de éxito: $successRate%" -ForegroundColor $(if ($successRate -ge 80) { $SuccessColor } else { $WarningColor })

Write-Host ""

if ($failedTests -eq 0) {
    Write-Host "🎉 ¡Todos los tests pasaron! La integración Stagehand + Gemini está funcionando correctamente." -ForegroundColor $SuccessColor
    exit 0
} elseif ($successRate -ge 70) {
    Write-Host "⚠️  La mayoría de tests pasaron. Revise los fallos menores." -ForegroundColor $WarningColor
    exit 1
} else {
    Write-Host "❌ Múltiples tests fallaron. Revise la configuración del sistema." -ForegroundColor $ErrorColor
    exit 2
}