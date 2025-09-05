# Scripts de Teste de Câmera - Robô G1

Este conjunto de scripts permite testar câmeras USB ou integradas no sistema, já que o robô G1 não possui APIs específicas de vídeo no SDK (diferente do Go2/B2).

## 📋 Arquivos Incluídos

### 1. `camera_test.py` - Script Completo
Script avançado com múltiplas funcionalidades:
- ✅ Detecção automática de câmeras (Linux: /dev/video0-11, Windows/Mac: IDs 0-9)
- ✅ Identificação específica de câmeras Intel RealSense
- ✅ Teste individual de câmeras com seleção interativa
- ✅ Teste simultâneo de múltiplas câmeras
- ✅ Teste específico apenas para câmeras RealSense
- ✅ Diagnósticos detalhados (resolução, FPS, propriedades avançadas)
- ✅ Salvamento de imagens com timestamp
- ✅ Interface de menu interativa com comandos avançados
- ✅ Relatórios em JSON
- ✅ Tratamento robusto de erros e timeouts

### 2. `simple_camera_test.py` - Script Simples
Script básico para teste rápido:
- ✅ Detecção automática de câmeras (Linux: /dev/video*, outros: IDs 0-9)
- ✅ Identificação de câmeras Intel RealSense
- ✅ Preview em tempo real
- ✅ Salvamento de imagens
- ✅ Interface simplificada
- ✅ Tratamento de erros e timeouts

## 🚀 Como Usar

### Pré-requisitos
```bash
# Instalar OpenCV (se não estiver instalado)
pip install opencv-python
```

### Uso Rápido - Script Simples
```bash
python simple_camera_test.py
```

**Controles:**
- `q` ou `ESC`: Sair
- `s`: Salvar imagem atual

### Uso Avançado - Script Completo
```bash
python camera_test.py
```

**Menu de Opções:**
1. **Testar câmera individual** - Seleção interativa com informações detalhadas
2. **Testar múltiplas câmeras** - Exibe várias câmeras simultaneamente
3. **Executar diagnósticos** - Gera relatório detalhado
4. **Salvar frame em base64** - Converte frame para formato base64
5. **Listar câmeras disponíveis** - Mostra informações detalhadas
6. **Testar apenas câmeras RealSense** - Teste específico para Intel RealSense
7. **Sair** - Encerra o programa

## 📁 Estrutura de Arquivos Gerados

```
unitree_sdk2_python/
├── camera_test.py              # Script principal
├── simple_camera_test.py       # Script simples
├── README_CAMERA_TEST.md       # Este arquivo
├── camera_captures/            # Diretório criado automaticamente
│   ├── camera_0_20241201_143022.jpg
│   ├── camera_1_20241201_143045.jpg
│   └── diagnostics_20241201_143100.json
└── captures/                   # Para o script simples
    └── camera_0_20241201_143200.jpg
```

## 🎯 Funcionalidades

- ✅ **Detecção automática** de câmeras USB e integradas (Linux: /dev/video0-11)
- 🔍 **Identificação Intel RealSense** - Detecta automaticamente câmeras de profundidade
- 📷 **Captura de imagens** com timestamp automático
- 🎥 **Gravação de vídeos** em formato MP4
- 🔍 **Diagnósticos completos** de câmeras (resolução, FPS, propriedades avançadas)
- 🖥️ **Interface interativa** com menu intuitivo e seleção avançada
- 📊 **Logs detalhados** de todas as operações
- 🔄 **Suporte a múltiplas câmeras** simultaneamente
- 🎯 **Teste específico RealSense** - Funcionalidade dedicada para câmeras Intel
- 💾 **Organização automática** de arquivos em diretório dedicado
- 🔐 **Salvamento em Base64** - Converte frames para formato base64 em arquivos .txt
- 🔓 **Decodificação Base64** - Script dedicado para converter base64 de volta para imagens
- ⚡ **Tratamento robusto de erros** - Timeouts e verificação de qualidade de frames
- 🔧 **Informações detalhadas** - Propriedades técnicas, resoluções suportadas

### 🎮 Controles Durante Visualização

- **`q`** ou **ESC** - Sair da visualização
- **`s`** - Salvar imagem atual
- **`r`** - Iniciar/Parar gravação de vídeo
- **`d`** - Mostrar/Ocultar diagnósticos em tempo real
- **`b`** - Salvar frame atual em formato base64 (.txt)

## 📁 Estrutura de Arquivos

Todos os arquivos são salvos no diretório `camera_captures/`:

```
camera_captures/
├── camera_0_20241201_143022.jpg           # Imagens capturadas
├── camera_0_video_20241201_143100.mp4     # Vídeos gravados
├── camera_0_frame_base64_20241201_143200.txt # Frames em base64
├── camera_0_frame_base64_20241201_143200_decoded.jpg # Imagens decodificadas
├── diagnostics_20241201_143200.json       # Relatórios de diagnóstico
└── camera_test_log_20241201.txt           # Logs das operações
```

## 🔧 Scripts Disponíveis

### 1. `simple_camera_test.py`
**Teste básico e rápido**
```bash
python simple_camera_test.py
```

### 2. `camera_test.py`
**Interface completa com menu**
```bash
python camera_test.py
```

### 3. `demo_camera_usage.py`
**Demonstração e exemplo de uso**
```bash
python demo_camera_usage.py
```

### 4. `decode_base64_frame.py`
**Decodificador de frames base64**
```bash
python decode_base64_frame.py
# ou
python decode_base64_frame.py camera_captures/camera_0_frame_base64_20241201_143200.txt
```

## 🔧 Funcionalidades Detalhadas

### Detecção Automática
**Linux:**
- Escaneia dispositivos /dev/video0 até /dev/video11
- Identifica automaticamente câmeras Intel RealSense
- Usa v4l2-ctl para obter informações detalhadas
- Verifica dispositivos USB Intel (lsusb)

**Windows/Mac:**
- Escaneia IDs de câmera 0-9
- Detecta RealSense por capacidade de múltiplas resoluções
- Verifica se cada câmera pode capturar frames
- Lista todas as câmeras funcionais

### Teste Individual
- **Seleção interativa** com informações detalhadas
- **Comandos especiais**: 'info X' para detalhes, 'test X' para teste rápido
- Configura resolução (640x480 padrão)
- Exibe preview em tempo real
- Mostra informações do frame
- Permite salvamento manual
- **Propriedades técnicas**: brilho, contraste, saturação, exposição
- **Resoluções suportadas**: testa automaticamente múltiplas resoluções

### Teste Múltiplo
- Combina múltiplas câmeras em uma janela
- Organiza automaticamente em grid
- Sincroniza captura de todas as câmeras

### Diagnósticos
- **Resolução suportada**: testa múltiplas resoluções automaticamente
- **Taxa de frames (FPS)**: medição em tempo real
- **Backend utilizado**: OpenCV backend detection
- **Configurações avançadas**: brilho, contraste, saturação, matiz, ganho, exposição
- **Formato de vídeo**: FOURCC codec information
- **Buffer size**: tamanho do buffer de frames
- **Qualidade de frame**: verificação de frames vazios/escuros
- **Timeout handling**: evita travamentos em dispositivos problemáticos
- Salva relatório em JSON

## 🎯 Casos de Uso

### 1. Verificação Rápida
```bash
# Teste básico da primeira câmera
python simple_camera_test.py
```

### 2. Diagnóstico Completo
```bash
# Execute o script completo e escolha opção 3
python camera_test.py
```

### 3. Teste de Múltiplas Câmeras
```bash
# Execute o script completo e escolha opção 2
python camera_test.py
```

### 4. Teste Específico Intel RealSense
```bash
# Execute o script completo e escolha opção 6
python camera_test.py
```

### 5. Seleção Interativa com Informações
```bash
# Execute o script completo, escolha opção 1
# Use comandos: 'info 1', 'test 2', etc.
python camera_test.py
```

## 🔍 Intel RealSense - Funcionalidades Específicas

### Detecção Automática
O script detecta automaticamente câmeras Intel RealSense usando múltiplos métodos:

**Linux:**
- Verificação via `v4l2-ctl --list-devices`
- Análise de nomes de dispositivos em `/sys/class/video4linux/`
- Detecção de IDs de vendor Intel via `lsusb`

**Todos os Sistemas:**
- Teste de capacidade para múltiplas resoluções típicas de RealSense
- Verificação de suporte a resoluções como 848x480, 1280x720, etc.

### Informações Específicas RealSense
Quando uma câmera RealSense é detectada, o script exibe:
- ✅ Identificação como "Intel RealSense"
- 📊 Propriedades técnicas avançadas
- 📏 Resoluções suportadas específicas
- 🎯 Opção de teste dedicado (Menu opção 6)

### Exemplo de Saída para RealSense
```
🎥 Câmera 0:
   📍 Tipo: Intel RealSense Depth Camera
   🔗 Caminho: /dev/video0
   📐 Resolução: 640x480
   🎬 FPS: 30.0
   ✅ Status: Funcionando
   🔍 Intel RealSense: ✅ Sim
   📊 Informações adicionais:
      • Brilho: 128.0
      • Contraste: 50.0
      • Saturação: 64.0
   📏 Resoluções suportadas: 320x240, 640x480, 848x480, 1280x720
```

## ⚠️ Solução de Problemas

### Câmera não detectada
- Verifique se a câmera está conectada
- **Linux**: Teste com `ls /dev/video*` para ver dispositivos disponíveis
- **Linux**: Use `v4l2-ctl --list-devices` para informações detalhadas
- Teste com outros aplicativos (ex: Cheese no Linux, Camera no Windows)
- Verifique permissões de acesso

### Erro de permissão (Linux)
```bash
# Adicionar usuário ao grupo video
sudo usermod -a -G video $USER

# Verificar permissões dos dispositivos
ls -la /dev/video*

# Se necessário, ajustar permissões
sudo chmod 666 /dev/video*

# Faça logout e login novamente
```

### Intel RealSense não detectada
**Linux:**
```bash
# Verificar se o dispositivo está conectado
lsusb | grep Intel

# Instalar drivers RealSense (se necessário)
sudo apt-get install librealsense2-dev

# Verificar dispositivos v4l2
v4l2-ctl --list-devices | grep -i realsense
```

**Todos os sistemas:**
- Verifique se os drivers Intel RealSense estão instalados
- Teste com o Intel RealSense Viewer oficial
- Reinicie o dispositivo USB

### Timeout ou travamento
- O script agora inclui timeouts automáticos (5 segundos)
- Dispositivos problemáticos são marcados como "Timeout"
- Use a opção de diagnóstico para identificar problemas específicos

### Erro: "OpenCV não está instalado"
```bash
pip install opencv-python
# ou
pip install opencv-contrib-python
```

### Erro: "Não foi possível abrir a câmera"
- Câmera pode estar em uso por outro aplicativo
- Feche outros programas que usam câmera
- Reinicie o sistema se necessário

### Baixa qualidade de imagem
- Verifique iluminação do ambiente
- Ajuste configurações de brilho/contraste via interface interativa
- Teste diferentes resoluções usando comandos 'info X'
- Para RealSense: verifique se está usando a resolução adequada

### Performance baixa
- Feche outros aplicativos que usam câmera
- Reduza a resolução
- **Linux**: Verifique se há conflitos com outros processos usando `/dev/video*`
- **RealSense**: Use resoluções otimizadas (848x480, 1280x720)
- Verifique recursos do sistema

### Múltiplas câmeras RealSense
- Cada RealSense pode usar múltiplos `/dev/video*` (até 6 dispositivos)
- Use a detecção automática para identificar todos os dispositivos
- O script agrupa automaticamente dispositivos da mesma câmera física
- Para teste simultâneo, use a opção 2 do menu principal

## 🔮 Integração Futura com SDK G1

Estes scripts são independentes do SDK Unitree, mas estão preparados para integração futura:

```python
# Exemplo de integração futura (quando APIs estiverem disponíveis)
from unitree_sdk2py.g1.video import VideoClient  # Hipotético

class G1CameraManager(CameraManager):
    def __init__(self):
        super().__init__()
        self.g1_client = VideoClient()  # Integração com SDK
    
    def get_g1_camera_stream(self):
        # Implementação futura para câmeras específicas do G1
        pass
```

## 📊 Informações Técnicas

### Formatos Suportados
- **Entrada**: Qualquer câmera compatível com OpenCV
- **Saída**: JPEG para imagens
- **Resolução padrão**: 640x480 (configurável)
- **Codecs**: Depende do sistema e drivers

### Compatibilidade
- **SO**: Windows, Linux, macOS
- **Python**: 3.6+
- **OpenCV**: 4.0+
- **Câmeras**: USB, integradas, IP (com configuração)

## 🤝 Contribuição

Para melhorar os scripts:
1. Adicione suporte para câmeras IP
2. Implemente gravação de vídeo
3. Adicione filtros e efeitos
4. Integre com APIs específicas do G1 quando disponíveis

## 📝 Notas

- Scripts testados com câmeras USB padrão
- Funciona independentemente do SDK Unitree
- Preparado para futuras integrações com G1
- Código comentado em português
- Tratamento robusto de erros

---

**Autor**: Script de Teste G1  
**Data**: 2024  
**Versão**: 1.0