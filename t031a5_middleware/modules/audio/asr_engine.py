#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
ASR Engine - Sistema de Reconhecimento de Fala

Engine responsável pela conversão de fala em texto,
com suporte a diferentes idiomas e configurações.
"""

import asyncio
import logging
import threading
import time
from typing import Optional, Dict, Any

try:
    import speech_recognition as sr
    import pyaudio
except ImportError as e:
    logging.warning(f"Bibliotecas de ASR não disponíveis: {e}")
    sr = None
    pyaudio = None

logger = logging.getLogger(__name__)

class ASREngine:
    """Engine de Automatic Speech Recognition"""
    
    def __init__(self, config):
        self.config = config
        self.recognizer = None
        self.microphone = None
        self.is_initialized = False
        self.is_running = False
        self.is_listening = False
        
        # Configurações de áudio
        self.sample_rate = 16000
        self.chunk_size = 1024
        
        logger.info("ASREngine inicializado")
    
    async def initialize(self) -> bool:
        """Inicializa o engine ASR"""
        try:
            if sr is None:
                logger.warning("speech_recognition não disponível, usando modo simulação")
                self.is_initialized = True
                return True
            
            # Inicializar em thread separada
            loop = asyncio.get_event_loop()
            success = await loop.run_in_executor(None, self._init_engine)
            
            if success:
                self.is_initialized = True
                logger.info("ASREngine inicializado com sucesso")
                return True
            else:
                logger.error("Falha na inicialização do ASREngine")
                return False
                
        except Exception as e:
            logger.error(f"Erro na inicialização do ASR: {e}")
            return False
    
    def _init_engine(self) -> bool:
        """Inicializa engine speech_recognition (executado em thread)"""
        try:
            # Inicializar recognizer
            self.recognizer = sr.Recognizer()
            
            # Configurar parâmetros
            self.recognizer.energy_threshold = self.config.energy_threshold
            self.recognizer.dynamic_energy_threshold = True
            self.recognizer.pause_threshold = 0.8
            self.recognizer.phrase_threshold = 0.3
            
            # Inicializar microfone
            self.microphone = sr.Microphone()
            
            # Calibrar para ruído ambiente
            with self.microphone as source:
                logger.info("Calibrando para ruído ambiente...")
                self.recognizer.adjust_for_ambient_noise(source, duration=1)
            
            logger.info(f"ASR inicializado - Threshold: {self.recognizer.energy_threshold}")
            return True
            
        except Exception as e:
            logger.error(f"Erro na inicialização do engine ASR: {e}")
            return False
    
    async def start(self) -> bool:
        """Inicia o engine ASR"""
        if not self.is_initialized:
            logger.error("ASREngine não foi inicializado")
            return False
        
        if self.is_running:
            return True
        
        try:
            self.is_running = True
            logger.info("ASREngine iniciado")
            return True
            
        except Exception as e:
            logger.error(f"Erro ao iniciar ASREngine: {e}")
            return False
    
    async def stop(self) -> bool:
        """Para o engine ASR"""
        if not self.is_running:
            return True
        
        try:
            self.is_running = False
            self.is_listening = False
            
            logger.info("ASREngine parado")
            return True
            
        except Exception as e:
            logger.error(f"Erro ao parar ASREngine: {e}")
            return False
    
    async def cleanup(self) -> None:
        """Limpa recursos do engine"""
        try:
            if self.is_running:
                await self.stop()
            
            self.recognizer = None
            self.microphone = None
            
            logger.info("Recursos do ASREngine limpos")
            
        except Exception as e:
            logger.error(f"Erro na limpeza do ASREngine: {e}")
    
    async def recognize(self, duration: Optional[float] = None) -> Dict[str, Any]:
        """Reconhece fala do microfone"""
        if not self.is_running:
            raise RuntimeError("ASREngine não está em execução")
        
        try:
            self.is_listening = True
            timeout = duration or self.config.timeout
            
            logger.info(f"Iniciando reconhecimento (timeout: {timeout}s)")
            
            # Executar reconhecimento em thread
            loop = asyncio.get_event_loop()
            result = await loop.run_in_executor(
                None, 
                self._recognize_sync, 
                timeout
            )
            
            return result
            
        except Exception as e:
            logger.error(f"Erro no reconhecimento ASR: {e}")
            return {
                "success": False,
                "text": "",
                "confidence": 0.0,
                "error": str(e)
            }
        
        finally:
            self.is_listening = False
    
    def _recognize_sync(self, timeout: float) -> Dict[str, Any]:
        """Executa reconhecimento síncrono (executado em thread)"""
        try:
            if self.recognizer is None or self.microphone is None:
                # Modo simulação
                logger.info("ASR (simulação): reconhecimento simulado")
                time.sleep(min(timeout, 2.0))  # Simular tempo de processamento
                return {
                    "success": True,
                    "text": "Texto simulado do ASR",
                    "confidence": 0.95,
                    "language": self.config.language
                }
            
            # Capturar áudio
            with self.microphone as source:
                logger.debug("Escutando...")
                audio = self.recognizer.listen(
                    source, 
                    timeout=timeout, 
                    phrase_time_limit=timeout
                )
            
            # Reconhecer usando Google Speech Recognition
            logger.debug("Processando áudio...")
            text = self.recognizer.recognize_google(
                audio, 
                language=self.config.language
            )
            
            result = {
                "success": True,
                "text": text,
                "confidence": 0.8,  # Google API não retorna confidence
                "language": self.config.language,
                "duration": timeout
            }
            
            logger.info(f"ASR resultado: '{text}'")
            return result
            
        except sr.WaitTimeoutError:
            logger.warning("Timeout no reconhecimento ASR")
            return {
                "success": False,
                "text": "",
                "confidence": 0.0,
                "error": "Timeout - nenhuma fala detectada"
            }
        
        except sr.UnknownValueError:
            logger.warning("Fala não compreendida")
            return {
                "success": False,
                "text": "",
                "confidence": 0.0,
                "error": "Fala não compreendida"
            }
        
        except sr.RequestError as e:
            logger.error(f"Erro no serviço de reconhecimento: {e}")
            return {
                "success": False,
                "text": "",
                "confidence": 0.0,
                "error": f"Erro no serviço: {e}"
            }
        
        except Exception as e:
            logger.error(f"Erro no reconhecimento síncrono: {e}")
            return {
                "success": False,
                "text": "",
                "confidence": 0.0,
                "error": str(e)
            }
    
    async def calibrate(self, duration: float = 1.0) -> bool:
        """Calibra o microfone para ruído ambiente"""
        try:
            if self.recognizer is None or self.microphone is None:
                logger.info("Calibração (simulação)")
                return True
            
            logger.info(f"Calibrando microfone ({duration}s)...")
            
            # Executar calibração em thread
            loop = asyncio.get_event_loop()
            success = await loop.run_in_executor(
                None, 
                self._calibrate_sync, 
                duration
            )
            
            return success
            
        except Exception as e:
            logger.error(f"Erro na calibração: {e}")
            return False
    
    def _calibrate_sync(self, duration: float) -> bool:
        """Executa calibração síncrona (executado em thread)"""
        try:
            with self.microphone as source:
                self.recognizer.adjust_for_ambient_noise(source, duration=duration)
            
            logger.info(f"Calibração concluída - Threshold: {self.recognizer.energy_threshold}")
            return True
            
        except Exception as e:
            logger.error(f"Erro na calibração síncrona: {e}")
            return False
    
    def set_energy_threshold(self, threshold: int) -> None:
        """Define threshold de energia para detecção de fala"""
        try:
            if self.recognizer:
                self.recognizer.energy_threshold = threshold
                logger.info(f"Energy threshold definido: {threshold}")
            
        except Exception as e:
            logger.error(f"Erro ao definir energy threshold: {e}")
    
    def get_energy_threshold(self) -> int:
        """Retorna threshold de energia atual"""
        if self.recognizer:
            return self.recognizer.energy_threshold
        return self.config.energy_threshold
    
    async def emergency_stop(self) -> None:
        """Para imediatamente qualquer reconhecimento em andamento"""
        logger.warning("Parada de emergência do ASR")
        
        try:
            self.is_listening = False
            # Note: speech_recognition não tem método de parada explícito
            # O reconhecimento em andamento continuará até completar
            
        except Exception as e:
            logger.error(f"Erro na parada de emergência do ASR: {e}")