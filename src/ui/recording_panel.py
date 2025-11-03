"""Recording panel UI component."""
from PyQt6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QPushButton,
                              QLabel, QComboBox, QGroupBox, QProgressBar)
from PyQt6.QtCore import Qt, QTimer, pyqtSignal
from PyQt6.QtGui import QFont
import numpy as np


class RecordingPanel(QWidget):
    """Panel for audio recording controls."""

    # Signals
    recording_finished = pyqtSignal(np.ndarray)  # Emitted when recording stops

    def __init__(self, audio_recorder, device_manager):
        """Initialize recording panel.

        Args:
            audio_recorder: AudioRecorder instance.
            device_manager: DeviceManager instance.
        """
        super().__init__()
        self.recorder = audio_recorder
        self.device_manager = device_manager
        self.current_audio = None
        self.recording_time = 0.0

        self.init_ui()
        self.setup_timer()
        self.setup_callbacks()

    def init_ui(self):
        """Initialize UI components."""
        layout = QVBoxLayout()

        # Recording controls group
        controls_group = QGroupBox("Recording Controls")
        controls_layout = QVBoxLayout()

        # Device selector
        device_layout = QHBoxLayout()
        device_layout.addWidget(QLabel("Microphone:"))

        self.device_combo = QComboBox()
        self.populate_devices()
        self.device_combo.currentIndexChanged.connect(self.on_device_changed)
        device_layout.addWidget(self.device_combo, 1)

        self.test_mic_btn = QPushButton("Test Mic")
        self.test_mic_btn.clicked.connect(self.test_microphone)
        device_layout.addWidget(self.test_mic_btn)

        controls_layout.addLayout(device_layout)

        # Recording buttons
        button_layout = QHBoxLayout()

        self.record_btn = QPushButton("⏺ Record")
        self.record_btn.clicked.connect(self.start_recording)
        self.record_btn.setStyleSheet("QPushButton { font-size: 14px; padding: 10px; }")
        button_layout.addWidget(self.record_btn)

        self.pause_btn = QPushButton("⏸ Pause")
        self.pause_btn.clicked.connect(self.toggle_pause)
        self.pause_btn.setEnabled(False)
        button_layout.addWidget(self.pause_btn)

        self.stop_btn = QPushButton("⏹ Stop")
        self.stop_btn.clicked.connect(self.stop_recording)
        self.stop_btn.setEnabled(False)
        button_layout.addWidget(self.stop_btn)

        controls_layout.addLayout(button_layout)

        # Duration display
        self.duration_label = QLabel("Duration: 00:00")
        duration_font = QFont()
        duration_font.setPointSize(16)
        duration_font.setBold(True)
        self.duration_label.setFont(duration_font)
        self.duration_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        controls_layout.addWidget(self.duration_label)

        # Audio level meter
        level_layout = QVBoxLayout()
        level_layout.addWidget(QLabel("Audio Level:"))

        self.level_bar = QProgressBar()
        self.level_bar.setRange(0, 100)
        self.level_bar.setValue(0)
        self.level_bar.setTextVisible(False)
        level_layout.addWidget(self.level_bar)

        controls_layout.addLayout(level_layout)

        # Status label
        self.status_label = QLabel("Ready to record")
        self.status_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        controls_layout.addWidget(self.status_label)

        controls_group.setLayout(controls_layout)
        layout.addWidget(controls_group)

        self.setLayout(layout)

    def setup_timer(self):
        """Setup timer for duration updates."""
        self.timer = QTimer()
        self.timer.timeout.connect(self.update_duration)

    def setup_callbacks(self):
        """Setup callbacks for audio recorder."""
        self.recorder.set_level_callback(self.update_audio_level)

    def populate_devices(self):
        """Populate device combo box."""
        self.device_combo.clear()
        devices = self.device_manager.get_input_devices()

        default_device = self.device_manager.get_default_input_device()
        default_idx = default_device['index'] if default_device else None

        for i, device in enumerate(devices):
            name = device['name']
            if device['index'] == default_idx:
                name += " (Default)"
            self.device_combo.addItem(name, device['index'])

    def on_device_changed(self, index):
        """Handle device selection change."""
        if index >= 0:
            device_idx = self.device_combo.itemData(index)
            self.device_manager.set_device(device_idx)

    def test_microphone(self):
        """Test the selected microphone."""
        self.test_mic_btn.setEnabled(False)
        self.status_label.setText("Testing microphone...")

        device_idx = self.device_combo.currentData()
        audio_data = self.device_manager.test_device(device_idx, duration=3.0)

        if audio_data is not None:
            self.status_label.setText("Microphone test successful!")
            # Could play back the audio here if desired
        else:
            self.status_label.setText("Microphone test failed!")

        self.test_mic_btn.setEnabled(True)

    def start_recording(self):
        """Start recording audio."""
        device_idx = self.device_combo.currentData()
        self.recorder.start_recording(device_idx)

        self.record_btn.setEnabled(False)
        self.pause_btn.setEnabled(True)
        self.stop_btn.setEnabled(True)
        self.device_combo.setEnabled(False)
        self.test_mic_btn.setEnabled(False)

        self.recording_time = 0.0
        self.timer.start(100)  # Update every 100ms

        self.status_label.setText("🔴 Recording...")
        self.status_label.setStyleSheet("QLabel { color: red; font-weight: bold; }")

    def toggle_pause(self):
        """Toggle pause/resume recording."""
        if self.recorder.is_paused:
            self.recorder.resume_recording()
            self.pause_btn.setText("⏸ Pause")
            self.status_label.setText("🔴 Recording...")
        else:
            self.recorder.pause_recording()
            self.pause_btn.setText("▶ Resume")
            self.status_label.setText("⏸ Paused")

    def stop_recording(self):
        """Stop recording audio."""
        self.current_audio = self.recorder.stop_recording()

        self.timer.stop()

        self.record_btn.setEnabled(True)
        self.pause_btn.setEnabled(False)
        self.stop_btn.setEnabled(False)
        self.device_combo.setEnabled(True)
        self.test_mic_btn.setEnabled(True)

        self.pause_btn.setText("⏸ Pause")
        self.status_label.setText("Recording stopped")
        self.status_label.setStyleSheet("")

        if self.current_audio is not None:
            self.recording_finished.emit(self.current_audio)

    def update_duration(self):
        """Update duration display."""
        if self.recorder.is_recording and not self.recorder.is_paused:
            self.recording_time += 0.1

        minutes = int(self.recording_time // 60)
        seconds = int(self.recording_time % 60)
        self.duration_label.setText(f"Duration: {minutes:02d}:{seconds:02d}")

    def update_audio_level(self, level: float):
        """Update audio level meter.

        Args:
            level: Audio level (0.0 to 1.0).
        """
        # Convert to percentage and update progress bar
        percentage = min(100, int(level * 100 * 10))  # Scale up for visibility
        self.level_bar.setValue(percentage)

        # Color code the level bar
        if percentage > 90:
            self.level_bar.setStyleSheet("QProgressBar::chunk { background-color: red; }")
        elif percentage > 70:
            self.level_bar.setStyleSheet("QProgressBar::chunk { background-color: orange; }")
        else:
            self.level_bar.setStyleSheet("QProgressBar::chunk { background-color: green; }")

    def get_audio_data(self):
        """Get the current recorded audio data.

        Returns:
            Numpy array of audio data or None.
        """
        return self.current_audio

    def clear_audio(self):
        """Clear the current audio data."""
        self.current_audio = None
        self.recorder.clear_audio()
        self.recording_time = 0.0
        self.duration_label.setText("Duration: 00:00")
        self.level_bar.setValue(0)
        self.status_label.setText("Ready to record")
        self.status_label.setStyleSheet("")
