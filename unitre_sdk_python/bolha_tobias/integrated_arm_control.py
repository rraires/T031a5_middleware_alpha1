#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Controle Integrado de Braços - Robô G1 Unitree

Este script demonstra como integrar controle de alto e baixo nível
em uma única aplicação, permitindo escolher o método mais adequado
para cada situação.

Uso: python integrated_arm_control.py <interface_de_rede>
"""

import sys
import time
import threading
from typing import Optional, Dict, Any

# Importações do SDK Unitree
sys.path.append('/opt/unitree/sdk2/lib/python')
from unitree_sdk2py.core.channel import ChannelSubscriber, ChannelPublisher
from unitree_sdk2py.idl.default import unitree_go_msg_dds__LowState_
from unitree_sdk2py.idl.default import unitree_go_msg_dds__LowCmd_
from unitree_sdk2py.idl.unitree_go.msg.dds_ import LowState_
from unitree_sdk2py.idl.unitree_go.msg.dds_ import LowCmd_
from unitree_sdk2py.utils.crc import CRC
from unitree_sdk2py.g1.g1_arm_action_client import G1ArmActionClient, action_map

class IntegratedArmController:
    """Controlador integrado que combina alto e baixo nível"""
    
    def __init__(self, network_interface: str):
        self.network_interface = network_interface
        self.high_level_client: Optional[G1ArmActionClient] = None
        self.low_level_active = False
        self.robot_state: Optional[LowState_] = None
        
        # Configurações de baixo nível
        self.dt = 0.002  # 2ms
        self.crc = CRC()
        
        # Índices dos motores dos braços
        self.left_arm_motors = [8, 9, 10, 11, 12, 13, 14]   # Braço esquerdo
        self.right_arm_motors = [15, 16, 17, 18, 19, 20, 21] # Braço direito
        
        # Posições neutras dos braços
        self.neutral_positions = {
            # Braço esquerdo
            8: 0.0, 9: 0.3, 10: -0.6, 11: 0.0, 12: 0.0, 13: 0.0, 14: 0.0,
            # Braço direito  
            15: 0.0, 16: 0.3, 17: -0.6, 18: 0.0, 19: 0.0, 20: 0.0, 21: 0.0
        }
        
        # Posições para levantar braços
        self.raised_positions = {
            # Braço esquerdo levantado
            'left': {8: 0.0, 9: -1.2, 10: -0.3, 11: 0.0, 12: 0.0, 13: 0.0, 14: 0.0},
            # Braço direito levantado
            'right': {15: 0.0, 16: -1.2, 17: -0.3, 18: 0.0, 19: 0.0, 20: 0.0, 21: 0.0}
        }
        
        print(f"🤖 Controlador Integrado inicializado para interface: {network_interface}")
    
    def initialize_high_level(self) -> bool:
        """Inicializa o cliente de alto nível"""
        try:
            print("🔧 Inicializando controle de alto nível...")
            self.high_level_client = G1ArmActionClient(self.network_interface)
            
            # Verificar se o cliente está funcionando
            actions = self.high_level_client.GetActionList()
            if actions:
                print(f"✅ Alto nível inicializado. {len(actions)} ações disponíveis")
                return True
            else:
                print("❌ Falha ao obter lista de ações")
                return False
                
        except Exception as e:
            print(f"❌ Erro ao inicializar alto nível: {e}")
            return False
    
    def initialize_low_level(self) -> bool:
        """Inicializa comunicação de baixo nível"""
        try:
            print("🔧 Inicializando controle de baixo nível...")
            
            # Subscriber para estado do robô
            self.state_subscriber = ChannelSubscriber(
                "rt/lowstate", LowState_
            )
            self.state_subscriber.Init(self._state_callback, 10)
            
            # Publisher para comandos
            self.cmd_publisher = ChannelPublisher(
                "rt/lowcmd", LowCmd_
            )
            self.cmd_publisher.Init()
            
            # Aguardar primeiro estado
            print("⏳ Aguardando estado do robô...")
            timeout = 5.0
            start_time = time.time()
            
            while self.robot_state is None and (time.time() - start_time) < timeout:
                time.sleep(0.1)
            
            if self.robot_state is None:
                print("❌ Timeout ao aguardar estado do robô")
                return False
            
            print("✅ Baixo nível inicializado")
            self.low_level_active = True
            return True
            
        except Exception as e:
            print(f"❌ Erro ao inicializar baixo nível: {e}")
            return False
    
    def _state_callback(self, msg: LowState_):
        """Callback para receber estado do robô"""
        self.robot_state = msg
    
    def high_level_movement(self, action_name: str, duration: float = 2.0) -> bool:
        """Executa movimento usando alto nível"""
        if not self.high_level_client:
            print("❌ Cliente de alto nível não inicializado")
            return False
        
        try:
            print(f"🎯 Executando ação de alto nível: {action_name}")
            
            # Verificar se a ação existe
            if action_name not in action_map:
                print(f"❌ Ação '{action_name}' não encontrada")
                return False
            
            # Executar ação
            action_id = action_map[action_name]
            result = self.high_level_client.ExecuteAction(action_id)
            
            if result:
                print(f"✅ Ação '{action_name}' executada")
                time.sleep(duration)
                return True
            else:
                print(f"❌ Falha ao executar ação '{action_name}'")
                return False
                
        except Exception as e:
            print(f"❌ Erro no movimento de alto nível: {e}")
            return False
    
    def low_level_movement(self, arm: str, action: str, duration: float = 2.0) -> bool:
        """Executa movimento usando baixo nível"""
        if not self.low_level_active or not self.robot_state:
            print("❌ Baixo nível não inicializado")
            return False
        
        try:
            print(f"🎯 Executando movimento de baixo nível: {arm} {action}")
            
            # Determinar posições alvo
            if action == "raise":
                if arm == "left":
                    target_positions = self.raised_positions['left']
                elif arm == "right":
                    target_positions = self.raised_positions['right']
                else:
                    print(f"❌ Braço inválido: {arm}")
                    return False
            elif action == "lower":
                if arm == "left":
                    target_positions = {k: self.neutral_positions[k] for k in self.left_arm_motors}
                elif arm == "right":
                    target_positions = {k: self.neutral_positions[k] for k in self.right_arm_motors}
                else:
                    print(f"❌ Braço inválido: {arm}")
                    return False
            else:
                print(f"❌ Ação inválida: {action}")
                return False
            
            # Executar movimento interpolado
            return self._execute_interpolated_movement(target_positions, duration)
            
        except Exception as e:
            print(f"❌ Erro no movimento de baixo nível: {e}")
            return False
    
    def _execute_interpolated_movement(self, target_positions: Dict[int, float], duration: float) -> bool:
        """Executa movimento interpolado"""
        try:
            # Obter posições iniciais
            initial_positions = {}
            for motor_id in target_positions.keys():
                initial_positions[motor_id] = self.robot_state.motor_state[motor_id].q
            
            # Calcular número de passos
            steps = int(duration / self.dt)
            
            print(f"🔄 Executando {steps} passos em {duration:.1f}s")
            
            for step in range(steps):
                # Calcular fator de interpolação (0 a 1)
                t = step / (steps - 1) if steps > 1 else 1.0
                
                # Criar comando
                cmd = LowCmd_()
                cmd.head[0] = 0xFE
                cmd.head[1] = 0xEF
                cmd.level_flag = 0xFF
                cmd.gpio = 0
                
                # Configurar motores
                for i in range(29):
                    cmd.motor_cmd[i].mode = 0x01  # Modo posição
                    cmd.motor_cmd[i].q = self.robot_state.motor_state[i].q
                    cmd.motor_cmd[i].kp = 0.0
                    cmd.motor_cmd[i].kd = 0.0
                    cmd.motor_cmd[i].dq = 0.0
                    cmd.motor_cmd[i].tau = 0.0
                
                # Aplicar interpolação aos motores alvo
                for motor_id, target_pos in target_positions.items():
                    initial_pos = initial_positions[motor_id]
                    interpolated_pos = initial_pos + t * (target_pos - initial_pos)
                    
                    cmd.motor_cmd[motor_id].mode = 0x01
                    cmd.motor_cmd[motor_id].q = interpolated_pos
                    cmd.motor_cmd[motor_id].kp = 30.0
                    cmd.motor_cmd[motor_id].kd = 3.0
                
                # Calcular CRC
                cmd.crc = self.crc.Crc(cmd)
                
                # Enviar comando
                self.cmd_publisher.Write(cmd)
                
                # Aguardar próximo ciclo
                time.sleep(self.dt)
            
            print("✅ Movimento de baixo nível concluído")
            return True
            
        except Exception as e:
            print(f"❌ Erro na execução interpolada: {e}")
            return False
    
    def demonstrate_sequence(self):
        """Demonstra a sequência completa usando ambos os métodos"""
        print("\n" + "="*60)
        print("🎭 DEMONSTRAÇÃO DE SEQUÊNCIA INTEGRADA")
        print("="*60)
        
        # Sequência usando alto nível
        print("\n🔵 PARTE 1: Controle de Alto Nível")
        print("-" * 40)
        
        if self.high_level_client:
            # Posição inicial
            self.high_level_movement("release arm", 1.0)
            
            # Levantar ambas as mãos
            self.high_level_movement("hands up", 2.0)
            
            # Levantar apenas mão direita
            self.high_level_movement("right hand up", 2.0)
            
            # Retornar à posição neutra
            self.high_level_movement("release arm", 1.0)
        
        print("\n⏸️  Pausa de 3 segundos entre métodos...")
        time.sleep(3)
        
        # Sequência usando baixo nível
        print("\n🟡 PARTE 2: Controle de Baixo Nível")
        print("-" * 40)
        
        if self.low_level_active:
            # Levantar mão esquerda
            self.low_level_movement("left", "raise", 2.0)
            time.sleep(1)
            
            # Abaixar mão esquerda
            self.low_level_movement("left", "lower", 2.0)
            time.sleep(1)
            
            # Levantar mão direita
            self.low_level_movement("right", "raise", 2.0)
            time.sleep(1)
            
            # Abaixar mão direita
            self.low_level_movement("right", "lower", 2.0)
        
        print("\n✅ Demonstração integrada concluída!")
    
    def cleanup(self):
        """Limpeza de recursos"""
        print("🧹 Limpando recursos...")
        self.low_level_active = False
        
        if hasattr(self, 'state_subscriber'):
            del self.state_subscriber
        if hasattr(self, 'cmd_publisher'):
            del self.cmd_publisher
        
        print("✅ Limpeza concluída")

def main():
    """Função principal"""
    if len(sys.argv) < 2:
        print("❌ Uso incorreto!")
        print(f"Uso: python {sys.argv[0]} <interface_de_rede>")
        print("Exemplo: python integrated_arm_control.py eth0")
        sys.exit(1)
    
    network_interface = sys.argv[1]
    
    # Aviso de segurança
    print("⚠️  AVISO DE SEGURANÇA:")
    print("   • Este script combina controle de alto e baixo nível")
    print("   • Certifique-se de que o robô está em área segura")
    print("   • Mantenha o botão de emergência sempre à mão")
    print("   • Interrompa se algo parecer anormal")
    
    try:
        input("\n🔄 Pressione Enter para continuar ou Ctrl+C para cancelar...")
    except KeyboardInterrupt:
        print("\n❌ Operação cancelada pelo usuário")
        sys.exit(0)
    
    # Criar controlador
    controller = IntegratedArmController(network_interface)
    
    try:
        # Inicializar sistemas
        print("\n🚀 Inicializando sistemas...")
        
        high_level_ok = controller.initialize_high_level()
        low_level_ok = controller.initialize_low_level()
        
        if not high_level_ok and not low_level_ok:
            print("❌ Falha ao inicializar ambos os sistemas")
            return
        
        if not high_level_ok:
            print("⚠️  Apenas baixo nível disponível")
        elif not low_level_ok:
            print("⚠️  Apenas alto nível disponível")
        else:
            print("✅ Ambos os sistemas inicializados")
        
        # Executar demonstração
        controller.demonstrate_sequence()
        
    except KeyboardInterrupt:
        print("\n⏸️  Interrompido pelo usuário")
    except Exception as e:
        print(f"\n❌ Erro durante execução: {e}")
    finally:
        controller.cleanup()
        print("\n👋 Programa finalizado")

if __name__ == "__main__":
    main()