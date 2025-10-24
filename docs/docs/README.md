# Documentación ExtractorOV Modular

## Índice de Documentación

Este directorio contiene toda la documentación del proyecto ExtractorOV Modular reorganizado.

## Estructura de Documentación

### 📊 Analysis (analysis/)
Documentos de análisis del proyecto:
- `ANALISIS_ARCHIVOS_ACTUALES.md` - Análisis de archivos del proyecto actual
- `ARCHIVOS_RUN_ANALISIS.md` - Análisis específico de archivos run_*

### 📋 Planning (planning/)
Documentos de planificación y diseño:
- `PLAN_REORGANIZACION.md` - Plan detallado de reorganización del proyecto

### 🛠️ Setup (setup/)  
Guías de configuración e instalación:
- `README_REQUISITOS_MINIMOS.md` - Requisitos mínimos del sistema
- `UBUNTU_SERVER_CHANGES_ANALYSIS.md` - Análisis de cambios para Ubuntu Server

### 📈 Reports (reports/)
Reportes y análisis generados:
- Reportes de consolidación de logs
- Análisis de rendimiento
- Métricas de extracción

## Documentación Principal

- [`README_PROYECTO_REORGANIZADO.md`](README_PROYECTO_REORGANIZADO.md) - Documentación principal del proyecto reorganizado

## Navegación Rápida

### Para Usuarios Nuevos
1. Lea [`README_PROYECTO_REORGANIZADO.md`](README_PROYECTO_REORGANIZADO.md)
2. Revise [`setup/README_REQUISITOS_MINIMOS.md`](setup/README_REQUISITOS_MINIMOS.md)
3. Configure credenciales según la guía principal

### Para Desarrolladores  
1. Revise [`analysis/ANALISIS_ARCHIVOS_ACTUALES.md`](analysis/ANALISIS_ARCHIVOS_ACTUALES.md)
2. Consulte [`planning/PLAN_REORGANIZACION.md`](planning/PLAN_REORGANIZACION.md)
3. Examine ejemplos en `../examples/`

### Para Administradores de Servidor
1. Consulte [`setup/UBUNTU_SERVER_CHANGES_ANALYSIS.md`](setup/UBUNTU_SERVER_CHANGES_ANALYSIS.md)
2. Revise configuraciones en `../config/`
3. Examine scripts en `../scripts/`

## Estructura del Proyecto

```
docs/
├── README.md                          # Este archivo
├── README_PROYECTO_REORGANIZADO.md    # Documentación principal
├── analysis/                          # Análisis del proyecto
│   ├── ANALISIS_ARCHIVOS_ACTUALES.md
│   └── ARCHIVOS_RUN_ANALISIS.md
├── planning/                          # Planificación
│   └── PLAN_REORGANIZACION.md
├── setup/                             # Configuración
│   ├── README_REQUISITOS_MINIMOS.md
│   └── UBUNTU_SERVER_CHANGES_ANALYSIS.md
└── reports/                           # Reportes
    └── [reportes generados]
```

## Estado de la Documentación

### ✅ Completado
- [x] Reorganización de archivos de documentación
- [x] Documentación principal actualizada
- [x] Estructura de carpetas organizada
- [x] Índice de navegación creado

### 📝 Pendiente
- [ ] Actualización de documentos legacy con nueva estructura
- [ ] Creación de documentación de API
- [ ] Guías de troubleshooting específicas
- [ ] Documentación de configuración avanzada

## Contribución

Para actualizar la documentación:

1. Mantener la estructura de carpetas establecida
2. Usar formato Markdown estándar
3. Actualizar este índice cuando se agreguen nuevos documentos
4. Referenciar la nueva estructura de imports

## Links Útiles

- [Proyecto Principal](../README.md)
- [Managers](../aire_manager.py) y [Afinia](../afinia_manager.py)
- [Ejemplos](../examples/)
- [Configuraciones](../config/)
- [Código Fuente](../src/)

---

*Documentación generada para ExtractorOV Modular v2.0*