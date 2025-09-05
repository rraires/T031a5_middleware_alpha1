#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Máquina de Estados do Middleware t031a5

Gerencia todos os estados possíveis do robô e as transições
entre eles, garantindo operação segura e coordenada.
"""

import asyncio
import logging
from enum import Enum, auto
from typing import Dict, List, Callable, Optional, Any
from dataclasses import dataclass, field
from datetime import datetime
import json

logger = logging.getLogger(__name__)

class RobotState(Enum):
    """Estados possíveis do robô"""
    # Estados básicos
    INITIALIZING = auto()
    IDLE = auto()
    ACTIVE = auto()
    ERROR = auto()
    EMERGENCY_STOP = auto()
    SHUTDOWN = auto()
    
    # Estados de interação
    LISTENING = auto()
    PROCESSING = auto()
    SPEAKING = auto()
    MOVING = auto()
    
    # Estados especiais
    CALIBRATING = auto()
    MAINTENANCE = auto()
    LEARNING = auto()

class ModuleState(Enum):
    """Estados dos módulos individuais"""
    OFFLINE = auto()
    INITIALIZING = auto()
    READY = auto()
    ACTIVE = auto()
    ERROR = auto()
    MAINTENANCE = auto()

@dataclass
class StateTransition:
    """Representa uma transição de estado"""
    from_state: RobotState
    to_state: RobotState
    condition: Optional[Callable[[], bool]] = None
    action: Optional[Callable[[], None]] = None
    timestamp: datetime = field(default_factory=datetime.now)
    metadata: Dict[str, Any] = field(default_factory=dict)

@dataclass
class ModuleStatus:
    """Status de um módulo do sistema"""
    name: str
    state: ModuleState
    health: float  # 0.0 a 1.0
    last_update: datetime = field(default_factory=datetime.now)
    error_count: int = 0
    metadata: Dict[str, Any] = field(default_factory=dict)

class StateMachine:
    """Máquina de estados principal do sistema"""
    
    def __init__(self):
        self.current_state = RobotState.INITIALIZING
        self.previous_state = None
        self.state_history: List[StateTransition] = []
        self.modules: Dict[str, ModuleStatus] = {}
        self.state_callbacks: Dict[RobotState, List[Callable]] = {}
        self.transition_callbacks: Dict[tuple, List[Callable]] = {}
        self._lock = asyncio.Lock()
        
        # Definir transições válidas
        self.valid_transitions = self._define_valid_transitions()
        
        logger.info("Máquina de estados inicializada")
    
    def _define_valid_transitions(self) -> Dict[RobotState, List[RobotState]]:
        """Define as transições válidas entre estados"""
        return {
            RobotState.INITIALIZING: [
                RobotState.IDLE,
                RobotState.ERROR,
                RobotState.EMERGENCY_STOP
            ],
            RobotState.IDLE: [
                RobotState.ACTIVE,
                RobotState.LISTENING,
                RobotState.CALIBRATING,
                RobotState.MAINTENANCE,
                RobotState.ERROR,
                RobotState.EMERGENCY_STOP,
                RobotState.SHUTDOWN
            ],
            RobotState.ACTIVE: [
                RobotState.IDLE,
                RobotState.LISTENING,
                RobotState.PROCESSING,
                RobotState.SPEAKING,
                RobotState.MOVING,
                RobotState.ERROR,
                RobotState.EMERGENCY_STOP
            ],
            RobotState.LISTENING: [
                RobotState.IDLE,
                RobotState.PROCESSING,
                RobotState.ERROR,
                RobotState.EMERGENCY_STOP
            ],
            RobotState.PROCESSING: [
                RobotState.IDLE,
                RobotState.SPEAKING,
                RobotState.MOVING,
                RobotState.LEARNING,
                RobotState.ERROR,
                RobotState.EMERGENCY_STOP
            ],
            RobotState.SPEAKING: [
                RobotState.IDLE,
                RobotState.ACTIVE,
                RobotState.MOVING,
                RobotState.ERROR,
                RobotState.EMERGENCY_STOP
            ],
            RobotState.MOVING: [
                RobotState.IDLE,
                RobotState.ACTIVE,
                RobotState.SPEAKING,
                RobotState.ERROR,
                RobotState.EMERGENCY_STOP
            ],
            RobotState.ERROR: [
                RobotState.IDLE,
                RobotState.MAINTENANCE,
                RobotState.EMERGENCY_STOP,
                RobotState.SHUTDOWN
            ],
            RobotState.EMERGENCY_STOP: [
                RobotState.IDLE,
                RobotState.MAINTENANCE,
                RobotState.SHUTDOWN
            ],
            RobotState.CALIBRATING: [
                RobotState.IDLE,
                RobotState.ERROR,
                RobotState.EMERGENCY_STOP
            ],
            RobotState.MAINTENANCE: [
                RobotState.IDLE,
                RobotState.CALIBRATING,
                RobotState.SHUTDOWN
            ],
            RobotState.LEARNING: [
                RobotState.IDLE,
                RobotState.ACTIVE,
                RobotState.ERROR,
                RobotState.EMERGENCY_STOP
            ],
            RobotState.SHUTDOWN: []  # Estado final
        }
    
    async def transition_to(self, new_state: RobotState, 
                           metadata: Optional[Dict[str, Any]] = None) -> bool:
        """Executa transição para novo estado"""
        async with self._lock:
            if not self._is_valid_transition(self.current_state, new_state):
                logger.warning(
                    f"Transição inválida: {self.current_state.name} -> {new_state.name}"
                )
                return False
            
            # Executar callbacks de saída do estado atual
            await self._execute_exit_callbacks(self.current_state)
            
            # Registrar transição
            transition = StateTransition(
                from_state=self.current_state,
                to_state=new_state,
                metadata=metadata or {}
            )
            
            self.state_history.append(transition)
            self.previous_state = self.current_state
            self.current_state = new_state
            
            logger.info(
                f"Transição de estado: {self.previous_state.name} -> {new_state.name}"
            )
            
            # Executar callbacks de entrada do novo estado
            await self._execute_entry_callbacks(new_state)
            
            # Executar callbacks de transição específica
            await self._execute_transition_callbacks(self.previous_state, new_state)
            
            return True
    
    def _is_valid_transition(self, from_state: RobotState, to_state: RobotState) -> bool:
        """Verifica se a transição é válida"""
        return to_state in self.valid_transitions.get(from_state, [])
    
    async def _execute_exit_callbacks(self, state: RobotState) -> None:
        """Executa callbacks de saída de estado"""
        callbacks = self.state_callbacks.get(state, [])
        for callback in callbacks:
            try:
                if asyncio.iscoroutinefunction(callback):
                    await callback()
                else:
                    callback()
            except Exception as e:
                logger.error(f"Erro em callback de saída {state.name}: {e}")
    
    async def _execute_entry_callbacks(self, state: RobotState) -> None:
        """Executa callbacks de entrada de estado"""
        callbacks = self.state_callbacks.get(state, [])
        for callback in callbacks:
            try:
                if asyncio.iscoroutinefunction(callback):
                    await callback()
                else:
                    callback()
            except Exception as e:
                logger.error(f"Erro em callback de entrada {state.name}: {e}")
    
    async def _execute_transition_callbacks(self, from_state: RobotState, 
                                          to_state: RobotState) -> None:
        """Executa callbacks de transição específica"""
        transition_key = (from_state, to_state)
        callbacks = self.transition_callbacks.get(transition_key, [])
        
        for callback in callbacks:
            try:
                if asyncio.iscoroutinefunction(callback):
                    await callback()
                else:
                    callback()
            except Exception as e:
                logger.error(
                    f"Erro em callback de transição {from_state.name}->{to_state.name}: {e}"
                )
    
    def register_state_callback(self, state: RobotState, callback: Callable) -> None:
        """Registra callback para entrada/saída de estado"""
        if state not in self.state_callbacks:
            self.state_callbacks[state] = []
        self.state_callbacks[state].append(callback)
        logger.debug(f"Callback registrado para estado {state.name}")
    
    def register_transition_callback(self, from_state: RobotState, 
                                   to_state: RobotState, callback: Callable) -> None:
        """Registra callback para transição específica"""
        transition_key = (from_state, to_state)
        if transition_key not in self.transition_callbacks:
            self.transition_callbacks[transition_key] = []
        self.transition_callbacks[transition_key].append(callback)
        logger.debug(f"Callback registrado para transição {from_state.name}->{to_state.name}")
    
    def register_module(self, name: str, initial_state: ModuleState = ModuleState.OFFLINE) -> None:
        """Registra um módulo no sistema"""
        self.modules[name] = ModuleStatus(
            name=name,
            state=initial_state,
            health=1.0
        )
        logger.info(f"Módulo registrado: {name}")
    
    def update_module_status(self, name: str, state: ModuleState, 
                           health: float = 1.0, metadata: Optional[Dict] = None) -> None:
        """Atualiza status de um módulo"""
        if name not in self.modules:
            logger.warning(f"Módulo não registrado: {name}")
            return
        
        module = self.modules[name]
        module.state = state
        module.health = max(0.0, min(1.0, health))  # Clamp entre 0 e 1
        module.last_update = datetime.now()
        
        if metadata:
            module.metadata.update(metadata)
        
        logger.debug(f"Status do módulo {name} atualizado: {state.name} (health: {health:.2f})")
    
    def get_system_health(self) -> float:
        """Calcula saúde geral do sistema"""
        if not self.modules:
            return 1.0
        
        total_health = sum(module.health for module in self.modules.values())
        return total_health / len(self.modules)
    
    def get_failed_modules(self) -> List[str]:
        """Retorna lista de módulos com falha"""
        return [
            name for name, module in self.modules.items()
            if module.state == ModuleState.ERROR or module.health < 0.5
        ]
    
    def get_state_info(self) -> Dict[str, Any]:
        """Retorna informações completas do estado atual"""
        return {
            "current_state": self.current_state.name,
            "previous_state": self.previous_state.name if self.previous_state else None,
            "system_health": self.get_system_health(),
            "failed_modules": self.get_failed_modules(),
            "modules": {
                name: {
                    "state": module.state.name,
                    "health": module.health,
                    "last_update": module.last_update.isoformat(),
                    "error_count": module.error_count
                }
                for name, module in self.modules.items()
            },
            "transition_count": len(self.state_history),
            "uptime": (datetime.now() - self.state_history[0].timestamp).total_seconds() if self.state_history else 0
        }
    
    async def emergency_stop(self, reason: str = "Emergency stop triggered") -> None:
        """Executa parada de emergência"""
        logger.critical(f"PARADA DE EMERGÊNCIA: {reason}")
        await self.transition_to(RobotState.EMERGENCY_STOP, {"reason": reason})
    
    def can_transition_to(self, target_state: RobotState) -> bool:
        """Verifica se pode transicionar para o estado alvo"""
        return self._is_valid_transition(self.current_state, target_state)
    
    def get_possible_transitions(self) -> List[RobotState]:
        """Retorna lista de transições possíveis do estado atual"""
        return self.valid_transitions.get(self.current_state, [])

# Instância global da máquina de estados
state_machine = StateMachine()