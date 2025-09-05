# Sistema de Teste de Áudio - Unitree G1

## Descrição

Este script fornece um sistema completo de teste para o sistema de áudio do robô Unitree G1. Inclui testes abrangentes para alto-falantes, microfone, controle de LED RGB, diagnósticos do sistema e muito mais.

## Características Principais

### 🔊 Testes de Alto-falante
- **Síntese de Voz (TTS)**: Teste de múltiplas frases com diferentes vozes
- **Controle de Volume**: Teste automático em diferentes níveis de volume
- **Reprodução PCM**: Suporte para arquivos WAV e geração de áudio sintético
- **Múltiplas Vozes**: Teste de diferentes vozes TTS disponíveis

### 🎤 Testes de Microfone
- **Verificação de Conectividade**: Teste de status do microfone
- **Configurações de Captura**: Validação de parâmetros de áudio

### 💡 Controle de LED RGB
- **Cores Básicas**: Teste de cores primárias e secundárias
- **Sequências de Cores**: Animações automáticas (fade, ciclo, piscar)
- **LED Personalizado**: Controle manual de cores RGB

### 🔧 Diagnósticos e Configurações
- **Diagnóstico Completo**: Teste integrado de todos os sistemas
- **Teste de Latência**: Medição de tempo de resposta do sistema
- **Verificação de APIs**: Status de todas as APIs de áudio
- **Configurações**: Volume padrão e timeout personalizáveis

### 📊 Logs e Monitoramento
- **Sistema de Logs**: Registro detalhado de todas as operações
- **Estatísticas de Erro**: Análise de performance e confiabilidade
- **Informações do Sistema**: Status completo do ambiente

### 🎪 Testes Integrados
- **Demo Completa**: Demonstração de todas as funcionalidades
- **Teste de Estresse**: Teste intensivo de estabilidade
- **Sequência de Saudação**: Apresentação interativa do sistema

## Pré-requisitos

### Software Necessário
- Python 3.7 ou superior
- SDK Unitree (`unitree_sdk2py`)
- Módulos padrão: `time`, `os`, `sys`, `logging`, `datetime`, `traceback`

### Hardware
- Robô Unitree G1 conectado à rede
- Interface de rede configurada (padrão: `enp2s0`)

## Instalação

1. **Clone ou baixe o script**:
   ```bash
   # Certifique-se de que o arquivo g1_audio_test.py está no diretório do projeto
   ```

2. **Instale o SDK do Unitree**:
   ```bash
   pip install unitree_sdk2py
   ```

3. **Configure a interface de rede**:
   - Edite a variável `network_interface` no script se necessário
   - Padrão: `"enp2s0"`

## Uso

### Execução Básica

```bash
python g1_audio_test.py
```

### Execução com Interface Personalizada

```bash
python g1_audio_test.py --interface eth0
```

### Menu Principal

Ao executar o script, você verá um menu interativo com as seguintes opções:

```
============================================================
    SISTEMA DE TESTE DE ÁUDIO - UNITREE G1
============================================================
Interface de Rede: enp2s0
Status da Conexão: ✓ Conectado
Volume Atual: 50%
============================================================

📢 TESTES DE ALTO-FALANTE:
  1. Teste de Síntese de Voz (TTS)
  2. Teste de Controle de Volume
  3. Teste de Reprodução de Áudio PCM
  4. Teste de Múltiplas Vozes

🎤 TESTES DE MICROFONE:
  5. Verificar Conectividade do Microfone
  6. Teste de Configurações de Captura

💡 CONTROLE DE LED:
  7. Teste de LED RGB
  8. Sequência de Cores
  9. LED Personalizado

🔧 DIAGNÓSTICOS:
 10. Diagnóstico Completo do Sistema
 11. Teste de Latência
 12. Verificar Status de Todas as APIs

⚙️  CONFIGURAÇÕES:
 13. Configurar Volume Padrão
 14. Configurar Timeout
 15. Logs do Sistema

🎯 TESTES INTEGRADOS:
 16. Demo Completa (TTS + LED + Volume)
 17. Teste de Stress
 18. Sequência de Saudação

📋 OUTRAS OPÇÕES:
 19. Reconectar ao Robô
 20. Exibir Informações do Sistema
 21. Estatísticas de Erro
  0. Sair
```

## Guia de Testes

### Testes Recomendados para Iniciantes

1. **Verificação Básica** (Opção 20):
   - Exibe informações do sistema e status da conexão
   - Verifica se todos os módulos estão disponíveis

2. **Teste de TTS** (Opção 1):
   - Teste básico de síntese de voz
   - Reproduz 4 frases de teste

3. **Teste de LED** (Opção 7):
   - Teste visual das cores básicas
   - Fácil de verificar funcionamento

### Testes Avançados

1. **Demo Completa** (Opção 16):
   - Demonstração integrada de todas as funcionalidades
   - Ideal para apresentações

2. **Teste de Estresse** (Opção 17):
   - Teste intensivo de estabilidade
   - Útil para validação de performance

3. **Diagnóstico Completo** (Opção 10):
   - Teste abrangente de todos os sistemas
   - Relatório detalhado de status

## Arquivos de Log

O sistema gera dois tipos de log:

### Log Principal (`g1_audio_test.log`)
- Registro de todas as operações
- Informações de debug e performance
- Rotação automática quando necessário

### Log Crítico (`g1_audio_critical.log`)
- Apenas erros críticos e falhas
- Informações detalhadas para debugging
- Inclui traceback completo

### Visualização de Logs

Use a **Opção 15** do menu para visualizar os logs mais recentes diretamente no terminal.

## Solução de Problemas

### Problemas Comuns

#### Erro de Conexão
```
❌ Não conectado ao robô. Use a opção 19 para reconectar.
```
**Solução**:
1. Verifique se o robô está ligado e conectado à rede
2. Use a Opção 19 para tentar reconectar
3. Verifique a interface de rede configurada

#### Timeout em Operações
```
⏰ Timeout em [operação] após 10s
```
**Solução**:
1. Use a Opção 14 para aumentar o timeout
2. Verifique a qualidade da conexão de rede
3. Reinicie o robô se necessário

#### Módulo não Encontrado
```
❌ unitree_sdk2py: SDK do Unitree (não disponível)
```
**Solução**:
```bash
pip install unitree_sdk2py
```

### Diagnóstico Avançado

1. **Verificar Estatísticas** (Opção 21):
   - Analise a taxa de erro do sistema
   - Identifique padrões de falha

2. **Logs Detalhados** (Opção 15):
   - Examine os logs para erros específicos
   - Procure por padrões de timeout ou falha

3. **Informações do Sistema** (Opção 20):
   - Verifique status de todos os componentes
   - Confirme configurações atuais

## Configurações Avançadas

### Personalização de Interface de Rede

Edite o arquivo `g1_audio_test.py` e modifique:

```python
network_interface = "sua_interface_aqui"  # ex: "eth0", "wlan0"
```

### Ajuste de Timeout Padrão

```python
default_timeout = 15  # segundos
```

### Configuração de Volume Inicial

```python
current_volume = 50  # 0-100%
```

## Estrutura do Código

### Classe Principal: `G1AudioTester`

#### Métodos de Inicialização
- `__init__()`: Configuração inicial
- `connect_to_robot()`: Estabelece conexão
- `display_menu()`: Exibe menu principal

#### Métodos de Teste
- `test_tts()`: Teste de síntese de voz
- `test_volume_control()`: Teste de volume
- `test_pcm_playback()`: Teste de reprodução PCM
- `test_multiple_voices()`: Teste de múltiplas vozes
- `test_microphone_connectivity()`: Teste de microfone
- `test_led_rgb()`: Teste de LED RGB

#### Métodos de Diagnóstico
- `run_audio_diagnostics()`: Diagnóstico completo
- `test_latency()`: Teste de latência
- `check_all_apis()`: Verificação de APIs

#### Métodos Utilitários
- `safe_execute()`: Execução segura com tratamento de erro
- `get_error_statistics()`: Estatísticas de performance
- `cleanup()`: Limpeza de recursos

## Contribuição

Para contribuir com melhorias:

1. Teste o script em diferentes cenários
2. Reporte bugs através dos logs gerados
3. Sugira novas funcionalidades
4. Documente casos de uso específicos

## Licença

Este script é fornecido como exemplo educacional para uso com o SDK do Unitree G1.

## Suporte

Para suporte técnico:

1. Consulte os logs gerados pelo sistema
2. Use as opções de diagnóstico integradas
3. Verifique a documentação oficial do Unitree SDK
4. Consulte a comunidade de desenvolvedores Unitree

---

**Versão**: 1.0  
**Última Atualização**: Janeiro 2025  
**Compatibilidade**: Unitree G1 com SDK v2+