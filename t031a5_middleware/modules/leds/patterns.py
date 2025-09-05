#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
LED Patterns - Biblioteca de Padrões Visuais

Contém definições e implementações de padrões visuais
para os LEDs do robô G1.
"""

import asyncio
import logging
import math
import time
import colorsys
from typing import Dict, Any, List, Tuple, Optional, Callable
from dataclasses import dataclass
from enum import Enum, auto

logger = logging.getLogger(__name__)

class PatternType(Enum):
    """Tipos de padrão"""
    STATIC = auto()        # Estático
    ANIMATED = auto()      # Animado
    REACTIVE = auto()      # Reativo a eventos
    PROCEDURAL = auto()    # Gerado proceduralmente

@dataclass
class PatternDefinition:
    """Definição de um padrão LED"""
    name: str
    description: str
    type: PatternType
    mode: str  # breathing, pulse, wave, etc.
    duration: float
    parameters: Dict[str, Any]
    frames: Optional[List[Tuple[int, int, int]]] = None
    generator: Optional[Callable] = None

class LEDPatterns:
    """Biblioteca de padrões LED"""
    
    def __init__(self, config):
        self.config = config
        self.patterns: Dict[str, PatternDefinition] = {}
        self.is_initialized = False
        
        logger.info("LEDPatterns inicializado")
    
    async def initialize(self) -> bool:
        """Inicializa biblioteca de padrões"""
        try:
            # Carregar padrões predefinidos
            self._load_builtin_patterns()
            
            # TODO: Carregar padrões customizados de arquivos
            # await self._load_custom_patterns()
            
            self.is_initialized = True
            logger.info(f"Biblioteca de padrões carregada: {len(self.patterns)} padrões")
            return True
            
        except Exception as e:
            logger.error(f"Erro na inicialização dos padrões: {e}")
            return False
    
    def _load_builtin_patterns(self) -> None:
        """Carrega padrões predefinidos"""
        # Padrão de respiração
        self.patterns["breathing"] = PatternDefinition(
            name="breathing",
            description="Respiração suave",
            type=PatternType.ANIMATED,
            mode="breathing",
            duration=4.0,
            parameters={
                "cycle_time": 2.0,
                "min_intensity": 0.1,
                "max_intensity": 1.0
            }
        )
        
        # Padrão de pulso
        self.patterns["pulse"] = PatternDefinition(
            name="pulse",
            description="Pulso rápido",
            type=PatternType.ANIMATED,
            mode="pulse",
            duration=3.0,
            parameters={
                "cycle_time": 0.5,
                "intensity_curve": "quadratic"
            }
        )
        
        # Padrão de onda
        self.patterns["wave"] = PatternDefinition(
            name="wave",
            description="Onda de cores",
            type=PatternType.ANIMATED,
            mode="wave",
            duration=4.0,
            parameters={
                "cycle_time": 1.5,
                "phase_shift": math.pi/3
            }
        )
        
        # Padrão de flash
        self.patterns["flash"] = PatternDefinition(
            name="flash",
            description="Flash intermitente",
            type=PatternType.ANIMATED,
            mode="flash",
            duration=2.0,
            parameters={
                "count": 5,
                "on_time": 0.2,
                "off_time": 0.2
            }
        )
        
        # Padrão arco-íris
        self.patterns["rainbow"] = PatternDefinition(
            name="rainbow",
            description="Ciclo de cores arco-íris",
            type=PatternType.PROCEDURAL,
            mode="rainbow",
            duration=6.0,
            parameters={
                "cycle_time": 3.0,
                "saturation": 1.0,
                "value": 1.0
            },
            generator=self._generate_rainbow
        )
        
        # Padrão de alerta
        self.patterns["alert"] = PatternDefinition(
            name="alert",
            description="Alerta vermelho piscante",
            type=PatternType.ANIMATED,
            mode="flash",
            duration=3.0,
            parameters={
                "count": 6,
                "on_time": 0.25,
                "off_time": 0.25,
                "color": (255, 0, 0)
            }
        )
        
        # Padrão de sucesso
        self.patterns["success"] = PatternDefinition(
            name="success",
            description="Confirmação verde",
            type=PatternType.ANIMATED,
            mode="pulse",
            duration=2.0,
            parameters={
                "cycle_time": 0.8,
                "color": (0, 255, 0),
                "pulses": 3
            }
        )
        
        # Padrão de carregamento
        self.patterns["loading"] = PatternDefinition(
            name="loading",
            description="Indicador de carregamento",
            type=PatternType.PROCEDURAL,
            mode="custom",
            duration=float('inf'),  # Infinito até ser parado
            parameters={
                "speed": 1.0,
                "color": (0, 100, 255)
            },
            generator=self._generate_loading
        )
        
        # Padrão de música
        self.patterns["music"] = PatternDefinition(
            name="music",
            description="Sincronizado com música",
            type=PatternType.REACTIVE,
            mode="custom",
            duration=float('inf'),
            parameters={
                "sensitivity": 0.5,
                "base_color": (100, 0, 255)
            },
            generator=self._generate_music_reactive
        )
    
    def _generate_rainbow(self, elapsed_time: float, parameters: Dict[str, Any]) -> Tuple[int, int, int]:
        """Gera cor do padrão arco-íris"""
        cycle_time = parameters.get("cycle_time", 3.0)
        saturation = parameters.get("saturation", 1.0)
        value = parameters.get("value", 1.0)
        
        hue = (elapsed_time / cycle_time) % 1.0
        rgb = colorsys.hsv_to_rgb(hue, saturation, value)
        
        return tuple(int(c * 255) for c in rgb)
    
    def _generate_loading(self, elapsed_time: float, parameters: Dict[str, Any]) -> Tuple[int, int, int]:
        """Gera padrão de carregamento"""
        speed = parameters.get("speed", 1.0)
        base_color = parameters.get("color", (0, 100, 255))
        
        # Criar efeito de "scanner"
        cycle_time = 2.0 / speed
        phase = (elapsed_time / cycle_time) % 1.0
        
        # Intensidade baseada em onda triangular
        if phase < 0.5:
            intensity = phase * 2
        else:
            intensity = (1 - phase) * 2
        
        return tuple(int(c * intensity) for c in base_color)
    
    def _generate_music_reactive(self, elapsed_time: float, parameters: Dict[str, Any]) -> Tuple[int, int, int]:
        """Gera padrão reativo à música"""
        # TODO: Implementar análise de áudio real
        # Por enquanto, simular reatividade
        
        base_color = parameters.get("base_color", (100, 0, 255))
        sensitivity = parameters.get("sensitivity", 0.5)
        
        # Simular "batida" musical
        beat_frequency = 2.0  # 2 Hz
        beat_intensity = (math.sin(elapsed_time * beat_frequency * 2 * math.pi) + 1) / 2
        beat_intensity = beat_intensity ** 2  # Tornar mais acentuado
        
        # Aplicar sensibilidade
        final_intensity = 0.3 + (beat_intensity * sensitivity * 0.7)
        
        return tuple(int(c * final_intensity) for c in base_color)
    
    async def execute_pattern(self, pattern_name: str, command) -> None:
        """Executa um padrão específico"""
        if pattern_name not in self.patterns:
            raise ValueError(f"Padrão não encontrado: {pattern_name}")
        
        pattern = self.patterns[pattern_name]
        
        if pattern.type == PatternType.PROCEDURAL and pattern.generator:
            await self._execute_procedural_pattern(pattern, command)
        elif pattern.type == PatternType.ANIMATED:
            await self._execute_animated_pattern(pattern, command)
        elif pattern.type == PatternType.STATIC:
            await self._execute_static_pattern(pattern, command)
        else:
            logger.warning(f"Tipo de padrão não suportado: {pattern.type}")
    
    async def _execute_procedural_pattern(self, pattern: PatternDefinition, command) -> None:
        """Executa padrão procedural"""
        duration = command.duration or pattern.duration
        if duration == float('inf'):
            duration = 10.0  # Limite de segurança
        
        start_time = time.time()
        
        while time.time() - start_time < duration:
            elapsed = time.time() - start_time
            
            # Gerar cor usando função geradora
            color = pattern.generator(elapsed, pattern.parameters)
            
            # Aplicar cor (seria feito pelo LEDManager)
            logger.debug(f"Padrão {pattern.name}: RGB{color}")
            
            await asyncio.sleep(1/30)  # 30 FPS
    
    async def _execute_animated_pattern(self, pattern: PatternDefinition, command) -> None:
        """Executa padrão animado"""
        # Implementação específica baseada no modo
        if pattern.mode == "breathing":
            await self._execute_breathing_pattern(pattern, command)
        elif pattern.mode == "pulse":
            await self._execute_pulse_pattern(pattern, command)
        elif pattern.mode == "wave":
            await self._execute_wave_pattern(pattern, command)
        elif pattern.mode == "flash":
            await self._execute_flash_pattern(pattern, command)
        else:
            logger.warning(f"Modo de padrão não implementado: {pattern.mode}")
    
    async def _execute_static_pattern(self, pattern: PatternDefinition, command) -> None:
        """Executa padrão estático"""
        # Padrão estático simples
        duration = command.duration or pattern.duration
        await asyncio.sleep(duration)
    
    async def _execute_breathing_pattern(self, pattern: PatternDefinition, command) -> None:
        """Executa padrão de respiração"""
        duration = command.duration or pattern.duration
        cycle_time = pattern.parameters.get("cycle_time", 2.0)
        min_intensity = pattern.parameters.get("min_intensity", 0.1)
        max_intensity = pattern.parameters.get("max_intensity", 1.0)
        
        start_time = time.time()
        
        while time.time() - start_time < duration:
            elapsed = time.time() - start_time
            
            # Calcular intensidade
            cycle_phase = (elapsed / cycle_time) % 1.0
            intensity = min_intensity + (max_intensity - min_intensity) * \
                       (math.sin(cycle_phase * 2 * math.pi) + 1) / 2
            
            # Aplicar à cor do comando
            adjusted_color = tuple(int(c * intensity) for c in command.color)
            logger.debug(f"Breathing: RGB{adjusted_color}")
            
            await asyncio.sleep(1/20)  # 20 FPS
    
    async def _execute_pulse_pattern(self, pattern: PatternDefinition, command) -> None:
        """Executa padrão de pulso"""
        duration = command.duration or pattern.duration
        cycle_time = pattern.parameters.get("cycle_time", 0.5)
        
        start_time = time.time()
        
        while time.time() - start_time < duration:
            elapsed = time.time() - start_time
            
            # Pulso mais acentuado
            cycle_phase = (elapsed / cycle_time) % 1.0
            intensity = (math.sin(cycle_phase * 2 * math.pi) + 1) / 2
            intensity = intensity ** 2  # Curva quadrática
            
            adjusted_color = tuple(int(c * intensity) for c in command.color)
            logger.debug(f"Pulse: RGB{adjusted_color}")
            
            await asyncio.sleep(1/50)  # 50 FPS
    
    async def _execute_wave_pattern(self, pattern: PatternDefinition, command) -> None:
        """Executa padrão de onda"""
        duration = command.duration or pattern.duration
        cycle_time = pattern.parameters.get("cycle_time", 1.5)
        phase_shift = pattern.parameters.get("phase_shift", math.pi/3)
        
        start_time = time.time()
        
        while time.time() - start_time < duration:
            elapsed = time.time() - start_time
            
            # Onda com deslocamento de fase para cada canal
            cycle_phase = (elapsed / cycle_time) % 1.0
            
            r_intensity = (math.sin(cycle_phase * 2 * math.pi) + 1) / 2
            g_intensity = (math.sin(cycle_phase * 2 * math.pi + phase_shift) + 1) / 2
            b_intensity = (math.sin(cycle_phase * 2 * math.pi + 2 * phase_shift) + 1) / 2
            
            r, g, b = command.color
            wave_color = (
                int(r * r_intensity),
                int(g * g_intensity),
                int(b * b_intensity)
            )
            
            logger.debug(f"Wave: RGB{wave_color}")
            await asyncio.sleep(1/30)  # 30 FPS
    
    async def _execute_flash_pattern(self, pattern: PatternDefinition, command) -> None:
        """Executa padrão de flash"""
        count = pattern.parameters.get("count", 3)
        on_time = pattern.parameters.get("on_time", 0.2)
        off_time = pattern.parameters.get("off_time", 0.2)
        
        for i in range(count):
            # On
            logger.debug(f"Flash ON: RGB{command.color}")
            await asyncio.sleep(on_time)
            
            # Off
            logger.debug("Flash OFF: RGB(0, 0, 0)")
            await asyncio.sleep(off_time)
    
    async def cleanup(self) -> None:
        """Limpa recursos dos padrões"""
        logger.info("Recursos dos padrões limpos")
    
    # === Métodos Utilitários ===
    
    def has_pattern(self, pattern_name: str) -> bool:
        """Verifica se padrão existe"""
        return pattern_name in self.patterns
    
    def get_pattern_info(self, pattern_name: str) -> Dict[str, Any]:
        """Retorna informações sobre um padrão"""
        if pattern_name not in self.patterns:
            raise ValueError(f"Padrão não encontrado: {pattern_name}")
        
        pattern = self.patterns[pattern_name]
        return {
            "name": pattern.name,
            "description": pattern.description,
            "type": pattern.type.name,
            "mode": pattern.mode,
            "duration": pattern.duration,
            "parameters": pattern.parameters.copy()
        }
    
    def get_pattern_names(self) -> List[str]:
        """Retorna lista de nomes de padrões"""
        return list(self.patterns.keys())
    
    def get_patterns_by_type(self, pattern_type: PatternType) -> List[str]:
        """Retorna padrões de um tipo específico"""
        return [
            name for name, pattern in self.patterns.items()
            if pattern.type == pattern_type
        ]
    
    def add_custom_pattern(self, pattern: PatternDefinition) -> None:
        """Adiciona padrão customizado"""
        self.patterns[pattern.name] = pattern
        logger.info(f"Padrão customizado adicionado: {pattern.name}")
    
    def remove_pattern(self, pattern_name: str) -> bool:
        """Remove padrão"""
        if pattern_name in self.patterns:
            del self.patterns[pattern_name]
            logger.info(f"Padrão removido: {pattern_name}")
            return True
        return False