#!/bin/bash

# ====================================================
# Script de Instalación para ExtractorOV_Modular
# Compatible con Ubuntu Server 20.04/22.04/24.04
# ====================================================

set -e  # Salir si hay algún error

# Colores para output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Funciones de logging
log_info() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

log_success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1"
}

log_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

log_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# Verificar si se ejecuta como root
check_root() {
    if [[ $EUID -eq 0 ]]; then
        log_error "No ejecutar este script como root. Usar sudo solo cuando sea necesario."
        exit 1
    fi
}

# Verificar versión de Ubuntu
check_ubuntu_version() {
    log_info "Verificando versión de Ubuntu..."
    
    if ! command -v lsb_release &> /dev/null; then
        log_error "lsb_release no encontrado. ¿Estás en Ubuntu?"
        exit 1
    fi
    
    UBUNTU_VERSION=$(lsb_release -rs)
    UBUNTU_CODENAME=$(lsb_release -cs)
    
    log_info "Ubuntu ${UBUNTU_VERSION} (${UBUNTU_CODENAME}) detectado"
    
    # Verificar versión soportada
    case $UBUNTU_VERSION in
        20.04|22.04|24.04)
            log_success "Versión de Ubuntu soportada"
            ;;
        *)
            log_warning "Versión de Ubuntu no probada. Continuando..."
            ;;
    esac
}

# Actualizar sistema
update_system() {
    log_info "Actualizando lista de paquetes..."
    sudo apt update
    
    log_info "Actualizando paquetes del sistema..."
    sudo apt upgrade -y
}

# Instalar dependencias del sistema
install_system_dependencies() {
    log_info "Instalando dependencias del sistema..."
    
    sudo apt install -y \
        python3 \
        python3-pip \
        python3-venv \
        curl \
        wget \
        git \
        unzip \
        xvfb \
        libnss3-dev \
        libatk-bridge2.0-dev \
        libdrm-dev \
        libxkbcommon-dev \
        libgbm-dev \
        libasound2-dev \
        libxrandr2 \
        libxss1 \
        libgconf-2-4 \
        libxcomposite1 \
        libxcursor1 \
        libxdamage1 \
        libxi6 \
        libxtst6 \
        libnss3 \
        libcups2 \
        libxrandr2 \
        libasound2 \
        libpangocairo-1.0-0 \
        libatk1.0-0 \
        libcairo-gobject2 \
        libgtk-3-0 \
        libgdk-pixbuf2.0-0
    
    log_success "Dependencias del sistema instaladas"
}

# Configurar Python y entorno virtual
setup_python_environment() {
    log_info "Configurando entorno virtual de Python..."
    
    # Crear directorio del proyecto si no existe
    PROJECT_DIR="$HOME/ExtractorOV_Modular"
    
    if [ ! -d "$PROJECT_DIR" ]; then
        log_info "Creando directorio del proyecto en $PROJECT_DIR"
        mkdir -p "$PROJECT_DIR"
        cd "$PROJECT_DIR"
    else
        log_info "Usando directorio existente $PROJECT_DIR"
        cd "$PROJECT_DIR"
    fi
    
    # Crear entorno virtual
    if [ ! -d "venv" ]; then
        log_info "Creando entorno virtual..."
        python3 -m venv venv
    else
        log_info "Entorno virtual ya existe"
    fi
    
    # Activar entorno virtual
    source venv/bin/activate
    
    # Actualizar pip
    log_info "Actualizando pip..."
    pip install --upgrade pip
    
    log_success "Entorno virtual configurado"
}

# Instalar dependencias de Python
install_python_dependencies() {
    log_info "Instalando dependencias de Python..."
    
    # Asegurar que estamos en el entorno virtual
    source venv/bin/activate
    
    # Instalar playwright y otras dependencias
    pip install \
        playwright \
        python-dotenv \
        asyncio \
        pathlib \
        json \
        datetime \
        typing \
        logging \
        re \
        os \
        sys
    
    log_success "Dependencias de Python instaladas"
}

# Instalar navegadores de Playwright
install_playwright_browsers() {
    log_info "Instalando navegadores de Playwright..."
    
    # Asegurar que estamos en el entorno virtual
    source venv/bin/activate
    
    # Instalar navegadores
    playwright install chromium
    playwright install-deps chromium
    
    log_success "Navegadores de Playwright instalados"
}

# Crear directorios necesarios
create_directories() {
    log_info "Creando directorios necesarios..."
    
    # Nueva estructura de directorios
    mkdir -p "$HOME/ExtractorOV_Modular/data/downloads/afinia/oficina_virtual"
    mkdir -p "$HOME/ExtractorOV_Modular/data/downloads/aire/oficina_virtual"
    mkdir -p "$HOME/ExtractorOV_Modular/data/logs"
    mkdir -p "$HOME/ExtractorOV_Modular/data/metrics"
    mkdir -p "$HOME/ExtractorOV_Modular/data/backup"
    mkdir -p "$HOME/ExtractorOV_Modular/config/env"
    mkdir -p "$HOME/ExtractorOV_Modular/config/ubuntu_config"
    
    log_success "Directorios creados con nueva estructura"
}

# Configurar variables de entorno para headless
setup_environment_variables() {
    log_info "Configurando variables de entorno..."
    
    # Crear archivo de entorno si no existe
    ENV_FILE="$HOME/ExtractorOV_Modular/.env"
    
    if [ ! -f "$ENV_FILE" ]; then
        cat > "$ENV_FILE" << 'EOF'
# Configuración para Ubuntu Server
DISPLAY=:99
HEADLESS=true
UBUNTU_SERVER=true

# Rutas base (se ajustarán dinámicamente)
HOME_DIR=/home/$USER
PROJECT_DIR=/home/$USER/ExtractorOV_Modular
DOWNLOADS_DIR=/home/$USER/ExtractorOV_Modular/downloads

# Configuración de Playwright
PLAYWRIGHT_BROWSERS_PATH=/home/$USER/ExtractorOV_Modular/venv/lib/python3.*/site-packages/playwright/driver/browsers
EOF
        log_success "Archivo .env creado"
    else
        log_info "Archivo .env ya existe"
    fi
}

# Crear servicio systemd (opcional)
create_systemd_service() {
    log_info "¿Deseas crear servicios systemd para auto-inicio? (y/N)"
    read -r response
    
    if [[ "$response" =~ ^([yY][eE][sS]|[yY])$ ]]; then
        log_info "Creando servicios systemd..."
        
        # Crear servicio para Aire
        sudo tee /etc/systemd/system/extractor-aire.service > /dev/null << EOF
[Unit]
Description=Extractor Aire - Oficina Virtual
After=network.target

[Service]
Type=simple
User=$USER
WorkingDirectory=$HOME/ExtractorOV_Modular
Environment=DISPLAY=:99
ExecStart=$HOME/ExtractorOV_Modular/venv/bin/python run_aire_ov_visual.py
Restart=on-failure
RestartSec=30

[Install]
WantedBy=multi-user.target
EOF
        
        # Crear servicio para Afinia
        sudo tee /etc/systemd/system/extractor-afinia.service > /dev/null << EOF
[Unit]
Description=Extractor Afinia - Oficina Virtual
After=network.target

[Service]
Type=simple
User=$USER
WorkingDirectory=$HOME/ExtractorOV_Modular
Environment=DISPLAY=:99
ExecStart=$HOME/ExtractorOV_Modular/venv/bin/python run_afinia_ov_visual.py
Restart=on-failure
RestartSec=30

[Install]
WantedBy=multi-user.target
EOF
        
        # Recargar systemd
        sudo systemctl daemon-reload
        
        log_success "Servicios systemd creados"
        log_info "Para habilitarlos: sudo systemctl enable extractor-aire extractor-afinia"
        log_info "Para iniciarlos: sudo systemctl start extractor-aire"
    fi
}

# Función principal
main() {
    log_info "=== INSTALACIÓN EXTRACTOROV MODULAR PARA UBUNTU SERVER ==="
    log_info "Este script instalará todas las dependencias necesarias"
    echo
    
    check_root
    check_ubuntu_version
    
    log_info "¿Continuar con la instalación? (y/N)"
    read -r response
    
    if [[ ! "$response" =~ ^([yY][eE][sS]|[yY])$ ]]; then
        log_info "Instalación cancelada"
        exit 0
    fi
    
    update_system
    install_system_dependencies
    setup_python_environment
    install_python_dependencies
    install_playwright_browsers
    create_directories
    setup_environment_variables
    create_systemd_service
    
    log_success "=== INSTALACIÓN COMPLETADA ==="
    echo
    log_info "Próximos pasos:"
    log_info "1. Copiar los archivos del proyecto a: $HOME/ExtractorOV_Modular"
    log_info "2. Activar el entorno virtual: source $HOME/ExtractorOV_Modular/venv/bin/activate"
    log_info "3. Ejecutar: python run_aire_ov_visual.py o python run_afinia_ov_visual.py"
    echo
    log_info "Para modo headless, usar: xvfb-run -a python run_aire_ov_visual.py"
}

# Ejecutar función principal
main "$@"