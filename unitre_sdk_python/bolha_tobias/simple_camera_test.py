#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Teste Simples de Câmera - Robô G1

Script simplificado para teste rápido de câmera.
Use este script para verificação básica de funcionamento.

Uso:
    python simple_camera_test.py

Controles:
    - 'q': Sair
    - 's': Salvar imagem
    - 'ESC': Sair
"""

import cv2
import datetime
import os

def test_camera(camera_id=0):
    """Teste simples de câmera"""
    print(f"🔍 Testando câmera {camera_id}...")
    
    # Tenta abrir a câmera
    cap = cv2.VideoCapture(camera_id)
    
    if not cap.isOpened():
        print(f"❌ Erro: Não foi possível abrir a câmera {camera_id}")
        return False
    
    # Configura resolução
    cap.set(cv2.CAP_PROP_FRAME_WIDTH, 640)
    cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 480)
    
    print("✓ Câmera aberta com sucesso!")
    print("📹 Pressione 'q' para sair, 's' para salvar imagem")
    
    frame_count = 0
    
    while True:
        ret, frame = cap.read()
        
        if not ret:
            print("❌ Erro na captura do frame")
            break
        
        frame_count += 1
        
        # Adiciona informações no frame
        timestamp = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        cv2.putText(frame, f"Frame: {frame_count}", (10, 30), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 255, 0), 2)
        cv2.putText(frame, timestamp, (10, 60), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (255, 255, 255), 1)
        
        # Mostra o frame
        cv2.imshow('Camera Test - G1', frame)
        
        # Verifica teclas pressionadas
        key = cv2.waitKey(1) & 0xFF
        
        if key == ord('q') or key == 27:  # 'q' ou ESC
            break
        elif key == ord('s'):  # Salvar imagem
            save_image(frame, camera_id)
    
    # Libera recursos
    cap.release()
    cv2.destroyAllWindows()
    
    print(f"✓ Teste concluído. Total de frames: {frame_count}")
    return True

def save_image(frame, camera_id):
    """Salva uma imagem com timestamp"""
    # Cria diretório se não existir
    if not os.path.exists("captures"):
        os.makedirs("captures")
    
    # Nome do arquivo com timestamp
    timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
    filename = f"captures/camera_{camera_id}_{timestamp}.jpg"
    
    # Salva a imagem
    cv2.imwrite(filename, frame)
    print(f"📸 Imagem salva: {filename}")

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
    
    return cameras

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

def main():
    """Função principal"""
    print("="*50)
    print("🤖 TESTE SIMPLES DE CÂMERA - ROBÔ G1")
    print("="*50)
    
    # Verifica OpenCV
    try:
        print(f"✓ OpenCV versão: {cv2.__version__}")
    except:
        print("❌ Erro com OpenCV")
        return
    
    # Detecta câmeras
    cameras = detect_cameras()
    
    if not cameras:
        print("❌ Nenhuma câmera encontrada")
        return
    
    print(f"\n📋 Câmeras disponíveis: {cameras}")
    
    # Testa a primeira câmera encontrada
    camera_id = cameras[0]
    print(f"\n🎥 Testando câmera {camera_id}...")
    
    test_camera(camera_id)

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n⚠️  Teste interrompido pelo usuário")
    except Exception as e:
        print(f"❌ Erro: {e}")
    finally:
        cv2.destroyAllWindows()
        print("\n👋 Finalizando...")