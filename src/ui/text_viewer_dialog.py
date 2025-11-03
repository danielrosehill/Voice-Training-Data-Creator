"""Text viewer dialog for expanded text viewing."""
from PyQt6.QtWidgets import (QDialog, QVBoxLayout, QHBoxLayout, QPushButton,
                              QTextEdit, QLabel, QGroupBox)
from PyQt6.QtCore import Qt, QTimer
from PyQt6.QtGui import QFont, QKeySequence, QShortcut


class TextViewerDialog(QDialog):
    """Modal dialog for viewing and editing text in expanded view."""

    def __init__(self, text: str, recording_panel=None, parent=None):
        """Initialize text viewer dialog.

        Args:
            text: The text to display.
            recording_panel: Optional RecordingPanel for controlling recording from dialog.
            parent: Parent widget.
        """
        super().__init__(parent)
        self.setWindowTitle("Text Viewer - Edit and Review")
        self.setModal(True)
        self.recording_panel = recording_panel

        # Make the dialog larger for better readability
        self.resize(900, 700)

        self.init_ui(text)
        self.setup_shortcuts()

        # Setup timer to update recording status
        if self.recording_panel:
            self.status_timer = QTimer()
            self.status_timer.timeout.connect(self.update_recording_status)
            self.status_timer.start(100)  # Update every 100ms

    def init_ui(self, text: str):
        """Initialize UI components.

        Args:
            text: The text to display.
        """
        layout = QVBoxLayout()
        layout.setSpacing(15)

        # Instructions
        instructions = QLabel(
            "Use this expanded view to review and edit your text before/during recording. "
            "Changes will be reflected in the main window."
        )
        instructions.setWordWrap(True)
        instructions.setStyleSheet("""
            QLabel {
                padding: 10px;
                background-color: #E3F2FD;
                border-radius: 5px;
                color: #1565C0;
            }
        """)
        layout.addWidget(instructions)

        # Recording controls (if recording panel provided)
        if self.recording_panel:
            rec_group = QGroupBox("Recording Controls")
            rec_layout = QVBoxLayout()
            rec_layout.setSpacing(10)

            # Status label
            self.rec_status_label = QLabel("Ready to record")
            self.rec_status_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
            status_font = QFont()
            status_font.setPointSize(11)
            status_font.setBold(True)
            self.rec_status_label.setFont(status_font)
            rec_layout.addWidget(self.rec_status_label)

            # Recording buttons
            rec_button_layout = QHBoxLayout()
            rec_button_layout.setSpacing(10)

            self.rec_pause_btn = QPushButton("⏸ Pause")
            self.rec_pause_btn.setToolTip("Pause/resume recording")
            self.rec_pause_btn.clicked.connect(self.toggle_pause_recording)
            self.rec_pause_btn.setEnabled(False)
            self.rec_pause_btn.setStyleSheet("""
                QPushButton {
                    font-size: 13px;
                    padding: 10px 16px;
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
            rec_button_layout.addWidget(self.rec_pause_btn)

            self.rec_stop_btn = QPushButton("⏹ Stop")
            self.rec_stop_btn.setToolTip("Stop recording")
            self.rec_stop_btn.clicked.connect(self.stop_recording)
            self.rec_stop_btn.setEnabled(False)
            self.rec_stop_btn.setStyleSheet("""
                QPushButton {
                    font-size: 13px;
                    padding: 10px 16px;
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
            rec_button_layout.addWidget(self.rec_stop_btn)

            rec_layout.addLayout(rec_button_layout)
            rec_group.setLayout(rec_layout)
            layout.addWidget(rec_group)

        # Text editor
        self.text_edit = QTextEdit()
        self.text_edit.setPlainText(text)

        # Set a nice readable font
        font = QFont()
        font.setPointSize(16)  # Larger default for easier reading
        font.setFamily("Segoe UI")
        self.text_edit.setFont(font)

        # Add some padding for better readability
        self.text_edit.setStyleSheet("""
            QTextEdit {
                padding: 15px;
                line-height: 1.6;
                border: 1px solid #cccccc;
                border-radius: 5px;
            }
        """)

        layout.addWidget(self.text_edit, 1)  # Give it most of the space

        # Font size controls and stats
        controls_row = QHBoxLayout()
        controls_row.setSpacing(10)

        # Font size controls
        font_controls = QHBoxLayout()
        font_controls.setSpacing(5)

        font_label = QLabel("Text Size:")
        font_label.setStyleSheet("QLabel { color: #666666; font-size: 11pt; }")
        font_controls.addWidget(font_label)

        self.font_smaller_btn = QPushButton("A-")
        self.font_smaller_btn.setToolTip("Decrease text size (Ctrl+-)")
        self.font_smaller_btn.setMaximumWidth(50)
        self.font_smaller_btn.clicked.connect(self.decrease_font_size)
        self.font_smaller_btn.setStyleSheet("""
            QPushButton {
                font-size: 13px;
                padding: 6px 10px;
                background-color: #f5f5f5;
                border: 1px solid #cccccc;
                border-radius: 3px;
            }
            QPushButton:hover {
                background-color: #e0e0e0;
            }
        """)
        font_controls.addWidget(self.font_smaller_btn)

        self.font_size_label = QLabel("16pt")
        self.font_size_label.setStyleSheet("QLabel { color: #666666; font-size: 11pt; min-width: 40px; }")
        self.font_size_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        font_controls.addWidget(self.font_size_label)

        self.font_bigger_btn = QPushButton("A+")
        self.font_bigger_btn.setToolTip("Increase text size (Ctrl++)")
        self.font_bigger_btn.setMaximumWidth(50)
        self.font_bigger_btn.clicked.connect(self.increase_font_size)
        self.font_bigger_btn.setStyleSheet("""
            QPushButton {
                font-size: 13px;
                padding: 6px 10px;
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
        self.count_label = QLabel()
        self.update_counts()
        self.count_label.setAlignment(Qt.AlignmentFlag.AlignRight)
        self.count_label.setStyleSheet("QLabel { color: #666666; font-size: 11pt; }")
        controls_row.addWidget(self.count_label)

        # Connect text changes to update count
        self.text_edit.textChanged.connect(self.update_counts)

        layout.addLayout(controls_row)

        # Buttons
        button_layout = QHBoxLayout()
        button_layout.setSpacing(10)

        button_layout.addStretch()

        cancel_btn = QPushButton("Cancel")
        cancel_btn.setToolTip("Close without saving changes (Esc)")
        cancel_btn.clicked.connect(self.reject)
        cancel_btn.setStyleSheet("""
            QPushButton {
                font-size: 13px;
                padding: 10px 20px;
                background-color: #757575;
                color: white;
                border-radius: 5px;
                font-weight: bold;
                min-width: 100px;
            }
            QPushButton:hover {
                background-color: #616161;
            }
        """)
        button_layout.addWidget(cancel_btn)

        save_btn = QPushButton("Save Changes")
        save_btn.setToolTip("Save changes and close (Ctrl+Enter)")
        save_btn.clicked.connect(self.accept)
        save_btn.setStyleSheet("""
            QPushButton {
                font-size: 13px;
                padding: 10px 20px;
                background-color: #4CAF50;
                color: white;
                border-radius: 5px;
                font-weight: bold;
                min-width: 100px;
            }
            QPushButton:hover {
                background-color: #45a049;
            }
        """)
        button_layout.addWidget(save_btn)

        layout.addLayout(button_layout)

        self.setLayout(layout)

    def setup_shortcuts(self):
        """Setup keyboard shortcuts."""
        # Ctrl+Enter to save
        save_shortcut = QShortcut(QKeySequence("Ctrl+Return"), self)
        save_shortcut.activated.connect(self.accept)

        # Ctrl+Plus to increase font
        increase_shortcut = QShortcut(QKeySequence.StandardKey.ZoomIn, self)
        increase_shortcut.activated.connect(self.increase_font_size)

        # Ctrl+Minus to decrease font
        decrease_shortcut = QShortcut(QKeySequence.StandardKey.ZoomOut, self)
        decrease_shortcut.activated.connect(self.decrease_font_size)

    def get_text(self) -> str:
        """Get the edited text.

        Returns:
            The text content.
        """
        return self.text_edit.toPlainText()

    def update_counts(self):
        """Update character and word counts."""
        text = self.text_edit.toPlainText()
        char_count = len(text)
        word_count = len(text.split()) if text.strip() else 0

        # Calculate estimated reading time
        wpm = 150  # Average reading speed
        minutes = word_count / wpm if word_count > 0 else 0

        self.count_label.setText(
            f"Characters: {char_count} | Words: {word_count} | "
            f"Estimated: {minutes:.1f} min"
        )

    def increase_font_size(self):
        """Increase the text font size."""
        font = self.text_edit.font()
        current_size = font.pointSize()
        if current_size < 32:  # Maximum font size
            new_size = current_size + 2
            font.setPointSize(new_size)
            self.text_edit.setFont(font)
            self.font_size_label.setText(f"{new_size}pt")

    def decrease_font_size(self):
        """Decrease the text font size."""
        font = self.text_edit.font()
        current_size = font.pointSize()
        if current_size > 8:  # Minimum font size
            new_size = current_size - 2
            font.setPointSize(new_size)
            self.text_edit.setFont(font)
            self.font_size_label.setText(f"{new_size}pt")

    def update_recording_status(self):
        """Update recording status and button states."""
        if not self.recording_panel:
            return

        recorder = self.recording_panel.recorder

        if recorder.is_recording:
            self.rec_pause_btn.setEnabled(True)
            self.rec_stop_btn.setEnabled(True)

            if recorder.is_paused:
                self.rec_status_label.setText("⏸ Recording Paused")
                self.rec_status_label.setStyleSheet("QLabel { color: orange; font-weight: bold; }")
                self.rec_pause_btn.setText("▶ Resume")
            else:
                self.rec_status_label.setText("🔴 Recording...")
                self.rec_status_label.setStyleSheet("QLabel { color: red; font-weight: bold; }")
                self.rec_pause_btn.setText("⏸ Pause")
        else:
            self.rec_pause_btn.setEnabled(False)
            self.rec_stop_btn.setEnabled(False)
            self.rec_status_label.setText("Ready to record")
            self.rec_status_label.setStyleSheet("")

    def toggle_pause_recording(self):
        """Toggle pause/resume recording."""
        if self.recording_panel:
            self.recording_panel.toggle_pause()

    def stop_recording(self):
        """Stop recording."""
        if self.recording_panel:
            self.recording_panel.stop_recording()

    def closeEvent(self, event):
        """Handle dialog close event."""
        # Stop the status timer
        if self.recording_panel and hasattr(self, 'status_timer'):
            self.status_timer.stop()
        super().closeEvent(event)
