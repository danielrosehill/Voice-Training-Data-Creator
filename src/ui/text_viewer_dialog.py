"""Text viewer dialog for expanded text viewing."""
from PyQt6.QtWidgets import (QDialog, QVBoxLayout, QHBoxLayout, QPushButton,
                              QTextEdit, QLabel)
from PyQt6.QtCore import Qt
from PyQt6.QtGui import QFont, QKeySequence, QShortcut


class TextViewerDialog(QDialog):
    """Modal dialog for viewing and editing text in expanded view."""

    def __init__(self, text: str, parent=None):
        """Initialize text viewer dialog.

        Args:
            text: The text to display.
            parent: Parent widget.
        """
        super().__init__(parent)
        self.setWindowTitle("Text Viewer - Edit and Review")
        self.setModal(True)

        # Make the dialog larger for better readability
        self.resize(900, 700)

        self.init_ui(text)
        self.setup_shortcuts()

    def init_ui(self, text: str):
        """Initialize UI components.

        Args:
            text: The text to display.
        """
        layout = QVBoxLayout()
        layout.setSpacing(15)

        # Instructions
        instructions = QLabel(
            "Use this expanded view to review and edit your text before recording. "
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
