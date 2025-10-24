#!/bin/bash
# -*- coding: utf-8 -*-

# ============================================================================
# Instalador y Configurador para Ubuntu Server - ExtractorOV Modular  
# ============================================================================
#
# Este script realiza la instalación completa y configuración del
# ExtractorOV en Ubuntu Server, incluyendo:
# - Instalación de dependencias del sistema
# - Configuración de entorno Python
# - Instalación de navegadores
# - Configuración de servicios systemd
# - Configuración de permisos y directorios
#
# Uso:
#   curl -sSL https://raw.githubusercontent.com/tu-usuario/ExtractorOV_Modular/main/ubuntu_config/install_ubuntu.sh | bash
#   # O descargando el archivo:
#   wget https://raw.githubusercontent.com/tu-usuario/ExtractorOV_Modular/main/ubuntu_config/install_ubuntu.sh
#   chmod +x install_ubuntu.sh
#   ./install_ubuntu.sh
# ============================================================================

set -euo pipefail

# Configuración
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_NAME="ExtractorOV_Modular"
INSTALL_DIR="/home/$USER/$PROJECT_NAME"
SERVICE_USER="$USER"

# URLs del repositorio (ajustar según sea necesario)
REPO_URL="https://github.com/tu-usuario/ExtractorOV_Modular"
RAW_URL="https://raw.githubusercontent.com/tu-usuario/ExtractorOV_Modular/main"

# Colores para output
RED='\033[0;31m'
GREEN='\033[0;32m' 
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
PURPLE='\033[0;35m'
CYAN='\033[0;36m'
NC='\033[0m'

# Función de logging
log() {
    local level="$1"
    shift
    local message="$*"
    local timestamp=$(date '+%Y-%m-%d %H:%M:%S')
    
    case "$level" in
        "INFO")    echo -e "${BLUE}[$timestamp] INFO:${NC} $message" ;;
        "WARN")    echo -e "${YELLOW}[$timestamp] WARN:${NC} $message" ;;
        "ERROR")   echo -e "${RED}[$timestamp] ERROR:${NC} $message" ;;
        "SUCCESS") echo -e "${GREEN}[$timestamp] SUCCESS:${NC} $message" ;;
        "STEP")    echo -e "${PURPLE}[$timestamp] STEP:${NC} $message" ;;
        *) echo "[$timestamp] $level: $message" ;;
    esac
}

# Función para mostrar banner
show_banner() {
    echo -e "${CYAN}"
    cat << 'EOF'
  ╔══════════════════════════════════════════════════════╗
  ║                                                      ║
  ║        ExtractorOV Modular - Ubuntu Installer       ║
  ║                                                      ║
  ║     Instalador completo para Ubuntu Server          ║
  ║                                                      ║
  ╚══════════════════════════════════════════════════════╝
EOF
    echo -e "${NC}"
}

# Función para detectar información del sistema
detect_system_info() {
    log "INFO" "🔍 Detectando información del sistema..."
    
    local os_info=$(lsb_release -d 2>/dev/null | cut -f2- || echo "Desconocido")
    local kernel_info=$(uname -r)
    local arch_info=$(uname -m)
    local memory_info=$(free -h | awk '/^Mem:/ {print $2}')
    local disk_info=$(df -h / | awk 'NR==2 {print $4}')
    
    echo "═══════════════════════════════════════════════════"
    echo "📋 INFORMACIÓN DEL SISTEMA"
    echo "═══════════════════════════════════════════════════"
    echo "OS: $os_info"
    echo "Kernel: $kernel_info"
    echo "Arquitectura: $arch_info"
    echo "Memoria: $memory_info"
    echo "Espacio libre: $disk_info"
    echo "Usuario: $USER"
    echo "Directorio de instalación: $INSTALL_DIR"
    echo "═══════════════════════════════════════════════════"
}

# Función para verificar prerrequisitos
check_prerequisites() {
    log "INFO" "✅ Verificando prerrequisitos..."
    
    # Verificar que no se esté ejecutando como root
    if [[ $EUID -eq 0 ]]; then
        log "ERROR" "❌ Este script NO debe ejecutarse como root"
        log "INFO" "Ejecutar como usuario normal con sudo disponible"
        exit 1
    fi
    
    # Verificar acceso a sudo
    if ! sudo -n true 2>/dev/null; then
        log "WARN" "⚠️ Se requieren privilegios sudo. Se solicitará contraseña."
    fi
    
    # Verificar conexión a internet
    if ! curl -s --max-time 5 http://google.com > /dev/null; then
        log "ERROR" "❌ Sin conexión a internet"
        exit 1
    fi
    
    log "SUCCESS" "✅ Prerrequisitos OK"
}

# Función para actualizar sistema
update_system() {
    log "STEP" "🔄 Actualizando sistema..."
    
    sudo apt update
    sudo apt upgrade -y
    
    log "SUCCESS" "✅ Sistema actualizado"
}

# Función para instalar dependencias del sistema
install_system_dependencies() {
    log "STEP" "📦 Instalando dependencias del sistema..."
    
    local packages=(
        # Python y herramientas básicas
        python3
        python3-pip
        python3-venv
        python3-dev
        
        # Herramientas de compilación
        build-essential
        curl
        wget
        git
        
        # XVFB y herramientas gráficas para headless
        xvfb
        xauth
        
        # Dependencias para navegadores
        libnss3
        libatk-bridge2.0-0
        libdrm2
        libxkbcommon0
        libxcomposite1
        libxdamage1
        libxrandr2
        libgbm1
        libxss1
        libasound2
        
        # Herramientas adicionales
        htop
        nano
        vim
        unzip
        software-properties-common
        
        # Dependencias de certificados
        ca-certificates
        
        # Herramientas de red
        net-tools
        
        # Para manejar procesos
        psmisc
        
        # Para cron jobs
        cron
    )
    
    log "INFO" "Instalando paquetes: ${packages[*]}"
    sudo apt install -y "${packages[@]}"
    
    log "SUCCESS" "✅ Dependencias del sistema instaladas"
}

# Función para instalar Chrome
install_chrome() {
    log "STEP" "🌐 Instalando Google Chrome..."
    
    # Descargar e instalar Chrome
    if ! command -v google-chrome-stable &> /dev/null; then
        log "INFO" "Descargando Google Chrome..."
        
        # Agregar clave GPG y repositorio
        curl -fsSL https://dl.google.com/linux/linux_signing_key.pub | sudo gpg --dearmor -o /usr/share/keyrings/google-chrome.gpg
        echo "deb [arch=amd64 signed-by=/usr/share/keyrings/google-chrome.gpg] http://dl.google.com/linux/chrome/deb/ stable main" | sudo tee /etc/apt/sources.list.d/google-chrome.list
        
        sudo apt update
        sudo apt install -y google-chrome-stable
        
        log "SUCCESS" "✅ Google Chrome instalado"
    else
        log "INFO" "✅ Google Chrome ya está instalado"
    fi
    
    # Verificar instalación
    if google-chrome-stable --version; then
        log "SUCCESS" "✅ Chrome verificado correctamente"
    else
        log "WARN" "⚠️ Chrome instalado pero con advertencias"
    fi
}

# Función para clonar o actualizar repositorio
setup_project() {
    log "STEP" "📁 Configurando proyecto..."
    
    if [[ -d "$INSTALL_DIR" ]]; then
        log "INFO" "Directorio existe, actualizando..."
        cd "$INSTALL_DIR"
        
        if [[ -d ".git" ]]; then
            git pull origin main
        else
            log "WARN" "Directorio existe pero no es un repositorio git"
            log "INFO" "Respaldando directorio existente..."
            mv "$INSTALL_DIR" "${INSTALL_DIR}_backup_$(date +%Y%m%d_%H%M%S)"
            git clone "$REPO_URL" "$INSTALL_DIR"
        fi
    else
        log "INFO" "Clonando repositorio..."
        git clone "$REPO_URL" "$INSTALL_DIR"
    fi
    
    cd "$INSTALL_DIR"
    
    # Hacer scripts ejecutables
    find . -name "*.sh" -type f -exec chmod +x {} \;
    
    log "SUCCESS" "✅ Proyecto configurado en $INSTALL_DIR"
}

# Función para configurar entorno Python
setup_python_environment() {
    log "STEP" "🐍 Configurando entorno Python..."
    
    cd "$INSTALL_DIR"
    
    # Crear entorno virtual
    if [[ ! -d "venv" ]]; then
        log "INFO" "Creando entorno virtual..."
        python3 -m venv venv
    fi
    
    # Activar entorno virtual
    source venv/bin/activate
    
    # Actualizar pip
    log "INFO" "Actualizando pip..."
    pip install --upgrade pip
    
    # Instalar requirements
    if [[ -f "requirements.txt" ]]; then
        log "INFO" "Instalando dependencias Python..."
        pip install -r requirements.txt
    else
        log "WARN" "requirements.txt no encontrado, instalando dependencias básicas..."
        pip install playwright requests python-dotenv selenium beautifulsoup4 lxml pandas openpyxl
    fi
    
    # Instalar navegadores de Playwright
    log "INFO" "Instalando navegadores de Playwright..."
    playwright install chromium
    
    log "SUCCESS" "✅ Entorno Python configurado"
}

# Función para crear directorios necesarios
create_directories() {
    log "STEP" "📁 Creando estructura de directorios..."
    
    cd "$INSTALL_DIR"
    
    local dirs=(
        "downloads"
        "processed"
        "data/logs"
        "pids"
        "screenshots"
        "temp"
        "backups"
        "config"
    )
    
    for dir in "${dirs[@]}"; do
        if [[ ! -d "$dir" ]]; then
            log "INFO" "Creando directorio: $dir"
            mkdir -p "$dir"
        fi
    done
    
    # Configurar permisos
    chmod 755 .
    chmod -R 755 downloads processed logs screenshots temp backups config
    chmod -R 644 pids
    
    log "SUCCESS" "✅ Directorios creados"
}

# Función para configurar variables de entorno
setup_environment_file() {
    log "STEP" "⚙️ Configurando archivo de entorno..."
    
    cd "$INSTALL_DIR"
    
    if [[ ! -f ".env" ]]; then
        log "INFO" "Creando archivo .env..."
        cat > .env << EOF
# Configuración para Ubuntu Server
UBUNTU_SERVER=true
HEADLESS=true
ENVIRONMENT=production

# Display para XVFB
DISPLAY=:99
XVFB_WHD=1366x768x24

# Rutas del proyecto
PROJECT_ROOT=$INSTALL_DIR
DOWNLOADS_PATH=$INSTALL_DIR/downloads
PROCESSED_PATH=$INSTALL_DIR/processed
LOGS_PATH=$INSTALL_DIR/logs
SCREENSHOTS_PATH=$INSTALL_DIR/screenshots

# Configuración de navegador
BROWSER_TIMEOUT=60000
BROWSER_SLOWMO=100
BROWSER_VIEWPORT_WIDTH=1366
BROWSER_VIEWPORT_HEIGHT=768

# Configuración de logging
LOG_LEVEL=INFO
LOG_TO_FILE=true
LOG_MAX_SIZE=100MB

# Configuración de red
HTTP_TIMEOUT=30
RETRY_ATTEMPTS=3
RETRY_DELAY=5

# Configuración específica de extractores
AIRE_ENABLED=true
AFINIA_ENABLED=true

# Configuración de horarios (cron-like)
SCHEDULE_ENABLED=true
SCHEDULE_HOUR=09
SCHEDULE_MINUTE=00

EOF
        log "SUCCESS" "✅ Archivo .env creado"
    else
        log "INFO" "✅ Archivo .env ya existe"
    fi
}

# Función para instalar servicios systemd
install_systemd_services() {
    log "STEP" "⚙️ Instalando servicios systemd..."
    
    cd "$INSTALL_DIR"
    
    # Copiar archivos de servicio
    local services=("extractorov-aire.service" "extractorov-afinia.service")
    
    for service in "${services[@]}"; do
        if [[ -f "ubuntu_config/$service" ]]; then
            log "INFO" "Instalando servicio: $service"
            
            # Actualizar rutas en el archivo de servicio
            sed "s|/home/ubuntu|$HOME|g" "ubuntu_config/$service" > "/tmp/$service"
            sed -i "s|User=ubuntu|User=$USER|g" "/tmp/$service"
            sed -i "s|Group=ubuntu|Group=$USER|g" "/tmp/$service"
            
            sudo mv "/tmp/$service" "/etc/systemd/system/"
            sudo systemctl daemon-reload
            sudo systemctl enable "$service"
            
            log "SUCCESS" "✅ Servicio $service instalado y habilitado"
        else
            log "WARN" "⚠️ Archivo de servicio no encontrado: $service"
        fi
    done
}

# Función para configurar cron jobs
setup_cron_jobs() {
    log "STEP" "⏰ Configurando cron jobs..."
    
    # Crear script de cron
    cat > "/tmp/extractorov_cron.sh" << EOF
#!/bin/bash
# Cron job para ExtractorOV
cd "$INSTALL_DIR"
source ubuntu_config/run_ubuntu.sh status >> logs/cron.log 2>&1

# Verificar y reiniciar servicios si es necesario
systemctl --user is-active --quiet extractorov-aire || systemctl --user start extractorov-aire
systemctl --user is-active --quiet extractorov-afinia || systemctl --user start extractorov-afinia
EOF
    
    chmod +x "/tmp/extractorov_cron.sh"
    mv "/tmp/extractorov_cron.sh" "$INSTALL_DIR/scripts/cron_check.sh"
    
    # Agregar al crontab del usuario
    local cron_job="*/15 * * * * $INSTALL_DIR/scripts/cron_check.sh"
    
    if ! crontab -l 2>/dev/null | grep -q "extractorov_cron"; then
        log "INFO" "Agregando cron job..."
        (crontab -l 2>/dev/null; echo "$cron_job") | crontab -
        log "SUCCESS" "✅ Cron job configurado"
    else
        log "INFO" "✅ Cron job ya existe"
    fi
}

# Función para ejecutar tests
run_tests() {
    log "STEP" "🧪 Ejecutando tests de verificación..."
    
    cd "$INSTALL_DIR"
    source venv/bin/activate
    
    # Test de configuración
    log "INFO" "Probando configuración de entorno..."
    if python3 -c "from ubuntu_config.environment_detector import *; print_system_info()"; then
        log "SUCCESS" "✅ Test de entorno OK"
    else
        log "ERROR" "❌ Error en test de entorno"
    fi
    
    # Test de navegador
    log "INFO" "Probando configuración de navegador..."
    if python3 -c "from ubuntu_config.ubuntu_browser import print_browser_info; print_browser_info()"; then
        log "SUCCESS" "✅ Test de navegador OK"
    else
        log "ERROR" "❌ Error en test de navegador"  
    fi
    
    # Test de XVFB
    log "INFO" "Probando XVFB..."
    if xvfb-run -a -s "-screen 0 1366x768x24" python3 -c "print('XVFB funciona correctamente')"; then
        log "SUCCESS" "✅ Test de XVFB OK"
    else
        log "ERROR" "❌ Error en test de XVFB"
    fi
}

# Función para mostrar resumen final
show_final_summary() {
    log "SUCCESS" "🎉 Instalación completada exitosamente!"
    
    echo ""
    echo "═══════════════════════════════════════════════════"
    echo "📋 RESUMEN DE INSTALACIÓN"
    echo "═══════════════════════════════════════════════════"
    echo "📁 Directorio: $INSTALL_DIR"
    echo "🐍 Python virtual env: $INSTALL_DIR/venv"
    echo "⚙️ Servicios systemd: extractorov-aire, extractorov-afinia"
    echo "📋 Logs: $INSTALL_DIR/logs"
    echo "💾 Descargas: $INSTALL_DIR/downloads"
    echo ""
    
    echo "🚀 COMANDOS ÚTILES:"
    echo "═══════════════════════════════════════════════════"
    echo "# Ir al directorio del proyecto"
    echo "cd $INSTALL_DIR"
    echo ""
    echo "# Ejecutar extractores manualmente"
    echo "ubuntu_config/run_ubuntu.sh aire"
    echo "ubuntu_config/run_ubuntu.sh afinia"
    echo "ubuntu_config/run_ubuntu.sh all"
    echo ""
    echo "# Ver estado de servicios"
    echo "sudo systemctl status extractorov-aire"
    echo "sudo systemctl status extractorov-afinia"
    echo ""
    echo "# Ver logs"
    echo "ubuntu_config/run_ubuntu.sh logs"
    echo "journalctl -u extractorov-aire -f"
    echo ""
    echo "# Iniciar/detener servicios"
    echo "sudo systemctl start extractorov-aire"
    echo "sudo systemctl stop extractorov-aire"
    echo "═══════════════════════════════════════════════════"
    
    echo ""
    log "INFO" "📖 Para más información, consultar el README.md"
    log "INFO" "🐛 Reportar problemas en: $REPO_URL/issues"
}

# Función para limpiar en caso de error
cleanup_on_error() {
    log "ERROR" "💥 Error durante la instalación"
    log "INFO" "🧹 Ejecutando limpieza..."
    
    # Detener servicios si están corriendo
    sudo systemctl stop extractorov-aire 2>/dev/null || true
    sudo systemctl stop extractorov-afinia 2>/dev/null || true
    
    # Remover servicios si fueron instalados
    sudo systemctl disable extractorov-aire 2>/dev/null || true
    sudo systemctl disable extractorov-afinia 2>/dev/null || true
    sudo rm -f /etc/systemd/system/extractorov-*.service
    sudo systemctl daemon-reload
    
    log "INFO" "Limpieza completada. Revise los logs para más detalles."
    exit 1
}

# Función principal
main() {
    # Configurar trap para cleanup en errores
    trap cleanup_on_error ERR
    
    show_banner
    detect_system_info
    
    log "INFO" "🚀 Iniciando instalación de ExtractorOV para Ubuntu Server..."
    
    check_prerequisites
    update_system
    install_system_dependencies
    install_chrome
    setup_project
    setup_python_environment
    create_directories
    setup_environment_file
    install_systemd_services
    setup_cron_jobs
    run_tests
    
    show_final_summary
    
    log "SUCCESS" "🎉 ¡Instalación completada exitosamente!"
    log "INFO" "🔄 Es recomendable reiniciar el sistema para asegurar que todos los servicios inicien correctamente."
}

# Verificar argumentos
if [[ $# -gt 0 ]]; then
    case "$1" in
        "--help"|"-h")
            echo "Instalador de ExtractorOV para Ubuntu Server"
            echo ""
            echo "Uso: $0 [opciones]"
            echo ""
            echo "Opciones:"
            echo "  --help, -h     Mostrar esta ayuda"
            echo "  --test         Ejecutar solo tests"
            echo ""
            exit 0
            ;;
        "--test")
            log "INFO" "🧪 Ejecutando solo tests..."
            run_tests
            exit 0
            ;;
        *)
            log "WARN" "Opción desconocida: $1"
            ;;
    esac
fi

# Ejecutar instalación
main