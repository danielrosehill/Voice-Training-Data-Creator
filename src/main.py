#!/usr/bin/env python3
"""Main entry point for Voice Training Data Creator."""
import sys
from pathlib import Path
from PyQt6.QtWidgets import QApplication, QMessageBox

from audio import AudioRecorder, DeviceManager
from storage import ConfigManager, SampleManager
from llm import TextGenerator
from ui import MainWindow


def main():
    """Main application entry point."""
    # Create QApplication
    app = QApplication(sys.argv)
    app.setApplicationName("Voice Training Data Creator")
    app.setOrganizationName("VoiceTrainingDataCreator")

    # Initialize core components
    config = ConfigManager()

    # Initialize audio components
    sample_rate = config.get_sample_rate()
    audio_recorder = AudioRecorder(sample_rate=sample_rate)
    device_manager = DeviceManager()

    # Initialize text generator
    api_key = config.get_api_key()
    model = config.get_openai_model()

    if api_key:
        try:
            text_generator = TextGenerator(api_key, model)
        except Exception as e:
            QMessageBox.warning(
                None,
                "API Initialization Failed",
                f"Failed to initialize text generator:\n{str(e)}\n\n"
                "You can configure the API key in Settings."
            )
            # Create dummy generator that will fail gracefully
            text_generator = TextGenerator("", model)
    else:
        # No API key configured yet
        text_generator = TextGenerator("", model)

    # Initialize sample manager
    base_path = config.get_base_path()
    if base_path:
        sample_manager = SampleManager(base_path)
    else:
        # Will be initialized when base path is configured
        sample_manager = SampleManager(Path.home() / "voice_samples")

    # Create and show main window
    window = MainWindow(
        config=config,
        audio_recorder=audio_recorder,
        device_manager=device_manager,
        text_generator=text_generator,
        sample_manager=sample_manager
    )
    window.show()

    # Run application
    sys.exit(app.exec())


if __name__ == "__main__":
    main()
