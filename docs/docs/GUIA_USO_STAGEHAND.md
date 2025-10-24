# Guía de Uso - Stagehand + Gemini Integration
## ExtractorOV Modular

---

## 🚀 Inicio Rápido

### 1. Iniciar el Sistema

```powershell
# Navegar al directorio
cd C:\00_Project_Dev\ExtractorOV_Modular\src\services\ai_integration

# Iniciar Stagehand Bridge
node stagehand_bridge.js
```

### 2. Verificar Estado
```powershell
# Verificar que el servicio esté activo
Invoke-WebRequest -Uri "http://localhost:3001/health"
```

### 3. Abrir Dashboard
Abrir en navegador: `src/services/ai_integration/service_dashboard.html`

---

## 📡 API Reference

### Health Check
**Endpoint:** `GET /health`  
**Descripción:** Verifica el estado del servicio

```javascript
// Ejemplo de uso
const response = await fetch('http://localhost:3001/health');
const data = await response.json();
console.log(data); // { status: "ok", timestamp: "..." }
```

### Crear Sesión Stagehand
**Endpoint:** `POST /stagehand/create`  
**Descripción:** Crea una nueva instancia de Stagehand con configuración Gemini

```javascript
const sessionConfig = {
  sessionId: 'mi-sesion-unica',
  config: {
    modelName: 'gemini-pro',
    apiKey: 'tu-api-key-gemini',
    verbose: 1,
    headless: true,
    browserOptions: {
      args: ['--no-sandbox', '--disable-dev-shm-usage']
    }
  }
};

const response = await fetch('http://localhost:3001/stagehand/create', {
  method: 'POST',
  headers: { 'Content-Type': 'application/json' },
  body: JSON.stringify(sessionConfig)
});
```

### Navegación Web
**Endpoint:** `POST /stagehand/:sessionId/navigate`  
**Descripción:** Navega a una URL específica

```javascript
const navigationData = {
  url: 'https://example.com'
};

const response = await fetch('http://localhost:3001/stagehand/mi-sesion-unica/navigate', {
  method: 'POST',
  headers: { 'Content-Type': 'application/json' },
  body: JSON.stringify(navigationData)
});
```

---

## 🎯 Casos de Uso Prácticos

### Caso 1: Extracción de Datos de Formulario

```javascript
async function extraerDatosFormulario() {
  // 1. Crear sesión
  const sessionId = 'extractor-formulario-' + Date.now();
  
  await fetch('http://localhost:3001/stagehand/create', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({
      sessionId: sessionId,
      config: {
        modelName: 'gemini-pro',
        apiKey: process.env.GEMINI_API_KEY,
        headless: false, // Para ver el proceso
        verbose: 2
      }
    })
  });

  // 2. Navegar a la página
  await fetch(`http://localhost:3001/stagehand/${sessionId}/navigate`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({
      url: 'https://ejemplo-formulario.com'
    })
  });

  // 3. Interactuar con elementos (implementar endpoints adicionales)
  // await stagehand.act("Llenar el campo nombre con 'Juan Pérez'");
  // await stagehand.act("Hacer clic en el botón enviar");
}
```

### Caso 2: Monitoreo de Precios

```javascript
async function monitorearPrecios() {
  const sessionId = 'monitor-precios';
  
  // Crear sesión para monitoreo
  await fetch('http://localhost:3001/stagehand/create', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({
      sessionId: sessionId,
      config: {
        modelName: 'gemini-pro',
        apiKey: process.env.GEMINI_API_KEY,
        headless: true,
        verbose: 1
      }
    })
  });

  // Navegar a sitio de e-commerce
  await fetch(`http://localhost:3001/stagehand/${sessionId}/navigate`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({
      url: 'https://tienda-online.com/producto/123'
    })
  });

  // Extraer precio (requiere endpoint adicional para extract)
}
```

### Caso 3: Automatización de Reportes

```javascript
async function generarReporteAutomatico() {
  const sessionId = 'reporte-automatico';
  
  // Configuración para reporte
  await fetch('http://localhost:3001/stagehand/create', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({
      sessionId: sessionId,
      config: {
        modelName: 'gemini-pro',
        apiKey: process.env.GEMINI_API_KEY,
        headless: true,
        verbose: 0 // Silencioso para reportes
      }
    })
  });

  // Navegar a dashboard interno
  await fetch(`http://localhost:3001/stagehand/${sessionId}/navigate`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({
      url: 'https://dashboard-interno.com/reportes'
    })
  });
}
```

---

## 🔧 Configuración Avanzada

### Variables de Entorno Recomendadas

```bash
# .env file
GEMINI_API_KEY=tu_api_key_aqui
STAGEHAND_PORT=3001
STAGEHAND_HEADLESS=true
STAGEHAND_VERBOSE=1
```

### Configuración de Gemini

```yaml
# credenciales_gemini.yml
gemini:
  api_key: "tu-api-key"
  model: "gemini-pro"
  temperature: 0.1
  max_tokens: 2048
  timeout: 30000
```

### Opciones del Navegador

```javascript
const browserOptions = {
  headless: true,
  args: [
    '--no-sandbox',
    '--disable-dev-shm-usage',
    '--disable-gpu',
    '--window-size=1920,1080'
  ],
  defaultViewport: {
    width: 1920,
    height: 1080
  }
};
```

---

## 🐛 Troubleshooting

### Problemas Comunes

#### 1. Error de Conexión
```
Error: connect ECONNREFUSED 127.0.0.1:3001
```
**Solución:** Verificar que Stagehand Bridge esté ejecutándose
```powershell
node stagehand_bridge.js
```

#### 2. Error de API Key
```
Error: Invalid API key for Gemini
```
**Solución:** Verificar configuración de credenciales
```javascript
// Verificar que la API key esté configurada
console.log(process.env.GEMINI_API_KEY ? 'API Key configurada' : 'API Key faltante');
```

#### 3. Error de Puerto Ocupado
```
Error: listen EADDRINUSE :::3001
```
**Solución:** Cambiar puerto o terminar proceso existente
```powershell
# Encontrar proceso en puerto 3001
netstat -ano | findstr :3001

# Terminar proceso (reemplazar PID)
taskkill /PID <PID> /F
```

#### 4. Error de Navegación
```
Error: Navigation timeout
```
**Solución:** Aumentar timeout o verificar URL
```javascript
const config = {
  // ... otras opciones
  timeout: 60000, // 60 segundos
  waitUntil: 'networkidle0'
};
```

---

## 📊 Monitoreo y Logs

### Logs del Sistema
```powershell
# Ver logs en tiempo real
Get-Content -Path "stagehand_bridge.log" -Wait

# Filtrar errores
Get-Content -Path "stagehand_bridge.log" | Select-String "ERROR"
```

### Métricas de Rendimiento
```javascript
// Ejemplo de monitoreo básico
async function verificarRendimiento() {
  const inicio = Date.now();
  
  const response = await fetch('http://localhost:3001/health');
  
  const tiempoRespuesta = Date.now() - inicio;
  console.log(`Tiempo de respuesta: ${tiempoRespuesta}ms`);
  
  return response.ok;
}
```

---

## 🔒 Seguridad

### Mejores Prácticas

1. **Nunca hardcodear API keys**
```javascript
// ❌ Incorrecto
const apiKey = 'AIzaSyC...';

// ✅ Correcto
const apiKey = process.env.GEMINI_API_KEY;
```

2. **Validar entrada de usuario**
```javascript
function validarURL(url) {
  try {
    new URL(url);
    return true;
  } catch {
    return false;
  }
}
```

3. **Limitar recursos**
```javascript
const config = {
  timeout: 30000, // 30 segundos máximo
  maxConcurrentSessions: 5,
  memoryLimit: '512MB'
};
```

---

## 📈 Optimización

### Rendimiento
- Usar `headless: true` para mejor rendimiento
- Implementar cache de sesiones
- Limitar sesiones concurrentes
- Monitorear uso de memoria

### Escalabilidad
- Considerar múltiples instancias
- Implementar load balancing
- Usar base de datos para estado de sesiones
- Configurar auto-scaling

---

## 🆘 Soporte

### Comandos de Diagnóstico

```powershell
# Verificar Node.js
node --version

# Verificar dependencias
npm list

# Verificar puertos
netstat -ano | findstr :3001

# Verificar procesos Node
Get-Process node
```

### Contacto y Recursos
- **Documentación Stagehand:** [GitHub Repository](https://github.com/browserbase/stagehand)
- **Documentación Gemini:** [Google AI Studio](https://ai.google.dev/)
- **Logs del sistema:** `stagehand_bridge.log`

---

*Guía creada por Sentinel Códice - Última actualización: 13 de octubre de 2025*