#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Core Orchestrator Engine do Middleware t031a5

Sistema central de coordenação que gerencia todos os módulos
e orquestra as interações multimodais do robô Unitree G1.
"""

import asyncio
import logging
import signal
import sys
from typing import Dict, List, Optional, Any, Callable
from datetime import datetime
import json
from pathlib import Path

# Imports locais
from .config_manager import config_manager, SystemConfig
from .state_machine import state_machine, RobotState, ModuleState

# Imports dos módulos (serão implementados)
# from ..modules.audio.manager import AudioManager
# from ..modules.motion.manager import MotionManager
# from ..modules.leds.manager import LEDManager
# from ..modules.video.manager import VideoManager
# from ..modules.sensors.fusion import SensorFusion

logger = logging.getLogger(__name__)

class ModuleInterface:
    """Interface base para todos os módulos"""
    
    def __init__(self, name: str):
        self.name = name
        self.is_initialized = False
        self.is_running = False
        self.health = 1.0
        self.last_error = None
    
    async def initialize(self) -> bool:
        """Inicializa o módulo"""
        raise NotImplementedError
    
    async def start(self) -> bool:
        """Inicia o módulo"""
        raise NotImplementedError
    
    async def stop(self) -> bool:
        """Para o módulo"""
        raise NotImplementedError
    
    async def cleanup(self) -> None:
        """Limpa recursos do módulo"""
        raise NotImplementedError
    
    def get_status(self) -> Dict[str, Any]:
        """Retorna status atual do módulo"""
        return {
            "name": self.name,
            "initialized": self.is_initialized,
            "running": self.is_running,
            "health": self.health,
            "last_error": self.last_error
        }

class CoreOrchestrator:
    """Engine central de orquestração do middleware"""
    
    def __init__(self):
        self.config: SystemConfig = config_manager.get_config()
        self.modules: Dict[str, ModuleInterface] = {}
        self.event_queue = asyncio.Queue()
        self.is_running = False
        self.shutdown_event = asyncio.Event()
        self.tasks: List[asyncio.Task] = []
        
        # Callbacks para eventos
        self.event_callbacks: Dict[str, List[Callable]] = {}
        
        # Estatísticas
        self.start_time = None
        self.event_count = 0
        self.error_count = 0
        
        logger.info("Core Orchestrator inicializado")
    
    async def initialize(self) -> bool:
        """Inicializa o sistema completo"""
        try:
            logger.info("Iniciando inicialização do sistema...")
            
            # Registrar handlers de sinal
            self._setup_signal_handlers()
            
            # Inicializar máquina de estados
            await state_machine.transition_to(RobotState.INITIALIZING)
            
            # Registrar módulos
            await self._register_modules()
            
            # Inicializar módulos
            success = await self._initialize_modules()
            
            if success:
                await state_machine.transition_to(RobotState.IDLE)
                logger.info("Sistema inicializado com sucesso")
                return True
            else:
                await state_machine.transition_to(RobotState.ERROR)
                logger.error("Falha na inicialização do sistema")
                return False
                
        except Exception as e:
            logger.error(f"Erro durante inicialização: {e}")
            await state_machine.transition_to(RobotState.ERROR)
            return False
    
    async def start(self) -> None:
        """Inicia o sistema principal"""
        if self.is_running:
            logger.warning("Sistema já está em execução")
            return
        
        try:
            self.is_running = True
            self.start_time = datetime.now()
            
            logger.info("Iniciando Core Orchestrator...")
            
            # Inicializar sistema
            if not await self.initialize():
                raise RuntimeError("Falha na inicialização")
            
            # Iniciar tarefas principais
            self.tasks = [
                asyncio.create_task(self._event_processor()),
                asyncio.create_task(self._health_monitor()),
                asyncio.create_task(self._state_monitor()),
                asyncio.create_task(self._performance_monitor())
            ]
            
            # Iniciar módulos
            await self._start_modules()
            
            # Transicionar para estado ativo
            await state_machine.transition_to(RobotState.ACTIVE)
            
            logger.info("Sistema iniciado e operacional")
            
            # Aguardar sinal de shutdown
            await self.shutdown_event.wait()
            
        except Exception as e:
            logger.error(f"Erro durante execução: {e}")
            await state_machine.emergency_stop(f"Erro crítico: {e}")
        
        finally:
            await self.shutdown()
    
    async def shutdown(self) -> None:
        """Para o sistema de forma segura"""
        if not self.is_running:
            return
        
        logger.info("Iniciando shutdown do sistema...")
        
        try:
            # Transicionar para estado de shutdown
            await state_machine.transition_to(RobotState.SHUTDOWN)
            
            # Parar módulos
            await self._stop_modules()
            
            # Cancelar tarefas
            for task in self.tasks:
                if not task.done():
                    task.cancel()
            
            # Aguardar conclusão das tarefas
            if self.tasks:
                await asyncio.gather(*self.tasks, return_exceptions=True)
            
            # Cleanup final
            await self._cleanup_modules()
            
            self.is_running = False
            logger.info("Sistema finalizado com sucesso")
            
        except Exception as e:
            logger.error(f"Erro durante shutdown: {e}")
    
    def _setup_signal_handlers(self) -> None:
        """Configura handlers para sinais do sistema"""
        def signal_handler(signum, frame):
            logger.info(f"Sinal recebido: {signum}")
            asyncio.create_task(self._graceful_shutdown())
        
        signal.signal(signal.SIGINT, signal_handler)
        signal.signal(signal.SIGTERM, signal_handler)
    
    async def _graceful_shutdown(self) -> None:
        """Executa shutdown gracioso"""
        logger.info("Executando shutdown gracioso...")
        self.shutdown_event.set()
    
    async def _register_modules(self) -> None:
        """Registra todos os módulos do sistema"""
        # Registrar módulos na máquina de estados
        modules_to_register = [
            "audio_manager",
            "motion_manager", 
            "led_manager",
            "video_manager",
            "sensor_fusion"
        ]
        
        for module_name in modules_to_register:
            state_machine.register_module(module_name)
            logger.debug(f"Módulo registrado: {module_name}")
    
    async def _initialize_modules(self) -> bool:
        """Inicializa todos os módulos"""
        logger.info("Inicializando módulos...")
        
        # TODO: Implementar inicialização real dos módulos
        # Por enquanto, simular inicialização bem-sucedida
        
        success_count = 0
        total_modules = len(self.modules) if self.modules else 5  # Placeholder
        
        # Simular inicialização dos módulos
        module_names = ["audio_manager", "motion_manager", "led_manager", 
                       "video_manager", "sensor_fusion"]
        
        for module_name in module_names:
            try:
                # Simular inicialização
                await asyncio.sleep(0.1)  # Simular tempo de inicialização
                
                state_machine.update_module_status(
                    module_name, 
                    ModuleState.READY, 
                    health=1.0
                )
                
                success_count += 1
                logger.info(f"Módulo {module_name} inicializado")
                
            except Exception as e:
                logger.error(f"Falha ao inicializar {module_name}: {e}")
                state_machine.update_module_status(
                    module_name, 
                    ModuleState.ERROR, 
                    health=0.0
                )
        
        success_rate = success_count / total_modules
        logger.info(f"Inicialização concluída: {success_count}/{total_modules} módulos")
        
        return success_rate >= 0.8  # Requer 80% de sucesso
    
    async def _start_modules(self) -> None:
        """Inicia todos os módulos"""
        logger.info("Iniciando módulos...")
        
        # TODO: Implementar start real dos módulos
        module_names = ["audio_manager", "motion_manager", "led_manager", 
                       "video_manager", "sensor_fusion"]
        
        for module_name in module_names:
            try:
                state_machine.update_module_status(
                    module_name, 
                    ModuleState.ACTIVE, 
                    health=1.0
                )
                logger.info(f"Módulo {module_name} iniciado")
                
            except Exception as e:
                logger.error(f"Falha ao iniciar {module_name}: {e}")
    
    async def _stop_modules(self) -> None:
        """Para todos os módulos"""
        logger.info("Parando módulos...")
        
        # TODO: Implementar stop real dos módulos
        for module_name in self.modules:
            try:
                # await self.modules[module_name].stop()
                logger.info(f"Módulo {module_name} parado")
            except Exception as e:
                logger.error(f"Erro ao parar {module_name}: {e}")
    
    async def _cleanup_modules(self) -> None:
        """Limpa recursos dos módulos"""
        logger.info("Limpando recursos dos módulos...")
        
        # TODO: Implementar cleanup real dos módulos
        for module_name in self.modules:
            try:
                # await self.modules[module_name].cleanup()
                logger.debug(f"Recursos do módulo {module_name} limpos")
            except Exception as e:
                logger.error(f"Erro na limpeza de {module_name}: {e}")
    
    async def _event_processor(self) -> None:
        """Processa eventos do sistema"""
        logger.debug("Processador de eventos iniciado")
        
        while self.is_running:
            try:
                # Aguardar evento com timeout
                event = await asyncio.wait_for(
                    self.event_queue.get(), 
                    timeout=1.0
                )
                
                await self._handle_event(event)
                self.event_count += 1
                
            except asyncio.TimeoutError:
                continue
            except Exception as e:
                logger.error(f"Erro no processamento de evento: {e}")
                self.error_count += 1
    
    async def _handle_event(self, event: Dict[str, Any]) -> None:
        """Processa um evento específico"""
        event_type = event.get("type", "unknown")
        
        logger.debug(f"Processando evento: {event_type}")
        
        # Executar callbacks registrados
        callbacks = self.event_callbacks.get(event_type, [])
        for callback in callbacks:
            try:
                if asyncio.iscoroutinefunction(callback):
                    await callback(event)
                else:
                    callback(event)
            except Exception as e:
                logger.error(f"Erro em callback para {event_type}: {e}")
    
    async def _health_monitor(self) -> None:
        """Monitor de saúde do sistema"""
        logger.debug("Monitor de saúde iniciado")
        
        while self.is_running:
            try:
                # Verificar saúde geral
                system_health = state_machine.get_system_health()
                failed_modules = state_machine.get_failed_modules()
                
                if system_health < 0.5:
                    logger.warning(f"Saúde do sistema baixa: {system_health:.2f}")
                    
                    if failed_modules:
                        logger.warning(f"Módulos com falha: {failed_modules}")
                
                # Verificar se precisa de parada de emergência
                if system_health < 0.3:
                    await state_machine.emergency_stop(
                        f"Saúde crítica do sistema: {system_health:.2f}"
                    )
                
                await asyncio.sleep(5.0)  # Verificar a cada 5 segundos
                
            except Exception as e:
                logger.error(f"Erro no monitor de saúde: {e}")
                await asyncio.sleep(1.0)
    
    async def _state_monitor(self) -> None:
        """Monitor de estados do sistema"""
        logger.debug("Monitor de estados iniciado")
        
        while self.is_running:
            try:
                # Log periódico do estado atual
                state_info = state_machine.get_state_info()
                
                if self.event_count % 100 == 0:  # Log a cada 100 eventos
                    logger.info(
                        f"Estado: {state_info['current_state']}, "
                        f"Saúde: {state_info['system_health']:.2f}, "
                        f"Eventos: {self.event_count}"
                    )
                
                await asyncio.sleep(10.0)  # Verificar a cada 10 segundos
                
            except Exception as e:
                logger.error(f"Erro no monitor de estados: {e}")
                await asyncio.sleep(1.0)
    
    async def _performance_monitor(self) -> None:
        """Monitor de performance do sistema"""
        logger.debug("Monitor de performance iniciado")
        
        while self.is_running:
            try:
                # Coletar métricas de performance
                uptime = (datetime.now() - self.start_time).total_seconds() if self.start_time else 0
                events_per_second = self.event_count / max(uptime, 1)
                error_rate = self.error_count / max(self.event_count, 1)
                
                # Log métricas periodicamente
                if uptime > 0 and int(uptime) % 60 == 0:  # A cada minuto
                    logger.info(
                        f"Performance - Uptime: {uptime:.0f}s, "
                        f"Events/s: {events_per_second:.2f}, "
                        f"Error rate: {error_rate:.2%}"
                    )
                
                await asyncio.sleep(1.0)
                
            except Exception as e:
                logger.error(f"Erro no monitor de performance: {e}")
                await asyncio.sleep(1.0)
    
    def register_event_callback(self, event_type: str, callback: Callable) -> None:
        """Registra callback para tipo de evento"""
        if event_type not in self.event_callbacks:
            self.event_callbacks[event_type] = []
        self.event_callbacks[event_type].append(callback)
        logger.debug(f"Callback registrado para evento: {event_type}")
    
    async def emit_event(self, event_type: str, data: Optional[Dict] = None) -> None:
        """Emite um evento para o sistema"""
        event = {
            "type": event_type,
            "timestamp": datetime.now().isoformat(),
            "data": data or {}
        }
        
        await self.event_queue.put(event)
    
    def get_system_status(self) -> Dict[str, Any]:
        """Retorna status completo do sistema"""
        uptime = (datetime.now() - self.start_time).total_seconds() if self.start_time else 0
        
        return {
            "orchestrator": {
                "running": self.is_running,
                "uptime": uptime,
                "event_count": self.event_count,
                "error_count": self.error_count,
                "queue_size": self.event_queue.qsize()
            },
            "state_machine": state_machine.get_state_info(),
            "config": {
                "version": self.config.general.get("version", "unknown"),
                "debug": self.config.general.get("debug", False)
            }
        }

# Instância global do orquestrador
orchestrator = CoreOrchestrator()