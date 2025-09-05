# 🤖 t031a5 Middleware - Versão Alpha1

## Visão Geral

O **t031a5 Middleware** é uma solução abrangente desenvolvida em Python para gerenciamento integral de sistemas robóticos humanoides, especificamente otimizada para o modelo G1 da Unitree. Este middleware atua como o sistema nervoso central do robô, coordenando de forma inteligente todas as entradas sensoriais e saídas de controle através de uma arquitetura modular e escalável.

## 🎯 Funcionalidades Principais

### 🎤 Sistema de Entradas Multimodais
- **Processamento de áudio** em tempo real com captura contínua via microfone
- **Conversão para formatos compatíveis** (WAV/FLAC) para análise por APIs de LLM
- **Captura e tratamento de fluxo de vídeo** através de protocolos modernos (WebRTC, RTSP)
- **Agregação de dados sensoriais** multimodais com timestamp sincronizado

### 🔊 Sistema de Saídas Inteligentes
- **Geração e reprodução de resposta de áudio** com controle de latência
- **Gerenciamento avançado de sistemas de LED** com controle de padrões e cores
- **Interface de movimento de alta precisão** integrada com SDK Python nativo da Unitree

### 🌐 Painel Web de Controle Integral
- **Dashboard em tempo real** com visualização unificada do status
- **Interface gráfica intuitiva** para monitoramento e controle
- **Visualização de streaming de vídeo** ao vivo com overlay de dados
- **Sistema responsivo** para acesso fácil via mobile

## 🚀 Instalação

### Pré-requisitos
- Python 3.8 ou superior
- SDK Unitree Python instalado
- Robô Unitree G1 conectado na rede

### Instalação Rápida

```bash
# Clone o repositório
git clone https://github.com/roberto/t031a5-middleware.git
cd t031a5-middleware

# Instale as dependências
pip install -r requirements.txt

# Instale o middleware
pip install -e .

# Configure o ambiente
cp config/config.yaml.example config/config.yaml
# Edite config/config.yaml com suas configurações
```

## 🎮 Uso Rápido

### Iniciar o Middleware

```bash
# Iniciar o sistema completo
t031a5 --config config/config.yaml

# Ou iniciar apenas o dashboard
t031a5-dashboard
```

### Acesso ao Dashboard

- **Desktop**: http://localhost:8080
- **Mobile**: http://localhost:8080/mobile
- **API**: http://localhost:8080/docs


## 🔧 Configuração

O sistema é altamente configurável através do arquivo `config/config.yaml`. Principais seções:

- **Network**: Configurações de rede e conectividade
- **Audio**: Parâmetros de TTS, ASR e processamento
- **Video**: Resolução, codec e streaming
- **Motion**: Segurança e interpolação de movimentos
- **AI**: Integração com LLMs e personalidade

## 🤝 Contribuição

Contribuições são bem-vindas! Por favor:

1. Faça um fork do projeto
2. Crie uma branch para sua feature
3. Commit suas mudanças
4. Push para a branch
5. Abra um Pull Request

## 📄 Licença

Este projeto está licenciado sob a Licença MIT - veja o arquivo [LICENSE](LICENSE) para detalhes.

## 🆘 Suporte

Para suporte e documentação adicional:

- 📖 [Documentação Completa](docs/)
- 🐛 [Reportar Bugs](https://github.com/roberto/t031a5-middleware/issues)
- 💬 [Discussões](https://github.com/roberto/t031a5-middleware/discussions)

---

**Desenvolvido com ❤️ para a comunidade de robótica**