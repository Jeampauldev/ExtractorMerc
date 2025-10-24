#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Servicios ExtractorOV
====================

Módulo de servicios para el procesamiento y carga de datos extraídos
por los extractores de Afinia y Aire.

Servicios disponibles:
- DatabaseService: Servicio unificado para operaciones de base de datos
- DataLoaderService: Servicio para carga masiva de archivos JSON
- S3UploaderService: Servicio para carga de archivos a AWS S3
"""

from .database_service import DatabaseService, create_database_service, DataLoadResult
from .data_loader_service import (
    DataLoaderService, 
    ProcessingStats, 
    FileProcessingResult,
    process_json_files,
    process_data_directory
)
from .s3_uploader_service import (
    S3UploaderService,
    S3UploadResult,
    S3BatchResult,
    upload_file_to_s3,
    upload_directory_to_s3
)
from .unified_s3_service import UnifiedS3Service, S3PathStructure

__all__ = [
    'DatabaseService',
    'create_database_service',
    'DataLoadResult',
    'DataLoaderService',
    'ProcessingStats',
    'FileProcessingResult',
    'process_json_files',
    'process_data_directory',
    'S3UploaderService',
    'UnifiedS3Service',
    'S3PathStructure',
    'S3UploadResult',
    'S3BatchResult',
    'upload_file_to_s3',
    'upload_directory_to_s3'
]
