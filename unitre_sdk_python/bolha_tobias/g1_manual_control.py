#!/usr/bin/env python3
"""
Script de Controle Manual do Robô Unitree G1
Baseado no precise_arm_test.py

Controles disponíveis:
- Braços: movimentos individuais e articulações
- Pernas: movimentos e posições predefinidas
- Locomoção: frente/trás, rotação, lateral
- Interface de teclado interativa
- Funcionalidades de segurança

Autor: Sistema de Controle G1
Data: 2024
"""

import time
import sys
import threading
import math
import select
import termios
import tty
from dataclasses import dataclass
from typing import Dict, List, Optional

# Importações do SDK Unitree
from unitree_sdk2py.core.channel import ChannelPublisher, ChannelSubscriber, ChannelFactoryInitialize
from unitree_sdk2py.idl.default import unitree_hg_msg_dds__LowState_
from unitree_sdk2py.idl.default import unitree_hg_msg_dds__LowCmd_
from unitree_sdk2py.idl.unitree_hg.msg.dds_ import LowState_, LowCmd_
from unitree_sdk2py.utils.crc import CRC
from unitree_sdk2py.utils.thread import Thread
from unitree_sdk2py.g1.loco.g1_loco_client import LocoClient
from unitree_sdk2py.comm.motion_switcher.motion_switcher_client import MotionSwitcherClient

# Constantes do robô G1
G1_NUM_MOTOR = 29
Kp = 60.0
Kd = 5.0

# Índices dos motores dos braços
class ArmJoints:
    # Braço esquerdo
    LEFT_SHOULDER_PITCH = 8   # Ombro esquerdo (pitch)
    LEFT_SHOULDER_ROLL = 9    # Ombro esquerdo (roll)
    LEFT_SHOULDER_YAW = 10    # Ombro esquerdo (yaw)
    LEFT_ELBOW = 11           # Cotovelo esquerdo
    LEFT_WRIST_ROLL = 12      # Punho esquerdo (roll)
    LEFT_WRIST_PITCH = 13     # Punho esquerdo (pitch)
    LEFT_WRIST_YAW = 14       # Punho esquerdo (yaw)
    
    # Braço direito
    RIGHT_SHOULDER_PITCH = 15 # Ombro direito (pitch)
    RIGHT_SHOULDER_ROLL = 16  # Ombro direito (roll)
    RIGHT_SHOULDER_YAW = 17   # Ombro direito (yaw)
    RIGHT_ELBOW = 18          # Cotovelo direito
    RIGHT_WRIST_ROLL = 19     # Punho direito (roll)
    RIGHT_WRIST_PITCH = 20    # Punho direito (pitch)
    RIGHT_WRIST_YAW = 21      # Punho direito (yaw)

# Índices dos motores das pernas
class LegJoints:
    # Perna esquerda
    LEFT_HIP_PITCH = 0        # Quadril esquerdo (pitch)
    LEFT_HIP_ROLL = 1         # Quadril esquerdo (roll)
    LEFT_HIP_YAW = 2          # Quadril esquerdo (yaw)
    LEFT_KNEE = 3             # Joelho esquerdo
    LEFT_ANKLE_PITCH = 4      # Tornozelo esquerdo (pitch)
    LEFT_ANKLE_ROLL = 5       # Tornozelo esquerdo (roll)
    
    # Perna direita
    RIGHT_HIP_PITCH = 6       # Quadril direito (pitch)
    RIGHT_HIP_ROLL = 7        # Quadril direito (roll)
    RIGHT_HIP_YAW = 8         # Quadril direito (yaw)
    RIGHT_KNEE = 9            # Joelho direito
    RIGHT_ANKLE_PITCH = 10    # Tornozelo direito (pitch)
    RIGHT_ANKLE_ROLL = 11     # Tornozelo direito (roll)

# Índices da cintura
class WaistJoints:
    WAIST_YAW = 22            # Cintura (yaw)
    WAIST_PITCH = 23          # Cintura (pitch)
    WAIST_ROLL = 24           # Cintura (roll)

# Modos de controle
class ControlMode:
    LOW_LEVEL = "low_level"     # Controle de baixo nível
    HIGH_LEVEL = "high_level"   # Controle de alto nível
    MIXED = "mixed"             # Controle misto

# Velocidades de movimento
class Speed:
    SLOW = 0.1
    NORMAL = 0.3
    FAST = 0.5

@dataclass
class RobotState:
    """Estado atual do robô"""
    mode: str = ControlMode.LOW_LEVEL
    speed: float = Speed.NORMAL
    emergency_stop: bool = False
    last_command: str = "None"
    timestamp: float = 0.0

class KeyboardInput:
    """Classe para captura de entrada do teclado em tempo real"""
    
    def __init__(self):
        self.old_settings = None
        self.running = False
        
    def __enter__(self):
        self.old_settings = termios.tcgetattr(sys.stdin)
        tty.setraw(sys.stdin.fileno())
        self.running = True
        return self
        
    def __exit__(self, type, value, traceback):
        termios.tcsetattr(sys.stdin, termios.TCSADRAIN, self.old_settings)
        self.running = False
        
    def get_key(self, timeout=0.1):
        """Captura uma tecla com timeout"""
        if select.select([sys.stdin], [], [], timeout) == ([sys.stdin], [], []):
            return sys.stdin.read(1)
        return None

class G1ManualController:
    """Controlador manual principal do robô G1"""
    
    def __init__(self, network_interface: str):
        self.network_interface = network_interface
        self.state = RobotState()
        
        # Clientes de comunicação
        self.motion_switcher = None
        self.loco_client = None
        self.low_cmd_publisher = None
        self.low_state_subscriber = None
        self.crc = CRC()
        
        # Estado do robô
        self.current_low_state = unitree_hg_msg_dds__LowState_()
        self.target_positions = [0.0] * G1_NUM_MOTOR
        self.current_positions = [0.0] * G1_NUM_MOTOR
        
        # Controle de threads
        self.running = False
        self.control_thread = None
        
        # Posições predefinidas
        self.init_predefined_positions()
        
    def init_predefined_positions(self):
        """Inicializa posições predefinidas para braços e pernas"""
        self.arm_positions = {
            'home': {
                # Braço esquerdo
                ArmJoints.LEFT_SHOULDER_PITCH: 0.0,
                ArmJoints.LEFT_SHOULDER_ROLL: 0.0,
                ArmJoints.LEFT_SHOULDER_YAW: 0.0,
                ArmJoints.LEFT_ELBOW: 0.0,
                ArmJoints.LEFT_WRIST_ROLL: 0.0,
                ArmJoints.LEFT_WRIST_PITCH: 0.0,
                ArmJoints.LEFT_WRIST_YAW: 0.0,
                # Braço direito
                ArmJoints.RIGHT_SHOULDER_PITCH: 0.0,
                ArmJoints.RIGHT_SHOULDER_ROLL: 0.0,
                ArmJoints.RIGHT_SHOULDER_YAW: 0.0,
                ArmJoints.RIGHT_ELBOW: 0.0,
                ArmJoints.RIGHT_WRIST_ROLL: 0.0,
                ArmJoints.RIGHT_WRIST_PITCH: 0.0,
                ArmJoints.RIGHT_WRIST_YAW: 0.0,
            },
            'arms_up': {
                # Braços levantados
                ArmJoints.LEFT_SHOULDER_PITCH: -1.57,
                ArmJoints.RIGHT_SHOULDER_PITCH: -1.57,
            },
            'arms_forward': {
                # Braços para frente
                ArmJoints.LEFT_SHOULDER_PITCH: -0.785,
                ArmJoints.RIGHT_SHOULDER_PITCH: -0.785,
            }
        }
        
        self.leg_positions = {
            'home': {
                # Posição neutra das pernas
                LegJoints.LEFT_HIP_PITCH: 0.0,
                LegJoints.LEFT_HIP_ROLL: 0.0,
                LegJoints.LEFT_HIP_YAW: 0.0,
                LegJoints.LEFT_KNEE: 0.0,
                LegJoints.LEFT_ANKLE_PITCH: 0.0,
                LegJoints.LEFT_ANKLE_ROLL: 0.0,
                LegJoints.RIGHT_HIP_PITCH: 0.0,
                LegJoints.RIGHT_HIP_ROLL: 0.0,
                LegJoints.RIGHT_HIP_YAW: 0.0,
                LegJoints.RIGHT_KNEE: 0.0,
                LegJoints.RIGHT_ANKLE_PITCH: 0.0,
                LegJoints.RIGHT_ANKLE_ROLL: 0.0,
            },
            'squat': {
                # Posição agachada
                LegJoints.LEFT_HIP_PITCH: 0.785,
                LegJoints.LEFT_KNEE: 1.57,
                LegJoints.LEFT_ANKLE_PITCH: -0.785,
                LegJoints.RIGHT_HIP_PITCH: 0.785,
                LegJoints.RIGHT_KNEE: 1.57,
                LegJoints.RIGHT_ANKLE_PITCH: -0.785,
            },
            'sit': {
                # Posição sentada
                LegJoints.LEFT_HIP_PITCH: 1.57,
                LegJoints.LEFT_KNEE: 1.57,
                LegJoints.RIGHT_HIP_PITCH: 1.57,
                LegJoints.RIGHT_KNEE: 1.57,
            },
            'wide_stance': {
                # Posição com pernas abertas
                LegJoints.LEFT_HIP_ROLL: 0.3,
                LegJoints.RIGHT_HIP_ROLL: -0.3,
            }
        }
    
    def initialize_communication(self):
        """Inicializa a comunicação com o robô"""
        try:
            print("Inicializando comunicação...")
            ChannelFactoryInitialize(0, self.network_interface)
            
            # Inicializa motion switcher
            self.motion_switcher = MotionSwitcherClient()
            self.motion_switcher.SetTimeout(10.0)
            self.motion_switcher.Init()
            
            # Inicializa cliente de locomoção
            self.loco_client = LocoClient()
            self.loco_client.SetTimeout(10.0)
            self.loco_client.Init()
            
            # Inicializa publishers e subscribers
            self.low_cmd_publisher = ChannelPublisher("rt/lowcmd", LowCmd_)
            self.low_cmd_publisher.Init()
            
            self.low_state_subscriber = ChannelSubscriber("rt/lowstate", LowState_)
            self.low_state_subscriber.Init(self.low_state_callback, 10)
            
            print("✓ Comunicação inicializada com sucesso")
            return True
            
        except Exception as e:
            print(f"✗ Erro ao inicializar comunicação: {e}")
            return False
    
    def low_state_callback(self, msg: LowState_):
        """Callback para receber estado de baixo nível"""
        self.current_low_state = msg
        for i in range(G1_NUM_MOTOR):
            if i < len(msg.motor_state):
                self.current_positions[i] = msg.motor_state[i].q
    
    def switch_to_low_level(self):
        """Muda para modo de controle de baixo nível"""
        try:
            self.motion_switcher.ReleaseMode()
            time.sleep(1.0)
            self.motion_switcher.CheckMode()
            self.state.mode = ControlMode.LOW_LEVEL
            print("✓ Modo de controle: Baixo nível")
            return True
        except Exception as e:
            print(f"✗ Erro ao mudar para baixo nível: {e}")
            return False
    
    def switch_to_high_level(self):
        """Muda para modo de controle de alto nível"""
        try:
            self.motion_switcher.RequestMode()
            time.sleep(1.0)
            self.state.mode = ControlMode.HIGH_LEVEL
            print("✓ Modo de controle: Alto nível")
            return True
        except Exception as e:
            print(f"✗ Erro ao mudar para alto nível: {e}")
            return False
    
    def send_low_level_command(self, joint_positions: Dict[int, float]):
        """Envia comando de baixo nível para articulações específicas"""
        if self.state.emergency_stop:
            return
            
        try:
            cmd = unitree_hg_msg_dds__LowCmd_()
            
            # Configura comando para todas as articulações
            for i in range(G1_NUM_MOTOR):
                cmd.motor_cmd[i].mode = 1  # Modo de posição
                cmd.motor_cmd[i].q = self.target_positions[i]
                cmd.motor_cmd[i].dq = 0.0
                cmd.motor_cmd[i].kp = Kp
                cmd.motor_cmd[i].kd = Kd
                cmd.motor_cmd[i].tau = 0.0
            
            # Aplica posições específicas
            for joint_id, position in joint_positions.items():
                if 0 <= joint_id < G1_NUM_MOTOR:
                    cmd.motor_cmd[joint_id].q = position
                    self.target_positions[joint_id] = position
            
            # Calcula CRC e publica
            cmd.crc = self.crc.Crc(cmd)
            self.low_cmd_publisher.Write(cmd)
            
        except Exception as e:
            print(f"✗ Erro ao enviar comando de baixo nível: {e}")
    
    def move_arm_joint(self, joint_id: int, delta: float, joint_name: str = ""):
        """Move uma articulação específica do braço"""
        if self.state.mode != ControlMode.LOW_LEVEL:
            print("⚠ Mudando para modo de baixo nível...")
            self.switch_to_low_level()
        
        current_pos = self.target_positions[joint_id]
        new_pos = current_pos + delta * self.state.speed
        
        # Limites de segurança específicos por articulação
        joint_limits = self.get_joint_limits(joint_id)
        new_pos = max(joint_limits[0], min(joint_limits[1], new_pos))
        
        self.send_low_level_command({joint_id: new_pos})
        joint_display = joint_name if joint_name else f"Articulação {joint_id}"
        print(f"{joint_display}: {current_pos:.3f} → {new_pos:.3f}")
    
    def get_joint_limits(self, joint_id: int):
        """Retorna limites de segurança para cada articulação"""
        # Limites específicos para cada tipo de articulação
        if joint_id in [ArmJoints.LEFT_SHOULDER_PITCH, ArmJoints.RIGHT_SHOULDER_PITCH]:
            return [-3.14, 1.57]  # Ombro pitch: -180° a 90°
        elif joint_id in [ArmJoints.LEFT_SHOULDER_ROLL, ArmJoints.RIGHT_SHOULDER_ROLL]:
            return [-1.57, 1.57]  # Ombro roll: -90° a 90°
        elif joint_id in [ArmJoints.LEFT_ELBOW, ArmJoints.RIGHT_ELBOW]:
            return [-2.62, 0.0]   # Cotovelo: -150° a 0°
        elif joint_id in [ArmJoints.LEFT_WRIST_PITCH, ArmJoints.RIGHT_WRIST_PITCH]:
            return [-1.57, 1.57]  # Punho pitch: -90° a 90°
        else:
            return [-3.14, 3.14]  # Limite padrão
    
    def move_arm_smooth(self, joint_positions: Dict[int, float], duration: float = 2.0):
        """Move braços suavemente para posições específicas"""
        if self.state.mode != ControlMode.LOW_LEVEL:
            self.switch_to_low_level()
        
        # Calcula interpolação suave
        start_positions = {joint_id: self.target_positions[joint_id] for joint_id in joint_positions}
        steps = int(duration * 50)  # 50 Hz
        
        for step in range(steps + 1):
            if self.state.emergency_stop:
                break
                
            t = step / steps
            # Interpolação suave (ease-in-out)
            smooth_t = 3 * t * t - 2 * t * t * t
            
            current_cmd = {}
            for joint_id, target_pos in joint_positions.items():
                start_pos = start_positions[joint_id]
                current_pos = start_pos + (target_pos - start_pos) * smooth_t
                current_cmd[joint_id] = current_pos
            
            self.send_low_level_command(current_cmd)
            time.sleep(0.02)  # 50 Hz
    
    def control_individual_arm(self, arm_side: str, joint_type: str, delta: float):
        """Controla articulações individuais dos braços"""
        joint_map = {
            'left': {
                'shoulder_pitch': (ArmJoints.LEFT_SHOULDER_PITCH, "Ombro Esq. Pitch"),
                'shoulder_roll': (ArmJoints.LEFT_SHOULDER_ROLL, "Ombro Esq. Roll"),
                'shoulder_yaw': (ArmJoints.LEFT_SHOULDER_YAW, "Ombro Esq. Yaw"),
                'elbow': (ArmJoints.LEFT_ELBOW, "Cotovelo Esq."),
                'wrist_pitch': (ArmJoints.LEFT_WRIST_PITCH, "Punho Esq. Pitch"),
                'wrist_roll': (ArmJoints.LEFT_WRIST_ROLL, "Punho Esq. Roll"),
                'wrist_yaw': (ArmJoints.LEFT_WRIST_YAW, "Punho Esq. Yaw"),
            },
            'right': {
                'shoulder_pitch': (ArmJoints.RIGHT_SHOULDER_PITCH, "Ombro Dir. Pitch"),
                'shoulder_roll': (ArmJoints.RIGHT_SHOULDER_ROLL, "Ombro Dir. Roll"),
                'shoulder_yaw': (ArmJoints.RIGHT_SHOULDER_YAW, "Ombro Dir. Yaw"),
                'elbow': (ArmJoints.RIGHT_ELBOW, "Cotovelo Dir."),
                'wrist_pitch': (ArmJoints.RIGHT_WRIST_PITCH, "Punho Dir. Pitch"),
                'wrist_roll': (ArmJoints.RIGHT_WRIST_ROLL, "Punho Dir. Roll"),
                'wrist_yaw': (ArmJoints.RIGHT_WRIST_YAW, "Punho Dir. Yaw"),
            }
        }
        
        if arm_side in joint_map and joint_type in joint_map[arm_side]:
            joint_id, joint_name = joint_map[arm_side][joint_type]
            self.move_arm_joint(joint_id, delta, joint_name)
    
    def move_leg_joint(self, joint_id: int, delta: float, joint_name: str = ""):
        """Move uma articulação específica da perna"""
        if self.state.mode != ControlMode.LOW_LEVEL:
            print("⚠ Mudando para modo de baixo nível...")
            self.switch_to_low_level()
        
        current_pos = self.target_positions[joint_id]
        new_pos = current_pos + delta * self.state.speed
        
        # Limites de segurança específicos para pernas
        joint_limits = self.get_leg_joint_limits(joint_id)
        new_pos = max(joint_limits[0], min(joint_limits[1], new_pos))
        
        self.send_low_level_command({joint_id: new_pos})
        joint_display = joint_name if joint_name else f"Articulação {joint_id}"
        print(f"{joint_display}: {current_pos:.3f} → {new_pos:.3f}")
    
    def get_leg_joint_limits(self, joint_id: int):
        """Retorna limites de segurança para articulações das pernas"""
        if joint_id in [LegJoints.LEFT_HIP_PITCH, LegJoints.RIGHT_HIP_PITCH]:
            return [-0.785, 2.356]  # Quadril pitch: -45° a 135°
        elif joint_id in [LegJoints.LEFT_HIP_ROLL, LegJoints.RIGHT_HIP_ROLL]:
            return [-0.785, 0.785]  # Quadril roll: -45° a 45°
        elif joint_id in [LegJoints.LEFT_KNEE, LegJoints.RIGHT_KNEE]:
            return [0.0, 2.356]     # Joelho: 0° a 135°
        elif joint_id in [LegJoints.LEFT_ANKLE_PITCH, LegJoints.RIGHT_ANKLE_PITCH]:
            return [-1.047, 1.047]  # Tornozelo pitch: -60° a 60°
        elif joint_id in [LegJoints.LEFT_ANKLE_ROLL, LegJoints.RIGHT_ANKLE_ROLL]:
            return [-0.524, 0.524]  # Tornozelo roll: -30° a 30°
        else:
            return [-1.57, 1.57]    # Limite padrão
    
    def control_individual_leg(self, leg_side: str, joint_type: str, delta: float):
        """Controla articulações individuais das pernas"""
        joint_map = {
            'left': {
                'hip_pitch': (LegJoints.LEFT_HIP_PITCH, "Quadril Esq. Pitch"),
                'hip_roll': (LegJoints.LEFT_HIP_ROLL, "Quadril Esq. Roll"),
                'hip_yaw': (LegJoints.LEFT_HIP_YAW, "Quadril Esq. Yaw"),
                'knee': (LegJoints.LEFT_KNEE, "Joelho Esq."),
                'ankle_pitch': (LegJoints.LEFT_ANKLE_PITCH, "Tornozelo Esq. Pitch"),
                'ankle_roll': (LegJoints.LEFT_ANKLE_ROLL, "Tornozelo Esq. Roll"),
            },
            'right': {
                'hip_pitch': (LegJoints.RIGHT_HIP_PITCH, "Quadril Dir. Pitch"),
                'hip_roll': (LegJoints.RIGHT_HIP_ROLL, "Quadril Dir. Roll"),
                'hip_yaw': (LegJoints.RIGHT_HIP_YAW, "Quadril Dir. Yaw"),
                'knee': (LegJoints.RIGHT_KNEE, "Joelho Dir."),
                'ankle_pitch': (LegJoints.RIGHT_ANKLE_PITCH, "Tornozelo Dir. Pitch"),
                'ankle_roll': (LegJoints.RIGHT_ANKLE_ROLL, "Tornozelo Dir. Roll"),
            }
        }
        
        if leg_side in joint_map and joint_type in joint_map[leg_side]:
            joint_id, joint_name = joint_map[leg_side][joint_type]
            self.move_leg_joint(joint_id, delta, joint_name)
    
    def set_leg_position(self, position_name: str):
        """Define posição predefinida das pernas"""
        if position_name not in self.leg_positions:
            print(f"✗ Posição '{position_name}' não encontrada")
            return
        
        if self.state.mode != ControlMode.LOW_LEVEL:
            self.switch_to_low_level()
        
        positions = self.leg_positions[position_name].copy()
        # Mescla com posições atuais
        for joint_id in range(G1_NUM_MOTOR):
            if joint_id not in positions:
                positions[joint_id] = self.target_positions[joint_id]
        
        # Movimento suave para posições das pernas
        self.move_arm_smooth(positions, duration=3.0)
        print(f"✓ Posição das pernas: {position_name}")
    
    def perform_leg_exercise(self, exercise_type: str):
        """Executa exercícios específicos com as pernas"""
        if self.state.mode != ControlMode.HIGH_LEVEL:
            self.switch_to_high_level()
        
        try:
            if exercise_type == "squat":
                print("🏋️ Executando agachamento...")
                self.loco_client.StandUp2Squat()
                time.sleep(3)
                self.loco_client.Squat2StandUp()
            elif exercise_type == "sit":
                print("🪑 Sentando...")
                self.loco_client.Sit()
            elif exercise_type == "stand":
                print("🧍 Levantando...")
                self.loco_client.Squat2StandUp()
            else:
                print(f"✗ Exercício '{exercise_type}' não reconhecido")
                
        except Exception as e:
            print(f"✗ Erro no exercício: {e}")
    
    def move_forward(self, distance: float = 0.5):
        """Move o robô para frente"""
        if self.state.mode != ControlMode.HIGH_LEVEL:
            self.switch_to_high_level()
        
        try:
            velocity = self.state.speed * 0.5  # Velocidade baseada no estado
            print(f"🚶 Movendo para frente (vel: {velocity:.2f})...")
            self.loco_client.Move(vx=velocity, vy=0.0, vyaw=0.0, continous_move=False)
        except Exception as e:
            print(f"✗ Erro no movimento: {e}")
    
    def move_backward(self, distance: float = 0.5):
        """Move o robô para trás"""
        if self.state.mode != ControlMode.HIGH_LEVEL:
            self.switch_to_high_level()
        
        try:
            velocity = -self.state.speed * 0.5
            print(f"🚶 Movendo para trás (vel: {velocity:.2f})...")
            self.loco_client.Move(vx=velocity, vy=0.0, vyaw=0.0, continous_move=False)
        except Exception as e:
            print(f"✗ Erro no movimento: {e}")
    
    def move_left(self):
        """Move o robô para a esquerda"""
        if self.state.mode != ControlMode.HIGH_LEVEL:
            self.switch_to_high_level()
        
        try:
            velocity = self.state.speed * 0.3
            print(f"🚶 Movendo para esquerda (vel: {velocity:.2f})...")
            self.loco_client.Move(vx=0.0, vy=velocity, vyaw=0.0, continous_move=False)
        except Exception as e:
            print(f"✗ Erro no movimento: {e}")
    
    def move_right(self):
        """Move o robô para a direita"""
        if self.state.mode != ControlMode.HIGH_LEVEL:
            self.switch_to_high_level()
        
        try:
            velocity = -self.state.speed * 0.3
            print(f"🚶 Movendo para direita (vel: {velocity:.2f})...")
            self.loco_client.Move(vx=0.0, vy=velocity, vyaw=0.0, continous_move=False)
        except Exception as e:
            print(f"✗ Erro no movimento: {e}")
    
    def rotate_left(self):
        """Rotaciona o robô para a esquerda"""
        if self.state.mode != ControlMode.HIGH_LEVEL:
            self.switch_to_high_level()
        
        try:
            angular_vel = self.state.speed * 0.5
            print(f"🔄 Rotacionando para esquerda (vel: {angular_vel:.2f})...")
            self.loco_client.Move(vx=0.0, vy=0.0, vyaw=angular_vel, continous_move=False)
        except Exception as e:
            print(f"✗ Erro na rotação: {e}")
    
    def rotate_right(self):
        """Rotaciona o robô para a direita"""
        if self.state.mode != ControlMode.HIGH_LEVEL:
            self.switch_to_high_level()
        
        try:
            angular_vel = -self.state.speed * 0.5
            print(f"🔄 Rotacionando para direita (vel: {angular_vel:.2f})...")
            self.loco_client.Move(vx=0.0, vy=0.0, vyaw=angular_vel, continous_move=False)
        except Exception as e:
            print(f"✗ Erro na rotação: {e}")
    
    def stop_movement(self):
        """Para todos os movimentos"""
        if self.state.mode != ControlMode.HIGH_LEVEL:
            self.switch_to_high_level()
        
        try:
            print("🛑 Parando movimento...")
            self.loco_client.StopMove()
        except Exception as e:
            print(f"✗ Erro ao parar: {e}")
    
    def emergency_stop(self):
        """Parada de emergência"""
        try:
            print("🚨 PARADA DE EMERGÊNCIA!")
            if self.state.mode == ControlMode.HIGH_LEVEL:
                self.loco_client.Damp()
            else:
                # Para todos os motores em modo de baixo nível
                zero_positions = {i: self.target_positions[i] for i in range(G1_NUM_MOTOR)}
                self.send_low_level_command(zero_positions)
            self.state.emergency_stop = True
        except Exception as e:
            print(f"✗ Erro na parada de emergência: {e}")
    
    def perform_gesture(self, gesture_name: str):
        """Executa gestos predefinidos"""
        if self.state.mode != ControlMode.HIGH_LEVEL:
            self.switch_to_high_level()
        
        try:
            if gesture_name == "wave":
                print("👋 Acenando...")
                self.loco_client.WaveHand()
            elif gesture_name == "shake":
                print("🤝 Cumprimentando...")
                self.loco_client.ShakeHand()
            elif gesture_name == "high_stand":
                print("🧍 Posição alta...")
                self.loco_client.HighStand()
            elif gesture_name == "low_stand":
                print("🧍 Posição baixa...")
                self.loco_client.LowStand()
            else:
                print(f"✗ Gesto '{gesture_name}' não reconhecido")
        except Exception as e:
            print(f"✗ Erro no gesto: {e}")
    
    def change_speed(self, speed_level: str):
        """Altera a velocidade de movimento"""
        speed_map = {
            'slow': 0.3,
            'normal': 1.0,
            'fast': 1.5
        }
        
        if speed_level in speed_map:
            self.state.speed = speed_map[speed_level]
            print(f"⚡ Velocidade alterada para: {speed_level} ({self.state.speed:.1f}x)")
        else:
            print(f"✗ Velocidade '{speed_level}' não reconhecida")
    
    def reset_to_home(self):
        """Retorna o robô para posição inicial"""
        print("🏠 Retornando para posição inicial...")
        
        # Reset braços
        self.set_arm_position('home')
        time.sleep(1)
        
        # Reset pernas
        self.set_leg_position('home')
        time.sleep(1)
        
        # Reset locomoção
        if self.state.mode == ControlMode.HIGH_LEVEL:
            self.loco_client.BalanceStand()
        
        self.state.emergency_stop = False
        print("✓ Posição inicial restaurada")
    
    def show_status(self):
        """Mostra status atual do robô"""
        print("\n" + "="*50)
        print("📊 STATUS DO ROBÔ G1")
        print("="*50)
        print(f"Modo: {self.state.mode}")
        print(f"Velocidade: {self.state.speed:.1f}x")
        print(f"Emergência: {'🚨 ATIVA' if self.state.emergency_stop else '✅ Normal'}")
        print(f"Tempo ativo: {time.time() - self.state.timestamp:.1f}s")
        
        # Mostra algumas posições dos motores
        print("\n🔧 Posições dos Motores (principais):")
        key_joints = [
            (ArmJoints.LEFT_SHOULDER_PITCH, "Ombro Esq."),
            (ArmJoints.RIGHT_SHOULDER_PITCH, "Ombro Dir."),
            (LegJoints.LEFT_KNEE, "Joelho Esq."),
            (LegJoints.RIGHT_KNEE, "Joelho Dir.")
        ]
        
        for joint_id, name in key_joints:
            pos = self.target_positions[joint_id]
            print(f"  {name}: {pos:.3f} rad ({math.degrees(pos):.1f}°)")
        
        print("="*50 + "\n")
    
    def set_arm_position(self, position_name: str):
        """Define posição predefinida dos braços"""
        if position_name not in self.arm_positions:
            print(f"✗ Posição '{position_name}' não encontrada")
            return
        
        if self.state.mode != ControlMode.LOW_LEVEL:
            self.switch_to_low_level()
        
        positions = self.arm_positions[position_name].copy()
        # Mescla com posições atuais
        for joint_id in range(G1_NUM_MOTOR):
            if joint_id not in positions:
                positions[joint_id] = self.target_positions[joint_id]
        
        self.send_low_level_command(positions)
        # Movimento suave para posições dos braços
        self.move_arm_smooth(positions, duration=2.0)
        print(f"✓ Posição dos braços: {position_name}")
    
    def show_main_menu(self):
        """Mostra o menu principal de controle"""
        print("\n" + "="*60)
        print("🤖 CONTROLE MANUAL DO ROBÔ UNITREE G1")
        print("="*60)
        print("\n📋 MENU PRINCIPAL:")
        print("  [1] Controle de Braços")
        print("  [2] Controle de Pernas")
        print("  [3] Locomoção")
        print("  [4] Gestos e Posições")
        print("  [5] Configurações")
        print("  [6] Status do Robô")
        print("  [ESC] Parada de Emergência")
        print("  [Q] Sair")
        print("\n💡 Digite o número da opção desejada...")
    
    def show_arm_menu(self):
        """Mostra menu de controle dos braços"""
        print("\n" + "="*50)
        print("🦾 CONTROLE DE BRAÇOS")
        print("="*50)
        print("\n🎯 Posições Predefinidas:")
        print("  [H] Home (posição inicial)")
        print("  [U] Levantar braços")
        print("  [D] Abaixar braços")
        print("  [E] Estender braços")
        print("  [F] Flexionar braços")
        
        print("\n🎮 Controle Individual:")
        print("  [1-6] Braço Esquerdo: 1=Ombro↑ 2=Ombro↓ 3=Cotovelo↑ 4=Cotovelo↓ 5=Punho↑ 6=Punho↓")
        print("  [7-0,-,=] Braço Direito: 7=Ombro↑ 8=Ombro↓ 9=Cotovelo↑ 0=Cotovelo↓ -=Punho↑ ==Punho↓")
        
        print("\n[B] Voltar ao menu principal")
    
    def show_leg_menu(self):
        """Mostra menu de controle das pernas"""
        print("\n" + "="*50)
        print("🦵 CONTROLE DE PERNAS")
        print("="*50)
        print("\n🎯 Posições Predefinidas:")
        print("  [H] Home (posição inicial)")
        print("  [S] Agachar (Squat)")
        print("  [T] Sentar (Sit)")
        print("  [W] Posição ampla (Wide stance)")
        
        print("\n🏋️ Exercícios:")
        print("  [1] Agachamento completo")
        print("  [2] Sentar")
        print("  [3] Levantar")
        
        print("\n[B] Voltar ao menu principal")
    
    def show_locomotion_menu(self):
        """Mostra menu de locomoção"""
        print("\n" + "="*50)
        print("🚶 CONTROLE DE LOCOMOÇÃO")
        print("="*50)
        print("\n🎮 Movimentos Direcionais:")
        print("  [W] Frente    [S] Trás")
        print("  [A] Esquerda  [D] Direita")
        print("  [Q] Rotação ← [E] Rotação →")
        print("  [SPACE] Parar movimento")
        
        print("\n⚡ Controle de Velocidade:")
        print("  [1] Lento  [2] Normal  [3] Rápido")
        
        print("\n[B] Voltar ao menu principal")
    
    def show_gesture_menu(self):
        """Mostra menu de gestos e posições"""
        print("\n" + "="*50)
        print("👋 GESTOS E POSIÇÕES")
        print("="*50)
        print("\n🤝 Gestos Sociais:")
        print("  [W] Acenar (Wave)")
        print("  [S] Cumprimentar (Shake)")
        
        print("\n🧍 Posições de Corpo:")
        print("  [H] Posição alta (High stand)")
        print("  [L] Posição baixa (Low stand)")
        print("  [R] Reset para home")
        
        print("\n[B] Voltar ao menu principal")
    
    def show_settings_menu(self):
        """Mostra menu de configurações"""
        print("\n" + "="*50)
        print("⚙️ CONFIGURAÇÕES")
        print("="*50)
        print("\n⚡ Velocidade Atual:", f"{self.state.speed:.1f}x")
        print("  [1] Lento (0.3x)")
        print("  [2] Normal (1.0x)")
        print("  [3] Rápido (1.5x)")
        
        print("\n🔧 Modo Atual:", self.state.mode.name)
        print("  [H] Modo Alto Nível (High Level)")
        print("  [L] Modo Baixo Nível (Low Level)")
        
        print("\n🏠 Reset:")
        print("  [R] Reset completo para posição inicial")
        
        print("\n[B] Voltar ao menu principal")
    
    def handle_arm_control(self, key: str):
        """Processa comandos de controle dos braços"""
        if key.upper() == 'H':
            self.set_arm_position('home')
        elif key.upper() == 'U':
            self.set_arm_position('raised')
        elif key.upper() == 'D':
            self.set_arm_position('lowered')
        elif key.upper() == 'E':
            self.set_arm_position('extended')
        elif key.upper() == 'F':
            self.set_arm_position('flexed')
        # Controle individual - Braço Esquerdo
        elif key == '1':
            self.control_individual_arm('left', 'shoulder', 0.1)
        elif key == '2':
            self.control_individual_arm('left', 'shoulder', -0.1)
        elif key == '3':
            self.control_individual_arm('left', 'elbow', 0.1)
        elif key == '4':
            self.control_individual_arm('left', 'elbow', -0.1)
        elif key == '5':
            self.control_individual_arm('left', 'wrist', 0.1)
        elif key == '6':
            self.control_individual_arm('left', 'wrist', -0.1)
        # Controle individual - Braço Direito
        elif key == '7':
            self.control_individual_arm('right', 'shoulder', 0.1)
        elif key == '8':
            self.control_individual_arm('right', 'shoulder', -0.1)
        elif key == '9':
            self.control_individual_arm('right', 'elbow', 0.1)
        elif key == '0':
            self.control_individual_arm('right', 'elbow', -0.1)
        elif key == '-':
            self.control_individual_arm('right', 'wrist', 0.1)
        elif key == '=':
            self.control_individual_arm('right', 'wrist', -0.1)
        else:
            print(f"✗ Comando '{key}' não reconhecido para braços")
    
    def handle_leg_control(self, key: str):
        """Processa comandos de controle das pernas"""
        if key.upper() == 'H':
            self.set_leg_position('home')
        elif key.upper() == 'S':
            self.set_leg_position('squat')
        elif key.upper() == 'T':
            self.set_leg_position('sit')
        elif key.upper() == 'W':
            self.set_leg_position('wide_stance')
        elif key == '1':
            self.perform_leg_exercise('squat')
        elif key == '2':
            self.perform_leg_exercise('sit')
        elif key == '3':
            self.perform_leg_exercise('stand')
        else:
            print(f"✗ Comando '{key}' não reconhecido para pernas")
    
    def handle_locomotion_control(self, key: str):
        """Processa comandos de locomoção"""
        if key.upper() == 'W':
            self.move_forward()
        elif key.upper() == 'S':
            self.move_backward()
        elif key.upper() == 'A':
            self.move_left()
        elif key.upper() == 'D':
            self.move_right()
        elif key.upper() == 'Q':
            self.rotate_left()
        elif key.upper() == 'E':
            self.rotate_right()
        elif key == ' ':
            self.stop_movement()
        elif key == '1':
            self.change_speed('slow')
        elif key == '2':
            self.change_speed('normal')
        elif key == '3':
            self.change_speed('fast')
        else:
            print(f"✗ Comando '{key}' não reconhecido para locomoção")
    
    def handle_gesture_control(self, key: str):
        """Processa comandos de gestos"""
        if key.upper() == 'W':
            self.perform_gesture('wave')
        elif key.upper() == 'S':
            self.perform_gesture('shake')
        elif key.upper() == 'H':
            self.perform_gesture('high_stand')
        elif key.upper() == 'L':
            self.perform_gesture('low_stand')
        elif key.upper() == 'R':
            self.reset_to_home()
        else:
            print(f"✗ Comando '{key}' não reconhecido para gestos")
    
    def handle_settings_control(self, key: str):
        """Processa comandos de configurações"""
        if key == '1':
            self.change_speed('slow')
        elif key == '2':
            self.change_speed('normal')
        elif key == '3':
            self.change_speed('fast')
        elif key.upper() == 'H':
            self.switch_to_high_level()
        elif key.upper() == 'L':
            self.switch_to_low_level()
        elif key.upper() == 'R':
            self.reset_to_home()
        else:
            print(f"✗ Comando '{key}' não reconhecido para configurações")
    
    def run_interactive_control(self):
        """Executa o loop principal de controle interativo"""
        print("\n🚀 Iniciando controle interativo do Unitree G1...")
        print("⚠️  AVISO: Certifique-se de que o robô está em área segura!")
        
        current_menu = 'main'
        keyboard = KeyboardInput()
        
        try:
            while not self.state.emergency_stop:
                # Mostra o menu apropriado
                if current_menu == 'main':
                    self.show_main_menu()
                elif current_menu == 'arms':
                    self.show_arm_menu()
                elif current_menu == 'legs':
                    self.show_leg_menu()
                elif current_menu == 'locomotion':
                    self.show_locomotion_menu()
                elif current_menu == 'gestures':
                    self.show_gesture_menu()
                elif current_menu == 'settings':
                    self.show_settings_menu()
                
                # Captura entrada do usuário
                key = keyboard.get_key()
                
                if not key:
                    time.sleep(0.1)
                    continue
                
                # Comandos globais
                if key == '\x1b':  # ESC
                    self.emergency_stop()
                    break
                elif key.upper() == 'Q' and current_menu == 'main':
                    print("👋 Encerrando controle manual...")
                    break
                elif key.upper() == 'B' and current_menu != 'main':
                    current_menu = 'main'
                    continue
                
                # Processa comandos específicos do menu
                if current_menu == 'main':
                    if key == '1':
                        current_menu = 'arms'
                    elif key == '2':
                        current_menu = 'legs'
                    elif key == '3':
                        current_menu = 'locomotion'
                    elif key == '4':
                        current_menu = 'gestures'
                    elif key == '5':
                        current_menu = 'settings'
                    elif key == '6':
                        self.show_status()
                    else:
                        print(f"✗ Opção '{key}' inválida")
                
                elif current_menu == 'arms':
                    self.handle_arm_control(key)
                elif current_menu == 'legs':
                    self.handle_leg_control(key)
                elif current_menu == 'locomotion':
                    self.handle_locomotion_control(key)
                elif current_menu == 'gestures':
                    self.handle_gesture_control(key)
                elif current_menu == 'settings':
                    self.handle_settings_control(key)
                
                time.sleep(0.1)  # Pequena pausa para evitar spam
        
        except KeyboardInterrupt:
            print("\n🛑 Interrompido pelo usuário")
            self.emergency_stop()
        except Exception as e:
            print(f"\n✗ Erro no controle: {e}")
            self.emergency_stop()
        finally:
            self.stop()
    
    def locomotion_move(self, vx: float, vy: float, vyaw: float):
        """Controla locomoção do robô"""
        if self.state.mode != ControlMode.HIGH_LEVEL:
            print("⚠ Mudando para modo de alto nível...")
            self.switch_to_high_level()
        
        try:
            # Aplica velocidade baseada na configuração atual
            scaled_vx = vx * self.state.speed
            scaled_vy = vy * self.state.speed
            scaled_vyaw = vyaw * self.state.speed
            
            self.loco_client.Move(scaled_vx, scaled_vy, scaled_vyaw)
            
            direction = ""
            if vx > 0: direction += "Frente "
            elif vx < 0: direction += "Trás "
            if vy > 0: direction += "Esquerda "
            elif vy < 0: direction += "Direita "
            if vyaw > 0: direction += "Rotação Anti-horária"
            elif vyaw < 0: direction += "Rotação Horária"
            
            if direction:
                print(f"🚶 Movimento: {direction.strip()} (velocidade: {self.state.speed:.1f})")
            
        except Exception as e:
            print(f"✗ Erro na locomoção: {e}")
    
    def stop_movement(self):
        """Para todos os movimentos"""
        try:
            if self.state.mode == ControlMode.HIGH_LEVEL:
                self.loco_client.StopMove()
            print("⏹ Movimento parado")
        except Exception as e:
            print(f"✗ Erro ao parar movimento: {e}")
    
    def emergency_stop(self):
        """Parada de emergência"""
        self.state.emergency_stop = True
        try:
            if self.loco_client:
                self.loco_client.Damp()
            print("🚨 PARADA DE EMERGÊNCIA ATIVADA")
        except Exception as e:
            print(f"✗ Erro na parada de emergência: {e}")
    
    def reset_emergency(self):
        """Reseta parada de emergência"""
        self.state.emergency_stop = False
        print("✓ Parada de emergência desativada")
    
    def change_speed(self, new_speed: float):
        """Altera velocidade de movimento"""
        self.state.speed = max(0.1, min(1.0, new_speed))
        speed_name = "Lenta" if self.state.speed <= 0.2 else "Normal" if self.state.speed <= 0.4 else "Rápida"
        print(f"⚡ Velocidade: {speed_name} ({self.state.speed:.1f})")
    
    def show_status(self):
        """Mostra status atual do robô"""
        print("\n" + "="*50)
        print("📊 STATUS DO ROBÔ G1")
        print("="*50)
        print(f"Modo: {self.state.mode}")
        print(f"Velocidade: {self.state.speed:.1f}")
        print(f"Emergência: {'🚨 ATIVA' if self.state.emergency_stop else '✓ Normal'}")
        print(f"Último comando: {self.state.last_command}")
        print(f"Timestamp: {time.strftime('%H:%M:%S', time.localtime(self.state.timestamp))}")
        print("="*50 + "\n")
    
    def show_menu(self):
        """Mostra menu de controles"""
        print("\n" + "="*60)
        print("🤖 CONTROLE MANUAL DO ROBÔ UNITREE G1")
        print("="*60)
        print("LOCOMOÇÃO (Alto Nível):")
        print("  W/S    - Frente/Trás")
        print("  A/D    - Esquerda/Direita")
        print("  Q/E    - Rotação Anti-horária/Horária")
        print("  SPACE  - Parar movimento")
        print("")
        print("BRAÇOS (Baixo Nível):")
        print("  1/2    - Ombro esquerdo +/-")
        print("  3/4    - Cotovelo esquerdo +/-")
        print("  5/6    - Ombro direito +/-")
        print("  7/8    - Cotovelo direito +/-")
        print("")
        print("POSIÇÕES PREDEFINIDAS:")
        print("  H      - Home (posição inicial)")
        print("  U      - Braços para cima")
        print("  F      - Braços para frente")
        print("")
        print("CONTROLE:")
        print("  +/-    - Aumentar/Diminuir velocidade")
        print("  M      - Alternar modo (Alto/Baixo nível)")
        print("  I      - Mostrar informações")
        print("  R      - Reset emergência")
        print("  ESC    - Parada de emergência")
        print("  X      - Sair")
        print("="*60 + "\n")
    
    def run_control_loop(self):
        """Loop principal de controle"""
        print("🎮 Iniciando controle manual...")
        self.show_menu()
        
        try:
            with KeyboardInput() as keyboard:
                while self.running:
                    key = keyboard.get_key(0.1)
                    
                    if key is None:
                        continue
                    
                    self.state.timestamp = time.time()
                    
                    # Controles de locomoção
                    if key.lower() == 'w':
                        self.state.last_command = "Frente"
                        self.locomotion_move(1.0, 0.0, 0.0)
                    elif key.lower() == 's':
                        self.state.last_command = "Trás"
                        self.locomotion_move(-1.0, 0.0, 0.0)
                    elif key.lower() == 'a':
                        self.state.last_command = "Esquerda"
                        self.locomotion_move(0.0, 1.0, 0.0)
                    elif key.lower() == 'd':
                        self.state.last_command = "Direita"
                        self.locomotion_move(0.0, -1.0, 0.0)
                    elif key.lower() == 'q':
                        self.state.last_command = "Rotação Anti-horária"
                        self.locomotion_move(0.0, 0.0, 1.0)
                    elif key.lower() == 'e':
                        self.state.last_command = "Rotação Horária"
                        self.locomotion_move(0.0, 0.0, -1.0)
                    elif key == ' ':
                        self.state.last_command = "Parar"
                        self.stop_movement()
                    
                    # Controles de braços
                    elif key == '1':
                        self.state.last_command = "Ombro esquerdo +"
                        self.move_arm_joint(ArmJoints.LEFT_SHOULDER_PITCH, -0.1)
                    elif key == '2':
                        self.state.last_command = "Ombro esquerdo -"
                        self.move_arm_joint(ArmJoints.LEFT_SHOULDER_PITCH, 0.1)
                    elif key == '3':
                        self.state.last_command = "Cotovelo esquerdo +"
                        self.move_arm_joint(ArmJoints.LEFT_ELBOW, 0.1)
                    elif key == '4':
                        self.state.last_command = "Cotovelo esquerdo -"
                        self.move_arm_joint(ArmJoints.LEFT_ELBOW, -0.1)
                    elif key == '5':
                        self.state.last_command = "Ombro direito +"
                        self.move_arm_joint(ArmJoints.RIGHT_SHOULDER_PITCH, -0.1)
                    elif key == '6':
                        self.state.last_command = "Ombro direito -"
                        self.move_arm_joint(ArmJoints.RIGHT_SHOULDER_PITCH, 0.1)
                    elif key == '7':
                        self.state.last_command = "Cotovelo direito +"
                        self.move_arm_joint(ArmJoints.RIGHT_ELBOW, 0.1)
                    elif key == '8':
                        self.state.last_command = "Cotovelo direito -"
                        self.move_arm_joint(ArmJoints.RIGHT_ELBOW, -0.1)
                    
                    # Posições predefinidas
                    elif key.lower() == 'h':
                        self.state.last_command = "Posição Home"
                        self.set_arm_position('home')
                    elif key.lower() == 'u':
                        self.state.last_command = "Braços para cima"
                        self.set_arm_position('arms_up')
                    elif key.lower() == 'f':
                        self.state.last_command = "Braços para frente"
                        self.set_arm_position('arms_forward')
                    
                    # Controles de velocidade
                    elif key == '+':
                        self.change_speed(self.state.speed + 0.1)
                    elif key == '-':
                        self.change_speed(self.state.speed - 0.1)
                    
                    # Controles de modo
                    elif key.lower() == 'm':
                        if self.state.mode == ControlMode.LOW_LEVEL:
                            self.switch_to_high_level()
                        else:
                            self.switch_to_low_level()
                    
                    # Informações e controles
                    elif key.lower() == 'i':
                        self.show_status()
                    elif key.lower() == 'r':
                        self.reset_emergency()
                    elif key == '\x1b':  # ESC
                        self.emergency_stop()
                    elif key.lower() == 'x':
                        print("🔚 Encerrando controle manual...")
                        break
                    
                    # Pequeno delay para evitar spam
                    time.sleep(0.05)
                    
        except KeyboardInterrupt:
            print("\n🔚 Controle interrompido pelo usuário")
        except Exception as e:
            print(f"\n✗ Erro no loop de controle: {e}")
        finally:
            self.stop_movement()
            print("✓ Controle manual finalizado")
    
    def start(self):
        """Inicia o controlador manual"""
        print("🚀 Iniciando Controlador Manual do G1...")
        
        if not self.initialize_communication():
            return False
        
        self.running = True
        
        # Inicia em modo de alto nível
        self.switch_to_high_level()
        
        # Executa loop de controle
        self.run_control_loop()
        
        return True
    
    def stop(self):
        """Para o controlador"""
        self.running = False
        self.stop_movement()

def main():
    """Função principal"""
    if len(sys.argv) < 2:
        print(f"Uso: python3 {sys.argv[0]} <interface_de_rede>")
        print("Exemplo: python3 g1_manual_control.py eth0")
        sys.exit(-1)
    
    print("⚠️  AVISO DE SEGURANÇA ⚠️")
    print("Este script controla diretamente o robô G1.")
    print("Certifique-se de que:")
    print("- O robô está em área segura")
    print("- Não há obstáculos ao redor")
    print("- Você está preparado para parada de emergência (ESC)")
    print("- O robô está devidamente conectado")
    
    response = input("\nDeseja continuar? (s/N): ")
    if response.lower() not in ['s', 'sim', 'y', 'yes']:
        print("Operação cancelada.")
        sys.exit(0)
    
    try:
        controller = G1ManualController(sys.argv[1])
        controller.start()
    except Exception as e:
        print(f"✗ Erro fatal: {e}")
        sys.exit(-1)

if __name__ == "__main__":
    main()