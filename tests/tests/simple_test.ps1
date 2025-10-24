# Test Simple de Stagehand Bridge
Write-Host "Probando Stagehand Bridge..." -ForegroundColor Cyan

# Test 1: Health Check
try {
    $response = Invoke-RestMethod -Uri "http://localhost:3001/health" -Method GET
    Write-Host " Health Check: OK" -ForegroundColor Green
    Write-Host "   Status: $($response.status)" -ForegroundColor White
} catch {
    Write-Host " Health Check: FAIL" -ForegroundColor Red
    Write-Host "   Error: $($_.Exception.Message)" -ForegroundColor Yellow
}

# Test 2: Crear sesión
try {
    $sessionId = "test-215950"
    $body = @{
        sessionId = $sessionId
        config = @{ headless = $true }
    } | ConvertTo-Json
    
    $response = Invoke-RestMethod -Uri "http://localhost:3001/stagehand/create" -Method POST -Body $body -ContentType "application/json"
    Write-Host " Crear sesión: OK" -ForegroundColor Green
    Write-Host "   Session ID: $sessionId" -ForegroundColor White
    
    # Cerrar sesión
    Invoke-RestMethod -Uri "http://localhost:3001/stagehand/$sessionId" -Method DELETE | Out-Null
    Write-Host " Cerrar sesión: OK" -ForegroundColor Green
} catch {
    Write-Host " Crear sesión: FAIL" -ForegroundColor Red
    Write-Host "   Error: $($_.Exception.Message)" -ForegroundColor Yellow
}

Write-Host "Tests completados." -ForegroundColor Cyan
