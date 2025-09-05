#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
TTS Engine - Sistema de Síntese de Voz

Engine responsável pela conversão de texto em fala,
com suporte a múltiplas vozes e configurações.
"""

import asyncio
import logging
import threading
from typing import Optional, Dict, Any, List
import tempfile
import os

try:
    import pyttsx3
except ImportError:
    pyttsx3 = None
    logging.warning("pyttsx3 não disponível")

logger = logging.getLogger(__name__)

class TTSEngine:
    """Engine de Text-to-Speech"""
    
    def __init__(self, config):
        self.config = config
        self.engine = None
        self.is_initialized = False
        self.is_running = False
        self.current_voice = config.default_voice
        self.available_voices: List[Dict] = []
        
        # Thread para operações síncronas do pyttsx3
        self.tts_thread = None
        self.tts_queue = None
        self.stop_event = threading.Event()
        
        logger.info("TTSEngine inicializado")
    
    async def initialize(self) -> bool:
        """Inicializa o engine TTS"""
        try:
            if pyttsx3 is None:
                logger.warning("pyttsx3 não disponível, usando modo simulação")
                self.is_initialized = True
                return True
            
            # Inicializar em thread separada (pyttsx3 é síncrono)
            loop = asyncio.get_event_loop()
            success = await loop.run_in_executor(None, self._init_engine)
            
            if success:
                self.is_initialized = True
                logger.info("TTSEngine inicializado com sucesso")
                return True
            else:
                logger.error("Falha na inicialização do TTSEngine")
                return False
                
        except Exception as e:
            logger.error(f"Erro na inicialização do TTS: {e}")
            return False
    
    def _init_engine(self) -> bool:
        """Inicializa engine pyttsx3 (executado em thread)"""
        try:
            self.engine = pyttsx3.init()
            
            # Configurar propriedades
            self.engine.setProperty('rate', 150)  # Velocidade
            self.engine.setProperty('volume', self.config.volume / 100.0)
            
            # Obter vozes disponíveis
            voices = self.engine.getProperty('voices')
            self.available_voices = [
                {
                    "id": i,
                    "name": voice.name,
                    "language": getattr(voice, 'languages', ['unknown'])[0]
                }
                for i, voice in enumerate(voices)
            ]
            
            # Definir voz padrão
            if self.available_voices and self.current_voice < len(self.available_voices):
                self.engine.setProperty('voice', voices[self.current_voice].id)
            
            logger.info(f"TTS inicializado com {len(self.available_voices)} vozes")
            return True
            
        except Exception as e:
            logger.error(f"Erro na inicialização do engine TTS: {e}")
            return False
    
    async def start(self) -> bool:
        """Inicia o engine TTS"""
        if not self.is_initialized:
            logger.error("TTSEngine não foi inicializado")
            return False
        
        if self.is_running:
            return True
        
        try:
            # Iniciar thread de processamento
            self.tts_queue = asyncio.Queue()
            self.stop_event.clear()
            
            self.tts_thread = threading.Thread(
                target=self._tts_worker,
                daemon=True
            )
            self.tts_thread.start()
            
            self.is_running = True
            logger.info("TTSEngine iniciado")
            return True
            
        except Exception as e:
            logger.error(f"Erro ao iniciar TTSEngine: {e}")
            return False
    
    async def stop(self) -> bool:
        """Para o engine TTS"""
        if not self.is_running:
            return True
        
        try:
            # Sinalizar parada
            self.stop_event.set()
            
            # Aguardar thread terminar
            if self.tts_thread and self.tts_thread.is_alive():
                self.tts_thread.join(timeout=5.0)
            
            self.is_running = False
            logger.info("TTSEngine parado")
            return True
            
        except Exception as e:
            logger.error(f"Erro ao parar TTSEngine: {e}")
            return False
    
    async def cleanup(self) -> None:
        """Limpa recursos do engine"""
        try:
            if self.is_running:
                await self.stop()
            
            if self.engine:
                # pyttsx3 não tem método de cleanup explícito
                self.engine = None
            
            logger.info("Recursos do TTSEngine limpos")
            
        except Exception as e:
            logger.error(f"Erro na limpeza do TTSEngine: {e}")
    
    async def synthesize(self, text: str, voice_id: Optional[int] = None) -> bool:
        """Sintetiza texto em fala"""
        if not self.is_running:
            raise RuntimeError("TTSEngine não está em execução")
        
        try:
            # Preparar solicitação
            request = {
                "text": text,
                "voice_id": voice_id or self.current_voice,
                "timestamp": asyncio.get_event_loop().time()
            }
            
            # Executar síntese em thread
            loop = asyncio.get_event_loop()
            success = await loop.run_in_executor(None, self._synthesize_sync, request)
            
            return success
            
        except Exception as e:
            logger.error(f"Erro na síntese TTS: {e}")
            return False
    
    def _synthesize_sync(self, request: Dict[str, Any]) -> bool:
        """Executa síntese síncrona (executado em thread)"""
        try:
            if self.engine is None:
                # Modo simulação
                logger.info(f"TTS (simulação): {request['text'][:50]}...")
                return True
            
            text = request["text"]
            voice_id = request["voice_id"]
            
            # Trocar voz se necessário
            if voice_id != self.current_voice and voice_id < len(self.available_voices):
                voices = self.engine.getProperty('voices')
                self.engine.setProperty('voice', voices[voice_id].id)
                self.current_voice = voice_id
            
            # Sintetizar e reproduzir
            self.engine.say(text)
            self.engine.runAndWait()
            
            logger.debug(f"TTS concluído: {text[:30]}...")
            return True
            
        except Exception as e:
            logger.error(f"Erro na síntese síncrona: {e}")
            return False
    
    def _tts_worker(self) -> None:
        """Worker thread para processamento TTS"""
        logger.debug("Worker TTS iniciado")
        
        while not self.stop_event.is_set():
            try:
                # Aguardar por solicitações
                # Nota: Esta é uma implementação simplificada
                # Em produção, usaria uma queue thread-safe
                self.stop_event.wait(0.1)
                
            except Exception as e:
                logger.error(f"Erro no worker TTS: {e}")
        
        logger.debug("Worker TTS finalizado")
    
    async def set_voice(self, voice_id: int) -> bool:
        """Define a voz ativa"""
        try:
            if voice_id < 0 or voice_id >= len(self.available_voices):
                logger.error(f"ID de voz inválido: {voice_id}")
                return False
            
            self.current_voice = voice_id
            logger.info(f"Voz alterada para: {self.available_voices[voice_id]['name']}")
            return True
            
        except Exception as e:
            logger.error(f"Erro ao definir voz: {e}")
            return False
    
    async def set_speed(self, speed: float) -> bool:
        """Define a velocidade da fala"""
        try:
            if self.engine:
                # Converter para rate do pyttsx3 (palavras por minuto)
                rate = int(150 * speed)  # 150 WPM base
                self.engine.setProperty('rate', rate)
            
            logger.info(f"Velocidade da fala definida: {speed}x")
            return True
            
        except Exception as e:
            logger.error(f"Erro ao definir velocidade: {e}")
            return False
    
    def get_voices(self) -> List[Dict[str, Any]]:
        """Retorna lista de vozes disponíveis"""
        return self.available_voices.copy()
    
    def get_current_voice(self) -> int:
        """Retorna ID da voz atual"""
        return self.current_voice
    
    async def emergency_stop(self) -> None:
        """Para imediatamente qualquer síntese em andamento"""
        logger.warning("Parada de emergência do TTS")
        
        try:
            if self.engine:
                self.engine.stop()
            
            self.stop_event.set()
            
        except Exception as e:
            logger.error(f"Erro na parada de emergência do TTS: {e}")