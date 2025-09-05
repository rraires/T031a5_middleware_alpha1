#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Script de Demonstração - Todos os Testes de Movimento do Braço

Este script demonstra todos os tipos de controle disponíveis:
1. Controle de alto nível simples
2. Controle de alto nível completo
3. Controle de baixo nível preciso

Uso: python demo_all_scripts.py <interface_de_rede>
"""

import sys
import time
import subprocess
import os

def run_script(script_name, network_interface):
    """Executa um script e retorna o resultado"""
    try:
        print(f"\n{'='*60}")
        print(f"🚀 EXECUTANDO: {script_name}")
        print(f"{'='*60}")
        
        # Verificar se o arquivo existe
        if not os.path.exists(script_name):
            print(f"❌ Erro: Arquivo {script_name} não encontrado")
            return False
        
        # Executar o script
        result = subprocess.run(
            [sys.executable, script_name, network_interface],
            capture_output=True,
            text=True,
            timeout=30  # Timeout de 30 segundos
        )
        
        if result.returncode == 0:
            print(f"✅ {script_name} executado com sucesso")
            if result.stdout:
                print("📄 Saída:")
                print(result.stdout)
            return True
        else:
            print(f"❌ {script_name} falhou (código: {result.returncode})")
            if result.stderr:
                print("📄 Erro:")
                print(result.stderr)
            return False
            
    except subprocess.TimeoutExpired:
        print(f"⏰ {script_name} excedeu o tempo limite (30s)")
        return False
    except Exception as e:
        print(f"❌ Erro ao executar {script_name}: {e}")
        return False

def show_menu():
    """Mostra o menu de opções"""
    print("\n" + "="*60)
    print("🤖 DEMONSTRAÇÃO DE SCRIPTS DE MOVIMENTO DO BRAÇO G1")
    print("="*60)
    print("\nEscolha o tipo de demonstração:")
    print("\n1. 🟢 Controle Simples (Alto Nível)")
    print("   - Execução rápida")
    print("   - Ações predefinidas")
    print("   - Mais seguro")
    print("\n2. 🔵 Controle Completo (Alto Nível)")
    print("   - Logs detalhados")
    print("   - Verificações de segurança")
    print("   - Tratamento de erros")
    print("\n3. 🟡 Controle Preciso (Baixo Nível) ⭐")
    print("   - Movimentos individuais")
    print("   - Controle motor por motor")
    print("   - Interpolação suave")
    print("\n4. 🔄 Executar Todos em Sequência")
    print("   - Demonstração completa")
    print("   - Comparação de métodos")
    print("\n5. ❌ Sair")
    print("\n" + "-"*60)

def get_user_choice():
    """Obtém a escolha do usuário"""
    while True:
        try:
            choice = input("\nDigite sua escolha (1-5): ").strip()
            if choice in ['1', '2', '3', '4', '5']:
                return int(choice)
            else:
                print("❌ Escolha inválida. Digite um número de 1 a 5.")
        except KeyboardInterrupt:
            print("\n\n👋 Saindo...")
            sys.exit(0)
        except Exception:
            print("❌ Entrada inválida. Digite um número de 1 a 5.")

def main():
    """Função principal"""
    # Verificar argumentos
    if len(sys.argv) < 2:
        print("❌ Uso incorreto!")
        print(f"Uso: python {sys.argv[0]} <interface_de_rede>")
        print("Exemplo: python demo_all_scripts.py eth0")
        sys.exit(1)
    
    network_interface = sys.argv[1]
    
    # Scripts disponíveis
    scripts = {
        1: "simple_arm_test.py",
        2: "test_arm_movements.py", 
        3: "precise_arm_test.py"
    }
    
    print(f"🌐 Interface de rede configurada: {network_interface}")
    
    # Aviso de segurança geral
    print("\n⚠️  AVISO DE SEGURANÇA GERAL:")
    print("   • Certifique-se de que o robô G1 está ligado e operacional")
    print("   • Remova todos os obstáculos ao redor do robô")
    print("   • Mantenha distância segura durante os testes")
    print("   • Tenha o botão de emergência sempre à mão")
    print("   • Interrompa imediatamente se algo parecer errado")
    
    try:
        input("\n🔄 Pressione Enter para continuar ou Ctrl+C para cancelar...")
    except KeyboardInterrupt:
        print("\n❌ Demonstração cancelada pelo usuário")
        sys.exit(0)
    
    while True:
        show_menu()
        choice = get_user_choice()
        
        if choice == 5:
            print("\n👋 Encerrando demonstração. Obrigado!")
            break
        elif choice == 4:
            # Executar todos os scripts
            print("\n🔄 EXECUTANDO TODOS OS SCRIPTS EM SEQUÊNCIA")
            print("⏱️  Isso pode levar alguns minutos...")
            
            success_count = 0
            for script_num in [1, 2, 3]:
                script_name = scripts[script_num]
                print(f"\n⏳ Aguardando 3 segundos antes do próximo teste...")
                time.sleep(3)
                
                if run_script(script_name, network_interface):
                    success_count += 1
                
                print(f"\n⏸️  Pausa de 5 segundos entre testes...")
                time.sleep(5)
            
            print(f"\n📊 RESUMO DA EXECUÇÃO:")
            print(f"   ✅ Scripts executados com sucesso: {success_count}/3")
            print(f"   ❌ Scripts com falha: {3 - success_count}/3")
            
        elif choice in scripts:
            # Executar script específico
            script_name = scripts[choice]
            
            print(f"\n⚠️  Você está prestes a executar: {script_name}")
            if choice == 3:
                print("   🟡 ATENÇÃO: Este é um controle de baixo nível!")
                print("   🟡 Certifique-se de que entende os riscos!")
            
            try:
                confirm = input("\n🤔 Deseja continuar? (s/N): ").strip().lower()
                if confirm in ['s', 'sim', 'y', 'yes']:
                    run_script(script_name, network_interface)
                else:
                    print("❌ Execução cancelada")
            except KeyboardInterrupt:
                print("\n❌ Execução cancelada pelo usuário")
        
        # Pausa antes de mostrar o menu novamente
        if choice != 5:
            try:
                input("\n⏸️  Pressione Enter para voltar ao menu...")
            except KeyboardInterrupt:
                print("\n👋 Encerrando demonstração...")
                break

if __name__ == "__main__":
    main()