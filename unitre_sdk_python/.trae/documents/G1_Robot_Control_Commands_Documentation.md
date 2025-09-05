# Documentação de Comandos para Controle do Robô G1 da Unitree

## 1. Visão Geral

Este documento apresenta uma documentação completa dos comandos de alto nível (high-level) e baixo nível (low-level) para controle do robô humanoide G1 da Unitree usando o SDK Python `unitree_sdk2_python`.

## 2. Configuração de Rede

### 2.1 Inicialização

Todos os exemplos requerem a configuração da interface de rede:

```python
from unitree_sdk2py.core.channel import ChannelFactoryInitialize

# Inicializar com interface de rede (substitua 'enp2s0' pela sua interface)
ChannelFactoryInitialize(0, "enp2s0")
```

### 2.2 Uso

```bash
python3 exemplo.py enp2s0  # Substitua 'enp2s0' pela sua interface de rede
```

## 3. Comandos de Alto Nível (High-Level)

### 3.1 Controle de Locomoção (LocoClient)

#### 3.1.1 Inicialização

```python
from unitree_sdk2py.g1.loco.g1_loco_client import LocoClient

loco_client = LocoClient()
loco_client.SetTimeout(10.0)
loco_client.Init()
```

#### 3.1.2 Comandos Básicos de Postura

| Comando        | Função        | Descrição                              |
| -------------- | ------------- | -------------------------------------- |
| `Damp()`       | Amortecimento | Coloca o robô em modo de amortecimento |
| `Start()`      | Iniciar       | Inicia o sistema de controle           |
| `ZeroTorque()` | Torque Zero   | Remove todo torque dos motores         |
| `Sit()`        | Sentar        | Faz o robô sentar                      |

#### 3.1.3 Comandos de Transição de Postura

| Comando           | Função                   | Descrição                                        |
| ----------------- | ------------------------ | ------------------------------------------------ |
| `Squat2StandUp()` | Agachar para Ficar em Pé | Transição de agachado para em pé                 |
| `StandUp2Squat()` | Ficar em Pé para Agachar | Transição de em pé para agachado                 |
| `Lie2StandUp()`   | Deitar para Ficar em Pé  | Levanta do chão (requer superfície dura e plana) |

#### 3.1.4 Controle de Altura

| Comando                  | Função               | Parâmetros      | Descrição                       |
| ------------------------ | -------------------- | --------------- | ------------------------------- |
| `HighStand()`            | Postura Alta         | -               | Posição em pé com altura máxima |
| `LowStand()`             | Postura Baixa        | -               | Posição em pé com altura mínima |
| `SetStandHeight(height)` | Altura Personalizada | `height: float` | Define altura específica        |

#### 3.1.5 Controle de Movimento

| Comando                    | Função             | Parâmetros                                                            | Descrição            |
| -------------------------- | ------------------ | --------------------------------------------------------------------- | -------------------- |
| `Move(vx, vy, vyaw)`       | Movimento          | `vx: float` (frente/trás)`vy: float` (lateral)`vyaw: float` (rotação) | Movimento direcional |
| `Move(vx, vy, vyaw, True)` | Movimento Contínuo | + `continous_move: bool`                                              | Movimento contínuo   |
| `StopMove()`               | Parar              | -                                                                     | Para o movimento     |

**Exemplo de Movimento:**

```python
# Mover para frente
loco_client.Move(0.3, 0, 0)

# Mover lateralmente
loco_client.Move(0, 0.3, 0)

# Rotacionar
loco_client.Move(0, 0, 0.3)

# Parar movimento
loco_client.StopMove()
```

#### 3.1.6 Gestos Sociais

| Comando          | Função         | Parâmetros        | Descrição                          |
| ---------------- | -------------- | ----------------- | ---------------------------------- |
| `WaveHand()`     | Acenar         | -                 | Acena sem girar                    |
| `WaveHand(True)` | Acenar e Girar | `turn_flag: bool` | Acena e gira                       |
| `ShakeHand()`    | Apertar Mãos   | -                 | Gesto de apertar mãos (2 estágios) |

**Exemplo de Gestos:**

```python
# Acenar simples
loco_client.WaveHand()

# Acenar com giro
loco_client.WaveHand(True)

# Apertar mãos (executar duas vezes para sequência completa)
loco_client.ShakeHand()
time.sleep(3)
loco_client.ShakeHand()
```

### 3.2 Controle de Braços (G1ArmActionClient)

#### 3.2.1 Inicialização

```python
from unitree_sdk2py.g1.arm.g1_arm_action_client import G1ArmActionClient, action_map

arm_client = G1ArmActionClient()
arm_client.SetTimeout(10.0)
arm_client.Init()
```

#### 3.2.2 Ações Disponíveis

| ID | Nome da Ação  | Código | Descrição             |
| -- | ------------- | ------ | --------------------- |
| 0  | release arm   | 99     | Liberar braços        |
| 1  | shake hand    | 27     | Apertar mãos          |
| 2  | high five     | 18     | Cumprimento           |
| 3  | hug           | 19     | Abraço                |
| 4  | high wave     | 26     | Acenar alto           |
| 5  | clap          | 17     | Bater palmas          |
| 6  | face wave     | 25     | Acenar no rosto       |
| 7  | left kiss     | 12     | Beijo esquerdo        |
| 8  | heart         | 20     | Coração               |
| 9  | right heart   | 21     | Coração direito       |
| 10 | hands up      | 15     | Mãos para cima        |
| 11 | x-ray         | 24     | Posição raio-X        |
| 12 | right hand up | 23     | Mão direita para cima |
| 13 | reject        | 22     | Rejeição              |
| 14 | right kiss    | 13     | Beijo direito         |
| 15 | two-hand kiss | 11     | Beijo com duas mãos   |

#### 3.2.3 Execução de Ações

```python
# Executar ação por nome
arm_client.ExecuteAction(action_map.get("high five"))
time.sleep(2)
arm_client.ExecuteAction(action_map.get("release arm"))

# Executar ação por ID
arm_client.ExecuteAction(18)  # high five
time.sleep(2)
arm_client.ExecuteAction(99)  # release arm
```

### 3.3 Sistema de Áudio (AudioClient)

#### 3.3.1 Inicialização

```python
from unitree_sdk2py.g1.audio.g1_audio_client import AudioClient

audio_client = AudioClient()
audio_client.SetTimeout(10.0)
audio_client.Init()
```

#### 3.3.2 Comandos de Áudio

| Comando                         | Função            | Parâmetros                 | Descrição            |
| ------------------------------- | ----------------- | -------------------------- | -------------------- |
| `TtsMaker(text, speaker_id)`    | Text-to-Speech    | `text: strspeaker_id: int` | Síntese de voz       |
| `GetVolume()`                   | Obter Volume      | -                          | Retorna volume atual |
| `SetVolume(volume)`             | Definir Volume    | `volume: int` (0-100)      | Define volume        |
| `LedControl(R, G, B)`           | Controle LED      | `R, G, B: int` (0-255)     | Controla LED RGB     |
| `PlayStream(app, stream, data)` | Reproduzir Stream | Parâmetros de stream       | Reproduz áudio PCM   |
| `PlayStop(app_name)`            | Parar Reprodução  | `app_name: str`            | Para reprodução      |

#### 3.3.3 Exemplo de Uso de Áudio

```python
# Verificar volume atual
code, volume_data = audio_client.GetVolume()
print(f"Volume atual: {volume_data}")

# Definir volume
audio_client.SetVolume(85)

# Text-to-Speech
audio_client.TtsMaker("Olá! Eu sou o robô G1 da Unitree.", 0)

# Controle de LED
audio_client.LedControl(255, 0, 0)    # Vermelho
time.sleep(1)
audio_client.LedControl(0, 255, 0)    # Verde
time.sleep(1)
audio_client.LedControl(0, 0, 255)    # Azul
```

## 4. Comandos de Baixo Nível (Low-Level)

### 4.1 Estruturas de Dados Principais

#### 4.1.1 LowCmd\_ (Comando de Baixo Nível)

```python
from unitree_sdk2py.idl.unitree_hg.msg.dds_ import LowCmd_

low_cmd = LowCmd_()
low_cmd.mode_pr = Mode.PR          # Modo de controle (PR ou AB)
low_cmd.mode_machine = mode        # Modo da máquina
low_cmd.motor_cmd[i].mode = 1      # 1: Habilitar, 0: Desabilitar
low_cmd.motor_cmd[i].tau = 0.0     # Torque
low_cmd.motor_cmd[i].q = 0.0       # Posição
low_cmd.motor_cmd[i].dq = 0.0      # Velocidade
low_cmd.motor_cmd[i].kp = 60.0     # Ganho proporcional
low_cmd.motor_cmd[i].kd = 1.0      # Ganho derivativo
```

#### 4.1.2 LowState\_ (Estado de Baixo Nível)

```python
from unitree_sdk2py.idl.unitree_hg.msg.dds_ import LowState_

# Estrutura do LowState_
class LowState_:
    version: array[uint32, 2]                    # Versão
    mode_pr: uint8                               # Modo PR/AB
    mode_machine: uint8                          # Modo da máquina
    tick: uint32                                 # Contador de tempo
    imu_state: IMUState_                         # Estado do IMU
    motor_state: array[MotorState_, 35]          # Estado dos motores
    wireless_remote: array[uint8, 40]            # Controle remoto
    reserve: array[uint32, 4]                    # Reservado
    crc: uint32                                  # Checksum
```

### 4.2 Índices das Juntas do G1

```python
class G1JointIndex:
    # Perna Esquerda
    LeftHipPitch = 0      # Quadril pitch esquerdo
    LeftHipRoll = 1       # Quadril roll esquerdo
    LeftHipYaw = 2        # Quadril yaw esquerdo
    LeftKnee = 3          # Joelho esquerdo
    LeftAnklePitch = 4    # Tornozelo pitch esquerdo
    LeftAnkleRoll = 5     # Tornozelo roll esquerdo
    
    # Perna Direita
    RightHipPitch = 6     # Quadril pitch direito
    RightHipRoll = 7      # Quadril roll direito
    RightHipYaw = 8       # Quadril yaw direito
    RightKnee = 9         # Joelho direito
    RightAnklePitch = 10  # Tornozelo pitch direito
    RightAnkleRoll = 11   # Tornozelo roll direito
    
    # Torso
    WaistYaw = 12         # Cintura yaw
    WaistRoll = 13        # Cintura roll
    WaistPitch = 14       # Cintura pitch
    
    # Braço Esquerdo
    LeftShoulderPitch = 15  # Ombro pitch esquerdo
    LeftShoulderRoll = 16   # Ombro roll esquerdo
    LeftShoulderYaw = 17    # Ombro yaw esquerdo
    LeftElbow = 18          # Cotovelo esquerdo
    LeftWristRoll = 19      # Punho roll esquerdo
    LeftWristPitch = 20     # Punho pitch esquerdo
    LeftWristYaw = 21       # Punho yaw esquerdo
    
    # Braço Direito
    RightShoulderPitch = 22 # Ombro pitch direito
    RightShoulderRoll = 23  # Ombro roll direito
    RightShoulderYaw = 24   # Ombro yaw direito
    RightElbow = 25         # Cotovelo direito
    RightWristRoll = 26     # Punho roll direito
    RightWristPitch = 27    # Punho pitch direito
    RightWristYaw = 28      # Punho yaw direito
    
    kNotUsedJoint = 29      # Junta não utilizada (controle especial)
```

### 4.3 Modos de Controle

```python
from unitree_sdk2py.idl.unitree_hg.msg.dds_ import LowCmd_

low_cmd = LowCmd_()
low_cmd.mode_pr = Mode.PR          # Modo de controle (PR ou AB)
low_cmd.mode_machine = mode        # Modo da máquina
low_cmd.motor_cmd[i].mode = 1      # 1: Habilitar, 0: Desabilitar
low_cmd.motor_cmd[i].tau = 0.0     # Torque
low_cmd.motor_cmd[i].q = 0.0       # Posição
low_cmd.motor_cmd[i].dq = 0.0      # Velocidade
low_cmd.motor_cmd[i].kp = 60.0     # Ganho proporcional
low_cmd.motor_cmd[i].kd = 1.0      # Ganho derivativo
```

### 4.4 Parâmetros de Controle

#### 4.4.1 Ganhos Proporcionais (Kp)

```python
Kp = [
    60, 60, 60, 100, 40, 40,      # Pernas
    60, 60, 60, 100, 40, 40,      # Pernas
    100, 100, 100,                # Torso
    60, 60, 60, 60, 40, 40, 40,   # Braço esquerdo
    60, 60, 60, 60, 40, 40, 40,   # Braço direito
]
```

#### 4.4.2 Ganhos Derivativos (Kd)

```python
Kd = [
    1, 1, 1, 2, 1, 1,             # Pernas
    1, 1, 1, 2, 1, 1,             # Pernas
    2, 2, 2,                      # Torso
    1.5, 1.5, 1.5, 1.5, 1, 1, 1, # Braço esquerdo
    1.5, 1.5, 1.5, 1.5, 1, 1, 1, # Braço direito
]
```

### 4.5 Inicialização de Baixo Nível

```python
import time
import sys
from unitree_sdk2py.core.channel import ChannelPublisher, ChannelSubscriber, ChannelFactoryInitialize
from unitree_sdk2py.idl.unitree_hg.msg.dds_ import LowCmd_, LowState_
from unitree_sdk2py.utils.crc import CRC
from unitree_sdk2py.utils.thread import RecurrentThread
from unitree_sdk2py.comm.motion_switcher.motion_switcher_client import MotionSwitcherClient

class LowLevelController:
    def __init__(self):
        self.time_ = 0.0
        self.control_dt_ = 0.002  # 2ms
        self.duration_ = 3.0      # 3s
        self.low_cmd = LowCmd_()
        self.low_state = None
        self.crc = CRC()
        
    def Init(self):
        # Inicializar Motion Switcher
        self.msc = MotionSwitcherClient()
        self.msc.SetTimeout(5.0)
        self.msc.Init()
        
        # Liberar modo atual
        status, result = self.msc.CheckMode()
        while result['name']:
            self.msc.ReleaseMode()
            status, result = self.msc.CheckMode()
            time.sleep(1)
        
        # Criar publisher e subscriber
        self.lowcmd_publisher_ = ChannelPublisher("rt/lowcmd", LowCmd_)
        self.lowcmd_publisher_.Init()
        
        self.lowstate_subscriber_ = ChannelSubscriber("rt/lowstate", LowState_)
        self.lowstate_subscriber_.Init(self.LowStateHandler, 10)
```

### 4.6 Controle de Motor Individual

```python
def ControlSingleMotor(self, joint_index, position, velocity, torque, kp, kd):
    """Controla um motor individual"""
    self.low_cmd.motor_cmd[joint_index].mode = 1      # Habilitar
    self.low_cmd.motor_cmd[joint_index].q = position   # Posição desejada
    self.low_cmd.motor_cmd[joint_index].dq = velocity  # Velocidade desejada
    self.low_cmd.motor_cmd[joint_index].tau = torque   # Torque
    self.low_cmd.motor_cmd[joint_index].kp = kp        # Ganho proporcional
    self.low_cmd.motor_cmd[joint_index].kd = kd        # Ganho derivativo

# Exemplo de uso
controller.ControlSingleMotor(
    G1JointIndex.LeftKnee,  # Joelho esquerdo
    position=0.5,           # 0.5 radianos
    velocity=0.0,           # Velocidade zero
    torque=0.0,             # Sem torque adicional
    kp=100.0,               # Ganho proporcional
    kd=2.0                  # Ganho derivativo
)
```

### 4.7 Leitura de Sensores

#### 4.7.1 Dados do IMU

```python
def ReadIMU(self):
    """Lê dados do IMU"""
    if self.low_state:
        imu = self.low_state.imu_state
        print(f"RPY: {imu.rpy}")           # Roll, Pitch, Yaw
        print(f"Quaternion: {imu.quat}")   # Quaternion
        print(f"Gyro: {imu.gyro}")         # Giroscópio
        print(f"Accel: {imu.accel}")       # Acelerômetro
```

#### 4.7.2 Estado dos Motores

```python
def ReadMotorStates(self):
    """Lê estado de todos os motores"""
    if self.low_state:
        for i in range(29):  # G1 tem 29 motores
            motor = self.low_state.motor_state[i]
            print(f"Motor {i}:")
            print(f"  Posição: {motor.q}")
            print(f"  Velocidade: {motor.dq}")
            print(f"  Torque: {motor.tau}")
            print(f"  Temperatura: {motor.temperature}")
```

### 4.8 Exemplo Completo de Baixo Nível

```python
class G1LowLevelExample:
    def __init__(self):
        self.time_ = 0.0
        self.control_dt_ = 0.002
        self.duration_ = 3.0
        self.low_cmd = LowCmd_()
        self.low_state = None
        self.mode_machine_ = 0
        self.update_mode_machine_ = False
        
    def LowCmdWrite(self):
        """Função principal de controle"""
        self.time_ += self.control_dt_
        
        if self.time_ < self.duration_:
            # Estágio 1: Posição zero
            for i in range(29):
                ratio = np.clip(self.time_ / self.duration_, 0.0, 1.0)
                self.low_cmd.mode_pr = Mode.PR
                self.low_cmd.mode_machine = self.mode_machine_
                self.low_cmd.motor_cmd[i].mode = 1
                self.low_cmd.motor_cmd[i].tau = 0.0
                self.low_cmd.motor_cmd[i].q = (1.0 - ratio) * self.low_state.motor_state[i].q
                self.low_cmd.motor_cmd[i].dq = 0.0
                self.low_cmd.motor_cmd[i].kp = Kp[i]
                self.low_cmd.motor_cmd[i].kd = Kd[i]
        
        elif self.time_ < self.duration_ * 2:
            # Estágio 2: Movimento do tornozelo em modo PR
            max_P = np.pi * 30.0 / 180.0
            max_R = np.pi * 10.0 / 180.0
            t = self.time_ - self.duration_
            
            L_P_des = max_P * np.sin(2.0 * np.pi * t)
            L_R_des = max_R * np.sin(2.0 * np.pi * t + np.pi)
            R_P_des = -max_P * np.sin(2.0 * np.pi * t)
            R_R_des = -max_R * np.sin(2.0 * np.pi * t + np.pi)
            
            self.low_cmd.mode_pr = Mode.PR
            self.low_cmd.motor_cmd[G1JointIndex.LeftAnklePitch].q = L_P_des
            self.low_cmd.motor_cmd[G1JointIndex.LeftAnkleRoll].q = L_R_des
            self.low_cmd.motor_cmd[G1JointIndex.RightAnklePitch].q = R_P_des
            self.low_cmd.motor_cmd[G1JointIndex.RightAnkleRoll].q = R_R_des
        
        else:
            # Estágio 3: Movimento do tornozelo em modo AB
            max_A = np.pi * 30.0 / 180.0
            max_B = np.pi * 10.0 / 180.0
            t = self.time_ - self.duration_ * 2
            
            L_A_des = max_A * np.sin(2.0 * np.pi * t)
            L_B_des = max_B * np.sin(2.0 * np.pi * t + np.pi)
            R_A_des = -max_A * np.sin(2.0 * np.pi * t)
            R_B_des = -max_B * np.sin(2.0 * np.pi * t + np.pi)
            
            self.low_cmd.mode_pr = Mode.AB
            self.low_cmd.motor_cmd[G1JointIndex.LeftAnkleA].q = L_A_des
            self.low_cmd.motor_cmd[G1JointIndex.LeftAnkleB].q = L_B_des
            self.low_cmd.motor_cmd[G1JointIndex.RightAnkleA].q = R_A_des
            self.low_cmd.motor_cmd[G1JointIndex.RightAnkleB].q = R_B_des
        
        # Calcular CRC e publicar
        self.low_cmd.crc = self.crc.Crc(self.low_cmd)
        self.lowcmd_publisher_.Write(self.low_cmd)
```

## 5. Considerações de Segurança

### 5.1 Precauções Gerais

* **SEMPRE** certifique-se de que não há obstáculos ao redor do robô

* Mantenha uma distância segura durante operação

* Tenha um botão de emergência acessível

* Teste comandos em ambiente controlado primeiro

### 5.2 Limitações de Movimento

* Velocidades máximas recomendadas: vx, vy ≤ 0.5 m/s, vyaw ≤ 0.5 rad/s

* Ângulos de junta dentro dos limites mecânicos

* Evite mudanças bruscas de direção

### 5.3 Monitoramento

* Monitore temperatura dos motores

* Verifique estado da bateria regularmente

* Observe dados do IMU para estabilidade

## 6. Solução de Problemas

### 6.1 Problemas Comuns

| Problema           | Causa Provável              | Solução                      |
| ------------------ | --------------------------- | ---------------------------- |
| Robô não responde  | Interface de rede incorreta | Verificar nome da interface  |
| Movimento instável | Ganhos inadequados          | Ajustar Kp e Kd              |
| Timeout de conexão | Rede desconectada           | Verificar conexão física     |
| Comando rejeitado  | Modo incorreto              | Verificar modo atual do robô |

### 6.2 Verificação de Status

```python
# Verificar modo atual
status, result = msc.CheckMode()
print(f"Modo atual: {result['name']}")

# Verificar versão da API
code, version = client.GetServerApiVersion()
print(f"Versão da API: {version}")
```

## 7. Exemplos Práticos

### 7.1 Sequência de Demonstração Completa

```python
import time
from unitree_sdk2py.core.channel import ChannelFactoryInitialize
from unitree_sdk2py.g1.loco.g1_loco_client import LocoClient
from unitree_sdk2py.g1.arm.g1_arm_action_client import G1ArmActionClient, action_map
from unitree_sdk2py.g1.audio.g1_audio_client import AudioClient

def demonstration_sequence(network_interface):
    # Inicialização
    ChannelFactoryInitialize(0, network_interface)
    
    # Clientes
    loco_client = LocoClient()
    arm_client = G1ArmActionClient()
    audio_client = AudioClient()
    
    # Configurar timeouts
    for client in [loco_client, arm_client, audio_client]:
        client.SetTimeout(10.0)
        client.Init()
    
    # Sequência de demonstração
    print("Iniciando demonstração...")
    
    # 1. Levantar
    loco_client.Squat2StandUp()
    time.sleep(3)
    
    # 2. Cumprimentar
    audio_client.TtsMaker("Olá! Eu sou o robô G1.", 0)
    arm_client.ExecuteAction(action_map.get("wave hand"))
    time.sleep(3)
    
    # 3. High five
    audio_client.TtsMaker("Vamos bater palmas!", 0)
    arm_client.ExecuteAction(action_map.get("high five"))
    time.sleep(2)
    arm_client.ExecuteAction(action_map.get("release arm"))
    
    # 4. Movimento
    audio_client.TtsMaker("Agora vou me mover.", 0)
    loco_client.Move(0.2, 0, 0)  # Frente
    time.sleep(2)
    loco_client.Move(0, 0.2, 0)  # Lateral
    time.sleep(2)
    loco_client.Move(0, 0, 0.3)  # Rotação
    time.sleep(2)
    loco_client.StopMove()
    
    # 5. LED show
    audio_client.TtsMaker("Show de luzes!", 0)
    colors = [(255,0,0), (0,255,0), (0,0,255), (255,255,0), (255,0,255)]
    for r, g, b in colors:
        audio_client.LedControl(r, g, b)
        time.sleep(0.5)
    
    # 6. Finalizar
    audio_client.TtsMaker("Demonstração concluída. Obrigado!", 0)
    loco_client.Damp()
    
if __name__ == "__main__":
    demonstration_sequence("enp2s0")  # Substitua pela sua interface
```

### 7.2 Controle Interativo

```python
def interactive_control():
    # ... inicialização ...
    
    commands = {
        '1': ('Levantar', lambda: loco_client.Squat2StandUp()),
        '2': ('Sentar', lambda: loco_client.StandUp2Squat()),
        '3': ('Acenar', lambda: loco_client.WaveHand()),
        '4': ('High Five', lambda: arm_client.ExecuteAction(action_map.get("high five"))),
        '5': ('Frente', lambda: loco_client.Move(0.3, 0, 0)),
        '6': ('Parar', lambda: loco_client.StopMove()),
        '7': ('Falar', lambda: audio_client.TtsMaker("Olá mundo!", 0)),
        '0': ('Sair', lambda: loco_client.Damp())
    }
    
    while True:
        print("\nComandos disponíveis:")
        for key, (name, _) in commands.items():
            print(f"{key}: {name}")
        
        choice = input("Escolha um comando: ")
        if choice in commands:
            name, action = commands[choice]
            print(f"Executando: {name}")
            action()
            if choice == '0':
                break
        else:
            print("Comando inválido!")
```

Esta documentação fornece uma base completa para desenvolvimento de aplicações com o robô G1 da
