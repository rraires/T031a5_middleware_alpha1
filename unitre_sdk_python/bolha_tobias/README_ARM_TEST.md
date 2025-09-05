# Scripts de Teste de Movimento do Braço - Robô G1

Este diretório contém scripts Python para testar movimentos específicos dos braços do robô Unitree G1.

## 🚀 Início Rápido

**Para usuários iniciantes:**
```bash
# Execute o script de demonstração interativo
python demo_all_scripts.py eth0
```

**Para teste rápido:**
```bash
# Execute o script simples
python simple_arm_test.py eth0
```

**Para controle avançado:**
```bash
# Execute o script de baixo nível (requer experiência)
python precise_arm_test.py eth0
```

## Scripts Disponíveis

### 1. test_arm_movements.py (Alto Nível)
**Descrição:** Script principal que executa a sequência solicitada usando ações predefinidas do SDK.

**Uso:**
```bash
python test_arm_movements.py <interface_de_rede>
```

**Características:**
- ✅ Tratamento completo de erros
- ✅ Logs detalhados
- ✅ Verificações de segurança
- ✅ Sequência automática

### 2. simple_arm_test.py (Alto Nível)
**Descrição:** Versão simplificada para testes rápidos.

**Uso:**
```bash
python simple_arm_test.py <interface_de_rede>
```

**Características:**
- ✅ Execução mais rápida
- ✅ Lista ações disponíveis
- ✅ Código mais simples

### 3. precise_arm_test.py (Baixo Nível) ⭐
**Descrição:** Controle preciso usando APIs de baixo nível para movimentos individuais dos braços.

**Uso:**
```bash
python precise_arm_test.py <interface_de_rede>
```

**Características:**
- ✅ Controle individual de cada motor
- ✅ Movimentos suaves com interpolação
- ✅ Controle preciso de posição
- ✅ Sequência automática de 8 segundos
- ✅ Ciclo de controle de 2ms
- ⚠️ Requer conhecimento dos motores

### 4. demo_all_scripts.py (Demonstração) 🎯
**Descrição:** Script interativo que permite executar todos os testes de forma organizada.

**Uso:**
```bash
python demo_all_scripts.py <interface_de_rede>
```

**Características:**
- ✅ Menu interativo
- ✅ Execução individual ou em sequência
- ✅ Avisos de segurança
- ✅ Comparação entre métodos
- ✅ Logs organizados
- ✅ Controle de timeout

### 5. integrated_arm_control.py (Integrado) 🌟
**Descrição:** Demonstra como combinar controle de alto e baixo nível em uma única aplicação.

**Uso:**
```bash
python integrated_arm_control.py <interface_de_rede>
```

**Características:**
- ✅ Combina alto e baixo nível
- ✅ Demonstração comparativa
- ✅ Fallback automático
- ✅ Controle inteligente
- ✅ Exemplo de arquitetura
- ⭐ **Recomendado para desenvolvedores**

## Sequência de Movimentos

Ambos os scripts executam a seguinte sequência:

1. **Posição inicial** - Liberar braços (posição neutra)
2. **Subir mão esquerda** - Levantar a mão esquerda
3. **Abaixar mão esquerda** - Retornar à posição neutra
4. **Subir mão direita** - Levantar a mão direita
5. **Abaixar mão direita** - Retornar à posição neutra

## Diferenças entre Controle de Alto e Baixo Nível

### Controle de Alto Nível (test_arm_movements.py, simple_arm_test.py)
- ✅ **Mais simples de usar**
- ✅ **Ações predefinidas seguras**
- ✅ **Menos risco de danos**
- ❌ **Limitado às ações disponíveis no SDK**
- ❌ **Não permite controle individual dos braços**

### Controle de Baixo Nível (precise_arm_test.py)
- ✅ **Controle total de cada motor**
- ✅ **Movimentos personalizados**
- ✅ **Controle individual dos braços**
- ✅ **Interpolação suave**
- ❌ **Mais complexo**
- ❌ **Requer conhecimento dos motores**
- ⚠️ **Maior risco se mal configurado**

## Limitações do SDK de Alto Nível

⚠️ **Importante:** O SDK Unitree G1 não possui uma ação específica para "levantar apenas a mão esquerda" nas APIs de alto nível. 

### Ações Disponíveis no SDK:

- `release arm` (ID: 99) - Libera/abaixa ambos os braços
- `right hand up` (ID: 23) - Levanta apenas a mão direita
- `hands up` (ID: 15) - Levanta ambas as mãos
- `two-hand kiss` (ID: 11)
- `left kiss` (ID: 12)
- `right kiss` (ID: 13)
- `clap` (ID: 17)
- `high five` (ID: 18)
- `hug` (ID: 19)
- `heart` (ID: 20)
- `right heart` (ID: 21)
- `reject` (ID: 22)
- `x-ray` (ID: 24)
- `face wave` (ID: 25)
- `high wave` (ID: 26)
- `shake hand` (ID: 27)

### Solução Implementada

Para simular "levantar apenas a mão esquerda", os scripts usam a ação `hands up` como melhor aproximação disponível, seguida de `release arm` para abaixar.

## Pré-requisitos

1. **SDK Instalado:**
   ```bash
   pip install unitree_sdk2py
   ```

2. **Robô G1 Conectado:**
   - Robô ligado e em modo operacional
   - Conexão de rede estabelecida
   - Interface de rede correta (eth0, wlan0, etc.)

3. **Dependências:**
   - Python 3.6+
   - cyclonedds
   - numpy

## Segurança

⚠️ **AVISOS IMPORTANTES:**

- **Sempre** certifique-se de que não há obstáculos ao redor do robô
- Mantenha distância segura durante os movimentos
- Tenha o botão de emergência à mão
- Teste primeiro em ambiente controlado
- Verifique se o robô está em superfície estável

## Solução de Problemas

### Erro de Conexão
```
Erro: Failed to initialize communication
```
**Solução:** Verifique se a interface de rede está correta e o robô está conectado.

### Erro de Timeout
```
Erro: Timeout waiting for response
```
**Solução:** 
- Verifique se o robô está ligado
- Aumente o timeout no código (padrão: 10 segundos)
- Verifique a qualidade da conexão de rede

### Erro de Permissão
```
Erro: Permission denied
```
**Solução:** Execute o script com privilégios adequados ou verifique as configurações de rede.

## Personalização

### Modificar Delays
Para alterar o tempo entre movimentos, edite as variáveis:

```python
self.movement_delay = 3.0  # Delay entre movimentos
self.action_delay = 2.0    # Delay para execução da ação
```

### Adicionar Novos Movimentos
Para adicionar novos movimentos, use as ações disponíveis no `action_map`:

```python
# Exemplo: adicionar um "high five"
arm_client.ExecuteAction(action_map["high five"])
time.sleep(2)
arm_client.ExecuteAction(action_map["release arm"])
```

## Estrutura dos Scripts

### test_arm_movements.py
- Classe `G1ArmMovementTest` para organização
- Tratamento completo de erros
- Logs detalhados
- Verificações de segurança
- Exibição de ações disponíveis

### simple_arm_test.py
- Implementação direta e simples
- Código linear fácil de entender
- Ideal para testes rápidos
- Menos verificações, mais velocidade

## Contribuição

Para melhorar os scripts:

1. Adicione novas sequências de movimento
2. Implemente controle de baixo nível para movimentos mais precisos
3. Adicione interface gráfica
4. Implemente gravação/reprodução de sequências

## Licença

Este código segue a mesma licença do SDK Unitree.