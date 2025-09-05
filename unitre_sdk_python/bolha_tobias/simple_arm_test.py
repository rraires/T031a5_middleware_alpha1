#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Script Simples de Teste de Movimentos do Braço - Robô G1

Sequência de movimentos:
1. Subir mão esquerda
2. Abaixar mão esquerda  
3. Subir mão direita
4. Abaixar mão direita

Uso: python simple_arm_test.py <interface_de_rede>
"""

import time
import sys
from unitree_sdk2py.core.channel import ChannelFactoryInitialize
from unitree_sdk2py.g1.arm.g1_arm_action_client import G1ArmActionClient
from unitree_sdk2py.g1.arm.g1_arm_action_client import action_map

def main():
    # Verificar argumentos
    if len(sys.argv) < 2:
        print(f"Uso: python {sys.argv[0]} <interface_de_rede>")
        print("Exemplo: python simple_arm_test.py eth0")
        sys.exit(1)
    
    network_interface = sys.argv[1]
    
    print("🤖 Teste Simples de Movimentos do Braço G1")
    print("⚠️  AVISO: Certifique-se de que não há obstáculos ao redor do robô!")
    
    try:
        input("Pressione Enter para continuar...")
    except KeyboardInterrupt:
        print("\nTeste cancelado.")
        sys.exit(0)
    
    try:
        # Inicializar comunicação
        print(f"Inicializando comunicação ({network_interface})...")
        ChannelFactoryInitialize(0, network_interface)
        
        # Inicializar cliente do braço
        print("Inicializando cliente do braço...")
        arm_client = G1ArmActionClient()
        arm_client.SetTimeout(10.0)
        arm_client.Init()
        
        print("\n🚀 Iniciando sequência de movimentos...\n")
        
        # Posição inicial - liberar braços
        print("0. Posição inicial (liberar braços)")
        arm_client.ExecuteAction(action_map["release arm"])
        time.sleep(2)
        
        # 1. Subir mão esquerda (usando "hands up" como aproximação)
        print("1. Subindo mão esquerda...")
        # Nota: O SDK não tem ação específica para mão esquerda individual
        # Usando "hands up" como melhor aproximação disponível
        arm_client.ExecuteAction(action_map["hands up"])
        time.sleep(3)
        
        # 2. Abaixar mão esquerda
        print("2. Abaixando mão esquerda...")
        arm_client.ExecuteAction(action_map["release arm"])
        time.sleep(3)
        
        # 3. Subir mão direita
        print("3. Subindo mão direita...")
        arm_client.ExecuteAction(action_map["right hand up"])
        time.sleep(3)
        
        # 4. Abaixar mão direita
        print("4. Abaixando mão direita...")
        arm_client.ExecuteAction(action_map["release arm"])
        time.sleep(2)
        
        print("\n✅ Sequência de movimentos concluída!")
        
        # Mostrar ações disponíveis para referência
        print("\n📋 Ações disponíveis no SDK:")
        for action_name, action_id in action_map.items():
            print(f"  - {action_name} (ID: {action_id})")
            
    except KeyboardInterrupt:
        print("\n⏹️  Teste interrompido pelo usuário")
    except Exception as e:
        print(f"\n❌ Erro: {e}")
        print("\nVerifique se:")
        print("- O robô está ligado e conectado")
        print("- A interface de rede está correta")
        print("- O SDK está instalado corretamente")

if __name__ == "__main__":
    main()