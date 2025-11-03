"""Main application window."""
from PyQt6.QtWidgets import (QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
                              QPushButton, QLabel, QMessageBox, QGroupBox,
                              QStatusBar, QMenuBar, QFileDialog, QTabWidget)
from PyQt6.QtCore import Qt, QTimer
from PyQt6.QtGui import QAction, QKeySequence, QShortcut
from pathlib import Path
import tempfile
import numpy as np

from .recording_panel import RecordingPanel
from .text_panel import TextPanel
from .settings_dialog import SettingsDialog
from .dataset_panel import DatasetPanel


class MainWindow(QMainWindow):
    """Main application window."""

    def __init__(self, config, audio_recorder, device_manager, text_generator, sample_manager):
        """Initialize main window.

        Args:
            config: ConfigManager instance.
            audio_recorder: AudioRecorder instance.
            device_manager: DeviceManager instance.
            text_generator: TextGenerator instance.
            sample_manager: SampleManager instance.
        """
        super().__init__()
        self.config = config
        self.recorder = audio_recorder
        self.device_manager = device_manager
        self.text_gen = text_generator
        self.sample_manager = sample_manager

        self.current_audio: np.ndarray = None
        self.session_samples = 0

        self.init_ui()
        self.setup_menu()
        self.setup_shortcuts()
        self.check_initial_config()

        # Update statistics periodically
        self.stats_timer = QTimer()
        self.stats_timer.timeout.connect(self.update_statistics)
        self.stats_timer.start(5000)  # Update every 5 seconds

    def init_ui(self):
        """Initialize UI components."""
        self.setWindowTitle("Voice Training Data Creator")
        self.resize(1200, 850)

        # Create central widget
        central_widget = QWidget()
        self.setCentralWidget(central_widget)

        main_layout = QVBoxLayout()
        main_layout.setSpacing(15)
        main_layout.setContentsMargins(15, 15, 15, 15)

        # Title
        title_label = QLabel("Voice Training Data Creator")
        title_font = title_label.font()
        title_font.setPointSize(20)
        title_font.setBold(True)
        title_label.setFont(title_font)
        title_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        title_label.setStyleSheet("QLabel { color: #1976D2; padding: 10px; }")
        main_layout.addWidget(title_label)

        # Create tab widget
        self.tabs = QTabWidget()
        self.tabs.setDocumentMode(True)

        # Tab 1: Recording and Text Generation
        recording_tab = QWidget()
        recording_layout = QVBoxLayout()
        recording_layout.setSpacing(15)

        # Main content - horizontal split
        content_layout = QHBoxLayout()
        content_layout.setSpacing(15)

        # Left side - Recording
        self.recording_panel = RecordingPanel(self.recorder, self.device_manager)
        self.recording_panel.recording_finished.connect(self.on_recording_finished)
        content_layout.addWidget(self.recording_panel, 1)

        # Right side - Text generation
        self.text_panel = TextPanel(self.text_gen)
        content_layout.addWidget(self.text_panel, 1)

        recording_layout.addLayout(content_layout, 1)

        # Session statistics
        stats_group = QGroupBox("Session Statistics")
        stats_layout = QHBoxLayout()
        stats_layout.setSpacing(20)
        stats_layout.setContentsMargins(15, 10, 15, 10)

        self.session_label = QLabel("This Session: 0 samples")
        self.session_label.setStyleSheet("QLabel { font-size: 11pt; }")
        self.session_label.setToolTip("Number of samples recorded in this session")
        stats_layout.addWidget(self.session_label)

        self.total_label = QLabel("Total: 0 samples")
        self.total_label.setStyleSheet("QLabel { font-size: 11pt; font-weight: bold; }")
        self.total_label.setToolTip("Total samples in your dataset")
        stats_layout.addWidget(self.total_label)

        self.duration_label = QLabel("Total Duration: 0.0 min")
        self.duration_label.setStyleSheet("QLabel { font-size: 11pt; }")
        self.duration_label.setToolTip("Total audio duration in your dataset")
        stats_layout.addWidget(self.duration_label)

        stats_layout.addStretch()

        stats_group.setLayout(stats_layout)
        recording_layout.addWidget(stats_group)

        # Save button
        self.save_btn = QPushButton("💾 Save Sample (Ctrl+Enter)")
        self.save_btn.setToolTip("Save the current recording and text as a training sample")
        self.save_btn.clicked.connect(self.save_sample)
        self.save_btn.setStyleSheet("""
            QPushButton {
                font-size: 16px;
                padding: 18px;
                background-color: #4CAF50;
                color: white;
                border-radius: 5px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #45a049;
            }
            QPushButton:disabled {
                background-color: #cccccc;
                color: #666666;
            }
        """)
        self.save_btn.setEnabled(False)
        recording_layout.addWidget(self.save_btn)

        recording_tab.setLayout(recording_layout)
        self.tabs.addTab(recording_tab, "📝 Record & Generate")

        # Tab 2: Dataset Overview
        self.dataset_panel = DatasetPanel(self.sample_manager, self.recorder.sample_rate)
        self.tabs.addTab(self.dataset_panel, "📊 Dataset")

        # Add tabs to main layout
        main_layout.addWidget(self.tabs)

        central_widget.setLayout(main_layout)

        # Status bar
        self.status_bar = QStatusBar()
        self.setStatusBar(self.status_bar)
        self.update_status_bar()

    def setup_menu(self):
        """Setup menu bar."""
        menubar = self.menuBar()

        # File menu
        file_menu = menubar.addMenu("&File")

        settings_action = QAction("&Settings", self)
        settings_action.setShortcut(QKeySequence("Ctrl+,"))
        settings_action.triggered.connect(self.open_settings)
        file_menu.addAction(settings_action)

        file_menu.addSeparator()

        exit_action = QAction("E&xit", self)
        exit_action.setShortcut(QKeySequence("Ctrl+Q"))
        exit_action.triggered.connect(self.close)
        file_menu.addAction(exit_action)

        # Help menu
        help_menu = menubar.addMenu("&Help")

        about_action = QAction("&About", self)
        about_action.triggered.connect(self.show_about)
        help_menu.addAction(about_action)

    def setup_shortcuts(self):
        """Setup keyboard shortcuts."""
        # Save shortcut
        save_shortcut = QShortcut(QKeySequence("Ctrl+Return"), self)
        save_shortcut.activated.connect(self.save_sample)

        # Generate text shortcut
        gen_shortcut = QShortcut(QKeySequence("Ctrl+G"), self)
        gen_shortcut.activated.connect(self.text_panel.generate_text)

        # Record shortcut (space when not typing)
        # Note: This is simplified; proper implementation would need focus management

    def check_initial_config(self):
        """Check if initial configuration is needed."""
        if not self.config.is_configured():
            QMessageBox.information(
                self,
                "Welcome",
                "Welcome to Voice Training Data Creator!\n\n"
                "Please configure your base path and API settings to get started."
            )
            self.open_settings()

    def open_settings(self):
        """Open settings dialog."""
        dialog = SettingsDialog(self.config, self.text_gen, self)
        dialog.settings_changed.connect(self.on_settings_changed)
        dialog.exec()

    def on_settings_changed(self):
        """Handle settings changes."""
        # Update sample manager with new base path
        base_path = self.config.get_base_path()
        if base_path:
            from storage import SampleManager
            self.sample_manager = SampleManager(base_path)
            # Update dataset panel with new sample manager
            self.dataset_panel.set_sample_manager(self.sample_manager)

        # Update text generator with new API settings
        api_key = self.config.get_api_key()
        model = self.config.get_openai_model()

        # Always recreate text generator when settings change
        if not api_key:
            api_key = ""

        from llm import TextGenerator
        try:
            self.text_gen = TextGenerator(api_key, model)
            self.text_panel.generator = self.text_gen
            print(f"Text generator updated with API key (length: {len(api_key)})")
        except Exception as e:
            print(f"Error updating text generator: {e}")

        # Update recorder sample rate
        sample_rate = self.config.get_sample_rate()
        self.recorder.sample_rate = sample_rate
        self.dataset_panel.sample_rate = sample_rate

        self.update_status_bar()
        self.update_statistics()

    def on_recording_finished(self, audio_data: np.ndarray):
        """Handle recording completion.

        Args:
            audio_data: Recorded audio data.
        """
        self.current_audio = audio_data
        self.check_save_enabled()

        # Run quality checks
        from utils import Validators
        if Validators.detect_clipping(audio_data):
            QMessageBox.warning(
                self,
                "Audio Clipping Detected",
                "The audio signal may be clipping. Consider reducing your microphone volume."
            )

        if Validators.detect_long_silence(audio_data, sample_rate=self.recorder.sample_rate):
            QMessageBox.warning(
                self,
                "Long Silence Detected",
                "The recording contains a long period of silence. You may want to re-record."
            )

    def check_save_enabled(self):
        """Check if save button should be enabled."""
        has_audio = self.current_audio is not None
        has_text = bool(self.text_panel.get_text().strip())

        self.save_btn.setEnabled(has_audio and has_text)

    def save_sample(self):
        """Save the current sample."""
        if not self.config.is_configured():
            QMessageBox.warning(
                self,
                "Not Configured",
                "Please configure the application in Settings first."
            )
            self.open_settings()
            return

        # Validate audio and text
        from utils import Validators
        text = self.text_panel.get_text()

        valid, error = Validators.validate_sample(self.current_audio, text)
        if not valid:
            QMessageBox.critical(
                self,
                "Validation Error",
                f"Cannot save sample:\n{error}"
            )
            return

        # Check disk space
        base_path = self.config.get_base_path()
        has_space, space_error = Validators.check_disk_space(base_path)
        if not has_space:
            QMessageBox.critical(
                self,
                "Insufficient Disk Space",
                space_error
            )
            return

        # Save audio to temporary file first
        temp_audio_path = Path(tempfile.gettempdir()) / "temp_recording.wav"
        if not self.recorder.save_audio(self.current_audio, temp_audio_path):
            QMessageBox.critical(
                self,
                "Save Error",
                "Failed to save audio file."
            )
            return

        # Create metadata
        metadata = self.sample_manager.create_metadata({
            'duration_minutes': self.text_panel.duration_spin.value(),
            'wpm': self.text_panel.wpm_spin.value(),
            'style': self.text_panel.style_combo.currentText(),
            'model': self.config.get_openai_model(),
            'sample_rate': self.recorder.sample_rate
        })

        # Save sample
        success, error = self.sample_manager.save_sample(
            temp_audio_path,
            text,
            metadata
        )

        if success:
            self.session_samples += 1
            self.update_statistics()

            # Clear current data
            self.current_audio = None
            self.recording_panel.clear_audio()
            self.text_panel.clear_text()
            self.check_save_enabled()

            # Show success message
            sample_num = self.sample_manager.get_next_sample_number() - 1
            QMessageBox.information(
                self,
                "Sample Saved",
                f"Sample #{sample_num} saved successfully!"
            )

            self.status_bar.showMessage(f"Sample #{sample_num} saved", 3000)
        else:
            QMessageBox.critical(
                self,
                "Save Error",
                f"Failed to save sample:\n{error}"
            )

    def update_statistics(self):
        """Update session statistics display."""
        if not self.config.is_configured():
            return

        total_samples = self.sample_manager.get_total_samples()
        total_duration = self.sample_manager.estimate_total_duration(
            self.recorder.sample_rate
        )

        self.session_label.setText(f"This Session: {self.session_samples} samples")
        self.total_label.setText(f"Total: {total_samples} samples")
        self.duration_label.setText(f"Total Duration: {total_duration:.1f} min")

    def update_status_bar(self):
        """Update status bar with configuration info."""
        if self.config.is_configured():
            base_path = self.config.get_base_path()
            self.status_bar.showMessage(f"Base Path: {base_path}")
        else:
            self.status_bar.showMessage("Not configured - please set up in Settings")

    def show_about(self):
        """Show about dialog."""
        QMessageBox.about(
            self,
            "About Voice Training Data Creator",
            "<h2>Voice Training Data Creator</h2>"
            "<p>Version 1.0</p>"
            "<p>A GUI tool for creating voice training datasets with synthetic text generation.</p>"
            "<p>Features:</p>"
            "<ul>"
            "<li>High-quality audio recording</li>"
            "<li>AI-powered text generation</li>"
            "<li>Multiple style options</li>"
            "<li>Custom vocabulary support</li>"
            "</ul>"
        )

    def closeEvent(self, event):
        """Handle application close.

        Args:
            event: Close event.
        """
        # Stop recording if active
        if self.recorder.is_recording:
            reply = QMessageBox.question(
                self,
                "Recording in Progress",
                "Recording is still in progress. Stop and exit?",
                QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
            )

            if reply == QMessageBox.StandardButton.Yes:
                self.cleanup()
                event.accept()
            else:
                event.ignore()
        else:
            self.cleanup()
            event.accept()

    def cleanup(self):
        """Clean up resources before closing."""
        # Stop stats timer
        if hasattr(self, 'stats_timer') and self.stats_timer.isActive():
            self.stats_timer.stop()

        # Stop recording panel timer
        if hasattr(self, 'recording_panel'):
            if hasattr(self.recording_panel, 'timer') and self.recording_panel.timer.isActive():
                self.recording_panel.timer.stop()

        # Stop dataset panel timer
        if hasattr(self, 'dataset_panel'):
            self.dataset_panel.cleanup()

        # Stop any active recording
        if self.recorder.is_recording:
            self.recorder.stop_recording()
