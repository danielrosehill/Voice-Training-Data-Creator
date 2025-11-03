"""Validation utilities."""
from pathlib import Path
from typing import Tuple, Optional
import numpy as np


class Validators:
    """Collection of validation utilities."""

    @staticmethod
    def validate_base_path(path: Path) -> Tuple[bool, Optional[str]]:
        """Validate base path for sample storage.

        Args:
            path: Path to validate.

        Returns:
            Tuple of (is_valid, error_message).
        """
        if not path:
            return False, "Path cannot be empty"

        if not path.exists():
            try:
                path.mkdir(parents=True, exist_ok=True)
            except Exception as e:
                return False, f"Cannot create directory: {str(e)}"

        if not path.is_dir():
            return False, "Path must be a directory"

        # Test write permissions
        test_file = path / ".write_test"
        try:
            test_file.touch()
            test_file.unlink()
        except Exception as e:
            return False, f"No write permission: {str(e)}"

        return True, None

    @staticmethod
    def validate_audio_data(audio_data: Optional[np.ndarray]) -> Tuple[bool, Optional[str]]:
        """Validate audio data.

        Args:
            audio_data: Audio data to validate.

        Returns:
            Tuple of (is_valid, error_message).
        """
        if audio_data is None:
            return False, "No audio data recorded"

        if len(audio_data) == 0:
            return False, "Audio recording is empty"

        # Check for silence (very low amplitude throughout)
        max_amplitude = np.abs(audio_data).max()
        if max_amplitude < 0.001:
            return False, "Audio appears to be silent. Please check your microphone."

        return True, None

    @staticmethod
    def validate_text_content(text: str) -> Tuple[bool, Optional[str]]:
        """Validate text content.

        Args:
            text: Text to validate.

        Returns:
            Tuple of (is_valid, error_message).
        """
        if not text or not text.strip():
            return False, "Text content is empty"

        if len(text.strip()) < 10:
            return False, "Text is too short (minimum 10 characters)"

        return True, None

    @staticmethod
    def validate_sample(audio_data: Optional[np.ndarray], text: str) -> Tuple[bool, Optional[str]]:
        """Validate both audio and text for a sample.

        Args:
            audio_data: Audio data to validate.
            text: Text content to validate.

        Returns:
            Tuple of (is_valid, error_message).
        """
        # Validate audio
        audio_valid, audio_error = Validators.validate_audio_data(audio_data)
        if not audio_valid:
            return False, audio_error

        # Validate text
        text_valid, text_error = Validators.validate_text_content(text)
        if not text_valid:
            return False, text_error

        return True, None

    @staticmethod
    def check_disk_space(path: Path, required_mb: int = 100) -> Tuple[bool, Optional[str]]:
        """Check available disk space.

        Args:
            path: Path to check.
            required_mb: Required space in megabytes.

        Returns:
            Tuple of (has_space, error_message).
        """
        try:
            import shutil
            stat = shutil.disk_usage(path)
            available_mb = stat.free / (1024 * 1024)

            if available_mb < required_mb:
                return False, f"Insufficient disk space. Available: {available_mb:.1f} MB, Required: {required_mb} MB"

            return True, None
        except Exception as e:
            return False, f"Cannot check disk space: {str(e)}"

    @staticmethod
    def detect_clipping(audio_data: np.ndarray, threshold: float = 0.99) -> bool:
        """Detect audio clipping.

        Args:
            audio_data: Audio data to check.
            threshold: Clipping threshold (0.0 to 1.0).

        Returns:
            True if clipping detected, False otherwise.
        """
        if audio_data is None or len(audio_data) == 0:
            return False

        max_amplitude = np.abs(audio_data).max()
        return max_amplitude >= threshold

    @staticmethod
    def detect_long_silence(audio_data: np.ndarray, threshold: float = 0.01,
                           min_duration: float = 3.0, sample_rate: int = 44100) -> bool:
        """Detect long periods of silence.

        Args:
            audio_data: Audio data to check.
            threshold: Silence threshold.
            min_duration: Minimum duration in seconds to consider.
            sample_rate: Sample rate of audio.

        Returns:
            True if long silence detected, False otherwise.
        """
        if audio_data is None or len(audio_data) == 0:
            return False

        # Find silent samples
        is_silent = np.abs(audio_data) < threshold

        # Count consecutive silent samples
        max_silent_samples = 0
        current_silent = 0

        for silent in is_silent:
            if silent:
                current_silent += 1
                max_silent_samples = max(max_silent_samples, current_silent)
            else:
                current_silent = 0

        # Convert to seconds
        max_silent_duration = max_silent_samples / sample_rate
        return max_silent_duration >= min_duration
