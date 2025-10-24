@echo off
echo ========================================
echo Instalando dependencias de Stagehand
echo ========================================

echo Verificando Node.js...
node --version
if %errorlevel% neq 0 (
    echo ERROR: Node.js no está instalado
    echo Por favor instala Node.js desde https://nodejs.org/
    pause
    exit /b 1
)

echo Verificando npm...
npm --version
if %errorlevel% neq 0 (
    echo ERROR: npm no está disponible
    pause
    exit /b 1
)

echo Instalando dependencias...
npm install @browserbase/stagehand express cors body-parser winston

if %errorlevel% neq 0 (
    echo ERROR: Falló la instalación de dependencias
    pause
    exit /b 1
)

echo ========================================
echo Instalación completada exitosamente!
echo ========================================
echo.
echo Para iniciar el bridge de Stagehand:
echo   node stagehand_bridge.js
echo.
pause