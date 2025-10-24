# Manual de Instalación y Configuración - ExtractorOV Modular

## Requisitos del Sistema

### Hardware Mínimo
- **CPU**: Intel Core i3 / AMD Ryzen 3 o superior
- **RAM**: 4 GB (recomendado 8 GB)
- **Almacenamiento**: 10 GB libres en disco
- **Conexión**: Internet estable con ancho de banda mínimo 10 Mbps

### Hardware Recomendado para Producción
- **CPU**: Intel Core i5 / AMD Ryzen 5 o superior (múltiples núcleos)
- **RAM**: 16 GB o superior
- **Almacenamiento**: SSD con 50 GB libres
- **Conexión**: Internet dedicada con ancho de banda 50 Mbps o superior

### Software Base

#### Windows 10/11
- **Sistema Operativo**: Windows 10 versión 1909 o superior
- **Python**: 3.8, 3.9, 3.10, o 3.11
- **PowerShell**: 5.1 o PowerShell 7+
- **Git**: Versión más reciente
- **Visual C++ Redistributable**: Instalado automáticamente con Python

#### Ubuntu Server (Recomendado para Producción)
- **Sistema Operativo**: Ubuntu 18.04 LTS o superior (recomendado 20.04/22.04 LTS)
- **Python**: 3.8 o superior (usualmente preinstalado)
- **Git**: Instalado
- **Dependencias del sistema**: Se instalan durante el proceso

## Instalación en Windows

### Paso 1: Preparación del Entorno

```powershell
# Verificar versión de Python
python --version

# Si Python no está instalado, descargar desde:
# https://python.org/downloads/

# Verificar Git
git --version

# Si Git no está instalado, descargar desde:
# https://git-scm.com/downloads
```

### Paso 2: Clonar el Repositorio

```powershell
# Clonar el proyecto
git clone https://github.com/tu-usuario/ExtractorOV_Modular.git
cd ExtractorOV_Modular

# Verificar contenido
dir
```

### Paso 3: Crear Entorno Virtual

```powershell
# Crear entorno virtual
python -m venv venv

# Activar entorno virtual
venv\Scripts\activate

# Verificar activación (debe aparecer (venv) al inicio del prompt)
python --version
pip --version
```

### Paso 4: Instalar Dependencias

```powershell
# Actualizar pip
python -m pip install --upgrade pip

# Instalar dependencias principales
pip install -r requirements.txt

# Verificar instalación crítica
pip show playwright python-dotenv pandas openpyxl

# Instalar navegadores para Playwright
python -m playwright install chromium

# Verificar instalación
python -m playwright install-deps
```

### Paso 5: Configurar Variables de Entorno

```powershell
# Crear directorio de configuración si no existe
if (!(Test-Path "config\env")) {
    New-Item -ItemType Directory -Path "config\env" -Force
}

# Copiar archivo de ejemplo
copy "config\env\.env.example" "config\env\.env"

# Editar archivo .env con credenciales reales
notepad "config\env\.env"
```

### Paso 6: Verificar Instalación

```powershell
# Test básico de importación
python -c "
import sys
sys.path.append('.')
print('Verificando importaciones básicas...')

try:
    from afinia_manager import AfiniaManager
    print('OK: afinia_manager importado correctamente')
except Exception as e:
    print(f'ERROR: {e}')

try:
    from aire_manager import AireManager
    print('OK: aire_manager importado correctamente')
except Exception as e:
    print(f'ERROR: {e}')

print('Verificación completada')
"

# Test de configuración
python scripts\validate_functionality.py
```

## Instalación en Ubuntu Server

### Paso 1: Preparación del Sistema

```bash
# Actualizar sistema
sudo apt update && sudo apt upgrade -y

# Instalar dependencias base
sudo apt install -y python3 python3-pip python3-venv git curl wget

# Instalar dependencias para Playwright
sudo apt install -y libnss3 libatk-bridge2.0-0 libdrm2 libxkbcommon0 \
    libxcomposite1 libxdamage1 libxrandr2 libgbm1 libxss1 libasound2
```

### Paso 2: Instalación Automatizada (Recomendada)

```bash
# Clonar repositorio
git clone https://github.com/tu-usuario/ExtractorOV_Modular.git
cd ExtractorOV_Modular

# Ejecutar script de instalación automática
chmod +x scripts/ubuntu_setup.sh
./scripts/ubuntu_setup.sh

# El script realizará:
# - Instalación de Chrome/Chromium
# - Creación de entorno virtual
# - Instalación de dependencias
# - Configuración de navegadores
# - Verificación del sistema
```

### Paso 3: Instalación Manual (Alternativa)

```bash
# Crear usuario para el sistema (opcional pero recomendado)
sudo useradd -m -s /bin/bash extractorov
sudo usermod -aG sudo extractorov
su - extractorov

# Clonar repositorio
git clone https://github.com/tu-usuario/ExtractorOV_Modular.git
cd ExtractorOV_Modular

# Crear entorno virtual
python3 -m venv venv
source venv/bin/activate

# Instalar dependencias
pip install --upgrade pip
pip install -r requirements.txt

# Instalar Chrome para Playwright
wget -q -O - https://dl.google.com/linux/linux_signing_key.pub | sudo apt-key add -
sudo sh -c 'echo "deb [arch=amd64] http://dl.google.com/linux/chrome/deb/ stable main" >> /etc/apt/sources.list.d/google.list'
sudo apt update
sudo apt install -y google-chrome-stable

# Instalar navegadores para Playwright
python -m playwright install chromium
python -m playwright install-deps
```

### Paso 4: Configuración de Servicios

```bash
# Crear directorio de logs
sudo mkdir -p /var/log/extractorov
sudo chown extractorov:extractorov /var/log/extractorov

# Configurar servicio systemd
sudo cp config/systemd/extractorov.service /etc/systemd/system/
sudo systemctl daemon-reload
sudo systemctl enable extractorov

# No iniciar aún - configurar primero las variables de entorno
```

## Configuración de Variables de Entorno

### Archivo de Configuración Principal

Crear y configurar el archivo `config/env/.env`:

```bash
# === CREDENCIALES DE OFICINAS VIRTUALES ===
# Credenciales para Afinia
OV_AFINIA_USERNAME=tu_usuario_afinia
OV_AFINIA_PASSWORD=tu_password_afinia
OV_AFINIA_URL=https://oficinavirtual.afinia.com.co

# Credenciales para Aire
OV_AIRE_USERNAME=tu_usuario_aire
OV_AIRE_PASSWORD=tu_password_aire
OV_AIRE_URL=https://oficinavirtual.aire.com.co

# === CONFIGURACIÓN DE BASE DE DATOS ===
# PostgreSQL RDS
RDS_HOST=tu-instancia.region.rds.amazonaws.com
RDS_PORT=5432
RDS_DATABASE=extractorov
RDS_USERNAME=db_user
RDS_PASSWORD=db_password_seguro
RDS_SSL_MODE=require

# Pool de conexiones
DB_POOL_SIZE=10
DB_MAX_OVERFLOW=20
DB_POOL_TIMEOUT=30
DB_POOL_RECYCLE=3600

# === CONFIGURACIÓN DE AMAZON S3 ===
AWS_ACCESS_KEY_ID=tu_access_key_id
AWS_SECRET_ACCESS_KEY=tu_secret_access_key
S3_BUCKET_NAME=tu-bucket-extractorov
S3_REGION=us-east-1
S3_ENDPOINT_URL=

# Configuración de uploads
S3_MAX_CONCURRENT_UPLOADS=5
S3_MULTIPART_THRESHOLD=100MB
S3_MAX_BANDWIDTH=50MB/s

# === CONFIGURACIÓN DE FILTROS ===
# Configuración de extracción
FILTER_DAYS_BACK=1
FILTER_STATE=Finalizado
DATE_FORMAT=%d/%m/%Y
MAX_RECORDS_PER_EXTRACTION=1000

# === CONFIGURACIÓN DE NAVEGADOR ===
# Playwright/Browser settings
HEADLESS_MODE=true
BROWSER_VIEWPORT_WIDTH=1920
BROWSER_VIEWPORT_HEIGHT=1080
USER_AGENT=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36

# Timeouts (en milisegundos)
PAGE_TIMEOUT=30000
NAVIGATION_TIMEOUT=60000
DOWNLOAD_TIMEOUT=120000
ELEMENT_TIMEOUT=10000

# === CONFIGURACIÓN DE LOGGING ===
LOG_LEVEL=INFO
LOG_FORMAT=professional
LOG_MAX_SIZE_MB=100
LOG_MAX_FILES=10
LOG_RETENTION_DAYS=30

# Directorios de logs
LOG_DIR=data/logs
ARCHIVE_LOG_DIR=data/logs/archived

# === CONFIGURACIÓN DE RENDIMIENTO ===
# Concurrencia y límites
MAX_CONCURRENT_EXTRACTIONS=2
MAX_CONCURRENT_DOWNLOADS=3
MAX_RETRY_ATTEMPTS=3
RETRY_DELAY_SECONDS=2

# Memoria
MEMORY_LIMIT_MB=2048
TEMP_DIR=data/temp

# === CONFIGURACIÓN DE MONITOREO ===
# Métricas y alertas
METRICS_ENABLED=true
METRICS_INTERVAL_SECONDS=60
HEALTH_CHECK_INTERVAL_SECONDS=300

# Alertas (opcional)
ALERT_EMAIL_ENABLED=false
ALERT_EMAIL_SMTP_SERVER=smtp.gmail.com
ALERT_EMAIL_SMTP_PORT=587
ALERT_EMAIL_USERNAME=alertas@tuempresa.com
ALERT_EMAIL_PASSWORD=password_email
ALERT_EMAIL_TO=admin@tuempresa.com

# === CONFIGURACIÓN DE DESARROLLO ===
# Solo para entornos de desarrollo/testing
DEBUG_MODE=false
TEST_MODE=false
MOCK_BROWSER=false
SKIP_DOWNLOADS=false
```

### Validación de Variables de Entorno

```bash
# Script para validar configuración
python scripts/validate_environment.py

# Output esperado:
# ✓ Credenciales de Afinia configuradas
# ✓ Credenciales de Aire configuradas  
# ✓ Configuración de base de datos válida
# ✓ Configuración de S3 válida
# ✓ Configuración de navegador válida
# ✓ Configuración de logging válida
```

## Configuración de Base de Datos

### Crear Esquema en PostgreSQL

```sql
-- Conectar como usuario administrador
-- psql -h tu-instancia.region.rds.amazonaws.com -U master_user -d postgres

-- Crear usuario y base de datos
CREATE USER extractorov_user WITH PASSWORD 'password_seguro';
CREATE DATABASE extractorov OWNER extractorov_user;

-- Conectar a la nueva base de datos
\c extractorov;

-- Crear esquema
CREATE SCHEMA IF NOT EXISTS data;
ALTER SCHEMA data OWNER TO extractorov_user;

-- Conceder permisos
GRANT ALL PRIVILEGES ON DATABASE extractorov TO extractorov_user;
GRANT ALL PRIVILEGES ON SCHEMA data TO extractorov_user;
GRANT ALL PRIVILEGES ON ALL TABLES IN SCHEMA data TO extractorov_user;
GRANT ALL PRIVILEGES ON ALL SEQUENCES IN SCHEMA data TO extractorov_user;

-- Crear tablas principales
CREATE TABLE data.ov_afinia (
    id SERIAL PRIMARY KEY,
    pqr_number VARCHAR(50) UNIQUE NOT NULL,
    extraction_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    pqr_data JSONB NOT NULL,
    status VARCHAR(20) DEFAULT 'processed',
    file_paths TEXT[],
    metadata JSONB DEFAULT '{}',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE data.ov_aire (
    id SERIAL PRIMARY KEY,
    pqr_number VARCHAR(50) UNIQUE NOT NULL,
    extraction_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    pqr_data JSONB NOT NULL,
    status VARCHAR(20) DEFAULT 'processed',
    file_paths TEXT[],
    metadata JSONB DEFAULT '{}',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Crear índices para optimización
CREATE INDEX idx_ov_afinia_pqr_number ON data.ov_afinia(pqr_number);
CREATE INDEX idx_ov_afinia_extraction_date ON data.ov_afinia(extraction_date);
CREATE INDEX idx_ov_afinia_status ON data.ov_afinia(status);

CREATE INDEX idx_ov_aire_pqr_number ON data.ov_aire(pqr_number);
CREATE INDEX idx_ov_aire_extraction_date ON data.ov_aire(extraction_date);
CREATE INDEX idx_ov_aire_status ON data.ov_aire(status);

-- Crear tabla de logs del sistema
CREATE TABLE data.system_logs (
    id SERIAL PRIMARY KEY,
    timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    service_name VARCHAR(50) NOT NULL,
    component VARCHAR(50) NOT NULL,
    log_level VARCHAR(10) NOT NULL,
    message TEXT NOT NULL,
    metadata JSONB DEFAULT '{}',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX idx_system_logs_timestamp ON data.system_logs(timestamp);
CREATE INDEX idx_system_logs_service ON data.system_logs(service_name);
CREATE INDEX idx_system_logs_level ON data.system_logs(log_level);
```

### Test de Conectividad a Base de Datos

```python
# Ejecutar test de conexión
python -c "
import os
import sys
sys.path.append('.')

from src.services.database_service import DatabaseService

try:
    db_service = DatabaseService()
    connected = db_service.test_connection()
    
    if connected:
        print('✓ Conexión a base de datos exitosa')
        
        # Test de operaciones básicas
        result = db_service.execute_query('SELECT version()')
        print(f'✓ PostgreSQL version: {result[0][0]}')
        
        # Verificar esquemas
        schemas = db_service.execute_query(
            'SELECT schema_name FROM information_schema.schemata WHERE schema_name = %s',
            ('data',)
        )
        if schemas:
            print('✓ Esquema \"data\" existe')
        else:
            print('⚠ Esquema \"data\" no encontrado')
            
    else:
        print('✗ Error de conexión a base de datos')
        
except Exception as e:
    print(f'✗ Error: {e}')
"
```

## Configuración de Amazon S3

### Crear Bucket y Políticas

```bash
# Usando AWS CLI (instalar si es necesario: pip install awscli)
aws configure set aws_access_key_id tu_access_key_id
aws configure set aws_secret_access_key tu_secret_access_key
aws configure set default.region us-east-1

# Crear bucket
aws s3 mb s3://tu-bucket-extractorov

# Crear estructura de directorios
aws s3api put-object --bucket tu-bucket-extractorov --key afinia/raw-data/
aws s3api put-object --bucket tu-bucket-extractorov --key afinia/processed/
aws s3api put-object --bucket tu-bucket-extractorov --key afinia/attachments/
aws s3api put-object --bucket tu-bucket-extractorov --key afinia/backups/

aws s3api put-object --bucket tu-bucket-extractorov --key aire/raw-data/
aws s3api put-object --bucket tu-bucket-extractorov --key aire/processed/
aws s3api put-object --bucket tu-bucket-extractorov --key aire/attachments/
aws s3api put-object --bucket tu-bucket-extractorov --key aire/backups/
```

### Política de Bucket S3

```json
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Sid": "ExtractorOVAccess",
      "Effect": "Allow",
      "Principal": {
        "AWS": "arn:aws:iam::ACCOUNT-ID:user/extractorov-user"
      },
      "Action": [
        "s3:GetObject",
        "s3:PutObject",
        "s3:DeleteObject",
        "s3:ListBucket"
      ],
      "Resource": [
        "arn:aws:s3:::tu-bucket-extractorov",
        "arn:aws:s3:::tu-bucket-extractorov/*"
      ]
    }
  ]
}
```

### Test de Conectividad a S3

```python
# Test de S3
python -c "
import os
import sys
sys.path.append('.')

from src.services.s3_uploader_service import S3UploaderService

try:
    s3_service = S3UploaderService()
    connected = s3_service.test_connection()
    
    if connected:
        print('✓ Conexión a S3 exitosa')
        
        # Test de operaciones básicas
        test_file = 'test_connection.txt'
        with open(test_file, 'w') as f:
            f.write('Test de conectividad S3')
            
        upload_success = s3_service.upload_file(test_file, 'test/test_connection.txt')
        
        if upload_success:
            print('✓ Upload de prueba exitoso')
            
            # Limpiar archivo de prueba
            s3_service.delete_file('test/test_connection.txt')
            os.remove(test_file)
            print('✓ Limpieza completada')
        else:
            print('⚠ Upload de prueba falló')
            
    else:
        print('✗ Error de conexión a S3')
        
except Exception as e:
    print(f'✗ Error: {e}')
"
```

## Configuración para Producción

### Configuración de Systemd (Ubuntu)

```ini
# /etc/systemd/system/extractorov.service
[Unit]
Description=ExtractorOV Modular Service
After=network.target postgresql.service
Wants=network.target

[Service]
Type=simple
User=extractorov
Group=extractorov
WorkingDirectory=/home/extractorov/ExtractorOV_Modular
Environment=PATH=/home/extractorov/ExtractorOV_Modular/venv/bin
ExecStart=/home/extractorov/ExtractorOV_Modular/venv/bin/python afinia_manager.py --headless
Restart=always
RestartSec=10
StandardOutput=append:/var/log/extractorov/service.log
StandardError=append:/var/log/extractorov/service.error.log

# Límites de recursos
LimitNOFILE=65536
LimitNPROC=4096
MemoryMax=2G
CPUQuota=200%

[Install]
WantedBy=multi-user.target
```

### Configuración de Cron para Ejecuciones Programadas

```bash
# Editar crontab
crontab -e

# Agregar tareas programadas
# Extracción diaria de Afinia a las 6:00 AM
0 6 * * * cd /home/extractorov/ExtractorOV_Modular && ./venv/bin/python afinia_manager.py --headless >> /var/log/extractorov/cron.log 2>&1

# Extracción diaria de Aire a las 6:30 AM  
30 6 * * * cd /home/extractorov/ExtractorOV_Modular && ./venv/bin/python aire_manager.py --headless >> /var/log/extractorov/cron.log 2>&1

# Limpieza de logs semanalmente los domingos a las 2:00 AM
0 2 * * 0 cd /home/extractorov/ExtractorOV_Modular && ./scripts/cleanup_logs.sh >> /var/log/extractorov/maintenance.log 2>&1

# Backup de base de datos diariamente a las 3:00 AM
0 3 * * * cd /home/extractorov/ExtractorOV_Modular && ./scripts/backup_database.sh >> /var/log/extractorov/backup.log 2>&1
```

### Configuración de Logging en Producción

```bash
# Configurar logrotate
sudo tee /etc/logrotate.d/extractorov > /dev/null << 'EOF'
/var/log/extractorov/*.log {
    daily
    rotate 30
    compress
    delaycompress
    missingok
    create 0644 extractorov extractorov
    postrotate
        systemctl reload extractorov || true
    endscript
}
EOF

# Test de configuración
sudo logrotate -d /etc/logrotate.d/extractorov
```

## Verificación Final del Sistema

### Script de Verificación Completa

```python
# Ejecutar verificación completa
python scripts/system_health_check.py

# Output esperado:
# === VERIFICACIÓN DEL SISTEMA EXTRACTOROV ===
# 
# ✓ Python 3.8+ instalado
# ✓ Dependencias principales instaladas
# ✓ Playwright y navegadores configurados
# ✓ Variables de entorno configuradas
# ✓ Conectividad a base de datos establecida
# ✓ Conectividad a S3 establecida
# ✓ Estructura de directorios creada
# ✓ Sistema de logging funcional
# ✓ Importaciones de código exitosas
# ✓ Configuración de servicios válida
# 
# === SISTEMA LISTO PARA PRODUCCIÓN ===
```

### Test de Ejecución Completa

```bash
# Test en modo dry-run (sin realizar extracciones reales)
python afinia_manager.py --headless --test-mode --dry-run

# Output esperado:
# [2025-10-10_06:00:00][afinia][manager][main][INFO] - Iniciando extractor Afinia en modo test
# [2025-10-10_06:00:01][afinia][manager][auth][INFO] - Simulando autenticación exitosa
# [2025-10-10_06:00:01][afinia][manager][filter][INFO] - Aplicando filtros de prueba
# [2025-10-10_06:00:02][afinia][manager][pagination][INFO] - Procesando paginación simulada
# [2025-10-10_06:00:03][afinia][manager][main][INFO] - Test completado exitosamente

# Si todo funciona correctamente, ejecutar test real con límite
python afinia_manager.py --headless --max-records 5

# Verificar resultados
ls -la data/downloads/afinia/
ls -la data/logs/current/
```

## Troubleshooting de Instalación

### Problemas Comunes

#### Error: "playwright executable not found"
```bash
# Solución
python -m playwright install chromium --with-deps

# En Ubuntu, también:
sudo apt install -y libnss3 libatk-bridge2.0-0 libdrm2 libxkbcommon0
```

#### Error: "Permission denied" en Ubuntu
```bash
# Solución
sudo chown -R $USER:$USER /path/to/ExtractorOV_Modular
chmod +x scripts/*.sh
```

#### Error de conexión a base de datos
```bash
# Verificar conectividad de red
telnet tu-instancia.region.rds.amazonaws.com 5432

# Verificar credenciales y configuración SSL
python -c "
import psycopg2
conn = psycopg2.connect(
    host='tu-host',
    database='tu-db',
    user='tu-user',
    password='tu-password',
    sslmode='require'
)
print('Conexión exitosa')
"
```

#### Error de memoria en ejecución
```bash
# Verificar uso de memoria
free -h
ps aux | grep python

# Configurar límites en systemd service
MemoryMax=4G
MemoryHigh=3G
```

### Logs de Diagnóstico

```bash
# Verificar logs del sistema
tail -f /var/log/extractorov/service.log

# Verificar logs de aplicación  
tail -f data/logs/current/afinia_manager.log

# Verificar logs del sistema operativo
sudo journalctl -u extractorov -f

# Verificar uso de recursos
htop
iostat -x 1
```

---

**Manual de Instalación y Configuración - ExtractorOV Modular**
*Versión: 2.0*
*Última actualización: Octubre 2025*