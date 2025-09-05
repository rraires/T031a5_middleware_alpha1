#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Módulo de LEDs do Middleware t031a5

Gerencia todas as funcionalidades visuais do robô:
- Controle de LEDs RGB
- Padrões visuais e animações
- Feedback visual contextual
- Sincronização com áudio e movimento
- Indicadores de status do sistema
"""

from .manager import LEDManager
from .patterns import LEDPatterns

__all__ = [
    "LEDManager",
    "LEDPatterns"
]