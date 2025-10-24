# AI Context Directory

## 🤖 Información para Agentes IA y Desarrolladores Automáticos

Esta carpeta contiene información especializada para facilitar el trabajo de agentes IA, herramientas de desarrollo automático y nuevos desarrolladores que necesiten entender rápidamente el proyecto.

---

## 📋 Contenido de la Carpeta

### `PROJECT_STANDARDS.md`
**Documento principal con estándares profesionales**
- Créditos y autoría del proyecto
- Estándares de código obligatorios
- Formato de logging profesional
- Reemplazos de emojis específicos
- Flujo de trabajo recomendado para IAs

### `TECHNICAL_CONTEXT.md`
**Contexto técnico detallado del sistema**
- Estado actual del sistema
- Arquitectura de datos (RDS, S3)
- Flujo de datos paso a paso
- Componentes críticos
- Patrones de diseño implementados
- Scripts de verificación y testing

---

## 🎯 Propósito

### Para Agentes IA
- Entender los estándares profesionales del proyecto
- Conocer qué archivos son críticos y cuáles se pueden modificar
- Aplicar el formato de logging correcto
- Usar herramientas de limpieza y verificación

### Para Desarrolladores
- Onboarding rápido al proyecto
- Comprensión de arquitectura y patrones
- Guías de mejores prácticas
- Referencias técnicas detalladas

### Para Herramientas Automáticas
- Configuración de scripts de limpieza
- Validación automática de código
- Estándares de documentación
- Patrones a seguir y evitar

---

## 🚀 Inicio Rápido para IAs

### 1. Leer Primero
```bash
# Orden recomendado de lectura
1. ai-context/README.md        # (este archivo)
2. ai-context/PROJECT_STANDARDS.md  # Estándares obligatorios
3. ai-context/TECHNICAL_CONTEXT.md  # Contexto técnico
```

### 2. Verificar Sistema
```bash
# Antes de hacer cambios
python scripts/validate_functionality.py
python -c "from afinia_manager import AfiniaManager; print('System OK')"
```

### 3. Hacer Cambios Seguros
```bash
# Patrón recomendado
1. Hacer backup de archivos a modificar
2. Aplicar cambios graduales
3. Ejecutar limpieza de emojis
4. Verificar funcionalidad
```

### 4. Aplicar Estándares
```bash
# Limpieza automática de formato
python scripts/clean_emojis_professional.py --apply-all
```

---

## ⚠️ Reglas Críticas

### ❌ NO HACER
- Modificar múltiples archivos críticos simultáneamente
- Usar emojis en logs o código
- Referencias a IA o automatización en comentarios
- Cambiar la estructura de base de datos sin aprobación
- Romper la funcionalidad existente

### ✅ SIEMPRE HACER
- Leer PROJECT_STANDARDS.md antes de cambios
- Usar formato de logging profesional
- Verificar funcionalidad después de cambios
- Aplicar scripts de limpieza
- Documentar cambios significativos

---

## 🔧 Herramientas Disponibles

### Scripts de Limpieza
```bash
# Por categorías
python scripts/clean_emojis_professional.py --apply-critical     # Archivos críticos
python scripts/clean_emojis_professional.py --apply-components  # Componentes
python scripts/clean_emojis_professional.py --apply-services    # Servicios

# Todo el proyecto
python scripts/clean_emojis_professional.py --apply-all
```

### Scripts de Verificación
```bash
# Funcionalidad general
python scripts/validate_functionality.py

# Estándares de logging
python scripts/verify_logging_standards.py

# Conectividad
python scripts/test_connectivity.py
```

### Testing Rápido
```bash
# Import test
python -c "
from afinia_manager import AfiniaManager
from src.services.database_service import DatabaseService
print('Imports OK')
"

# Initialization test
python -c "
from afinia_manager import AfiniaManager
manager = AfiniaManager(headless=True, test_mode=True)
print('Initialization OK')
"
```

---

## 📊 Estado del Proyecto

### ✅ Completado
- Sistema de logging profesional sin emojis
- Limpieza de archivos críticos y componentes
- Scripts de automatización y verificación
- Documentación para IAs

### 🔄 En Progreso
- Integración completa con RDS
- Optimización de servicios S3
- Dashboard de monitoreo
- Scripts de mantenimiento

---

## 💡 Tips para IAs

### Modificando Código
```python
# Plantilla de verificación post-cambios
def verify_after_changes():
    try:
        # Test básico de importación
        from afinia_manager import AfiniaManager
        
        # Test de inicialización
        manager = AfiniaManager(headless=True, test_mode=True)
        
        # Test de logging format
        import logging
        logger = logging.getLogger('test')
        logger.info("VERIFICANDO formato profesional")
        
        return True
    except Exception as e:
        print(f"ERROR: {e}")
        return False

# Ejecutar después de cada cambio
if verify_after_changes():
    print("✅ Cambios OK")
else:
    print("❌ Revisar cambios")
```

### Manteniendo Estándares
```python
# Siempre aplicar después de modificar archivos
import subprocess
result = subprocess.run([
    "python", 
    "scripts/clean_emojis_professional.py", 
    "--apply-all"
], capture_output=True, text=True)

if result.returncode == 0:
    print("✅ Estándares aplicados")
else:
    print(f"❌ Error aplicando estándares: {result.stderr}")
```

---

## 📞 Soporte

### Para Problemas Técnicos
1. **Consultar** `TECHNICAL_CONTEXT.md`
2. **Revisar logs** en `data/logs/current/`
3. **Ejecutar** scripts de diagnóstico
4. **Verificar** configuración en `config/env/.env`

### Para Dudas de Estándares
1. **Revisar** `PROJECT_STANDARDS.md`
2. **Aplicar** scripts de limpieza
3. **Validar** con scripts de verificación

---

## 🏆 Créditos

**Desarrollado por: ISES | Analyst Data Jeam Paul Arcon Solano**

Esta carpeta y sistema de estándares ha sido diseñado para mantener la calidad profesional del proyecto y facilitar el trabajo colaborativo con agentes IA.

---

*Última actualización: 2025-10-08*
*Para mantener esta carpeta actualizada, documenta cualquier cambio significativo en el proyecto.*