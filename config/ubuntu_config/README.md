# ExtractorOV - Configuración para Ubuntu Server

## Descripción

Esta configuración proporciona soporte completo para ejecutar ExtractorOV_Modular en Ubuntu Server con optimizaciones específicas para entornos de servidor, modo headless y servicios systemd automatizados.

## Instalación

### Instalación Automatizada (Recomendada)

```bash
# Desde el directorio raíz del proyecto
chmod +x scripts/ubuntu_setup.sh
./scripts/ubuntu_setup.sh
```

### Instalación Manual

```bash
# 1. Instalar dependencias del sistema
sudo apt update && sudo apt upgrade -y
sudo apt install -y python3 python3-pip python3-venv python3-dev
sudo apt install -y build-essential curl wget git
sudo apt install -y xvfb xauth htop nano vim unzip ca-certificates

# 2. Instalar Google Chrome
wget -q -O - https://dl.google.com/linux/linux_signing_key.pub | sudo apt-key add -
echo "deb [arch=amd64] http://dl.google.com/linux/chrome/deb/ stable main" | sudo tee /etc/apt/sources.list.d/google.list
sudo apt update && sudo apt install -y google-chrome-stable

# 3. Configurar entorno Python
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
playwright install chromium

# 4. Configurar servicios systemd
sudo cp config/ubuntu_config/extractorov-afinia.service /etc/systemd/system/
sudo cp config/ubuntu_config/extractorov-aire.service /etc/systemd/system/
sudo systemctl daemon-reload
sudo systemctl enable extractorov-afinia extractorov-aire
```

## Requisitos del Sistema

### Mínimos
- **OS**: Ubuntu Server 18.04 LTS o superior
- **RAM**: 2GB mínimo
- **CPU**: 1 core mínimo
- **Disco**: 5GB libres
- **Red**: Conexión estable a internet

### Recomendados
- **OS**: Ubuntu Server 20.04 LTS o 22.04 LTS
- **RAM**: 4GB o más
- **CPU**: 2 cores o más
- **Disco**: 10GB libres
- **Red**: Banda ancha estable

## Componentes

### Scripts de Configuración

#### `install_ubuntu.sh`
Script de instalación automatizada que configura:
- Dependencias del sistema
- Google Chrome y dependencias gráficas
- Entorno virtual Python
- Servicios systemd
- Variables de entorno para Ubuntu

#### `run_ubuntu.sh`
Script principal de ejecución con comandos:
```bash
# Configuración inicial
./run_ubuntu.sh setup

# Ejecutar extractores
./run_ubuntu.sh afinia
./run_ubuntu.sh aire
./run_ubuntu.sh all

# Monitoreo
./run_ubuntu.sh status
./run_ubuntu.sh logs
./run_ubuntu.sh stop
```

### Módulos Python

#### `environment_detector.py`
Detecta automáticamente el entorno de ejecución:
- Identificación de Ubuntu Server
- Detección de capacidades gráficas
- Configuración automática de variables

#### `ubuntu_browser.py`
Configuración optimizada de navegador para Ubuntu:
- Argumentos de Chrome para modo headless
- Configuración de XVFB
- Optimizaciones de rendimiento

#### `ubuntu_paths.py`
Gestor de rutas multiplataforma:
- Rutas específicas de Ubuntu
- Creación automática de directorios
- Manejo de permisos

### Servicios Systemd

#### `extractorov-afinia.service`
Servicio para el extractor de Afinia:
- Auto-reinicio en fallos
- Variables de entorno configuradas
- Logging automático

#### `extractorov-aire.service`
Servicio para el extractor de Aire:
- Configuración similar a Afinia
- Ejecución independiente
- Monitoreo de estado

## Configuración

### Variables de Entorno para Ubuntu

El sistema configura automáticamente:

```bash
# Display virtual
DISPLAY=:99
XVFB_WHD=1920x1080x24

# Configuración de servidor
UBUNTU_SERVER=true
HEADLESS_MODE=true

# Rutas específicas
CHROME_BINARY_PATH=/usr/bin/google-chrome-stable
DOWNLOAD_PATH=./data/downloads
LOG_PATH=./data/logs
```

### Modo Headless

Características del modo sin interfaz gráfica:
- XVFB para display virtual
- Chrome optimizado para servidor
- Sin dependencias gráficas del usuario
- Timeouts extendidos para conexiones lentas

### Estructura de Directorios

```
/home/usuario/ExtractorOV_Modular/
├── config/ubuntu_config/       # Configuraciones Ubuntu
│   ├── environment_detector.py # Detector de entorno
│   ├── ubuntu_paths.py         # Gestor de rutas
│   ├── ubuntu_browser.py       # Configuración navegador
│   ├── install_ubuntu.sh       # Instalador
│   ├── run_ubuntu.sh          # Script principal
│   ├── *.service              # Servicios systemd
│   └── README.md              # Esta documentación
├── data/                      # Datos del sistema
│   ├── downloads/             # Archivos descargados
│   ├── logs/                  # Logs del sistema
│   ├── metrics/               # Métricas de rendimiento
│   └── temp/                  # Archivos temporales
├── venv/                      # Entorno virtual Python
└── config/env/.env            # Configuración principal
```

## Operación

### Gestión de Servicios

```bash
# Ver estado
sudo systemctl status extractorov-afinia
sudo systemctl status extractorov-aire

# Iniciar/detener
sudo systemctl start extractorov-afinia
sudo systemctl stop extractorov-afinia

# Habilitar auto-inicio
sudo systemctl enable extractorov-afinia

# Ver logs del servicio
journalctl -u extractorov-afinia -f
journalctl -u extractorov-aire --since "1 hour ago"
```

### Monitoreo

#### Logs de Aplicación
```bash
# Logs en tiempo real
tail -f data/logs/current/afinia_*.log
tail -f data/logs/current/aire_*.log

# Buscar errores
grep -i error data/logs/current/*.log

# Logs de fecha específica
ls data/logs/archived/2024-01-15/
```

#### Recursos del Sistema
```bash
# Uso de CPU y memoria
htop

# Espacio en disco
df -h

# Procesos del extractor
ps aux | grep python3
ps aux | grep chrome
ps aux | grep xvfb
```

### Automatización

#### Cron Jobs
```bash
# Editar tareas programadas
crontab -e

# Ejemplos de programación
# Ejecutar Afinia diario a las 9:00 AM
0 9 * * * /home/usuario/ExtractorOV_Modular/config/ubuntu_config/run_ubuntu.sh afinia

# Ejecutar Aire de lunes a viernes a las 10:00 AM
0 10 * * 1-5 /home/usuario/ExtractorOV_Modular/config/ubuntu_config/run_ubuntu.sh aire

# Verificar estado cada hora
0 * * * * /home/usuario/ExtractorOV_Modular/config/ubuntu_config/run_ubuntu.sh status
```

## Troubleshooting

### Problemas Comunes

#### Error de XVFB
```bash
# Verificar proceso XVFB
ps aux | grep Xvfb

# Reiniciar XVFB
pkill Xvfb
Xvfb :99 -ac -screen 0 1920x1080x24 &
export DISPLAY=:99
```

#### Error de Chrome
```bash
# Verificar instalación
google-chrome-stable --version

# Verificar dependencias
ldd /usr/bin/google-chrome-stable

# Reinstalar si es necesario
sudo apt remove --purge google-chrome-stable
sudo apt install google-chrome-stable
```

#### Error de Permisos
```bash
# Verificar propietario
ls -la /home/usuario/ExtractorOV_Modular

# Corregir permisos
sudo chown -R usuario:usuario /home/usuario/ExtractorOV_Modular
chmod +x config/ubuntu_config/*.sh
```

#### Error de Python/Dependencias
```bash
# Verificar entorno virtual
source venv/bin/activate
python3 --version
pip list

# Reinstalar dependencias
pip install -r requirements.txt --force-reinstall
playwright install chromium --with-deps
```

### Comandos de Diagnóstico

```bash
# Test completo del sistema
config/ubuntu_config/install_ubuntu.sh --test

# Información del entorno
python3 -c "from config.ubuntu_config.environment_detector import get_system_info; print(get_system_info())"

# Test de conectividad
curl -I https://www.google.com
ping -c 4 8.8.8.8

# Verificar configuración de Chrome
google-chrome-stable --headless --disable-gpu --dump-dom https://www.google.com
```

## Mantenimiento

### Actualización del Sistema

```bash
# Detener servicios
sudo systemctl stop extractorov-afinia extractorov-aire

# Actualizar sistema
sudo apt update && sudo apt upgrade -y

# Actualizar código
git pull origin main

# Actualizar dependencias Python
source venv/bin/activate
pip install -r requirements.txt --upgrade

# Reiniciar servicios
sudo systemctl start extractorov-afinia extractorov-aire
```

### Limpieza de Archivos

```bash
# Limpiar logs antiguos (más de 30 días)
find data/logs/archived/ -name "*.log" -mtime +30 -delete

# Limpiar archivos temporales
rm -rf data/temp/*

# Limpiar screenshots antiguos
find data/downloads/*/screenshots/ -name "*.png" -mtime +7 -delete

# Limpiar cache del navegador
rm -rf ~/.cache/google-chrome/
rm -rf data/temp/.playwright/
```

### Respaldo y Restauración

```bash
# Crear respaldo completo
tar -czf extractorov_backup_$(date +%Y%m%d).tar.gz \
    --exclude='venv' \
    --exclude='data/logs' \
    --exclude='data/temp' \
    --exclude='__pycache__' \
    /home/usuario/ExtractorOV_Modular/

# Respaldo solo configuraciones
tar -czf config_backup_$(date +%Y%m%d).tar.gz \
    config/ \
    requirements.txt \
    *.py

# Restaurar respaldo
tar -xzf extractorov_backup_YYYYMMDD.tar.gz -C /home/usuario/
```

## Configuración Avanzada

### Optimización de Rendimiento

```bash
# En config/env/.env, ajustar:
MAX_MEMORY_MB=2048
MAX_CONCURRENT_PAGES=2
THREAD_POOL_SIZE=4
GARBAGE_COLLECTION_THRESHOLD=100

# Argumentos adicionales de Chrome
CHROME_ARGS="--no-sandbox --disable-dev-shm-usage --disable-gpu --memory-pressure-off"
```

### Configuración de Red

```bash
# Para servidores con proxy
export HTTP_PROXY=http://proxy.company.com:8080
export HTTPS_PROXY=http://proxy.company.com:8080
export NO_PROXY=localhost,127.0.0.1,.local

# Configuración de firewall
sudo ufw enable
sudo ufw allow ssh
sudo ufw allow from 192.168.1.0/24
```

### Configuración de Seguridad

```bash
# Permisos restrictivos para archivos sensibles
chmod 600 config/env/.env
chmod 700 config/ubuntu_config/

# Configurar logrotate
sudo tee /etc/logrotate.d/extractorov << EOF
/home/usuario/ExtractorOV_Modular/data/logs/current/*.log {
    daily
    missingok
    rotate 30
    compress
    delaycompress
    notifempty
    copytruncate
}
EOF
```

## Soporte

### Información para Reportes

Antes de reportar problemas, recopilar:

```bash
# Información del sistema
uname -a > system_info.txt
df -h >> system_info.txt
free -h >> system_info.txt
google-chrome-stable --version >> system_info.txt

# Logs recientes
tail -500 data/logs/current/*.log > recent_logs.txt

# Estado de servicios
systemctl status extractorov-* > services_status.txt

# Variables de entorno
env | grep -E "(DISPLAY|UBUNTU|HEADLESS|CHROME)" > env_vars.txt
```

### Recursos Adicionales

- **Documentación Principal**: README.md en raíz del proyecto
- **Configuración de Variables**: config/env/README.md
- **Scripts de Instalación**: scripts/ubuntu_setup.sh
- **Logs del Sistema**: journalctl -u extractorov-*

## Notas Importantes

### Mejores Prácticas

1. **Nunca ejecutar como root**: Usar usuario normal con sudo
2. **Monitorear recursos**: CPU, memoria y espacio en disco
3. **Configurar alertas**: Para fallos de servicios
4. **Mantener actualizaciones**: Sistema y dependencias
5. **Hacer respaldos regulares**: Configuraciones y datos

### Limitaciones

- Requiere entorno Ubuntu Server con acceso a internet
- Chrome puede consumir memoria significativa
- XVFB necesario para operaciones gráficas
- Algunas páginas web pueden no funcionar correctamente en modo headless

### Próximas Mejoras

- Dashboard web para monitoreo remoto
- API REST para control programático
- Contenedores Docker para despliegue simplificado
- Integración con sistemas de monitoreo (Prometheus, Grafana)
- Notificaciones automáticas por email/Slack

---

**ExtractorOV Ubuntu Configuration** - Configuración profesional optimizada para Ubuntu Server con soporte completo para ejecución automatizada y monitoreo de servicios.