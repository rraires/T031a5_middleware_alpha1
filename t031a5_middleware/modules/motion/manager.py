#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
MotionManager - Gerenciador de Movimento do Middleware t031a5

Responsável por coordenar todos os movimentos do robô G1,
incluindo locomoção, gestos, controle de braços e segurança.
"""

import asyncio
import logging
import json
import time
import math
from typing import Optional, Dict, Any, List, Tuple, Callable
from datetime import datetime
from enum import Enum, auto
from dataclasses import dataclass
import sys
import os

# Adicionar path do SDK Unitree
sys.path.append(os.path.join(os.path.dirname(__file__), '../../../unitre_sdk_python'))

try:
    from unitree_sdk2py.core.channel import ChannelFactoryInitialize
    from unitree_sdk2py.g1.loco.g1_loco_client import LocoClient
    from unitree_sdk2py.g1.arm.g1_arm_action_client import G1ArmActionClient
except ImportError as e:
    logging.warning(f"SDK Unitree não encontrado: {e}")
    LocoClient = None
    G1ArmActionClient = None

# Imports locais
from ...core.config_manager import config_manager
from ...core.state_machine import state_machine, ModuleState, RobotState
from .high_level import HighLevelController
from .low_level import LowLevelController

logger = logging.getLogger(__name__)

class MovementType(Enum):
    """Tipos de movimento"""
    LOCOMOTION = auto()      # Locomoção básica
    GESTURE = auto()         # Gestos expressivos
    ARM_ACTION = auto()      # Ações de braço
    COMPLEX = auto()         # Movimentos complexos coordenados
    EMERGENCY = auto()       # Movimentos de emergência

class MovementPriority(Enum):
    """Prioridades de movimento"""
    LOW = 1
    NORMAL = 2
    HIGH = 3
    EMERGENCY = 4

@dataclass
class MovementCommand:
    """Comando de movimento"""
    id: str
    type: MovementType
    priority: MovementPriority
    data: Dict[str, Any]
    duration: Optional[float] = None
    callback: Optional[Callable] = None
    timestamp: datetime = None
    
    def __post_init__(self):
        if self.timestamp is None:
            self.timestamp = datetime.now()

@dataclass
class RobotPose:
    """Pose do robô"""
    position: Tuple[float, float, float]  # x, y, z
    orientation: Tuple[float, float, float]  # roll, pitch, yaw
    joint_angles: Dict[str, float]
    timestamp: datetime = None
    
    def __post_init__(self):
        if self.timestamp is None:
            self.timestamp = datetime.now()

class MotionManager:
    """Gerenciador principal do sistema de movimento"""
    
    def __init__(self):
        self.config = config_manager.get_config().motion
        self.network_config = config_manager.get_config().network
        
        # Componentes principais
        self.loco_client: Optional[LocoClient] = None
        self.arm_client: Optional[G1ArmActionClient] = None
        self.high_level: Optional[HighLevelController] = None
        self.low_level: Optional[LowLevelController] = None
        
        # Estado do módulo
        self.is_initialized = False
        self.is_running = False
        self.health = 1.0
        self.last_error = None
        
        # Estado do movimento
        self.is_moving = False
        self.current_movement: Optional[MovementCommand] = None
        self.movement_queue = asyncio.PriorityQueue()
        self.emergency_stop_active = False
        
        # Pose atual
        self.current_pose: Optional[RobotPose] = None
        self.target_pose: Optional[RobotPose] = None
        
        # Biblioteca de gestos
        self.gesture_library: Dict[str, Dict] = {}
        
        # Callbacks
        self.movement_callbacks: List[Callable] = []
        self.pose_callbacks: List[Callable] = []
        
        # Tarefas assíncronas
        self.tasks: List[asyncio.Task] = []
        
        # Estatísticas
        self.stats = {
            "movements_executed": 0,
            "gestures_performed": 0,
            "emergency_stops": 0,
            "movement_errors": 0,
            "uptime": 0,
            "last_movement": None
        }
        
        logger.info("MotionManager inicializado")
    
    async def initialize(self) -> bool:
        """Inicializa o sistema de movimento"""
        try:
            logger.info("Inicializando MotionManager...")
            
            # Registrar na máquina de estados
            state_machine.update_module_status(
                "motion_manager", 
                ModuleState.INITIALIZING, 
                health=0.5
            )
            
            # Inicializar SDK Unitree
            if not await self._initialize_unitree_sdk():
                raise RuntimeError("Falha na inicialização do SDK Unitree")
            
            # Inicializar controladores
            await self._initialize_controllers()
            
            # Carregar biblioteca de gestos
            await self._load_gesture_library()
            
            # Obter pose inicial
            await self._update_current_pose()
            
            # Marcar como inicializado
            self.is_initialized = True
            self.health = 1.0
            
            state_machine.update_module_status(
                "motion_manager", 
                ModuleState.READY, 
                health=self.health
            )
            
            logger.info("MotionManager inicializado com sucesso")
            return True
            
        except Exception as e:
            logger.error(f"Erro na inicialização do MotionManager: {e}")
            self.last_error = str(e)
            self.health = 0.0
            
            state_machine.update_module_status(
                "motion_manager", 
                ModuleState.ERROR, 
                health=self.health
            )
            
            return False
    
    async def _initialize_unitree_sdk(self) -> bool:
        """Inicializa o SDK Unitree para movimento"""
        try:
            if LocoClient is None or G1ArmActionClient is None:
                logger.warning("SDK Unitree não disponível, usando modo simulação")
                return True
            
            # Inicializar factory de canais (se ainda não foi feito)
            try:
                ChannelFactoryInitialize(0, self.network_config.interface)
            except:
                pass  # Pode já ter sido inicializado pelo AudioManager
            
            # Criar cliente de locomoção
            self.loco_client = LocoClient()
            self.loco_client.Init()
            
            # Criar cliente de braços
            self.arm_client = G1ArmActionClient()
            self.arm_client.Init()
            
            logger.info("SDK Unitree Motion inicializado")
            return True
            
        except Exception as e:
            logger.error(f"Erro na inicialização do SDK Unitree: {e}")
            return False
    
    async def _initialize_controllers(self) -> None:
        """Inicializa controladores de alto e baixo nível"""
        # Inicializar controlador de alto nível
        self.high_level = HighLevelController(
            self.loco_client, 
            self.arm_client, 
            self.config
        )
        await self.high_level.initialize()
        
        # Inicializar controlador de baixo nível
        self.low_level = LowLevelController(
            self.config
        )
        await self.low_level.initialize()
        
        logger.info("Controladores de movimento inicializados")
    
    async def _load_gesture_library(self) -> None:
        """Carrega biblioteca de gestos"""
        try:
            gestures_path = self.config.gestures.library_path
            
            # Gestos básicos predefinidos
            self.gesture_library = {
                "wave_hello": {
                    "name": "Acenar Olá",
                    "description": "Acena com a mão direita",
                    "duration": 3.0,
                    "actions": [
                        {"type": "arm_action", "arm": "right", "action": "wave", "duration": 3.0}
                    ]
                },
                "shake_hands": {
                    "name": "Apertar Mãos",
                    "description": "Estende a mão direita para cumprimento",
                    "duration": 2.0,
                    "actions": [
                        {"type": "arm_action", "arm": "right", "action": "handshake", "duration": 2.0}
                    ]
                },
                "nod_yes": {
                    "name": "Acenar Sim",
                    "description": "Balança a cabeça afirmativamente",
                    "duration": 1.5,
                    "actions": [
                        {"type": "head_nod", "direction": "yes", "repetitions": 3, "duration": 1.5}
                    ]
                },
                "shake_no": {
                    "name": "Balançar Não",
                    "description": "Balança a cabeça negativamente",
                    "duration": 1.5,
                    "actions": [
                        {"type": "head_shake", "direction": "no", "repetitions": 3, "duration": 1.5}
                    ]
                },
                "point_forward": {
                    "name": "Apontar Frente",
                    "description": "Aponta para frente com o braço direito",
                    "duration": 2.0,
                    "actions": [
                        {"type": "arm_action", "arm": "right", "action": "point", "direction": "forward", "duration": 2.0}
                    ]
                },
                "thinking_pose": {
                    "name": "Pose Pensativa",
                    "description": "Coloca a mão no queixo em pose pensativa",
                    "duration": 3.0,
                    "actions": [
                        {"type": "arm_action", "arm": "right", "action": "thinking", "duration": 3.0}
                    ]
                },
                "celebration": {
                    "name": "Comemoração",
                    "description": "Levanta os dois braços em comemoração",
                    "duration": 2.5,
                    "actions": [
                        {"type": "arm_action", "arm": "both", "action": "celebrate", "duration": 2.5}
                    ]
                }
            }
            
            # TODO: Carregar gestos personalizados de arquivos
            # if os.path.exists(gestures_path):
            #     await self._load_custom_gestures(gestures_path)
            
            logger.info(f"Biblioteca de gestos carregada: {len(self.gesture_library)} gestos")
            
        except Exception as e:
            logger.error(f"Erro ao carregar biblioteca de gestos: {e}")
    
    async def start(self) -> bool:
        """Inicia o sistema de movimento"""
        if not self.is_initialized:
            logger.error("MotionManager não foi inicializado")
            return False
        
        if self.is_running:
            logger.warning("MotionManager já está em execução")
            return True
        
        try:
            logger.info("Iniciando MotionManager...")
            
            # Iniciar tarefas assíncronas
            self.tasks = [
                asyncio.create_task(self._movement_processor()),
                asyncio.create_task(self._pose_monitor()),
                asyncio.create_task(self._safety_monitor()),
                asyncio.create_task(self._health_monitor())
            ]
            
            # Iniciar controladores
            await self.high_level.start()
            await self.low_level.start()
            
            self.is_running = True
            self.stats["uptime"] = time.time()
            
            state_machine.update_module_status(
                "motion_manager", 
                ModuleState.ACTIVE, 
                health=self.health
            )
            
            logger.info("MotionManager iniciado com sucesso")
            return True
            
        except Exception as e:
            logger.error(f"Erro ao iniciar MotionManager: {e}")
            self.last_error = str(e)
            self.health = 0.0
            
            state_machine.update_module_status(
                "motion_manager", 
                ModuleState.ERROR, 
                health=self.health
            )
            
            return False
    
    async def stop(self) -> bool:
        """Para o sistema de movimento"""
        if not self.is_running:
            return True
        
        try:
            logger.info("Parando MotionManager...")
            
            # Parar movimento atual
            await self.stop_movement()
            
            # Parar controladores
            if self.high_level:
                await self.high_level.stop()
            if self.low_level:
                await self.low_level.stop()
            
            # Cancelar tarefas
            for task in self.tasks:
                if not task.done():
                    task.cancel()
            
            # Aguardar conclusão
            if self.tasks:
                await asyncio.gather(*self.tasks, return_exceptions=True)
            
            self.is_running = False
            
            state_machine.update_module_status(
                "motion_manager", 
                ModuleState.READY, 
                health=self.health
            )
            
            logger.info("MotionManager parado")
            return True
            
        except Exception as e:
            logger.error(f"Erro ao parar MotionManager: {e}")
            return False
    
    async def cleanup(self) -> None:
        """Limpa recursos do sistema de movimento"""
        try:
            logger.info("Limpando recursos do MotionManager...")
            
            # Parar se estiver rodando
            if self.is_running:
                await self.stop()
            
            # Cleanup controladores
            if self.high_level:
                await self.high_level.cleanup()
            if self.low_level:
                await self.low_level.cleanup()
            
            # Limpar fila de movimentos
            while not self.movement_queue.empty():
                try:
                    self.movement_queue.get_nowait()
                except asyncio.QueueEmpty:
                    break
            
            self.is_initialized = False
            
            logger.info("Recursos do MotionManager limpos")
            
        except Exception as e:
            logger.error(f"Erro na limpeza do MotionManager: {e}")
    
    # === Métodos de Movimento ===
    
    async def move(self, vx: float, vy: float, omega: float, 
                  duration: float = 1.0, priority: MovementPriority = MovementPriority.NORMAL) -> str:
        """Move o robô com velocidades especificadas"""
        if not self.is_running:
            raise RuntimeError("MotionManager não está em execução")
        
        if self.emergency_stop_active:
            raise RuntimeError("Parada de emergência ativa")
        
        command_id = f"move_{int(time.time() * 1000)}"
        
        command = MovementCommand(
            id=command_id,
            type=MovementType.LOCOMOTION,
            priority=priority,
            data={
                "vx": vx,
                "vy": vy,
                "omega": omega,
                "duration": duration
            },
            duration=duration
        )
        
        await self.movement_queue.put((priority.value, command))
        self.stats["last_movement"] = datetime.now().isoformat()
        
        logger.info(f"Comando de movimento enfileirado: vx={vx}, vy={vy}, omega={omega}")
        return command_id
    
    async def perform_gesture(self, gesture_name: str, 
                            priority: MovementPriority = MovementPriority.NORMAL) -> str:
        """Executa um gesto da biblioteca"""
        if not self.is_running:
            raise RuntimeError("MotionManager não está em execução")
        
        if self.emergency_stop_active:
            raise RuntimeError("Parada de emergência ativa")
        
        if gesture_name not in self.gesture_library:
            raise ValueError(f"Gesto não encontrado: {gesture_name}")
        
        command_id = f"gesture_{int(time.time() * 1000)}"
        gesture = self.gesture_library[gesture_name]
        
        command = MovementCommand(
            id=command_id,
            type=MovementType.GESTURE,
            priority=priority,
            data={
                "gesture_name": gesture_name,
                "gesture_data": gesture
            },
            duration=gesture.get("duration", 2.0)
        )
        
        await self.movement_queue.put((priority.value, command))
        self.stats["last_movement"] = datetime.now().isoformat()
        
        logger.info(f"Gesto enfileirado: {gesture_name}")
        return command_id
    
    async def move_arm(self, arm: str, action: str, parameters: Dict[str, Any] = None,
                      priority: MovementPriority = MovementPriority.NORMAL) -> str:
        """Move um braço específico"""
        if not self.is_running:
            raise RuntimeError("MotionManager não está em execução")
        
        if self.emergency_stop_active:
            raise RuntimeError("Parada de emergência ativa")
        
        command_id = f"arm_{int(time.time() * 1000)}"
        
        command = MovementCommand(
            id=command_id,
            type=MovementType.ARM_ACTION,
            priority=priority,
            data={
                "arm": arm,
                "action": action,
                "parameters": parameters or {}
            },
            duration=parameters.get("duration", 2.0) if parameters else 2.0
        )
        
        await self.movement_queue.put((priority.value, command))
        self.stats["last_movement"] = datetime.now().isoformat()
        
        logger.info(f"Ação de braço enfileirada: {arm} - {action}")
        return command_id
    
    async def stop_movement(self) -> None:
        """Para o movimento atual"""
        try:
            if self.current_movement:
                logger.info(f"Parando movimento: {self.current_movement.id}")
            
            self.is_moving = False
            self.current_movement = None
            
            # Parar movimento no SDK
            if self.loco_client:
                self.loco_client.StopMove()
            
            # Parar controladores
            if self.high_level:
                await self.high_level.stop_movement()
            if self.low_level:
                await self.low_level.stop_movement()
            
            logger.info("Movimento parado")
            
        except Exception as e:
            logger.error(f"Erro ao parar movimento: {e}")
    
    async def emergency_stop(self) -> None:
        """Para todos os movimentos imediatamente"""
        logger.warning("Parada de emergência do movimento")
        
        self.emergency_stop_active = True
        self.stats["emergency_stops"] += 1
        
        # Parar movimento atual
        await self.stop_movement()
        
        # Limpar fila de movimentos
        while not self.movement_queue.empty():
            try:
                self.movement_queue.get_nowait()
            except asyncio.QueueEmpty:
                break
        
        # Transicionar para estado de emergência
        await state_machine.transition_to(RobotState.EMERGENCY_STOP)
        
        logger.warning("Parada de emergência do movimento concluída")
    
    async def resume_from_emergency(self) -> None:
        """Resume operação após parada de emergência"""
        if not self.emergency_stop_active:
            return
        
        logger.info("Resumindo operação após parada de emergência")
        
        self.emergency_stop_active = False
        
        # Verificar se é seguro continuar
        if self.health > 0.7:
            await state_machine.transition_to(RobotState.ACTIVE)
            logger.info("Operação resumida")
        else:
            logger.warning("Sistema não está saudável o suficiente para resumir")
    
    # === Processamento de Movimentos ===
    
    async def _movement_processor(self) -> None:
        """Processa fila de comandos de movimento"""
        logger.debug("Processador de movimentos iniciado")
        
        while self.is_running:
            try:
                if self.emergency_stop_active:
                    await asyncio.sleep(1.0)
                    continue
                
                # Aguardar comando com timeout
                priority, command = await asyncio.wait_for(
                    self.movement_queue.get(), 
                    timeout=1.0
                )
                
                await self._execute_movement_command(command)
                
            except asyncio.TimeoutError:
                continue
            except Exception as e:
                logger.error(f"Erro no processador de movimentos: {e}")
                self.stats["movement_errors"] += 1
    
    async def _execute_movement_command(self, command: MovementCommand) -> None:
        """Executa um comando de movimento"""
        try:
            self.is_moving = True
            self.current_movement = command
            
            logger.info(f"Executando movimento: {command.type.name} - {command.id}")
            
            # Transicionar para estado de movimento
            await state_machine.transition_to(RobotState.MOVING)
            
            # Executar baseado no tipo
            if command.type == MovementType.LOCOMOTION:
                await self._execute_locomotion(command)
            elif command.type == MovementType.GESTURE:
                await self._execute_gesture(command)
            elif command.type == MovementType.ARM_ACTION:
                await self._execute_arm_action(command)
            elif command.type == MovementType.COMPLEX:
                await self._execute_complex_movement(command)
            
            # Executar callback se fornecido
            if command.callback:
                try:
                    if asyncio.iscoroutinefunction(command.callback):
                        await command.callback(command)
                    else:
                        command.callback(command)
                except Exception as e:
                    logger.error(f"Erro em callback de movimento: {e}")
            
            self.stats["movements_executed"] += 1
            
            # Notificar callbacks
            for callback in self.movement_callbacks:
                try:
                    if asyncio.iscoroutinefunction(callback):
                        await callback({
                            "type": "movement_completed",
                            "command": command,
                            "timestamp": datetime.now().isoformat()
                        })
                    else:
                        callback({
                            "type": "movement_completed",
                            "command": command,
                            "timestamp": datetime.now().isoformat()
                        })
                except Exception as e:
                    logger.error(f"Erro em callback de movimento: {e}")
            
            logger.debug(f"Movimento concluído: {command.id}")
            
        except Exception as e:
            logger.error(f"Erro na execução do movimento: {e}")
            self.stats["movement_errors"] += 1
        
        finally:
            self.is_moving = False
            self.current_movement = None
            
            # Retornar ao estado ativo se não houver mais movimentos
            if self.movement_queue.empty():
                await state_machine.transition_to(RobotState.ACTIVE)
    
    async def _execute_locomotion(self, command: MovementCommand) -> None:
        """Executa comando de locomoção"""
        data = command.data
        vx = data["vx"]
        vy = data["vy"]
        omega = data["omega"]
        duration = data["duration"]
        
        if self.high_level:
            await self.high_level.move(vx, vy, omega, duration)
        else:
            # Fallback para SDK direto
            if self.loco_client:
                self.loco_client.SetVelocity(vx, vy, omega, duration)
            
            # Aguardar duração do movimento
            await asyncio.sleep(duration)
    
    async def _execute_gesture(self, command: MovementCommand) -> None:
        """Executa comando de gesto"""
        gesture_data = command.data["gesture_data"]
        gesture_name = command.data["gesture_name"]
        
        logger.info(f"Executando gesto: {gesture_name}")
        
        # Executar ações do gesto
        for action in gesture_data.get("actions", []):
            await self._execute_gesture_action(action)
        
        self.stats["gestures_performed"] += 1
    
    async def _execute_gesture_action(self, action: Dict[str, Any]) -> None:
        """Executa uma ação específica de gesto"""
        action_type = action.get("type")
        duration = action.get("duration", 1.0)
        
        if action_type == "arm_action":
            arm = action.get("arm", "right")
            arm_action = action.get("action", "wave")
            
            if self.high_level:
                await self.high_level.perform_arm_action(arm, arm_action, duration)
            elif self.arm_client:
                # Usar SDK direto
                # TODO: Mapear ações para IDs do SDK
                pass
        
        elif action_type == "head_nod" or action_type == "head_shake":
            # TODO: Implementar movimentos de cabeça
            logger.info(f"Simulando movimento de cabeça: {action_type}")
            await asyncio.sleep(duration)
        
        else:
            logger.warning(f"Tipo de ação não suportado: {action_type}")
            await asyncio.sleep(duration)
    
    async def _execute_arm_action(self, command: MovementCommand) -> None:
        """Executa comando de ação de braço"""
        data = command.data
        arm = data["arm"]
        action = data["action"]
        parameters = data["parameters"]
        
        if self.high_level:
            await self.high_level.perform_arm_action(arm, action, command.duration, parameters)
        elif self.arm_client:
            # Usar SDK direto
            # TODO: Implementar mapeamento de ações
            pass
    
    async def _execute_complex_movement(self, command: MovementCommand) -> None:
        """Executa movimento complexo coordenado"""
        # TODO: Implementar movimentos complexos
        logger.info("Executando movimento complexo (não implementado)")
        await asyncio.sleep(command.duration or 2.0)
    
    # === Monitoramento ===
    
    async def _pose_monitor(self) -> None:
        """Monitor de pose do robô"""
        logger.debug("Monitor de pose iniciado")
        
        while self.is_running:
            try:
                # Atualizar pose atual
                await self._update_current_pose()
                
                # Notificar callbacks de pose
                if self.current_pose:
                    for callback in self.pose_callbacks:
                        try:
                            if asyncio.iscoroutinefunction(callback):
                                await callback(self.current_pose)
                            else:
                                callback(self.current_pose)
                        except Exception as e:
                            logger.error(f"Erro em callback de pose: {e}")
                
                await asyncio.sleep(0.1)  # 10 Hz
                
            except Exception as e:
                logger.error(f"Erro no monitor de pose: {e}")
                await asyncio.sleep(1.0)
    
    async def _update_current_pose(self) -> None:
        """Atualiza pose atual do robô"""
        try:
            # TODO: Obter pose real do SDK
            # Por enquanto, usar pose simulada
            self.current_pose = RobotPose(
                position=(0.0, 0.0, 0.5),  # x, y, z
                orientation=(0.0, 0.0, 0.0),  # roll, pitch, yaw
                joint_angles={}  # TODO: Obter ângulos reais
            )
            
        except Exception as e:
            logger.error(f"Erro ao atualizar pose: {e}")
    
    async def _safety_monitor(self) -> None:
        """Monitor de segurança"""
        logger.debug("Monitor de segurança iniciado")
        
        while self.is_running:
            try:
                # Verificar condições de segurança
                if self.is_moving and self.current_movement:
                    # Verificar timeout de movimento
                    elapsed = (datetime.now() - self.current_movement.timestamp).total_seconds()
                    max_duration = self.current_movement.duration or self.config.safety.timeout
                    
                    if elapsed > max_duration * 2:  # 2x o tempo esperado
                        logger.warning(f"Movimento excedeu timeout: {elapsed:.1f}s")
                        await self.stop_movement()
                
                await asyncio.sleep(1.0)  # Verificar a cada segundo
                
            except Exception as e:
                logger.error(f"Erro no monitor de segurança: {e}")
                await asyncio.sleep(1.0)
    
    async def _health_monitor(self) -> None:
        """Monitor de saúde do módulo"""
        logger.debug("Monitor de saúde do movimento iniciado")
        
        while self.is_running:
            try:
                # Calcular saúde baseada em erros recentes
                total_movements = self.stats["movements_executed"]
                error_rate = self.stats["movement_errors"] / max(total_movements, 1)
                
                # Atualizar saúde
                if error_rate < 0.1:
                    self.health = 1.0
                elif error_rate < 0.3:
                    self.health = 0.7
                else:
                    self.health = 0.3
                
                # Considerar paradas de emergência
                if self.stats["emergency_stops"] > 3:
                    self.health = min(self.health, 0.5)
                
                # Atualizar status na máquina de estados
                current_state = ModuleState.ACTIVE if self.health > 0.5 else ModuleState.ERROR
                if self.emergency_stop_active:
                    current_state = ModuleState.ERROR
                
                state_machine.update_module_status(
                    "motion_manager", 
                    current_state, 
                    health=self.health
                )
                
                await asyncio.sleep(10.0)  # Verificar a cada 10 segundos
                
            except Exception as e:
                logger.error(f"Erro no monitor de saúde: {e}")
                await asyncio.sleep(1.0)
    
    # === Métodos Utilitários ===
    
    def register_movement_callback(self, callback: Callable) -> None:
        """Registra callback para eventos de movimento"""
        self.movement_callbacks.append(callback)
        logger.debug("Callback de movimento registrado")
    
    def register_pose_callback(self, callback: Callable) -> None:
        """Registra callback para atualizações de pose"""
        self.pose_callbacks.append(callback)
        logger.debug("Callback de pose registrado")
    
    def get_available_gestures(self) -> List[str]:
        """Retorna lista de gestos disponíveis"""
        return list(self.gesture_library.keys())
    
    def get_gesture_info(self, gesture_name: str) -> Optional[Dict[str, Any]]:
        """Retorna informações sobre um gesto específico"""
        return self.gesture_library.get(gesture_name)
    
    def get_current_pose(self) -> Optional[RobotPose]:
        """Retorna pose atual do robô"""
        return self.current_pose
    
    def is_movement_active(self) -> bool:
        """Verifica se há movimento ativo"""
        return self.is_moving
    
    def get_movement_queue_size(self) -> int:
        """Retorna tamanho da fila de movimentos"""
        return self.movement_queue.qsize()
    
    def get_status(self) -> Dict[str, Any]:
        """Retorna status atual do módulo"""
        uptime = time.time() - self.stats["uptime"] if self.stats["uptime"] else 0
        
        return {
            "name": "motion_manager",
            "initialized": self.is_initialized,
            "running": self.is_running,
            "health": self.health,
            "last_error": self.last_error,
            "state": {
                "moving": self.is_moving,
                "emergency_stop": self.emergency_stop_active,
                "current_movement": self.current_movement.id if self.current_movement else None,
                "queue_size": self.movement_queue.qsize()
            },
            "pose": {
                "position": self.current_pose.position if self.current_pose else None,
                "orientation": self.current_pose.orientation if self.current_pose else None
            },
            "gestures": {
                "available": len(self.gesture_library),
                "library": list(self.gesture_library.keys())
            },
            "statistics": {
                **self.stats,
                "uptime": uptime,
                "error_rate": self.stats["movement_errors"] / max(self.stats["movements_executed"], 1)
            }
        }