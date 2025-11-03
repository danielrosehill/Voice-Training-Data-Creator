"""Recording panel UI component."""
from PyQt6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QPushButton,
                              QLabel, QComboBox, QGroupBox, QSpacerItem, QSizePolicy)
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

    def init_ui(self):
        """Initialize UI components."""
        layout = QVBoxLayout()
        layout.setSpacing(15)

        # Recording controls group
        controls_group = QGroupBox("Recording Controls")
        controls_layout = QVBoxLayout()
        controls_layout.setSpacing(12)

        # Device selector
        device_layout = QHBoxLayout()
        mic_label = QLabel("Microphone:")
        mic_label.setToolTip("Select your input device for recording")
        device_layout.addWidget(mic_label)

        self.device_combo = QComboBox()
        self.device_combo.setToolTip("Choose the microphone you want to use")
        self.populate_devices()
        self.device_combo.currentIndexChanged.connect(self.on_device_changed)
        device_layout.addWidget(self.device_combo, 1)

        self.test_mic_btn = QPushButton("Test Mic")
        self.test_mic_btn.setToolTip("Test your microphone by recording a 3-second sample")
        self.test_mic_btn.clicked.connect(self.test_microphone)
        self.test_mic_btn.setStyleSheet("QPushButton { padding: 6px 12px; }")
        device_layout.addWidget(self.test_mic_btn)

        controls_layout.addLayout(device_layout)

        # Add spacing
        controls_layout.addSpacing(10)

        # Status label (moved above buttons for better visibility)
        self.status_label = QLabel("Ready to record")
        self.status_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        status_font = QFont()
        status_font.setPointSize(11)
        status_font.setBold(True)
        self.status_label.setFont(status_font)
        controls_layout.addWidget(self.status_label)

        # Duration display
        self.duration_label = QLabel("Duration: 00:00")
        duration_font = QFont()
        duration_font.setPointSize(20)
        duration_font.setBold(True)
        self.duration_label.setFont(duration_font)
        self.duration_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.duration_label.setStyleSheet("QLabel { color: #2196F3; }")
        controls_layout.addWidget(self.duration_label)

        # Add spacing
        controls_layout.addSpacing(10)

        # Recording buttons
        button_layout = QHBoxLayout()
        button_layout.setSpacing(10)

        self.record_btn = QPushButton("⏺ Record")
        self.record_btn.setToolTip("Start recording (Space when ready)")
        self.record_btn.clicked.connect(self.start_recording)
        self.record_btn.setStyleSheet("""
            QPushButton {
                font-size: 14px;
                padding: 12px 20px;
                background-color: #f44336;
                color: white;
                border-radius: 5px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #da190b;
            }
            QPushButton:disabled {
                background-color: #cccccc;
                color: #666666;
            }
        """)
        button_layout.addWidget(self.record_btn)

        self.pause_btn = QPushButton("⏸ Pause")
        self.pause_btn.setToolTip("Pause/resume recording")
        self.pause_btn.clicked.connect(self.toggle_pause)
        self.pause_btn.setEnabled(False)
        self.pause_btn.setStyleSheet("""
            QPushButton {
                font-size: 14px;
                padding: 12px 20px;
                background-color: #FF9800;
                color: white;
                border-radius: 5px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #F57C00;
            }
            QPushButton:disabled {
                background-color: #cccccc;
                color: #666666;
            }
        """)
        button_layout.addWidget(self.pause_btn)

        self.stop_btn = QPushButton("⏹ Stop")
        self.stop_btn.setToolTip("Stop recording and prepare to save")
        self.stop_btn.clicked.connect(self.stop_recording)
        self.stop_btn.setEnabled(False)
        self.stop_btn.setStyleSheet("""
            QPushButton {
                font-size: 14px;
                padding: 12px 20px;
                background-color: #757575;
                color: white;
                border-radius: 5px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #616161;
            }
            QPushButton:disabled {
                background-color: #cccccc;
                color: #666666;
            }
        """)
        button_layout.addWidget(self.stop_btn)

        controls_layout.addLayout(button_layout)

        # Delete button (for bad takes)
        self.delete_btn = QPushButton("🗑 Delete Recording")
        self.delete_btn.setToolTip("Delete the current recording (for bad takes)")
        self.delete_btn.clicked.connect(self.delete_recording)
        self.delete_btn.setEnabled(False)
        self.delete_btn.setStyleSheet("""
            QPushButton {
                font-size: 13px;
                padding: 10px 16px;
                background-color: #d32f2f;
                color: white;
                border-radius: 5px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #b71c1c;
            }
            QPushButton:disabled {
                background-color: #cccccc;
                color: #666666;
            }
        """)
        controls_layout.addWidget(self.delete_btn)

        controls_group.setLayout(controls_layout)
        layout.addWidget(controls_group)

        # Add stretch to push everything to the top
        layout.addStretch()

        self.setLayout(layout)

    def setup_timer(self):
        """Setup timer for duration updates."""
        self.timer = QTimer()
        self.timer.timeout.connect(self.update_duration)

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

        # Enable delete button after recording stops
        if self.current_audio is not None:
            self.delete_btn.setEnabled(True)
            self.recording_finished.emit(self.current_audio)

    def delete_recording(self):
        """Delete the current recording (for bad takes)."""
        if self.current_audio is not None:
            self.clear_audio()
            self.status_label.setText("Recording deleted")
            self.delete_btn.setEnabled(False)

    def update_duration(self):
        """Update duration display."""
        if self.recorder.is_recording and not self.recorder.is_paused:
            self.recording_time += 0.1

        minutes = int(self.recording_time // 60)
        seconds = int(self.recording_time % 60)
        self.duration_label.setText(f"Duration: {minutes:02d}:{seconds:02d}")

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
        self.status_label.setText("Ready to record")
        self.status_label.setStyleSheet("")
        self.delete_btn.setEnabled(False)
