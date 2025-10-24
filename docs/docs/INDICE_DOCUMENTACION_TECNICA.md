# Índice de Documentación Técnica - ExtractorOV Modular

## Resumen Ejecutivo

Este documento proporciona un índice completo de toda la documentación técnica disponible para el sistema ExtractorOV Modular, organizada por audiencia objetivo y nivel de detalle técnico.

## Estructura de la Documentación

### Documentación por Audiencia

```
docs/
├── arquitectura/          # Para Arquitectos de Software y Tech Leads
├── desarrollo/           # Para Desarrolladores y Programadores  
├── operaciones/          # Para Administradores de Sistema y DevOps
├── usuario/              # Para Usuarios Finales y Operadores
├── setup/                # Configuración e instalación (heredado)
├── analysis/             # Análisis técnicos (heredado)
├── planning/             # Planificación del proyecto (heredado)
└── reports/              # Reportes del sistema (heredado)
```

## Documentación Esencial (Nueva)

### 1. Arquitectura del Sistema

#### [`arquitectura/VISION_GENERAL_SISTEMA.md`](arquitectura/VISION_GENERAL_SISTEMA.md)
**Audiencia**: Arquitectos de Software, Tech Leads, Desarrolladores Senior
**Contenido**:
- Principios arquitectónicos del sistema
- Vista de alto nivel de componentes
- Patrones de diseño implementados
- Flujo de datos completo
- Configuración del sistema
- Métricas y monitoreo
- Consideraciones de seguridad y escalabilidad

**Cuándo consultar**:
- Antes de implementar nuevas funcionalidades
- Para entender la arquitectura general
- Al planificar modificaciones estructurales
- Para documentar decisiones arquitectónicas

### 2. Desarrollo de Software

#### [`desarrollo/GUIA_DESARROLLADOR.md`](desarrollo/GUIA_DESARROLLADOR.md)
**Audiencia**: Desarrolladores, Programadores, QA Engineers
**Contenido**:
- Estructura del código y convenciones
- Arquitectura de clases y interfaces
- Sistema de logging unificado
- Manejo de errores y excepciones
- Framework de testing completo
- Desarrollo de nuevas funcionalidades
- Integración continua y herramientas
- Mejores prácticas de código

**Cuándo consultar**:
- Al incorporarse al equipo de desarrollo
- Antes de escribir nuevo código
- Para implementar pruebas
- Al configurar entorno de desarrollo
- Para resolver problemas de código

### 3. Operaciones e Instalación

#### [`operaciones/MANUAL_INSTALACION.md`](operaciones/MANUAL_INSTALACION.md)
**Audiencia**: Administradores de Sistema, DevOps Engineers, SysAdmins
**Contenido**:
- Requisitos completos del sistema
- Instalación paso a paso (Windows y Ubuntu)
- Configuración de variables de entorno
- Setup de base de datos PostgreSQL
- Configuración de Amazon S3
- Configuración para producción
- Monitoreo y troubleshooting
- Scripts de automatización

**Cuándo consultar**:
- Al instalar el sistema por primera vez
- Para configurar entornos de producción
- Al diagnosticar problemas del sistema
- Para configurar monitoreo automático
- Al planificar despliegues

### 4. Usuario Final

#### [`usuario/MANUAL_USUARIO.md`](usuario/MANUAL_USUARIO.md)
**Audiencia**: Usuarios Finales, Operadores, Analistas de Datos
**Contenido**:
- Guía completa de uso del sistema
- Comandos y parámetros disponibles
- Interpretación de resultados
- Casos de uso comunes
- Solución de problemas frecuentes
- Mantenimiento básico
- Programación de extracciones automáticas
- Mejores prácticas operativas

**Cuándo consultar**:
- Para aprender a usar el sistema
- Al ejecutar extracciones diarias
- Para resolver problemas comunes
- Al interpretar resultados
- Para programar tareas automáticas

## Documentación Heredada (Existente)

### Setup y Configuración

#### [`setup/README_REQUISITOS_MINIMOS.md`](setup/README_REQUISITOS_MINIMOS.md)
**Contenido**: Requisitos mínimos del sistema (complementa la nueva documentación)

#### [`setup/UBUNTU_SERVER_CHANGES_ANALYSIS.md`](setup/UBUNTU_SERVER_CHANGES_ANALYSIS.md)
**Contenido**: Análisis específico para cambios en Ubuntu Server

### Análisis Técnico

#### [`analysis/ANALISIS_ARCHIVOS_ACTUALES.md`](analysis/ANALISIS_ARCHIVOS_ACTUALES.md)
**Contenido**: Análisis de archivos del proyecto actual

#### [`analysis/ARCHIVOS_RUN_ANALISIS.md`](analysis/ARCHIVOS_RUN_ANALISIS.md)
**Contenido**: Análisis específico de archivos run_*

### Planificación

#### [`planning/PLAN_REORGANIZACION.md`](planning/PLAN_REORGANIZACION.md)
**Contenido**: Plan detallado de reorganización del proyecto

### Reportes

#### [`reports/REUBICACION_ARCHIVOS_FINALIZACION.md`](reports/REUBICACION_ARCHIVOS_FINALIZACION.md)
**Contenido**: Reporte de finalización de reubicación de archivos

### Documentación Principal

#### [`README_PROYECTO_REORGANIZADO.md`](README_PROYECTO_REORGANIZADO.md)
**Contenido**: Documentación principal del proyecto reorganizado

## Rutas de Aprendizaje por Rol

### Para Nuevos Desarrolladores
```
1. arquitectura/VISION_GENERAL_SISTEMA.md        # Entender la arquitectura
2. desarrollo/GUIA_DESARROLLADOR.md              # Aprender estándares de desarrollo
3. operaciones/MANUAL_INSTALACION.md             # Configurar entorno local
4. analysis/ANALISIS_ARCHIVOS_ACTUALES.md        # Contexto del código actual
```

### Para Administradores de Sistema
```
1. operaciones/MANUAL_INSTALACION.md             # Instalación completa
2. arquitectura/VISION_GENERAL_SISTEMA.md        # Entender componentes del sistema
3. setup/README_REQUISITOS_MINIMOS.md            # Verificar requisitos
4. setup/UBUNTU_SERVER_CHANGES_ANALYSIS.md       # Configuración específica Ubuntu
```

### Para Usuarios Finales
```
1. usuario/MANUAL_USUARIO.md                     # Guía completa de uso
2. README_PROYECTO_REORGANIZADO.md               # Contexto general del proyecto
3. setup/README_REQUISITOS_MINIMOS.md            # Entender requisitos básicos
```

### Para Project Managers
```
1. README_PROYECTO_REORGANIZADO.md               # Vista general del proyecto
2. arquitectura/VISION_GENERAL_SISTEMA.md        # Entender alcance técnico
3. planning/PLAN_REORGANIZACION.md               # Historial de planificación
4. reports/REUBICACION_ARCHIVOS_FINALIZACION.md  # Estado actual del proyecto
```

## Matriz de Documentación por Caso de Uso

| Caso de Uso | Documentos Primarios | Documentos Secundarios |
|-------------|---------------------|------------------------|
| **Instalación Inicial** | `operaciones/MANUAL_INSTALACION.md` | `setup/README_REQUISITOS_MINIMOS.md`, `setup/UBUNTU_SERVER_CHANGES_ANALYSIS.md` |
| **Desarrollo de Código** | `desarrollo/GUIA_DESARROLLADOR.md` | `arquitectura/VISION_GENERAL_SISTEMA.md`, `analysis/ANALISIS_ARCHIVOS_ACTUALES.md` |
| **Uso Diario del Sistema** | `usuario/MANUAL_USUARIO.md` | `README_PROYECTO_REORGANIZADO.md` |
| **Troubleshooting** | `operaciones/MANUAL_INSTALACION.md`, `usuario/MANUAL_USUARIO.md` | Todos los documentos de analysis/ |
| **Arquitectura y Diseño** | `arquitectura/VISION_GENERAL_SISTEMA.md` | `desarrollo/GUIA_DESARROLLADOR.md`, `planning/PLAN_REORGANIZACION.md` |
| **Onboarding de Equipo** | Todos los documentos nuevos | Documentos de planning/ y reports/ |

## Prioridad de Consulta

### Alta Prioridad (Uso Diario)
1. `usuario/MANUAL_USUARIO.md` - Para operación diaria
2. `operaciones/MANUAL_INSTALACION.md` - Para setup y troubleshooting
3. `desarrollo/GUIA_DESARROLLADOR.md` - Para desarrollo activo

### Media Prioridad (Consulta Frecuente)
1. `arquitectura/VISION_GENERAL_SISTEMA.md` - Para entender el sistema
2. `README_PROYECTO_REORGANIZADO.md` - Para contexto general

### Baja Prioridad (Consulta Ocasional)
1. Documentos en `analysis/` - Para análisis histórico
2. Documentos en `planning/` - Para contexto de planificación
3. Documentos en `reports/` - Para reportes específicos
4. Documentos en `setup/` - Para configuraciones especiales

## Mantenimiento de la Documentación

### Responsabilidades por Documento

| Documento | Responsable Principal | Frecuencia de Actualización |
|-----------|----------------------|----------------------------|
| `arquitectura/VISION_GENERAL_SISTEMA.md` | Arquitecto de Software | Trimestral o cambios mayores |
| `desarrollo/GUIA_DESARROLLADOR.md` | Tech Lead/Senior Developer | Mensual o cambios en estándares |
| `operaciones/MANUAL_INSTALACION.md` | DevOps/SysAdmin | Al cambiar infraestructura |
| `usuario/MANUAL_USUARIO.md` | Product Owner/Support | Al agregar funcionalidades |

### Versionado
- Todos los documentos incluyen fecha de última actualización
- Cambios mayores requieren incremento de versión
- Versionado semántico para documentación técnica crítica

### Proceso de Actualización
1. **Identificar necesidad** de actualización
2. **Asignar responsable** según tabla anterior
3. **Realizar cambios** manteniendo estructura
4. **Revisar cambios** con stakeholders relevantes
5. **Actualizar fecha** y versión
6. **Comunicar cambios** al equipo

## Recursos Adicionales

### Documentación Externa Referenciada
- **Playwright Documentation**: https://playwright.dev/docs/
- **PostgreSQL Documentation**: https://www.postgresql.org/docs/
- **AWS S3 Documentation**: https://docs.aws.amazon.com/s3/
- **Python Best Practices**: https://pep8.org/

### Herramientas de Documentación
- **Markdown**: Para formato estándar
- **Mermaid**: Para diagramas (futuro)
- **Sphinx**: Para generación automática (futuro)

### Contacto para Documentación
- **Actualizaciones urgentes**: Contactar Tech Lead
- **Nuevos documentos**: Crear issue en repositorio
- **Sugerencias de mejora**: Email al equipo de desarrollo

---

**Índice de Documentación Técnica - ExtractorOV Modular**
*Versión: 2.0*
*Última actualización: Octubre 2025*
*Total de documentos: 12 (4 nuevos + 8 heredados)*