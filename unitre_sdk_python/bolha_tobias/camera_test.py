#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Script de Teste de Câmera para Robô G1

Este script testa câmeras USB ou integradas disponíveis no sistema
usando OpenCV. Como o G1 não possui APIs específicas de vídeo no SDK,
este script funciona independentemente mas pode ser integrado futuramente.

Funcionalidades:
- Detecção automática de câmeras disponíveis
- Captura de imagens e vídeo
- Preview em tempo real
- Salvamento com timestamp
- Diagnósticos de resolução e FPS
- Teste de múltiplas câmeras

Autor: Script de Teste G1
Data: 2024
"""

import cv2
import os
import time
import datetime
import numpy as np
from typing import List, Tuple, Optional
import threading
import json
import base64

class CameraManager:
    """Gerenciador de câmeras para teste e diagnóstico"""
    
    def __init__(self):
        self.cameras = {}
        self.active_cameras = []
        self.capture_directory = "camera_captures"
        self.create_capture_directory()
    
    def _check_realsense_device(self, camera_id):
        """Verifica se um dispositivo é Intel RealSense usando múltiplos métodos"""
        try:
            import platform
            import subprocess
            import os
            
            if platform.system() == 'Linux':
                # Método 1: Verifica usando v4l2-ctl (mais confiável)
                try:
                    result = subprocess.run(['v4l2-ctl', '--device', f'/dev/video{camera_id}', '--info'], 
                                          capture_output=True, text=True, timeout=5)
                    if result.returncode == 0:
                        output_lower = result.stdout.lower()
                        if any(keyword in output_lower for keyword in ['realsense', 'intel', 'depth']):
                            return True
                except (subprocess.TimeoutExpired, FileNotFoundError, subprocess.SubprocessError):
                    pass
                
                # Método 2: Verifica o nome do dispositivo no sysfs
                try:
                    device_name_path = f'/sys/class/video4linux/video{camera_id}/name'
                    if os.path.exists(device_name_path):
                        with open(device_name_path, 'r') as f:
                            device_name = f.read().strip().lower()
                            if any(keyword in device_name for keyword in ['realsense', 'intel', 'depth']):
                                return True
                except (IOError, OSError):
                    pass
                
                # Método 3: Verifica informações do dispositivo USB
                try:
                    # Procura por dispositivos Intel RealSense via lsusb
                    result = subprocess.run(['lsusb'], capture_output=True, text=True, timeout=5)
                    if result.returncode == 0:
                        output_lower = result.stdout.lower()
                        # IDs de vendor conhecidos da Intel para RealSense
                        intel_ids = ['8086:', '045e:']  # Intel e Microsoft (alguns RealSense)
                        if any(vid in output_lower for vid in intel_ids) and 'realsense' in output_lower:
                            return True
                except (subprocess.TimeoutExpired, FileNotFoundError, subprocess.SubprocessError):
                    pass
            
            # Método 4: Testa características específicas da câmera (funciona em todos os OS)
            cap = cv2.VideoCapture(camera_id)
            if cap.isOpened():
                try:
                    # Salva configurações originais
                    original_width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
                    original_height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
                    original_fps = cap.get(cv2.CAP_PROP_FPS)
                    
                    # Testa múltiplas resoluções típicas do RealSense
                    test_resolutions = [(640, 480), (848, 480), (1280, 720), (1920, 1080)]
                    successful_changes = 0
                    
                    for width, height in test_resolutions:
                        cap.set(cv2.CAP_PROP_FRAME_WIDTH, width)
                        cap.set(cv2.CAP_PROP_FRAME_HEIGHT, height)
                        
                        actual_width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
                        actual_height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
                        
                        if actual_width == width and actual_height == height:
                            successful_changes += 1
                    
                    cap.release()
                    
                    # RealSense geralmente suporta múltiplas resoluções
                    return successful_changes >= 2
                    
                except Exception:
                    cap.release()
                    return False
            
            return False
            
        except Exception as e:
            print(f"⚠️  Erro ao verificar RealSense para câmera {camera_id}: {e}")
            return False
        
    def create_capture_directory(self):
        """Cria diretório para salvar capturas"""
        if not os.path.exists(self.capture_directory):
            os.makedirs(self.capture_directory)
            print(f"✓ Diretório criado: {self.capture_directory}")
    
    def detect_cameras(self, max_cameras: int = 12) -> List[dict]:
        """Detecta câmeras disponíveis no sistema com tratamento robusto de erros"""
        print("🔍 Detectando câmeras disponíveis...")
        available_cameras = []
        failed_devices = []
        timeout_devices = []
        
        # Para Linux, testa dispositivos /dev/video0 a /dev/video11
        import platform
        if platform.system() == 'Linux':
            print("🐧 Sistema Linux detectado - verificando dispositivos /dev/video*")
            
            # Verifica se os dispositivos existem
            import os
            video_devices = []
            for i in range(12):  # /dev/video0 a /dev/video11
                device_path = f"/dev/video{i}"
                if os.path.exists(device_path):
                    video_devices.append(i)
                    print(f"📹 Dispositivo encontrado: {device_path}")
            
            # Testa cada dispositivo encontrado
            for i in video_devices:
                device_path = f"/dev/video{i}"
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
                                # Verificar se consegue ler propriedades básicas
                                width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
                                height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
                                fps = cap.get(cv2.CAP_PROP_FPS)
                                
                                # Verifica se é Intel RealSense
                                is_realsense = self._check_realsense_device(i)
                                device_type = "Intel RealSense" if is_realsense else "Câmera USB"
                                
                                # Tentar capturar um frame com timeout
                                signal.alarm(3)  # 3 segundos para captura
                                ret, frame = cap.read()
                                signal.alarm(0)
                                
                                # Verificar qualidade do frame
                                frame_quality = "OK"
                                if ret and frame is not None:
                                    if frame.size == 0:
                                        frame_quality = "Frame vazio"
                                    elif len(frame.shape) != 3:
                                        frame_quality = "Formato inválido"
                                    else:
                                        # Verificar se não é apenas preto
                                        if frame.mean() < 5:
                                            frame_quality = "Imagem muito escura"
                                else:
                                    frame_quality = "Sem sinal"
                                
                                camera_info = {
                                    'id': i,
                                    'width': width if width > 0 else 640,
                                    'height': height if height > 0 else 480,
                                    'fps': fps if fps > 0 else 30.0,
                                    'status': frame_quality,
                                    'device_path': device_path,
                                    'type': device_type,
                                    'is_realsense': is_realsense
                                }
                                
                                available_cameras.append(camera_info)
                                print(f"✓ {device_type} {i}: {width}x{height} @ {fps:.1f}fps")
                                
                            except Exception as prop_error:
                                print(f"⚠️ Propriedades inválidas: {prop_error}")
                                failed_devices.append((device_path, f"Propriedades: {prop_error}"))
                            
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
            # Para Windows/outros sistemas, usa detecção padrão
            print("🪟 Sistema não-Linux - usando detecção padrão")
            for i in range(max_cameras):
                try:
                    print(f"📹 Testando Câmera {i}...", end=" ")
                    
                    cap = cv2.VideoCapture(i)
                    if cap.isOpened():
                        try:
                            width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
                            height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
                            fps = cap.get(cv2.CAP_PROP_FPS)
                            
                            # Tentar capturar um frame
                            ret, frame = cap.read()
                            
                            frame_quality = "OK"
                            if ret and frame is not None:
                                if frame.size == 0:
                                    frame_quality = "Frame vazio"
                                elif len(frame.shape) != 3:
                                    frame_quality = "Formato inválido"
                            else:
                                frame_quality = "Sem sinal"
                            
                            camera_info = {
                                'id': i,
                                'width': width if width > 0 else 640,
                                'height': height if height > 0 else 480,
                                'fps': fps if fps > 0 else 30.0,
                                'status': frame_quality,
                                'device_path': f"Camera {i}",
                                'type': "Câmera USB",
                                'is_realsense': False
                            }
                            
                            available_cameras.append(camera_info)
                            print(f"✓ Câmera {i}: {width}x{height} @ {fps:.1f}fps")
                        
                        except Exception as prop_error:
                            print(f"⚠️ Erro nas propriedades: {prop_error}")
                            failed_devices.append((f"Camera {i}", str(prop_error)))
                        
                        finally:
                            cap.release()
                    else:
                        # Para de procurar após algumas tentativas sem sucesso
                        if i > 2 and len(available_cameras) == 0:
                            break
                except Exception as e:
                    # Ignora erros silenciosamente para câmeras não existentes
                    continue
        
        # Relatório final
        realsense_count = sum(1 for cam in available_cameras if cam['is_realsense'])
        working_cameras = sum(1 for cam in available_cameras if cam['status'] == 'OK')
        
        print(f"\n📊 Resumo da detecção:")
        print(f"   📹 Total de câmeras detectadas: {len(available_cameras)}")
        print(f"   ✅ Câmeras funcionando: {working_cameras}")
        print(f"   🎯 Intel RealSense detectadas: {realsense_count}")
        
        if failed_devices:
            print(f"   ❌ Dispositivos com falha: {len(failed_devices)}")
            for device, error in failed_devices:
                print(f"      • {device}: {error}")
        
        if timeout_devices:
            print(f"   ⏰ Dispositivos com timeout: {len(timeout_devices)}")
            for device, error in timeout_devices:
                print(f"      • {device}: {error}")
        
        return available_cameras
    
    def get_camera_info(self, camera_id: int) -> dict:
        """Obtém informações detalhadas da câmera"""
        cap = cv2.VideoCapture(camera_id)
        if not cap.isOpened():
            return {"error": "Não foi possível abrir a câmera"}
        
        info = {
            "camera_id": camera_id,
            "width": int(cap.get(cv2.CAP_PROP_FRAME_WIDTH)),
            "height": int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT)),
            "fps": cap.get(cv2.CAP_PROP_FPS),
            "brightness": cap.get(cv2.CAP_PROP_BRIGHTNESS),
            "contrast": cap.get(cv2.CAP_PROP_CONTRAST),
            "saturation": cap.get(cv2.CAP_PROP_SATURATION),
            "backend": cap.getBackendName()
        }
        
        cap.release()
        return info
    
    def test_camera_capture(self, camera_id: int, duration: int = 5) -> bool:
        """Testa captura de uma câmera específica"""
        print(f"\n📹 Testando câmera {camera_id}...")
        
        cap = cv2.VideoCapture(camera_id)
        if not cap.isOpened():
            print(f"❌ Erro: Não foi possível abrir a câmera {camera_id}")
            return False
        
        # Configurações da câmera
        cap.set(cv2.CAP_PROP_FRAME_WIDTH, 640)
        cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 480)
        
        start_time = time.time()
        frame_count = 0
        
        print(f"⏱️  Capturando por {duration} segundos...")
        print("Pressione 'q' para parar, 's' para salvar imagem, 'b' para salvar base64, 'ESC' para sair")
        
        while True:
            ret, frame = cap.read()
            if not ret:
                print("❌ Erro na captura do frame")
                break
            
            frame_count += 1
            current_time = time.time()
            elapsed = current_time - start_time
            
            # Adiciona informações no frame
            info_text = f"Camera {camera_id} | Frame: {frame_count} | Tempo: {elapsed:.1f}s"
            cv2.putText(frame, info_text, (10, 30), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 255, 0), 2)
            
            # Adiciona timestamp
            timestamp = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            cv2.putText(frame, timestamp, (10, frame.shape[0] - 10), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (255, 255, 255), 1)
            
            cv2.imshow(f'Camera {camera_id} Test', frame)
            
            key = cv2.waitKey(1) & 0xFF
            if key == ord('q') or elapsed >= duration:
                break
            elif key == ord('s'):
                self.save_image(frame, camera_id)
            elif key == ord('b'):
                # Salva o frame atual em base64
                success, buffer = cv2.imencode('.jpg', frame)
                if success:
                    img_base64 = base64.b64encode(buffer).decode('utf-8')
                    timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
                    filename = f"camera_{camera_id}_frame_base64_{timestamp}.txt"
                    filepath = os.path.join(self.capture_directory, filename)
                    
                    with open(filepath, 'w', encoding='utf-8') as f:
                        f.write(f"# Frame capturado da câmera {camera_id}\n")
                        f.write(f"# Timestamp: {datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
                        f.write(f"# Resolução: {frame.shape[1]}x{frame.shape[0]}\n")
                        f.write(f"# Formato: JPEG codificado em Base64\n")
                        f.write("# Para decodificar: base64.b64decode(data_below)\n")
                        f.write("\n")
                        f.write(img_base64)
                    
                    print(f"\n📷 Frame salvo em base64: {filepath}")
                else:
                    print("\n❌ Erro ao codificar frame para base64")
            elif key == 27:  # ESC
                break
        
        cap.release()
        cv2.destroyAllWindows()
        
        # Calcula FPS real
        actual_fps = frame_count / elapsed if elapsed > 0 else 0
        print(f"✓ Teste concluído: {frame_count} frames em {elapsed:.1f}s (FPS: {actual_fps:.1f})")
        
        return True
    
    def save_image(self, frame: np.ndarray, camera_id: int) -> str:
        """Salva uma imagem com timestamp"""
        timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"camera_{camera_id}_{timestamp}.jpg"
        filepath = os.path.join(self.capture_directory, filename)
        
        cv2.imwrite(filepath, frame)
        print(f"📸 Imagem salva: {filepath}")
        return filepath
    
    def save_frame_base64(self, camera_id: int) -> str:
        """Captura um frame e salva em formato base64 em arquivo txt"""
        print(f"\n📷 Capturando frame da câmera {camera_id} para base64...")
        
        cap = cv2.VideoCapture(camera_id)
        if not cap.isOpened():
            print(f"❌ Erro: Não foi possível abrir a câmera {camera_id}")
            return ""
        
        try:
            # Captura um frame
            ret, frame = cap.read()
            if not ret or frame is None:
                print("❌ Erro: Não foi possível capturar frame")
                return ""
            
            # Converte frame para JPEG em memória
            success, buffer = cv2.imencode('.jpg', frame)
            if not success:
                print("❌ Erro: Não foi possível codificar imagem")
                return ""
            
            # Converte para base64
            img_base64 = base64.b64encode(buffer).decode('utf-8')
            
            # Salva em arquivo txt com timestamp
            timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"camera_{camera_id}_frame_base64_{timestamp}.txt"
            filepath = os.path.join(self.capture_directory, filename)
            
            with open(filepath, 'w', encoding='utf-8') as f:
                f.write(f"# Frame capturado da câmera {camera_id}\n")
                f.write(f"# Timestamp: {datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
                f.write(f"# Resolução: {frame.shape[1]}x{frame.shape[0]}\n")
                f.write(f"# Formato: JPEG codificado em Base64\n")
                f.write("# Para decodificar: base64.b64decode(data_below)\n")
                f.write("\n")
                f.write(img_base64)
            
            print(f"✅ Frame salvo em base64: {filepath}")
            print(f"📊 Tamanho do arquivo: {len(img_base64)} caracteres")
            print(f"📐 Resolução da imagem: {frame.shape[1]}x{frame.shape[0]}")
            
            return filepath
            
        except Exception as e:
            print(f"❌ Erro ao salvar frame em base64: {e}")
            return ""
        finally:
            cap.release()
    
    def test_multiple_cameras(self, camera_ids: List[int], duration: int = 10):
        """Testa múltiplas câmeras simultaneamente"""
        print(f"\n🎥 Testando {len(camera_ids)} câmeras simultaneamente...")
        
        caps = []
        for cam_id in camera_ids:
            cap = cv2.VideoCapture(cam_id)
            if cap.isOpened():
                cap.set(cv2.CAP_PROP_FRAME_WIDTH, 320)
                cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 240)
                caps.append((cam_id, cap))
            else:
                print(f"❌ Não foi possível abrir câmera {cam_id}")
        
        if not caps:
            print("❌ Nenhuma câmera disponível para teste múltiplo")
            return
        
        start_time = time.time()
        print(f"⏱️  Capturando por {duration} segundos...")
        print("Pressione 'q' para parar, 's' para salvar todas as imagens, 'b' para salvar todas em base64")
        
        while True:
            frames = []
            valid_frames = True
            
            for cam_id, cap in caps:
                ret, frame = cap.read()
                if ret:
                    # Adiciona ID da câmera no frame
                    cv2.putText(frame, f"Cam {cam_id}", (10, 30), cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 255, 0), 2)
                    frames.append(frame)
                else:
                    valid_frames = False
                    break
            
            if not valid_frames:
                break
            
            # Combina frames em uma única janela
            if len(frames) == 1:
                combined = frames[0]
            elif len(frames) == 2:
                combined = np.hstack(frames)
            else:
                # Para mais de 2 câmeras, organiza em grid
                rows = []
                for i in range(0, len(frames), 2):
                    if i + 1 < len(frames):
                        rows.append(np.hstack([frames[i], frames[i+1]]))
                    else:
                        rows.append(frames[i])
                combined = np.vstack(rows)
            
            cv2.imshow('Multiple Cameras Test', combined)
            
            key = cv2.waitKey(1) & 0xFF
            elapsed = time.time() - start_time
            
            if key == ord('q') or elapsed >= duration:
                break
            elif key == ord('s'):
                for i, frame in enumerate(frames):
                    self.save_image(frame, camera_ids[i])
            elif key == ord('b'):
                # Salva todos os frames em base64
                for i, frame in enumerate(frames):
                    success, buffer = cv2.imencode('.jpg', frame)
                    if success:
                        img_base64 = base64.b64encode(buffer).decode('utf-8')
                        timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
                        filename = f"camera_{camera_ids[i]}_frame_base64_{timestamp}.txt"
                        filepath = os.path.join(self.capture_directory, filename)
                        
                        with open(filepath, 'w', encoding='utf-8') as f:
                            f.write(f"# Frame capturado da câmera {camera_ids[i]}\n")
                            f.write(f"# Timestamp: {datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
                            f.write(f"# Resolução: {frame.shape[1]}x{frame.shape[0]}\n")
                            f.write(f"# Formato: JPEG codificado em Base64\n")
                            f.write("# Para decodificar: base64.b64decode(data_below)\n")
                            f.write("\n")
                            f.write(img_base64)
                        
                        print(f"📷 Frame da câmera {camera_ids[i]} salvo em base64: {filepath}")
                    else:
                        print(f"❌ Erro ao codificar frame da câmera {camera_ids[i]} para base64")
        
        # Libera recursos
        for _, cap in caps:
            cap.release()
        cv2.destroyAllWindows()
        
        print(f"✓ Teste múltiplo concluído em {elapsed:.1f}s")
    
    def list_cameras(self):
        """Lista todas as câmeras detectadas com informações detalhadas"""
        cameras = self.detect_cameras()
        
        if not cameras:
            print("❌ Nenhuma câmera encontrada!")
            return
        
        print(f"\n📹 {len(cameras)} câmera(s) detectada(s):")
        print("=" * 80)
        
        for camera_info in cameras:
            camera_id = camera_info['id']
            print(f"\n🎥 Câmera {camera_id}:")
            print(f"   📍 Tipo: {camera_info['type']}")
            print(f"   🔗 Caminho: {camera_info['device_path']}")
            print(f"   📐 Resolução: {camera_info['width']}x{camera_info['height']}")
            print(f"   🎬 FPS: {camera_info['fps']:.1f}")
            print(f"   ✅ Status: {camera_info['status']}")
            
            if camera_info['is_realsense']:
                print(f"   🔍 Intel RealSense: ✅ Sim")
                # Obter informações adicionais para RealSense
                additional_info = self._get_detailed_camera_info(camera_id)
                if additional_info:
                    print(f"   📊 Informações adicionais:")
                    for key, value in additional_info.items():
                        print(f"      • {key}: {value}")
            else:
                print(f"   🔍 Intel RealSense: ❌ Não")
                
            # Testa resoluções suportadas
            supported_resolutions = self._test_supported_resolutions(camera_id)
            if supported_resolutions:
                print(f"   📏 Resoluções suportadas: {', '.join(supported_resolutions)}")
        
        print("\n" + "=" * 80)
        realsense_count = sum(1 for cam in cameras if cam['is_realsense'])
        print(f"📊 Resumo: {len(cameras)} câmeras total ({realsense_count} Intel RealSense, {len(cameras)-realsense_count} outras)")
        print()
    
    def _get_detailed_camera_info(self, camera_id):
        """Obtém informações detalhadas de uma câmera específica"""
        try:
            cap = cv2.VideoCapture(camera_id)
            if not cap.isOpened():
                return None
            
            info = {}
            
            # Propriedades básicas
            info['Brilho'] = f"{cap.get(cv2.CAP_PROP_BRIGHTNESS):.1f}"
            info['Contraste'] = f"{cap.get(cv2.CAP_PROP_CONTRAST):.1f}"
            info['Saturação'] = f"{cap.get(cv2.CAP_PROP_SATURATION):.1f}"
            info['Matiz'] = f"{cap.get(cv2.CAP_PROP_HUE):.1f}"
            info['Ganho'] = f"{cap.get(cv2.CAP_PROP_GAIN):.1f}"
            info['Exposição'] = f"{cap.get(cv2.CAP_PROP_EXPOSURE):.1f}"
            
            # Informações de formato
            fourcc = int(cap.get(cv2.CAP_PROP_FOURCC))
            if fourcc > 0:
                fourcc_str = "".join([chr((fourcc >> 8 * i) & 0xFF) for i in range(4)])
                info['Formato'] = fourcc_str
            
            # Buffer size
            buffer_size = cap.get(cv2.CAP_PROP_BUFFERSIZE)
            if buffer_size > 0:
                info['Buffer'] = f"{int(buffer_size)} frames"
            
            cap.release()
            return info
            
        except Exception as e:
            print(f"⚠️  Erro ao obter informações detalhadas da câmera {camera_id}: {e}")
            return None
    
    def _test_supported_resolutions(self, camera_id):
        """Testa e retorna as resoluções suportadas por uma câmera"""
        try:
            cap = cv2.VideoCapture(camera_id)
            if not cap.isOpened():
                return []
            
            # Resoluções comuns para testar
            test_resolutions = [
                (320, 240), (640, 480), (800, 600), (848, 480),
                (1024, 768), (1280, 720), (1280, 960), (1600, 1200),
                (1920, 1080), (2560, 1440), (3840, 2160)
            ]
            
            supported = []
            original_width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
            original_height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
            
            for width, height in test_resolutions:
                cap.set(cv2.CAP_PROP_FRAME_WIDTH, width)
                cap.set(cv2.CAP_PROP_FRAME_HEIGHT, height)
                
                actual_width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
                actual_height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
                
                if actual_width == width and actual_height == height:
                    supported.append(f"{width}x{height}")
            
            # Restaura resolução original
            cap.set(cv2.CAP_PROP_FRAME_WIDTH, original_width)
            cap.set(cv2.CAP_PROP_FRAME_HEIGHT, original_height)
            
            cap.release()
            return supported[:5]  # Limita a 5 resoluções para não poluir a saída
            
        except Exception as e:
            print(f"⚠️  Erro ao testar resoluções da câmera {camera_id}: {e}")
            return []

    def run_diagnostics(self, camera_ids: List[int]):
        """Executa diagnósticos completos das câmeras"""
        print("\n🔧 Executando diagnósticos...")
        
        diagnostics = []
        for cam_id in camera_ids:
            print(f"\n--- Diagnóstico Câmera {cam_id} ---")
            info = self.get_camera_info(cam_id)
            
            if "error" in info:
                print(f"❌ {info['error']}")
                continue
            
            print(f"Resolução: {info['width']}x{info['height']}")
            print(f"FPS: {info['fps']}")
            print(f"Backend: {info['backend']}")
            print(f"Brilho: {info['brightness']}")
            print(f"Contraste: {info['contrast']}")
            print(f"Saturação: {info['saturation']}")
            
            diagnostics.append(info)
        
        # Salva diagnósticos em arquivo
        timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
        diag_file = os.path.join(self.capture_directory, f"diagnostics_{timestamp}.json")
        
        with open(diag_file, 'w', encoding='utf-8') as f:
            json.dump(diagnostics, f, indent=2, ensure_ascii=False)
        
        print(f"\n📋 Diagnósticos salvos em: {diag_file}")
        return diagnostics

def select_camera_interactive(available_cameras):
    """Permite ao usuário selecionar uma câmera interativamente com informações detalhadas"""
    if not available_cameras:
        print("❌ Nenhuma câmera disponível para seleção!")
        return None
    
    if len(available_cameras) == 1:
        return available_cameras[0]['id']
    
    print("\n📹 Câmeras disponíveis para seleção:")
    print("=" * 70)
    
    for i, cam_info in enumerate(available_cameras, 1):
        camera_id = cam_info['id']
        camera_type = "🔍 Intel RealSense" if cam_info['is_realsense'] else "📷 Câmera USB"
        resolution = f"{cam_info['width']}x{cam_info['height']}"
        fps = f"{cam_info['fps']:.1f} FPS"
        device_path = cam_info['device_path']
        
        print(f"  {i:2d}. 🎥 Câmera {camera_id}")
        print(f"      📍 Tipo: {camera_type}")
        print(f"      📐 Resolução: {resolution}")
        print(f"      🎬 FPS: {fps}")
        print(f"      🔗 Dispositivo: {device_path}")
        print(f"      ✅ Status: {cam_info['status']}")
        print()
    
    print("=" * 70)
    print("💡 Dicas:")
    print("   • Digite o número da câmera para selecioná-la")
    print("   • Digite 'info X' para ver informações detalhadas da câmera X")
    print("   • Digite 'test X' para fazer um teste rápido da câmera X")
    print("   • Digite 'q' para sair")
    print()
    
    while True:
        try:
            choice = input(f"Escolha uma opção: ").strip()
            
            if choice.lower() == 'q':
                print("🚫 Seleção cancelada.")
                return None
            
            # Comando para informações detalhadas
            if choice.lower().startswith('info '):
                try:
                    cam_num = int(choice.split()[1])
                    if 1 <= cam_num <= len(available_cameras):
                        selected_camera = available_cameras[cam_num - 1]
                        print(f"\n📊 Informações detalhadas da Câmera {selected_camera['id']}:")
                        print("-" * 50)
                        
                        # Criar instância temporária do CameraManager para obter informações
                        temp_manager = CameraManager()
                        detailed_info = temp_manager._get_detailed_camera_info(selected_camera['id'])
                        
                        if detailed_info:
                            for key, value in detailed_info.items():
                                print(f"   • {key}: {value}")
                        
                        supported_res = temp_manager._test_supported_resolutions(selected_camera['id'])
                        if supported_res:
                            print(f"   • Resoluções suportadas: {', '.join(supported_res)}")
                        
                        print("-" * 50)
                        continue
                    else:
                        print(f"❌ Número inválido! Use um número entre 1 e {len(available_cameras)}.")
                        continue
                except (ValueError, IndexError):
                    print("❌ Formato inválido! Use: info <número>")
                    continue
            
            # Comando para teste rápido
            if choice.lower().startswith('test '):
                try:
                    cam_num = int(choice.split()[1])
                    if 1 <= cam_num <= len(available_cameras):
                        selected_camera = available_cameras[cam_num - 1]
                        print(f"\n🧪 Teste rápido da Câmera {selected_camera['id']}...")
                        
                        # Teste rápido de 3 segundos
                        cap = cv2.VideoCapture(selected_camera['id'])
                        if cap.isOpened():
                            print("✅ Câmera aberta com sucesso!")
                            ret, frame = cap.read()
                            if ret:
                                print(f"✅ Frame capturado: {frame.shape[1]}x{frame.shape[0]} pixels")
                                print("💡 Pressione qualquer tecla para continuar...")
                                
                                # Mostra frame por 3 segundos
                                cv2.imshow(f'Teste Câmera {selected_camera["id"]}', frame)
                                cv2.waitKey(3000)
                                cv2.destroyAllWindows()
                            else:
                                print("❌ Falha ao capturar frame")
                            cap.release()
                        else:
                            print("❌ Falha ao abrir câmera")
                        
                        print("🧪 Teste concluído.\n")
                        continue
                    else:
                        print(f"❌ Número inválido! Use um número entre 1 e {len(available_cameras)}.")
                        continue
                except (ValueError, IndexError):
                    print("❌ Formato inválido! Use: test <número>")
                    continue
            
            # Seleção direta por número
            try:
                choice_num = int(choice)
                if 1 <= choice_num <= len(available_cameras):
                    selected_camera = available_cameras[choice_num - 1]
                    print(f"\n✅ Câmera {selected_camera['id']} selecionada!")
                    print(f"   📍 Tipo: {'🔍 Intel RealSense' if selected_camera['is_realsense'] else '📷 Câmera USB'}")
                    print(f"   📐 Resolução: {selected_camera['width']}x{selected_camera['height']}")
                    print(f"   🎬 FPS: {selected_camera['fps']:.1f}")
                    return selected_camera['id']
                else:
                    print(f"❌ Escolha inválida! Digite um número entre 1 e {len(available_cameras)}.")
            except ValueError:
                print("❌ Entrada inválida! Digite um número, 'info X', 'test X' ou 'q' para sair.")
        
        except KeyboardInterrupt:
            print("\n🚫 Operação cancelada pelo usuário.")
            return None

def main():
    """Função principal do script de teste"""
    print("="*60)
    print("🤖 SCRIPT DE TESTE DE CÂMERA - ROBÔ G1")
    print("="*60)
    
    camera_manager = CameraManager()
    
    # Detecta câmeras disponíveis
    available_cameras = camera_manager.detect_cameras()
    
    if not available_cameras:
        print("\n❌ Nenhuma câmera encontrada. Verifique as conexões.")
        return
    
    # Extrai apenas os IDs para compatibilidade com funções existentes
    camera_ids = [cam['id'] for cam in available_cameras]
    
    while True:
        print("\n" + "="*40)
        print("MENU DE OPÇÕES:")
        print("1. Testar câmera individual")
        print("2. Testar múltiplas câmeras")
        print("3. Executar diagnósticos")
        print("4. Salvar frame em base64")
        print("5. Listar câmeras disponíveis")
        print("6. Testar apenas câmeras RealSense")
        print("7. Sair")
        print("="*40)
        
        try:
            choice = input("\nEscolha uma opção (1-7): ").strip()
            
            if choice == '1':
                camera_id = select_camera_interactive(available_cameras)
                duration = int(input("Duração do teste em segundos (padrão 5): ") or "5")
                camera_manager.test_camera_capture(camera_id, duration)
            
            elif choice == '2':
                if len(available_cameras) < 2:
                    print("❌ Necessário pelo menos 2 câmeras para teste múltiplo")
                else:
                    duration = int(input("Duração do teste em segundos (padrão 10): ") or "10")
                    camera_manager.test_multiple_cameras(camera_ids, duration)
            
            elif choice == '3':
                camera_manager.run_diagnostics(camera_ids)
            
            elif choice == '4':
                camera_id = select_camera_interactive(available_cameras)
                result = camera_manager.save_frame_base64(camera_id)
                if result:
                    print(f"\n✅ Operação concluída com sucesso!")
                    print(f"📁 Arquivo salvo: {result}")
                else:
                    print("\n❌ Falha ao salvar frame em base64")
            
            elif choice == '5':
                print("\n📋 Câmeras disponíveis:")
                print("=" * 60)
                
                for cam_info in available_cameras:
                    print(f"📹 {cam_info['type']} (ID: {cam_info['id']}):")
                    print(f"   📍 Dispositivo: {cam_info['device_path']}")
                    print(f"   📐 Resolução: {cam_info['width']}x{cam_info['height']}")
                    print(f"   🎬 FPS: {cam_info['fps']:.1f}")
                    print(f"   ✅ Status: {cam_info['status']}")
                    if cam_info['is_realsense']:
                        print(f"   🎯 Tipo: Intel RealSense (Câmera de Profundidade)")
                    print("-" * 40)
            
            elif choice == '6':
                # Testar apenas câmeras RealSense
                realsense_cameras = [cam for cam in available_cameras if cam['is_realsense']]
                if not realsense_cameras:
                    print("❌ Nenhuma câmera Intel RealSense encontrada")
                    continue
                
                realsense_ids = [cam['id'] for cam in realsense_cameras]
                print(f"\n🎯 Testando {len(realsense_cameras)} câmera(s) Intel RealSense...")
                
                if len(realsense_cameras) == 1:
                    duration = int(input("Duração do teste em segundos (padrão 5): ") or "5")
                    camera_manager.test_camera_capture(realsense_ids[0], duration)
                else:
                    duration = int(input("Duração do teste em segundos (padrão 10): ") or "10")
                    camera_manager.test_multiple_cameras(realsense_ids, duration)
            
            elif choice == '7':
                print("\n👋 Encerrando script de teste...")
                break
            
            else:
                print("❌ Opção inválida. Tente novamente.")
        
        except KeyboardInterrupt:
            print("\n\n⚠️  Interrompido pelo usuário")
            break
        except ValueError:
            print("❌ Entrada inválida. Digite um número.")
        except Exception as e:
            print(f"❌ Erro inesperado: {e}")
    
    print("\n✓ Script finalizado")

if __name__ == "__main__":
    # Verifica se OpenCV está instalado
    try:
        import cv2
        print(f"✓ OpenCV versão: {cv2.__version__}")
    except ImportError:
        print("❌ OpenCV não está instalado. Execute: pip install opencv-python")
        exit(1)
    
    main()