"""Text generation panel UI component."""
from PyQt6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QPushButton,
                              QLabel, QComboBox, QGroupBox, QTextEdit, QSpinBox,
                              QDoubleSpinBox, QCheckBox, QLineEdit, QMessageBox, QDialog)
from PyQt6.QtCore import Qt, pyqtSignal, QThread
from typing import Optional
from .text_viewer_dialog import TextViewerDialog


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

    def __init__(self, text_generator, recording_panel=None):
        """Initialize text panel.

        Args:
            text_generator: TextGenerator instance.
            recording_panel: Optional RecordingPanel instance for dialog controls.
        """
        super().__init__()
        self.generator = text_generator
        self.recording_panel = recording_panel
        self.worker: Optional[TextGenerationWorker] = None
        self.default_font_size = 14  # Start with larger default font
        self.init_ui()

    def init_ui(self):
        """Initialize UI components."""
        layout = QVBoxLayout()
        layout.setSpacing(15)

        # Text generation controls group
        controls_group = QGroupBox("Text Generation")
        controls_layout = QVBoxLayout()
        controls_layout.setSpacing(12)

        # Duration control
        duration_layout = QHBoxLayout()
        duration_label = QLabel("Target Duration (minutes):")
        duration_label.setToolTip("How long should the text take to read?")
        duration_layout.addWidget(duration_label)
        self.duration_spin = QDoubleSpinBox()
        self.duration_spin.setRange(0.5, 60.0)
        self.duration_spin.setValue(3.0)
        self.duration_spin.setSingleStep(0.5)
        self.duration_spin.setToolTip("Typical voice samples are 3-5 minutes")
        duration_layout.addWidget(self.duration_spin)
        duration_layout.addStretch()
        controls_layout.addLayout(duration_layout)

        # WPM control
        wpm_layout = QHBoxLayout()
        wpm_label = QLabel("Words Per Minute:")
        wpm_label.setToolTip("Speaking speed for calculating text length")
        wpm_layout.addWidget(wpm_label)
        self.wpm_spin = QSpinBox()
        self.wpm_spin.setRange(50, 300)
        self.wpm_spin.setValue(150)
        self.wpm_spin.setSingleStep(10)
        self.wpm_spin.setToolTip("Average speaking speed is 130-170 WPM")
        wpm_layout.addWidget(self.wpm_spin)
        wpm_layout.addStretch()
        controls_layout.addLayout(wpm_layout)

        # Style selector
        style_layout = QHBoxLayout()
        style_label = QLabel("Style:")
        style_label.setToolTip("Choose the speaking style for generated text")
        style_layout.addWidget(style_label)
        self.style_combo = QComboBox()
        self.style_combo.addItems(self.STYLES)
        self.style_combo.setToolTip("Different styles for varied training data")
        style_layout.addWidget(self.style_combo, 1)
        controls_layout.addLayout(style_layout)

        # Add spacing
        controls_layout.addSpacing(8)

        # Dictionary controls
        dict_layout = QVBoxLayout()
        dict_layout.setSpacing(6)
        self.use_dict_checkbox = QCheckBox("Use Custom Dictionary")
        self.use_dict_checkbox.setToolTip("Include specific words in the generated text")
        self.use_dict_checkbox.toggled.connect(self.toggle_dictionary)
        dict_layout.addWidget(self.use_dict_checkbox)

        dict_input_layout = QHBoxLayout()
        dict_words_label = QLabel("Words (comma-separated):")
        dict_words_label.setToolTip("Enter up to 50 words to include")
        dict_input_layout.addWidget(dict_words_label)
        self.dict_input = QLineEdit()
        self.dict_input.setPlaceholderText("e.g., neural, synthesis, phoneme")
        self.dict_input.setToolTip("Technical terms or specific vocabulary you want to practice")
        self.dict_input.setEnabled(False)
        dict_input_layout.addWidget(self.dict_input)
        dict_layout.addLayout(dict_input_layout)

        controls_layout.addLayout(dict_layout)

        # Add spacing
        controls_layout.addSpacing(10)

        # Generation buttons
        button_layout = QHBoxLayout()
        button_layout.setSpacing(10)

        self.generate_btn = QPushButton("🔄 Generate Text")
        self.generate_btn.setToolTip("Generate new text based on settings (Ctrl+G)")
        self.generate_btn.clicked.connect(self.generate_text)
        self.generate_btn.setStyleSheet("""
            QPushButton {
                font-size: 14px;
                padding: 12px 20px;
                background-color: #2196F3;
                color: white;
                border-radius: 5px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #1976D2;
            }
            QPushButton:disabled {
                background-color: #cccccc;
                color: #666666;
            }
        """)
        button_layout.addWidget(self.generate_btn)

        self.regenerate_btn = QPushButton("♻ Regenerate")
        self.regenerate_btn.setToolTip("Generate new text with same settings")
        self.regenerate_btn.clicked.connect(self.generate_text)
        self.regenerate_btn.setEnabled(False)
        self.regenerate_btn.setStyleSheet("""
            QPushButton {
                font-size: 14px;
                padding: 12px 20px;
                background-color: #00BCD4;
                color: white;
                border-radius: 5px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #0097A7;
            }
            QPushButton:disabled {
                background-color: #cccccc;
                color: #666666;
            }
        """)
        button_layout.addWidget(self.regenerate_btn)

        controls_layout.addLayout(button_layout)

        controls_group.setLayout(controls_layout)
        layout.addWidget(controls_group)

        # Text display group with expand button in header
        text_group = QGroupBox()
        text_group_layout = QVBoxLayout()
        text_group_layout.setContentsMargins(0, 0, 0, 0)
        text_group_layout.setSpacing(0)

        # Custom header with expand button
        header_widget = QWidget()
        header_layout = QHBoxLayout()
        header_layout.setContentsMargins(10, 5, 10, 5)
        header_layout.setSpacing(10)

        header_label = QLabel("Generated Text")
        header_label.setStyleSheet("QLabel { font-weight: bold; font-size: 11pt; }")
        header_layout.addWidget(header_label)

        header_layout.addStretch()

        self.expand_btn = QPushButton("⛶ Expand")
        self.expand_btn.setToolTip("Open text in expanded view for easier reading and editing (Ctrl+E)")
        self.expand_btn.clicked.connect(self.open_text_viewer)
        self.expand_btn.setEnabled(False)  # Enable only when there's text
        self.expand_btn.setStyleSheet("""
            QPushButton {
                font-size: 12px;
                padding: 6px 12px;
                background-color: #2196F3;
                color: white;
                border-radius: 3px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #1976D2;
            }
            QPushButton:disabled {
                background-color: #cccccc;
                color: #666666;
            }
        """)
        header_layout.addWidget(self.expand_btn)

        header_widget.setLayout(header_layout)
        header_widget.setStyleSheet("""
            QWidget {
                background-color: #f5f5f5;
                border-bottom: 1px solid #cccccc;
            }
        """)
        text_group_layout.addWidget(header_widget)

        # Text content area
        content_widget = QWidget()
        text_layout = QVBoxLayout()
        text_layout.setSpacing(8)
        text_layout.setContentsMargins(10, 10, 10, 10)

        self.text_edit = QTextEdit()
        self.text_edit.setPlaceholderText("Generated text will appear here. You can edit it before saving.")
        self.text_edit.setToolTip("Edit the text as needed before recording. Click 'Expand' for a larger view.")
        # Much smaller preview - use expand button for reading
        self.text_edit.setMinimumHeight(80)
        self.text_edit.setMaximumHeight(120)
        text_layout.addWidget(self.text_edit)

        # Font size controls and character/word count
        controls_row = QHBoxLayout()
        controls_row.setSpacing(10)

        # Font size controls
        font_controls = QHBoxLayout()
        font_controls.setSpacing(5)

        font_label = QLabel("Text Size:")
        font_label.setStyleSheet("QLabel { color: #666666; font-size: 10pt; }")
        font_controls.addWidget(font_label)

        self.font_smaller_btn = QPushButton("A-")
        self.font_smaller_btn.setToolTip("Decrease text size")
        self.font_smaller_btn.setMaximumWidth(50)
        self.font_smaller_btn.clicked.connect(self.decrease_font_size)
        self.font_smaller_btn.setStyleSheet("""
            QPushButton {
                font-size: 12px;
                padding: 4px 8px;
                background-color: #f5f5f5;
                border: 1px solid #cccccc;
                border-radius: 3px;
            }
            QPushButton:hover {
                background-color: #e0e0e0;
            }
        """)
        font_controls.addWidget(self.font_smaller_btn)

        self.font_size_label = QLabel(f"{self.default_font_size}pt")
        self.font_size_label.setStyleSheet("QLabel { color: #666666; font-size: 10pt; min-width: 35px; }")
        self.font_size_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        font_controls.addWidget(self.font_size_label)

        self.font_bigger_btn = QPushButton("A+")
        self.font_bigger_btn.setToolTip("Increase text size")
        self.font_bigger_btn.setMaximumWidth(50)
        self.font_bigger_btn.clicked.connect(self.increase_font_size)
        self.font_bigger_btn.setStyleSheet("""
            QPushButton {
                font-size: 12px;
                padding: 4px 8px;
                background-color: #f5f5f5;
                border: 1px solid #cccccc;
                border-radius: 3px;
            }
            QPushButton:hover {
                background-color: #e0e0e0;
            }
        """)
        font_controls.addWidget(self.font_bigger_btn)

        controls_row.addLayout(font_controls)
        controls_row.addStretch()

        # Character/word count
        self.count_label = QLabel("Characters: 0 | Words: 0")
        self.count_label.setAlignment(Qt.AlignmentFlag.AlignRight)
        self.count_label.setStyleSheet("QLabel { color: #666666; font-size: 10pt; }")
        controls_row.addWidget(self.count_label)

        text_layout.addLayout(controls_row)

        # Connect text changes to update count and enable expand button
        self.text_edit.textChanged.connect(self.update_counts)
        self.text_edit.textChanged.connect(self.check_expand_button)

        content_widget.setLayout(text_layout)
        text_group_layout.addWidget(content_widget)

        text_group.setLayout(text_group_layout)
        layout.addWidget(text_group)  # Don't stretch - keep compact

        # Add stretch at the bottom to push content to top
        layout.addStretch()

        self.setLayout(layout)

        # Set initial font size after all widgets are created
        self.update_text_font()

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

    def update_text_font(self):
        """Update the text edit font size."""
        font = self.text_edit.font()
        font.setPointSize(self.default_font_size)
        self.text_edit.setFont(font)
        self.font_size_label.setText(f"{self.default_font_size}pt")

    def increase_font_size(self):
        """Increase the text font size."""
        if self.default_font_size < 32:  # Maximum font size
            self.default_font_size += 2
            self.update_text_font()

    def decrease_font_size(self):
        """Decrease the text font size."""
        if self.default_font_size > 8:  # Minimum font size
            self.default_font_size -= 2
            self.update_text_font()

    def check_expand_button(self):
        """Enable or disable expand button based on text content."""
        has_text = bool(self.text_edit.toPlainText().strip())
        self.expand_btn.setEnabled(has_text)

    def open_text_viewer(self):
        """Open the text viewer dialog for expanded editing."""
        current_text = self.text_edit.toPlainText()

        dialog = TextViewerDialog(current_text, self.recording_panel, self)
        if dialog.exec() == QDialog.DialogCode.Accepted:
            # Save the edited text back to the main text area
            edited_text = dialog.get_text()
            self.text_edit.setPlainText(edited_text)
            self.text_generated.emit(edited_text)
