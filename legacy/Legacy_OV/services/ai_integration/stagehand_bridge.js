/**
 * Stagehand Bridge - Node.js Bridge para usar Stagehand desde Python
 * ================================================================
 * 
 * Este bridge permite usar el SDK oficial de Stagehand desde Python
 * a través de una API REST local.
 */

const { Stagehand } = require('@browserbasehq/stagehand');
const express = require('express');
const cors = require('cors');
const bodyParser = require('body-parser');
const winston = require('winston');
const path = require('path');

// Configuración del logger
const logger = winston.createLogger({
    level: 'info',
    format: winston.format.combine(
        winston.format.timestamp(),
        winston.format.json()
    ),
    transports: [
        new winston.transports.Console(),
        new winston.transports.File({ filename: 'stagehand_bridge.log' })
    ]
});

class StagehandBridge {
    constructor() {
        this.app = express();
        this.port = process.env.STAGEHAND_BRIDGE_PORT || 3001;
        this.stagehandInstances = new Map();
        this.setupMiddleware();
        this.setupRoutes();
    }

    setupMiddleware() {
        this.app.use(cors());
        this.app.use(bodyParser.json({ limit: '10mb' }));
        this.app.use(bodyParser.urlencoded({ extended: true }));
        
        // Middleware de logging
        this.app.use((req, res, next) => {
            logger.info(`${req.method} ${req.path}`, { body: req.body });
            next();
        });
    }

    setupRoutes() {
        // Health check
        this.app.get('/health', (req, res) => {
            res.json({ status: 'ok', timestamp: new Date().toISOString() });
        });

        // Crear nueva instancia de Stagehand
        this.app.post('/stagehand/create', async (req, res) => {
            try {
                const { sessionId, config = {} } = req.body;
                
                if (!sessionId) {
                    return res.status(400).json({ error: 'sessionId es requerido' });
                }

                // Configuración base de Stagehand simplificada para evitar errores de proxy
                const stagehandConfig = {
                    env: 'LOCAL',
                    headless: true,
                    verbose: 0,
                    debugDom: false
                };

                // Solo agregar configuración de IA si TODAS las credenciales están presentes
                const hasValidApiKey = config.apiKey && typeof config.apiKey === 'string' && 
                                     config.apiKey.trim() !== '' && config.apiKey !== 'test-key';
                const hasValidProjectId = config.projectId && typeof config.projectId === 'string' && 
                                         config.projectId.trim() !== '' && config.projectId !== 'test-project';
                const hasValidModelName = config.modelName && typeof config.modelName === 'string';

                if (hasValidApiKey && hasValidProjectId && hasValidModelName) {
                    stagehandConfig.modelName = config.modelName;
                    stagehandConfig.apiKey = config.apiKey;
                    stagehandConfig.projectId = config.projectId;
                    logger.info(`Configurando modelo de IA: ${config.modelName} con credenciales válidas`);
                } else {
                    logger.info('Usando configuración básica sin modelo de IA (credenciales incompletas o de prueba)');
                }

                // Crear instancia con manejo de errores mejorado
                let stagehand;
                try {
                    logger.info('Intentando crear instancia de Stagehand con configuración básica...');
                    stagehand = new Stagehand(stagehandConfig);
                    logger.info('Instancia creada, iniciando...');
                    await stagehand.init();
                    logger.info('Stagehand inicializado exitosamente');
                } catch (initError) {
                    logger.error('Error durante la inicialización de Stagehand:', initError.message);
                    
                    // Intentar con configuración ultra-mínima como fallback
                    logger.info('Intentando con configuración ultra-mínima...');
                    const ultraMinimalConfig = {
                        env: 'LOCAL',
                        headless: true
                    };
                    
                    try {
                        stagehand = new Stagehand(ultraMinimalConfig);
                        await stagehand.init();
                        logger.info('Stagehand inicializado con configuración ultra-mínima');
                    } catch (fallbackError) {
                        logger.error('Error en configuración fallback:', fallbackError.message);
                        
                        // Último intento: configuración mínima absoluta
                        logger.info('Último intento con configuración mínima absoluta...');
                        try {
                            stagehand = new Stagehand({ env: 'LOCAL' });
                            await stagehand.init();
                            logger.info('Stagehand inicializado con configuración mínima absoluta');
                        } catch (finalError) {
                            logger.error('Error final:', finalError.message);
                            throw new Error(`No se pudo inicializar Stagehand: ${finalError.message}`);
                        }
                    }
                }
                
                this.stagehandInstances.set(sessionId, stagehand);
                
                logger.info(`Stagehand instance created for session: ${sessionId}`);
                res.json({ 
                    success: true, 
                    sessionId,
                    message: 'Instancia de Stagehand creada exitosamente',
                    config: {
                        modelName: stagehandConfig.modelName || 'default',
                        hasApiKey: !!stagehandConfig.apiKey,
                        projectId: stagehandConfig.projectId || 'none'
                    }
                });
            } catch (error) {
                logger.error('Error creating Stagehand instance:', error);
                res.status(500).json({ 
                    error: error.message,
                    details: 'Error al crear instancia de Stagehand. Verifique la configuración.'
                });
            }
        });

        // Navegar a una URL
        this.app.post('/stagehand/:sessionId/navigate', async (req, res) => {
            try {
                const { sessionId } = req.params;
                const { url } = req.body;
                
                if (!url) {
                    return res.status(400).json({ error: 'URL es requerida' });
                }
                
                const stagehand = this.stagehandInstances.get(sessionId);
                if (!stagehand) {
                    return res.status(404).json({ error: 'Sesión no encontrada' });
                }

                await stagehand.page.goto(url);
                
                res.json({ 
                    success: true, 
                    message: `Navegado a ${url}` 
                });
            } catch (error) {
                logger.error('Error navigating:', error);
                res.status(500).json({ error: error.message });
            }
        });

        // Realizar acción con instrucción en lenguaje natural
        this.app.post('/stagehand/:sessionId/act', async (req, res) => {
            try {
                const { sessionId } = req.params;
                const { instruction, options = {} } = req.body;
                
                if (!instruction) {
                    return res.status(400).json({ error: 'Instrucción es requerida' });
                }
                
                const stagehand = this.stagehandInstances.get(sessionId);
                if (!stagehand) {
                    return res.status(404).json({ error: 'Sesión no encontrada' });
                }

                const result = await stagehand.act({
                    action: instruction,
                    ...options
                });
                
                res.json({ 
                    success: true, 
                    result,
                    message: `Acción ejecutada: ${instruction}` 
                });
            } catch (error) {
                logger.error('Error performing action:', error);
                res.status(500).json({ error: error.message });
            }
        });

        // Extraer información de la página
        this.app.post('/stagehand/:sessionId/extract', async (req, res) => {
            try {
                const { sessionId } = req.params;
                const { instruction, schema } = req.body;
                
                if (!instruction) {
                    return res.status(400).json({ error: 'Instrucción de extracción es requerida' });
                }
                
                const stagehand = this.stagehandInstances.get(sessionId);
                if (!stagehand) {
                    return res.status(404).json({ error: 'Sesión no encontrada' });
                }

                const result = await stagehand.extract({
                    instruction,
                    schema
                });
                
                res.json({ 
                    success: true, 
                    data: result,
                    message: 'Extracción completada exitosamente' 
                });
            } catch (error) {
                logger.error('Error extracting data:', error);
                res.status(500).json({ error: error.message });
            }
        });

        // Observar cambios en la página
        this.app.post('/stagehand/:sessionId/observe', async (req, res) => {
            try {
                const { sessionId } = req.params;
                const { instruction } = req.body;
                
                if (!instruction) {
                    return res.status(400).json({ error: 'Instrucción de observación es requerida' });
                }
                
                const stagehand = this.stagehandInstances.get(sessionId);
                if (!stagehand) {
                    return res.status(404).json({ error: 'Sesión no encontrada' });
                }

                const result = await stagehand.observe({
                    instruction
                });
                
                res.json({ 
                    success: true, 
                    observation: result,
                    message: 'Observación completada' 
                });
            } catch (error) {
                logger.error('Error observing:', error);
                res.status(500).json({ error: error.message });
            }
        });

        // Obtener información de la sesión
        this.app.get('/stagehand/:sessionId/info', (req, res) => {
            try {
                const { sessionId } = req.params;
                const stagehand = this.stagehandInstances.get(sessionId);
                
                if (!stagehand) {
                    return res.status(404).json({ error: 'Sesión no encontrada' });
                }

                res.json({
                    success: true,
                    sessionId,
                    status: 'active',
                    message: 'Sesión activa y funcionando'
                });
            } catch (error) {
                logger.error('Error getting session info:', error);
                res.status(500).json({ error: error.message });
            }
        });

        // Cerrar sesión
        this.app.delete('/stagehand/:sessionId', async (req, res) => {
            try {
                const { sessionId } = req.params;
                const stagehand = this.stagehandInstances.get(sessionId);
                
                if (!stagehand) {
                    return res.status(404).json({ error: 'Sesión no encontrada' });
                }

                await stagehand.close();
                this.stagehandInstances.delete(sessionId);
                
                logger.info(`Session closed: ${sessionId}`);
                res.json({ 
                    success: true, 
                    message: 'Sesión cerrada exitosamente' 
                });
            } catch (error) {
                logger.error('Error closing session:', error);
                res.status(500).json({ error: error.message });
            }
        });

        // Listar sesiones activas
        this.app.get('/stagehand/sessions', (req, res) => {
            try {
                const sessions = Array.from(this.stagehandInstances.keys());
                res.json({
                    success: true,
                    sessions,
                    count: sessions.length,
                    message: `${sessions.length} sesiones activas`
                });
            } catch (error) {
                logger.error('Error listing sessions:', error);
                res.status(500).json({ error: error.message });
            }
        });
    }

    start() {
        this.app.listen(this.port, () => {
            logger.info(`Stagehand Bridge iniciado en puerto ${this.port}`);
            console.log(`🚀 Stagehand Bridge corriendo en http://localhost:${this.port}`);
            console.log(`📊 Health check: http://localhost:${this.port}/health`);
            console.log(`📖 Documentación disponible en /docs`);
        });
    }
}

// Iniciar el bridge
const bridge = new StagehandBridge();
bridge.start();

module.exports = StagehandBridge;