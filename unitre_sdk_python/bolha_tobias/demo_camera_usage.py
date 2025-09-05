#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Demonstração de Uso dos Scripts de Câmera - Robô G1

Este script demonstra como usar programaticamente as funcionalidades
dos scripts de teste de câmera.

Uso:
    python demo_camera_usage.py
"""

import sys
import os
import time

# Adiciona o diretório atual ao path para importar os módulos
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

try:
    from camera_test import CameraManager
    import cv2
except ImportError as e:
    print(f"❌ Erro de importação: {e}")
    print("Certifique-se de que o OpenCV está instalado: pip install opencv-python")
    sys.exit(1)

def detect_cameras():
    """Detecta câmeras disponíveis incluindo Intel RealSense no Linux com tratamento robusto de erros"""
    cameras = []
    failed_devices = []
    timeout_devices = []
    
    # Detecta o sistema operacional
    import platform
    if platform.system() == 'Linux':
        print("🔍 Detectando câmeras no Linux...")
        
        # Verifica dispositivos /dev/video0 até /dev/video11
        import os
        for i in range(12):
            device_path = f"/dev/video{i}"
            
            if os.path.exists(device_path):
                print(f"📹 Testando {device_path}...", end=" ")
                
                try:
                    # Timeout para evitar travamentos
                    import signal
                    
                    def timeout_handler(signum, frame):
                        raise TimeoutError("Timeout ao abrir câmera")
                    
                    # Configurar timeout de 5 segundos
                    signal.signal(signal.SIGALRM, timeout_handler)
                    signal.alarm(5)
                    
                    try:
                        cap = cv2.VideoCapture(i)
                        signal.alarm(0)  # Cancelar timeout
                        
                        if cap.isOpened():
                            try:
                                # Tentar capturar um frame com timeout
                                signal.alarm(3)  # 3 segundos para captura
                                ret, frame = cap.read()
                                signal.alarm(0)
                                
                                if ret and frame is not None:
                                    width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
                                    height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
                                    fps = cap.get(cv2.CAP_PROP_FPS)
                                    
                                    # Verifica se é RealSense
                                    is_realsense = check_realsense_device(i)
                                    
                                    # Verificar qualidade do frame
                                    frame_status = "OK"
                                    if frame.size == 0:
                                        frame_status = "Frame vazio"
                                    elif len(frame.shape) != 3:
                                        frame_status = "Formato inválido"
                                    elif frame.mean() < 5:
                                        frame_status = "Imagem muito escura"
                                    
                                    cameras.append({
                                        'id': i,
                                        'width': width if width > 0 else 640,
                                        'height': height if height > 0 else 480,
                                        'fps': fps if fps > 0 else 30.0,
                                        'device_path': device_path,
                                        'is_realsense': is_realsense,
                                        'status': frame_status
                                    })
                                    
                                    device_type = "🔍 RealSense" if is_realsense else "📷 USB"
                                    print(f"✅ {device_type} ({width}x{height} @ {fps:.1f}fps)")
                                else:
                                    print(f"❌ Sem sinal")
                                    failed_devices.append((device_path, "Não conseguiu capturar frame"))
                            
                            except Exception as frame_error:
                                print(f"⚠️ Erro na captura: {frame_error}")
                                failed_devices.append((device_path, f"Erro na captura: {frame_error}"))
                            
                            finally:
                                cap.release()
                        else:
                            print(f"❌ Falha ao abrir")
                            failed_devices.append((device_path, "Não foi possível abrir o dispositivo"))
                    
                    except TimeoutError as te:
                        print(f"⏰ Timeout")
                        timeout_devices.append((device_path, str(te)))
                        signal.alarm(0)
                    
                    except Exception as open_error:
                        print(f"❌ Erro: {open_error}")
                        failed_devices.append((device_path, str(open_error)))
                        signal.alarm(0)
                
                except Exception as e:
                    print(f"💥 Erro crítico: {e}")
                    failed_devices.append((device_path, f"Erro crítico: {e}"))
                    continue
    else:
        print("🔍 Detectando câmeras...")
        
        # Para outros sistemas
        for i in range(10):
            try:
                print(f"📹 Testando Câmera {i}...", end=" ")
                
                cap = cv2.VideoCapture(i)
                if cap.isOpened():
                    try:
                        ret, frame = cap.read()
                        if ret and frame is not None:
                            width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
                            height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
                            fps = cap.get(cv2.CAP_PROP_FPS)
                            
                            # Verifica se é RealSense
                            is_realsense = check_realsense_device(i)
                            
                            # Verificar qualidade do frame
                            frame_status = "OK"
                            if frame.size == 0:
                                frame_status = "Frame vazio"
                            elif len(frame.shape) != 3:
                                frame_status = "Formato inválido"
                            
                            cameras.append({
                                'id': i,
                                'width': width if width > 0 else 640,
                                'height': height if height > 0 else 480,
                                'fps': fps if fps > 0 else 30.0,
                                'device_path': f'Camera {i}',
                                'is_realsense': is_realsense,
                                'status': frame_status
                            })
                            
                            device_type = "🔍 RealSense" if is_realsense else "📷 USB"
                            print(f"✅ {device_type} ({width}x{height} @ {fps:.1f}fps)")
                        else:
                            print(f"❌ Sem sinal")
                            failed_devices.append((f"Camera {i}", "Não conseguiu capturar frame"))
                    
                    except Exception as frame_error:
                        print(f"⚠️ Erro: {frame_error}")
                        failed_devices.append((f"Camera {i}", str(frame_error)))
                    
                    finally:
                        cap.release()
                else:
                    # Não imprime erro para câmeras não existentes
                    continue
            except Exception:
                continue
    
    # Relatório final
    realsense_count = sum(1 for cam in cameras if cam['is_realsense'])
    working_cameras = sum(1 for cam in cameras if cam.get('status', 'OK') == 'OK')
    
    print(f"\n📊 Resumo da detecção:")
    print(f"   📹 Total de câmeras detectadas: {len(cameras)}")
    print(f"   ✅ Câmeras funcionando: {working_cameras}")
    print(f"   🔍 Câmeras RealSense: {realsense_count}")
    
    if failed_devices:
        print(f"   ❌ Dispositivos com falha: {len(failed_devices)}")
        for device, error in failed_devices:
            print(f"      • {device}: {error}")
    
    if timeout_devices:
        print(f"   ⏰ Dispositivos com timeout: {len(timeout_devices)}")
        for device, error in timeout_devices:
            print(f"      • {device}: {error}")
    
    return [cam['id'] for cam in cameras]

def check_realsense_device(camera_id):
    """Verifica se um dispositivo é Intel RealSense (versão simplificada)"""
    try:
        import platform
        if platform.system() == 'Linux':
            # Verifica o nome do dispositivo no Linux
            try:
                with open(f'/sys/class/video4linux/video{camera_id}/name', 'r') as f:
                    device_name = f.read().strip().lower()
                    return 'realsense' in device_name or 'intel' in device_name
            except:
                pass
        
        # Método alternativo: testa características da câmera
        cap = cv2.VideoCapture(camera_id)
        if cap.isOpened():
            # Testa se suporta múltiplas resoluções (característica comum do RealSense)
            original_width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
            original_height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
            
            # Testa resolução 640x480
            cap.set(cv2.CAP_PROP_FRAME_WIDTH, 640)
            cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 480)
            test_width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
            test_height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
            
            cap.release()
            
            # Se conseguiu mudar a resolução, pode ser RealSense
            return (test_width == 640 and test_height == 480) and (original_width != 640 or original_height != 480)
        
        return False
    except Exception:
        return False

def demo_camera_detection():
    """Demonstra detecção de câmeras"""
    print("\n" + "="*50)
    print("📹 DEMONSTRAÇÃO: DETECÇÃO DE CÂMERAS")
    print("="*50)
    
    camera_manager = CameraManager()
    cameras = camera_manager.detect_cameras()
    
    if cameras:
        print(f"\n✅ Sucesso! {len(cameras)} câmera(s) detectada(s): {cameras}")
        return cameras
    else:
        print("\n❌ Nenhuma câmera detectada")
        return []

def demo_camera_info(cameras):
    """Demonstra obtenção de informações das câmeras"""
    if not cameras:
        return
    
    print("\n" + "="*50)
    print("📊 DEMONSTRAÇÃO: INFORMAÇÕES DAS CÂMERAS")
    print("="*50)
    
    camera_manager = CameraManager()
    
    for cam_id in cameras:
        print(f"\n--- Câmera {cam_id} ---")
        info = camera_manager.get_camera_info(cam_id)
        
        if "error" not in info:
            print(f"Resolução: {info['width']}x{info['height']}")
            print(f"FPS: {info['fps']}")
            print(f"Backend: {info['backend']}")
            print(f"Brilho: {info['brightness']}")
            print(f"Contraste: {info['contrast']}")
        else:
            print(f"❌ {info['error']}")

def demo_quick_capture(cameras):
    """Demonstra captura rápida de uma imagem"""
    if not cameras:
        return
    
    print("\n" + "="*50)
    print("📸 DEMONSTRAÇÃO: CAPTURA RÁPIDA")
    print("="*50)
    
    camera_id = cameras[0]
    print(f"\n📷 Capturando imagem da câmera {camera_id}...")
    
    cap = cv2.VideoCapture(camera_id)
    if cap.isOpened():
        ret, frame = cap.read()
        if ret:
            # Salva a imagem
            filename = f"demo_capture_camera_{camera_id}.jpg"
            cv2.imwrite(filename, frame)
            print(f"✅ Imagem salva: {filename}")
            
            # Mostra informações do frame
            height, width = frame.shape[:2]
            print(f"📐 Dimensões: {width}x{height}")
            print(f"📊 Canais: {frame.shape[2] if len(frame.shape) > 2 else 1}")
        else:
            print("❌ Erro na captura")
        cap.release()
    else:
        print(f"❌ Não foi possível abrir câmera {camera_id}")

def demo_automated_test(cameras):
    """Demonstra teste automatizado de câmera"""
    if not cameras:
        return
    
    print("\n" + "="*50)
    print("🤖 DEMONSTRAÇÃO: TESTE AUTOMATIZADO")
    print("="*50)
    
    camera_id = cameras[0]
    print(f"\n🎥 Testando câmera {camera_id} por 3 segundos...")
    
    cap = cv2.VideoCapture(camera_id)
    if not cap.isOpened():
        print(f"❌ Erro ao abrir câmera {camera_id}")
        return
    
    start_time = time.time()
    frame_count = 0
    
    while time.time() - start_time < 3:  # Testa por 3 segundos
        ret, frame = cap.read()
        if ret:
            frame_count += 1
        else:
            print("❌ Erro na captura do frame")
            break
        
        # Pequena pausa para não sobrecarregar
        time.sleep(0.033)  # ~30 FPS
    
    cap.release()
    
    elapsed = time.time() - start_time
    fps = frame_count / elapsed if elapsed > 0 else 0
    
    print(f"✅ Teste concluído:")
    print(f"   📊 Frames capturados: {frame_count}")
    print(f"   ⏱️  Tempo decorrido: {elapsed:.1f}s")
    print(f"   🎯 FPS médio: {fps:.1f}")

def demo_diagnostics(cameras):
    """Demonstra diagnósticos automatizados"""
    if not cameras:
        return
    
    print("\n" + "="*50)
    print("🔧 DEMONSTRAÇÃO: DIAGNÓSTICOS AUTOMATIZADOS")
    print("="*50)
    
    camera_manager = CameraManager()
    diagnostics = camera_manager.run_diagnostics(cameras)
    
    print(f"\n📋 Relatório gerado com {len(diagnostics)} câmera(s)")

def show_usage_examples():
    """Mostra exemplos de uso dos scripts"""
    print("\n" + "="*50)
    print("📚 EXEMPLOS DE USO DOS SCRIPTS")
    print("="*50)
    
    examples = [
        {
            "title": "Teste Rápido",
            "command": "python simple_camera_test.py",
            "description": "Teste básico da primeira câmera encontrada"
        },
        {
            "title": "Menu Interativo",
            "command": "python camera_test.py",
            "description": "Interface completa com múltiplas opções"
        },
        {
            "title": "Demonstração",
            "command": "python demo_camera_usage.py",
            "description": "Este script - demonstração automatizada"
        }
    ]
    
    for i, example in enumerate(examples, 1):
        print(f"\n{i}. {example['title']}")
        print(f"   Comando: {example['command']}")
        print(f"   Descrição: {example['description']}")

def main():
    """Função principal da demonstração"""
    print("="*60)
    print("🎬 DEMONSTRAÇÃO DOS SCRIPTS DE CÂMERA - ROBÔ G1")
    print("="*60)
    
    try:
        # Verifica OpenCV
        print(f"✓ OpenCV versão: {cv2.__version__}")
        
        # 1. Detecta câmeras
        cameras = demo_camera_detection()
        
        if not cameras:
            print("\n⚠️  Sem câmeras disponíveis para demonstração")
            print("\n💡 Dicas:")
            print("   - Conecte uma câmera USB")
            print("   - Verifique se a câmera não está em uso")
            print("   - Teste com outros aplicativos primeiro")
            return
        
        # 2. Mostra informações das câmeras
        demo_camera_info(cameras)
        
        # 3. Captura rápida
        demo_quick_capture(cameras)
        
        # 4. Teste automatizado
        demo_automated_test(cameras)
        
        # 5. Diagnósticos
        demo_diagnostics(cameras)
        
        # 6. Exemplos de uso
        show_usage_examples()
        
        print("\n" + "="*60)
        print("✅ DEMONSTRAÇÃO CONCLUÍDA COM SUCESSO!")
        print("="*60)
        
        print("\n📝 Próximos passos:")
        print("   1. Execute 'python simple_camera_test.py' para teste básico")
        print("   2. Execute 'python camera_test.py' para interface completa")
        print("   3. Consulte 'README_CAMERA_TEST.md' para documentação")
        
    except KeyboardInterrupt:
        print("\n\n⚠️  Demonstração interrompida pelo usuário")
    except Exception as e:
        print(f"\n❌ Erro durante demonstração: {e}")
        print("\n🔧 Verifique:")
        print("   - Se o OpenCV está instalado corretamente")
        print("   - Se as câmeras estão funcionando")
        print("   - Se não há conflitos com outros aplicativos")
    finally:
        # Limpa recursos do OpenCV
        cv2.destroyAllWindows()
        print("\n👋 Demonstração finalizada")

if __name__ == "__main__":
    main()