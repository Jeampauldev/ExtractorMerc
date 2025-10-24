# 🔧 Guía Completa: Solución del Problema de NPM en Windows

## 📋 Resumen del Problema

**Síntoma:** Cada vez que se ejecuta `npm`, aparece una ventana emergente preguntando "¿Con qué programa desea abrir este archivo?"

**Causa:** Existe un archivo conflictivo llamado `npm` en `C:\Windows\system32\` que interfiere con el npm real de Node.js.

## 🎯 Solución Permanente

### Opción 1: Script Automático (Recomendado)

1. **Ejecutar como Administrador:**
   ```powershell
   # Navegar al directorio del proyecto
   cd "C:\00_Project_Dev\ExtractorOV_Modular"
   
   # Ejecutar el script de solución
   Start-Process PowerShell -ArgumentList "-ExecutionPolicy Bypass -File `"scripts\fix_npm_permanently.ps1`"" -Verb RunAs
   ```

2. **El script realizará automáticamente:**
   - ✅ Verificación de permisos de administrador
   - ✅ Detección del archivo conflictivo
   - ✅ Toma de propiedad del archivo
   - ✅ Asignación de permisos
   - ✅ Eliminación del archivo conflictivo
   - ✅ Verificación de que npm funciona correctamente

### Opción 2: Solución Manual

Si prefieres hacerlo manualmente:

1. **Abrir PowerShell como Administrador**
2. **Ejecutar los siguientes comandos:**
   ```powershell
   # Tomar propiedad del archivo
   takeown /f "C:\Windows\system32\npm" /a
   
   # Asignar permisos completos
   icacls "C:\Windows\system32\npm" /grant administrators:F
   
   # Eliminar el archivo conflictivo
   Remove-Item "C:\Windows\system32\npm" -Force
   ```

3. **Verificar que npm funciona:**
   ```powershell
   npm --version
   ```

## 🔍 Diagnóstico del Problema

### Verificar si el problema existe:
```powershell
# Verificar si existe el archivo conflictivo
Test-Path "C:\Windows\system32\npm"

# Ver qué npm está siendo utilizado
Get-Command npm | Select-Object Name, Source, CommandType

# Verificar las rutas de Node.js en PATH
$env:PATH -split ';' | Where-Object { $_ -like '*node*' }
```

### Ubicaciones correctas de Node.js:
- **Node.js:** `C:\Program Files\nodejs\`
- **NPM real:** `C:\Program Files\nodejs\npm.cmd`
- **Archivo conflictivo:** `C:\Windows\system32\npm` (debe eliminarse)

## 🚀 Verificación Post-Solución

Después de aplicar la solución, verifica que todo funciona correctamente:

```powershell
# Verificar versiones
node --version
npm --version

# Probar instalación de paquetes
npm init -y
npm install express --save

# Verificar que no aparecen ventanas emergentes
npm list
```

## 📊 Dashboard de Servicios

Se ha creado un dashboard web para monitorear los servicios:

**Ubicación:** `src/services/ai_integration/service_dashboard.html`

**Características:**
- 🎭 Monitoreo de Stagehand Bridge
- 💎 Estado de integración con Gemini
- ⚙️ Información del sistema
- 🎮 Controles de servicios
- 📋 Registro de actividad en tiempo real

**Para usar el dashboard:**
1. Abrir `service_dashboard.html` en cualquier navegador
2. El dashboard verificará automáticamente el estado de los servicios
3. Usar los controles para gestionar Stagehand
4. Probar endpoints directamente desde la interfaz

## 🔄 Prevención de Problemas Futuros

### Para evitar que el problema se repita:

1. **No instalar software que modifique system32**
2. **Verificar PATH regularmente:**
   ```powershell
   $env:PATH -split ';' | Where-Object { $_ -like '*node*' }
   ```

3. **Usar el script de verificación periódicamente:**
   ```powershell
   # Crear un script de verificación rápida
   if (Test-Path "C:\Windows\system32\npm") {
       Write-Host "⚠️ ADVERTENCIA: Archivo npm conflictivo detectado" -ForegroundColor Red
   } else {
       Write-Host "✅ NPM configurado correctamente" -ForegroundColor Green
   }
   ```

## 🛠️ Solución de Problemas Adicionales

### Si npm sigue sin funcionar después de la solución:

1. **Verificar instalación de Node.js:**
   ```powershell
   # Reinstalar Node.js si es necesario
   # Descargar desde: https://nodejs.org/
   ```

2. **Limpiar caché de npm:**
   ```powershell
   npm cache clean --force
   ```

3. **Verificar variables de entorno:**
   ```powershell
   # Verificar que Node.js esté en PATH
   echo $env:PATH
   ```

### Si aparecen errores de permisos:

1. **Ejecutar siempre como administrador para cambios del sistema**
2. **Verificar que el usuario tiene permisos en la carpeta de Node.js**
3. **Considerar usar npm con --global flag para instalaciones globales**

## 📞 Soporte

Si el problema persiste después de seguir esta guía:

1. **Verificar logs del sistema**
2. **Revisar el dashboard de servicios**
3. **Ejecutar diagnósticos completos**
4. **Considerar reinstalación completa de Node.js**

---

**Nota:** Esta solución ha sido probada en Windows 10/11 con Node.js v22.17.1 y npm v10.9.2.

**Última actualización:** $(Get-Date -Format "yyyy-MM-dd HH:mm:ss")