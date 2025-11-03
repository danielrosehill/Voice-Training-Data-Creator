"""Audio device management for microphone selection."""
import sounddevice as sd
from typing import List, Dict, Optional


class DeviceManager:
    """Manages audio input devices."""

    def __init__(self):
        self._devices = None
        self._refresh_devices()

    def _refresh_devices(self):
        """Refresh the list of available audio devices."""
        self._devices = sd.query_devices()

    def get_input_devices(self) -> List[Dict]:
        """Get list of available input devices.

        Returns:
            List of dictionaries containing device info.
        """
        if self._devices is None:
            self._refresh_devices()

        input_devices = []
        for idx, device in enumerate(self._devices):
            if device['max_input_channels'] > 0:
                input_devices.append({
                    'index': idx,
                    'name': device['name'],
                    'channels': device['max_input_channels'],
                    'sample_rate': device['default_samplerate']
                })
        return input_devices

    def get_default_input_device(self) -> Optional[Dict]:
        """Get the default input device.

        Returns:
            Dictionary containing default device info, or None if not found.
        """
        try:
            default_idx = sd.default.device[0]
            if default_idx is None:
                return None

            device = sd.query_devices(default_idx)
            return {
                'index': default_idx,
                'name': device['name'],
                'channels': device['max_input_channels'],
                'sample_rate': device['default_samplerate']
            }
        except Exception:
            return None

    def set_device(self, device_index: int):
        """Set the active input device.

        Args:
            device_index: Index of the device to use.
        """
        sd.default.device[0] = device_index

    def test_device(self, device_index: int, duration: float = 3.0,
                    sample_rate: int = 44100) -> Optional[object]:
        """Test an audio device by recording a short sample.

        Args:
            device_index: Device to test.
            duration: Test duration in seconds.
            sample_rate: Sample rate for recording.

        Returns:
            Recorded audio data if successful, None otherwise.
        """
        try:
            recording = sd.rec(
                int(duration * sample_rate),
                samplerate=sample_rate,
                channels=1,
                device=device_index,
                dtype='float32'
            )
            sd.wait()
            return recording
        except Exception as e:
            print(f"Device test failed: {e}")
            return None
