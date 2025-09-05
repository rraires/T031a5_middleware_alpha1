#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
AudioManager - Gerenciador de Áudio do Middleware t031a5

Responsável por coordenar todas as operações de áudio do robô G1,
incluindo TTS, ASR, controle de volume e integração com SDK Unitree.
"""

import asyncio
import logging
import threading
import queue
import time
from typing import Optional, Dict, Any, Callable, List
from datetime import datetime
import json
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
from ...core.state_machine import state_machine, ModuleState
from .tts_engine import TTSEngine
from .asr_engine import ASREngine

logger = logging.getLogger(__name__)

class AudioManager:
    """Gerenciador principal do sistema de áudio"""
    
    def __init__(self):
        self.config = config_manager.get_config().audio
        self.network_config = config_manager.get_config().network
        
        # Componentes principais
        self.unitree_client: Optional[AudioClient] = None
        self.tts_engine: Optional[TTSEngine] = None
        self.asr_engine: Optional[ASREngine] = None
        
        # Estado do módulo
        self.is_initialized = False
        self.is_running = False
        self.health = 1.0
        self.last_error = None
        
        # Controle de áudio
        self.current_volume = self.config.tts.volume
        self.is_speaking = False
        self.is_listening = False
        
        # Filas de processamento
        self.tts_queue = asyncio.Queue()
        self.asr_queue = asyncio.Queue()
        self.audio_events = asyncio.Queue()
        
        # Callbacks
        self.speech_callbacks: List[Callable] = []
        self.audio_callbacks: List[Callable] = []
        
        # Tarefas assíncronas
        self.tasks: List[asyncio.Task] = []
        
        # Estatísticas
        self.stats = {
            "tts_requests": 0,
            "asr_requests": 0,
            "audio_errors": 0,
            "uptime": 0,
            "last_activity": None
        }
        
        logger.info("AudioManager inicializado")
    
    async def initialize(self) -> bool:
        """Inicializa o sistema de áudio"""
        try:
            logger.info("Inicializando AudioManager...")
            
            # Registrar na máquina de estados
            state_machine.update_module_status(
                "audio_manager", 
                ModuleState.INITIALIZING, 
                health=0.5
            )
            
            # Inicializar SDK Unitree
            if not await self._initialize_unitree_sdk():
                raise RuntimeError("Falha na inicialização do SDK Unitree")
            
            # Inicializar engines TTS e ASR
            await self._initialize_engines()
            
            # Configurar volume inicial
            await self.set_volume(self.config.tts.volume)
            
            # Marcar como inicializado
            self.is_initialized = True
            self.health = 1.0
            
            state_machine.update_module_status(
                "audio_manager", 
                ModuleState.READY, 
                health=self.health
            )
            
            logger.info("AudioManager inicializado com sucesso")
            return True
            
        except Exception as e:
            logger.error(f"Erro na inicialização do AudioManager: {e}")
            self.last_error = str(e)
            self.health = 0.0
            
            state_machine.update_module_status(
                "audio_manager", 
                ModuleState.ERROR, 
                health=self.health
            )
            
            return False
    
    async def _initialize_unitree_sdk(self) -> bool:
        """Inicializa o SDK Unitree para áudio"""
        try:
            if AudioClient is None:
                logger.warning("SDK Unitree não disponível, usando modo simulação")
                return True
            
            # Inicializar factory de canais
            ChannelFactoryInitialize(0, self.network_config.interface)
            
            # Criar cliente de áudio
            self.unitree_client = AudioClient()
            self.unitree_client.Init()
            
            logger.info("SDK Unitree Audio inicializado")
            return True
            
        except Exception as e:
            logger.error(f"Erro na inicialização do SDK Unitree: {e}")
            return False
    
    async def _initialize_engines(self) -> None:
        """Inicializa engines TTS e ASR"""
        # Inicializar TTS Engine
        self.tts_engine = TTSEngine(self.config.tts)
        await self.tts_engine.initialize()
        
        # Inicializar ASR Engine
        self.asr_engine = ASREngine(self.config.asr)
        await self.asr_engine.initialize()
        
        logger.info("Engines TTS e ASR inicializados")
    
    async def start(self) -> bool:
        """Inicia o sistema de áudio"""
        if not self.is_initialized:
            logger.error("AudioManager não foi inicializado")
            return False
        
        if self.is_running:
            logger.warning("AudioManager já está em execução")
            return True
        
        try:
            logger.info("Iniciando AudioManager...")
            
            # Iniciar tarefas assíncronas
            self.tasks = [
                asyncio.create_task(self._tts_processor()),
                asyncio.create_task(self._asr_processor()),
                asyncio.create_task(self._audio_monitor()),
                asyncio.create_task(self._health_monitor())
            ]
            
            # Iniciar engines
            await self.tts_engine.start()
            await self.asr_engine.start()
            
            self.is_running = True
            self.stats["uptime"] = time.time()
            
            state_machine.update_module_status(
                "audio_manager", 
                ModuleState.ACTIVE, 
                health=self.health
            )
            
            logger.info("AudioManager iniciado com sucesso")
            return True
            
        except Exception as e:
            logger.error(f"Erro ao iniciar AudioManager: {e}")
            self.last_error = str(e)
            self.health = 0.0
            
            state_machine.update_module_status(
                "audio_manager", 
                ModuleState.ERROR, 
                health=self.health
            )
            
            return False
    
    async def stop(self) -> bool:
        """Para o sistema de áudio"""
        if not self.is_running:
            return True
        
        try:
            logger.info("Parando AudioManager...")
            
            # Parar engines
            if self.tts_engine:
                await self.tts_engine.stop()
            if self.asr_engine:
                await self.asr_engine.stop()
            
            # Cancelar tarefas
            for task in self.tasks:
                if not task.done():
                    task.cancel()
            
            # Aguardar conclusão
            if self.tasks:
                await asyncio.gather(*self.tasks, return_exceptions=True)
            
            self.is_running = False
            
            state_machine.update_module_status(
                "audio_manager", 
                ModuleState.READY, 
                health=self.health
            )
            
            logger.info("AudioManager parado")
            return True
            
        except Exception as e:
            logger.error(f"Erro ao parar AudioManager: {e}")
            return False
    
    async def cleanup(self) -> None:
        """Limpa recursos do sistema de áudio"""
        try:
            logger.info("Limpando recursos do AudioManager...")
            
            # Parar se estiver rodando
            if self.is_running:
                await self.stop()
            
            # Cleanup engines
            if self.tts_engine:
                await self.tts_engine.cleanup()
            if self.asr_engine:
                await self.asr_engine.cleanup()
            
            # Limpar filas
            while not self.tts_queue.empty():
                try:
                    self.tts_queue.get_nowait()
                except asyncio.QueueEmpty:
                    break
            
            while not self.asr_queue.empty():
                try:
                    self.asr_queue.get_nowait()
                except asyncio.QueueEmpty:
                    break
            
            self.is_initialized = False
            
            logger.info("Recursos do AudioManager limpos")
            
        except Exception as e:
            logger.error(f"Erro na limpeza do AudioManager: {e}")
    
    # === Métodos de TTS ===
    
    async def speak(self, text: str, voice_id: Optional[int] = None, 
                   priority: int = 0, callback: Optional[Callable] = None) -> str:
        """Fala um texto usando TTS"""
        if not self.is_running:
            raise RuntimeError("AudioManager não está em execução")
        
        request_id = f"tts_{int(time.time() * 1000)}"
        
        tts_request = {
            "id": request_id,
            "text": text,
            "voice_id": voice_id or self.config.tts.default_voice,
            "priority": priority,
            "callback": callback,
            "timestamp": datetime.now().isoformat()
        }
        
        await self.tts_queue.put(tts_request)
        self.stats["tts_requests"] += 1
        self.stats["last_activity"] = datetime.now().isoformat()
        
        logger.info(f"Solicitação TTS enfileirada: {text[:50]}...")
        return request_id
    
    async def _tts_processor(self) -> None:
        """Processa fila de solicitações TTS"""
        logger.debug("Processador TTS iniciado")
        
        while self.is_running:
            try:
                # Aguardar solicitação com timeout
                request = await asyncio.wait_for(
                    self.tts_queue.get(), 
                    timeout=1.0
                )
                
                await self._process_tts_request(request)
                
            except asyncio.TimeoutError:
                continue
            except Exception as e:
                logger.error(f"Erro no processador TTS: {e}")
                self.stats["audio_errors"] += 1
    
    async def _process_tts_request(self, request: Dict[str, Any]) -> None:
        """Processa uma solicitação TTS individual"""
        try:
            self.is_speaking = True
            
            text = request["text"]
            voice_id = request["voice_id"]
            callback = request.get("callback")
            
            logger.info(f"Processando TTS: {text[:50]}...")
            
            # Usar SDK Unitree se disponível
            if self.unitree_client:
                code = self.unitree_client.TtsMaker(text, voice_id)
                if code != 0:
                    logger.error(f"Erro no TTS Unitree: código {code}")
                    raise RuntimeError(f"TTS falhou com código {code}")
            else:
                # Usar engine local como fallback
                await self.tts_engine.synthesize(text, voice_id)
            
            # Executar callback se fornecido
            if callback:
                try:
                    if asyncio.iscoroutinefunction(callback):
                        await callback(request)
                    else:
                        callback(request)
                except Exception as e:
                    logger.error(f"Erro em callback TTS: {e}")
            
            # Emitir evento
            await self.audio_events.put({
                "type": "tts_completed",
                "request_id": request["id"],
                "text": text,
                "timestamp": datetime.now().isoformat()
            })
            
            logger.debug(f"TTS concluído: {request['id']}")
            
        except Exception as e:
            logger.error(f"Erro no processamento TTS: {e}")
            self.stats["audio_errors"] += 1
            
            # Emitir evento de erro
            await self.audio_events.put({
                "type": "tts_error",
                "request_id": request["id"],
                "error": str(e),
                "timestamp": datetime.now().isoformat()
            })
        
        finally:
            self.is_speaking = False
    
    # === Métodos de ASR ===
    
    async def start_listening(self, duration: Optional[float] = None, 
                            callback: Optional[Callable] = None) -> str:
        """Inicia escuta para reconhecimento de fala"""
        if not self.is_running:
            raise RuntimeError("AudioManager não está em execução")
        
        request_id = f"asr_{int(time.time() * 1000)}"
        
        asr_request = {
            "id": request_id,
            "duration": duration or self.config.asr.timeout,
            "callback": callback,
            "timestamp": datetime.now().isoformat()
        }
        
        await self.asr_queue.put(asr_request)
        self.stats["asr_requests"] += 1
        self.stats["last_activity"] = datetime.now().isoformat()
        
        logger.info(f"Solicitação ASR enfileirada: {request_id}")
        return request_id
    
    async def _asr_processor(self) -> None:
        """Processa fila de solicitações ASR"""
        logger.debug("Processador ASR iniciado")
        
        while self.is_running:
            try:
                # Aguardar solicitação com timeout
                request = await asyncio.wait_for(
                    self.asr_queue.get(), 
                    timeout=1.0
                )
                
                await self._process_asr_request(request)
                
            except asyncio.TimeoutError:
                continue
            except Exception as e:
                logger.error(f"Erro no processador ASR: {e}")
                self.stats["audio_errors"] += 1
    
    async def _process_asr_request(self, request: Dict[str, Any]) -> None:
        """Processa uma solicitação ASR individual"""
        try:
            self.is_listening = True
            
            duration = request["duration"]
            callback = request.get("callback")
            
            logger.info(f"Processando ASR: {request['id']}")
            
            # Usar engine ASR
            result = await self.asr_engine.recognize(duration)
            
            # Executar callback se fornecido
            if callback:
                try:
                    if asyncio.iscoroutinefunction(callback):
                        await callback(request, result)
                    else:
                        callback(request, result)
                except Exception as e:
                    logger.error(f"Erro em callback ASR: {e}")
            
            # Emitir evento
            await self.audio_events.put({
                "type": "asr_completed",
                "request_id": request["id"],
                "result": result,
                "timestamp": datetime.now().isoformat()
            })
            
            logger.info(f"ASR concluído: {result.get('text', 'N/A')}")
            
        except Exception as e:
            logger.error(f"Erro no processamento ASR: {e}")
            self.stats["audio_errors"] += 1
            
            # Emitir evento de erro
            await self.audio_events.put({
                "type": "asr_error",
                "request_id": request["id"],
                "error": str(e),
                "timestamp": datetime.now().isoformat()
            })
        
        finally:
            self.is_listening = False
    
    # === Controle de Volume ===
    
    async def set_volume(self, volume: int) -> bool:
        """Define o volume do sistema"""
        try:
            # Validar volume
            volume = max(0, min(100, volume))
            
            if self.unitree_client:
                code = self.unitree_client.SetVolume(volume)
                if code != 0:
                    logger.error(f"Erro ao definir volume: código {code}")
                    return False
            
            self.current_volume = volume
            logger.info(f"Volume definido para: {volume}%")
            
            # Emitir evento
            await self.audio_events.put({
                "type": "volume_changed",
                "volume": volume,
                "timestamp": datetime.now().isoformat()
            })
            
            return True
            
        except Exception as e:
            logger.error(f"Erro ao definir volume: {e}")
            return False
    
    async def get_volume(self) -> int:
        """Obtém o volume atual"""
        try:
            if self.unitree_client:
                code, data = self.unitree_client.GetVolume()
                if code == 0 and data:
                    self.current_volume = data.get("volume", self.current_volume)
            
            return self.current_volume
            
        except Exception as e:
            logger.error(f"Erro ao obter volume: {e}")
            return self.current_volume
    
    # === Monitoramento ===
    
    async def _audio_monitor(self) -> None:
        """Monitor de eventos de áudio"""
        logger.debug("Monitor de áudio iniciado")
        
        while self.is_running:
            try:
                # Processar eventos de áudio
                event = await asyncio.wait_for(
                    self.audio_events.get(), 
                    timeout=1.0
                )
                
                # Notificar callbacks registrados
                for callback in self.audio_callbacks:
                    try:
                        if asyncio.iscoroutinefunction(callback):
                            await callback(event)
                        else:
                            callback(event)
                    except Exception as e:
                        logger.error(f"Erro em callback de áudio: {e}")
                
            except asyncio.TimeoutError:
                continue
            except Exception as e:
                logger.error(f"Erro no monitor de áudio: {e}")
    
    async def _health_monitor(self) -> None:
        """Monitor de saúde do módulo"""
        logger.debug("Monitor de saúde do áudio iniciado")
        
        while self.is_running:
            try:
                # Calcular saúde baseada em erros recentes
                total_requests = self.stats["tts_requests"] + self.stats["asr_requests"]
                error_rate = self.stats["audio_errors"] / max(total_requests, 1)
                
                # Atualizar saúde
                if error_rate < 0.1:
                    self.health = 1.0
                elif error_rate < 0.3:
                    self.health = 0.7
                else:
                    self.health = 0.3
                
                # Atualizar status na máquina de estados
                state_machine.update_module_status(
                    "audio_manager", 
                    ModuleState.ACTIVE if self.health > 0.5 else ModuleState.ERROR, 
                    health=self.health
                )
                
                await asyncio.sleep(10.0)  # Verificar a cada 10 segundos
                
            except Exception as e:
                logger.error(f"Erro no monitor de saúde: {e}")
                await asyncio.sleep(1.0)
    
    # === Métodos Utilitários ===
    
    def register_audio_callback(self, callback: Callable) -> None:
        """Registra callback para eventos de áudio"""
        self.audio_callbacks.append(callback)
        logger.debug("Callback de áudio registrado")
    
    def register_speech_callback(self, callback: Callable) -> None:
        """Registra callback para eventos de fala"""
        self.speech_callbacks.append(callback)
        logger.debug("Callback de fala registrado")
    
    def get_status(self) -> Dict[str, Any]:
        """Retorna status atual do módulo"""
        uptime = time.time() - self.stats["uptime"] if self.stats["uptime"] else 0
        
        return {
            "name": "audio_manager",
            "initialized": self.is_initialized,
            "running": self.is_running,
            "health": self.health,
            "last_error": self.last_error,
            "state": {
                "speaking": self.is_speaking,
                "listening": self.is_listening,
                "volume": self.current_volume
            },
            "queues": {
                "tts_pending": self.tts_queue.qsize(),
                "asr_pending": self.asr_queue.qsize(),
                "events_pending": self.audio_events.qsize()
            },
            "statistics": {
                **self.stats,
                "uptime": uptime,
                "error_rate": self.stats["audio_errors"] / max(
                    self.stats["tts_requests"] + self.stats["asr_requests"], 1
                )
            }
        }
    
    async def emergency_stop(self) -> None:
        """Para todas as operações de áudio imediatamente"""
        logger.warning("Parada de emergência do áudio")
        
        self.is_speaking = False
        self.is_listening = False
        
        # Limpar filas
        while not self.tts_queue.empty():
            try:
                self.tts_queue.get_nowait()
            except asyncio.QueueEmpty:
                break
        
        while not self.asr_queue.empty():
            try:
                self.asr_queue.get_nowait()
            except asyncio.QueueEmpty:
                break
        
        # Parar engines
        if self.tts_engine:
            await self.tts_engine.emergency_stop()
        if self.asr_engine:
            await self.asr_engine.emergency_stop()