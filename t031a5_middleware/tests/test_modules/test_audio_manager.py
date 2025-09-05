"""Tests for the Audio Manager module."""

import pytest
from unittest.mock import Mock, patch, MagicMock, call
import asyncio
from pathlib import Path
import tempfile
import os

from modules.audio_manager import (
    AudioManager,
    AudioConfig,
    AudioDevice,
    AudioFormat,
    TTSEngine,
    ASREngine,
    AudioProcessingError,
    DeviceNotFoundError
)


class TestAudioConfig:
    """Tests for AudioConfig class."""
    
    def test_audio_config_creation(self):
        """Test audio configuration creation."""
        config = AudioConfig(
            sample_rate=44100,
            channels=2,
            bit_depth=16,
            buffer_size=1024
        )
        
        assert config.sample_rate == 44100
        assert config.channels == 2
        assert config.bit_depth == 16
        assert config.buffer_size == 1024
    
    def test_audio_config_defaults(self):
        """Test audio configuration with default values."""
        config = AudioConfig()
        
        assert config.sample_rate == 16000
        assert config.channels == 1
        assert config.bit_depth == 16
        assert config.buffer_size == 1024
    
    def test_audio_config_to_dict(self):
        """Test audio configuration serialization."""
        config = AudioConfig(sample_rate=48000, channels=2)
        config_dict = config.to_dict()
        
        assert config_dict["sample_rate"] == 48000
        assert config_dict["channels"] == 2
        assert config_dict["bit_depth"] == 16
        assert config_dict["buffer_size"] == 1024


class TestAudioDevice:
    """Tests for AudioDevice class."""
    
    def test_audio_device_creation(self):
        """Test audio device creation."""
        device = AudioDevice(
            device_id="device_1",
            name="Test Microphone",
            device_type="input",
            channels=1,
            sample_rate=16000
        )
        
        assert device.device_id == "device_1"
        assert device.name == "Test Microphone"
        assert device.device_type == "input"
        assert device.channels == 1
        assert device.sample_rate == 16000
        assert device.is_available == True
    
    def test_audio_device_to_dict(self):
        """Test audio device serialization."""
        device = AudioDevice(
            device_id="device_1",
            name="Test Speaker",
            device_type="output",
            channels=2,
            sample_rate=44100
        )
        
        device_dict = device.to_dict()
        
        assert device_dict["device_id"] == "device_1"
        assert device_dict["name"] == "Test Speaker"
        assert device_dict["device_type"] == "output"
        assert device_dict["channels"] == 2
        assert device_dict["sample_rate"] == 44100
        assert device_dict["is_available"] == True


class TestAudioFormat:
    """Tests for AudioFormat enum."""
    
    def test_audio_format_values(self):
        """Test audio format enum values."""
        assert AudioFormat.WAV.value == "wav"
        assert AudioFormat.MP3.value == "mp3"
        assert AudioFormat.FLAC.value == "flac"
        assert AudioFormat.OGG.value == "ogg"


class TestTTSEngine:
    """Tests for TTSEngine enum."""
    
    def test_tts_engine_values(self):
        """Test TTS engine enum values."""
        assert TTSEngine.ESPEAK.value == "espeak"
        assert TTSEngine.FESTIVAL.value == "festival"
        assert TTSEngine.PICO.value == "pico"
        assert TTSEngine.GOOGLE.value == "google"


class TestASREngine:
    """Tests for ASREngine enum."""
    
    def test_asr_engine_values(self):
        """Test ASR engine enum values."""
        assert ASREngine.WHISPER.value == "whisper"
        assert ASREngine.VOSK.value == "vosk"
        assert ASREngine.GOOGLE.value == "google"
        assert ASREngine.SPHINX.value == "sphinx"


class TestAudioManager:
    """Tests for AudioManager class."""
    
    @pytest.fixture
    def audio_config(self):
        """Create audio configuration for testing."""
        return AudioConfig(
            sample_rate=16000,
            channels=1,
            bit_depth=16,
            buffer_size=1024
        )
    
    @pytest.fixture
    def audio_manager(self, audio_config):
        """Create audio manager instance for testing."""
        return AudioManager(config=audio_config)
    
    def test_audio_manager_initialization(self, audio_manager, audio_config):
        """Test audio manager initialization."""
        assert audio_manager.config == audio_config
        assert audio_manager.is_initialized == False
        assert audio_manager.current_volume == 0.5
        assert audio_manager.is_muted == False
        assert len(audio_manager.input_devices) == 0
        assert len(audio_manager.output_devices) == 0
    
    @patch('modules.audio_manager.pyaudio.PyAudio')
    async def test_initialize_success(self, mock_pyaudio, audio_manager):
        """Test successful audio manager initialization."""
        # Mock PyAudio instance
        mock_audio = Mock()
        mock_pyaudio.return_value = mock_audio
        mock_audio.get_device_count.return_value = 2
        
        # Mock device info
        mock_audio.get_device_info_by_index.side_effect = [
            {
                'index': 0,
                'name': 'Test Microphone',
                'maxInputChannels': 1,
                'maxOutputChannels': 0,
                'defaultSampleRate': 16000.0
            },
            {
                'index': 1,
                'name': 'Test Speaker',
                'maxInputChannels': 0,
                'maxOutputChannels': 2,
                'defaultSampleRate': 44100.0
            }
        ]
        
        await audio_manager.initialize()
        
        assert audio_manager.is_initialized == True
        assert len(audio_manager.input_devices) == 1
        assert len(audio_manager.output_devices) == 1
        assert audio_manager.input_devices[0].name == "Test Microphone"
        assert audio_manager.output_devices[0].name == "Test Speaker"
    
    @patch('modules.audio_manager.pyaudio.PyAudio')
    async def test_initialize_failure(self, mock_pyaudio, audio_manager):
        """Test audio manager initialization failure."""
        mock_pyaudio.side_effect = Exception("Audio system not available")
        
        with pytest.raises(AudioProcessingError):
            await audio_manager.initialize()
        
        assert audio_manager.is_initialized == False
    
    async def test_shutdown(self, audio_manager):
        """Test audio manager shutdown."""
        # Mock initialization
        audio_manager.is_initialized = True
        audio_manager._audio = Mock()
        
        await audio_manager.shutdown()
        
        assert audio_manager.is_initialized == False
        audio_manager._audio.terminate.assert_called_once()
    
    def test_set_volume(self, audio_manager):
        """Test volume setting."""
        audio_manager.set_volume(0.8)
        assert audio_manager.current_volume == 0.8
        
        # Test volume clamping
        audio_manager.set_volume(1.5)
        assert audio_manager.current_volume == 1.0
        
        audio_manager.set_volume(-0.1)
        assert audio_manager.current_volume == 0.0
    
    def test_mute_unmute(self, audio_manager):
        """Test mute and unmute functionality."""
        audio_manager.set_volume(0.7)
        
        # Test mute
        audio_manager.mute()
        assert audio_manager.is_muted == True
        assert audio_manager._previous_volume == 0.7
        assert audio_manager.current_volume == 0.0
        
        # Test unmute
        audio_manager.unmute()
        assert audio_manager.is_muted == False
        assert audio_manager.current_volume == 0.7
    
    def test_get_input_devices(self, audio_manager):
        """Test getting input devices."""
        # Add mock devices
        device1 = AudioDevice("dev1", "Mic 1", "input", 1, 16000)
        device2 = AudioDevice("dev2", "Mic 2", "input", 2, 44100)
        audio_manager.input_devices = [device1, device2]
        
        devices = audio_manager.get_input_devices()
        assert len(devices) == 2
        assert devices[0].name == "Mic 1"
        assert devices[1].name == "Mic 2"
    
    def test_get_output_devices(self, audio_manager):
        """Test getting output devices."""
        # Add mock devices
        device1 = AudioDevice("dev1", "Speaker 1", "output", 2, 44100)
        device2 = AudioDevice("dev2", "Speaker 2", "output", 2, 48000)
        audio_manager.output_devices = [device1, device2]
        
        devices = audio_manager.get_output_devices()
        assert len(devices) == 2
        assert devices[0].name == "Speaker 1"
        assert devices[1].name == "Speaker 2"
    
    def test_get_device_by_id(self, audio_manager):
        """Test getting device by ID."""
        device = AudioDevice("test_device", "Test Device", "input", 1, 16000)
        audio_manager.input_devices = [device]
        
        found_device = audio_manager.get_device_by_id("test_device")
        assert found_device == device
        
        # Test device not found
        with pytest.raises(DeviceNotFoundError):
            audio_manager.get_device_by_id("nonexistent")
    
    @patch('modules.audio_manager.pyaudio.PyAudio')
    async def test_start_recording(self, mock_pyaudio, audio_manager):
        """Test starting audio recording."""
        # Setup
        audio_manager.is_initialized = True
        audio_manager._audio = Mock()
        
        device = AudioDevice("input_device", "Test Mic", "input", 1, 16000)
        audio_manager.input_devices = [device]
        
        mock_stream = Mock()
        audio_manager._audio.open.return_value = mock_stream
        
        # Start recording
        await audio_manager.start_recording(device_id="input_device")
        
        assert audio_manager.is_recording == True
        assert audio_manager._recording_stream == mock_stream
        
        # Verify stream was opened with correct parameters
        audio_manager._audio.open.assert_called_once()
        call_args = audio_manager._audio.open.call_args
        assert call_args[1]['input'] == True
        assert call_args[1]['channels'] == 1
        assert call_args[1]['rate'] == 16000
    
    async def test_start_recording_device_not_found(self, audio_manager):
        """Test starting recording with invalid device."""
        audio_manager.is_initialized = True
        
        with pytest.raises(DeviceNotFoundError):
            await audio_manager.start_recording(device_id="nonexistent")
    
    async def test_stop_recording(self, audio_manager):
        """Test stopping audio recording."""
        # Setup recording state
        audio_manager.is_recording = True
        audio_manager._recording_stream = Mock()
        audio_manager._recording_data = [b'audio_data']
        
        data = await audio_manager.stop_recording()
        
        assert audio_manager.is_recording == False
        assert audio_manager._recording_stream is None
        assert data == [b'audio_data']
        
        # Verify stream was stopped and closed
        audio_manager._recording_stream.stop_stream.assert_called_once()
        audio_manager._recording_stream.close.assert_called_once()
    
    async def test_stop_recording_not_recording(self, audio_manager):
        """Test stopping recording when not recording."""
        audio_manager.is_recording = False
        
        with pytest.raises(AudioProcessingError):
            await audio_manager.stop_recording()
    
    @patch('modules.audio_manager.pyaudio.PyAudio')
    async def test_play_audio_data(self, mock_pyaudio, audio_manager):
        """Test playing audio data."""
        # Setup
        audio_manager.is_initialized = True
        audio_manager._audio = Mock()
        
        device = AudioDevice("output_device", "Test Speaker", "output", 2, 44100)
        audio_manager.output_devices = [device]
        
        mock_stream = Mock()
        audio_manager._audio.open.return_value = mock_stream
        
        audio_data = b'test_audio_data'
        
        # Play audio
        await audio_manager.play_audio_data(audio_data, device_id="output_device")
        
        # Verify stream was opened and data was written
        audio_manager._audio.open.assert_called_once()
        mock_stream.write.assert_called_once_with(audio_data)
        mock_stream.stop_stream.assert_called_once()
        mock_stream.close.assert_called_once()
    
    async def test_play_audio_data_device_not_found(self, audio_manager):
        """Test playing audio with invalid device."""
        audio_manager.is_initialized = True
        
        with pytest.raises(DeviceNotFoundError):
            await audio_manager.play_audio_data(b'data', device_id="nonexistent")
    
    @patch('modules.audio_manager.wave.open')
    async def test_load_audio_file(self, mock_wave_open, audio_manager):
        """Test loading audio file."""
        # Mock wave file
        mock_wave_file = Mock()
        mock_wave_open.return_value.__enter__.return_value = mock_wave_file
        mock_wave_file.getnchannels.return_value = 1
        mock_wave_file.getsampwidth.return_value = 2
        mock_wave_file.getframerate.return_value = 16000
        mock_wave_file.readframes.return_value = b'audio_data'
        
        with tempfile.NamedTemporaryFile(suffix='.wav', delete=False) as tmp_file:
            tmp_path = tmp_file.name
        
        try:
            audio_data, config = await audio_manager.load_audio_file(tmp_path)
            
            assert audio_data == b'audio_data'
            assert config.channels == 1
            assert config.sample_rate == 16000
            assert config.bit_depth == 16
        finally:
            os.unlink(tmp_path)
    
    async def test_load_audio_file_not_found(self, audio_manager):
        """Test loading non-existent audio file."""
        with pytest.raises(AudioProcessingError):
            await audio_manager.load_audio_file("nonexistent.wav")
    
    @patch('modules.audio_manager.wave.open')
    async def test_save_audio_file(self, mock_wave_open, audio_manager):
        """Test saving audio file."""
        # Mock wave file
        mock_wave_file = Mock()
        mock_wave_open.return_value.__enter__.return_value = mock_wave_file
        
        audio_data = b'test_audio_data'
        config = AudioConfig(channels=1, sample_rate=16000, bit_depth=16)
        
        with tempfile.NamedTemporaryFile(suffix='.wav', delete=False) as tmp_file:
            tmp_path = tmp_file.name
        
        try:
            await audio_manager.save_audio_file(audio_data, tmp_path, config)
            
            # Verify wave file was configured correctly
            mock_wave_file.setnchannels.assert_called_once_with(1)
            mock_wave_file.setsampwidth.assert_called_once_with(2)  # 16 bits = 2 bytes
            mock_wave_file.setframerate.assert_called_once_with(16000)
            mock_wave_file.writeframes.assert_called_once_with(audio_data)
        finally:
            if os.path.exists(tmp_path):
                os.unlink(tmp_path)
    
    @patch('modules.audio_manager.subprocess.run')
    async def test_text_to_speech_espeak(self, mock_subprocess, audio_manager):
        """Test text-to-speech with eSpeak engine."""
        mock_subprocess.return_value.returncode = 0
        
        with tempfile.NamedTemporaryFile(suffix='.wav', delete=False) as tmp_file:
            tmp_path = tmp_file.name
            tmp_file.write(b'fake_audio_data')
        
        try:
            audio_data = await audio_manager.text_to_speech(
                "Hello world", 
                engine=TTSEngine.ESPEAK,
                output_file=tmp_path
            )
            
            assert audio_data == b'fake_audio_data'
            
            # Verify subprocess was called with correct arguments
            mock_subprocess.assert_called_once()
            call_args = mock_subprocess.call_args[0][0]
            assert 'espeak' in call_args
            assert 'Hello world' in call_args
        finally:
            if os.path.exists(tmp_path):
                os.unlink(tmp_path)
    
    @patch('modules.audio_manager.subprocess.run')
    async def test_text_to_speech_failure(self, mock_subprocess, audio_manager):
        """Test text-to-speech failure."""
        mock_subprocess.return_value.returncode = 1
        mock_subprocess.return_value.stderr = "TTS engine error"
        
        with pytest.raises(AudioProcessingError):
            await audio_manager.text_to_speech("Hello world", engine=TTSEngine.ESPEAK)
    
    @patch('modules.audio_manager.subprocess.run')
    async def test_speech_to_text_whisper(self, mock_subprocess, audio_manager):
        """Test speech-to-text with Whisper engine."""
        mock_subprocess.return_value.returncode = 0
        mock_subprocess.return_value.stdout = "Hello world"
        
        with tempfile.NamedTemporaryFile(suffix='.wav', delete=False) as tmp_file:
            tmp_path = tmp_file.name
            tmp_file.write(b'fake_audio_data')
        
        try:
            text = await audio_manager.speech_to_text(
                tmp_path,
                engine=ASREngine.WHISPER
            )
            
            assert text == "Hello world"
            
            # Verify subprocess was called with correct arguments
            mock_subprocess.assert_called_once()
            call_args = mock_subprocess.call_args[0][0]
            assert 'whisper' in call_args
            assert tmp_path in call_args
        finally:
            if os.path.exists(tmp_path):
                os.unlink(tmp_path)
    
    @patch('modules.audio_manager.subprocess.run')
    async def test_speech_to_text_failure(self, mock_subprocess, audio_manager):
        """Test speech-to-text failure."""
        mock_subprocess.return_value.returncode = 1
        mock_subprocess.return_value.stderr = "ASR engine error"
        
        with tempfile.NamedTemporaryFile(suffix='.wav', delete=False) as tmp_file:
            tmp_path = tmp_file.name
        
        try:
            with pytest.raises(AudioProcessingError):
                await audio_manager.speech_to_text(tmp_path, engine=ASREngine.WHISPER)
        finally:
            if os.path.exists(tmp_path):
                os.unlink(tmp_path)
    
    def test_get_audio_info(self, audio_manager):
        """Test getting audio system information."""
        # Setup mock devices
        input_device = AudioDevice("input1", "Test Mic", "input", 1, 16000)
        output_device = AudioDevice("output1", "Test Speaker", "output", 2, 44100)
        
        audio_manager.input_devices = [input_device]
        audio_manager.output_devices = [output_device]
        audio_manager.is_initialized = True
        audio_manager.current_volume = 0.8
        audio_manager.is_muted = False
        
        info = audio_manager.get_audio_info()
        
        assert info["is_initialized"] == True
        assert info["current_volume"] == 0.8
        assert info["is_muted"] == False
        assert info["is_recording"] == False
        assert len(info["input_devices"]) == 1
        assert len(info["output_devices"]) == 1
        assert info["input_devices"][0]["name"] == "Test Mic"
        assert info["output_devices"][0]["name"] == "Test Speaker"


if __name__ == "__main__":
    pytest.main([__file__])