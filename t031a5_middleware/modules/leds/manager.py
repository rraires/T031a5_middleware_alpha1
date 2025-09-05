#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
LEDManager - Gerenciador de LEDs do Middleware t031a5

Responsável por coordenar todo o sistema visual do robô G1,
incluindo controle de LEDs RGB, padrões visuais e feedback contextual.
"""

import asyncio
import logging
import time
import math
from typing import Optional, Dict, Any, List, Tuple, Callable
from datetime import datetime
from enum import Enum, auto
from dataclasses import dataclass
import colorsys
import sys
import os

# Adicionar path do SDK Unitree
sys.path.append(os.path.join(os.path.dirname(__file__), '../../../unitre_sdk_python'))

try:
    from unitree_sdk2py.core.channel import ChannelFactoryInitialize
    from unitree_sdk2py.g1.audio.g1_audio_client import AudioClient
except ImportError as e:
    logging.warning(f"SDK Unitree não encontrado: {e}")
    AudioClient = None

# Imports locais
from ...core.config_manager import config_manager
from ...core.state_machine import state_machine, ModuleState, RobotState
from .patterns import LEDPatterns

logger = logging.getLogger(__name__)

class LEDMode(Enum):
    """Modos de operação dos LEDs"""
    OFF = auto()           # LEDs desligados
    STATIC = auto()        # Cor estática
    BREATHING = auto()     # Respiração suave
    PULSE = auto()         # Pulso rápido
    WAVE = auto()          # Onda de cores
    RAINBOW = auto()       # Arco-íris
    FLASH = auto()         # Piscar
    CUSTOM = auto()        # Padrão customizado

class LEDPriority(Enum):
    """Prioridades de controle LED"""
    LOW = 1
    NORMAL = 2
    HIGH = 3
    EMERGENCY = 4
    SYSTEM = 5

@dataclass
class LEDCommand:
    """Comando de LED"""
    id: str
    mode: LEDMode
    priority: LEDPriority
    color: Tuple[int, int, int]  # RGB (0-255)
    duration: Optional[float] = None
    parameters: Dict[str, Any] = None
    callback: Optional[Callable] = None
    timestamp: datetime = None
    
    def __post_init__(self):
        if self.timestamp is None:
            self.timestamp = datetime.now()
        if self.parameters is None:
            self.parameters = {}

@dataclass
class LEDState:
    """Estado atual dos LEDs"""
    mode: LEDMode
    color: Tuple[int, int, int]
    brightness: float  # 0.0 a 1.0
    active_pattern: Optional[str] = None
    timestamp: datetime = None
    
    def __post_init__(self):
        if self.timestamp is None:
            self.timestamp = datetime.now()

class LEDManager:
    """Gerenciador principal do sistema de LEDs"""
    
    def __init__(self):
        self.config = config_manager.get_config().leds
        self.network_config = config_manager.get_config().network
        
        # Componentes principais
        self.audio_client: Optional[AudioClient] = None
        self.patterns: Optional[LEDPatterns] = None
        
        # Estado do módulo
        self.is_initialized = False
        self.is_running = False
        self.health = 1.0
        self.last_error = None
        
        # Estado dos LEDs
        self.current_state = LEDState(
            mode=LEDMode.OFF,
            color=(0, 0, 0),
            brightness=0.0
        )
        self.target_state: Optional[LEDState] = None
        self.current_command: Optional[LEDCommand] = None
        
        # Controle de animação
        self.animation_active = False
        self.animation_start_time = 0.0
        self.animation_frame = 0
        
        # Filas de processamento
        self.command_queue = asyncio.PriorityQueue()
        self.led_events = asyncio.Queue()
        
        # Callbacks
        self.led_callbacks: List[Callable] = []
        self.state_callbacks: List[Callable] = []
        
        # Tarefas assíncronas
        self.tasks: List[asyncio.Task] = []
        
        # Mapeamento de contextos para cores
        self.context_colors = {
            "idle": (0, 100, 255),      # Azul suave
            "listening": (0, 255, 100),  # Verde azulado
            "speaking": (100, 255, 0),   # Verde amarelado
            "thinking": (255, 200, 0),   # Amarelo
            "moving": (255, 100, 0),     # Laranja
            "error": (255, 0, 0),        # Vermelho
            "emergency": (255, 0, 255),  # Magenta
            "success": (0, 255, 0),      # Verde
            "warning": (255, 255, 0),    # Amarelo brilhante
            "calibrating": (128, 0, 255), # Roxo
            "learning": (255, 0, 128)     # Rosa
        }
        
        # Estatísticas
        self.stats = {
            "commands_executed": 0,
            "patterns_played": 0,
            "color_changes": 0,
            "led_errors": 0,
            "uptime": 0,
            "last_activity": None
        }
        
        logger.info("LEDManager inicializado")
    
    async def initialize(self) -> bool:
        """Inicializa o sistema de LEDs"""
        try:
            logger.info("Inicializando LEDManager...")
            
            # Registrar na máquina de estados
            state_machine.update_module_status(
                "led_manager", 
                ModuleState.INITIALIZING, 
                health=0.5
            )
            
            # Inicializar SDK Unitree
            if not await self._initialize_unitree_sdk():
                raise RuntimeError("Falha na inicialização do SDK Unitree")
            
            # Inicializar padrões
            self.patterns = LEDPatterns(self.config)
            await self.patterns.initialize()
            
            # Configurar brilho inicial
            await self._set_brightness(self.config.brightness / 100.0)
            
            # Registrar callbacks de estado do robô
            self._register_state_callbacks()
            
            # Marcar como inicializado
            self.is_initialized = True
            self.health = 1.0
            
            state_machine.update_module_status(
                "led_manager", 
                ModuleState.READY, 
                health=self.health
            )
            
            logger.info("LEDManager inicializado com sucesso")
            return True
            
        except Exception as e:
            logger.error(f"Erro na inicialização do LEDManager: {e}")
            self.last_error = str(e)
            self.health = 0.0
            
            state_machine.update_module_status(
                "led_manager", 
                ModuleState.ERROR, 
                health=self.health
            )
            
            return False
    
    async def _initialize_unitree_sdk(self) -> bool:
        """Inicializa o SDK Unitree para LEDs"""
        try:
            if AudioClient is None:
                logger.warning("SDK Unitree não disponível, usando modo simulação")
                return True
            
            # Usar cliente de áudio para controle de LEDs
            # (O controle de LED está integrado no AudioClient)
            self.audio_client = AudioClient()
            self.audio_client.Init()
            
            logger.info("SDK Unitree LED inicializado")
            return True
            
        except Exception as e:
            logger.error(f"Erro na inicialização do SDK Unitree: {e}")
            return False
    
    def _register_state_callbacks(self) -> None:
        """Registra callbacks para mudanças de estado do robô"""
        # Registrar callback para mudanças de estado
        state_machine.register_state_callback(
            RobotState.IDLE, 
            lambda: asyncio.create_task(self.set_context_color("idle"))
        )
        
        state_machine.register_state_callback(
            RobotState.LISTENING, 
            lambda: asyncio.create_task(self.set_context_color("listening"))
        )
        
        state_machine.register_state_callback(
            RobotState.SPEAKING, 
            lambda: asyncio.create_task(self.set_context_color("speaking"))
        )
        
        state_machine.register_state_callback(
            RobotState.MOVING, 
            lambda: asyncio.create_task(self.set_context_color("moving"))
        )
        
        state_machine.register_state_callback(
            RobotState.ERROR, 
            lambda: asyncio.create_task(self.set_context_color("error"))
        )
        
        state_machine.register_state_callback(
            RobotState.EMERGENCY_STOP, 
            lambda: asyncio.create_task(self.set_context_color("emergency"))
        )
        
        logger.info("Callbacks de estado registrados")
    
    async def start(self) -> bool:
        """Inicia o sistema de LEDs"""
        if not self.is_initialized:
            logger.error("LEDManager não foi inicializado")
            return False
        
        if self.is_running:
            logger.warning("LEDManager já está em execução")
            return True
        
        try:
            logger.info("Iniciando LEDManager...")
            
            # Iniciar tarefas assíncronas
            self.tasks = [
                asyncio.create_task(self._command_processor()),
                asyncio.create_task(self._animation_engine()),
                asyncio.create_task(self._led_monitor()),
                asyncio.create_task(self._health_monitor())
            ]
            
            self.is_running = True
            self.stats["uptime"] = time.time()
            
            # LED de inicialização
            await self.set_color((0, 255, 0), duration=1.0)  # Verde de inicialização
            
            state_machine.update_module_status(
                "led_manager", 
                ModuleState.ACTIVE, 
                health=self.health
            )
            
            logger.info("LEDManager iniciado com sucesso")
            return True
            
        except Exception as e:
            logger.error(f"Erro ao iniciar LEDManager: {e}")
            self.last_error = str(e)
            self.health = 0.0
            
            state_machine.update_module_status(
                "led_manager", 
                ModuleState.ERROR, 
                health=self.health
            )
            
            return False
    
    async def stop(self) -> bool:
        """Para o sistema de LEDs"""
        if not self.is_running:
            return True
        
        try:
            logger.info("Parando LEDManager...")
            
            # Desligar LEDs
            await self.set_color((0, 0, 0), duration=0.5)
            
            # Cancelar tarefas
            for task in self.tasks:
                if not task.done():
                    task.cancel()
            
            # Aguardar conclusão
            if self.tasks:
                await asyncio.gather(*self.tasks, return_exceptions=True)
            
            self.is_running = False
            
            state_machine.update_module_status(
                "led_manager", 
                ModuleState.READY, 
                health=self.health
            )
            
            logger.info("LEDManager parado")
            return True
            
        except Exception as e:
            logger.error(f"Erro ao parar LEDManager: {e}")
            return False
    
    async def cleanup(self) -> None:
        """Limpa recursos do sistema de LEDs"""
        try:
            logger.info("Limpando recursos do LEDManager...")
            
            # Parar se estiver rodando
            if self.is_running:
                await self.stop()
            
            # Cleanup padrões
            if self.patterns:
                await self.patterns.cleanup()
            
            # Limpar filas
            while not self.command_queue.empty():
                try:
                    self.command_queue.get_nowait()
                except asyncio.QueueEmpty:
                    break
            
            while not self.led_events.empty():
                try:
                    self.led_events.get_nowait()
                except asyncio.QueueEmpty:
                    break
            
            self.is_initialized = False
            
            logger.info("Recursos do LEDManager limpos")
            
        except Exception as e:
            logger.error(f"Erro na limpeza do LEDManager: {e}")
    
    # === Métodos de Controle de LED ===
    
    async def set_color(self, color: Tuple[int, int, int], 
                       duration: Optional[float] = None,
                       priority: LEDPriority = LEDPriority.NORMAL) -> str:
        """Define cor estática dos LEDs"""
        if not self.is_running:
            raise RuntimeError("LEDManager não está em execução")
        
        command_id = f"color_{int(time.time() * 1000)}"
        
        command = LEDCommand(
            id=command_id,
            mode=LEDMode.STATIC,
            priority=priority,
            color=color,
            duration=duration
        )
        
        await self.command_queue.put((priority.value, command))
        self.stats["last_activity"] = datetime.now().isoformat()
        
        logger.info(f"Comando de cor enfileirado: RGB{color}")
        return command_id
    
    async def set_pattern(self, pattern_name: str, 
                         color: Optional[Tuple[int, int, int]] = None,
                         duration: Optional[float] = None,
                         priority: LEDPriority = LEDPriority.NORMAL) -> str:
        """Define padrão de LED"""
        if not self.is_running:
            raise RuntimeError("LEDManager não está em execução")
        
        if not self.patterns.has_pattern(pattern_name):
            raise ValueError(f"Padrão não encontrado: {pattern_name}")
        
        command_id = f"pattern_{int(time.time() * 1000)}"
        
        # Obter modo do padrão
        pattern_info = self.patterns.get_pattern_info(pattern_name)
        mode = LEDMode[pattern_info["mode"].upper()]
        
        command = LEDCommand(
            id=command_id,
            mode=mode,
            priority=priority,
            color=color or (255, 255, 255),
            duration=duration,
            parameters={"pattern_name": pattern_name}
        )
        
        await self.command_queue.put((priority.value, command))
        self.stats["last_activity"] = datetime.now().isoformat()
        
        logger.info(f"Padrão enfileirado: {pattern_name}")
        return command_id
    
    async def set_context_color(self, context: str, 
                               priority: LEDPriority = LEDPriority.NORMAL) -> str:
        """Define cor baseada no contexto"""
        if context not in self.context_colors:
            logger.warning(f"Contexto não encontrado: {context}")
            context = "idle"
        
        color = self.context_colors[context]
        
        # Definir padrão baseado no contexto
        if context == "listening":
            return await self.set_pattern("pulse", color, priority=priority)
        elif context == "speaking":
            return await self.set_pattern("wave", color, priority=priority)
        elif context == "error" or context == "emergency":
            return await self.set_pattern("flash", color, priority=LEDPriority.EMERGENCY)
        else:
            return await self.set_color(color, priority=priority)
    
    async def flash(self, color: Tuple[int, int, int], 
                   count: int = 3, interval: float = 0.5,
                   priority: LEDPriority = LEDPriority.HIGH) -> str:
        """Pisca LEDs com cor especificada"""
        command_id = f"flash_{int(time.time() * 1000)}"
        
        command = LEDCommand(
            id=command_id,
            mode=LEDMode.FLASH,
            priority=priority,
            color=color,
            duration=count * interval * 2,  # On + Off para cada flash
            parameters={
                "count": count,
                "interval": interval
            }
        )
        
        await self.command_queue.put((priority.value, command))
        self.stats["last_activity"] = datetime.now().isoformat()
        
        logger.info(f"Flash enfileirado: {count}x RGB{color}")
        return command_id
    
    async def rainbow(self, duration: float = 5.0, 
                     priority: LEDPriority = LEDPriority.NORMAL) -> str:
        """Executa padrão arco-íris"""
        command_id = f"rainbow_{int(time.time() * 1000)}"
        
        command = LEDCommand(
            id=command_id,
            mode=LEDMode.RAINBOW,
            priority=priority,
            color=(255, 255, 255),  # Cor base (será ignorada)
            duration=duration
        )
        
        await self.command_queue.put((priority.value, command))
        self.stats["last_activity"] = datetime.now().isoformat()
        
        logger.info(f"Arco-íris enfileirado: {duration}s")
        return command_id
    
    async def turn_off(self, priority: LEDPriority = LEDPriority.NORMAL) -> str:
        """Desliga LEDs"""
        return await self.set_color((0, 0, 0), priority=priority)
    
    async def set_brightness(self, brightness: float) -> None:
        """Define brilho dos LEDs (0.0 a 1.0)"""
        brightness = max(0.0, min(1.0, brightness))
        await self._set_brightness(brightness)
        
        logger.info(f"Brilho definido: {brightness:.2f}")
    
    async def _set_brightness(self, brightness: float) -> None:
        """Define brilho interno"""
        self.current_state.brightness = brightness
        
        # Aplicar brilho à cor atual
        if self.current_state.color != (0, 0, 0):
            adjusted_color = tuple(
                int(c * brightness) for c in self.current_state.color
            )
            await self._apply_color(adjusted_color)
    
    # === Processamento de Comandos ===
    
    async def _command_processor(self) -> None:
        """Processa fila de comandos LED"""
        logger.debug("Processador de comandos LED iniciado")
        
        while self.is_running:
            try:
                # Aguardar comando com timeout
                priority, command = await asyncio.wait_for(
                    self.command_queue.get(), 
                    timeout=1.0
                )
                
                await self._execute_led_command(command)
                
            except asyncio.TimeoutError:
                continue
            except Exception as e:
                logger.error(f"Erro no processador de comandos LED: {e}")
                self.stats["led_errors"] += 1
    
    async def _execute_led_command(self, command: LEDCommand) -> None:
        """Executa um comando LED"""
        try:
            self.current_command = command
            
            logger.info(f"Executando comando LED: {command.mode.name} - {command.id}")
            
            # Executar baseado no modo
            if command.mode == LEDMode.STATIC:
                await self._execute_static_color(command)
            elif command.mode == LEDMode.BREATHING:
                await self._execute_breathing(command)
            elif command.mode == LEDMode.PULSE:
                await self._execute_pulse(command)
            elif command.mode == LEDMode.WAVE:
                await self._execute_wave(command)
            elif command.mode == LEDMode.RAINBOW:
                await self._execute_rainbow(command)
            elif command.mode == LEDMode.FLASH:
                await self._execute_flash(command)
            elif command.mode == LEDMode.CUSTOM:
                await self._execute_custom_pattern(command)
            
            # Executar callback se fornecido
            if command.callback:
                try:
                    if asyncio.iscoroutinefunction(command.callback):
                        await command.callback(command)
                    else:
                        command.callback(command)
                except Exception as e:
                    logger.error(f"Erro em callback LED: {e}")
            
            self.stats["commands_executed"] += 1
            
            # Emitir evento
            await self.led_events.put({
                "type": "command_completed",
                "command": command,
                "timestamp": datetime.now().isoformat()
            })
            
            logger.debug(f"Comando LED concluído: {command.id}")
            
        except Exception as e:
            logger.error(f"Erro na execução do comando LED: {e}")
            self.stats["led_errors"] += 1
        
        finally:
            self.current_command = None
    
    async def _execute_static_color(self, command: LEDCommand) -> None:
        """Executa cor estática"""
        await self._apply_color(command.color)
        
        if command.duration:
            await asyncio.sleep(command.duration)
    
    async def _execute_breathing(self, command: LEDCommand) -> None:
        """Executa padrão de respiração"""
        duration = command.duration or 5.0
        start_time = time.time()
        
        while time.time() - start_time < duration:
            # Calcular intensidade baseada em seno
            elapsed = time.time() - start_time
            cycle_time = 2.0  # 2 segundos por ciclo
            intensity = (math.sin(elapsed * 2 * math.pi / cycle_time) + 1) / 2
            
            # Aplicar intensidade à cor
            adjusted_color = tuple(
                int(c * intensity * self.current_state.brightness) 
                for c in command.color
            )
            
            await self._apply_color(adjusted_color)
            await asyncio.sleep(0.05)  # 20 FPS
    
    async def _execute_pulse(self, command: LEDCommand) -> None:
        """Executa padrão de pulso"""
        duration = command.duration or 3.0
        start_time = time.time()
        
        while time.time() - start_time < duration:
            # Pulso rápido
            elapsed = time.time() - start_time
            cycle_time = 0.5  # 0.5 segundos por ciclo
            intensity = (math.sin(elapsed * 2 * math.pi / cycle_time) + 1) / 2
            intensity = intensity ** 2  # Tornar pulso mais acentuado
            
            adjusted_color = tuple(
                int(c * intensity * self.current_state.brightness) 
                for c in command.color
            )
            
            await self._apply_color(adjusted_color)
            await asyncio.sleep(0.02)  # 50 FPS
    
    async def _execute_wave(self, command: LEDCommand) -> None:
        """Executa padrão de onda"""
        duration = command.duration or 4.0
        start_time = time.time()
        
        while time.time() - start_time < duration:
            # Onda de cor
            elapsed = time.time() - start_time
            cycle_time = 1.5  # 1.5 segundos por ciclo
            phase = (elapsed / cycle_time) % 1.0
            
            # Criar gradiente de cor
            r, g, b = command.color
            wave_r = int(r * (0.5 + 0.5 * math.sin(phase * 2 * math.pi)))
            wave_g = int(g * (0.5 + 0.5 * math.sin(phase * 2 * math.pi + math.pi/3)))
            wave_b = int(b * (0.5 + 0.5 * math.sin(phase * 2 * math.pi + 2*math.pi/3)))
            
            adjusted_color = (
                int(wave_r * self.current_state.brightness),
                int(wave_g * self.current_state.brightness),
                int(wave_b * self.current_state.brightness)
            )
            
            await self._apply_color(adjusted_color)
            await asyncio.sleep(0.03)  # ~33 FPS
    
    async def _execute_rainbow(self, command: LEDCommand) -> None:
        """Executa padrão arco-íris"""
        duration = command.duration or 5.0
        start_time = time.time()
        
        while time.time() - start_time < duration:
            elapsed = time.time() - start_time
            cycle_time = 3.0  # 3 segundos por ciclo completo
            hue = (elapsed / cycle_time) % 1.0
            
            # Converter HSV para RGB
            rgb = colorsys.hsv_to_rgb(hue, 1.0, 1.0)
            color = tuple(
                int(c * 255 * self.current_state.brightness) for c in rgb
            )
            
            await self._apply_color(color)
            await asyncio.sleep(0.05)  # 20 FPS
    
    async def _execute_flash(self, command: LEDCommand) -> None:
        """Executa padrão de flash"""
        count = command.parameters.get("count", 3)
        interval = command.parameters.get("interval", 0.5)
        
        for i in range(count):
            # Ligar
            await self._apply_color(command.color)
            await asyncio.sleep(interval / 2)
            
            # Desligar
            await self._apply_color((0, 0, 0))
            await asyncio.sleep(interval / 2)
    
    async def _execute_custom_pattern(self, command: LEDCommand) -> None:
        """Executa padrão customizado"""
        pattern_name = command.parameters.get("pattern_name")
        
        if pattern_name and self.patterns:
            await self.patterns.execute_pattern(pattern_name, command)
        else:
            logger.warning(f"Padrão customizado não encontrado: {pattern_name}")
            await self._execute_static_color(command)
    
    async def _apply_color(self, color: Tuple[int, int, int]) -> None:
        """Aplica cor aos LEDs físicos"""
        try:
            r, g, b = color
            
            # Aplicar via SDK Unitree
            if self.audio_client:
                code = self.audio_client.LedControl(r, g, b)
                if code != 0:
                    logger.error(f"Erro no controle de LED: código {code}")
            else:
                # Modo simulação
                logger.debug(f"LED simulado: RGB({r}, {g}, {b})")
            
            # Atualizar estado atual
            self.current_state.color = color
            self.current_state.timestamp = datetime.now()
            self.stats["color_changes"] += 1
            
        except Exception as e:
            logger.error(f"Erro ao aplicar cor: {e}")
            raise
    
    # === Engine de Animação ===
    
    async def _animation_engine(self) -> None:
        """Engine de animação para padrões complexos"""
        logger.debug("Engine de animação iniciado")
        
        while self.is_running:
            try:
                if self.animation_active and self.current_command:
                    # Atualizar frame de animação
                    self.animation_frame += 1
                    
                    # Executar lógica de animação específica
                    await self._update_animation_frame()
                
                await asyncio.sleep(1/30)  # 30 FPS
                
            except Exception as e:
                logger.error(f"Erro no engine de animação: {e}")
                await asyncio.sleep(0.1)
    
    async def _update_animation_frame(self) -> None:
        """Atualiza frame de animação"""
        # TODO: Implementar animações complexas
        pass
    
    # === Monitoramento ===
    
    async def _led_monitor(self) -> None:
        """Monitor de eventos LED"""
        logger.debug("Monitor de LED iniciado")
        
        while self.is_running:
            try:
                # Processar eventos LED
                event = await asyncio.wait_for(
                    self.led_events.get(), 
                    timeout=1.0
                )
                
                # Notificar callbacks registrados
                for callback in self.led_callbacks:
                    try:
                        if asyncio.iscoroutinefunction(callback):
                            await callback(event)
                        else:
                            callback(event)
                    except Exception as e:
                        logger.error(f"Erro em callback LED: {e}")
                
            except asyncio.TimeoutError:
                continue
            except Exception as e:
                logger.error(f"Erro no monitor de LED: {e}")
    
    async def _health_monitor(self) -> None:
        """Monitor de saúde do módulo"""
        logger.debug("Monitor de saúde do LED iniciado")
        
        while self.is_running:
            try:
                # Calcular saúde baseada em erros recentes
                total_commands = self.stats["commands_executed"]
                error_rate = self.stats["led_errors"] / max(total_commands, 1)
                
                # Atualizar saúde
                if error_rate < 0.1:
                    self.health = 1.0
                elif error_rate < 0.3:
                    self.health = 0.7
                else:
                    self.health = 0.3
                
                # Atualizar status na máquina de estados
                state_machine.update_module_status(
                    "led_manager", 
                    ModuleState.ACTIVE if self.health > 0.5 else ModuleState.ERROR, 
                    health=self.health
                )
                
                await asyncio.sleep(10.0)  # Verificar a cada 10 segundos
                
            except Exception as e:
                logger.error(f"Erro no monitor de saúde: {e}")
                await asyncio.sleep(1.0)
    
    # === Métodos Utilitários ===
    
    def register_led_callback(self, callback: Callable) -> None:
        """Registra callback para eventos LED"""
        self.led_callbacks.append(callback)
        logger.debug("Callback LED registrado")
    
    def register_state_callback(self, callback: Callable) -> None:
        """Registra callback para mudanças de estado"""
        self.state_callbacks.append(callback)
        logger.debug("Callback de estado LED registrado")
    
    def get_current_color(self) -> Tuple[int, int, int]:
        """Retorna cor atual dos LEDs"""
        return self.current_state.color
    
    def get_current_brightness(self) -> float:
        """Retorna brilho atual"""
        return self.current_state.brightness
    
    def get_available_patterns(self) -> List[str]:
        """Retorna lista de padrões disponíveis"""
        if self.patterns:
            return self.patterns.get_pattern_names()
        return []
    
    def get_context_colors(self) -> Dict[str, Tuple[int, int, int]]:
        """Retorna mapeamento de contextos para cores"""
        return self.context_colors.copy()
    
    def is_animation_active(self) -> bool:
        """Verifica se há animação ativa"""
        return self.animation_active
    
    def get_command_queue_size(self) -> int:
        """Retorna tamanho da fila de comandos"""
        return self.command_queue.qsize()
    
    async def emergency_stop(self) -> None:
        """Para todas as operações LED imediatamente"""
        logger.warning("Parada de emergência do LED")
        
        self.animation_active = False
        self.current_command = None
        
        # Limpar fila
        while not self.command_queue.empty():
            try:
                self.command_queue.get_nowait()
            except asyncio.QueueEmpty:
                break
        
        # LED de emergência
        await self._apply_color((255, 0, 0))  # Vermelho
    
    def get_status(self) -> Dict[str, Any]:
        """Retorna status atual do módulo"""
        uptime = time.time() - self.stats["uptime"] if self.stats["uptime"] else 0
        
        return {
            "name": "led_manager",
            "initialized": self.is_initialized,
            "running": self.is_running,
            "health": self.health,
            "last_error": self.last_error,
            "state": {
                "current_color": self.current_state.color,
                "brightness": self.current_state.brightness,
                "mode": self.current_state.mode.name,
                "active_pattern": self.current_state.active_pattern,
                "animation_active": self.animation_active,
                "current_command": self.current_command.id if self.current_command else None,
                "queue_size": self.command_queue.qsize()
            },
            "patterns": {
                "available": len(self.get_available_patterns()),
                "library": self.get_available_patterns()
            },
            "contexts": list(self.context_colors.keys()),
            "statistics": {
                **self.stats,
                "uptime": uptime,
                "error_rate": self.stats["led_errors"] / max(self.stats["commands_executed"], 1)
            }
        }