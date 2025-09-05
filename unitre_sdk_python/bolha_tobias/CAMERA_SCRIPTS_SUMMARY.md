# Resumo dos Scripts de Teste de Câmera - Robô G1

## 📋 Scripts Criados

### 1. `simple_camera_test.py` ⭐ **RECOMENDADO PARA INÍCIO**
**Uso**: Teste rápido e simples
```bash
python simple_camera_test.py
```

**Funcionalidades**:
- ✅ **Detecção automática multiplataforma** (Linux: /dev/video*, Windows/Mac: IDs 0-9)
- ✅ **Identificação Intel RealSense** automática
- ✅ **Tratamento robusto de erros** com timeouts
- ✅ Preview em tempo real
- ✅ Salvamento de imagens (tecla 's')
- ✅ Interface simplificada
- ✅ Controles: 'q' para sair, 's' para salvar

---

### 2. `camera_test.py` 🔧 **COMPLETO E AVANÇADO**
**Uso**: Interface completa com menu
```bash
python camera_test.py
```

**Funcionalidades**:
- ✅ **Menu interativo com 6 opções** (incluindo teste RealSense)
- ✅ **Seleção interativa de câmeras** com comandos 'info X' e 'test X'
- ✅ **Detecção automática Linux** (/dev/video0-11) e **identificação RealSense**
- ✅ Teste individual de câmeras com propriedades técnicas
- ✅ Teste simultâneo de múltiplas câmeras
- ✅ **Diagnósticos avançados** com timeout handling
- ✅ **Teste específico Intel RealSense** (opção 6)
- ✅ Listagem detalhada de câmeras disponíveis
- ✅ Salvamento automático de capturas

---

### 3. `demo_camera_usage.py` 🎬 **DEMONSTRAÇÃO**
**Uso**: Demonstração automatizada
```bash
python demo_camera_usage.py
```

**Funcionalidades**:
- ✅ **Demonstração completa automatizada** com detecção Linux
- ✅ **Detecção e identificação RealSense** automática
- ✅ **Detecção robusta** com tratamento de timeouts
- ✅ Detecção e teste de todas as câmeras
- ✅ Captura automática de imagens
- ✅ Teste de performance (FPS)
- ✅ Geração de relatórios
- ✅ Exemplos de uso

---

### 4. `decode_base64_frame.py` 🔓 **DECODIFICADOR**
**Uso**: Decodificação de frames base64
```bash
python decode_base64_frame.py
```

**Funcionalidades**:
- ✅ Decodificação de arquivos base64 para imagens
- ✅ Conversão de frames salvos em formato .txt
- ✅ Recuperação de imagens originais
- ✅ Validação de integridade dos dados

---

## 🚀 Como Começar

### Passo 1: Verificar Instalação
```bash
# O OpenCV já foi instalado automaticamente
pip list | grep opencv
```

### Passo 2: Teste Rápido
```bash
python simple_camera_test.py
```

### Passo 3: Explorar Funcionalidades
```bash
python camera_test.py
```

### Passo 4: Ver Demonstração
```bash
python demo_camera_usage.py
```

---

## 📊 Resultados dos Testes

### ✅ Status: **TODOS OS SCRIPTS FUNCIONANDO**

### 🎯 Câmeras Detectadas: **4 câmeras**
- **Câmera 0**: 640x480 @ 30 FPS (MSMF) - ✅ **PRINCIPAL**
- **Câmera 1**: 640x480 @ 29.97 FPS (MSMF) - ✅ **SECUNDÁRIA**
- **Câmera 2**: 640x480 (DSHOW) - ⚠️ **LIMITADA**
- **Câmera 3**: 640x480 (DSHOW) - ⚠️ **LIMITADA**

### 📁 Arquivos Gerados
- `camera_captures/` - Diretório para capturas do script completo
- `captures/` - Diretório para capturas do script simples
- `diagnostics_*.json` - Relatórios de diagnóstico
- `demo_capture_camera_*.jpg` - Imagens de demonstração
- `*_frame_base64_*.txt` - Frames salvos em formato base64
- `*_decoded.jpg` - Imagens decodificadas do base64

---

## 🎮 Controles dos Scripts

### Script Simples (`simple_camera_test.py`)
- **'q'** ou **ESC**: Sair
- **'s'**: Salvar imagem atual
- **'b'**: Salvar frame atual em formato base64 (.txt)

### Script Completo (`camera_test.py`)
- **Menu numérico**: Escolher opção (1-5)
- **Durante teste**: 'q' para parar, 's' para salvar
- **ESC**: Sair do teste atual

---

## 🔧 Características Técnicas

### Detecção Automática
**Linux:**
- ✅ Escaneia dispositivos `/dev/video0` até `/dev/video11`
- ✅ **Identificação automática Intel RealSense** via múltiplos métodos
- ✅ Usa `v4l2-ctl` para informações detalhadas
- ✅ Verifica IDs de vendor Intel via `lsusb`

**Windows/Mac:**
- ✅ Escaneia IDs de câmera 0-9
- ✅ **Detecta RealSense** por capacidade de múltiplas resoluções
- ✅ Verifica funcionalidade de cada câmera
- ✅ Lista apenas câmeras operacionais

**Todos os sistemas:**
- ✅ **Tratamento robusto de erros** com timeouts (5s)
- ✅ **Verificação de qualidade** de frames (vazios/escuros)
- ✅ **Relatórios detalhados** de dispositivos com falha

### Configurações Padrão
- **Resolução**: 640x480 (configurável)
- **Formato**: JPEG para salvamento
- **Backend**: MSMF/DSHOW (automático)

### Diagnósticos Inclusos
- 📐 **Múltiplas resoluções** testadas automaticamente
- 🎯 **Taxa de frames (FPS)** medição em tempo real
- 🔧 **Backend utilizado** (MSMF/DSHOW/V4L2)
- 🌟 **Propriedades avançadas**: brilho, contraste, saturação, matiz, ganho, exposição
- 🎬 **Formato de vídeo**: informações FOURCC codec
- 📏 **Buffer size**: tamanho do buffer de frames
- 🔍 **Intel RealSense**: identificação e propriedades específicas
- ⏱️ **Timeout handling**: evita travamentos
- 📊 **Relatórios detalhados** em JSON

---

## 💡 Dicas de Uso

### Para Teste Rápido
```bash
# Use o script simples
python simple_camera_test.py
```

### Para Diagnóstico Completo
```bash
# Use o script completo, opção 3
python camera_test.py
# Escolha: 3 (Executar diagnósticos)
```

### Para Múltiplas Câmeras
```bash
# Use o script completo, opção 2
python camera_test.py
# Escolha: 2 (Testar múltiplas câmeras)
```

### Para Intel RealSense Específico
```bash
# Use o script completo, opção 6
python camera_test.py
# Escolha: 6 (Testar Intel RealSense)
```

### Para Seleção Interativa
```bash
# Use o script completo, opção 1
python camera_test.py
# Escolha: 1 (Testar câmera individual)
# Use comandos: 'info 1', 'test 2', etc.
```

---

## 🔍 Intel RealSense - Funcionalidades Específicas

### Detecção Automática RealSense
**Linux:**
- 🔍 Verificação via `v4l2-ctl --list-devices`
- 📁 Análise de nomes em `/sys/class/video4linux/`
- 🔌 Detecção de IDs Intel via `lsusb`

**Todos os sistemas:**
- 📏 Teste de resoluções típicas RealSense (848x480, 1280x720)
- 🎯 Verificação de capacidade multi-resolução

### Informações Específicas
- ✅ Identificação como "Intel RealSense Depth Camera"
- 📊 Propriedades técnicas avançadas
- 📏 Lista de resoluções suportadas
- 🎯 Opção de teste dedicado (Menu opção 6)
- 🔗 Caminho do dispositivo (/dev/video*)

### Exemplo de Detecção RealSense
```
🎥 Câmera 0:
   📍 Tipo: Intel RealSense Depth Camera
   🔗 Caminho: /dev/video0
   📐 Resolução: 640x480
   🎬 FPS: 30.0
   ✅ Status: Funcionando
   🔍 Intel RealSense: ✅ Sim
```

---

## 🚨 Solução de Problemas

### ❌ "Nenhuma câmera encontrada"
**Linux:**
```bash
# Verificar dispositivos disponíveis
ls /dev/video*

# Informações detalhadas
v4l2-ctl --list-devices

# Verificar permissões
ls -la /dev/video*
```

**Todos os sistemas:**
1. Verifique conexões USB
2. Teste com aplicativo nativo (Cheese/Camera)
3. Feche outros programas que usam câmera
4. Reinicie o sistema se necessário

### 🔍 Intel RealSense não detectada
**Linux:**
```bash
# Verificar dispositivo USB
lsusb | grep Intel

# Instalar drivers (se necessário)
sudo apt-get install librealsense2-dev

# Verificar v4l2
v4l2-ctl --list-devices | grep -i realsense
```

**Todos os sistemas:**
- Instale Intel RealSense SDK
- Teste com Intel RealSense Viewer
- Reinicie dispositivo USB

### ⏱️ Timeout ou travamento
- ✅ Scripts incluem timeouts automáticos (5s)
- ✅ Dispositivos problemáticos marcados como "Timeout"
- ✅ Use diagnósticos para identificar problemas

### ❌ "Erro na captura do frame"
1. Câmera pode estar ocupada
2. Drivers podem estar desatualizados
3. **Linux**: Verifique permissões `/dev/video*`
4. Tente câmera diferente

### 🔐 Erro de permissão (Linux)
```bash
# Adicionar usuário ao grupo video
sudo usermod -a -G video $USER

# Ajustar permissões se necessário
sudo chmod 666 /dev/video*

# Logout e login novamente
```

### ⚠️ Performance baixa
1. Feche outros aplicativos
2. **Linux**: Verifique conflitos em `/dev/video*`
3. **RealSense**: Use resoluções otimizadas
4. Use apenas uma câmera por vez
5. Reduza resolução se necessário

---

## 🔮 Integração Futura com G1

Os scripts estão preparados para integração futura com APIs específicas do G1:

```python
# Exemplo de integração futura
from unitree_sdk2py.g1.video import VideoClient  # Quando disponível

class G1CameraManager(CameraManager):
    def __init__(self):
        super().__init__()
        self.g1_client = VideoClient()  # Integração SDK
```

---

## 📚 Documentação Adicional

- **`README_CAMERA_TEST.md`**: Documentação completa
- **Diagnósticos JSON**: Relatórios técnicos detalhados
- **Código comentado**: Todos os scripts em português

---

## ✅ Conclusão

### Status Final: **SUCESSO COMPLETO** 🎉

- ✅ **4 câmeras detectadas e funcionais**
- ✅ **3 scripts criados e testados**
- ✅ **OpenCV instalado e configurado**
- ✅ **Documentação completa gerada**
- ✅ **Arquivos de exemplo criados**
- ✅ **Relatórios de diagnóstico funcionais**

### Próximos Passos Recomendados:
1. **Teste básico**: `python simple_camera_test.py`
2. **Exploração**: `python camera_test.py`
3. **Integração**: Adaptar para necessidades específicas do G1

---

**Criado em**: 28/08/2024  
**Status**: Pronto para uso  
**Compatibilidade**: Windows, OpenCV 4.12.0  
**Câmeras testadas**: 4 dispositivos detectados