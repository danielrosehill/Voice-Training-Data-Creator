"""Sample storage and management."""
from pathlib import Path
from typing import Optional, Tuple, List
import json
from datetime import datetime


class SampleManager:
    """Manages saving and organizing voice training samples."""

    def __init__(self, base_path: Path):
        """Initialize sample manager.

        Args:
            base_path: Base directory for storing samples.
        """
        self.base_path = base_path
        self.samples_dir = base_path / "samples"
        self.samples_dir.mkdir(parents=True, exist_ok=True)

    def get_next_sample_number(self) -> int:
        """Get the next available sample number.

        Returns:
            Next sample number (e.g., 1, 2, 3...).
        """
        if not self.samples_dir.exists():
            return 1

        # Find all numeric directories
        existing = []
        for item in self.samples_dir.iterdir():
            if item.is_dir() and item.name.isdigit():
                existing.append(int(item.name))

        if not existing:
            return 1

        return max(existing) + 1

    def get_sample_folder(self, sample_num: int) -> Path:
        """Get the folder path for a sample number.

        Args:
            sample_num: Sample number.

        Returns:
            Path to sample folder.
        """
        folder_name = f"{sample_num:03d}"
        return self.samples_dir / folder_name

    def save_sample(self, audio_path: Path, text_content: str,
                    metadata: Optional[dict] = None) -> Tuple[bool, Optional[str]]:
        """Save a voice sample with text and optional metadata.

        Args:
            audio_path: Path to the audio file (already saved).
            text_content: Text content to save.
            metadata: Optional metadata dictionary.

        Returns:
            Tuple of (success, error_message).
        """
        try:
            # Get next sample number
            sample_num = self.get_next_sample_number()
            sample_folder = self.get_sample_folder(sample_num)

            # Create folder
            sample_folder.mkdir(parents=True, exist_ok=True)

            # Save text file
            text_file = sample_folder / f"{sample_num}.txt"
            text_file.write_text(text_content, encoding='utf-8')

            # Move or copy audio file
            target_audio = sample_folder / f"{sample_num}.wav"
            if audio_path != target_audio:
                import shutil
                shutil.move(str(audio_path), str(target_audio))

            # Save metadata if provided
            if metadata:
                metadata_file = sample_folder / f"{sample_num}_metadata.json"
                with open(metadata_file, 'w') as f:
                    json.dump(metadata, f, indent=2)

            return True, None

        except Exception as e:
            return False, str(e)

    def get_total_samples(self) -> int:
        """Get total number of samples in the base path.

        Returns:
            Number of samples.
        """
        if not self.samples_dir.exists():
            return 0

        count = 0
        for item in self.samples_dir.iterdir():
            if item.is_dir() and item.name.isdigit():
                count += 1

        return count

    def get_sample_info(self, sample_num: int) -> Optional[dict]:
        """Get information about a specific sample.

        Args:
            sample_num: Sample number.

        Returns:
            Dictionary with sample info or None if not found.
        """
        folder = self.get_sample_folder(sample_num)
        if not folder.exists():
            return None

        audio_file = folder / f"{sample_num}.wav"
        text_file = folder / f"{sample_num}.txt"
        metadata_file = folder / f"{sample_num}_metadata.json"

        info = {
            'number': sample_num,
            'folder': str(folder),
            'has_audio': audio_file.exists(),
            'has_text': text_file.exists(),
            'has_metadata': metadata_file.exists()
        }

        if audio_file.exists():
            info['audio_size'] = audio_file.stat().st_size

        if text_file.exists():
            info['text_content'] = text_file.read_text(encoding='utf-8')
            info['text_length'] = len(info['text_content'])

        if metadata_file.exists():
            with open(metadata_file, 'r') as f:
                info['metadata'] = json.load(f)

        return info

    def estimate_total_duration(self, sample_rate: int = 44100) -> float:
        """Estimate total duration of all samples in minutes.

        Args:
            sample_rate: Sample rate used for recordings.

        Returns:
            Estimated duration in minutes.
        """
        if not self.samples_dir.exists():
            return 0.0

        total_seconds = 0.0
        for item in self.samples_dir.iterdir():
            if item.is_dir() and item.name.isdigit():
                sample_num = int(item.name)
                audio_file = item / f"{sample_num}.wav"
                if audio_file.exists():
                    try:
                        import soundfile as sf
                        info = sf.info(audio_file)
                        total_seconds += info.duration
                    except Exception:
                        pass

        return total_seconds / 60.0

    def create_metadata(self, generation_params: dict) -> dict:
        """Create metadata dictionary for a sample.

        Args:
            generation_params: Parameters used for text generation.

        Returns:
            Metadata dictionary.
        """
        return {
            'timestamp': datetime.now().isoformat(),
            'generation_params': generation_params
        }
