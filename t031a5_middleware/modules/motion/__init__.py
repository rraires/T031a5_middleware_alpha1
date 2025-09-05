#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Módulo de Movimento do Middleware t031a5

Gerencia todas as funcionalidades de movimento do robô:
- Locomoção (alto nível)
- Controle de braços e articulações (baixo nível)
- Gestos e movimentos predefinidos
- Coordenação de movimentos complexos
- Sistema de segurança e parada de emergência
"""

from .manager import MotionManager
from .high_level import HighLevelController
from .low_level import LowLevelController

__all__ = [
    "MotionManager",
    "HighLevelController",
    "LowLevelController"
]