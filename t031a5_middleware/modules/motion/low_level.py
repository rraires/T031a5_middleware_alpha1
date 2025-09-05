#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Low Level Controller - Controle de Baixo Nível

Controlador responsável por controle preciso de motores,
articulações individuais e movimentos de baixo nível.
"""

import asyncio
import logging
import time
import math
from typing import Optional, Dict, Any, List

logger = logging.getLogger(__name__)

class LowLevelController:
    """Controlador de movimento de baixo nível"""
    
    def __init__(self, config):
        self.config = config
        
        self.is_initialized = False
        self.is_running = False
        
        # Mapeamento de articulações
        self.joint_mapping = {
            # Braços
            "left_shoulder_pitch": 0,
            "left_shoulder_roll": 1,
            "left_shoulder_yaw": 2,
            "left_elbow": 3,
            "left_wrist_roll": 4,
            "left_wrist_pitch": 5,
            "left_wrist_yaw": 6,
            
            "right_shoulder_pitch": 7,
            "right_shoulder_roll": 8,
            "right_shoulder_yaw": 9,
            "right_elbow": 10,
            "right_wrist_roll": 11,
            "right_wrist_pitch": 12,
            "right_wrist_yaw": 13,
            
            # Pernas
            "left_hip_pitch": 14,
            "left_hip_roll": 15,
            "left_hip_yaw": 16,
            "left_knee": 17,
            "left_ankle_pitch": 18,
            "left_ankle_roll": 19,
            
            "right_hip_pitch": 20,
            "right_hip_roll": 21,
            "right_hip_yaw": 22,
            "right_knee": 23,
            "right_ankle_pitch": 24,
            "right_ankle_roll": 25,
            
            # Torso
            "waist_yaw": 26,
            "waist_pitch": 27,
            "waist_roll": 28
        }
        
        # Limites de articulações (em radianos)
        self.joint_limits = {
            "left_shoulder_pitch": (-math.pi/2, math.pi/2),
            "left_shoulder_roll": (-math.pi/2, math.pi/2),
            "left_shoulder_yaw": (-math.pi, math.pi),
            "left_elbow": (0, math.pi),
            # ... outros limites
        }
        
        logger.info("LowLevelController inicializado")
    
    async def initialize(self) -> bool:
        """Inicializa o controlador"""
        try:
            # TODO: Inicializar comunicação de baixo nível
            
            self.is_initialized = True
            logger.info("LowLevelController inicializado com sucesso")
            return True
            
        except Exception as e:
            logger.error(f"Erro na inicialização do LowLevelController: {e}")
            return False
    
    async def start(self) -> bool:
        """Inicia o controlador"""
        if not self.is_initialized:
            return False
        
        self.is_running = True
        logger.info("LowLevelController iniciado")
        return True
    
    async def stop(self) -> bool:
        """Para o controlador"""
        self.is_running = False
        logger.info("LowLevelController parado")
        return True
    
    async def cleanup(self) -> None:
        """Limpa recursos"""
        if self.is_running:
            await self.stop()
        
        logger.info("LowLevelController limpo")
    
    async def set_joint_position(self, joint_name: str, position: float, 
                               duration: float = 1.0) -> None:
        """Define posição de uma articulação específica"""
        try:
            if joint_name not in self.joint_mapping:
                raise ValueError(f"Articulação não encontrada: {joint_name}")
            
            # Verificar limites
            if joint_name in self.joint_limits:
                min_pos, max_pos = self.joint_limits[joint_name]
                position = max(min_pos, min(max_pos, position))
            
            joint_id = self.joint_mapping[joint_name]
            
            # TODO: Implementar controle real de articulação
            logger.info(f"Posição da articulação {joint_name} (ID: {joint_id}) definida para: {position:.3f} rad")
            
            # Simular tempo de movimento
            await asyncio.sleep(duration)
            
        except Exception as e:
            logger.error(f"Erro ao definir posição da articulação: {e}")
            raise
    
    async def set_multiple_joints(self, joint_positions: Dict[str, float], 
                                duration: float = 1.0) -> None:
        """Define posições de múltiplas articulações simultaneamente"""
        try:
            logger.info(f"Definindo posições de {len(joint_positions)} articulações")
            
            # TODO: Implementar controle coordenado de múltiplas articulações
            for joint_name, position in joint_positions.items():
                if joint_name in self.joint_mapping:
                    joint_id = self.joint_mapping[joint_name]
                    logger.debug(f"Articulação {joint_name} (ID: {joint_id}): {position:.3f} rad")
            
            # Simular tempo de movimento
            await asyncio.sleep(duration)
            
        except Exception as e:
            logger.error(f"Erro ao definir posições das articulações: {e}")
            raise
    
    async def get_joint_position(self, joint_name: str) -> float:
        """Obtém posição atual de uma articulação"""
        try:
            if joint_name not in self.joint_mapping:
                raise ValueError(f"Articulação não encontrada: {joint_name}")
            
            # TODO: Implementar leitura real da posição
            # Por enquanto, retornar posição simulada
            return 0.0
            
        except Exception as e:
            logger.error(f"Erro ao obter posição da articulação: {e}")
            raise
    
    async def get_all_joint_positions(self) -> Dict[str, float]:
        """Obtém posições de todas as articulações"""
        try:
            positions = {}
            
            for joint_name in self.joint_mapping.keys():
                positions[joint_name] = await self.get_joint_position(joint_name)
            
            return positions
            
        except Exception as e:
            logger.error(f"Erro ao obter posições das articulações: {e}")
            raise
    
    async def interpolate_to_pose(self, target_positions: Dict[str, float], 
                                duration: float = 2.0, steps: int = 50) -> None:
        """Interpola suavemente para uma pose alvo"""
        try:
            logger.info(f"Interpolando para pose alvo em {duration}s com {steps} passos")
            
            # Obter posições atuais
            current_positions = await self.get_all_joint_positions()
            
            # Calcular incrementos
            step_duration = duration / steps
            increments = {}
            
            for joint_name, target_pos in target_positions.items():
                if joint_name in current_positions:
                    current_pos = current_positions[joint_name]
                    increments[joint_name] = (target_pos - current_pos) / steps
            
            # Executar interpolação
            for step in range(steps):
                step_positions = {}
                
                for joint_name, target_pos in target_positions.items():
                    if joint_name in current_positions and joint_name in increments:
                        current_pos = current_positions[joint_name]
                        new_pos = current_pos + increments[joint_name] * (step + 1)
                        step_positions[joint_name] = new_pos
                
                await self.set_multiple_joints(step_positions, step_duration)
            
            logger.info("Interpolação para pose concluída")
            
        except Exception as e:
            logger.error(f"Erro na interpolação de pose: {e}")
            raise
    
    async def stop_movement(self) -> None:
        """Para movimento atual"""
        try:
            # TODO: Implementar parada de movimento de baixo nível
            logger.info("Movimento parado pelo controlador de baixo nível")
            
        except Exception as e:
            logger.error(f"Erro ao parar movimento: {e}")
    
    def get_joint_names(self) -> List[str]:
        """Retorna lista de nomes de articulações"""
        return list(self.joint_mapping.keys())
    
    def get_joint_limits(self, joint_name: str) -> Optional[Tuple[float, float]]:
        """Retorna limites de uma articulação"""
        return self.joint_limits.get(joint_name)