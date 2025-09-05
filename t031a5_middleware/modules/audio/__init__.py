#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Módulo de Áudio do Middleware t031a5

Gerencia todas as funcionalidades de áudio do robô:
- Text-to-Speech (TTS)
- Automatic Speech Recognition (ASR) 
- Controle de volume
- Reprodução de áudio PCM
- Integração com APIs de LLM
"""

from .manager import AudioManager
from .tts_engine import TTSEngine
from .asr_engine import ASREngine

__all__ = [
    "AudioManager",
    "TTSEngine",
    "ASREngine"
]