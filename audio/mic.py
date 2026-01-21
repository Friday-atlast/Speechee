"""
Speechee - Microphone Interface
Hardware microphone access and device management.
"""

import sys
from typing import Optional, List, Dict, Any

try:
    import sounddevice as sd
    AUDIO_BACKEND = "sounddevice"
except ImportError:
    sd = None
    AUDIO_BACKEND = None

try:
    import pyaudio
    if AUDIO_BACKEND is None:
        AUDIO_BACKEND = "pyaudio"
except ImportError:
    pyaudio = None


class MicrophoneError(Exception):
    """Microphone related errors."""
    pass


class Microphone:
    """
    Microphone device interface.
    
    Usage:
        mic = Microphone()
        devices = mic.list_devices()
        mic.set_device(0)  # Select device by index
    """
    
    # Whisper.cpp required format
    SAMPLE_RATE = 16000      # 16kHz
    CHANNELS = 1             # Mono
    DTYPE = "int16"          # 16-bit
    
    def __init__(self, device_id: Optional[int] = None):
        """
        Initialize microphone.
        
        Args:
            device_id: Specific device index. None = default device.
        """
        self._validate_backend()
        self.device_id = device_id
        self.sample_rate = self.SAMPLE_RATE
        self.channels = self.CHANNELS
        
    def _validate_backend(self) -> None:
        """Check if audio backend is available."""
        if AUDIO_BACKEND is None:
            raise MicrophoneError(
                "No audio backend found!\n"
                "Install: pip install sounddevice soundfile\n"
                "Or: pip install pyaudio"
            )
    
    def list_devices(self) -> List[Dict[str, Any]]:
        """
        List all available audio input devices.
        
        Returns:
            List of device dictionaries
        """
        devices = []
        
        if AUDIO_BACKEND == "sounddevice":
            all_devices = sd.query_devices()
            for i, dev in enumerate(all_devices):
                if dev['max_input_channels'] > 0:  # Input device
                    devices.append({
                        "index": i,
                        "name": dev['name'],
                        "channels": dev['max_input_channels'],
                        "sample_rate": int(dev['default_samplerate']),
                        "is_default": i == sd.default.device[0]
                    })
        
        elif AUDIO_BACKEND == "pyaudio":
            p = pyaudio.PyAudio()
            for i in range(p.get_device_count()):
                dev = p.get_device_info_by_index(i)
                if dev['maxInputChannels'] > 0:
                    devices.append({
                        "index": i,
                        "name": dev['name'],
                        "channels": dev['maxInputChannels'],
                        "sample_rate": int(dev['defaultSampleRate']),
                        "is_default": i == p.get_default_input_device_info()['index']
                    })
            p.terminate()
        
        return devices
    
    def get_default_device(self) -> Optional[Dict[str, Any]]:
        """Get default input device info."""
        devices = self.list_devices()
        for dev in devices:
            if dev.get('is_default'):
                return dev
        return devices[0] if devices else None
    
    def set_device(self, device_id: int) -> None:
        """Set active input device."""
        devices = self.list_devices()
        valid_ids = [d['index'] for d in devices]
        
        if device_id not in valid_ids:
            raise MicrophoneError(
                f"Invalid device ID: {device_id}\n"
                f"Available: {valid_ids}"
            )
        
        self.device_id = device_id
    
    def get_device_id(self) -> Optional[int]:
        """Get current device ID."""
        return self.device_id
    
    def test_device(self, duration: float = 1.0) -> bool:
        """
        Test if microphone is working.
        
        Args:
            duration: Test recording duration in seconds
            
        Returns:
            True if device works
        """
        try:
            if AUDIO_BACKEND == "sounddevice":
                recording = sd.rec(
                    int(duration * self.sample_rate),
                    samplerate=self.sample_rate,
                    channels=self.channels,
                    dtype=self.DTYPE,
                    device=self.device_id
                )
                sd.wait()
                return len(recording) > 0
            
            elif AUDIO_BACKEND == "pyaudio":
                p = pyaudio.PyAudio()
                stream = p.open(
                    format=pyaudio.paInt16,
                    channels=self.channels,
                    rate=self.sample_rate,
                    input=True,
                    input_device_index=self.device_id,
                    frames_per_buffer=1024
                )
                data = stream.read(int(duration * self.sample_rate))
                stream.stop_stream()
                stream.close()
                p.terminate()
                return len(data) > 0
                
        except Exception as e:
            print(f"[MIC TEST ERROR] {e}")
            return False
        
        return False
    
    def get_info(self) -> Dict[str, Any]:
        """Get microphone configuration info."""
        default_dev = self.get_default_device()
        return {
            "backend": AUDIO_BACKEND,
            "device_id": self.device_id,
            "sample_rate": self.sample_rate,
            "channels": self.channels,
            "dtype": self.DTYPE,
            "default_device": default_dev['name'] if default_dev else None,
            "total_input_devices": len(self.list_devices())
        }


def print_devices():
    """Print all available input devices."""
    mic = Microphone()
    devices = mic.list_devices()
    
    print("\n" + "=" * 60)
    print("AVAILABLE INPUT DEVICES")
    print("=" * 60)
    
    if not devices:
        print("\n  No input devices found!")
        print("  Check microphone connection.")
    else:
        print(f"\n{'ID':<5} {'Name':<40} {'Channels':<10} {'Default':<8}")
        print("-" * 60)
        for dev in devices:
            default = "✓" if dev['is_default'] else ""
            print(f"{dev['index']:<5} {dev['name'][:38]:<40} {dev['channels']:<10} {default:<8}")
    
    print("=" * 60)


if __name__ == "__main__":
    print(f"\nAudio Backend: {AUDIO_BACKEND}")
    print_devices()
    
    # Test default device
    mic = Microphone()
    info = mic.get_info()
    print(f"\n[CONFIG]")
    for k, v in info.items():
        print(f"  {k}: {v}")
    
    print(f"\n[TESTING] Recording 1 second...")
    if mic.test_device(1.0):
        print("[SUCCESS] Microphone is working!")
    else:
        print("[FAILED] Microphone test failed!")