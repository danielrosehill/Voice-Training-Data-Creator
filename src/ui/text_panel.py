"""Text generation panel UI component."""
from PyQt6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QPushButton,
                              QLabel, QComboBox, QGroupBox, QTextEdit, QSpinBox,
                              QDoubleSpinBox, QCheckBox, QLineEdit, QMessageBox)
from PyQt6.QtCore import Qt, pyqtSignal, QThread
from typing import Optional


class TextGenerationWorker(QThread):
    """Worker thread for text generation."""

    finished = pyqtSignal(str, str)  # text, error

    def __init__(self, generator, duration, wpm, style, dictionary):
        super().__init__()
        self.generator = generator
        self.duration = duration
        self.wpm = wpm
        self.style = style
        self.dictionary = dictionary

    def run(self):
        """Run text generation."""
        text, error = self.generator.generate_text(
            duration_minutes=self.duration,
            wpm=self.wpm,
            style=self.style,
            dictionary=self.dictionary
        )
        self.finished.emit(text or "", error or "")


class TextPanel(QWidget):
    """Panel for text generation controls."""

    # Signals
    text_generated = pyqtSignal(str)

    STYLES = [
        "General Purpose",
        "Colloquial",
        "Voice Note",
        "Technical",
        "Prose"
    ]

    def __init__(self, text_generator):
        """Initialize text panel.

        Args:
            text_generator: TextGenerator instance.
        """
        super().__init__()
        self.generator = text_generator
        self.worker: Optional[TextGenerationWorker] = None
        self.init_ui()

    def init_ui(self):
        """Initialize UI components."""
        layout = QVBoxLayout()

        # Text generation controls group
        controls_group = QGroupBox("Text Generation")
        controls_layout = QVBoxLayout()

        # Duration control
        duration_layout = QHBoxLayout()
        duration_layout.addWidget(QLabel("Target Duration (minutes):"))
        self.duration_spin = QDoubleSpinBox()
        self.duration_spin.setRange(0.5, 60.0)
        self.duration_spin.setValue(3.0)
        self.duration_spin.setSingleStep(0.5)
        duration_layout.addWidget(self.duration_spin)
        duration_layout.addStretch()
        controls_layout.addLayout(duration_layout)

        # WPM control
        wpm_layout = QHBoxLayout()
        wpm_layout.addWidget(QLabel("Words Per Minute:"))
        self.wpm_spin = QSpinBox()
        self.wpm_spin.setRange(50, 300)
        self.wpm_spin.setValue(150)
        self.wpm_spin.setSingleStep(10)
        wpm_layout.addWidget(self.wpm_spin)
        wpm_layout.addStretch()
        controls_layout.addLayout(wpm_layout)

        # Style selector
        style_layout = QHBoxLayout()
        style_layout.addWidget(QLabel("Style:"))
        self.style_combo = QComboBox()
        self.style_combo.addItems(self.STYLES)
        style_layout.addWidget(self.style_combo, 1)
        controls_layout.addLayout(style_layout)

        # Dictionary controls
        dict_layout = QVBoxLayout()
        self.use_dict_checkbox = QCheckBox("Use Custom Dictionary")
        self.use_dict_checkbox.toggled.connect(self.toggle_dictionary)
        dict_layout.addWidget(self.use_dict_checkbox)

        dict_input_layout = QHBoxLayout()
        dict_input_layout.addWidget(QLabel("Words (comma-separated):"))
        self.dict_input = QLineEdit()
        self.dict_input.setPlaceholderText("e.g., neural, synthesis, phoneme")
        self.dict_input.setEnabled(False)
        dict_input_layout.addWidget(self.dict_input)
        dict_layout.addLayout(dict_input_layout)

        controls_layout.addLayout(dict_layout)

        # Generation buttons
        button_layout = QHBoxLayout()

        self.generate_btn = QPushButton("🔄 Generate Text")
        self.generate_btn.clicked.connect(self.generate_text)
        self.generate_btn.setStyleSheet("QPushButton { font-size: 14px; padding: 10px; }")
        button_layout.addWidget(self.generate_btn)

        self.regenerate_btn = QPushButton("♻ Regenerate")
        self.regenerate_btn.clicked.connect(self.generate_text)
        self.regenerate_btn.setEnabled(False)
        button_layout.addWidget(self.regenerate_btn)

        controls_layout.addLayout(button_layout)

        controls_group.setLayout(controls_layout)
        layout.addWidget(controls_group)

        # Text display group
        text_group = QGroupBox("Generated Text")
        text_layout = QVBoxLayout()

        self.text_edit = QTextEdit()
        self.text_edit.setPlaceholderText("Generated text will appear here. You can edit it before saving.")
        text_layout.addWidget(self.text_edit)

        # Character/word count
        self.count_label = QLabel("Characters: 0 | Words: 0")
        self.count_label.setAlignment(Qt.AlignmentFlag.AlignRight)
        text_layout.addWidget(self.count_label)

        # Connect text changes to update count
        self.text_edit.textChanged.connect(self.update_counts)

        text_group.setLayout(text_layout)
        layout.addWidget(text_group, 1)  # Give more space to text display

        self.setLayout(layout)

    def toggle_dictionary(self, checked: bool):
        """Toggle dictionary input.

        Args:
            checked: Whether dictionary is enabled.
        """
        self.dict_input.setEnabled(checked)

    def generate_text(self):
        """Generate text using LLM."""
        # Get parameters
        duration = self.duration_spin.value()
        wpm = self.wpm_spin.value()
        style = self.style_combo.currentText()

        # Get dictionary if enabled
        dictionary = None
        if self.use_dict_checkbox.isChecked():
            dict_text = self.dict_input.text().strip()
            if dict_text:
                dictionary = [w.strip() for w in dict_text.split(',') if w.strip()]

                # Validate dictionary
                if len(dictionary) > 50:
                    QMessageBox.warning(
                        self,
                        "Dictionary Too Large",
                        "Dictionary contains more than 50 words. Consider reducing for better results."
                    )
                    return

        # Disable controls during generation
        self.set_controls_enabled(False)
        self.generate_btn.setText("⏳ Generating...")
        self.text_edit.setPlaceholderText("Generating text, please wait...")

        # Start generation in worker thread
        self.worker = TextGenerationWorker(
            self.generator,
            duration,
            wpm,
            style,
            dictionary
        )
        self.worker.finished.connect(self.on_generation_finished)
        self.worker.start()

    def on_generation_finished(self, text: str, error: str):
        """Handle generation completion.

        Args:
            text: Generated text.
            error: Error message if any.
        """
        self.set_controls_enabled(True)
        self.generate_btn.setText("🔄 Generate Text")
        self.text_edit.setPlaceholderText("Generated text will appear here. You can edit it before saving.")

        if error:
            QMessageBox.critical(
                self,
                "Generation Error",
                f"Failed to generate text:\n{error}"
            )
        elif text:
            self.text_edit.setPlainText(text)
            self.regenerate_btn.setEnabled(True)
            self.text_generated.emit(text)
        else:
            QMessageBox.warning(
                self,
                "No Text Generated",
                "No text was generated. Please try again."
            )

        self.worker = None

    def set_controls_enabled(self, enabled: bool):
        """Enable or disable controls.

        Args:
            enabled: Whether to enable controls.
        """
        self.duration_spin.setEnabled(enabled)
        self.wpm_spin.setEnabled(enabled)
        self.style_combo.setEnabled(enabled)
        self.use_dict_checkbox.setEnabled(enabled)
        self.dict_input.setEnabled(enabled and self.use_dict_checkbox.isChecked())
        self.generate_btn.setEnabled(enabled)
        self.regenerate_btn.setEnabled(enabled)

    def update_counts(self):
        """Update character and word counts."""
        text = self.text_edit.toPlainText()
        char_count = len(text)
        word_count = len(text.split()) if text.strip() else 0
        self.count_label.setText(f"Characters: {char_count} | Words: {word_count}")

    def get_text(self) -> str:
        """Get the current text.

        Returns:
            Text content.
        """
        return self.text_edit.toPlainText()

    def clear_text(self):
        """Clear the text content."""
        self.text_edit.clear()
        self.regenerate_btn.setEnabled(False)

    def set_text(self, text: str):
        """Set the text content.

        Args:
            text: Text to set.
        """
        self.text_edit.setPlainText(text)
