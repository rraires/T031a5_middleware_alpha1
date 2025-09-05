#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Gerenciador de Configuração do Middleware t031a5

Responsável por carregar, validar e gerenciar todas as configurações
do sistema de orquestração do robô Unitree G1.
"""

import os
import yaml
from typing import Dict, Any, Optional
from pathlib import Path
from pydantic import BaseModel, Field, validator
import logging

logger = logging.getLogger(__name__)

class NetworkConfig(BaseModel):
    """Configurações de rede"""
    interface: str = Field(default="enp2s0", description="Interface de rede")
    robot_ip: str = Field(default="192.168.123.15", description="IP do robô G1")
    middleware_port: int = Field(default=8080, ge=1024, le=65535)
    websocket_port: int = Field(default=8081, ge=1024, le=65535)
    streaming_port: int = Field(default=8082, ge=1024, le=65535)

class AudioConfig(BaseModel):
    """Configurações de áudio"""
    sample_rate: int = Field(default=16000, ge=8000, le=48000)
    channels: int = Field(default=1, ge=1, le=2)
    chunk_size: int = Field(default=1024, ge=256, le=4096)
    format: str = Field(default="int16")
    
    class TTSConfig(BaseModel):
        default_voice: int = Field(default=0, ge=0)
        volume: int = Field(default=80, ge=0, le=100)
        speed: float = Field(default=1.0, ge=0.5, le=2.0)
    
    class ASRConfig(BaseModel):
        language: str = Field(default="pt-BR")
        timeout: float = Field(default=5.0, ge=1.0, le=30.0)
        energy_threshold: int = Field(default=300, ge=100, le=1000)
    
    tts: TTSConfig = TTSConfig()
    asr: ASRConfig = ASRConfig()

class VideoConfig(BaseModel):
    """Configurações de vídeo"""
    class Resolution(BaseModel):
        width: int = Field(default=640, ge=320, le=1920)
        height: int = Field(default=480, ge=240, le=1080)
    
    class Streaming(BaseModel):
        protocol: str = Field(default="webrtc")
        bitrate: int = Field(default=1000000, ge=100000, le=10000000)
    
    resolution: Resolution = Resolution()
    fps: int = Field(default=30, ge=15, le=60)
    codec: str = Field(default="h264")
    quality: int = Field(default=80, ge=10, le=100)
    streaming: Streaming = Streaming()

class MotionConfig(BaseModel):
    """Configurações de movimento"""
    class Safety(BaseModel):
        emergency_stop: bool = Field(default=True)
        max_velocity: float = Field(default=1.0, ge=0.1, le=3.0)
        timeout: float = Field(default=2.0, ge=0.5, le=10.0)
    
    class Interpolation(BaseModel):
        smooth_factor: float = Field(default=0.8, ge=0.1, le=1.0)
        transition_time: float = Field(default=1.0, ge=0.1, le=5.0)
    
    class Gestures(BaseModel):
        library_path: str = Field(default="./data/gestures/")
    
    safety: Safety = Safety()
    interpolation: Interpolation = Interpolation()
    gestures: Gestures = Gestures()

class LEDConfig(BaseModel):
    """Configurações de LEDs"""
    brightness: int = Field(default=80, ge=0, le=100)
    transition_speed: float = Field(default=0.5, ge=0.1, le=2.0)
    
    class Patterns(BaseModel):
        idle: str = Field(default="breathing")
        listening: str = Field(default="pulse_blue")
        speaking: str = Field(default="wave_green")
        error: str = Field(default="flash_red")
    
    patterns: Patterns = Patterns()

class AIConfig(BaseModel):
    """Configurações de IA/LLM"""
    provider: str = Field(default="openai")
    model: str = Field(default="gpt-4-turbo")
    real_time_api: bool = Field(default=True)
    max_tokens: int = Field(default=150, ge=50, le=1000)
    temperature: float = Field(default=0.7, ge=0.0, le=2.0)
    
    class Personality(BaseModel):
        style: str = Field(default="friendly")
        energy_level: str = Field(default="medium")
        responsiveness: str = Field(default="high")
    
    personality: Personality = Personality()

class SystemConfig(BaseModel):
    """Configuração principal do sistema"""
    general: Dict[str, Any] = Field(default_factory=dict)
    network: NetworkConfig = NetworkConfig()
    audio: AudioConfig = AudioConfig()
    video: VideoConfig = VideoConfig()
    motion: MotionConfig = MotionConfig()
    leds: LEDConfig = LEDConfig()
    ai: AIConfig = AIConfig()
    logging: Dict[str, Any] = Field(default_factory=dict)
    performance: Dict[str, Any] = Field(default_factory=dict)

class ConfigManager:
    """Gerenciador central de configurações"""
    
    def __init__(self, config_path: Optional[str] = None):
        self.config_path = config_path or self._find_config_file()
        self.config: Optional[SystemConfig] = None
        self._load_config()
    
    def _find_config_file(self) -> str:
        """Encontra o arquivo de configuração"""
        possible_paths = [
            "config/config.yaml",
            "../config/config.yaml",
            "/etc/t031a5/config.yaml",
            os.path.expanduser("~/.t031a5/config.yaml")
        ]
        
        for path in possible_paths:
            if os.path.exists(path):
                return path
        
        raise FileNotFoundError("Arquivo de configuração não encontrado")
    
    def _load_config(self) -> None:
        """Carrega configuração do arquivo YAML"""
        try:
            with open(self.config_path, 'r', encoding='utf-8') as file:
                config_data = yaml.safe_load(file)
            
            self.config = SystemConfig(**config_data)
            logger.info(f"Configuração carregada de: {self.config_path}")
            
        except Exception as e:
            logger.error(f"Erro ao carregar configuração: {e}")
            # Usar configuração padrão em caso de erro
            self.config = SystemConfig()
            logger.warning("Usando configuração padrão")
    
    def get_config(self) -> SystemConfig:
        """Retorna a configuração atual"""
        if self.config is None:
            raise RuntimeError("Configuração não carregada")
        return self.config
    
    def reload_config(self) -> None:
        """Recarrega a configuração"""
        self._load_config()
        logger.info("Configuração recarregada")
    
    def save_config(self, config_path: Optional[str] = None) -> None:
        """Salva a configuração atual"""
        if self.config is None:
            raise RuntimeError("Nenhuma configuração para salvar")
        
        save_path = config_path or self.config_path
        
        try:
            # Converter para dict e salvar
            config_dict = self.config.dict()
            
            with open(save_path, 'w', encoding='utf-8') as file:
                yaml.dump(config_dict, file, default_flow_style=False, 
                         allow_unicode=True, indent=2)
            
            logger.info(f"Configuração salva em: {save_path}")
            
        except Exception as e:
            logger.error(f"Erro ao salvar configuração: {e}")
            raise
    
    def update_config(self, section: str, key: str, value: Any) -> None:
        """Atualiza um valor específico da configuração"""
        if self.config is None:
            raise RuntimeError("Configuração não carregada")
        
        try:
            section_obj = getattr(self.config, section)
            setattr(section_obj, key, value)
            logger.info(f"Configuração atualizada: {section}.{key} = {value}")
            
        except AttributeError:
            logger.error(f"Seção ou chave inválida: {section}.{key}")
            raise
    
    def validate_config(self) -> bool:
        """Valida a configuração atual"""
        if self.config is None:
            return False
        
        try:
            # Validação adicional personalizada
            network = self.config.network
            
            # Verificar se as portas não conflitam
            ports = [network.middleware_port, network.websocket_port, network.streaming_port]
            if len(set(ports)) != len(ports):
                logger.error("Portas de rede conflitantes detectadas")
                return False
            
            # Verificar se diretórios existem
            gestures_path = self.config.motion.gestures.library_path
            if not os.path.exists(gestures_path):
                logger.warning(f"Diretório de gestos não existe: {gestures_path}")
                os.makedirs(gestures_path, exist_ok=True)
            
            logger.info("Configuração validada com sucesso")
            return True
            
        except Exception as e:
            logger.error(f"Erro na validação da configuração: {e}")
            return False

# Instância global do gerenciador de configuração
config_manager = ConfigManager()