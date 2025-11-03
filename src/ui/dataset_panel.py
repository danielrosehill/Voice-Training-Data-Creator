"""Dataset statistics panel UI component."""
from PyQt6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QLabel,
                              QGroupBox, QPushButton)
from PyQt6.QtCore import Qt, QTimer
from PyQt6.QtGui import QFont


class DatasetPanel(QWidget):
    """Panel for displaying dataset statistics."""

    def __init__(self, sample_manager, sample_rate):
        """Initialize dataset panel.

        Args:
            sample_manager: SampleManager instance.
            sample_rate: Sample rate used for recordings.
        """
        super().__init__()
        self.sample_manager = sample_manager
        self.sample_rate = sample_rate

        self.init_ui()
        self.setup_timer()
        self.update_statistics()

    def init_ui(self):
        """Initialize UI components."""
        layout = QVBoxLayout()
        layout.setSpacing(20)
        layout.setContentsMargins(20, 20, 20, 20)

        # Title
        title_label = QLabel("Dataset Overview")
        title_font = title_label.font()
        title_font.setPointSize(16)
        title_font.setBold(True)
        title_label.setFont(title_font)
        title_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        title_label.setStyleSheet("QLabel { color: #1976D2; padding: 10px; }")
        layout.addWidget(title_label)

        # Statistics group
        stats_group = QGroupBox("Training Data Statistics")
        stats_layout = QVBoxLayout()
        stats_layout.setSpacing(25)
        stats_layout.setContentsMargins(30, 30, 30, 30)

        # Sample count
        sample_count_layout = QVBoxLayout()
        sample_count_layout.setSpacing(5)

        sample_count_label = QLabel("Total Samples")
        sample_count_label.setStyleSheet("QLabel { color: #666666; font-size: 12pt; }")
        sample_count_layout.addWidget(sample_count_label)

        self.sample_count_value = QLabel("0")
        sample_count_font = QFont()
        sample_count_font.setPointSize(36)
        sample_count_font.setBold(True)
        self.sample_count_value.setFont(sample_count_font)
        self.sample_count_value.setStyleSheet("QLabel { color: #4CAF50; }")
        self.sample_count_value.setAlignment(Qt.AlignmentFlag.AlignCenter)
        sample_count_layout.addWidget(self.sample_count_value)

        stats_layout.addLayout(sample_count_layout)

        # Separator
        separator_label = QLabel("─" * 50)
        separator_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        separator_label.setStyleSheet("QLabel { color: #E0E0E0; }")
        stats_layout.addWidget(separator_label)

        # Duration
        duration_layout = QVBoxLayout()
        duration_layout.setSpacing(5)

        duration_label = QLabel("Total Duration")
        duration_label.setStyleSheet("QLabel { color: #666666; font-size: 12pt; }")
        duration_layout.addWidget(duration_label)

        self.duration_value = QLabel("0.0 minutes")
        duration_font = QFont()
        duration_font.setPointSize(36)
        duration_font.setBold(True)
        self.duration_value.setFont(duration_font)
        self.duration_value.setStyleSheet("QLabel { color: #2196F3; }")
        self.duration_value.setAlignment(Qt.AlignmentFlag.AlignCenter)
        duration_layout.addWidget(self.duration_value)

        # Additional duration info
        self.duration_hours = QLabel("(0.0 hours)")
        self.duration_hours.setStyleSheet("QLabel { color: #999999; font-size: 11pt; }")
        self.duration_hours.setAlignment(Qt.AlignmentFlag.AlignCenter)
        duration_layout.addWidget(self.duration_hours)

        stats_layout.addLayout(duration_layout)

        stats_group.setLayout(stats_layout)
        layout.addWidget(stats_group)

        # Info section
        info_group = QGroupBox("Dataset Information")
        info_layout = QVBoxLayout()
        info_layout.setSpacing(10)
        info_layout.setContentsMargins(15, 15, 15, 15)

        self.base_path_label = QLabel("Base Path: Not configured")
        self.base_path_label.setStyleSheet("QLabel { font-size: 10pt; }")
        self.base_path_label.setWordWrap(True)
        info_layout.addWidget(self.base_path_label)

        self.last_sample_label = QLabel("Last Sample: N/A")
        self.last_sample_label.setStyleSheet("QLabel { font-size: 10pt; }")
        info_layout.addWidget(self.last_sample_label)

        info_group.setLayout(info_layout)
        layout.addWidget(info_group)

        # Refresh button
        refresh_btn = QPushButton("🔄 Refresh Statistics")
        refresh_btn.setToolTip("Manually refresh dataset statistics")
        refresh_btn.clicked.connect(self.update_statistics)
        refresh_btn.setStyleSheet("""
            QPushButton {
                font-size: 13px;
                padding: 12px;
                background-color: #2196F3;
                color: white;
                border-radius: 5px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #1976D2;
            }
        """)
        layout.addWidget(refresh_btn)

        # Add stretch to push everything to the top
        layout.addStretch()

        self.setLayout(layout)

    def setup_timer(self):
        """Setup timer for automatic statistics updates."""
        self.timer = QTimer()
        self.timer.timeout.connect(self.update_statistics)
        self.timer.start(5000)  # Update every 5 seconds

    def update_statistics(self):
        """Update dataset statistics display."""
        # Get sample count
        total_samples = self.sample_manager.get_total_samples()
        self.sample_count_value.setText(str(total_samples))

        # Get total duration
        total_duration_minutes = self.sample_manager.estimate_total_duration(
            self.sample_rate
        )
        total_duration_hours = total_duration_minutes / 60.0

        self.duration_value.setText(f"{total_duration_minutes:.1f} minutes")
        self.duration_hours.setText(f"({total_duration_hours:.2f} hours)")

        # Update base path
        base_path = str(self.sample_manager.base_path)
        self.base_path_label.setText(f"Base Path: {base_path}")

        # Update last sample info
        if total_samples > 0:
            last_sample_num = self.sample_manager.get_next_sample_number() - 1
            self.last_sample_label.setText(f"Last Sample: #{last_sample_num:03d}")
        else:
            self.last_sample_label.setText("Last Sample: N/A")

    def set_sample_manager(self, sample_manager):
        """Update the sample manager.

        Args:
            sample_manager: New SampleManager instance.
        """
        self.sample_manager = sample_manager
        self.update_statistics()

    def cleanup(self):
        """Clean up resources."""
        if hasattr(self, 'timer') and self.timer.isActive():
            self.timer.stop()
