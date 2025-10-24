#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Configuración RDS Enterprise
============================

Configuración avanzada para conexión con base de datos RDS PostgreSQL
con pool de conexiones, SSL/TLS, monitoreo y gestión robusta.

Base de datos: ce-ia
Esquema: data_general
Tablas: ov_afinia, ov_aire

Autor: ISES | Analyst Data Jeam Paul Arcon Solano
Fecha: Octubre 2025
"""

import os
import ssl
import time
from datetime import datetime
from typing import Dict, Optional, Any, List
from urllib.parse import quote_plus
import logging

import sqlalchemy as sa
from sqlalchemy import create_engine, text, inspect, MetaData, Table, Column, Integer, String, DateTime, Boolean, Text
from sqlalchemy.engine import Engine
from sqlalchemy.exc import SQLAlchemyError, DisconnectionError, TimeoutError as SQLTimeoutError
from sqlalchemy.pool import QueuePool
from sqlalchemy.orm import sessionmaker, Session

from config.env_loader import get_rds_config, get_app_config

logger = logging.getLogger(__name__)

class RDSConnectionConfig:
    """
    Configuración avanzada para conexión RDS
    """
    
    def __init__(self):
        """Inicializar configuración RDS"""
        self.rds_config = get_rds_config()
        self.app_config = get_app_config()
        
        # Validar configuración
        self._validate_config()
        
        # Configuración de conexión
        self.connection_string = self._build_connection_string()
        self.engine_config = self._build_engine_config()
        
        # Estado de conexión
        self.engine: Optional[Engine] = None
        self.session_factory: Optional[sessionmaker] = None
        self._connection_healthy = False
        self._last_health_check = None
        
    def _validate_config(self) -> None:
        """Valida la configuración RDS"""
        required_fields = ['host', 'database', 'username', 'password']
        
        for field in required_fields:
            if not self.rds_config.get(field):
                raise ValueError(f"[2025-10-10_05:32:20][system][rds_config][_validate_config][ERROR] - Campo RDS requerido faltante: {field}")
        
        logger.info(f"[2025-10-10_05:32:20][system][rds_config][_validate_config][INFO] - Configuración RDS validada correctamente")
    
    def _build_connection_string(self) -> str:
        """Construye la cadena de conexión PostgreSQL"""
        username = quote_plus(str(self.rds_config['username']))
        password = quote_plus(str(self.rds_config['password']))
        host = self.rds_config['host']
        port = self.rds_config.get('port', 5432)
        database = self.rds_config['database']
        
        # Parámetros de conexión SSL
        ssl_params = "sslmode=require&sslcert=&sslkey=&sslrootcert="
        
        connection_string = f"postgresql://{username}:{password}@{host}:{port}/{database}?{ssl_params}"
        
        logger.debug(f"[2025-10-10_05:32:20][system][rds_config][_build_connection_string][DEBUG] - Cadena de conexión construida para host: {host}")
        
        return connection_string
    
    def _build_engine_config(self) -> Dict[str, Any]:
        """Configuración avanzada del engine SQLAlchemy"""
        return {
            # Pool de conexiones
            'poolclass': QueuePool,
            'pool_size': 10,              # Conexiones base
            'max_overflow': 20,           # Conexiones adicionales
            'pool_timeout': 30,           # Timeout para obtener conexión
            'pool_recycle': 3600,         # Reciclar conexiones cada hora
            'pool_pre_ping': True,        # Verificar conexión antes de usar
            
            # Timeouts
            'connect_args': {
                'connect_timeout': 10,
                'application_name': 'ExtractorOV_Enterprise',
                'options': '-c statement_timeout=30s'
            },
            
            # Logging de queries (solo en desarrollo)
            'echo': self.app_config.get('debug', False),
            'echo_pool': self.app_config.get('debug', False),
            
            # Opciones avanzadas
            'execution_options': {
                'autocommit': False,
                'isolation_level': 'READ_COMMITTED'
            }
        }
    
    def create_engine(self) -> Engine:
        """
        Crear engine de SQLAlchemy con configuración empresarial
        
        Returns:
            Engine configurado
        """
        try:
            logger.info("[2025-10-10_05:32:20][system][rds_config][create_engine][INFO] - Creando engine RDS")
            
            self.engine = create_engine(
                self.connection_string,
                **self.engine_config
            )
            
            # Crear factory de sesiones
            self.session_factory = sessionmaker(
                bind=self.engine,
                autoflush=False,
                autocommit=False
            )
            
            logger.info("[2025-10-10_05:32:20][system][rds_config][create_engine][INFO] - Engine RDS creado exitosamente")
            return self.engine
            
        except Exception as e:
            logger.error(f"[2025-10-10_05:32:20][system][rds_config][create_engine][ERROR] - Error creando engine: {e}")
            raise
    
    def test_connection(self) -> bool:
        """
        Probar conexión a la base de datos
        
        Returns:
            True si la conexión es exitosa
        """
        if not self.engine:
            self.create_engine()
        
        try:
            logger.info("[2025-10-10_05:32:20][system][rds_config][test_connection][INFO] - Probando conexión RDS")
            
            with self.engine.connect() as connection:
                result = connection.execute(text("SELECT 1 as test"))
                test_value = result.scalar()
                
                if test_value == 1:
                    self._connection_healthy = True
                    self._last_health_check = datetime.now()
                    logger.info("[2025-10-10_05:32:20][system][rds_config][test_connection][INFO] - Conexión RDS exitosa")
                    return True
                else:
                    logger.error("[2025-10-10_05:32:20][system][rds_config][test_connection][ERROR] - Test de conexión falló")
                    return False
                    
        except Exception as e:
            logger.error(f"[2025-10-10_05:32:20][system][rds_config][test_connection][ERROR] - Error en conexión RDS: {e}")
            self._connection_healthy = False
            return False
    
    def check_schema_and_tables(self) -> Dict[str, Any]:
        """
        Verificar existencia del esquema data_general y tablas ov_afinia/ov_aire
        
        Returns:
            Dict con estado de esquemas y tablas
        """
        if not self.engine:
            self.create_engine()
        
        result = {
            'schema_exists': False,
            'tables': {
                'ov_afinia': False,
                'ov_aire': False
            },
            'error': None
        }
        
        try:
            with self.engine.connect() as connection:
                # Verificar esquema data_general
                schema_query = text("""
                    SELECT schema_name 
                    FROM information_schema.schemata 
                    WHERE schema_name = 'data_general'
                """)
                schema_result = connection.execute(schema_query).fetchone()
                result['schema_exists'] = schema_result is not None
                
                if result['schema_exists']:
                    # Verificar tablas
                    table_query = text("""
                        SELECT table_name 
                        FROM information_schema.tables 
                        WHERE table_schema = 'data_general' 
                        AND table_name IN ('ov_afinia', 'ov_aire')
                    """)
                    table_results = connection.execute(table_query).fetchall()
                    existing_tables = [row[0] for row in table_results]
                    
                    result['tables']['ov_afinia'] = 'ov_afinia' in existing_tables
                    result['tables']['ov_aire'] = 'ov_aire' in existing_tables
                
                logger.info(f"[2025-10-10_05:32:20][system][rds_config][check_schema_and_tables][INFO] - Verificación completada: esquema={result['schema_exists']}, tablas={result['tables']}")
                
        except Exception as e:
            result['error'] = str(e)
            logger.error(f"[2025-10-10_05:32:20][system][rds_config][check_schema_and_tables][ERROR] - Error verificando esquemas: {e}")
        
        return result
    
    def create_schema_and_tables(self) -> bool:
        """
        Crear esquema data_general y tablas ov_afinia/ov_aire si no existen
        
        Returns:
            True si la creación fue exitosa
        """
        if not self.engine:
            self.create_engine()
        
        try:
            logger.info("[2025-10-10_05:32:20][system][rds_config][create_schema_and_tables][INFO] - Creando esquema y tablas")
            
            with self.engine.begin() as connection:
                # Crear esquema data_general
                connection.execute(text("CREATE SCHEMA IF NOT EXISTS data_general"))
                logger.info("[2025-10-10_05:32:20][system][rds_config][create_schema_and_tables][INFO] - Esquema data_general creado")
                
                # DDL para tabla ov_afinia
                afinia_ddl = text("""
                    CREATE TABLE IF NOT EXISTS data_general.ov_afinia (
                        id SERIAL PRIMARY KEY,
                        numero_radicado VARCHAR(50) UNIQUE NOT NULL,
                        fecha TIMESTAMP NOT NULL,
                        estado_solicitud VARCHAR(100),
                        tipo_pqr VARCHAR(200),
                        nic VARCHAR(20),
                        nombres_apellidos VARCHAR(200),
                        telefono VARCHAR(20),
                        celular VARCHAR(20),
                        correo_electronico VARCHAR(100),
                        documento_identidad VARCHAR(20),
                        canal_respuesta VARCHAR(100),
                        hash_registro VARCHAR(64) UNIQUE,
                        fecha_extraccion TIMESTAMP DEFAULT NOW(),
                        archivos_s3_urls JSONB,
                        procesado_flag BOOLEAN DEFAULT FALSE,
                        archivo_origen VARCHAR(200),
                        warnings TEXT,
                        created_at TIMESTAMP DEFAULT NOW(),
                        updated_at TIMESTAMP DEFAULT NOW()
                    )
                """)
                
                # DDL para tabla ov_aire
                aire_ddl = text("""
                    CREATE TABLE IF NOT EXISTS data_general.ov_aire (
                        id SERIAL PRIMARY KEY,
                        numero_radicado VARCHAR(50) UNIQUE NOT NULL,
                        fecha TIMESTAMP NOT NULL,
                        estado_solicitud VARCHAR(100),
                        tipo_pqr VARCHAR(200),
                        nic VARCHAR(20),
                        nombres_apellidos VARCHAR(200),
                        telefono VARCHAR(20),
                        celular VARCHAR(20),
                        correo_electronico VARCHAR(100),
                        documento_identidad VARCHAR(20),
                        canal_respuesta VARCHAR(100),
                        hash_registro VARCHAR(64) UNIQUE,
                        fecha_extraccion TIMESTAMP DEFAULT NOW(),
                        archivos_s3_urls JSONB,
                        procesado_flag BOOLEAN DEFAULT FALSE,
                        archivo_origen VARCHAR(200),
                        warnings TEXT,
                        created_at TIMESTAMP DEFAULT NOW(),
                        updated_at TIMESTAMP DEFAULT NOW()
                    )
                """)
                
                # Ejecutar DDLs
                connection.execute(afinia_ddl)
                connection.execute(aire_ddl)
                
                # Crear índices
                indices = [
                    "CREATE INDEX IF NOT EXISTS idx_ov_afinia_numero_radicado ON data_general.ov_afinia (numero_radicado)",
                    "CREATE INDEX IF NOT EXISTS idx_ov_afinia_fecha ON data_general.ov_afinia (fecha)",
                    "CREATE INDEX IF NOT EXISTS idx_ov_afinia_hash ON data_general.ov_afinia (hash_registro)",
                    "CREATE INDEX IF NOT EXISTS idx_ov_aire_numero_radicado ON data_general.ov_aire (numero_radicado)",
                    "CREATE INDEX IF NOT EXISTS idx_ov_aire_fecha ON data_general.ov_aire (fecha)",
                    "CREATE INDEX IF NOT EXISTS idx_ov_aire_hash ON data_general.ov_aire (hash_registro)"
                ]
                
                for index_sql in indices:
                    connection.execute(text(index_sql))
                
                logger.info("[2025-10-10_05:32:20][system][rds_config][create_schema_and_tables][INFO] - Tablas e índices creados exitosamente")
                return True
                
        except Exception as e:
            logger.error(f"[2025-10-10_05:32:20][system][rds_config][create_schema_and_tables][ERROR] - Error creando esquemas: {e}")
            return False
    
    def get_session(self) -> Session:
        """
        Obtener sesión de base de datos
        
        Returns:
            Sesión SQLAlchemy
        """
        if not self.session_factory:
            self.create_engine()
        
        return self.session_factory()
    
    def health_check(self) -> Dict[str, Any]:
        """
        Verificación completa de salud de la conexión
        
        Returns:
            Dict con métricas de salud
        """
        health_info = {
            'timestamp': datetime.now().isoformat(),
            'connection_healthy': False,
            'response_time_ms': None,
            'pool_info': None,
            'error': None
        }
        
        try:
            start_time = time.time()
            
            # Test básico de conexión
            is_healthy = self.test_connection()
            health_info['connection_healthy'] = is_healthy
            health_info['response_time_ms'] = round((time.time() - start_time) * 1000, 2)
            
            # Información del pool
            if self.engine:
                pool = self.engine.pool
                health_info['pool_info'] = {
                    'size': pool.size(),
                    'checked_in': pool.checkedin(),
                    'checked_out': pool.checkedout(),
                    'overflow': pool.overflow(),
                    'invalid': pool.invalid()
                }
            
        except Exception as e:
            health_info['error'] = str(e)
            logger.error(f"[2025-10-10_05:32:20][system][rds_config][health_check][ERROR] - Error en health check: {e}")
        
        return health_info
    
    def close_connections(self) -> None:
        """Cerrar todas las conexiones"""
        try:
            if self.engine:
                self.engine.dispose()
                logger.info("[2025-10-10_05:32:20][system][rds_config][close_connections][INFO] - Conexiones RDS cerradas")
        except Exception as e:
            logger.error(f"[2025-10-10_05:32:20][system][rds_config][close_connections][ERROR] - Error cerrando conexiones: {e}")


class RDSConnectionManager:
    """
    Gestor singleton para conexión RDS
    """
    
    _instance = None
    _config: Optional[RDSConnectionConfig] = None
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(RDSConnectionManager, cls).__new__(cls)
        return cls._instance
    
    def get_config(self) -> RDSConnectionConfig:
        """
        Obtener configuración RDS (singleton)
        
        Returns:
            Configuración RDS
        """
        if self._config is None:
            self._config = RDSConnectionConfig()
        return self._config
    
    def get_engine(self) -> Engine:
        """
        Obtener engine RDS
        
        Returns:
            Engine SQLAlchemy
        """
        config = self.get_config()
        if not config.engine:
            config.create_engine()
        return config.engine
    
    def get_session(self) -> Session:
        """
        Obtener sesión RDS
        
        Returns:
            Sesión SQLAlchemy
        """
        config = self.get_config()
        return config.get_session()
    
    def test_connection(self) -> bool:
        """Test de conexión"""
        config = self.get_config()
        return config.test_connection()
    
    def setup_database(self) -> bool:
        """
        Configurar base de datos completa (esquema + tablas)
        
        Returns:
            True si la configuración fue exitosa
        """
        config = self.get_config()
        
        # Verificar estado actual
        check_result = config.check_schema_and_tables()
        
        if check_result['error']:
            logger.error(f"[2025-10-10_05:32:20][system][rds_manager][setup_database][ERROR] - Error verificando BD: {check_result['error']}")
            return False
        
        # Crear lo que falta
        if not check_result['schema_exists'] or not all(check_result['tables'].values()):
            logger.info("[2025-10-10_05:32:20][system][rds_manager][setup_database][INFO] - Creando esquemas y tablas faltantes")
            return config.create_schema_and_tables()
        else:
            logger.info("[2025-10-10_05:32:20][system][rds_manager][setup_database][INFO] - BD ya configurada correctamente")
            return True


# Funciones de conveniencia

def get_rds_engine() -> Engine:
    """
    Obtener engine RDS configurado
    
    Returns:
        Engine SQLAlchemy
    """
    manager = RDSConnectionManager()
    return manager.get_engine()


def get_rds_session() -> Session:
    """
    Obtener sesión RDS
    
    Returns:
        Sesión SQLAlchemy
    """
    manager = RDSConnectionManager()
    return manager.get_session()


def test_rds_connection() -> bool:
    """
    Test rápido de conexión RDS
    
    Returns:
        True si la conexión es exitosa
    """
    manager = RDSConnectionManager()
    return manager.test_connection()


def setup_rds_database() -> bool:
    """
    Configurar base de datos RDS completa
    
    Returns:
        True si la configuración fue exitosa
    """
    manager = RDSConnectionManager()
    return manager.setup_database()


if __name__ == "__main__":
    # Test de configuración RDS
    logger.info("[2025-10-10_05:32:20][system][rds_config][main][INFO] - Iniciando test de configuración RDS")
    
    try:
        manager = RDSConnectionManager()
        config = manager.get_config()
        
        print("=" * 60)
        print("TEST DE CONFIGURACIÓN RDS")
        print("=" * 60)
        
        # Test de conexión
        print("1. Probando conexión...")
        is_connected = manager.test_connection()
        print(f"   Conexión: {'[EMOJI_REMOVIDO] EXITOSA' if is_connected else '[EMOJI_REMOVIDO] FALLIDA'}")
        
        if is_connected:
            # Verificar esquemas
            print("2. Verificando esquemas y tablas...")
            check_result = config.check_schema_and_tables()
            print(f"   Esquema data_general: {'[EMOJI_REMOVIDO] Existe' if check_result['schema_exists'] else '[EMOJI_REMOVIDO] No existe'}")
            print(f"   Tabla ov_afinia: {'[EMOJI_REMOVIDO] Existe' if check_result['tables']['ov_afinia'] else '[EMOJI_REMOVIDO] No existe'}")
            print(f"   Tabla ov_aire: {'[EMOJI_REMOVIDO] Existe' if check_result['tables']['ov_aire'] else '[EMOJI_REMOVIDO] No existe'}")
            
            # Setup automático si es necesario
            if not check_result['schema_exists'] or not all(check_result['tables'].values()):
                print("3. Configurando base de datos...")
                setup_success = manager.setup_database()
                print(f"   Setup: {'[EMOJI_REMOVIDO] EXITOSO' if setup_success else '[EMOJI_REMOVIDO] FALLIDO'}")
            else:
                print("3. Base de datos ya configurada [EMOJI_REMOVIDO]")
            
            # Health check
            print("4. Health check...")
            health = config.health_check()
            print(f"   Estado: {'[EMOJI_REMOVIDO] SALUDABLE' if health['connection_healthy'] else '[EMOJI_REMOVIDO] PROBLEMA'}")
            print(f"   Tiempo respuesta: {health['response_time_ms']}ms")
            
            if health['pool_info']:
                pool = health['pool_info']
                print(f"   Pool conexiones: {pool['checked_out']}/{pool['size']} activas")
        
        print("\n" + "=" * 60)
        
    except Exception as e:
        print(f"ERROR: {e}")
        logger.error(f"[2025-10-10_05:32:20][system][rds_config][main][ERROR] - Error en test: {e}")