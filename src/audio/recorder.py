"""Audio recording functionality."""
import sounddevice as sd
import soundfile as sf
import numpy as np
from typing import Optional, Callable
from pathlib import Path
import threading


class AudioRecorder:
    """Handles audio recording with pause/resume capability."""

    def __init__(self, sample_rate: int = 44100, channels: int = 1):
        """Initialize the audio recorder.

        Args:
            sample_rate: Sample rate in Hz (default: 44100).
            channels: Number of audio channels (default: 1 for mono).
        """
        self.sample_rate = sample_rate
        self.channels = channels
        self.is_recording = False
        self.is_paused = False
        self._audio_data = []
        self._stream = None
        self._lock = threading.Lock()
        self._level_callback: Optional[Callable[[float], None]] = None

    def set_level_callback(self, callback: Callable[[float], None]):
        """Set callback for audio level monitoring.

        Args:
            callback: Function that receives audio level (0.0 to 1.0).
        """
        self._level_callback = callback

    def start_recording(self, device_index: Optional[int] = None):
        """Start recording audio.

        Args:
            device_index: Optional device index to use.
        """
        if self.is_recording:
            return

        with self._lock:
            self._audio_data = []
            self.is_recording = True
            self.is_paused = False

        def audio_callback(indata, frames, time, status):
            """Callback for audio stream."""
            if status:
                print(f"Audio status: {status}")

            if self.is_recording and not self.is_paused:
                with self._lock:
                    self._audio_data.append(indata.copy())

                # Calculate audio level for monitoring
                if self._level_callback:
                    level = np.abs(indata).mean()
                    self._level_callback(float(level))

        self._stream = sd.InputStream(
            samplerate=self.sample_rate,
            channels=self.channels,
            callback=audio_callback,
            device=device_index,
            dtype='float32'
        )
        self._stream.start()

    def pause_recording(self):
        """Pause the current recording."""
        if self.is_recording and not self.is_paused:
            self.is_paused = True

    def resume_recording(self):
        """Resume a paused recording."""
        if self.is_recording and self.is_paused:
            self.is_paused = False

    def stop_recording(self) -> Optional[np.ndarray]:
        """Stop recording and return the audio data.

        Returns:
            Numpy array containing the recorded audio, or None if no data.
        """
        if not self.is_recording:
            return None

        self.is_recording = False
        self.is_paused = False

        if self._stream:
            self._stream.stop()
            self._stream.close()
            self._stream = None

        with self._lock:
            if not self._audio_data:
                return None

            # Concatenate all audio chunks
            audio = np.concatenate(self._audio_data, axis=0)
            self._audio_data = []
            return audio

    def save_audio(self, audio_data: np.ndarray, file_path: Path) -> bool:
        """Save audio data to a WAV file.

        Args:
            audio_data: Audio data to save.
            file_path: Path where to save the file.

        Returns:
            True if successful, False otherwise.
        """
        try:
            file_path.parent.mkdir(parents=True, exist_ok=True)
            sf.write(
                file_path,
                audio_data,
                self.sample_rate,
                subtype='PCM_16'
            )
            return True
        except Exception as e:
            print(f"Error saving audio: {e}")
            return False

    def get_duration(self, audio_data: Optional[np.ndarray] = None) -> float:
        """Get duration of recorded audio in seconds.

        Args:
            audio_data: Optional audio data. If None, uses current recording.

        Returns:
            Duration in seconds.
        """
        if audio_data is None:
            with self._lock:
                if not self._audio_data:
                    return 0.0
                audio_data = np.concatenate(self._audio_data, axis=0)

        if audio_data is None or len(audio_data) == 0:
            return 0.0

        return len(audio_data) / self.sample_rate

    def has_audio_data(self) -> bool:
        """Check if there is recorded audio data.

        Returns:
            True if audio data exists, False otherwise.
        """
        with self._lock:
            return len(self._audio_data) > 0

    def clear_audio(self):
        """Clear all recorded audio data."""
        with self._lock:
            self._audio_data = []
