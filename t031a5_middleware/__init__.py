#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Middleware t031a5 para Robô Unitree G1

Sistema de orquestração completo para robótica humanoide,
projetado para integração multimodal e interação natural.
"""

__version__ = "1.0.0"
__author__ = "Roberto"
__description__ = "Middleware de Orquestração para Robótica Humanoide Unitree G1"

# Imports principais
from .core.orchestrator import orchestrator
from .core.config_manager import config_manager
from .core.state_machine import state_machine

__all__ = [
    "orchestrator",
    "config_manager", 
    "state_machine"
]