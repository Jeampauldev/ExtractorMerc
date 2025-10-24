# Arquitectura ExtractorMERC v2.0 - Refactorizada

## Resumen Ejecutivo

ExtractorMERC v2.0 representa una refactorización completa del sistema original, transformando una arquitectura monolítica con código legacy disperso en un sistema modular, mantenible y escalable. La nueva arquitectura separa claramente las responsabilidades, elimina duplicación de código y establece patrones consistentes para futuras extensiones.

## Arquitectura General

### Principios de Diseño

1. **Separación de Responsabilidades**: Cada módulo tiene una responsabilidad específica y bien definida
2. **Modularidad**: Componentes independientes que pueden ser reutilizados y probados por separado
3. **Extensibilidad**: Fácil adición de nuevas empresas o funcionalidades
4. **Mantenibilidad**: Código limpio, documentado y siguiendo estándares
5. **Robustez**: Manejo integral de errores y logging centralizado

### Estructura de Directorios

```
Merc/
├── core/                    # Componentes fundamentales del sistema
│   ├── base_extractor.py   # Clase base abstracta para extractores
│   ├── browser_manager.py  # Gestión centralizada de navegadores
│   ├── authentication_manager.py  # Autenticación unificada
│   ├── data_processor.py   # Procesamiento de datos centralizado
│   ├── mercurio_adapter.py # Adaptador específico para Mercurio
│   └── ...                 # Otros componentes core
├── services/               # Extractores específicos por empresa
│   ├── afinia_extractor.py # Extractor para Afinia
│   └── aire_extractor.py   # Extractor para Aire
├── config/                 # Configuraciones del sistema
│   └── afinia_config.py    # Configuración específica de Afinia
├── utils/                  # Utilidades y helpers
│   ├── afinia_validators.py # Validadores específicos
│   └── aire_logger.py      # Logger específico
├── tests/                  # Pruebas del sistema
├── docs/                   # Documentación
├── main.py                 # Punto de entrada principal
├── flujos_optimizado.yaml  # Configuración de flujos v2.0
└── .gitignore             # Control de versiones
```

## Componentes Principales

### 1. Core Components

#### BaseExtractor (core/base_extractor.py)
- **Propósito**: Clase base abstracta que define la interfaz común para todos los extractores
- **Responsabilidades**:
  - Definir métodos abstractos obligatorios
  - Implementar funcionalidades comunes (logging, manejo de estado)
  - Proporcionar template method pattern para el flujo de extracción
- **Beneficios**: Garantiza consistencia entre extractores y facilita mantenimiento

#### BrowserManager (core/browser_manager.py)
- **Propósito**: Gestión centralizada de navegadores Playwright
- **Responsabilidades**:
  - Configuración optimizada de navegadores
  - Manejo de contextos y páginas
  - Gestión de descargas
  - Limpieza de recursos
- **Beneficios**: Configuración consistente y manejo robusto de recursos

#### AuthenticationManager (core/authentication_manager.py)
- **Propósito**: Autenticación unificada para plataformas Mercurio
- **Responsabilidades**:
  - Manejo de credenciales por empresa
  - Proceso de login estandarizado
  - Verificación de autenticación exitosa
- **Beneficios**: Reutilización de lógica de autenticación y manejo consistente

#### DataProcessor (core/data_processor.py)
- **Propósito**: Procesamiento centralizado de datos CSV y JSON
- **Responsabilidades**:
  - Limpieza y transformación de datos
  - Validación de calidad de datos
  - Generación de estadísticas
  - Manejo de diferentes formatos
- **Beneficios**: Procesamiento consistente y reutilizable

### 2. Services Layer

#### AfiniaExtractor (services/afinia_extractor.py)
- **Propósito**: Extractor específico para la plataforma Mercurio de Afinia
- **Hereda de**: BaseExtractor
- **Responsabilidades**:
  - Implementar lógica específica de navegación para Afinia
  - Configurar filtros y búsquedas específicas
  - Manejar descargas de reportes CSV y PDF
- **Beneficios**: Especialización sin duplicación de código base

#### AireExtractor (services/aire_extractor.py)
- **Propósito**: Extractor específico para la plataforma Mercurio de Aire
- **Hereda de**: BaseExtractor
- **Responsabilidades**:
  - Implementar lógica específica de navegación para Aire
  - Configurar filtros y búsquedas específicas
  - Manejar descargas de reportes CSV y PDF
- **Beneficios**: Especialización manteniendo consistencia arquitectónica

### 3. Configuration Layer

#### Configuración Centralizada
- **Archivos de configuración por empresa**: Separación clara de configuraciones
- **Variables de entorno**: Manejo seguro de credenciales
- **Flujos YAML**: Definición declarativa de procesos de negocio

### 4. Orchestration Layer

#### ExtractorMercOrchestrator (main.py)
- **Propósito**: Coordinación y ejecución de múltiples extractores
- **Responsabilidades**:
  - Registro y gestión de extractores
  - Ejecución paralela o secuencial
  - Agregación de resultados
  - Manejo de errores a nivel sistema
- **Beneficios**: Control centralizado y capacidad de ejecución masiva

## Patrones de Diseño Implementados

### 1. Template Method Pattern
- **Ubicación**: BaseExtractor.run_extraction()
- **Propósito**: Define el esqueleto del algoritmo de extracción
- **Beneficio**: Consistencia en el flujo mientras permite personalización

### 2. Strategy Pattern
- **Ubicación**: Extractores específicos (Afinia, Aire)
- **Propósito**: Diferentes estrategias de extracción por empresa
- **Beneficio**: Flexibilidad para manejar diferentes plataformas

### 3. Adapter Pattern
- **Ubicación**: MercurioAdapter
- **Propósito**: Adapta la interfaz específica de Mercurio
- **Beneficio**: Abstrae complejidades específicas de la plataforma

### 4. Factory Pattern
- **Ubicación**: Creación de extractores en main.py
- **Propósito**: Creación controlada de instancias de extractores
- **Beneficio**: Flexibilidad en la creación y configuración

## Flujo de Datos

### 1. Inicialización
```
main.py → ExtractorMercOrchestrator → Registro de Extractores
```

### 2. Ejecución
```
Orchestrator → BaseExtractor.run_extraction() → 
├── setup_browser() → BrowserManager
├── authenticate() → AuthenticationManager  
├── extract_data() → Extractor específico
├── process_data() → DataProcessor
└── cleanup() → BrowserManager
```

### 3. Procesamiento
```
Datos Raw → DataProcessor → 
├── Limpieza
├── Transformación
├── Validación
└── Estadísticas
```

## Beneficios de la Nueva Arquitectura

### 1. Mantenibilidad
- **Código organizado**: Separación clara de responsabilidades
- **Eliminación de duplicación**: Componentes reutilizables
- **Documentación integrada**: Código autodocumentado

### 2. Escalabilidad
- **Fácil adición de empresas**: Nuevo extractor heredando de BaseExtractor
- **Componentes modulares**: Modificación independiente
- **Configuración flexible**: Adaptación sin cambios de código

### 3. Robustez
- **Manejo integral de errores**: Logging y recuperación consistentes
- **Validación de datos**: Calidad garantizada
- **Limpieza de recursos**: Prevención de memory leaks

### 4. Testabilidad
- **Componentes aislados**: Pruebas unitarias independientes
- **Interfaces claras**: Mocking y stubbing facilitados
- **Separación de concerns**: Testing enfocado

## Migración desde v1.0

### Cambios Principales
1. **Eliminación de código legacy**: Archivos HTML y extractores duplicados
2. **Reorganización estructural**: Nueva jerarquía de directorios
3. **Centralización de funcionalidades**: Componentes core reutilizables
4. **Modernización de patrones**: Implementación de mejores prácticas

### Compatibilidad
- **Flujos de negocio**: Mantenidos en flujos_optimizado.yaml
- **Funcionalidades**: Todas las capacidades originales preservadas
- **Configuración**: Migrada a nuevo formato más flexible

## Próximos Pasos

### Fase 1: Consolidación
- [ ] Pruebas exhaustivas de todos los componentes
- [ ] Validación de flujos de negocio
- [ ] Optimización de rendimiento

### Fase 2: Extensión
- [ ] Adición de nuevas empresas
- [ ] Implementación de métricas avanzadas
- [ ] Dashboard de monitoreo

### Fase 3: Automatización
- [ ] CI/CD pipeline
- [ ] Despliegue automatizado
- [ ] Monitoreo en producción

---

**Autor**: ExtractorOV Team  
**Fecha**: 2025-01-27  
**Versión**: 2.0  
**Estado**: Refactorización Completa