"""Settings dialog UI component."""
from PyQt6.QtWidgets import (QDialog, QVBoxLayout, QHBoxLayout, QPushButton,
                              QLabel, QLineEdit, QComboBox, QGroupBox,
                              QFileDialog, QMessageBox, QSpinBox, QTabWidget,
                              QWidget)
from PyQt6.QtCore import Qt, pyqtSignal
from pathlib import Path


class SettingsDialog(QDialog):
    """Dialog for application settings."""

    # Signals
    settings_changed = pyqtSignal()

    SAMPLE_RATES = [44100, 48000]
    OPENAI_MODELS = [
        "gpt-4o-mini",
        "gpt-4o",
        "gpt-4-turbo",
        "gpt-3.5-turbo"
    ]

    def __init__(self, config_manager, text_generator, parent=None):
        """Initialize settings dialog.

        Args:
            config_manager: ConfigManager instance.
            text_generator: TextGenerator instance.
            parent: Parent widget.
        """
        super().__init__(parent)
        self.config = config_manager
        self.text_gen = text_generator
        self.init_ui()
        self.load_settings()

    def init_ui(self):
        """Initialize UI components."""
        self.setWindowTitle("Settings")
        self.setModal(True)
        self.resize(600, 500)

        layout = QVBoxLayout()

        # Tab widget for organized settings
        tabs = QTabWidget()

        # General settings tab
        general_tab = self.create_general_tab()
        tabs.addTab(general_tab, "General")

        # Audio settings tab
        audio_tab = self.create_audio_tab()
        tabs.addTab(audio_tab, "Audio")

        # API settings tab
        api_tab = self.create_api_tab()
        tabs.addTab(api_tab, "API Configuration")

        layout.addWidget(tabs)

        # Buttons
        button_layout = QHBoxLayout()
        button_layout.addStretch()

        self.save_btn = QPushButton("Save")
        self.save_btn.clicked.connect(self.save_settings)
        button_layout.addWidget(self.save_btn)

        self.cancel_btn = QPushButton("Cancel")
        self.cancel_btn.clicked.connect(self.reject)
        button_layout.addWidget(self.cancel_btn)

        layout.addLayout(button_layout)

        self.setLayout(layout)

    def create_general_tab(self) -> QWidget:
        """Create general settings tab."""
        tab = QWidget()
        layout = QVBoxLayout()

        # Base path settings
        path_group = QGroupBox("Storage Location")
        path_layout = QVBoxLayout()

        base_path_layout = QHBoxLayout()
        base_path_layout.addWidget(QLabel("Base Path:"))
        self.base_path_edit = QLineEdit()
        self.base_path_edit.setReadOnly(True)
        base_path_layout.addWidget(self.base_path_edit, 1)

        self.browse_btn = QPushButton("Browse...")
        self.browse_btn.clicked.connect(self.browse_base_path)
        base_path_layout.addWidget(self.browse_btn)

        path_layout.addLayout(base_path_layout)

        path_info = QLabel("This is where all voice samples will be stored.")
        path_info.setWordWrap(True)
        path_layout.addWidget(path_info)

        path_group.setLayout(path_layout)
        layout.addWidget(path_group)

        layout.addStretch()

        tab.setLayout(layout)
        return tab

    def create_audio_tab(self) -> QWidget:
        """Create audio settings tab."""
        tab = QWidget()
        layout = QVBoxLayout()

        # Audio quality settings
        quality_group = QGroupBox("Audio Quality")
        quality_layout = QVBoxLayout()

        sample_rate_layout = QHBoxLayout()
        sample_rate_layout.addWidget(QLabel("Sample Rate:"))
        self.sample_rate_combo = QComboBox()
        for rate in self.SAMPLE_RATES:
            self.sample_rate_combo.addItem(f"{rate} Hz", rate)
        sample_rate_layout.addWidget(self.sample_rate_combo)
        sample_rate_layout.addStretch()

        quality_layout.addLayout(sample_rate_layout)

        sample_rate_info = QLabel(
            "Higher sample rates provide better quality but larger file sizes. "
            "44100 Hz is standard for most applications."
        )
        sample_rate_info.setWordWrap(True)
        quality_layout.addWidget(sample_rate_info)

        quality_group.setLayout(quality_layout)
        layout.addWidget(quality_group)

        layout.addStretch()

        tab.setLayout(layout)
        return tab

    def create_api_tab(self) -> QWidget:
        """Create API settings tab."""
        tab = QWidget()
        layout = QVBoxLayout()

        # OpenAI API settings
        api_group = QGroupBox("OpenAI API Configuration")
        api_layout = QVBoxLayout()

        # API key
        key_layout = QHBoxLayout()
        key_layout.addWidget(QLabel("API Key:"))
        self.api_key_edit = QLineEdit()
        self.api_key_edit.setEchoMode(QLineEdit.EchoMode.Password)
        self.api_key_edit.setPlaceholderText("Enter your OpenAI API key")
        key_layout.addWidget(self.api_key_edit, 1)

        self.test_api_btn = QPushButton("Test Connection")
        self.test_api_btn.clicked.connect(self.test_api_connection)
        key_layout.addWidget(self.test_api_btn)

        api_layout.addLayout(key_layout)

        # Model selection
        model_layout = QHBoxLayout()
        model_layout.addWidget(QLabel("Model:"))
        self.model_combo = QComboBox()
        self.model_combo.addItems(self.OPENAI_MODELS)
        model_layout.addWidget(self.model_combo)
        model_layout.addStretch()

        api_layout.addLayout(model_layout)

        # Info
        api_info = QLabel(
            "Your API key is stored securely in your system keyring. "
            "gpt-4o-mini is recommended for cost-effectiveness."
        )
        api_info.setWordWrap(True)
        api_layout.addWidget(api_info)

        api_group.setLayout(api_layout)
        layout.addWidget(api_group)

        layout.addStretch()

        tab.setLayout(layout)
        return tab

    def browse_base_path(self):
        """Browse for base path."""
        current_path = self.base_path_edit.text()
        if not current_path:
            current_path = str(Path.home())

        path = QFileDialog.getExistingDirectory(
            self,
            "Select Base Path for Samples",
            current_path
        )

        if path:
            self.base_path_edit.setText(path)

    def test_api_connection(self):
        """Test API connection."""
        api_key = self.api_key_edit.text().strip()
        if not api_key:
            QMessageBox.warning(
                self,
                "No API Key",
                "Please enter an API key first."
            )
            return

        # Temporarily update generator with new key
        model = self.model_combo.currentText()
        from llm import TextGenerator
        temp_gen = TextGenerator(api_key, model)

        self.test_api_btn.setEnabled(False)
        self.test_api_btn.setText("Testing...")

        success, error = temp_gen.test_connection()

        self.test_api_btn.setEnabled(True)
        self.test_api_btn.setText("Test Connection")

        if success:
            QMessageBox.information(
                self,
                "Connection Successful",
                "API connection test successful!"
            )
        else:
            QMessageBox.critical(
                self,
                "Connection Failed",
                f"API connection test failed:\n{error}"
            )

    def load_settings(self):
        """Load current settings into dialog."""
        # Base path
        base_path = self.config.get_base_path()
        if base_path:
            self.base_path_edit.setText(str(base_path))

        # Sample rate
        sample_rate = self.config.get_sample_rate()
        index = self.sample_rate_combo.findData(sample_rate)
        if index >= 0:
            self.sample_rate_combo.setCurrentIndex(index)

        # API key (don't display for security, but show if exists)
        api_key = self.config.get_api_key()
        if api_key:
            self.api_key_edit.setPlaceholderText("API key is set (enter new key to change)")

        # Model
        model = self.config.get_openai_model()
        index = self.model_combo.findText(model)
        if index >= 0:
            self.model_combo.setCurrentIndex(index)

    def save_settings(self):
        """Save settings."""
        # Validate base path
        base_path_str = self.base_path_edit.text().strip()
        if not base_path_str:
            QMessageBox.warning(
                self,
                "Invalid Settings",
                "Please select a base path for storing samples."
            )
            return

        base_path = Path(base_path_str)

        # Validate path
        from utils import Validators
        valid, error = Validators.validate_base_path(base_path)
        if not valid:
            QMessageBox.critical(
                self,
                "Invalid Path",
                f"Invalid base path:\n{error}"
            )
            return

        # Save base path
        self.config.set_base_path(base_path)

        # Save sample rate
        sample_rate = self.sample_rate_combo.currentData()
        self.config.set_sample_rate(sample_rate)

        # Save API key if changed
        api_key = self.api_key_edit.text().strip()
        if api_key:
            self.config.set_api_key(api_key)

        # Save model
        model = self.model_combo.currentText()
        self.config.set_openai_model(model)

        # Emit signal that settings changed
        self.settings_changed.emit()

        QMessageBox.information(
            self,
            "Settings Saved",
            "Settings have been saved successfully."
        )

        self.accept()
