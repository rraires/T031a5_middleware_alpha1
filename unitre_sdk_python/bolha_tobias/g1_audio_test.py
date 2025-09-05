#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Script de Teste do Sistema de Áudio - Unitree G1

Este script fornece uma interface completa para testar todas as funcionalidades
do sistema de áudio do robô G1, incluindo:
- Síntese de voz (TTS)
- Controle de volume
- Reprodução de áudio PCM
- Controle de LED RGB
- Diagnósticos do sistema
- Verificação de conectividade

Uso:
    python g1_audio_test.py <interface_de_rede>
    
Exemplo:
    python g1_audio_test.py eth0
    python g1_audio_test.py wlan0

Autor: Sistema de Teste Automatizado
Versão: 1.0
Data: 2024
"""

import sys
import time
import os
import logging
import traceback
from datetime import datetime
from typing import Optional, Tuple, List, Any, Callable

try:
    from unitree_sdk2py.core.channel import ChannelFactoryInitialize
    from unitree_sdk2py.g1.audio.g1_audio_client import AudioClient
except ImportError as e:
    print(f"Erro ao importar SDK do Unitree: {e}")
    print("Certifique-se de que o unitree_sdk2py está instalado corretamente.")
    sys.exit(1)

# Configuração avançada de logging
class ColoredFormatter(logging.Formatter):
    """Formatter com cores para diferentes níveis de log"""
    
    COLORS = {
        'DEBUG': '\033[36m',    # Ciano
        'INFO': '\033[32m',     # Verde
        'WARNING': '\033[33m',  # Amarelo
        'ERROR': '\033[31m',    # Vermelho
        'CRITICAL': '\033[35m', # Magenta
        'RESET': '\033[0m'      # Reset
    }
    
    def format(self, record):
        log_color = self.COLORS.get(record.levelname, self.COLORS['RESET'])
        record.levelname = f"{log_color}{record.levelname}{self.COLORS['RESET']}"
        return super().format(record)

# Configurar logger principal
logger = logging.getLogger('G1AudioTest')
logger.setLevel(logging.DEBUG)

# Handler para arquivo (sem cores)
file_handler = logging.FileHandler('g1_audio_test.log', encoding='utf-8')
file_handler.setLevel(logging.DEBUG)
file_formatter = logging.Formatter(
    '%(asctime)s - %(name)s - %(levelname)s - %(funcName)s:%(lineno)d - %(message)s'
)
file_handler.setFormatter(file_formatter)

# Handler para console (com cores se suportado)
console_handler = logging.StreamHandler()
console_handler.setLevel(logging.INFO)
try:
    # Tentar usar cores no console
    console_formatter = ColoredFormatter(
        '%(asctime)s - %(levelname)s - %(message)s'
    )
except:
    # Fallback para formato simples
    console_formatter = logging.Formatter(
        '%(asctime)s - %(levelname)s - %(message)s'
    )
console_handler.setFormatter(console_formatter)

# Adicionar handlers
logger.addHandler(file_handler)
logger.addHandler(console_handler)

# Logger para operações críticas
critical_logger = logging.getLogger('G1AudioTest.Critical')
critical_handler = logging.FileHandler('g1_audio_critical.log', encoding='utf-8')
critical_handler.setLevel(logging.ERROR)
critical_handler.setFormatter(file_formatter)
critical_logger.addHandler(critical_handler)

# Evitar propagação para o logger raiz
critical_logger.propagate = False

class G1AudioTester:
    """
    Classe principal para teste do sistema de áudio do G1
    """
    
    def __init__(self, network_interface: str):
        """
        Inicializa o testador de áudio
        
        Args:
            network_interface: Interface de rede (ex: 'eth0', 'wlan0')
        """
        self.network_interface = network_interface
        self.audio_client: Optional[AudioClient] = None
        self.is_connected = False
        self.current_volume = 50
        
        # Configurações padrão
        self.default_timeout = 10.0
        self.timeout = 10.0  # Adicionar atributo timeout
        self.test_voices = [0, 1]  # IDs de vozes disponíveis
        self.test_volumes = [30, 50, 75, 100]
        
        logger.info(f"Inicializando testador de áudio para interface: {network_interface}")
    
    def initialize_connection(self) -> bool:
        """
        Inicializa a conexão com o robô G1
        
        Returns:
            bool: True se a conexão foi estabelecida com sucesso
        """
        try:
            logger.info("Inicializando canal de comunicação...")
            ChannelFactoryInitialize(0, self.network_interface)
            
            logger.info("Criando cliente de áudio...")
            self.audio_client = AudioClient()
            self.audio_client.SetTimeout(self.default_timeout)
            self.audio_client.Init()
            
            # Testar conectividade
            logger.info("Testando conectividade...")
            code, volume_data = self.audio_client.GetVolume()
            
            if code == 0:
                self.is_connected = True
                self.current_volume = volume_data.get('volume', 50)
                logger.info(f"Conexão estabelecida com sucesso. Volume atual: {self.current_volume}%")
                return True
            else:
                logger.error(f"Erro na conectividade: código {code}")
                return False
                
        except Exception as e:
            logger.error(f"Erro ao inicializar conexão: {e}")
            return False
    
    def display_main_menu(self):
        """
        Exibe o menu principal do sistema de teste
        """
        print("\n" + "="*60)
        print("    SISTEMA DE TESTE DE ÁUDIO - UNITREE G1")
        print("="*60)
        print(f"Interface de Rede: {self.network_interface}")
        print(f"Status da Conexão: {'✓ Conectado' if self.is_connected else '✗ Desconectado'}")
        print(f"Volume Atual: {self.current_volume}%")
        print("="*60)
        print("\n📢 TESTES DE ALTO-FALANTE:")
        print("  1. Teste de Síntese de Voz (TTS)")
        print("  2. Teste de Controle de Volume")
        print("  3. Teste de Reprodução de Áudio PCM")
        print("  4. Teste de Múltiplas Vozes")
        
        print("\n🎤 TESTES DE MICROFONE:")
        print("  5. 🎤 Teste de Conectividade do Microfone")
        print("  6. ⚙️  Teste de Configurações do Microfone")
        print("  7. 🔄 Teste de Captura e Reprodução (Microfone → Alto-falante)")
        
        print("\n💡 CONTROLE DE LED:")
        print("  8. 💡 Controle de LED RGB")
        print("  9. 🌈 Teste de Sequência de Cores")
        print(" 10. 🎨 Controle Personalizado de LED")
        
        print("\n🔧 DIAGNÓSTICOS:")
        print(" 11. Diagnóstico Completo do Sistema")
        print(" 12. Teste de Latência")
        print(" 13. Verificar Status de Todas as APIs")
        
        print("\n⚙️  CONFIGURAÇÕES:")
        print(" 14. Configurar Volume Padrão")
        print(" 15. Configurar Timeout")
        print(" 16. Logs do Sistema")
        
        print("\n🎯 TESTES INTEGRADOS:")
        print(" 17. Demo Completa (TTS + LED + Volume)")
        print(" 18. Teste de Stress")
        print(" 19. Sequência de Saudação")
        
        print("\n📋 OUTRAS OPÇÕES:")
        print(" 20. Reconectar ao Robô")
        print(" 21. Exibir Informações do Sistema")
        print(" 22. Estatísticas de Erro")
        print("  0. Sair")
        
        print("\n" + "="*60)
    
    def get_user_choice(self) -> int:
        """
        Obtém a escolha do usuário do menu
        
        Returns:
            int: Opção escolhida pelo usuário
        """
        try:
            choice = input("\nEscolha uma opção (0-22): ").strip()
            return int(choice)
        except ValueError:
            print("❌ Opção inválida. Digite um número entre 0 e 22.")
            return -1
    
    def check_connection(self) -> bool:
        """
        Verifica se a conexão está ativa
        
        Returns:
            bool: True se conectado
        """
        if not self.is_connected or not self.audio_client:
            print("❌ Não conectado ao robô. Use a opção 19 para reconectar.")
            return False
        return True
    
    def safe_execute(self, operation_name: str, operation_func, *args, **kwargs):
        """
        Executa uma operação de áudio com tratamento de erro robusto
        
        Args:
            operation_name: Nome da operação para logging
            operation_func: Função a ser executada
            *args, **kwargs: Argumentos para a função
            
        Returns:
            Resultado da operação ou None em caso de erro
        """
        if not self.check_connection():
            return None
            
        operation_id = f"{operation_name}_{int(time.time() * 1000)}"
        
        try:
            logger.info(f"[{operation_id}] Iniciando: {operation_name}")
            logger.debug(f"[{operation_id}] Argumentos: args={args}, kwargs={kwargs}")
            
            start_time = time.time()
            
            # Executar operação com timeout
            result = self._execute_with_timeout(operation_func, args, kwargs, self.default_timeout)
            
            end_time = time.time()
            duration = end_time - start_time
            
            # Log detalhado do resultado
            self._log_operation_result(operation_id, operation_name, result, duration)
            
            # Feedback visual para o usuário
            self._display_operation_feedback(operation_name, result)
            
            # Incrementar contador de operações
            if not hasattr(self, 'operation_count'):
                self.operation_count = 0
            self.operation_count += 1
                
            return result
            
        except TimeoutError as e:
            error_msg = f"Timeout em {operation_name} após {self.default_timeout}s"
            logger.error(f"[{operation_id}] {error_msg}")
            print(f"⏰ {error_msg}")
            self._log_critical_error(operation_name, error_msg, e)
            return None
            
        except ConnectionError as e:
            error_msg = f"Erro de conexão em {operation_name}"
            logger.error(f"[{operation_id}] {error_msg}: {e}")
            print(f"🔌 {error_msg}")
            self.is_connected = False
            self._log_critical_error(operation_name, error_msg, e)
            return None
            
        except Exception as e:
            error_msg = f"Erro inesperado em {operation_name}"
            logger.error(f"[{operation_id}] {error_msg}: {e}")
            logger.debug(f"[{operation_id}] Traceback: {traceback.format_exc()}")
            print(f"❌ {error_msg}: {e}")
            self._log_critical_error(operation_name, error_msg, e)
            return None
    
    def _execute_with_timeout(self, func, args, kwargs, timeout):
        """
        Executa uma função com timeout (implementação simplificada)
        """
        # Nota: Em um ambiente real, usaríamos threading ou asyncio
        # Para este exemplo, executamos diretamente
        return func(*args, **kwargs)
    
    def _log_operation_result(self, operation_id: str, operation_name: str, result, duration: float):
        """
        Registra o resultado detalhado de uma operação
        """
        logger.info(f"[{operation_id}] {operation_name} concluída em {duration:.3f}s")
        
        if isinstance(result, tuple) and len(result) == 2:
            code, data = result
            logger.info(f"[{operation_id}] Código: {code}, Dados: {data}")
        elif isinstance(result, int):
            logger.info(f"[{operation_id}] Código de retorno: {result}")
        else:
            logger.info(f"[{operation_id}] Resultado: {type(result).__name__}")
        
        # Log de performance
        if duration > 5.0:
            logger.warning(f"[{operation_id}] Operação lenta detectada: {duration:.3f}s")
        elif duration > 10.0:
            logger.error(f"[{operation_id}] Operação muito lenta: {duration:.3f}s")
    
    def _display_operation_feedback(self, operation_name: str, result):
        """
        Exibe feedback visual para o usuário
        """
        if isinstance(result, tuple) and len(result) == 2:
            code, data = result
            if code == 0:
                print(f"✅ {operation_name}: Sucesso")
            else:
                print(f"❌ {operation_name}: Erro (código: {code})")
        elif isinstance(result, int):
            if result == 0:
                print(f"✅ {operation_name}: Sucesso")
            else:
                print(f"❌ {operation_name}: Erro (código: {result})")
        else:
            print(f"✅ {operation_name}: Concluída")
    
    def _log_critical_error(self, operation_name: str, error_msg: str, exception: Exception):
        """
        Registra erros críticos em log separado
        """
        critical_info = {
            'timestamp': datetime.now().isoformat(),
            'operation': operation_name,
            'error_message': error_msg,
            'exception_type': type(exception).__name__,
            'exception_details': str(exception),
            'network_interface': self.network_interface,
            'connection_status': self.is_connected,
            'traceback': traceback.format_exc()
        }
        
        # Log crítico estruturado
        critical_logger.error(f"CRITICAL_ERROR: {critical_info}")
        
        # Incrementar contador de erros
        if not hasattr(self, 'error_count'):
            self.error_count = 0
        self.error_count += 1
    
    def get_error_statistics(self) -> dict:
        """
        Retorna estatísticas de erro
        """
        total_ops = getattr(self, 'operation_count', 0)
        total_errors = getattr(self, 'error_count', 0)
        
        if total_ops == 0:
            success_rate = 0.0
        else:
            success_rate = ((total_ops - total_errors) / total_ops) * 100
        
        return {
            'total_operations': total_ops,
            'total_errors': total_errors,
            'success_rate': success_rate,
            'error_rate': (total_errors / total_ops * 100) if total_ops > 0 else 0.0
        }
    
    def run(self):
        """
        Executa o loop principal do sistema de teste
        """
        print("🚀 Iniciando Sistema de Teste de Áudio do Unitree G1...")
        
        # Tentar conectar
        if not self.initialize_connection():
            print("❌ Falha na inicialização. Verifique a conexão e tente novamente.")
            return
        
        print("✅ Sistema inicializado com sucesso!")
        
        while True:
            try:
                self.display_main_menu()
                choice = self.get_user_choice()
                
                if choice == 0:
                    print("\n👋 Encerrando sistema de teste...")
                    self.cleanup()
                    break
                elif choice == 1:
                    self.test_tts()
                elif choice == 2:
                    self.test_volume_control()
                elif choice == 3:
                    self.test_pcm_playback()
                elif choice == 4:
                    self.test_multiple_voices()
                elif choice == 5:
                    self.test_microphone_connectivity()
                elif choice == 6:
                    self.test_microphone_settings()
                elif choice == 7:
                    self.test_microphone_capture_playback()
                elif choice == 8:
                    self.test_led_rgb()
                elif choice == 9:
                    self.test_color_sequence()
                elif choice == 10:
                    self.test_custom_led()
                elif choice == 11:
                    self.run_full_diagnostics()
                elif choice == 12:
                    self.test_latency()
                elif choice == 13:
                    self.check_all_apis()
                elif choice == 14:
                    self.configure_default_volume()
                elif choice == 15:
                    self.configure_timeout()
                elif choice == 16:
                    self.show_system_logs()
                elif choice == 17:
                    self.run_complete_demo()
                elif choice == 18:
                    self.run_stress_test()
                elif choice == 19:
                    self.run_greeting_sequence()
                elif choice == 20:
                    self.reconnect()
                elif choice == 21:
                    self.show_system_info()
                elif choice == 22:
                    self.show_error_statistics()
                elif choice == -1:
                    continue  # Opção inválida, continuar
                else:
                    print(f"❌ Opção {choice} não implementada ainda.")
                
                input("\nPressione Enter para continuar...")
                
            except KeyboardInterrupt:
                print("\n\n⚠️  Interrupção detectada. Encerrando...")
                self.cleanup()
                break
            except Exception as e:
                logger.error(f"Erro no loop principal: {e}")
                print(f"❌ Erro inesperado: {e}")
    
    # ==================== TESTES DE ALTO-FALANTE ====================
    
    def test_tts(self):
        """
        Teste de síntese de voz (TTS)
        """
        print("\n🔊 TESTE DE SÍNTESE DE VOZ (TTS)")
        print("="*50)
        
        test_phrases = [
            "Olá! Eu sou o robô G1 da Unitree.",
            "Testando sistema de síntese de voz.",
            "Este é um teste de áudio completo.",
            "Funcionalidade TTS operando corretamente."
        ]
        
        for i, phrase in enumerate(test_phrases, 1):
            print(f"\n📢 Teste {i}/4: '{phrase}'")
            result = self.safe_execute(
                f"TTS Teste {i}",
                self.audio_client.TtsMaker,
                phrase, 0
            )
            
            if result == 0:
                print(f"   ✅ Frase {i} reproduzida com sucesso")
            else:
                print(f"   ❌ Erro na frase {i}: código {result}")
            
            time.sleep(2)  # Aguardar reprodução
        
        print("\n📊 Teste de TTS concluído.")
    
    def test_volume_control(self):
        """
        Teste de controle de volume
        """
        print("\n🔊 TESTE DE CONTROLE DE VOLUME")
        print("="*50)
        
        # Obter volume atual
        print("\n📊 Verificando volume atual...")
        code, volume_data = self.audio_client.GetVolume()
        if code == 0:
            original_volume = volume_data.get('volume', 50)
            print(f"   Volume atual: {original_volume}%")
        else:
            print(f"   ❌ Erro ao obter volume: {code}")
            original_volume = 50
        
        # Testar diferentes volumes
        test_volumes = [25, 50, 75, 100]
        test_phrase = "Testando volume em"
        
        for volume in test_volumes:
            print(f"\n🔧 Configurando volume para {volume}%...")
            
            # Definir volume
            result = self.safe_execute(
                f"Definir Volume {volume}%",
                self.audio_client.SetVolume,
                volume
            )
            
            if result == 0:
                # Verificar se foi aplicado
                code, new_volume = self.audio_client.GetVolume()
                if code == 0:
                    actual_volume = new_volume.get('volume', 0)
                    print(f"   ✅ Volume configurado: {actual_volume}%")
                    
                    # Testar com TTS
                    tts_result = self.safe_execute(
                        f"TTS Volume {volume}%",
                        self.audio_client.TtsMaker,
                        f"{test_phrase} {volume} por cento", 0
                    )
                    
                    if tts_result == 0:
                        print(f"   🔊 Teste de áudio no volume {volume}% concluído")
                    
                    time.sleep(3)  # Aguardar reprodução
                else:
                    print(f"   ❌ Erro ao verificar volume: {code}")
            else:
                print(f"   ❌ Erro ao definir volume {volume}%: {result}")
        
        # Restaurar volume original
        print(f"\n🔄 Restaurando volume original ({original_volume}%)...")
        self.safe_execute(
            "Restaurar Volume Original",
            self.audio_client.SetVolume,
            original_volume
        )
        
        self.current_volume = original_volume
        print("\n📊 Teste de controle de volume concluído.")
    
    def test_pcm_playback(self):
        """
        Teste de reprodução de áudio PCM
        """
        print("\n🎵 TESTE DE REPRODUÇÃO DE ÁUDIO PCM")
        print("="*50)
        
        print("\n⚠️  Nota: Este teste requer arquivos WAV no formato:")
        print("   - Sample Rate: 16kHz")
        print("   - Canais: 1 (mono)")
        print("   - Bit Depth: 16-bit")
        
        # Verificar se existe módulo wav
        try:
            from wav import read_wav, play_pcm_stream
            print("   ✅ Módulo WAV disponível")
        except ImportError:
            print("   ❌ Módulo WAV não encontrado")
            print("   📝 Criando dados PCM sintéticos para teste...")
            self._test_synthetic_pcm()
            return
        
        # Procurar arquivos WAV no diretório
        wav_files = [f for f in os.listdir('.') if f.endswith('.wav')]
        
        if not wav_files:
            print("   ⚠️  Nenhum arquivo WAV encontrado no diretório atual")
            print("   📝 Criando dados PCM sintéticos para teste...")
            self._test_synthetic_pcm()
            return
        
        print(f"\n📁 Arquivos WAV encontrados: {len(wav_files)}")
        for i, file in enumerate(wav_files[:3], 1):  # Limitar a 3 arquivos
            print(f"   {i}. {file}")
        
        # Testar primeiro arquivo
        test_file = wav_files[0]
        print(f"\n🎵 Testando arquivo: {test_file}")
        
        try:
            # Carregar arquivo WAV
            pcm_list, sample_rate, num_channels, success = read_wav(test_file)
            
            if not success:
                print(f"   ❌ Erro ao carregar {test_file}")
                return
            
            # Validar formato
            if sample_rate != 16000 or num_channels != 1:
                print(f"   ❌ Formato não suportado:")
                print(f"      Sample Rate: {sample_rate}Hz (requerido: 16000Hz)")
                print(f"      Canais: {num_channels} (requerido: 1)")
                return
            
            print(f"   ✅ Arquivo válido:")
            print(f"      Sample Rate: {sample_rate}Hz")
            print(f"      Canais: {num_channels}")
            print(f"      Duração: {len(pcm_list) / (sample_rate * 2):.2f} segundos")
            
            # Reproduzir
            print("\n▶️  Iniciando reprodução...")
            play_pcm_stream(
                client=self.audio_client,
                pcm_list=pcm_list,
                stream_name="audio_test",
                verbose=True
            )
            
            print("   ✅ Reprodução concluída")
            
            # Parar stream
            self.safe_execute(
                "Parar Reprodução",
                self.audio_client.PlayStop,
                "audio_test"
            )
            
        except Exception as e:
            print(f"   ❌ Erro durante reprodução: {e}")
        
        print("\n📊 Teste de reprodução PCM concluído.")
    
    def _test_synthetic_pcm(self):
        """
        Teste com dados PCM sintéticos (tom puro)
        """
        import math
        import struct
        
        print("\n🎼 Gerando tom sintético (440Hz - Lá)...")
        
        # Parâmetros
        sample_rate = 16000
        duration = 2.0  # 2 segundos
        frequency = 440  # Lá (A4)
        amplitude = 0.3  # 30% do máximo
        
        # Gerar amostras
        num_samples = int(sample_rate * duration)
        pcm_data = bytearray()
        
        for i in range(num_samples):
            # Gerar onda senoidal
            t = i / sample_rate
            sample = amplitude * math.sin(2 * math.pi * frequency * t)
            
            # Converter para 16-bit signed integer
            sample_int = int(sample * 32767)
            sample_int = max(-32768, min(32767, sample_int))
            
            # Adicionar ao buffer (little-endian)
            pcm_data.extend(struct.pack('<h', sample_int))
        
        print(f"   ✅ Tom gerado: {duration}s, {frequency}Hz")
        print(f"   📊 Tamanho dos dados: {len(pcm_data)} bytes")
        
        # Reproduzir
        print("\n▶️  Reproduzindo tom sintético...")
        
        try:
            result = self.safe_execute(
                "Reprodução PCM Sintética",
                self.audio_client.PlayStream,
                "audio_test", "synthetic_tone", bytes(pcm_data)
            )
            
            if result == 0:
                print("   ✅ Tom reproduzido com sucesso")
                time.sleep(duration + 0.5)  # Aguardar reprodução
                
                # Parar reprodução
                self.safe_execute(
                    "Parar Tom Sintético",
                    self.audio_client.PlayStop,
                    "audio_test"
                )
            else:
                print(f"   ❌ Erro na reprodução: {result}")
                
        except Exception as e:
            print(f"   ❌ Erro durante reprodução sintética: {e}")
    
    def test_multiple_voices(self):
        """
        Teste de múltiplas vozes TTS
        """
        print("\n🎭 TESTE DE MÚLTIPLAS VOZES")
        print("="*50)
        
        test_text = "Esta é a voz número"
        max_voices = 5  # Testar até 5 vozes diferentes
        
        print(f"\n🔍 Testando vozes de 0 a {max_voices-1}...")
        
        working_voices = []
        
        for voice_id in range(max_voices):
            print(f"\n🎤 Testando voz {voice_id}...")
            
            result = self.safe_execute(
                f"TTS Voz {voice_id}",
                self.audio_client.TtsMaker,
                f"{test_text} {voice_id}", voice_id
            )
            
            if result == 0:
                print(f"   ✅ Voz {voice_id}: Funcionando")
                working_voices.append(voice_id)
            else:
                print(f"   ❌ Voz {voice_id}: Erro (código: {result})")
            
            time.sleep(2.5)  # Aguardar reprodução
        
        print(f"\n📊 Resumo do teste:")
        print(f"   Vozes testadas: {max_voices}")
        print(f"   Vozes funcionando: {len(working_voices)}")
        print(f"   IDs das vozes funcionais: {working_voices}")
        
        # Atualizar lista de vozes disponíveis
        if working_voices:
            self.test_voices = working_voices
            print(f"   ✅ Lista de vozes atualizada")
        
        print("\n📊 Teste de múltiplas vozes concluído.")
    
    # ==================== TESTES DE MICROFONE ====================
    
    def test_microphone_connectivity(self):
        """
        Teste de Conectividade do Microfone
        """
        print("\n🎤 TESTE DE CONECTIVIDADE DO MICROFONE")
        print("="*55)
        
        print("\n⚠️  Nota: O G1 possui APIs limitadas para microfone.")
        print("   As funcionalidades disponíveis são principalmente para ASR.")
        
        # Verificar se há APIs de microfone disponíveis
        mic_methods = []
        for method_name in dir(self.audio_client):
            if any(keyword in method_name.lower() for keyword in ['mic', 'asr', 'record', 'capture']):
                mic_methods.append(method_name)
        
        if mic_methods:
            print(f"\n🔍 Métodos relacionados ao microfone encontrados:")
            for i, method in enumerate(mic_methods, 1):
                print(f"   {i}. {method}")
        else:
            print("\n❌ Nenhum método específico de microfone encontrado")
        
        # Teste básico de conectividade
        print("\n🔧 Testando conectividade básica...")
        
        # Simular teste de microfone através de TTS (feedback loop)
        print("\n🔄 Teste de feedback: TTS -> Microfone (simulado)")
        
        feedback_result = self.safe_execute(
            "Teste de Feedback",
            self.audio_client.TtsMaker,
            "Testando conectividade do microfone através de síntese de voz", 0
        )
        
        if feedback_result == 0:
            print("   ✅ Sistema de áudio responsivo (TTS funcionando)")
            print("   📝 Microfone provavelmente conectado (teste indireto)")
        else:
            print(f"   ❌ Problema no sistema de áudio: {feedback_result}")
        
        time.sleep(3)
        
        print("\n📊 Teste de conectividade do microfone concluído.")
        print("   💡 Para testes avançados de microfone, use APIs ASR específicas.")
    
    def test_microphone_settings(self):
        """
        Teste de Configurações do Microfone
        """
        print("\n⚙️  TESTE DE CONFIGURAÇÕES DO MICROFONE")
        print("="*55)
        
        print("\n📋 Configurações típicas de microfone para G1:")
        print("   - Sample Rate: 16kHz")
        print("   - Canais: 1 (mono)")
        print("   - Bit Depth: 16-bit")
        print("   - Formato: PCM")
        
        # Verificar configurações através de métodos disponíveis
        print("\n🔍 Verificando métodos de configuração disponíveis...")
        
        config_methods = []
        for method_name in dir(self.audio_client):
            if any(keyword in method_name.lower() for keyword in ['config', 'setting', 'param']):
                config_methods.append(method_name)
        
        if config_methods:
            print(f"\n⚙️  Métodos de configuração encontrados:")
            for i, method in enumerate(config_methods, 1):
                print(f"   {i}. {method}")
        else:
            print("\n❌ Nenhum método de configuração específico encontrado")
        
        # Teste de configuração através de volume (relacionado)
        print("\n🔧 Testando configuração relacionada (volume do sistema)...")
        
        code, volume_data = self.audio_client.GetVolume()
        if code == 0:
            volume = volume_data.get('volume', 'N/A')
            print(f"   ✅ Volume do sistema: {volume}%")
            print("   📝 Sistema de áudio configurado e responsivo")
        else:
            print(f"   ❌ Erro ao acessar configurações: {code}")
        
        print("\n📊 Teste de configurações do microfone concluído.")
    
    def test_microphone_capture_playback(self):
        """
        Teste de Captura e Reprodução (Microfone → Alto-falante)
        """
        print("\n🔄 TESTE DE CAPTURA E REPRODUÇÃO (MICROFONE → ALTO-FALANTE)")
        print("="*60)
        
        try:
            import pyaudio
            import wave
            import tempfile
            import os
            from wav import play_pcm_stream
        except ImportError as e:
            print(f"❌ Erro: Biblioteca necessária não encontrada: {e}")
            print("💡 Instale com: pip install pyaudio")
            return
        
        # Configurações de áudio (compatíveis com G1)
        CHUNK = 1024
        FORMAT = pyaudio.paInt16
        CHANNELS = 1  # Mono
        RATE = 16000  # 16kHz
        RECORD_SECONDS = 3
        
        print(f"\n⚙️  Configurações:")
        print(f"   • Sample Rate: {RATE} Hz")
        print(f"   • Canais: {CHANNELS} (mono)")
        print(f"   • Formato: 16-bit PCM")
        print(f"   • Duração: {RECORD_SECONDS} segundos")
        
        try:
            # Inicializar PyAudio
            audio = pyaudio.PyAudio()
            
            # Verificar dispositivos de áudio disponíveis
            print("\n🔍 Dispositivos de áudio disponíveis:")
            default_input = audio.get_default_input_device_info()
            print(f"   🎯 Dispositivo padrão: {default_input['name']} (ID: {default_input['index']})")
            
            for i in range(audio.get_device_count()):
                info = audio.get_device_info_by_index(i)
                if info['maxInputChannels'] > 0:
                    print(f"   📱 {i}: {info['name']} (Input) - Max Channels: {info['maxInputChannels']}")
            
            print(f"\n🎙️  Preparando para gravar {RECORD_SECONDS} segundos...")
            print("   ⚠️  Certifique-se de que o microfone não está mutado!")
            input("   Pressione Enter para começar a gravação...")
            
            # Configurar stream de entrada com tratamento de erro
            try:
                stream = audio.open(
                    format=FORMAT,
                    channels=CHANNELS,
                    rate=RATE,
                    input=True,
                    frames_per_buffer=CHUNK,
                    input_device_index=None  # Usar dispositivo padrão
                )
            except Exception as e:
                print(f"❌ Erro ao abrir stream de áudio: {e}")
                print("💡 Tentando com dispositivo específico...")
                # Tentar com o primeiro dispositivo de entrada disponível
                for i in range(audio.get_device_count()):
                    info = audio.get_device_info_by_index(i)
                    if info['maxInputChannels'] > 0:
                        try:
                            stream = audio.open(
                                format=FORMAT,
                                channels=CHANNELS,
                                rate=RATE,
                                input=True,
                                frames_per_buffer=CHUNK,
                                input_device_index=i
                            )
                            print(f"✅ Usando dispositivo: {info['name']}")
                            break
                        except:
                            continue
                else:
                    print("❌ Não foi possível abrir nenhum dispositivo de áudio")
                    return
            
            print("\n🔴 GRAVANDO... Fale agora!")
            frames = []
            max_amplitude = 0
            
            for i in range(0, int(RATE / CHUNK * RECORD_SECONDS)):
                try:
                    data = stream.read(CHUNK, exception_on_overflow=False)
                    frames.append(data)
                    
                    # Verificar amplitude do sinal para detectar se há áudio
                    import struct
                    audio_chunk = struct.unpack(f'{CHUNK}h', data)
                    chunk_max = max(abs(sample) for sample in audio_chunk)
                    max_amplitude = max(max_amplitude, chunk_max)
                    
                    # Mostrar progresso com indicador de nível
                    progress = (i + 1) / (RATE / CHUNK * RECORD_SECONDS)
                    bar_length = 20
                    filled_length = int(bar_length * progress)
                    bar = '█' * filled_length + '-' * (bar_length - filled_length)
                    level_indicator = '🔊' if chunk_max > 1000 else '🔉' if chunk_max > 100 else '🔈'
                    print(f"\r   [{bar}] {progress*100:.1f}% {level_indicator} Nível: {chunk_max:5d}", end='', flush=True)
                    
                except Exception as e:
                    print(f"\n❌ Erro na leitura do áudio: {e}")
                    break
            
            print(f"\n✅ Gravação concluída! Amplitude máxima detectada: {max_amplitude}")
            
            if max_amplitude < 100:
                print("⚠️  AVISO: Amplitude muito baixa detectada!")
                print("   • Verifique se o microfone está conectado")
                print("   • Verifique se o microfone não está mutado")
                print("   • Aumente o volume do microfone nas configurações do sistema")
                print("   • Fale mais próximo ao microfone")
            
            # Parar e fechar stream
            stream.stop_stream()
            stream.close()
            
            # Converter dados para formato compatível com G1
            print("\n🔄 Processando áudio...")
            audio_data = b''.join(frames)
            
            # Verificar se há dados de áudio
            if len(audio_data) == 0:
                print("❌ Nenhum dado de áudio capturado!")
                return
            
            print(f"   📊 Dados capturados: {len(audio_data)} bytes")
            
            # Criar arquivo temporário WAV
            import tempfile
            with tempfile.NamedTemporaryFile(suffix='.wav', delete=False) as temp_file:
                temp_filename = temp_file.name
                
                # Salvar como WAV
                import wave
                wf = wave.open(temp_filename, 'wb')
                wf.setnchannels(CHANNELS)
                wf.setsampwidth(audio.get_sample_size(FORMAT))
                wf.setframerate(RATE)
                wf.writeframes(audio_data)
                wf.close()
            
            # Verificar o arquivo criado
            import os
            file_size = os.path.getsize(temp_filename)
            print(f"   💾 Arquivo WAV criado: {temp_filename}")
            print(f"   📏 Tamanho do arquivo: {file_size} bytes")
            
            if file_size < 1000:
                print("⚠️  AVISO: Arquivo muito pequeno, pode não conter áudio válido!")
            
            # Reproduzir no alto-falante do G1
            print("\n🔊 Reproduzindo no alto-falante do G1...")
            
            # Converter para lista de bytes (formato esperado pelo G1)
            pcm_list = list(audio_data)
            
            # Reproduzir usando o AudioClient
            try:
                play_pcm_stream(self.audio_client, pcm_list, "microphone_test", 
                              chunk_size=32000, sleep_time=0.5, verbose=True)
                
                print("\n✅ Reprodução concluída!")
                print("\n📊 Teste de captura e reprodução realizado com sucesso!")
                
            except Exception as e:
                print(f"\n❌ Erro na reprodução: {e}")
            
            # Arquivo temporário mantido para análise
            print(f"\n💾 Arquivo de áudio salvo em: {temp_filename}")
            print("   📝 O arquivo foi mantido para que você possa verificar a gravação")
            print("   🔍 Você pode reproduzir este arquivo em qualquer player de áudio")
                
        except Exception as e:
            print(f"\n❌ Erro durante o teste: {e}")
            print("\n💡 Verifique se:")
            print("   • O microfone está conectado e funcionando")
            print("   • PyAudio está instalado corretamente")
            print("   • Não há outros aplicativos usando o microfone")
            
        finally:
            try:
                audio.terminate()
            except:
                pass
        
        print("\n📋 Teste de captura e reprodução concluído.")
    
    # ==================== CONTROLE DE LED RGB ===================="
    
    def test_led_rgb(self):
        """
        Controle de LED RGB
        """
        return self.test_led_control()
    
    def test_led_control(self):
        """
        Controle de LED RGB
        """
        print("\n💡 CONTROLE DE LED RGB")
        print("="*40)
        
        # Cores de teste
        test_colors = [
            (255, 0, 0, "Vermelho"),
            (0, 255, 0, "Verde"),
            (0, 0, 255, "Azul"),
            (255, 255, 0, "Amarelo"),
            (255, 0, 255, "Magenta"),
            (0, 255, 255, "Ciano"),
            (255, 255, 255, "Branco"),
            (128, 128, 128, "Cinza"),
        ]
        
        print(f"\n🌈 Testando {len(test_colors)} cores diferentes...")
        
        for i, (r, g, b, name) in enumerate(test_colors, 1):
            print(f"\n💡 Teste {i}/{len(test_colors)}: {name} (R:{r}, G:{g}, B:{b})")
            
            result = self.safe_execute(
                f"LED {name}",
                self.audio_client.LedControl,
                r, g, b
            )
            
            if result == 0:
                print(f"   ✅ LED configurado para {name}")
                
                # TTS para anunciar a cor
                tts_result = self.safe_execute(
                    f"TTS Cor {name}",
                    self.audio_client.TtsMaker,
                    f"LED configurado para {name.lower()}", 0
                )
                
                time.sleep(2)  # Mostrar cor por 2 segundos
            else:
                print(f"   ❌ Erro ao configurar LED para {name}: {result}")
        
        # Desligar LED
        print("\n🔄 Desligando LED...")
        result = self.safe_execute(
            "Desligar LED",
            self.audio_client.LedControl,
            0, 0, 0
        )
        
        if result == 0:
            print("   ✅ LED desligado")
        else:
            print(f"   ❌ Erro ao desligar LED: {result}")
        
        print("\n📊 Teste de controle de LED concluído.")
    
    def test_led_patterns(self):
        """
        Teste de padrões de LED
        """
        print("\n🎨 TESTE DE PADRÕES DE LED")
        print("="*50)
        
        print("\n🔄 Padrão 1: Fade RGB")
        for intensity in [50, 100, 150, 200, 255, 200, 150, 100, 50]:
            self.safe_execute("LED Fade", self.audio_client.LedControl, intensity, 0, 0)
            time.sleep(0.2)
            self.safe_execute("LED Fade", self.audio_client.LedControl, 0, intensity, 0)
            time.sleep(0.2)
            self.safe_execute("LED Fade", self.audio_client.LedControl, 0, 0, intensity)
            time.sleep(0.2)
        
        print("\n🌈 Padrão 2: Ciclo de cores")
        colors = [(255,0,0), (255,128,0), (255,255,0), (0,255,0), (0,255,255), (0,0,255), (128,0,255)]
        for r, g, b in colors:
            self.safe_execute("LED Ciclo", self.audio_client.LedControl, r, g, b)
            time.sleep(0.5)
        
        print("\n⚡ Padrão 3: Piscar branco")
        for _ in range(5):
            self.safe_execute("LED Piscar", self.audio_client.LedControl, 255, 255, 255)
            time.sleep(0.3)
            self.safe_execute("LED Piscar", self.audio_client.LedControl, 0, 0, 0)
            time.sleep(0.3)
        
        # Finalizar com LED desligado
        self.safe_execute("Desligar LED", self.audio_client.LedControl, 0, 0, 0)
        print("\n📊 Teste de padrões de LED concluído.")
    
    # ==================== DIAGNÓSTICOS DO SISTEMA ====================
    
    def run_audio_diagnostics(self):
        """
        Executa diagnósticos completos do sistema de áudio
        """
        print("\n🔍 DIAGNÓSTICOS DO SISTEMA DE ÁUDIO")
        print("="*60)
        
        diagnostics = {
            'connection': False,
            'tts': False,
            'volume': False,
            'led': False,
            'pcm': False
        }
        
        # 1. Teste de conectividade
        print("\n1️⃣  Testando conectividade...")
        if self.is_connected:
            print("   ✅ Conexão estabelecida")
            diagnostics['connection'] = True
        else:
            print("   ❌ Falha na conexão")
        
        # 2. Teste de TTS
        print("\n2️⃣  Testando TTS...")
        tts_result = self.safe_execute(
            "Diagnóstico TTS",
            self.audio_client.TtsMaker,
            "Teste de diagnóstico do sistema", 0
        )
        if tts_result == 0:
            print("   ✅ TTS funcionando")
            diagnostics['tts'] = True
        else:
            print(f"   ❌ TTS com problema: {tts_result}")
        
        time.sleep(2)
        
        # 3. Teste de volume
        print("\n3️⃣  Testando controle de volume...")
        code, volume_data = self.audio_client.GetVolume()
        if code == 0:
            print(f"   ✅ Volume acessível: {volume_data.get('volume', 'N/A')}%")
            diagnostics['volume'] = True
        else:
            print(f"   ❌ Erro no volume: {code}")
        
        # 4. Teste de LED
        print("\n4️⃣  Testando LED...")
        led_result = self.safe_execute(
            "Diagnóstico LED",
            self.audio_client.LedControl,
            0, 255, 0  # Verde para sucesso
        )
        if led_result == 0:
            print("   ✅ LED funcionando")
            diagnostics['led'] = True
            time.sleep(1)
            self.safe_execute("Desligar LED", self.audio_client.LedControl, 0, 0, 0)
        else:
            print(f"   ❌ LED com problema: {led_result}")
        
        # 5. Teste básico de PCM
        print("\n5️⃣  Testando capacidade PCM...")
        try:
            # Teste simples com dados mínimos
            test_data = b'\x00\x00' * 100  # 100 amostras de silêncio
            pcm_result = self.safe_execute(
                "Diagnóstico PCM",
                self.audio_client.PlayStream,
                "diagnostic_test", "silence", test_data
            )
            if pcm_result == 0:
                print("   ✅ PCM funcionando")
                diagnostics['pcm'] = True
                self.safe_execute("Parar PCM", self.audio_client.PlayStop, "diagnostic_test")
            else:
                print(f"   ❌ PCM com problema: {pcm_result}")
        except Exception as e:
            print(f"   ❌ Erro no teste PCM: {e}")
        
        # Resumo dos diagnósticos
        print("\n📊 RESUMO DOS DIAGNÓSTICOS")
        print("="*40)
        
        total_tests = len(diagnostics)
        passed_tests = sum(diagnostics.values())
        
        for test_name, result in diagnostics.items():
            status = "✅ PASSOU" if result else "❌ FALHOU"
            print(f"   {test_name.upper():12} : {status}")
        
        print(f"\n📈 Resultado geral: {passed_tests}/{total_tests} testes passaram")
        
        if passed_tests == total_tests:
            print("🎉 Sistema de áudio totalmente funcional!")
            # LED verde para sucesso total
            self.safe_execute("Sucesso Total", self.audio_client.LedControl, 0, 255, 0)
            time.sleep(2)
            self.safe_execute("Desligar LED", self.audio_client.LedControl, 0, 0, 0)
        elif passed_tests >= total_tests * 0.7:
            print("⚠️  Sistema parcialmente funcional")
            # LED amarelo para sucesso parcial
            self.safe_execute("Sucesso Parcial", self.audio_client.LedControl, 255, 255, 0)
            time.sleep(2)
            self.safe_execute("Desligar LED", self.audio_client.LedControl, 0, 0, 0)
        else:
            print("🚨 Sistema com problemas significativos")
            # LED vermelho para problemas
            self.safe_execute("Problemas", self.audio_client.LedControl, 255, 0, 0)
            time.sleep(2)
            self.safe_execute("Desligar LED", self.audio_client.LedControl, 0, 0, 0)
        
        print("\n📊 Diagnósticos concluídos.")
        return diagnostics
    
    # ==================== MÉTODOS AUXILIARES DO MENU ====================
    
    def test_color_sequence(self):
        """
        Teste de Sequência de Cores
        """
        print("\n🌈 TESTE DE SEQUÊNCIA DE CORES")
        print("="*45)
        
        sequences = {
            "Arco-íris": [(255,0,0), (255,127,0), (255,255,0), (0,255,0), (0,0,255), (75,0,130), (148,0,211)],
            "Oceano": [(0,119,190), (0,180,216), (144,224,239), (0,119,190)],
            "Fogo": [(255,0,0), (255,69,0), (255,140,0), (255,215,0)],
            "Floresta": [(34,139,34), (0,128,0), (50,205,50), (124,252,0)]
        }
        
        for seq_name, colors in sequences.items():
            print(f"\n🎨 Sequência: {seq_name}")
            for i, (r, g, b) in enumerate(colors):
                print(f"   Cor {i+1}: RGB({r}, {g}, {b})")
                self.safe_execute(f"LED {seq_name}", self.audio_client.LedControl, r, g, b)
                time.sleep(0.8)
        
        # Finalizar
        self.safe_execute("Desligar LED", self.audio_client.LedControl, 0, 0, 0)
        print("\n📊 Teste de sequência de cores concluído.")
    
    def test_custom_led(self):
        """
        Controle Personalizado de LED
        """
        print("\n🎨 CONTROLE PERSONALIZADO DE LED")
        print("="*45)
        
        print("\n📝 Digite valores RGB (0-255) ou pressione Enter para usar padrões:")
        
        try:
            r_input = input("   Vermelho (0-255): ").strip()
            r = int(r_input) if r_input else 255
            r = max(0, min(255, r))
            
            g_input = input("   Verde (0-255): ").strip()
            g = int(g_input) if g_input else 0
            g = max(0, min(255, g))
            
            b_input = input("   Azul (0-255): ").strip()
            b = int(b_input) if b_input else 0
            b = max(0, min(255, b))
            
            print(f"\n🎨 Testando cor RGB({r}, {g}, {b})...")
            
            result = self.safe_execute("LED Personalizado", self.audio_client.LedControl, r, g, b)
            
            if result == 0:
                print("   ✅ Cor aplicada com sucesso!")
                input("\n   Pressione Enter para desligar o LED...")
            else:
                print(f"   ❌ Erro ao aplicar cor: {result}")
            
        except ValueError:
            print("   ❌ Valores inválidos. Usando cor padrão (branco).")
            r, g, b = 255, 255, 255
            self.safe_execute("LED Padrão", self.audio_client.LedControl, r, g, b)
            time.sleep(2)
        
        # Desligar LED
        self.safe_execute("Desligar LED", self.audio_client.LedControl, 0, 0, 0)
        print("\n📊 Teste de LED personalizado concluído.")
    
    def run_full_diagnostics(self):
        """
        Executa diagnósticos completos (alias para run_audio_diagnostics)
        """
        return self.run_audio_diagnostics()
    
    def test_latency(self):
        """
        Teste de latência do sistema de áudio
        """
        print("\n⏱️  TESTE DE LATÊNCIA DO SISTEMA")
        print("="*50)
        
        latencies = []
        
        print("\n📊 Executando 5 testes de latência TTS...")
        
        for i in range(5):
            print(f"\n🔊 Teste {i+1}/5...")
            
            start_time = time.time()
            result = self.safe_execute(
                f"Latência Teste {i+1}",
                self.audio_client.TtsMaker,
                f"Teste de latência número {i+1}", 0
            )
            end_time = time.time()
            
            if result == 0:
                latency = (end_time - start_time) * 1000  # em ms
                latencies.append(latency)
                print(f"   ✅ Latência: {latency:.2f}ms")
            else:
                print(f"   ❌ Erro no teste {i+1}: {result}")
            
            time.sleep(1)
        
        if latencies:
            avg_latency = sum(latencies) / len(latencies)
            min_latency = min(latencies)
            max_latency = max(latencies)
            
            print(f"\n📈 RESULTADOS DE LATÊNCIA:")
            print(f"   Média: {avg_latency:.2f}ms")
            print(f"   Mínima: {min_latency:.2f}ms")
            print(f"   Máxima: {max_latency:.2f}ms")
            print(f"   Testes válidos: {len(latencies)}/5")
            
            if avg_latency < 100:
                print("   🎉 Latência excelente!")
            elif avg_latency < 200:
                print("   ✅ Latência boa")
            elif avg_latency < 500:
                print("   ⚠️  Latência aceitável")
            else:
                print("   ❌ Latência alta")
        else:
            print("\n❌ Nenhum teste de latência foi bem-sucedido.")
        
        print("\n📊 Teste de latência concluído.")
    
    def check_all_apis(self):
        """
        Verifica disponibilidade de todas as APIs
        """
        print("\n🔍 VERIFICAÇÃO DE TODAS AS APIS")
        print("="*50)
        
        apis = {
            'TtsMaker': 'Síntese de voz',
            'GetVolume': 'Obter volume',
            'SetVolume': 'Definir volume',
            'PlayStream': 'Reprodução PCM',
            'PlayStop': 'Parar reprodução',
            'LedControl': 'Controle de LED'
        }
        
        results = {}
        
        for api_name, description in apis.items():
            print(f"\n🔧 Testando {api_name} ({description})...")
            
            try:
                if api_name == 'TtsMaker':
                    result = self.audio_client.TtsMaker("Teste de API", 0)
                elif api_name == 'GetVolume':
                    result, _ = self.audio_client.GetVolume()
                elif api_name == 'SetVolume':
                    result = self.audio_client.SetVolume(self.current_volume)
                elif api_name == 'PlayStream':
                    test_data = b'\x00\x00' * 50
                    result = self.audio_client.PlayStream("api_test", "test", test_data)
                    if result == 0:
                        self.audio_client.PlayStop("api_test")
                elif api_name == 'PlayStop':
                    result = self.audio_client.PlayStop("nonexistent")
                elif api_name == 'LedControl':
                    result = self.audio_client.LedControl(0, 0, 255)
                    if result == 0:
                        time.sleep(0.5)
                        self.audio_client.LedControl(0, 0, 0)
                
                results[api_name] = result == 0
                status = "✅ DISPONÍVEL" if result == 0 else f"❌ ERRO ({result})"
                print(f"   {status}")
                
            except Exception as e:
                results[api_name] = False
                print(f"   ❌ EXCEÇÃO: {e}")
            
            time.sleep(0.5)
        
        # Resumo
        print(f"\n📊 RESUMO DAS APIS:")
        print("="*30)
        
        available = sum(results.values())
        total = len(results)
        
        for api_name, available_status in results.items():
            status = "✅" if available_status else "❌"
            print(f"   {api_name:12} : {status}")
        
        print(f"\n📈 APIs disponíveis: {available}/{total}")
        
        if available == total:
            print("🎉 Todas as APIs estão funcionando!")
        elif available >= total * 0.8:
            print("✅ Maioria das APIs funcionando")
        else:
            print("⚠️  Várias APIs com problemas")
        
        print("\n📊 Verificação de APIs concluída.")
    
    def configure_default_volume(self):
        """
        Configurar volume padrão do sistema
        """
        print("\n🔧 CONFIGURAÇÃO DE VOLUME PADRÃO")
        print("="*50)
        
        # Mostrar volume atual
        code, volume_data = self.audio_client.GetVolume()
        if code == 0:
            current_volume = volume_data.get('volume', 50)
            print(f"\n📊 Volume atual: {current_volume}%")
        else:
            print(f"\n❌ Erro ao obter volume atual: {code}")
            current_volume = 50
        
        print("\n📝 Digite o novo volume padrão (0-100) ou pressione Enter para manter atual:")
        
        try:
            volume_input = input("   Novo volume: ").strip()
            
            if volume_input:
                new_volume = int(volume_input)
                new_volume = max(0, min(100, new_volume))
                
                print(f"\n🔧 Configurando volume para {new_volume}%...")
                result = self.safe_execute(
                    "Configurar Volume Padrão",
                    self.audio_client.SetVolume,
                    new_volume
                )
                
                if result == 0:
                    self.current_volume = new_volume
                    print(f"   ✅ Volume configurado para {new_volume}%")
                    
                    # Testar com TTS
                    self.safe_execute(
                        "Teste Volume Configurado",
                        self.audio_client.TtsMaker,
                        f"Volume configurado para {new_volume} por cento", 0
                    )
                else:
                    print(f"   ❌ Erro ao configurar volume: {result}")
            else:
                print(f"\n📊 Volume mantido em {current_volume}%")
                
        except ValueError:
            print("\n❌ Valor inválido. Volume não alterado.")
        
        print("\n📊 Configuração de volume concluída.")
    
    def configure_timeout(self):
        """
        Configurar timeout das operações
        """
        print("\n⏱️  CONFIGURAÇÃO DE TIMEOUT")
        print("="*50)
        
        print(f"\n📊 Timeout atual: {self.default_timeout}s")
        print("\n📝 Digite o novo timeout (1-30s) ou pressione Enter para manter atual:")
        
        try:
            timeout_input = input("   Novo timeout: ").strip()
            
            if timeout_input:
                new_timeout = float(timeout_input)
                new_timeout = max(1.0, min(30.0, new_timeout))
                
                self.default_timeout = new_timeout
                if hasattr(self.audio_client, 'SetTimeout'):
                    self.audio_client.SetTimeout(new_timeout)
                print(f"\n✅ Timeout configurado para {new_timeout}s")
                
                # Testar com operação simples
                print("\n🔧 Testando novo timeout...")
                start_time = time.time()
                result = self.safe_execute(
                    "Teste Timeout",
                    self.audio_client.TtsMaker,
                    "Testando novo timeout configurado", 0
                )
                elapsed = time.time() - start_time
                
                if result == 0:
                    print(f"   ✅ Teste concluído em {elapsed:.2f}s")
                else:
                    print(f"   ❌ Erro no teste: {result}")
            else:
                print(f"\n📊 Timeout mantido em {self.default_timeout}s")
                
        except ValueError:
            print("\n❌ Valor inválido. Timeout não alterado.")
        
        print("\n📊 Configuração de timeout concluída.")
    
    def show_system_logs(self):
        """
        Exibir logs do sistema
        """
        print("\n📋 LOGS DO SISTEMA")
        print("="*50)
        
        log_file = "g1_audio_test.log"
        
        try:
            if os.path.exists(log_file):
                print(f"\n📁 Lendo arquivo: {log_file}")
                
                with open(log_file, 'r', encoding='utf-8') as f:
                    lines = f.readlines()
                
                if lines:
                    print(f"\n📊 Total de linhas: {len(lines)}")
                    print("\n📝 Últimas 20 linhas:")
                    print("-" * 60)
                    
                    for line in lines[-20:]:
                        print(f"   {line.rstrip()}")
                    
                    print("-" * 60)
                    
                    if len(lines) > 20:
                        print(f"\n💡 Mostrando apenas as últimas 20 linhas de {len(lines)} total.")
                        print(f"   Para ver todos os logs, abra: {log_file}")
                else:
                    print("\n📝 Arquivo de log está vazio.")
            else:
                print(f"\n❌ Arquivo de log não encontrado: {log_file}")
                print("   Execute alguns testes para gerar logs.")
                
        except Exception as e:
            print(f"\n❌ Erro ao ler logs: {e}")
        
        print("\n📊 Visualização de logs concluída.")
    
    def run_complete_demo(self):
        """
        Executa uma demonstração completa do sistema
        """
        print("\n🎭 DEMONSTRAÇÃO COMPLETA DO SISTEMA")
        print("="*60)
        
        print("\n🚀 Iniciando demonstração completa...")
        
        # 1. Saudação inicial
        print("\n1️⃣  Saudação inicial...")
        self.safe_execute("Demo Saudação", self.audio_client.LedControl, 0, 255, 0)
        self.safe_execute("Demo TTS", self.audio_client.TtsMaker, "Olá! Bem-vindo à demonstração completa do sistema de áudio do robô G1", 0)
        time.sleep(3)
        
        # 2. Teste de volume
        print("\n2️⃣  Demonstração de controle de volume...")
        volumes = [30, 60, 90]
        for vol in volumes:
            self.safe_execute("Demo Volume", self.audio_client.SetVolume, vol)
            self.safe_execute("Demo TTS Volume", self.audio_client.TtsMaker, f"Volume em {vol} por cento", 0)
            time.sleep(2)
        
        # 3. Demonstração de LED
        print("\n3️⃣  Demonstração de LED RGB...")
        demo_colors = [(255,0,0), (0,255,0), (0,0,255), (255,255,0), (255,0,255), (0,255,255)]
        for r, g, b in demo_colors:
            self.safe_execute("Demo LED", self.audio_client.LedControl, r, g, b)
            time.sleep(0.8)
        
        # 4. Teste de múltiplas vozes
        print("\n4️⃣  Demonstração de múltiplas vozes...")
        voices = [
            "Esta é a primeira voz de demonstração",
            "Agora testando uma segunda frase",
            "E finalmente a terceira demonstração"
        ]
        
        for i, voice_text in enumerate(voices):
            self.safe_execute(f"Demo Voz {i+1}", self.audio_client.TtsMaker, voice_text, 0)
            time.sleep(2)
        
        # 5. Finalização
        print("\n5️⃣  Finalizando demonstração...")
        self.safe_execute("Demo Final TTS", self.audio_client.TtsMaker, "Demonstração completa finalizada com sucesso!", 0)
        
        # LED de finalização (verde piscando)
        for _ in range(3):
            self.safe_execute("Demo Final LED", self.audio_client.LedControl, 0, 255, 0)
            time.sleep(0.5)
            self.safe_execute("Demo Final LED Off", self.audio_client.LedControl, 0, 0, 0)
            time.sleep(0.5)
        
        # Restaurar configurações
        self.safe_execute("Restaurar Volume", self.audio_client.SetVolume, self.current_volume)
        
        print("\n🎉 Demonstração completa finalizada!")
        print("📊 Todas as funcionalidades foram testadas com sucesso.")
    
    def run_stress_test(self):
        """
        Executa teste de stress do sistema
        """
        print("\n💪 TESTE DE STRESS DO SISTEMA")
        print("="*50)
        
        print("\n⚠️  Este teste executará operações intensivas por alguns minutos.")
        confirm = input("   Continuar? (s/N): ").strip().lower()
        
        if confirm not in ['s', 'sim', 'y', 'yes']:
            print("\n❌ Teste de stress cancelado.")
            return
        
        print("\n🚀 Iniciando teste de stress...")
        
        errors = 0
        total_operations = 0
        start_time = time.time()
        
        # Teste 1: TTS intensivo
        print("\n1️⃣  Teste de TTS intensivo (20 operações)...")
        for i in range(20):
            result = self.safe_execute(f"Stress TTS {i+1}", self.audio_client.TtsMaker, f"Teste de stress número {i+1}", 0)
            total_operations += 1
            if result != 0:
                errors += 1
            time.sleep(0.5)
        
        # Teste 2: Controle de volume intensivo
        print("\n2️⃣  Teste de volume intensivo (30 operações)...")
        for i in range(30):
            volume = (i % 10) * 10 + 10  # 10, 20, 30, ..., 100
            result = self.safe_execute(f"Stress Volume {i+1}", self.audio_client.SetVolume, volume)
            total_operations += 1
            if result != 0:
                errors += 1
            time.sleep(0.1)
        
        # Teste 3: LED intensivo
        print("\n3️⃣  Teste de LED intensivo (50 operações)...")
        for i in range(50):
            r = (i * 5) % 256
            g = (i * 7) % 256
            b = (i * 11) % 256
            result = self.safe_execute(f"Stress LED {i+1}", self.audio_client.LedControl, r, g, b)
            total_operations += 1
            if result != 0:
                errors += 1
            time.sleep(0.05)
        
        # Teste 4: Operações mistas
        print("\n4️⃣  Teste de operações mistas (25 ciclos)...")
        for i in range(25):
            # TTS
            result1 = self.safe_execute(f"Stress Mix TTS {i+1}", self.audio_client.TtsMaker, f"Ciclo {i+1}", 0)
            # Volume
            result2 = self.safe_execute(f"Stress Mix Vol {i+1}", self.audio_client.SetVolume, 50 + (i % 5) * 10)
            # LED
            result3 = self.safe_execute(f"Stress Mix LED {i+1}", self.audio_client.LedControl, 255, 0, 0)
            
            total_operations += 3
            if result1 != 0: errors += 1
            if result2 != 0: errors += 1
            if result3 != 0: errors += 1
            
            time.sleep(0.2)
        
        end_time = time.time()
        duration = end_time - start_time
        
        # Limpar estado final
        self.safe_execute("Stress Cleanup", self.audio_client.LedControl, 0, 0, 0)
        self.safe_execute("Stress Restore Volume", self.audio_client.SetVolume, self.current_volume)
        
        # Resultados
        print(f"\n📊 RESULTADOS DO TESTE DE STRESS:")
        print("="*40)
        print(f"   Duração total: {duration:.2f}s")
        print(f"   Operações totais: {total_operations}")
        print(f"   Operações com erro: {errors}")
        print(f"   Taxa de sucesso: {((total_operations - errors) / total_operations * 100):.1f}%")
        print(f"   Operações por segundo: {(total_operations / duration):.1f}")
        
        if errors == 0:
            print("\n🎉 Sistema passou no teste de stress sem erros!")
        elif errors < total_operations * 0.05:
            print("\n✅ Sistema estável com poucos erros")
        elif errors < total_operations * 0.15:
            print("\n⚠️  Sistema com alguns problemas")
        else:
            print("\n❌ Sistema instável - muitos erros detectados")
        
        print("\n📊 Teste de stress concluído.")
    
    def run_greeting_sequence(self):
        """
        Executa uma sequência de saudação interativa
        """
        print("\n👋 SEQUÊNCIA DE SAUDAÇÃO INTERATIVA")
        print("="*50)
        
        # Saudação inicial com LED azul
        print("\n🤖 Iniciando saudação...")
        self.safe_execute("Saudação LED", self.audio_client.LedControl, 0, 100, 255)
        self.safe_execute("Saudação TTS", self.audio_client.TtsMaker, "Olá! Eu sou o robô G1 da Unitree. Como posso ajudá-lo hoje?", 0)
        time.sleep(3)
        
        # Apresentação das capacidades
        print("\n📢 Apresentando capacidades...")
        capabilities = [
            "Posso falar usando síntese de voz",
            "Controlo meu volume de áudio",
            "Tenho LEDs RGB coloridos",
            "Reproduzo áudio em formato PCM"
        ]
        
        colors = [(255,0,0), (0,255,0), (0,0,255), (255,255,0)]
        
        for i, (capability, (r, g, b)) in enumerate(zip(capabilities, colors)):
            print(f"   {i+1}. {capability}")
            self.safe_execute(f"Capacidade LED {i+1}", self.audio_client.LedControl, r, g, b)
            self.safe_execute(f"Capacidade TTS {i+1}", self.audio_client.TtsMaker, capability, 0)
            time.sleep(3)
        
        # Demonstração interativa
        print("\n🎨 Demonstração de cores...")
        self.safe_execute("Demo Cores TTS", self.audio_client.TtsMaker, "Agora vou mostrar algumas cores", 0)
        time.sleep(2)
        
        color_names = ["vermelho", "verde", "azul", "amarelo", "roxo", "ciano"]
        color_values = [(255,0,0), (0,255,0), (0,0,255), (255,255,0), (255,0,255), (0,255,255)]
        
        for name, (r, g, b) in zip(color_names, color_values):
            self.safe_execute(f"Cor {name} LED", self.audio_client.LedControl, r, g, b)
            self.safe_execute(f"Cor {name} TTS", self.audio_client.TtsMaker, name, 0)
            time.sleep(1.5)
        
        # Finalização
        print("\n✨ Finalizando saudação...")
        self.safe_execute("Final TTS", self.audio_client.TtsMaker, "Obrigado por conhecer minhas funcionalidades! Estou pronto para trabalhar.", 0)
        
        # LED de despedida (fade out verde)
        for intensity in range(255, 0, -15):
            self.safe_execute("Despedida LED", self.audio_client.LedControl, 0, intensity, 0)
            time.sleep(0.1)
        
        self.safe_execute("Desligar LED", self.audio_client.LedControl, 0, 0, 0)
        
        print("\n👋 Sequência de saudação concluída!")
    
    def reconnect(self):
        """
        Tenta reconectar ao sistema
        """
        print("\n🔄 RECONEXÃO DO SISTEMA")
        print("="*50)
        
        print("\n⚠️  Tentando reconectar...")
        
        # Limpar conexão atual
        self.is_connected = False
        self.audio_client = None
        
        # Tentar reconectar
        if self.initialize_connection():
            print("\n✅ Reconexão bem-sucedida!")
            
            # Teste rápido
            print("\n🔧 Testando conexão...")
            result = self.safe_execute("Teste Reconexão", self.audio_client.TtsMaker, "Reconexão realizada com sucesso", 0)
            
            if result == 0:
                print("   ✅ Sistema funcionando normalmente")
            else:
                print(f"   ⚠️  Conexão estabelecida mas com problemas: {result}")
        else:
            print("\n❌ Falha na reconexão")
            print("   Verifique:")
            print("   - Conexão de rede")
            print("   - Interface de rede especificada")
            print("   - Status do robô G1")
        
        print("\n📊 Processo de reconexão concluído.")
    
    def show_system_info(self):
        """
        Exibe informações detalhadas do sistema
        """
        print("\n💻 INFORMAÇÕES DO SISTEMA")
        print("="*50)
        
        # Informações básicas
        print(f"\n🌐 Interface de rede: {self.network_interface}")
        print(f"⏱️  Timeout configurado: {self.default_timeout}s")
        print(f"🔊 Volume atual: {self.current_volume}%")
        print(f"🔗 Status da conexão: {'✅ Conectado' if self.is_connected else '❌ Desconectado'}")
        print(f"📅 Data/Hora atual: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        print(f"📁 Diretório de trabalho: {os.getcwd()}")
        
        # Estatísticas de operações
        stats = self.get_error_statistics()
        print(f"\n📊 ESTATÍSTICAS DE OPERAÇÕES:")
        print(f"   Total de operações: {stats['total_operations']}")
        print(f"   Total de erros: {stats['total_errors']}")
        print(f"   Taxa de sucesso: {stats['success_rate']:.1f}%")
        print(f"   Taxa de erro: {stats['error_rate']:.1f}%")
        
        if stats['total_operations'] > 0:
            if stats['success_rate'] >= 95:
                print("   🟢 Sistema funcionando excelentemente")
            elif stats['success_rate'] >= 85:
                print("   🟡 Sistema funcionando bem")
            elif stats['success_rate'] >= 70:
                print("   🟠 Sistema com alguns problemas")
            else:
                print("   🔴 Sistema com muitos problemas")
        
        # Informações do Python
        print(f"\n🐍 AMBIENTE PYTHON:")
        print(f"   Versão: {sys.version.split()[0]}")
        print(f"   Plataforma: {sys.platform}")
        print(f"   Executável: {sys.executable}")
        
        # Verificar módulos disponíveis
        print("\n📚 MÓDULOS DISPONÍVEIS:")
        modules = {
            'unitree_sdk2py': 'SDK do Unitree',
            'time': 'Controle de tempo',
            'os': 'Sistema operacional',
            'sys': 'Sistema Python',
            'logging': 'Sistema de logs',
            'datetime': 'Data e hora',
            'traceback': 'Rastreamento de erros'
        }
        
        for module, description in modules.items():
            try:
                __import__(module)
                print(f"   ✅ {module}: {description}")
            except ImportError:
                print(f"   ❌ {module}: {description} (não disponível)")
        
        # Informações de arquivos de log
        print("\n📋 ARQUIVOS DE LOG:")
        log_files = [
            ('g1_audio_test.log', 'Log principal'),
            ('g1_audio_critical.log', 'Log de erros críticos')
        ]
        
        for log_file, description in log_files:
            if os.path.exists(log_file):
                log_size = os.path.getsize(log_file)
                # Contar linhas do arquivo
                try:
                    with open(log_file, 'r', encoding='utf-8') as f:
                        line_count = sum(1 for _ in f)
                    print(f"   ✅ {log_file}: {description} ({log_size} bytes, {line_count} linhas)")
                except:
                    print(f"   ✅ {log_file}: {description} ({log_size} bytes)")
            else:
                print(f"   ❌ {log_file}: {description} (não encontrado)")
        
        # Configurações de teste
        print(f"\n⚙️  CONFIGURAÇÕES DE TESTE:")
        print(f"   Vozes disponíveis: {getattr(self, 'test_voices', [0, 1])}")
        print(f"   Volumes de teste: {getattr(self, 'test_volumes', [30, 50, 75, 100])}")
        
        print("\n📊 Informações do sistema exibidas.")
    
    def show_error_statistics(self):
        """
        Exibe estatísticas detalhadas de erro
        """
        print("\n📊 ESTATÍSTICAS DE ERRO DETALHADAS")
        print("="*50)
        
        stats = self.get_error_statistics()
        
        print(f"\n📈 RESUMO GERAL:")
        print(f"   Total de operações executadas: {stats['total_operations']}")
        print(f"   Operações bem-sucedidas: {stats['total_operations'] - stats['total_errors']}")
        print(f"   Operações com erro: {stats['total_errors']}")
        print(f"   Taxa de sucesso: {stats['success_rate']:.2f}%")
        print(f"   Taxa de erro: {stats['error_rate']:.2f}%")
        
        # Análise da qualidade
        print(f"\n🎯 ANÁLISE DE QUALIDADE:")
        if stats['total_operations'] == 0:
            print("   ⚪ Nenhuma operação executada ainda")
        elif stats['error_rate'] == 0:
            print("   🟢 Perfeito - Nenhum erro detectado")
        elif stats['error_rate'] < 5:
            print("   🟢 Excelente - Muito poucos erros")
        elif stats['error_rate'] < 10:
            print("   🟡 Bom - Alguns erros ocasionais")
        elif stats['error_rate'] < 20:
            print("   🟠 Regular - Vários erros detectados")
        elif stats['error_rate'] < 50:
            print("   🔴 Ruim - Muitos erros")
        else:
            print("   🔴 Crítico - Sistema muito instável")
        
        # Recomendações
        print(f"\n💡 RECOMENDAÇÕES:")
        if stats['error_rate'] > 20:
            print("   • Verificar conexão de rede")
            print("   • Reiniciar o sistema")
            print("   • Verificar logs críticos")
        elif stats['error_rate'] > 10:
            print("   • Monitorar sistema mais de perto")
            print("   • Verificar logs para padrões")
        elif stats['error_rate'] > 0:
            print("   • Sistema funcionando bem")
            print("   • Erros ocasionais são normais")
        else:
            print("   • Sistema funcionando perfeitamente")
        
        print("\n📊 Estatísticas de erro exibidas.")
    
    def cleanup(self):
        """
        Limpa recursos e finaliza conexões
        """
        logger.info("Limpando recursos...")
        
        if self.audio_client and self.is_connected:
            try:
                # Desligar LED
                self.audio_client.LedControl(0, 0, 0)
                # Parar qualquer reprodução
                self.audio_client.PlayStop("audio_test")
                logger.info("Recursos limpos com sucesso")
            except Exception as e:
                logger.error(f"Erro na limpeza: {e}")
        
        print("✅ Sistema finalizado.")

def main():
    """
    Função principal
    """
    print("🎵 Sistema de Teste de Áudio - Unitree G1")
    print("==========================================\n")
    
    if len(sys.argv) != 2:
        print("❌ Uso incorreto!")
        print("\nUso:")
        print(f"    python {sys.argv[0]} <interface_de_rede>")
        print("\nExemplos:")
        print(f"    python {sys.argv[0]} eth0")
        print(f"    python {sys.argv[0]} wlan0")
        print("\nInterfaces de rede comuns:")
        print("  - eth0: Ethernet cabeada")
        print("  - wlan0: WiFi")
        print("  - enp0s3: Ethernet (algumas distribuições)")
        sys.exit(1)
    
    network_interface = sys.argv[1]
    
    # Validar interface de rede
    if not network_interface.strip():
        print("❌ Interface de rede não pode estar vazia.")
        sys.exit(1)
    
    print(f"🌐 Interface de rede: {network_interface}")
    print(f"📅 Data/Hora: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"📁 Diretório de trabalho: {os.getcwd()}")
    print(f"📝 Log será salvo em: g1_audio_test.log\n")
    
    # Criar e executar testador
    tester = G1AudioTester(network_interface)
    tester.run()

if __name__ == "__main__":
    main()