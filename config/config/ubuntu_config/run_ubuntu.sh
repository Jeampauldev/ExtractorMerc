#!/bin/bash
# -*- coding: utf-8 -*-

# ============================================================================
# Script de Ejecución para Ubuntu Server - ExtractorOV Modular
# ============================================================================
# 
# Este script configura y ejecuta el ExtractorOV en Ubuntu Server de forma
# optimizada, con soporte para modo headless y gestión de procesos.
#
# Uso:
#   ./run_ubuntu.sh [comando] [opciones]
#
# Comandos:
#   aire       - Ejecutar extractor de Aire
#   afinia     - Ejecutar extractor de Afinia
#   all        - Ejecutar todos los extractores
#   test       - Ejecutar en modo test
#   setup      - Configurar entorno inicial
#   status     - Ver estado de procesos
#   stop       - Detener todos los extractores
#   logs       - Ver logs en tiempo real
# ============================================================================

set -euo pipefail  # Modo estricto

# Configuración base
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"
UBUNTU_CONFIG="$PROJECT_ROOT/ubuntu_config"
VENV_PATH="$PROJECT_ROOT/venv"
LOGS_DIR="$PROJECT_ROOT/logs"
PID_DIR="$PROJECT_ROOT/pids"

# Colores para output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # Sin color

# Función para logging
log() {
    local level="$1"
    shift
    local message="$*"
    local timestamp=$(date '+%Y-%m-%d %H:%M:%S')
    
    case "$level" in
        "INFO")  echo -e "${BLUE}[$timestamp] INFO:${NC} $message" ;;
        "WARN")  echo -e "${YELLOW}[$timestamp] WARN:${NC} $message" ;;
        "ERROR") echo -e "${RED}[$timestamp] ERROR:${NC} $message" ;;
        "SUCCESS") echo -e "${GREEN}[$timestamp] SUCCESS:${NC} $message" ;;
        *) echo "[$timestamp] $level: $message" ;;
    esac
}

# Función para verificar dependencias
check_dependencies() {
    log "INFO" "🔍 Verificando dependencias..."
    
    local missing_deps=()
    
    # Verificar Python 3
    if ! command -v python3 &> /dev/null; then
        missing_deps+=(python3)
    fi
    
    # Verificar pip
    if ! command -v pip3 &> /dev/null; then
        missing_deps+=(python3-pip)
    fi
    
    # Verificar XVFB para headless
    if ! command -v xvfb-run &> /dev/null; then
        missing_deps+=(xvfb)
    fi
    
    # Verificar Chrome/Chromium
    local chrome_found=false
    for chrome_cmd in google-chrome-stable google-chrome chromium-browser chromium; do
        if command -v "$chrome_cmd" &> /dev/null; then
            chrome_found=true
            log "INFO" "✅ Chrome encontrado: $chrome_cmd"
            break
        fi
    done
    
    if [[ "$chrome_found" != true ]]; then
        log "WARN" "⚠️ Chrome no encontrado - Playwright lo instalará automáticamente"
    fi
    
    if [[ ${#missing_deps[@]} -gt 0 ]]; then
        log "ERROR" "❌ Dependencias faltantes: ${missing_deps[*]}"
        log "INFO" "Instalar con: sudo apt update && sudo apt install -y ${missing_deps[*]}"
        return 1
    fi
    
    log "SUCCESS" "✅ Todas las dependencias están instaladas"
    return 0
}

# Función para configurar entorno virtual
setup_venv() {
    log "INFO" "🐍 Configurando entorno virtual de Python..."
    
    if [[ ! -d "$VENV_PATH" ]]; then
        log "INFO" "Creando entorno virtual en $VENV_PATH"
        python3 -m venv "$VENV_PATH"
    fi
    
    # Activar entorno virtual
    source "$VENV_PATH/bin/activate"
    
    # Actualizar pip
    log "INFO" "Actualizando pip..."
    pip install --upgrade pip
    
    # Instalar requirements
    if [[ -f "$PROJECT_ROOT/requirements.txt" ]]; then
        log "INFO" "Instalando dependencias de requirements.txt..."
        pip install -r "$PROJECT_ROOT/requirements.txt"
    fi
    
    # Instalar Playwright browsers
    log "INFO" "Instalando navegadores de Playwright..."
    playwright install chromium
    
    log "SUCCESS" "✅ Entorno virtual configurado correctamente"
}

# Función para configurar XVFB
setup_xvfb() {
    log "INFO" "🖥️ Configurando XVFB para modo headless..."
    
    # Configurar variables de entorno para XVFB
    export DISPLAY=:99
    export XVFB_WHD="1366x768x24"
    
    # Verificar si XVFB ya está corriendo
    if pgrep -f "Xvfb :99" > /dev/null; then
        log "INFO" "✅ XVFB ya está ejecutándose en :99"
    else
        log "INFO" "Iniciando XVFB en display :99..."
        Xvfb :99 -ac -screen 0 1366x768x24 &
        sleep 2
        
        if pgrep -f "Xvfb :99" > /dev/null; then
            log "SUCCESS" "✅ XVFB iniciado correctamente"
        else
            log "ERROR" "❌ Error iniciando XVFB"
            return 1
        fi
    fi
}

# Función para crear directorios necesarios
create_directories() {
    local dirs=("$LOGS_DIR" "$PID_DIR")
    
    for dir in "${dirs[@]}"; do
        if [[ ! -d "$dir" ]]; then
            log "INFO" "📁 Creando directorio: $dir"
            mkdir -p "$dir"
        fi
    done
    
    # Crear directorio de descargas si no existe
    local downloads_dir="$PROJECT_ROOT/downloads"
    if [[ ! -d "$downloads_dir" ]]; then
        mkdir -p "$downloads_dir"
        log "INFO" "📁 Directorio de descargas creado: $downloads_dir"
    fi
}

# Función para configurar variables de entorno
setup_environment() {
    log "INFO" "⚙️ Configurando variables de entorno..."
    
    # Variables específicas para Ubuntu Server
    export UBUNTU_SERVER=true
    export HEADLESS=true
    export PYTHONPATH="$PROJECT_ROOT:$PYTHONPATH"
    
    # Configurar variables de XVFB si no están definidas
    if [[ -z "${DISPLAY:-}" ]]; then
        export DISPLAY=:99
    fi
    
    if [[ -z "${XVFB_WHD:-}" ]]; then
        export XVFB_WHD="1366x768x24"
    fi
    
    log "SUCCESS" "✅ Variables de entorno configuradas"
}

# Función para ejecutar extractor
run_extractor() {
    local extractor="$1"
    local mode="${2:-normal}"
    
    log "INFO" "🚀 Ejecutando extractor: $extractor (modo: $mode)"
    
    # Activar entorno virtual
    source "$VENV_PATH/bin/activate"
    
    # Configurar Python path
    export PYTHONPATH="$PROJECT_ROOT:$PYTHONPATH"
    
    local script_path=""
    local log_file=""
    local pid_file=""
    
    case "$extractor" in
        "aire")
            script_path="$PROJECT_ROOT/aire_manager.py"
            log_file="$LOGS_DIR/aire_$(date +%Y%m%d_%H%M%S).log"
            pid_file="$PID_DIR/aire.pid"
            ;;
        "afinia")
            script_path="$PROJECT_ROOT/afinia_manager_advanced.py"
            log_file="$LOGS_DIR/afinia_$(date +%Y%m%d_%H%M%S).log"
            pid_file="$PID_DIR/afinia.pid"
            ;;
        *)
            log "ERROR" "❌ Extractor desconocido: $extractor"
            return 1
            ;;
    esac
    
    if [[ ! -f "$script_path" ]]; then
        log "ERROR" "❌ Script no encontrado: $script_path"
        return 1
    fi
    
    # Preparar comando
    local cmd="python3 '$script_path'"
    
    if [[ "$mode" == "test" ]]; then
        cmd+=" --test"
    fi
    
    # Ejecutar con XVFB
    log "INFO" "📝 Log file: $log_file"
    log "INFO" "🆔 PID file: $pid_file"
    
    if [[ "$mode" == "foreground" ]]; then
        # Ejecutar en primer plano
        xvfb-run -a -s "-screen 0 1366x768x24" bash -c "$cmd" 2>&1 | tee "$log_file"
    else
        # Ejecutar en background
        nohup xvfb-run -a -s "-screen 0 1366x768x24" bash -c "$cmd" > "$log_file" 2>&1 &
        local pid=$!
        echo "$pid" > "$pid_file"
        log "SUCCESS" "✅ Extractor $extractor iniciado (PID: $pid)"
        log "INFO" "Para ver logs: tail -f $log_file"
    fi
}

# Función para obtener estado de procesos
get_status() {
    log "INFO" "📊 Estado de extractores:"
    
    for extractor in aire afinia; do
        local pid_file="$PID_DIR/$extractor.pid"
        
        if [[ -f "$pid_file" ]]; then
            local pid=$(cat "$pid_file")
            
            if kill -0 "$pid" 2>/dev/null; then
                log "SUCCESS" "✅ $extractor: RUNNING (PID: $pid)"
            else
                log "WARN" "❌ $extractor: STOPPED (PID file stale)"
                rm -f "$pid_file"
            fi
        else
            log "INFO" "⚪ $extractor: NOT STARTED"
        fi
    done
}

# Función para detener extractores
stop_extractors() {
    log "INFO" "🛑 Deteniendo extractores..."
    
    for extractor in aire afinia; do
        local pid_file="$PID_DIR/$extractor.pid"
        
        if [[ -f "$pid_file" ]]; then
            local pid=$(cat "$pid_file")
            
            if kill -0 "$pid" 2>/dev/null; then
                log "INFO" "Deteniendo $extractor (PID: $pid)..."
                kill -TERM "$pid"
                
                # Esperar hasta 10 segundos para que se detenga
                local count=0
                while kill -0 "$pid" 2>/dev/null && [[ $count -lt 10 ]]; do
                    sleep 1
                    ((count++))
                done
                
                # Si aún sigue corriendo, forzar
                if kill -0 "$pid" 2>/dev/null; then
                    log "WARN" "Forzando detención de $extractor..."
                    kill -KILL "$pid"
                fi
                
                log "SUCCESS" "✅ $extractor detenido"
            fi
            
            rm -f "$pid_file"
        fi
    done
}

# Función para mostrar logs en tiempo real
show_logs() {
    local extractor="${1:-all}"
    
    case "$extractor" in
        "aire"|"afinia")
            local latest_log=$(find "$LOGS_DIR" -name "${extractor}_*.log" -type f -exec ls -t {} + | head -1)
            if [[ -f "$latest_log" ]]; then
                log "INFO" "📋 Mostrando logs de $extractor: $latest_log"
                tail -f "$latest_log"
            else
                log "ERROR" "❌ No se encontraron logs para $extractor"
            fi
            ;;
        "all"|*)
            local latest_log=$(find "$LOGS_DIR" -name "*.log" -type f -exec ls -t {} + | head -1)
            if [[ -f "$latest_log" ]]; then
                log "INFO" "📋 Mostrando logs más recientes: $latest_log"
                tail -f "$latest_log"
            else
                log "ERROR" "❌ No se encontraron logs"
            fi
            ;;
    esac
}

# Función para mostrar ayuda
show_help() {
    cat << 'EOF'
🚀 ExtractorOV Ubuntu Server - Script de Ejecución

USAGE:
    ./run_ubuntu.sh [COMANDO] [OPCIONES]

COMANDOS:
    aire           Ejecutar extractor de Aire
    afinia         Ejecutar extractor de Afinia  
    all            Ejecutar todos los extractores
    test           Ejecutar en modo test (todos los extractores)
    setup          Configurar entorno inicial completo
    status         Ver estado de procesos en ejecución
    stop           Detener todos los extractores
    logs [name]    Ver logs en tiempo real (aire, afinia, o all)
    help           Mostrar esta ayuda

OPCIONES:
    --foreground   Ejecutar en primer plano (no background)
    --test         Ejecutar en modo test
    --force-setup  Forzar reconfiguración del entorno

EJEMPLOS:
    ./run_ubuntu.sh setup                    # Configurar entorno inicial
    ./run_ubuntu.sh aire                     # Ejecutar extractor Aire
    ./run_ubuntu.sh afinia --foreground      # Ejecutar Afinia en primer plano
    ./run_ubuntu.sh all                      # Ejecutar todos los extractores
    ./run_ubuntu.sh test                     # Ejecutar todos en modo test
    ./run_ubuntu.sh status                   # Ver estado
    ./run_ubuntu.sh logs aire                # Ver logs de Aire
    ./run_ubuntu.sh stop                     # Detener todos

DIRECTORIOS:
    Proyecto:     $PROJECT_ROOT
    Logs:         $LOGS_DIR
    PIDs:         $PID_DIR
    Virtual ENV:  $VENV_PATH

Para más información: https://github.com/tu-usuario/ExtractorOV_Modular
EOF
}

# Función principal
main() {
    local command="${1:-help}"
    local foreground=false
    local test_mode=false
    local force_setup=false
    
    # Procesar opciones
    shift || true
    while [[ $# -gt 0 ]]; do
        case "$1" in
            --foreground) foreground=true ;;
            --test) test_mode=true ;;
            --force-setup) force_setup=true ;;
            *) log "WARN" "Opción desconocida: $1" ;;
        esac
        shift
    done
    
    # Crear directorios básicos
    create_directories
    
    case "$command" in
        "setup")
            log "INFO" "🔧 Configurando entorno Ubuntu Server..."
            check_dependencies || exit 1
            setup_venv
            setup_environment
            setup_xvfb
            log "SUCCESS" "✅ Configuración completada"
            ;;
            
        "aire"|"afinia")
            check_dependencies || exit 1
            setup_environment
            setup_xvfb
            
            local mode="normal"
            if [[ "$test_mode" == true ]]; then
                mode="test"
            elif [[ "$foreground" == true ]]; then
                mode="foreground"
            fi
            
            run_extractor "$command" "$mode"
            ;;
            
        "all")
            check_dependencies || exit 1
            setup_environment
            setup_xvfb
            
            local mode="normal"
            if [[ "$test_mode" == true ]]; then
                mode="test"
            elif [[ "$foreground" == true ]]; then
                mode="foreground"
            fi
            
            log "INFO" "🚀 Iniciando todos los extractores..."
            run_extractor "aire" "$mode"
            sleep 2
            run_extractor "afinia" "$mode"
            ;;
            
        "test")
            check_dependencies || exit 1
            setup_environment
            setup_xvfb
            
            log "INFO" "🧪 Ejecutando en modo test..."
            run_extractor "aire" "test"
            sleep 2
            run_extractor "afinia" "test"
            ;;
            
        "status")
            get_status
            ;;
            
        "stop")
            stop_extractors
            ;;
            
        "data/logs")
            local target="${1:-all}"
            show_logs "$target"
            ;;
            
        "help"|*)
            show_help
            ;;
    esac
}

# Verificar si se está ejecutando como script principal
if [[ "${BASH_SOURCE[0]}" == "${0}" ]]; then
    main "$@"
fi