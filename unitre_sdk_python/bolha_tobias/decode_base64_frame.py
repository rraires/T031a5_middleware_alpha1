#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Script para Decodificar Frames Base64 - Robô G1

Este script demonstra como decodificar os arquivos base64 gerados
pelo script de teste de câmera e convertê-los de volta para imagens.

Uso:
    python decode_base64_frame.py <arquivo_base64.txt>
    
Exemplo:
    python decode_base64_frame.py camera_captures/camera_0_frame_base64_20241201_143022.txt

Autor: Script de Teste G1
Data: 2024
"""

import base64
import cv2
import numpy as np
import sys
import os

def decode_base64_frame(base64_file_path: str) -> bool:
    """
    Decodifica um arquivo base64 e salva como imagem
    
    Args:
        base64_file_path: Caminho para o arquivo .txt com dados base64
        
    Returns:
        bool: True se bem-sucedido, False caso contrário
    """
    if not os.path.exists(base64_file_path):
        print(f"❌ Arquivo não encontrado: {base64_file_path}")
        return False
    
    try:
        print(f"📖 Lendo arquivo: {base64_file_path}")
        
        # Lê o arquivo
        with open(base64_file_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        # Extrai apenas os dados base64 (remove comentários)
        lines = content.split('\n')
        base64_data = ''
        
        for line in lines:
            if not line.startswith('#') and line.strip():
                base64_data += line.strip()
        
        if not base64_data:
            print("❌ Nenhum dado base64 encontrado no arquivo")
            return False
        
        print(f"📊 Tamanho dos dados base64: {len(base64_data)} caracteres")
        
        # Decodifica base64
        img_data = base64.b64decode(base64_data)
        print(f"📊 Tamanho dos dados decodificados: {len(img_data)} bytes")
        
        # Converte para array numpy
        nparr = np.frombuffer(img_data, np.uint8)
        
        # Decodifica imagem
        img = cv2.imdecode(nparr, cv2.IMREAD_COLOR)
        
        if img is None:
            print("❌ Erro ao decodificar imagem")
            return False
        
        print(f"📐 Resolução da imagem: {img.shape[1]}x{img.shape[0]}")
        
        # Gera nome do arquivo de saída
        base_name = os.path.splitext(os.path.basename(base64_file_path))[0]
        output_file = f"{base_name}_decoded.jpg"
        output_path = os.path.join(os.path.dirname(base64_file_path), output_file)
        
        # Salva imagem decodificada
        cv2.imwrite(output_path, img)
        print(f"✅ Imagem decodificada salva: {output_path}")
        
        # Mostra a imagem (opcional)
        print("\n🖼️  Pressione qualquer tecla para fechar a visualização...")
        cv2.imshow('Imagem Decodificada', img)
        cv2.waitKey(0)
        cv2.destroyAllWindows()
        
        return True
        
    except Exception as e:
        print(f"❌ Erro ao decodificar: {e}")
        return False

def list_base64_files(directory: str = "camera_captures") -> list:
    """
    Lista todos os arquivos base64 no diretório especificado
    
    Args:
        directory: Diretório para procurar arquivos
        
    Returns:
        list: Lista de arquivos base64 encontrados
    """
    if not os.path.exists(directory):
        return []
    
    base64_files = []
    for file in os.listdir(directory):
        if file.endswith('_base64.txt'):
            base64_files.append(os.path.join(directory, file))
    
    return sorted(base64_files)

def main():
    """
    Função principal do script
    """
    print("="*60)
    print("🔓 DECODIFICADOR DE FRAMES BASE64 - ROBÔ G1")
    print("="*60)
    
    # Verifica argumentos da linha de comando
    if len(sys.argv) > 1:
        file_path = sys.argv[1]
        print(f"\n📁 Arquivo especificado: {file_path}")
        
        if decode_base64_frame(file_path):
            print("\n✅ Decodificação concluída com sucesso!")
        else:
            print("\n❌ Falha na decodificação")
    else:
        # Modo interativo - lista arquivos disponíveis
        print("\n🔍 Procurando arquivos base64...")
        
        base64_files = list_base64_files()
        
        if not base64_files:
            print("❌ Nenhum arquivo base64 encontrado no diretório 'camera_captures'")
            print("\n💡 Dica: Execute primeiro o script de teste de câmera e use a opção 'b' ou menu '4'")
            return
        
        print(f"\n📋 Arquivos base64 encontrados ({len(base64_files)}):")
        for i, file_path in enumerate(base64_files, 1):
            file_name = os.path.basename(file_path)
            file_size = os.path.getsize(file_path)
            print(f"  {i}. {file_name} ({file_size:,} bytes)")
        
        try:
            choice = input(f"\nEscolha um arquivo (1-{len(base64_files)}) ou 'q' para sair: ").strip()
            
            if choice.lower() == 'q':
                print("👋 Saindo...")
                return
            
            file_index = int(choice) - 1
            
            if 0 <= file_index < len(base64_files):
                selected_file = base64_files[file_index]
                print(f"\n📁 Arquivo selecionado: {os.path.basename(selected_file)}")
                
                if decode_base64_frame(selected_file):
                    print("\n✅ Decodificação concluída com sucesso!")
                else:
                    print("\n❌ Falha na decodificação")
            else:
                print("❌ Opção inválida")
                
        except ValueError:
            print("❌ Entrada inválida")
        except KeyboardInterrupt:
            print("\n\n⚠️  Interrompido pelo usuário")
    
    print("\n✓ Script finalizado")

if __name__ == "__main__":
    # Verifica se OpenCV está instalado
    try:
        import cv2
        print(f"✓ OpenCV versão: {cv2.__version__}")
    except ImportError:
        print("❌ OpenCV não está instalado. Execute: pip install opencv-python")
        sys.exit(1)
    
    main()