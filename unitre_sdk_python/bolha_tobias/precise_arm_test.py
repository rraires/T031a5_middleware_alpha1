#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Script de Controle Preciso dos Braços - Robô G1 Unitree

Este script usa controle de baixo nível para movimentos precisos:
1. Levantar mão esquerda (controle individual dos motores)
2. Abaixar mão esquerda
3. Levantar mão direita
4. Abaixar mão direita

Uso: python precise_arm_test.py <interface_de_rede>
"""

import time
import sys
import numpy as np

from unitree_sdk2py.core.channel import ChannelPublisher, ChannelSubscriber, ChannelFactoryInitialize
from unitree_sdk2py.idl.default import unitree_hg_msg_dds__LowCmd_
from unitree_sdk2py.idl.default import unitree_hg_msg_dds__LowState_
from unitree_sdk2py.idl.unitree_hg.msg.dds_ import LowCmd_
from unitree_sdk2py.idl.unitree_hg.msg.dds_ import LowState_
from unitree_sdk2py.utils.crc import CRC
from unitree_sdk2py.utils.thread import RecurrentThread
from unitree_sdk2py.comm.motion_switcher.motion_switcher_client import MotionSwitcherClient

# Constantes do robô G1
G1_NUM_MOTOR = 29

# Parâmetros de controle PID
Kp = [
    60, 60, 60, 100, 40, 40,      # pernas
    60, 60, 60, 100, 40, 40,      # pernas
    60, 40, 40,                   # cintura
    40, 40, 40, 40, 40, 40, 40,   # braços
    40, 40, 40, 40, 40, 40, 40    # braços
]

Kd = [
    1, 1, 1, 2, 1, 1,     # pernas
    1, 1, 1, 2, 1, 1,     # pernas
    1, 1, 1,              # cintura
    1, 1, 1, 1, 1, 1, 1,  # braços
    1, 1, 1, 1, 1, 1, 1   # braços
]

# Índices dos motores dos braços
class ArmJoints:
    # Braço esquerdo
    LeftShoulderPitch = 15
    LeftShoulderRoll = 16
    LeftShoulderYaw = 17
    LeftElbow = 18
    LeftWristRoll = 19
    LeftWristPitch = 20
    LeftWristYaw = 21
    
    # Braço direito
    RightShoulderPitch = 22
    RightShoulderRoll = 23
    RightShoulderYaw = 24
    RightElbow = 25
    RightWristRoll = 26
    RightWristPitch = 27
    RightWristYaw = 28

class Mode:
    PR = 0  # Controle em série para juntas Pitch/Roll
    AB = 1  # Controle paralelo para juntas A/B

class PreciseArmController:
    """Controlador preciso para movimentos dos braços do G1"""
    
    def __init__(self):
        self.time_ = 0.0
        self.control_dt_ = 0.002  # 2ms
        self.phase_duration_ = 2.0  # 2 segundos por fase
        self.phase1_duration_ = 1.0  # 1 segundo para fase 1 (dobro da velocidade)
        self.current_phase_ = 0
        self.low_cmd = unitree_hg_msg_dds__LowCmd_()
        self.low_state = None
        self.mode_machine_ = 0
        self.update_mode_machine_ = False
        self.crc = CRC()
        self.initial_positions = {}
        self.target_positions = {}
        
        # Posições alvo para levantar os braços
        self.left_arm_up_positions = {
            ArmJoints.LeftShoulderPitch: -np.pi/3,  # Levantar ombro
            ArmJoints.LeftShoulderRoll: np.pi/6,    # Abrir ligeiramente
            ArmJoints.LeftElbow: -np.pi/4,          # Dobrar cotovelo
        }
    
    def init_communication(self):
        """Inicializa a comunicação com o robô"""
        try:
            # Inicializar motion switcher
            self.msc = MotionSwitcherClient()
            self.msc.SetTimeout(5.0)
            self.msc.Init()
            
            # Verificar e liberar modo atual
            status, result = self.msc.CheckMode()
            while result['name']:
                print(f"Liberando modo atual: {result['name']}")
                self.msc.ReleaseMode()
                status, result = self.msc.CheckMode()
                time.sleep(1)
            
            # Criar publisher para comandos
            self.lowcmd_publisher_ = ChannelPublisher("rt/lowcmd", LowCmd_)
            self.lowcmd_publisher_.Init()
            
            # Criar subscriber para estado
            self.lowstate_subscriber = ChannelSubscriber("rt/lowstate", LowState_)
            self.lowstate_subscriber.Init(self.low_state_handler, 10)
            
            print("✓ Comunicação inicializada com sucesso")
            return True
            
        except Exception as e:
            print(f"✗ Erro ao inicializar comunicação: {e}")
            return False
    
    def low_state_handler(self, msg: LowState_):
        """Handler para receber estado do robô"""
        self.low_state = msg
        
        if not self.update_mode_machine_:
            self.mode_machine_ = self.low_state.mode_machine
            self.update_mode_machine_ = True
            
            # Salvar posições iniciais dos motores
            for i in range(G1_NUM_MOTOR):
                self.initial_positions[i] = self.low_state.motor_state[i].q
    
    def interpolate_position(self, start_pos, target_pos, ratio):
        """Interpola entre posição inicial e alvo"""
        return start_pos + (target_pos - start_pos) * ratio
    
    def set_motor_command(self, motor_id, position, velocity=0.0, torque=0.0):
        """Define comando para um motor específico"""
        self.low_cmd.motor_cmd[motor_id].mode = 1  # Habilitar
        self.low_cmd.motor_cmd[motor_id].q = position
        self.low_cmd.motor_cmd[motor_id].dq = velocity
        self.low_cmd.motor_cmd[motor_id].tau = torque
        self.low_cmd.motor_cmd[motor_id].kp = Kp[motor_id]
        self.low_cmd.motor_cmd[motor_id].kd = Kd[motor_id]
    
    def control_loop(self):
        """Loop principal de controle - apenas Fase 1"""
        self.time_ += self.control_dt_
        
        # Configurar modo de controle
        self.low_cmd.mode_pr = Mode.PR
        self.low_cmd.mode_machine = self.mode_machine_
        
        # Inicializar todos os motores com posições atuais
        for i in range(G1_NUM_MOTOR):
            if i in self.initial_positions:
                self.set_motor_command(i, self.initial_positions[i])
        
        # Apenas Fase 1: Levantar mão esquerda
        if self.time_ <= self.phase1_duration_:
            ratio = self.time_ / self.phase1_duration_
            self.control_left_arm_up(ratio)
            if self.current_phase_ != 1:
                self.current_phase_ = 1
                print("🤖 Fase 1: Levantando mão esquerda (VELOCIDADE DUPLA)")
        else:
            # Manter posição final após completar a fase 1
            for joint_id, target_pos in self.left_arm_up_positions.items():
                self.set_motor_command(joint_id, target_pos)
    
    def control_left_arm_up(self, ratio):
        """Controla movimento de levantar braço esquerdo"""
        ratio = np.clip(ratio, 0.0, 1.0)
        smooth_ratio = 0.5 * (1 - np.cos(np.pi * ratio))  # Suavização
        
        for joint_id, target_pos in self.left_arm_up_positions.items():
            initial_pos = self.initial_positions.get(joint_id, 0.0)
            current_pos = self.interpolate_position(initial_pos, target_pos, smooth_ratio)
            self.set_motor_command(joint_id, current_pos)
    

    
    def send_command(self):
        """Envia comando para o robô"""
        self.low_cmd.crc = self.crc.Crc(self.low_cmd)
        self.lowcmd_publisher_.Write(self.low_cmd)
    
    def start_control(self):
        """Inicia o loop de controle"""
        print("🚀 Iniciando controle preciso dos braços...")
        
        # Aguardar inicialização do estado
        while not self.update_mode_machine_:
            print("⏳ Aguardando inicialização do estado...")
            time.sleep(1)
        
        print("✓ Estado inicializado, iniciando movimentos")
        
        # Criar thread de controle
        self.control_thread = RecurrentThread(
            interval=self.control_dt_,
            target=self.control_and_send,
            name="precise_arm_control"
        )
        
        self.control_thread.Start()
        
        # Executar apenas a Fase 1
        total_duration = self.phase1_duration_ + 1  # Fase 1 + 1 segundo para manter posição
        print(f"⏱️  Executando apenas Fase 1 por {total_duration} segundos...")
        print(f"   • Fase 1 (mão esquerda up): {self.phase1_duration_}s (VELOCIDADE DUPLA)")
        print(f"   • Manter posição: 1s")
        
        try:
            time.sleep(total_duration + 1)  # +1 segundo de margem
            print("✅ Sequência concluída!")
        except KeyboardInterrupt:
            print("\n⏹️  Interrompido pelo usuário")
        finally:
            self.control_thread.Stop()
    
    def control_and_send(self):
        """Executa controle e envia comando"""
        self.control_loop()
        self.send_command()

def main():
    """Função principal"""
    # Verificar argumentos
    if len(sys.argv) < 2:
        print(f"Uso: python {sys.argv[0]} <interface_de_rede>")
        print("Exemplo: python precise_arm_test.py eth0")
        sys.exit(1)
    
    network_interface = sys.argv[1]
    
    print("🤖 CONTROLE PRECISO DOS BRAÇOS - ROBÔ G1")
    print(f"🌐 Interface de rede: {network_interface}")
    
    # Aviso de segurança
    print("\n⚠️  AVISO DE SEGURANÇA:")
    print("   • Certifique-se de que não há obstáculos ao redor do robô")
    print("   • Este script usa controle de baixo nível - seja cauteloso")
    print("   • Mantenha o botão de emergência à mão")
    print("   • O robô executará apenas o movimento de levantar a mão esquerda por ~2 segundos")
    
    try:
        input("\n🔄 Pressione Enter para continuar ou Ctrl+C para cancelar...")
    except KeyboardInterrupt:
        print("\n❌ Teste cancelado pelo usuário")
        sys.exit(0)
    
    try:
        # Inicializar comunicação DDS
        print(f"\n🔧 Inicializando comunicação DDS ({network_interface})...")
        ChannelFactoryInitialize(0, network_interface)
        
        # Criar controlador
        controller = PreciseArmController()
        
        # Inicializar comunicação
        if not controller.init_communication():
            print("❌ Falha na inicialização da comunicação")
            sys.exit(1)
        
        # Iniciar controle
        controller.start_control()
        
        print("\n🎉 Teste de controle preciso concluído!")
        
    except KeyboardInterrupt:
        print("\n⏹️  Teste interrompido pelo usuário")
    except Exception as e:
        print(f"\n❌ Erro inesperado: {e}")
        print("\nVerifique se:")
        print("- O robô está ligado e em modo operacional")
        print("- A interface de rede está correta")
        print("- Você tem permissões adequadas")
        print("- O SDK está instalado corretamente")

if __name__ == "__main__":
    main()