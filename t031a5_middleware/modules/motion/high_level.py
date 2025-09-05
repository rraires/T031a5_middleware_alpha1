#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
High Level Controller - Controle de Alto Nível

Controlador responsável por movimentos de alto nível como
locomoção, gestos predefinidos e ações coordenadas.
"""

import asyncio
import logging
import time
from typing import Optional, Dict, Any

logger = logging.getLogger(__name__)

class HighLevelController:
    """Controlador de movimento de alto nível"""
    
    def __init__(self, loco_client, arm_client, config):
        self.loco_client = loco_client
        self.arm_client = arm_client
        self.config = config
        
        self.is_initialized = False
        self.is_running = False
        
        logger.info("HighLevelController inicializado")
    
    async def initialize(self) -> bool:
        """Inicializa o controlador"""
        try:
            # Configurações iniciais
            if self.loco_client:
                # Configurar modo de locomoção
                self.loco_client.Start()  # Iniciar modo de locomoção
            
            self.is_initialized = True
            logger.info("HighLevelController inicializado com sucesso")
            return True
            
        except Exception as e:
            logger.error(f"Erro na inicialização do HighLevelController: {e}")
            return False
    
    async def start(self) -> bool:
        """Inicia o controlador"""
        if not self.is_initialized:
            return False
        
        self.is_running = True
        logger.info("HighLevelController iniciado")
        return True
    
    async def stop(self) -> bool:
        """Para o controlador"""
        self.is_running = False
        logger.info("HighLevelController parado")
        return True
    
    async def cleanup(self) -> None:
        """Limpa recursos"""
        if self.is_running:
            await self.stop()
        
        logger.info("HighLevelController limpo")
    
    async def move(self, vx: float, vy: float, omega: float, duration: float) -> None:
        """Move o robô com velocidades especificadas"""
        try:
            if self.loco_client:
                # Usar SDK Unitree
                self.loco_client.SetVelocity(vx, vy, omega, duration)
                logger.info(f"Movimento executado: vx={vx}, vy={vy}, omega={omega}, duration={duration}")
            else:
                # Modo simulação
                logger.info(f"Movimento simulado: vx={vx}, vy={vy}, omega={omega}, duration={duration}")
            
            # Aguardar duração do movimento
            await asyncio.sleep(duration)
            
        except Exception as e:
            logger.error(f"Erro no movimento: {e}")
            raise
    
    async def perform_arm_action(self, arm: str, action: str, duration: float, 
                               parameters: Dict[str, Any] = None) -> None:
        """Executa ação de braço"""
        try:
            if self.arm_client:
                # Mapear ações para IDs do SDK
                action_mapping = {
                    "wave": 1,
                    "handshake": 2,
                    "point": 3,
                    "thinking": 4,
                    "celebrate": 5
                }
                
                action_id = action_mapping.get(action, 1)
                
                # Executar ação
                code = self.arm_client.ExecuteAction(action_id)
                if code != 0:
                    logger.error(f"Erro na execução da ação de braço: código {code}")
                
                logger.info(f"Ação de braço executada: {arm} - {action}")
            else:
                # Modo simulação
                logger.info(f"Ação de braço simulada: {arm} - {action}")
            
            # Aguardar duração da ação
            await asyncio.sleep(duration)
            
        except Exception as e:
            logger.error(f"Erro na ação de braço: {e}")
            raise
    
    async def stop_movement(self) -> None:
        """Para movimento atual"""
        try:
            if self.loco_client:
                self.loco_client.StopMove()
            
            logger.info("Movimento parado pelo controlador de alto nível")
            
        except Exception as e:
            logger.error(f"Erro ao parar movimento: {e}")