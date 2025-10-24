@echo off
chcp 65001 >nul
echo ===== CONFIGURACION DE CONEXION RDS =====
echo.

echo [1/4] Verificando Python...
python --version
if %errorlevel% neq 0 (
    echo ERROR: Python no esta instalado o no esta en PATH
    pause
    exit /b 1
)

echo.
echo [2/4] Creando entorno virtual...
if exist "venv" (
    echo Entorno virtual ya existe, eliminando...
    rmdir /s /q venv
)
python -m venv venv
if %errorlevel% neq 0 (
    echo ERROR: No se pudo crear el entorno virtual
    pause
    exit /b 1
)

echo.
echo [3/4] Activando entorno e instalando dependencias...
call venv\Scripts\activate.bat
pip install --upgrade pip
pip install -r requirements.txt
if %errorlevel% neq 0 (
    echo ERROR: No se pudieron instalar las dependencias
    pause
    exit /b 1
)

echo.
echo [4/4] Probando conexion...
python conexion_rds.py

echo.
echo ===== CONFIGURACION COMPLETADA =====
pause