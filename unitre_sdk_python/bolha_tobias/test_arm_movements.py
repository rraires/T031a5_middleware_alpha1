#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Script de Teste de Movimentos do Braço - Robô G1 Unitree

Este script executa uma sequência específica de movimentos:
1. Levantar a mão esquerda
2. Abaixar a mão esquerda
3. Levantar a mão direita
4. Abaixar a mão direita

Uso: python test_arm_movements.py <interface_de_rede>
Exemplo: python test_arm_movements.py eth0
"""

import time
import sys
from unitree_sdk2py.core.channel import ChannelFactoryInitialize
from unitree_sdk2py.g1.arm.g1_arm_action_client import G1ArmActionClient
from unitree_sdk2py.g1.arm.g1_arm_action_client import action_map

class G1ArmMovementTest:
    """Classe para controlar os movimentos de teste do braço do robô G1"""
    
    def __init__(self):
        self.arm_client = None
        self.movement_delay = 3.0  # Delay entre movimentos em segundos
        self.action_delay = 2.0    # Delay para execução da ação
    
    def initialize_client(self):
        """Inicializa o cliente de ações do braço"""
        try:
            self.arm_client = G1ArmActionClient()
            self.arm_client.SetTimeout(10.0)
            self.arm_client.Init()
            print("✓ Cliente de ações do braço inicializado com sucesso")
            return True
        except Exception as e:
            print(f"✗ Erro ao inicializar cliente: {e}")
            return False
    
    def execute_action_safely(self, action_name, description):
        """Executa uma ação com tratamento de erro"""
        try:
            action_id = action_map.get(action_name)
            if action_id is None:
                print(f"✗ Ação '{action_name}' não encontrada no mapa de ações")
                return False
            
            print(f"🤖 Executando: {description}")
            result = self.arm_client.ExecuteAction(action_id)
            
            if result == 0:
                print(f"✓ {description} - Sucesso")
                time.sleep(self.action_delay)
                return True
            else:
                print(f"✗ {description} - Falhou (código: {result})")
                return False
                
        except Exception as e:
            print(f"✗ Erro ao executar {description}: {e}")
            return False
    
    def release_arms(self):
        """Libera/abaixa os braços para posição neutra"""
        return self.execute_action_safely("release arm", "Liberando braços (posição neutra)")
    
    def left_hand_up(self):
        """Levanta a mão esquerda"""
        # Nota: O SDK não tem uma ação específica para "left hand up"
        # Vamos usar "hands up" e depois simular o movimento individual
        print("⚠️  Simulando levantar mão esquerda (usando 'hands up' como aproximação)")
        return self.execute_action_safely("hands up", "Levantando mão esquerda")
    
    def right_hand_up(self):
        """Levanta a mão direita"""
        return self.execute_action_safely("right hand up", "Levantando mão direita")
    
    def run_movement_sequence(self):
        """Executa a sequência completa de movimentos"""
        print("\n" + "="*60)
        print("🚀 INICIANDO SEQUÊNCIA DE TESTE DE MOVIMENTOS DO BRAÇO")
        print("="*60)
        
        # Posição inicial - liberar braços
        print("\n📍 Fase 0: Posição inicial")
        if not self.release_arms():
            return False
        time.sleep(self.movement_delay)
        
        # Fase 1: Levantar mão esquerda
        print("\n📍 Fase 1: Levantar mão esquerda")
        if not self.left_hand_up():
            return False
        time.sleep(self.movement_delay)
        
        # Fase 2: Abaixar mão esquerda
        print("\n📍 Fase 2: Abaixar mão esquerda")
        if not self.release_arms():
            return False
        time.sleep(self.movement_delay)
        
        # Fase 3: Levantar mão direita
        print("\n📍 Fase 3: Levantar mão direita")
        if not self.right_hand_up():
            return False
        time.sleep(self.movement_delay)
        
        # Fase 4: Abaixar mão direita
        print("\n📍 Fase 4: Abaixar mão direita")
        if not self.release_arms():
            return False
        
        print("\n" + "="*60)
        print("✅ SEQUÊNCIA DE MOVIMENTOS CONCLUÍDA COM SUCESSO!")
        print("="*60)
        return True
    
    def show_available_actions(self):
        """Mostra as ações disponíveis no action_map"""
        print("\n📋 Ações disponíveis no SDK:")
        print("-" * 40)
        for action_name, action_id in action_map.items():
            print(f"  {action_name:<20} (ID: {action_id})")
        print("-" * 40)

def main():
    """Função principal"""
    # Verificar argumentos da linha de comando
    if len(sys.argv) < 2:
        print("❌ Uso incorreto!")
        print(f"Uso: python {sys.argv[0]} <interface_de_rede>")
        print("Exemplo: python test_arm_movements.py eth0")
        print("         python test_arm_movements.py wlan0")
        sys.exit(1)
    
    network_interface = sys.argv[1]
    
    print("🤖 TESTE DE MOVIMENTOS DO BRAÇO - ROBÔ G1 UNITREE")
    print(f"🌐 Interface de rede: {network_interface}")
    
    # Aviso de segurança
    print("\n⚠️  AVISO DE SEGURANÇA:")
    print("   • Certifique-se de que não há obstáculos ao redor do robô")
    print("   • Mantenha distância segura durante os movimentos")
    print("   • Tenha o botão de emergência à mão")
    
    try:
        input("\n🔄 Pressione Enter para continuar ou Ctrl+C para cancelar...")
    except KeyboardInterrupt:
        print("\n❌ Teste cancelado pelo usuário")
        sys.exit(0)
    
    try:
        # Inicializar o canal de comunicação
        print(f"\n🔧 Inicializando canal de comunicação ({network_interface})...")
        ChannelFactoryInitialize(0, network_interface)
        print("✓ Canal de comunicação inicializado")
        
        # Criar e inicializar o controlador de teste
        movement_test = G1ArmMovementTest()
        
        if not movement_test.initialize_client():
            print("❌ Falha na inicialização do cliente")
            sys.exit(1)
        
        # Mostrar ações disponíveis
        movement_test.show_available_actions()
        
        # Executar sequência de movimentos
        success = movement_test.run_movement_sequence()
        
        if success:
            print("\n🎉 Teste concluído com sucesso!")
            sys.exit(0)
        else:
            print("\n❌ Teste falhou durante a execução")
            sys.exit(1)
            
    except KeyboardInterrupt:
        print("\n\n⏹️  Teste interrompido pelo usuário")
        sys.exit(0)
    except Exception as e:
        print(f"\n❌ Erro inesperado: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()