# Documentação do Sistema de Áudio - Robô G1 Unitree

## 1. Visão Geral do Sistema

O sistema de áudio do robô G1 da Unitree oferece funcionalidades completas para controle de microfone e alto-falante, incluindo síntese de voz (TTS), reconhecimento de voz (ASR), reprodução de áudio e controle de volume. O sistema utiliza comunicação via DDS e suporta formatos de áudio específicos otimizados para robótica.

### 1.1 Características Principais

* **Síntese de Voz (TTS)**: Conversão de texto para fala com múltiplas vozes

* **Reconhecimento de Voz (ASR)**: Captura e processamento de comandos de voz

* **Reprodução de Áudio**: Suporte para streaming PCM e arquivos WAV

* **Controle de Volume**: Ajuste dinâmico do volume do sistema

* **Controle de LED**: Integração com sistema de iluminação RGB

* **Formato Suportado**: PCM 16-bit, 16kHz, mono

## 2. Configuração e Inicialização

### 2.1 Importação e Configuração Básica

```python
from unitree_sdk2py.core.channel import ChannelFactoryInitialize
from unitree_sdk2py.g1.audio.g1_audio_client import AudioClient

# Inicializar canal de comunicação
ChannelFactoryInitialize(0, "interface_de_rede")  # ex: "eth0", "wlan0"

# Criar cliente de áudio
audio_client = AudioClient()
audio_client.SetTimeout(10.0)  # Timeout de 10 segundos
audio_client.Init()
```

### 2.2 Parâmetros de Configuração

| Parâmetro           | Tipo  | Descrição                          | Valor Padrão |
| ------------------- | ----- | ---------------------------------- | ------------ |
| `timeout`           | float | Timeout para operações (segundos)  | 10.0         |
| `network_interface` | str   | Interface de rede para comunicação | "eth0"       |
| `service_name`      | str   | Nome do serviço de áudio           | "voice"      |
| `api_version`       | str   | Versão da API                      | "1.0.0.0"    |

## 3. Comandos de Alto-Falante

### 3.1 Síntese de Voz (TTS)

#### Sintaxe

```python
code = audio_client.TtsMaker(text: str, speaker_id: int)
```

#### Parâmetros

| Parâmetro    | Tipo | Descrição                    | Valores Válidos             |
| ------------ | ---- | ---------------------------- | --------------------------- |
| `text`       | str  | Texto para conversão em fala | Qualquer string             |
| `speaker_id` | int  | ID da voz do locutor         | 0-N (dependente do sistema) |

#### Retorno

* `code` (int): Código de status (0 = sucesso)

#### Exemplo Prático

```python
# Síntese de voz básica
result = audio_client.TtsMaker("Olá, eu sou o robô G1!", 0)
if result == 0:
    print("TTS executado com sucesso")
else:
    print(f"Erro no TTS: {result}")

# Múltiplas vozes
audio_client.TtsMaker("Voz padrão", 0)
time.sleep(3)
audio_client.TtsMaker("Voz alternativa", 1)
```

### 3.2 Reprodução de Áudio PCM

#### Sintaxe

```python
code = audio_client.PlayStream(app_name: str, stream_id: str, pcm_data: bytes)
```

#### Parâmetros

| Parâmetro   | Tipo  | Descrição          | Formato              |
| ----------- | ----- | ------------------ | -------------------- |
| `app_name`  | str   | Nome da aplicação  | Identificador único  |
| `stream_id` | str   | ID único do stream | Timestamp ou UUID    |
| `pcm_data`  | bytes | Dados PCM de áudio | 16-bit little-endian |

#### Especificações de Áudio

* **Sample Rate**: 16kHz (16000 Hz)

* **Canais**: 1 (mono)

* **Bit Depth**: 16-bit

* **Formato**: PCM little-endian

* **Chunk Size**: 96000 bytes (≈3 segundos)

#### Exemplo Prático

```python
# Reprodução de arquivo WAV
from wav import read_wav, play_pcm_stream

# Carregar arquivo WAV
pcm_list, sample_rate, num_channels, is_ok = read_wav("audio.wav")

if is_ok and sample_rate == 16000 and num_channels == 1:
    # Reproduzir usando streaming
    play_pcm_stream(audio_client, pcm_list, "minha_app")
else:
    print("Formato de áudio não suportado")
```

### 3.3 Controle de Reprodução

#### Parar Reprodução

```python
code = audio_client.PlayStop(app_name: str)
```

#### Exemplo

```python
# Iniciar reprodução
audio_client.PlayStream("app_teste", "stream_001", pcm_data)

# Parar reprodução
audio_client.PlayStop("app_teste")
```

### 3.4 Controle de Volume

#### Obter Volume Atual

```python
code, volume_data = audio_client.GetVolume()
```

#### Definir Volume

```python
code = audio_client.SetVolume(volume: int)
```

#### Parâmetros

| Parâmetro | Tipo | Descrição       | Faixa |
| --------- | ---- | --------------- | ----- |
| `volume`  | int  | Nível de volume | 0-100 |

#### Exemplo Prático

```python
# Verificar volume atual
code, volume_info = audio_client.GetVolume()
if code == 0:
    current_volume = volume_info.get('volume', 0)
    print(f"Volume atual: {current_volume}%")

# Ajustar volume
audio_client.SetVolume(75)  # 75%
print("Volume ajustado para 75%")

# Verificar mudança
code, new_volume = audio_client.GetVolume()
if code == 0:
    print(f"Novo volume: {new_volume['volume']}%")
```

## 4. Comandos de Microfone

### 4.1 Reconhecimento de Voz (ASR)

**Nota**: A API ASR está registrada no sistema (`ROBOT_API_ID_AUDIO_ASR = 1002`), mas a implementação específica não está exposta no cliente atual. Esta funcionalidade pode estar disponível em versões futuras ou através de APIs de baixo nível.

#### API ID Disponível

```python
# ID da API ASR registrada
ROBOT_API_ID_AUDIO_ASR = 1002
```

### 4.2 Configurações de Captura

Para captura de áudio do microfone, o sistema suporta:

* **Sample Rate**: 16kHz

* **Formato**: PCM 16-bit

* **Canais**: 1 (mono)

* **Encoding**: Little-endian

## 5. Funcionalidades Auxiliares

### 5.1 Controle de LED RGB

#### Sintaxe

```python
code = audio_client.LedControl(R: int, G: int, B: int)
```

#### Parâmetros

| Parâmetro | Tipo | Descrição           | Faixa |
| --------- | ---- | ------------------- | ----- |
| `R`       | int  | Componente vermelho | 0-255 |
| `G`       | int  | Componente verde    | 0-255 |
| `B`       | int  | Componente azul     | 0-255 |

#### Exemplo Prático

```python
# Sequência de cores
audio_client.LedControl(255, 0, 0)    # Vermelho
time.sleep(1)
audio_client.LedControl(0, 255, 0)    # Verde
time.sleep(1)
audio_client.LedControl(0, 0, 255)    # Azul
time.sleep(1)
audio_client.LedControl(255, 255, 255) # Branco
```

## 6. Utilitários de Áudio

### 6.1 Manipulação de Arquivos WAV

#### Leitura de Arquivo WAV

```python
from wav import read_wav

pcm_list, sample_rate, num_channels, success = read_wav("arquivo.wav")
```

#### Escrita de Arquivo WAV

```python
from wav import write_wave

write_wave("saida.wav", 16000, pcm_samples, 1)
```

#### Streaming PCM

```python
from wav import play_pcm_stream

play_pcm_stream(
    client=audio_client,
    pcm_list=pcm_data,
    stream_name="meu_stream",
    chunk_size=96000,  # 3 segundos a 16kHz
    sleep_time=1.0,
    verbose=True
)
```

### 6.2 Parâmetros de Streaming

| Parâmetro    | Tipo  | Descrição              | Valor Padrão |
| ------------ | ----- | ---------------------- | ------------ |
| `chunk_size` | int   | Bytes por chunk        | 96000 (3s)   |
| `sleep_time` | float | Delay entre chunks (s) | 1.0          |
| `verbose`    | bool  | Log detalhado          | False        |

## 7. Códigos de Erro e Tratamento

### 7.1 Códigos de Status

| Código | Descrição | Ação Recomendada               |
| ------ | --------- | ------------------------------ |
| 0      | Sucesso   | Continuar operação             |
| != 0   | Erro      | Verificar parâmetros e conexão |

### 7.2 Tratamento de Erros

```python
def safe_audio_operation():
    try:
        # Verificar conexão
        code, volume = audio_client.GetVolume()
        if code != 0:
            print(f"Erro de conexão: {code}")
            return False
        
        # Executar operação
        result = audio_client.TtsMaker("Teste", 0)
        if result == 0:
            print("Operação bem-sucedida")
            return True
        else:
            print(f"Erro na operação: {result}")
            return False
            
    except Exception as e:
        print(f"Exceção: {e}")
        return False
```

### 7.3 Validação de Formato de Áudio

```python
def validate_audio_format(sample_rate, channels, bits_per_sample):
    """
    Valida se o formato de áudio é suportado pelo G1
    """
    if sample_rate != 16000:
        print(f"Sample rate não suportado: {sample_rate}Hz (requerido: 16000Hz)")
        return False
    
    if channels != 1:
        print(f"Número de canais não suportado: {channels} (requerido: 1)")
        return False
    
    if bits_per_sample != 16:
        print(f"Bits por amostra não suportado: {bits_per_sample} (requerido: 16)")
        return False
    
    return True
```

## 8. Limitações e Considerações Técnicas

### 8.1 Limitações de Hardware

* **Sample Rate Fixo**: Apenas 16kHz suportado

* **Formato Único**: PCM 16-bit little-endian mono

* **Latência**: Dependente da rede e processamento

* **Concurrent Streams**: Limitado pelo hardware

### 8.2 Considerações de Rede

* **Largura de Banda**: \~32 KB/s para áudio 16kHz mono

* **Latência de Rede**: Pode afetar tempo de resposta

* **Timeout**: Configurar adequadamente para ambiente

### 8.3 Limitações de Software

* **API ASR**: Não implementada no cliente atual

* **Formatos**: Apenas WAV/PCM suportados nativamente

* **Concurrent Apps**: Gerenciamento por `app_name`

## 9. Integração com Outros Sistemas

### 9.1 Integração com Sistema de Locomoção

```python
from unitree_sdk2py.g1.loco.g1_loco_client import LocoClient

# Coordenar áudio com movimento
sport_client = LocoClient()
sport_client.SetTimeout(10.0)
sport_client.Init()

# Executar ação coordenada
sport_client.WaveHand()  # Acenar
audio_client.TtsMaker("Olá! Como você está?", 0)  # Falar
```

### 9.2 Sincronização de Eventos

```python
import time

def coordinated_greeting():
    # Iniciar movimento
    sport_client.WaveHand()
    
    # Aguardar posicionamento
    time.sleep(1)
    
    # Iniciar fala
    audio_client.TtsMaker("Prazer em conhecê-lo!", 0)
    
    # Efeito visual
    audio_client.LedControl(0, 255, 0)  # Verde
    time.sleep(3)
    audio_client.LedControl(0, 0, 0)    # Desligar
```

## 10. Exemplos Práticos Completos

### 10.1 Sistema de Saudação Interativo

```python
import time
import sys
from unitree_sdk2py.core.channel import ChannelFactoryInitialize
from unitree_sdk2py.g1.audio.g1_audio_client import AudioClient
from unitree_sdk2py.g1.loco.g1_loco_client import LocoClient

def interactive_greeting_system(network_interface):
    # Inicialização
    ChannelFactoryInitialize(0, network_interface)
    
    audio_client = AudioClient()
    audio_client.SetTimeout(10.0)
    audio_client.Init()
    
    sport_client = LocoClient()
    sport_client.SetTimeout(10.0)
    sport_client.Init()
    
    # Configurar volume
    audio_client.SetVolume(80)
    
    # Sequência de saudação
    print("Iniciando sequência de saudação...")
    
    # 1. Acenar
    sport_client.WaveHand()
    
    # 2. Saudação inicial
    audio_client.TtsMaker("Olá! Eu sou o robô G1 da Unitree!", 0)
    time.sleep(4)
    
    # 3. Demonstração de capacidades
    audio_client.TtsMaker("Vou demonstrar minhas capacidades de áudio.", 0)
    time.sleep(3)
    
    # 4. Teste de LED
    audio_client.TtsMaker("Primeiro, o controle de LED.", 0)
    time.sleep(2)
    
    colors = [(255, 0, 0), (0, 255, 0), (0, 0, 255), (255, 255, 0)]
    color_names = ["vermelho", "verde", "azul", "amarelo"]
    
    for color, name in zip(colors, color_names):
        audio_client.LedControl(*color)
        audio_client.TtsMaker(f"Cor {name}", 0)
        time.sleep(2)
    
    # 5. Desligar LED
    audio_client.LedControl(0, 0, 0)
    
    # 6. Teste de volume
    audio_client.TtsMaker("Agora vou testar diferentes volumes.", 0)
    time.sleep(3)
    
    volumes = [30, 60, 90]
    for vol in volumes:
        audio_client.SetVolume(vol)
        audio_client.TtsMaker(f"Volume em {vol} por cento", 0)
        time.sleep(2)
    
    # 7. Finalização
    audio_client.SetVolume(80)
    audio_client.TtsMaker("Demonstração concluída. Obrigado!", 0)
    time.sleep(3)
    
    print("Sequência de saudação finalizada.")

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Uso: python script.py <interface_de_rede>")
        sys.exit(1)
    
    interactive_greeting_system(sys.argv[1])
```

### 10.2 Reprodutor de Áudio WAV

```python
import sys
from unitree_sdk2py.core.channel import ChannelFactoryInitialize
from unitree_sdk2py.g1.audio.g1_audio_client import AudioClient
from wav import read_wav, play_pcm_stream

def audio_player(network_interface, wav_file, volume=80):
    # Inicialização
    ChannelFactoryInitialize(0, network_interface)
    
    audio_client = AudioClient()
    audio_client.SetTimeout(10.0)
    audio_client.Init()
    
    # Configurar volume
    audio_client.SetVolume(volume)
    
    # Carregar arquivo WAV
    print(f"Carregando arquivo: {wav_file}")
    pcm_list, sample_rate, num_channels, success = read_wav(wav_file)
    
    if not success:
        print("Erro ao carregar arquivo WAV")
        return False
    
    # Validar formato
    if sample_rate != 16000 or num_channels != 1:
        print(f"Formato não suportado: {sample_rate}Hz, {num_channels} canais")
        print("Requerido: 16000Hz, 1 canal (mono)")
        return False
    
    print(f"Arquivo carregado com sucesso:")
    print(f"  Sample Rate: {sample_rate}Hz")
    print(f"  Canais: {num_channels}")
    print(f"  Duração: {len(pcm_list) / (sample_rate * 2):.2f} segundos")
    
    # Reproduzir
    print("Iniciando reprodução...")
    play_pcm_stream(
        client=audio_client,
        pcm_list=pcm_list,
        stream_name="audio_player",
        verbose=True
    )
    
    print("Reprodução finalizada.")
    
    # Parar stream
    audio_client.PlayStop("audio_player")
    
    return True

if __name__ == "__main__":
    if len(sys.argv) < 3:
        print("Uso: python script.py <interface_de_rede> <arquivo.wav> [volume]")
        sys.exit(1)
    
    interface = sys.argv[1]
    wav_file = sys.argv[2]
    volume = int(sys.argv[3]) if len(sys.argv) > 3 else 80
    
    audio_player(interface, wav_file, volume)
```

## 11. Solução de Problemas

### 11.1 Problemas Comuns

#### Erro de Conexão

```
Problema: Timeout ou erro de conexão
Solução: 
1. Verificar interface de rede
2. Confirmar conectividade com o robô
3. Aumentar timeout se necessário
```

#### Formato de Áudio Não Suportado

```
Problema: Arquivo WAV não reproduz
Solução:
1. Converter para 16kHz, mono, 16-bit
2. Usar ferramentas como ffmpeg:
   ffmpeg -i input.wav -ar 16000 -ac 1 -sample_fmt s16 output.wav
```

#### Volume Não Funciona

```
Problema: Comando de volume não tem efeito
Solução:
1. Verificar se o valor está entre 0-100
2. Confirmar se o áudio está sendo reproduzido
3. Testar com TTS primeiro
```

### 11.2 Diagnóstico de Sistema

```python
def diagnose_audio_system(audio_client):
    """
    Executa diagnóstico completo do sistema de áudio
    """
    print("=== Diagnóstico do Sistema de Áudio ===")
    
    # Teste 1: Conectividade
    print("1. Testando conectividade...")
    code, volume_data = audio_client.GetVolume()
    if code == 0:
        print(f"   ✓ Conectividade OK - Volume atual: {volume_data.get('volume', 'N/A')}%")
    else:
        print(f"   ✗ Erro de conectividade: {code}")
        return False
    
    # Teste 2: TTS
    print("2. Testando TTS...")
    result = audio_client.TtsMaker("Teste de síntese de voz", 0)
    if result == 0:
        print("   ✓ TTS funcionando")
    else:
        print(f"   ✗ Erro no TTS: {result}")
    
    # Teste 3: Controle de Volume
    print("3. Testando controle de volume...")
    original_volume = volume_data.get('volume', 50)
    
    test_result = audio_client.SetVolume(75)
    if test_result == 0:
        code, new_volume = audio_client.GetVolume()
        if code == 0 and new_volume.get('volume') == 75:
            print("   ✓ Controle de volume funcionando")
            # Restaurar volume original
            audio_client.SetVolume(original_volume)
        else:
            print("   ✗ Erro na verificação de volume")
    else:
        print(f"   ✗ Erro ao definir volume: {test_result}")
    
    # Teste 4: LED
    print("4. Testando controle de LED...")
    led_result = audio_client.LedControl(0, 255, 0)
    if led_result == 0:
        print("   ✓ Controle de LED funcionando")
        time.sleep(1)
        audio_client.LedControl(0, 0, 0)  # Desligar
    else:
        print(f"   ✗ Erro no controle de LED: {led_result}")
    
    print("=== Diagnóstico Concluído ===")
    return True
```

### 11.3 Logs e Depuração

```python
import logging

# Configurar logging
logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(levelname)s - %(message)s'
)

def debug_audio_operation(audio_client, operation_name, operation_func):
    """
    Executa operação de áudio com logging detalhado
    """
    logging.info(f"Iniciando operação: {operation_name}")
    
    try:
        start_time = time.time()
        result = operation_func()
        end_time = time.time()
        
        logging.info(f"Operação {operation_name} concluída em {end_time - start_time:.2f}s")
        logging.info(f"Resultado: {result}")
        
        return result
        
    except Exception as e:
        logging.error(f"Erro na operação {operation_name}: {e}")
        return None

# Exemplo de uso
result = debug_audio_operation(
    audio_client,
    "TTS_Test",
    lambda: audio_client.TtsMaker("Teste de debug", 0)
)
```

## 12. APIs de Referência

### 12.1 IDs de API

```python
# Constantes de API definidas em g1_audio_api.py
AUDIO_SERVICE_NAME = "voice"
AUDIO_API_VERSION = "1.0.0.0"

# IDs de API
ROBOT_API_ID_AUDIO_TTS = 1001        # Síntese de voz
ROBOT_API_ID_AUDIO_ASR = 1002        # Reconhecimento de voz
ROBOT_API_ID_AUDIO_START_PLAY = 1003 # Iniciar reprodução
ROBOT_API_ID_AUDIO_STOP_PLAY = 1004  # Parar reprodução
ROBOT_API_ID_AUDIO_GET_VOLUME = 1005 # Obter volume
ROBOT_API_ID_AUDIO_SET_VOLUME = 1006 # Definir volume
ROBOT_API_ID_AUDIO_SET_RGB_LED = 1010 # Controle de LED
```

### 12.2 Estrutura de Dados

#### Parâmetros TTS

```json
{
    "index": 1,
    "text": "Texto para síntese",
    "speaker_id": 0
}
```

#### Parâmetros de Volume

```json
{
    "volume": 75
}
```

#### Parâmetros de LED

```json
{
    "R": 255,
    "G": 0,
    "B": 0
}
```

#### Parâmetros de Stream

```json
{
    "app_name": "minha_aplicacao",
    "stream_id": "stream_12345"
}
```

***

**Versão da Documentação**: 1.0\
**Data**: 2024\
**SDK**: Unitree SDK2 Python\
**Robô**: G1 Humanoid Robot
