#!/usr/bin/env python3
"""
ExtractorMerc Afinia - Extractores Mercurio para Afinia
======================================================

Módulo que contiene todos los extractores modulares de Mercurio
específicos para la empresa Afinia.
"""

from .mercurio_afinia_modular import MercurioAfiniaModular, extract_afinia_mercurio

__all__ = ['MercurioAfiniaModular', 'extract_afinia_mercurio']
