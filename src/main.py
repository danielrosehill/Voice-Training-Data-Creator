#!/usr/bin/env python3
"""Main entry point for Voice Training Data Creator (Flet version)."""
import flet as ft
from pathlib import Path
import threading
import time
import tempfile
import subprocess
import platform

# Flet compatibility: support both old (Colors/Icons) and new (colors/icons)
COLORS = getattr(ft, "colors", None) or getattr(ft, "Colors", None)
ICONS = getattr(ft, "icons", None) or getattr(ft, "Icons", None)

from audio import AudioRecorder, DeviceManager
from storage import ConfigManager, SampleManager
from llm import TextGenerator


class VoiceTrainingApp:
    """Main application class for Flet."""

    def __init__(self, page: ft.Page):
        """Initialize the application.

        Args:
            page: The Flet page instance.
        """
        self.page = page
        self.page.title = "Voice Training Data Creator"
        self.page.window_width = 1280
        self.page.window_height = 900
        self.page.padding = 24
        self.page.theme_mode = ft.ThemeMode.LIGHT

        # Professional color theme
        try:
            self.page.theme = ft.Theme(
                color_scheme_seed=COLORS.BLUE_700,
                use_material3=True,
            )
        except Exception:
            pass

        # Custom color palette for professional look
        self.colors = {
            'primary': COLORS.BLUE_700,
            'primary_light': COLORS.BLUE_400,
            'secondary': COLORS.INDIGO_700,
            'accent': COLORS.CYAN_600,
            'success': COLORS.GREEN_600,
            'warning': COLORS.ORANGE_600,
            'error': COLORS.RED_600,
            'text_primary': COLORS.GREY_900,
            'text_secondary': COLORS.GREY_600,
            'background': COLORS.GREY_50,
            'surface': COLORS.WHITE,
            'border': COLORS.GREY_300,
        }

        # Initialize core components
        self.config = ConfigManager()
        self.audio_recorder = AudioRecorder(sample_rate=self.config.get_sample_rate())
        self.device_manager = DeviceManager()

        # Initialize text generator
        api_key = self.config.get_api_key() or ""
        model = self.config.get_openai_model()
        try:
            self.text_generator = TextGenerator(api_key, model)
        except Exception as e:
            print(f"Warning: Failed to initialize text generator: {e}")
            self.text_generator = TextGenerator("", model)

        # Initialize sample manager
        base_path = self.config.get_base_path()
        if base_path:
            self.sample_manager = SampleManager(base_path)
        else:
            self.sample_manager = SampleManager(Path.home() / "voice_samples")

        # Session state
        self.current_audio = None
        self.session_samples = 0
        self._record_timer_thread = None
        self._record_timer_stop = threading.Event()

        # Audio playback state
        self.audio_player = None
        self.current_playing_sample = None

        # Build UI
        self.build_ui()

        # Check initial configuration
        if not self.config.is_configured():
            self.show_welcome_dialog()

    def build_ui(self):
        """Build the main UI."""
        # Title with better styling
        title = ft.Container(
            content=ft.Text(
                "Voice Training Data Creator",
                size=32,
                weight=ft.FontWeight.BOLD,
                color=self.colors['primary'],
                text_align=ft.TextAlign.CENTER,
            ),
            padding=ft.padding.only(bottom=16),
        )

        # Create tabs with better styling
        self.tabs = ft.Tabs(
            selected_index=0,
            animation_duration=300,
            label_color=self.colors['primary'],
            indicator_color=self.colors['primary'],
            divider_color=self.colors['border'],
            on_change=self.on_tab_change,
            tabs=[
                ft.Tab(
                    text="Record & Generate",
                    icon=ICONS.MIC,
                    content=self.build_recording_tab(),
                ),
                ft.Tab(
                    text="Dataset",
                    icon=ICONS.ANALYTICS,
                    content=self.build_dataset_tab(),
                ),
                ft.Tab(
                    text="Training Files",
                    icon=ICONS.FOLDER_OPEN,
                    content=self.build_training_files_tab(),
                ),
                ft.Tab(
                    text="Settings",
                    icon=ICONS.SETTINGS,
                    content=self.build_settings_tab(),
                ),
            ],
            expand=True,
        )

        # Status bar with better styling
        self.status_bar = ft.Container(
            content=ft.Text(
                self.get_status_text(),
                size=13,
                color=self.colors['text_secondary'],
            ),
            padding=ft.padding.symmetric(vertical=8, horizontal=12),
            bgcolor=self.colors['surface'],
            border=ft.border.all(1, self.colors['border']),
            border_radius=8,
        )

        # File/dir pickers (overlay components)
        self.dir_picker = ft.FilePicker(on_result=self.on_pick_directory)
        self.page.overlay.append(self.dir_picker)

        # Main layout with better spacing
        self.page.add(
            ft.Column(
                [
                    title,
                    self.tabs,
                    ft.Container(height=12),
                    self.status_bar,
                ],
                expand=True,
                spacing=0,
            )
        )

        # Create recording controls for app bar (initially hidden)
        self.appbar_status_label = ft.Text(
            "Ready",
            size=14,
            weight=ft.FontWeight.W_500,
            color=COLORS.WHITE,
        )

        self.appbar_duration_label = ft.Text(
            "00:00",
            size=16,
            weight=ft.FontWeight.BOLD,
            color=COLORS.WHITE,
        )

        self.appbar_record_btn = ft.IconButton(
            ICONS.FIBER_MANUAL_RECORD,
            tooltip="Start recording",
            on_click=self.start_recording,
            icon_color=COLORS.RED_400,
            icon_size=28,
        )

        self.appbar_pause_btn = ft.IconButton(
            ICONS.PAUSE,
            tooltip="Pause recording",
            on_click=self.toggle_pause,
            icon_color=COLORS.ORANGE_400,
            icon_size=28,
            visible=False,
        )

        self.appbar_stop_btn = ft.IconButton(
            ICONS.STOP,
            tooltip="Stop recording",
            on_click=self.stop_recording,
            icon_color=COLORS.WHITE,
            icon_size=28,
            visible=False,
        )

        self.appbar_retake_btn = ft.IconButton(
            ICONS.REPLAY,
            tooltip="Retake recording",
            on_click=self.retake_recording,
            icon_color=COLORS.ORANGE_400,
            icon_size=28,
            visible=False,
        )

        # Recording controls container (visible only on Record & Generate tab)
        self.appbar_recording_controls = ft.Container(
            content=ft.Row(
                [
                    ft.Container(
                        content=ft.Column(
                            [
                                self.appbar_status_label,
                                self.appbar_duration_label,
                            ],
                            spacing=2,
                            horizontal_alignment=ft.CrossAxisAlignment.END,
                        ),
                        padding=ft.padding.only(right=12),
                    ),
                    self.appbar_record_btn,
                    self.appbar_pause_btn,
                    self.appbar_stop_btn,
                    self.appbar_retake_btn,
                    ft.Container(width=8),  # Spacer before settings icons
                ],
                spacing=8,
                alignment=ft.MainAxisAlignment.END,
            ),
            visible=True,  # Visible by default since we start on recording tab
        )

        # Menu bar with better styling and recording controls
        self.page.appbar = ft.AppBar(
            title=ft.Text("Voice Training Data Creator", size=18, weight=ft.FontWeight.W_600),
            center_title=False,
            bgcolor=self.colors['primary'],
            color=COLORS.WHITE,
            actions=[
                self.appbar_recording_controls,
                ft.IconButton(
                    ICONS.SETTINGS,
                    tooltip="Open Settings",
                    on_click=lambda _: self._go_to_settings(),
                    icon_color=COLORS.WHITE,
                ),
                ft.IconButton(
                    ICONS.BRIGHTNESS_6,
                    tooltip="Toggle Light/Dark Theme",
                    on_click=lambda _: self.toggle_theme(),
                    icon_color=COLORS.WHITE,
                ),
                ft.IconButton(
                    ICONS.INFO,
                    tooltip="About This App",
                    on_click=lambda _: self.show_about(),
                    icon_color=COLORS.WHITE,
                ),
            ],
        )

    def build_recording_tab(self):
        """Build the recording and text generation tab.

        Returns:
            The tab content.
        """
        # Save button - prominent action
        self.save_btn = ft.ElevatedButton(
            "Save Sample",
            icon=ICONS.SAVE,
            on_click=self.save_sample,
            disabled=True,
            bgcolor=self.colors['success'],
            color=COLORS.WHITE,
            height=56,
            style=ft.ButtonStyle(
                shape=ft.RoundedRectangleBorder(radius=8),
                elevation={"": 2, "hovered": 4, "disabled": 0},
                padding=ft.padding.symmetric(horizontal=24, vertical=16),
                text_style=ft.TextStyle(size=16, weight=ft.FontWeight.W_600),
            ),
        )

        # Auto-generate checkbox
        self.autogenerate_checkbox = ft.Checkbox(
            label="Auto-generate next sample after saving",
            value=self.config.get_autogenerate_next(),
            on_change=self.on_autogenerate_toggled,
        )

        # Recording panel (moved above text panel)
        recording_panel = self.build_recording_panel()

        # Text generation panel
        text_panel = self.build_text_panel()

        # Session statistics
        stats = self.build_statistics_panel()

        return ft.Container(
            content=ft.Column(
                [
                    self.save_btn,
                    self.autogenerate_checkbox,
                    recording_panel,
                    text_panel,
                    stats,
                ],
                spacing=15,
                scroll=ft.ScrollMode.AUTO,
            ),
            padding=10,
            expand=True,
        )

    def build_text_panel(self):
        """Build the text generation panel.

        Returns:
            The text panel widget.
        """
        # Controls
        self.duration_field = ft.TextField(
            label="Target Duration (minutes)",
            value="3.0",
            width=200,
            keyboard_type=ft.KeyboardType.NUMBER,
            tooltip="How long you want the generated text to take to read",
        )

        self.wpm_field = ft.TextField(
            label="Words Per Minute",
            value="150",
            width=200,
            keyboard_type=ft.KeyboardType.NUMBER,
            tooltip="Average speaking speed (120-180 is typical)",
        )

        self.style_dropdown = ft.Dropdown(
            label="Style",
            width=300,
            options=[
                ft.dropdown.Option("General Purpose"),
                ft.dropdown.Option("Colloquial"),
                ft.dropdown.Option("Voice Note"),
                ft.dropdown.Option("Technical"),
                ft.dropdown.Option("Prose"),
            ],
            value="General Purpose",
        )

        self.use_dict_checkbox = ft.Checkbox(
            label="Use Custom Dictionary",
            value=False,
            on_change=self.toggle_dictionary,
        )

        self.dict_input = ft.TextField(
            label="Words (comma-separated)",
            hint_text="e.g., neural, synthesis, phoneme",
            disabled=True,
            expand=True,
        )

        # Generate buttons with consistent styling
        self.generate_btn = ft.ElevatedButton(
            "Generate Text",
            icon=ICONS.AUTO_AWESOME,
            on_click=self.generate_text,
            bgcolor=self.colors['primary'],
            color=COLORS.WHITE,
            tooltip="Generate new text using AI based on your parameters",
            style=ft.ButtonStyle(
                shape=ft.RoundedRectangleBorder(radius=8),
                elevation={"": 2, "hovered": 4},
                padding=ft.padding.symmetric(horizontal=20, vertical=12),
            ),
        )

        self.new_sample_btn = ft.ElevatedButton(
            "New Sample",
            icon=ICONS.ADD,
            on_click=self.new_sample,
            disabled=True,
            bgcolor=self.colors['success'],
            color=COLORS.WHITE,
            tooltip="Clear everything and start a completely new sample",
            style=ft.ButtonStyle(
                shape=ft.RoundedRectangleBorder(radius=8),
                elevation={"": 2, "hovered": 4, "disabled": 0},
                padding=ft.padding.symmetric(horizontal=20, vertical=12),
            ),
        )

        self.regenerate_btn = ft.ElevatedButton(
            "Regenerate",
            icon=ICONS.REFRESH,
            on_click=self.generate_text,
            disabled=True,
            bgcolor=self.colors['accent'],
            color=COLORS.WHITE,
            tooltip="Generate different text with the same parameters",
            style=ft.ButtonStyle(
                shape=ft.RoundedRectangleBorder(radius=8),
                elevation={"": 2, "hovered": 4, "disabled": 0},
                padding=ft.padding.symmetric(horizontal=20, vertical=12),
            ),
        )

        # Text display - expandable
        self.text_edit = ft.TextField(
            label="Generated Text",
            multiline=True,
            min_lines=8,
            max_lines=25,
            hint_text="Generated text will appear here. You can edit it before saving.",
            on_change=self.on_text_changed,
            expand=True,
        )

        self.char_count_label = ft.Text("Characters: 0 | Words: 0", size=12, color=COLORS.GREY_700)

        return ft.Card(
            content=ft.Container(
                content=ft.Column(
                    [
                        ft.Text("Text Generation", size=20, weight=ft.FontWeight.BOLD, color=self.colors['text_primary']),
                        ft.Container(height=4),
                        ft.Row([self.duration_field, self.wpm_field, self.style_dropdown], spacing=12),
                        ft.Container(height=4),
                        self.use_dict_checkbox,
                        self.dict_input,
                        ft.Container(height=8),
                        ft.Row([self.generate_btn, self.new_sample_btn, self.regenerate_btn], spacing=12, wrap=True),
                        ft.Divider(height=1, color=self.colors['border']),
                        self.text_edit,
                        self.char_count_label,
                    ],
                    spacing=12,
                ),
                padding=20,
            ),
            elevation=3,
            surface_tint_color=self.colors['primary_light'],
        )

    def build_recording_panel(self):
        """Build the recording controls panel.

        Returns:
            The recording panel widget.
        """
        # Device selector
        devices = self.device_manager.get_input_devices()
        device_options = [
            ft.dropdown.Option(text=f"{d['name']} (Device {d['index']})", key=str(d['index']))
            for d in devices
        ]

        # Set default to preferred device if available
        preferred_device = self.config.get_preferred_device()
        default_device = None
        if preferred_device and preferred_device["device_index"] is not None:
            # Check if preferred device is still available
            if any(d['index'] == preferred_device["device_index"] for d in devices):
                default_device = str(preferred_device["device_index"])

        if default_device is None and device_options:
            default_device = device_options[0].key

        self.device_dropdown = ft.Dropdown(
            label="Microphone",
            options=device_options,
            value=default_device,
            expand=True,
        )

        self.test_mic_btn = ft.ElevatedButton(
            "Test Mic",
            icon=ICONS.MIC_NONE,
            on_click=self.test_microphone,
            tooltip="Test your microphone to verify it's working",
        )

        # Status and duration with dynamic coloring
        self.status_label = ft.Text(
            "Ready to record",
            size=16,
            weight=ft.FontWeight.W_600,
            text_align=ft.TextAlign.CENTER,
            color=self.colors['text_secondary'],
        )

        self.duration_label = ft.Text(
            "Duration: 00:00",
            size=36,
            weight=ft.FontWeight.BOLD,
            color=self.colors['primary'],
            text_align=ft.TextAlign.CENTER,
        )

        # Recording buttons with professional styling
        self.record_btn = ft.ElevatedButton(
            "Record",
            icon=ICONS.FIBER_MANUAL_RECORD,
            on_click=self.start_recording,
            bgcolor=self.colors['error'],
            color=COLORS.WHITE,
            expand=True,
            visible=True,
            tooltip="Start recording your voice",
            style=ft.ButtonStyle(
                shape=ft.RoundedRectangleBorder(radius=8),
                elevation={"": 2, "hovered": 4},
                padding=ft.padding.symmetric(horizontal=20, vertical=16),
                text_style=ft.TextStyle(size=16, weight=ft.FontWeight.W_600),
            ),
        )

        self.pause_btn = ft.ElevatedButton(
            "Pause",
            icon=ICONS.PAUSE,
            on_click=self.toggle_pause,
            bgcolor=self.colors['warning'],
            color=COLORS.WHITE,
            expand=True,
            visible=False,
            tooltip="Pause/resume recording",
            style=ft.ButtonStyle(
                shape=ft.RoundedRectangleBorder(radius=8),
                elevation={"": 2, "hovered": 4},
                padding=ft.padding.symmetric(horizontal=20, vertical=16),
                text_style=ft.TextStyle(size=16, weight=ft.FontWeight.W_600),
            ),
        )

        self.stop_btn = ft.ElevatedButton(
            "Stop",
            icon=ICONS.STOP,
            on_click=self.stop_recording,
            bgcolor=self.colors['text_secondary'],
            color=COLORS.WHITE,
            expand=True,
            visible=False,
            tooltip="Stop recording and save the audio",
            style=ft.ButtonStyle(
                shape=ft.RoundedRectangleBorder(radius=8),
                elevation={"": 2, "hovered": 4},
                padding=ft.padding.symmetric(horizontal=20, vertical=16),
                text_style=ft.TextStyle(size=16, weight=ft.FontWeight.W_600),
            ),
        )

        self.retake_btn = ft.ElevatedButton(
            "Retake",
            icon=ICONS.REPLAY,
            on_click=self.retake_recording,
            bgcolor=self.colors['warning'],
            color=COLORS.WHITE,
            expand=True,
            visible=False,
            tooltip="Discard current recording and start over immediately",
            style=ft.ButtonStyle(
                shape=ft.RoundedRectangleBorder(radius=8),
                elevation={"": 2, "hovered": 4},
                padding=ft.padding.symmetric(horizontal=20, vertical=16),
                text_style=ft.TextStyle(size=16, weight=ft.FontWeight.W_600),
            ),
        )

        self.delete_btn = ft.OutlinedButton(
            "Delete Recording",
            icon=ICONS.DELETE,
            on_click=self.delete_recording,
            disabled=True,
            expand=True,
            tooltip="Delete the current audio recording",
            style=ft.ButtonStyle(
                shape=ft.RoundedRectangleBorder(radius=8),
                side=ft.BorderSide(2, self.colors['error']),
                color={"": self.colors['error'], "disabled": self.colors['text_secondary']},
                padding=ft.padding.symmetric(horizontal=20, vertical=12),
            ),
        )

        return ft.Card(
            content=ft.Container(
                content=ft.Column(
                    [
                        ft.Text("Recording Controls", size=20, weight=ft.FontWeight.BOLD, color=self.colors['text_primary']),
                        ft.Container(height=4),
                        ft.Row([self.device_dropdown, self.test_mic_btn], spacing=12),
                        ft.Container(height=8),
                        ft.Container(
                            content=ft.Column([
                                self.status_label,
                                self.duration_label,
                            ], horizontal_alignment=ft.CrossAxisAlignment.CENTER, spacing=8),
                            bgcolor=self.colors['background'],
                            border_radius=8,
                            padding=16,
                        ),
                        ft.Container(height=4),
                        ft.Row([self.record_btn, self.pause_btn, self.stop_btn, self.retake_btn], spacing=12),
                        self.delete_btn,
                    ],
                    spacing=12,
                ),
                padding=20,
            ),
            elevation=3,
            surface_tint_color=self.colors['primary_light'],
        )

    def build_statistics_panel(self):
        """Build the statistics panel.

        Returns:
            The statistics panel widget.
        """
        total_samples = self.sample_manager.get_total_samples()
        total_duration = self.sample_manager.estimate_total_duration(self.audio_recorder.sample_rate)

        self.session_label = ft.Text(f"This Session: {self.session_samples} samples")
        self.total_label = ft.Text(f"Total: {total_samples} samples", weight=ft.FontWeight.BOLD)
        self.duration_stats_label = ft.Text(f"Total Duration: {total_duration:.1f} min")

        return ft.Card(
            content=ft.Container(
                content=ft.Column(
                    [
                        ft.Text("Session Statistics", size=20, weight=ft.FontWeight.BOLD, color=self.colors['text_primary']),
                        ft.Container(height=4),
                        ft.Row(
                            [self.session_label, self.total_label, self.duration_stats_label],
                            spacing=40,
                            wrap=True,
                        ),
                    ],
                    spacing=12,
                ),
                padding=20,
            ),
            elevation=3,
            surface_tint_color=self.colors['primary_light'],
        )

    def build_dataset_tab(self):
        """Build the dataset overview tab.

        Returns:
            The tab content.
        """
        # Static header
        header = ft.Text("Dataset Overview", size=24, weight=ft.FontWeight.BOLD)

        # Labels populated from SampleManager
        base = str(self.config.get_base_path() or "(not set)")
        self.dataset_base_label = ft.Text(f"Base Path: {base}")
        self.dataset_count_label = ft.Text("Notes saved: 0", weight=ft.FontWeight.BOLD)
        self.dataset_minutes_label = ft.Text("Minutes recorded: 0.0", weight=ft.FontWeight.BOLD)

        # Goal progress widgets
        self.goal_progress_bar = ft.ProgressBar(
            value=0,
            width=400,
            height=20,
            color=COLORS.GREEN_700,
            bgcolor=COLORS.GREY_300,
        )
        self.goal_progress_label = ft.Text(
            "Goal: 0.0 / 60.0 minutes (0%)",
            size=14,
            weight=ft.FontWeight.BOLD,
        )

        refresh_btn = ft.ElevatedButton(
            "Refresh Stats",
            icon=ICONS.REFRESH,
            on_click=lambda _: self.refresh_dataset_stats(),
        )

        open_folder_btn = ft.ElevatedButton(
            "Open Dataset Folder",
            icon=ICONS.FOLDER_OPEN,
            on_click=lambda _: self.open_dataset_folder(),
            bgcolor=COLORS.BLUE_700,
            color=COLORS.WHITE,
        )

        # Compose tab content
        content = ft.Column(
            [
                header,
                self.dataset_base_label,
                ft.Row([self.dataset_count_label, self.dataset_minutes_label], spacing=20),
                ft.Row([refresh_btn, open_folder_btn], spacing=10),
                ft.Divider(),
                ft.Text("Training Data Goal Progress", size=18, weight=ft.FontWeight.BOLD),
                self.goal_progress_label,
                self.goal_progress_bar,
                ft.Divider(),
                ft.Text("Saved samples will appear in your base path under 'samples/'."),
            ],
            spacing=16,
        )

        # Initialize values
        self.refresh_dataset_stats()

        return ft.Container(content=content, padding=20)

    def build_training_files_tab(self):
        """Build the training files browser tab.

        Returns:
            The tab content.
        """
        # Header
        header = ft.Text("Training Files", size=24, weight=ft.FontWeight.BOLD)

        # File list container (populated on refresh)
        self.files_list = ft.Column([], spacing=10, scroll=ft.ScrollMode.AUTO, expand=True)

        # Refresh button
        refresh_files_btn = ft.ElevatedButton(
            "Refresh Files",
            icon=ICONS.REFRESH,
            on_click=lambda _: self.refresh_training_files(),
        )

        # Stats label
        self.files_stats_label = ft.Text("Loading files...", size=14)

        # Main content
        content = ft.Column(
            [
                header,
                self.files_stats_label,
                refresh_files_btn,
                ft.Divider(),
                self.files_list,
            ],
            spacing=16,
            expand=True,
        )

        # Initial load
        self.refresh_training_files()

        return ft.Container(content=content, padding=20, expand=True)

    def build_settings_tab(self):
        """Build the settings tab.

        Returns:
            The tab content.
        """
        # Current values
        current_base = str(self.config.get_base_path() or "")
        current_api = self.config.get_api_key() or ""
        current_model = self.config.get_openai_model()
        current_rate = str(self.config.get_sample_rate())
        current_auto = self.config.get_autogenerate_next()
        current_goal = str(self.config.get_goal_duration())

        # Get current preferred device
        preferred_device = self.config.get_preferred_device()
        current_device_idx = preferred_device["device_index"] if preferred_device else None

        # Base path section
        self.settings_base_path_field = ft.TextField(
            label="Base Path for Samples",
            value=current_base,
            read_only=True,
            expand=True,
            hint_text="Click Browse to select a folder",
        )
        browse_btn = ft.ElevatedButton(
            "Browse",
            icon=ICONS.FOLDER_OPEN,
            on_click=lambda _: self.dir_picker.get_directory_path(dialog_title="Select base directory"),
        )

        # API section
        self.settings_api_key_field = ft.TextField(
            label="OpenAI API Key",
            value=current_api,
            password=True,
            can_reveal_password=True,
            expand=True,
            hint_text="Enter your OpenAI API key",
        )

        self.settings_model_dropdown = ft.Dropdown(
            label="OpenAI Model",
            value=current_model,
            options=[
                ft.dropdown.Option("gpt-4o-mini"),
                ft.dropdown.Option("gpt-4o"),
                ft.dropdown.Option("gpt-4.1-mini"),
            ],
            width=300,
        )

        self.settings_api_status = ft.Text("", size=12)

        def on_test_api(_):
            api_key = self.settings_api_key_field.value.strip()
            model = self.settings_model_dropdown.value
            if not api_key:
                self.settings_api_status.value = "Please enter an API key"
                self.settings_api_status.color = COLORS.RED_600
                self.page.update()
                return

            self.settings_api_status.value = "Testing..."
            self.settings_api_status.color = COLORS.GREY_600
            self.page.update()

            tg = TextGenerator(api_key, model)
            ok, err = tg.test_connection()
            if ok:
                self.settings_api_status.value = "✓ API connection successful"
                self.settings_api_status.color = COLORS.GREEN_600
            else:
                self.settings_api_status.value = f"✗ API test failed: {err}"
                self.settings_api_status.color = COLORS.RED_600
            self.page.update()

        # Audio settings
        devices = self.device_manager.get_input_devices()
        device_options = [ft.dropdown.Option(text="None (use system default)", key="none")]
        device_options.extend([
            ft.dropdown.Option(text=f"{d['name']} (Device {d['index']})", key=str(d['index']))
            for d in devices
        ])

        self.settings_preferred_mic_dropdown = ft.Dropdown(
            label="Preferred Microphone",
            options=device_options,
            value=str(current_device_idx) if current_device_idx is not None else "none",
            expand=True,
            hint_text="Select your preferred microphone device",
        )

        self.settings_sample_rate_field = ft.TextField(
            label="Sample Rate (Hz)",
            value=current_rate,
            width=200,
            keyboard_type=ft.KeyboardType.NUMBER,
            hint_text="e.g., 44100",
        )

        # Goals & preferences
        self.settings_goal_duration_field = ft.TextField(
            label="Training Data Goal (minutes)",
            value=current_goal,
            width=200,
            keyboard_type=ft.KeyboardType.NUMBER,
            hint_text="e.g., 60 for 1 hour",
        )

        self.settings_auto_checkbox = ft.Checkbox(
            label="Auto-generate next sample after saving",
            value=current_auto,
        )

        self.settings_save_status = ft.Text("", size=12, weight=ft.FontWeight.BOLD)

        def on_save_settings(_):
            # Persist config
            base = self.settings_base_path_field.value.strip()
            if base:
                self.config.set_base_path(Path(base))
                self.sample_manager = SampleManager(Path(base))
                self.refresh_statistics()
                self.refresh_dataset_stats()

            # API key and model
            api_key = self.settings_api_key_field.value.strip()
            if api_key:
                self.config.set_api_key(api_key)
            self.config.set_openai_model(self.settings_model_dropdown.value)

            # Sample rate
            try:
                rate = int(self.settings_sample_rate_field.value)
                if rate > 0:
                    self.config.set_sample_rate(rate)
                    self.audio_recorder.sample_rate = rate
            except Exception:
                pass

            # Preferred microphone
            if self.settings_preferred_mic_dropdown.value and self.settings_preferred_mic_dropdown.value != "none":
                try:
                    device_idx = int(self.settings_preferred_mic_dropdown.value)
                    device_name = next((d['name'] for d in devices if d['index'] == device_idx), "Unknown")
                    self.config.set_preferred_device(device_idx, device_name)
                    # Update the main dropdown to match
                    self.device_dropdown.value = str(device_idx)
                except Exception:
                    pass
            else:
                self.config.set("preferred_device_index", None)
                self.config.set("preferred_device_name", None)

            # Autogenerate setting
            self.config.set_autogenerate_next(self.settings_auto_checkbox.value)
            self.autogenerate_checkbox.value = self.settings_auto_checkbox.value

            # Goal duration
            try:
                goal = float(self.settings_goal_duration_field.value)
                if goal > 0:
                    self.config.set_goal_duration(goal)
            except Exception:
                pass

            # Update status bar and text generator
            self.status_bar.value = self.get_status_text()
            try:
                api_key = self.config.get_api_key() or ""
                model = self.config.get_openai_model()
                self.text_generator = TextGenerator(api_key, model)
            except Exception:
                pass

            # Show success message
            self.settings_save_status.value = "✓ Settings saved successfully"
            self.settings_save_status.color = COLORS.GREEN_600
            self.page.update()

        content = ft.Column(
            [
                ft.Text("Application Settings", size=24, weight=ft.FontWeight.BOLD),
                ft.Divider(),

                # Paths section
                ft.Text("Storage Paths", size=18, weight=ft.FontWeight.BOLD),
                ft.Row([self.settings_base_path_field, browse_btn]),
                ft.Text("All voice samples will be saved in this location", size=12, italic=True, color=COLORS.GREY_600),
                ft.Divider(),

                # API section
                ft.Text("OpenAI API Configuration", size=18, weight=ft.FontWeight.BOLD),
                self.settings_api_key_field,
                self.settings_model_dropdown,
                ft.Row([
                    ft.ElevatedButton("Test Connection", icon=ICONS.CHECK, on_click=on_test_api),
                    self.settings_api_status,
                ]),
                ft.Text("API key is required for text generation", size=12, italic=True, color=COLORS.GREY_600),
                ft.Divider(),

                # Audio section
                ft.Text("Audio Settings", size=18, weight=ft.FontWeight.BOLD),
                self.settings_preferred_mic_dropdown,
                ft.Text("Your preferred microphone will be automatically selected when recording",
                       size=12, italic=True, color=COLORS.GREY_600),
                self.settings_sample_rate_field,
                ft.Text("Higher sample rates provide better quality but larger file sizes",
                       size=12, italic=True, color=COLORS.GREY_600),
                ft.Divider(),

                # Goals section
                ft.Text("Training Goals & Preferences", size=18, weight=ft.FontWeight.BOLD),
                self.settings_goal_duration_field,
                ft.Text("Set your target dataset duration (e.g., 60 minutes = 1 hour of training data)",
                       size=12, italic=True, color=COLORS.GREY_600),
                self.settings_auto_checkbox,
                ft.Divider(),

                # Save button
                ft.Row([
                    ft.ElevatedButton(
                        "Save Settings",
                        icon=ICONS.SAVE,
                        on_click=on_save_settings,
                        bgcolor=COLORS.BLUE_700,
                        color=COLORS.WHITE,
                    ),
                    self.settings_save_status,
                ]),
            ],
            spacing=12,
            scroll=ft.ScrollMode.AUTO,
        )

        return ft.Container(content=content, padding=20)

    # Event handlers
    def on_autogenerate_toggled(self, e):
        """Handle autogenerate checkbox toggle."""
        self.config.set_autogenerate_next(e.control.value)

    def toggle_dictionary(self, e):
        """Toggle dictionary input."""
        self.dict_input.disabled = not e.control.value
        self.page.update()

    def on_text_changed(self, e):
        """Update character and word counts."""
        text = self.text_edit.value or ""
        char_count = len(text)
        word_count = len(text.split()) if text.strip() else 0
        self.char_count_label.value = f"Characters: {char_count} | Words: {word_count}"
        self.check_save_enabled()
        has_text = bool(text.strip())
        self.new_sample_btn.disabled = not has_text
        self.page.update()

    def generate_text(self, e):
        """Generate text using LLM."""
        # Disable controls
        self.generate_btn.disabled = True
        self.generate_btn.text = "⏳ Generating..."
        self.page.update()

        try:
            duration = float(self.duration_field.value)
            wpm = int(self.wpm_field.value)
            style = self.style_dropdown.value

            dictionary = None
            if self.use_dict_checkbox.value and self.dict_input.value:
                dictionary = [w.strip() for w in self.dict_input.value.split(',') if w.strip()]

            text, error = self.text_generator.generate_text(
                duration_minutes=duration,
                wpm=wpm,
                style=style,
                dictionary=dictionary
            )

            if error:
                self.show_error_dialog("Generation Error", f"Failed to generate text:\n{error}")
            elif text:
                self.text_edit.value = text
                self.new_sample_btn.disabled = False
                self.regenerate_btn.disabled = False
            else:
                self.show_error_dialog("No Text", "No text was generated. Please try again.")

        except Exception as ex:
            self.show_error_dialog("Error", str(ex))
        finally:
            self.generate_btn.disabled = False
            self.generate_btn.text = "Generate Text"
            self.page.update()

    def new_sample(self, e):
        """Start a completely new sample, clearing current state."""
        # Clear text
        self.text_edit.value = ""

        # Clear audio if present
        if self.current_audio is not None:
            self.current_audio = None
            self.audio_recorder.clear_audio()

        # Reset UI state
        self.duration_label.value = "Duration: 00:00"
        self.status_label.value = "Ready to record"
        self.delete_btn.disabled = True
        self.new_sample_btn.disabled = True
        self.regenerate_btn.disabled = True
        self.save_btn.disabled = True

        self.page.update()

        # Auto-generate if enabled
        if self.config.get_autogenerate_next():
            self.generate_text(None)

    def check_save_enabled(self):
        """Check if save button should be enabled."""
        has_audio = self.current_audio is not None
        has_text = bool(self.text_edit.value and self.text_edit.value.strip())
        self.save_btn.disabled = not (has_audio and has_text)

    def save_sample(self, e):
        """Save the current sample."""
        if not self.config.is_configured():
            self.show_error_dialog("Not Configured", "Please set a base path in Settings first.")
            return

        if self.current_audio is None:
            self.show_error_dialog("No Recording", "Please record audio before saving.")
            return

        if not self.text_edit.value or not self.text_edit.value.strip():
            self.show_error_dialog("No Text", "Please generate or enter text before saving.")
            return

        # Prepare temp audio file
        try:
            base = self.config.get_base_path()
            tmp_dir = base / "_tmp"
            tmp_dir.mkdir(parents=True, exist_ok=True)
            tmp_wav = tmp_dir / "current.wav"

            # Save current audio to temp path
            saved = self.audio_recorder.save_audio(self.current_audio, tmp_wav)
            if not saved:
                self.show_error_dialog("Save Failed", "Could not save audio to disk.")
                return

            # Build metadata
            generation_params = {
                "duration_minutes": float(self.duration_field.value or 0),
                "wpm": int(self.wpm_field.value or 0),
                "style": self.style_dropdown.value,
                "used_dictionary": bool(self.use_dict_checkbox.value),
                "dictionary": [w.strip() for w in (self.dict_input.value or '').split(',') if w.strip()] if self.use_dict_checkbox.value else [],
                "model": self.config.get_openai_model(),
                "sample_rate": self.audio_recorder.sample_rate,
            }
            metadata = self.sample_manager.create_metadata(generation_params)

            # Persist via SampleManager (moves file into place and writes text/metadata)
            ok, err = self.sample_manager.save_sample(tmp_wav, self.text_edit.value.strip(), metadata)
            if not ok:
                self.show_error_dialog("Save Failed", f"Error saving sample: {err}")
                return

            # Update UI state
            self.session_samples += 1
            self.refresh_statistics()
            self.page.update()

            # Start a new sample automatically
            self.new_sample(None)

        except Exception as ex:
            self.show_error_dialog("Error", str(ex))

    def start_recording(self, e):
        """Start recording."""
        # Ensure base path set so saving later works
        if not self.config.is_configured():
            self.show_error_dialog("Not Configured", "Please set a base path in Settings first.")
            return

        # Resolve device index
        device_idx = None
        if self.device_dropdown.value is not None:
            try:
                device_idx = int(self.device_dropdown.value)
            except Exception:
                device_idx = None

        # Start audio recording
        try:
            self.audio_recorder.start_recording(device_index=device_idx)
        except Exception as ex:
            self.show_error_dialog("Recording Error", str(ex))
            return

        # Update main panel buttons visibility and status with visual feedback
        self.record_btn.visible = False
        self.pause_btn.visible = True
        self.stop_btn.visible = True
        self.retake_btn.visible = True
        self.delete_btn.disabled = True
        self.status_label.value = "● Recording..."
        self.status_label.color = self.colors['error']
        self.duration_label.value = "Duration: 00:00"
        self.duration_label.color = self.colors['error']

        # Update app bar controls
        self.appbar_record_btn.visible = False
        self.appbar_pause_btn.visible = True
        self.appbar_stop_btn.visible = True
        self.appbar_retake_btn.visible = True
        self.appbar_status_label.value = "Recording"
        self.appbar_duration_label.value = "00:00"

        self.page.update()

        # Start timer thread to update duration label live
        self._record_timer_stop.clear()

        def _timer_loop():
            while not self._record_timer_stop.is_set():
                seconds = self.audio_recorder.get_duration()
                mins = int(seconds // 60)
                secs = int(seconds % 60)
                duration_text = f"{mins:02d}:{secs:02d}"
                self.duration_label.value = f"Duration: {duration_text}"
                self.appbar_duration_label.value = duration_text
                try:
                    self.page.update()
                except Exception:
                    pass
                time.sleep(0.3)

        self._record_timer_thread = threading.Thread(target=_timer_loop, daemon=True)
        self._record_timer_thread.start()

    def open_narration_view(self):
        """Open a large, high-contrast text viewer for narration."""
        if not (self.text_edit.value and self.text_edit.value.strip()):
            self.show_error_dialog("No Text", "Generate or enter text first.")
            return

        # Default font size for narration
        if not hasattr(self, "narration_font_size"):
            self.narration_font_size = 22

        # Text field for readable narration
        self.narration_text = ft.TextField(
            value=self.text_edit.value,
            multiline=True,
            read_only=True,
            text_style=ft.TextStyle(size=self.narration_font_size),
            border=ft.InputBorder.NONE,
            expand=True,
        )

        def inc_font(_):
            self.narration_font_size = min(self.narration_font_size + 2, 64)
            self.narration_text.text_style = ft.TextStyle(size=self.narration_font_size)
            self.page.update()

        def dec_font(_):
            self.narration_font_size = max(self.narration_font_size - 2, 12)
            self.narration_text.text_style = ft.TextStyle(size=self.narration_font_size)
            self.page.update()

        def copy_text(_):
            try:
                self.page.set_clipboard(self.text_edit.value)
            except Exception:
                pass

        content = ft.Container(
            width=1000,
            height=600,
            bgcolor=COLORS.SURFACE,
            padding=20,
            content=ft.Column([
                ft.Row([
                    ft.Text("Narration View", size=20, weight=ft.FontWeight.BOLD),
                    ft.Container(expand=True),
                    ft.IconButton(ICONS.REMOVE, tooltip="Smaller", on_click=dec_font),
                    ft.IconButton(ICONS.ADD, tooltip="Larger", on_click=inc_font),
                    ft.IconButton(ICONS.CONTENT_COPY, tooltip="Copy", on_click=copy_text),
                ], alignment=ft.MainAxisAlignment.SPACE_BETWEEN),
                ft.Divider(),
                self.narration_text,
            ], spacing=10),
        )

        dialog = ft.AlertDialog(
            modal=True,
            content=content,
            actions=[
                ft.TextButton("Close", on_click=lambda _: self.close_dialog(dialog)),
            ],
            actions_alignment=ft.MainAxisAlignment.END,
        )
        self.page.dialog = dialog
        dialog.open = True
        self.page.update()

    def on_tab_change(self, e):
        """Handle tab changes to show/hide app bar recording controls."""
        # Show app bar controls only on Record & Generate tab (index 0)
        self.appbar_recording_controls.visible = (e.control.selected_index == 0)
        self.page.update()

    def _go_to_settings(self):
        """Navigate to settings tab."""
        self.tabs.selected_index = 3
        self.page.update()

    def toggle_theme(self):
        """Toggle between light and dark theme."""
        try:
            self.page.theme_mode = (
                ft.ThemeMode.DARK if self.page.theme_mode == ft.ThemeMode.LIGHT else ft.ThemeMode.LIGHT
            )
            self.page.update()
        except Exception:
            pass

    def toggle_pause(self, e):
        """Toggle pause/resume recording."""
        if not self.audio_recorder.is_recording:
            return
        if not self.audio_recorder.is_paused:
            self.audio_recorder.pause_recording()
            # Update main panel
            self.pause_btn.text = "Resume"
            self.pause_btn.icon = ICONS.PLAY_ARROW
            self.status_label.value = "⏸ Paused"
            self.status_label.color = self.colors['warning']
            self.duration_label.color = self.colors['warning']
            # Update app bar
            self.appbar_pause_btn.icon = ICONS.PLAY_ARROW
            self.appbar_pause_btn.tooltip = "Resume recording"
            self.appbar_status_label.value = "Paused"
        else:
            self.audio_recorder.resume_recording()
            # Update main panel
            self.pause_btn.text = "Pause"
            self.pause_btn.icon = ICONS.PAUSE
            self.status_label.value = "● Recording..."
            self.status_label.color = self.colors['error']
            self.duration_label.color = self.colors['error']
            # Update app bar
            self.appbar_pause_btn.icon = ICONS.PAUSE
            self.appbar_pause_btn.tooltip = "Pause recording"
            self.appbar_status_label.value = "Recording"
        self.page.update()

    def stop_recording(self, e):
        """Stop recording."""
        if not self.audio_recorder.is_recording:
            return

        # Stop timer thread
        self._record_timer_stop.set()
        if self._record_timer_thread and self._record_timer_thread.is_alive():
            try:
                self._record_timer_thread.join(timeout=1.0)
            except Exception:
                pass

        audio = self.audio_recorder.stop_recording()
        if audio is None or len(audio) == 0:
            # Update main panel
            self.status_label.value = "No audio captured"
            self.record_btn.visible = True
            self.pause_btn.visible = False
            self.stop_btn.visible = False
            self.retake_btn.visible = False
            self.delete_btn.disabled = True
            # Update app bar
            self.appbar_record_btn.visible = True
            self.appbar_pause_btn.visible = False
            self.appbar_stop_btn.visible = False
            self.appbar_retake_btn.visible = False
            self.appbar_status_label.value = "Ready"
            self.page.update()
            return

        self.current_audio = audio
        seconds = self.audio_recorder.get_duration(audio)
        mins = int(seconds // 60)
        secs = int(seconds % 60)
        duration_text = f"{mins:02d}:{secs:02d}"

        # Update main panel
        self.duration_label.value = f"Duration: {duration_text}"
        self.duration_label.color = self.colors['success']
        self.status_label.value = "✓ Recording complete"
        self.status_label.color = self.colors['success']
        self.record_btn.visible = True
        self.pause_btn.visible = False
        self.pause_btn.text = "Pause"
        self.pause_btn.icon = ICONS.PAUSE
        self.stop_btn.visible = False
        self.retake_btn.visible = False
        self.delete_btn.disabled = False

        # Update app bar
        self.appbar_duration_label.value = duration_text
        self.appbar_status_label.value = "Complete"
        self.appbar_record_btn.visible = True
        self.appbar_pause_btn.visible = False
        self.appbar_stop_btn.visible = False
        self.appbar_retake_btn.visible = False

        # Enable save if text exists
        self.check_save_enabled()
        self.page.update()

    def delete_recording(self, e):
        """Delete current recording."""
        self.current_audio = None
        self.audio_recorder.clear_audio()
        self.duration_label.value = "Duration: 00:00"
        self.duration_label.color = self.colors['primary']
        self.status_label.value = "Recording deleted"
        self.status_label.color = self.colors['text_secondary']
        self.delete_btn.disabled = True
        self.check_save_enabled()
        self.page.update()

    def retake_recording(self, e):
        """Discard current recording and immediately start a new one."""
        # Stop the timer thread if recording
        if self.audio_recorder.is_recording:
            self._record_timer_stop.set()
            if self._record_timer_thread and self._record_timer_thread.is_alive():
                try:
                    self._record_timer_thread.join(timeout=1.0)
                except Exception:
                    pass

            # Stop current recording (discarding it)
            self.audio_recorder.stop_recording()

        # Clear any existing audio
        self.current_audio = None
        self.audio_recorder.clear_audio()

        # Reset UI briefly
        self.status_label.value = "Retaking..."
        self.page.update()

        # Start a new recording immediately
        self.start_recording(None)

    def test_microphone(self, e):
        """Test the microphone."""
        self.show_info_dialog("Test Mic", "Microphone test functionality to be implemented")

    def open_settings(self):
        """Open settings dialog."""
        # Fields populated from current config
        current_base = str(self.config.get_base_path() or "")
        current_api = self.config.get_api_key() or ""
        current_model = self.config.get_openai_model()
        current_rate = str(self.config.get_sample_rate())
        current_auto = self.config.get_autogenerate_next()
        current_goal = str(self.config.get_goal_duration())

        # Inputs
        self.base_path_field = ft.TextField(
            label="Base Path",
            value=current_base,
            read_only=True,
            expand=True,
        )
        browse_btn = ft.ElevatedButton(
            "Browse",
            icon=ICONS.FOLDER_OPEN,
            on_click=lambda _: self.dir_picker.get_directory_path(dialog_title="Select base directory"),
        )

        self.api_key_field = ft.TextField(
            label="OpenAI API Key",
            value=current_api,
            password=True,
            can_reveal_password=True,
            expand=True,
        )

        self.model_dropdown = ft.Dropdown(
            label="Model",
            value=current_model,
            options=[
                ft.dropdown.Option("gpt-4o-mini"),
                ft.dropdown.Option("gpt-4o"),
                ft.dropdown.Option("gpt-4.1-mini"),
            ],
            width=300,
        )

        self.sample_rate_field = ft.TextField(
            label="Sample Rate",
            value=current_rate,
            width=200,
            keyboard_type=ft.KeyboardType.NUMBER,
        )

        self.auto_checkbox = ft.Checkbox(
            label="Auto-generate next sample after saving",
            value=current_auto,
        )

        self.goal_duration_field = ft.TextField(
            label="Training Data Goal (minutes)",
            value=current_goal,
            width=200,
            keyboard_type=ft.KeyboardType.NUMBER,
            hint_text="e.g., 60 for 1 hour",
        )

        self.settings_status = ft.Text("")

        # Actions
        def on_test(_):
            api_key = self.api_key_field.value.strip()
            model = self.model_dropdown.value
            tg = TextGenerator(api_key, model)
            ok, err = tg.test_connection()
            if ok:
                self.settings_status.value = "API connection successful"
                self.settings_status.color = COLORS.GREEN_600
            else:
                self.settings_status.value = f"API test failed: {err}"
                self.settings_status.color = COLORS.RED_600
            self.page.update()

        def on_save(_):
            # Persist config
            base = self.base_path_field.value.strip()
            if base:
                self.config.set_base_path(Path(base))
                # Re-init sample manager and stats
                self.sample_manager = SampleManager(Path(base))
                self.refresh_statistics()
            # API key and model
            self.config.set_api_key(self.api_key_field.value.strip())
            self.config.set_openai_model(self.model_dropdown.value)
            # Sample rate
            try:
                rate = int(self.sample_rate_field.value)
                if rate > 0:
                    self.config.set_sample_rate(rate)
                    self.audio_recorder.sample_rate = rate
            except Exception:
                pass
            # Autogenerate setting
            self.config.set_autogenerate_next(self.auto_checkbox.value)
            self.autogenerate_checkbox.value = self.auto_checkbox.value
            # Goal duration
            try:
                goal = float(self.goal_duration_field.value)
                if goal > 0:
                    self.config.set_goal_duration(goal)
            except Exception:
                pass

            # Update status bar and text generator
            self.status_bar.value = self.get_status_text()
            try:
                api_key = self.config.get_api_key() or ""
                model = self.config.get_openai_model()
                self.text_generator = TextGenerator(api_key, model)
            except Exception:
                pass

            self.close_dialog(settings_dialog)
            # Also refresh dataset tab stats
            self.refresh_dataset_stats()

        settings_dialog = ft.AlertDialog(
            title=ft.Text("Settings"),
            content=ft.Column(
                [
                    ft.Text("Paths", weight=ft.FontWeight.BOLD),
                    ft.Row([self.base_path_field, browse_btn]),
                    ft.Divider(),
                    ft.Text("API", weight=ft.FontWeight.BOLD),
                    self.api_key_field,
                    self.model_dropdown,
                    ft.Row([
                        ft.ElevatedButton("Test Connection", icon=ICONS.CHECK, on_click=on_test),
                        self.settings_status,
                    ], alignment=ft.MainAxisAlignment.START),
                    ft.Divider(),
                    ft.Text("Audio", weight=ft.FontWeight.BOLD),
                    self.sample_rate_field,
                    ft.Divider(),
                    ft.Text("Goals & Preferences", weight=ft.FontWeight.BOLD),
                    self.goal_duration_field,
                    self.auto_checkbox,
                ],
                tight=False,
                scroll=ft.ScrollMode.AUTO,
            ),
            actions=[
                ft.TextButton("Cancel", on_click=lambda _: self.close_dialog(settings_dialog)),
                ft.ElevatedButton("Save", icon=ICONS.SAVE, on_click=on_save),
            ],
            actions_alignment=ft.MainAxisAlignment.END,
            on_dismiss=lambda _: None,
        )

        self.page.dialog = settings_dialog
        settings_dialog.open = True
        self.page.update()

    def get_status_text(self):
        """Get status bar text."""
        if self.config.is_configured():
            return f"Base Path: {self.config.get_base_path()}"
        return "Not configured - please set up in Settings"

    # Dialog helpers
    def show_welcome_dialog(self):
        """Show welcome dialog."""
        dialog = ft.AlertDialog(
            title=ft.Text("Welcome"),
            content=ft.Text(
                "Welcome to Voice Training Data Creator!\n\n"
                "Please configure your base path and API settings to get started."
            ),
            actions=[
                ft.TextButton("Open Settings", on_click=lambda _: (self.close_dialog(dialog), self.open_settings())),
                ft.TextButton("Close", on_click=lambda _: self.close_dialog(dialog)),
            ],
        )
        self.page.dialog = dialog
        dialog.open = True
        self.page.update()

    def on_pick_directory(self, e: ft.FilePickerResultEvent):
        """Handle directory selection from picker."""
        if e.path:
            # Update settings tab field if it exists
            if hasattr(self, 'settings_base_path_field'):
                self.settings_base_path_field.value = e.path
            # Update old dialog field if it exists
            if hasattr(self, 'base_path_field'):
                self.base_path_field.value = e.path
            self.page.update()

    def refresh_statistics(self):
        """Refresh statistics labels from sample manager."""
        total_samples = self.sample_manager.get_total_samples()
        total_duration = self.sample_manager.estimate_total_duration(self.audio_recorder.sample_rate)
        self.total_label.value = f"Total: {total_samples} samples"
        self.duration_stats_label.value = f"Total Duration: {total_duration:.1f} min"
        self.page.update()

    def refresh_dataset_stats(self):
        """Refresh Dataset tab stats."""
        base = str(self.config.get_base_path() or "(not set)")
        self.dataset_base_label.value = f"Base Path: {base}"
        total_samples = self.sample_manager.get_total_samples()
        total_minutes = self.sample_manager.estimate_total_duration(self.audio_recorder.sample_rate)
        self.dataset_count_label.value = f"Notes saved: {total_samples}"
        self.dataset_minutes_label.value = f"Minutes recorded: {total_minutes:.1f}"

        # Update goal progress
        goal_minutes = self.config.get_goal_duration()
        progress_pct = min((total_minutes / goal_minutes * 100) if goal_minutes > 0 else 0, 100)
        progress_value = min(total_minutes / goal_minutes if goal_minutes > 0 else 0, 1.0)

        self.goal_progress_bar.value = progress_value
        self.goal_progress_label.value = f"Goal: {total_minutes:.1f} / {goal_minutes:.1f} minutes ({progress_pct:.1f}%)"

        # Change color based on progress
        if progress_pct >= 100:
            self.goal_progress_bar.color = COLORS.GREEN_700
            self.goal_progress_label.color = COLORS.GREEN_700
        elif progress_pct >= 50:
            self.goal_progress_bar.color = COLORS.BLUE_700
            self.goal_progress_label.color = COLORS.BLUE_700
        else:
            self.goal_progress_bar.color = COLORS.ORANGE_700
            self.goal_progress_label.color = COLORS.ORANGE_700

        self.page.update()

    def open_dataset_folder(self):
        """Open the dataset base path in the file manager."""
        base_path = self.config.get_base_path()

        if not base_path:
            self.show_error_dialog("No Base Path", "Please set a base path in Settings first.")
            return

        if not base_path.exists():
            self.show_error_dialog("Path Not Found", f"The base path does not exist:\n{base_path}")
            return

        try:
            system = platform.system()
            if system == "Linux":
                subprocess.Popen(["xdg-open", str(base_path)])
            elif system == "Darwin":  # macOS
                subprocess.Popen(["open", str(base_path)])
            elif system == "Windows":
                subprocess.Popen(["explorer", str(base_path)])
            else:
                self.show_error_dialog("Unsupported OS", f"Cannot open folder on {system}")
        except Exception as ex:
            self.show_error_dialog("Error Opening Folder", str(ex))

    def refresh_training_files(self):
        """Refresh the training files list."""
        try:
            samples = self.sample_manager.get_all_samples()

            # Update stats
            total_duration = sum(s.get('duration', 0) for s in samples)
            self.files_stats_label.value = f"Total samples: {len(samples)} | Total duration: {total_duration:.1f}s ({total_duration/60:.1f} min)"

            # Clear existing list
            self.files_list.controls.clear()

            if not samples:
                self.files_list.controls.append(
                    ft.Text("No training files found. Start recording to create samples!",
                           size=14, italic=True, color=COLORS.GREY_600)
                )
            else:
                # Add each sample as a card
                for sample in samples:
                    self.files_list.controls.append(self.create_sample_card(sample))

            self.page.update()

        except Exception as e:
            self.show_error_dialog("Error Loading Files", str(e))

    def create_sample_card(self, sample: dict):
        """Create a card widget for a sample.

        Args:
            sample: Sample info dictionary.

        Returns:
            Card widget.
        """
        sample_num = sample['number']
        duration = sample.get('duration', 0)
        text_content = sample.get('text_content', '(no text)')

        # Truncate text for display
        display_text = text_content[:120] + "..." if len(text_content) > 120 else text_content

        # Play button
        play_btn = ft.IconButton(
            icon=ICONS.PLAY_CIRCLE,
            tooltip="Play audio sample",
            on_click=lambda _: self.play_sample_audio(sample),
            icon_color=self.colors['primary'],
            icon_size=32,
        )

        # Delete button
        delete_btn = ft.IconButton(
            icon=ICONS.DELETE_OUTLINE,
            tooltip="Delete this sample",
            on_click=lambda _: self.confirm_delete_sample(sample_num),
            icon_color=self.colors['error'],
            icon_size=28,
        )

        # Sample badge
        badge = ft.Container(
            content=ft.Text(
                f"#{sample_num:03d}",
                size=12,
                weight=ft.FontWeight.BOLD,
                color=COLORS.WHITE,
            ),
            bgcolor=self.colors['primary'],
            border_radius=12,
            padding=ft.padding.symmetric(horizontal=10, vertical=4),
        )

        # Sample info
        info_column = ft.Column(
            [
                ft.Row([
                    badge,
                    ft.Text(
                        f"{duration:.1f}s",
                        size=13,
                        color=self.colors['text_secondary'],
                        weight=ft.FontWeight.W_500,
                    ),
                ], spacing=12),
                ft.Container(height=4),
                ft.Text(
                    display_text,
                    size=13,
                    color=self.colors['text_primary'],
                    max_lines=2,
                    overflow=ft.TextOverflow.ELLIPSIS,
                ),
            ],
            spacing=6,
            expand=True,
        )

        # Card content
        card_content = ft.Row(
            [
                info_column,
                ft.Row([play_btn, delete_btn], spacing=4),
            ],
            alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
            vertical_alignment=ft.CrossAxisAlignment.CENTER,
        )

        return ft.Card(
            content=ft.Container(
                content=card_content,
                padding=16,
            ),
            elevation=2,
            surface_tint_color=self.colors['primary_light'],
        )

    def play_sample_audio(self, sample: dict):
        """Play audio for a sample using in-app audio player.

        Args:
            sample: Sample info dictionary.
        """
        audio_path = sample.get('audio_path')
        if not audio_path or not Path(audio_path).exists():
            self.show_error_dialog("No Audio", "Audio file not found for this sample.")
            return

        try:
            self.current_playing_sample = sample
            self.show_audio_player_dialog(audio_path, sample)
        except Exception as e:
            # If in-app player fails, offer system player as fallback
            self.show_audio_error_with_fallback(audio_path, str(e))

    def show_audio_player_dialog(self, audio_path: str, sample: dict):
        """Show audio player dialog with playback controls.

        Args:
            audio_path: Path to the audio file.
            sample: Sample info dictionary.
        """
        sample_num = sample['number']
        duration = sample.get('duration', 0)
        text_content = sample.get('text_content', '(no text)')

        # Convert file path to proper URI format for Flet
        audio_file_path = Path(audio_path).resolve()
        audio_uri = f"file://{audio_file_path}"

        # Create audio player
        self.audio_player = ft.Audio(
            src=audio_uri,
            autoplay=True,
            volume=1.0,
            on_duration_changed=lambda e: self.update_audio_duration(e),
            on_position_changed=lambda e: self.update_audio_position(e),
            on_state_changed=lambda e: self.update_audio_state(e),
        )
        self.page.overlay.append(self.audio_player)

        # Playback state
        self.audio_is_playing = True
        self.audio_duration = duration
        self.audio_position = 0.0

        # Play/Pause button
        self.play_pause_btn = ft.IconButton(
            icon=ICONS.PAUSE_CIRCLE,
            icon_size=48,
            icon_color=self.colors['primary'],
            tooltip="Pause",
            on_click=lambda _: self.toggle_audio_playback(),
        )

        # Progress bar
        self.audio_progress = ft.ProgressBar(
            value=0,
            width=400,
            height=8,
            color=self.colors['primary'],
            bgcolor=self.colors['border'],
        )

        # Time labels
        self.audio_time_label = ft.Text(
            "0:00 / 0:00",
            size=13,
            color=self.colors['text_secondary'],
        )

        # Volume slider
        self.volume_slider = ft.Slider(
            min=0,
            max=100,
            value=100,
            width=150,
            on_change=lambda e: self.change_volume(e),
            active_color=self.colors['primary'],
        )

        # Sample info
        info_text = ft.Column([
            ft.Text(f"Sample #{sample_num:03d}", size=18, weight=ft.FontWeight.BOLD, color=self.colors['text_primary']),
            ft.Text(f"Duration: {duration:.1f}s", size=13, color=self.colors['text_secondary']),
            ft.Divider(height=1, color=self.colors['border']),
            ft.Text("Text:", size=12, weight=ft.FontWeight.W_600, color=self.colors['text_primary']),
            ft.Text(text_content, size=12, color=self.colors['text_secondary'], max_lines=4, overflow=ft.TextOverflow.ELLIPSIS),
        ], spacing=8)

        # Player controls
        controls = ft.Column([
            ft.Row([
                ft.Icon(ICONS.VOLUME_UP, color=self.colors['text_secondary'], size=20),
                self.volume_slider,
            ], alignment=ft.MainAxisAlignment.CENTER, spacing=8),
            ft.Container(height=8),
            ft.Row([self.play_pause_btn], alignment=ft.MainAxisAlignment.CENTER),
            ft.Container(height=8),
            self.audio_progress,
            self.audio_time_label,
        ], horizontal_alignment=ft.CrossAxisAlignment.CENTER, spacing=4)

        # Dialog content
        content = ft.Container(
            content=ft.Column([
                info_text,
                ft.Divider(height=1, color=self.colors['border']),
                controls,
            ], spacing=16),
            width=500,
            padding=20,
        )

        # Create dialog
        dialog = ft.AlertDialog(
            modal=False,
            title=ft.Text("Audio Player", size=20, weight=ft.FontWeight.BOLD),
            content=content,
            actions=[
                ft.TextButton("Close", on_click=lambda _: self.close_audio_player(dialog)),
            ],
            actions_alignment=ft.MainAxisAlignment.END,
        )

        self.page.dialog = dialog
        dialog.open = True
        self.page.update()

    def toggle_audio_playback(self):
        """Toggle audio playback between play and pause."""
        if self.audio_player:
            if self.audio_is_playing:
                self.audio_player.pause()
                self.play_pause_btn.icon = ICONS.PLAY_CIRCLE
                self.play_pause_btn.tooltip = "Play"
                self.audio_is_playing = False
            else:
                self.audio_player.resume()
                self.play_pause_btn.icon = ICONS.PAUSE_CIRCLE
                self.play_pause_btn.tooltip = "Pause"
                self.audio_is_playing = True
            self.page.update()

    def change_volume(self, e):
        """Change audio volume."""
        if self.audio_player:
            self.audio_player.volume = e.control.value / 100
            self.audio_player.update()

    def update_audio_duration(self, e):
        """Update audio duration when available."""
        if e.data and e.data != "0":
            try:
                self.audio_duration = float(e.data) / 1000  # Convert ms to seconds
            except Exception:
                pass

    def update_audio_position(self, e):
        """Update audio position during playback."""
        if e.data:
            try:
                position_ms = float(e.data)
                self.audio_position = position_ms / 1000  # Convert ms to seconds

                # Update progress bar
                if self.audio_duration > 0:
                    progress = self.audio_position / self.audio_duration
                    self.audio_progress.value = min(progress, 1.0)

                # Update time label
                pos_mins = int(self.audio_position // 60)
                pos_secs = int(self.audio_position % 60)
                dur_mins = int(self.audio_duration // 60)
                dur_secs = int(self.audio_duration % 60)
                self.audio_time_label.value = f"{pos_mins}:{pos_secs:02d} / {dur_mins}:{dur_secs:02d}"

                self.page.update()
            except Exception:
                pass

    def update_audio_state(self, e):
        """Update UI based on audio state."""
        if e.data == "completed":
            self.audio_is_playing = False
            self.play_pause_btn.icon = ICONS.REPLAY
            self.play_pause_btn.tooltip = "Replay"
            self.page.update()

    def close_audio_player(self, dialog):
        """Close audio player and clean up."""
        if self.audio_player:
            try:
                self.audio_player.pause()
                self.page.overlay.remove(self.audio_player)
            except Exception:
                pass
            self.audio_player = None

        self.current_playing_sample = None
        dialog.open = False
        self.page.update()

    def show_audio_error_with_fallback(self, audio_path: str, error: str):
        """Show error dialog with option to play in system player.

        Args:
            audio_path: Path to the audio file.
            error: Error message from in-app player.
        """
        def play_in_system(_):
            try:
                system = platform.system()
                if system == "Linux":
                    subprocess.Popen(["xdg-open", audio_path])
                elif system == "Darwin":  # macOS
                    subprocess.Popen(["open", audio_path])
                elif system == "Windows":
                    subprocess.Popen(["start", audio_path], shell=True)
                self.close_dialog(dialog)
            except Exception as ex:
                self.close_dialog(dialog)
                self.show_error_dialog("Error", f"Failed to open audio file: {ex}")

        dialog = ft.AlertDialog(
            title=ft.Text("Audio Player Error"),
            content=ft.Text(
                f"Failed to play audio in-app: {error}\n\n"
                "Would you like to open the audio file in your system's default player?"
            ),
            actions=[
                ft.TextButton("Cancel", on_click=lambda _: self.close_dialog(dialog)),
                ft.ElevatedButton(
                    "Open in System Player",
                    icon=ICONS.OPEN_IN_NEW,
                    on_click=play_in_system,
                    bgcolor=self.colors['primary'],
                    color=COLORS.WHITE,
                ),
            ],
        )
        self.page.dialog = dialog
        dialog.open = True
        self.page.update()

    def confirm_delete_sample(self, sample_num: int):
        """Show confirmation dialog for deleting a sample.

        Args:
            sample_num: Sample number to delete.
        """
        dialog = ft.AlertDialog(
            title=ft.Text("Confirm Delete"),
            content=ft.Text(
                f"Are you sure you want to delete sample #{sample_num:03d}?\n\n"
                "This will permanently delete the sample and renumber all subsequent samples."
            ),
            actions=[
                ft.TextButton("Cancel", on_click=lambda _: self.close_dialog(dialog)),
                ft.TextButton(
                    "Delete",
                    on_click=lambda _: self.delete_sample(sample_num, dialog),
                    style=ft.ButtonStyle(color=COLORS.RED_700),
                ),
            ],
        )
        self.page.dialog = dialog
        dialog.open = True
        self.page.update()

    def delete_sample(self, sample_num: int, dialog):
        """Delete a sample and refresh the list.

        Args:
            sample_num: Sample number to delete.
            dialog: Dialog to close after deletion.
        """
        try:
            success, error = self.sample_manager.delete_sample(sample_num)

            if success:
                self.close_dialog(dialog)
                self.refresh_training_files()
                self.refresh_dataset_stats()
                self.show_info_dialog(
                    "Sample Deleted",
                    f"Sample #{sample_num:03d} has been deleted and subsequent samples have been renumbered."
                )
            else:
                self.close_dialog(dialog)
                self.show_error_dialog("Delete Failed", error or "Unknown error")

        except Exception as e:
            self.close_dialog(dialog)
            self.show_error_dialog("Delete Failed", str(e))

    def show_info_dialog(self, title, message):
        """Show info dialog."""
        dialog = ft.AlertDialog(
            title=ft.Text(title),
            content=ft.Text(message),
            actions=[
                ft.TextButton("OK", on_click=lambda _: self.close_dialog(dialog)),
            ],
        )
        self.page.dialog = dialog
        dialog.open = True
        self.page.update()

    def show_error_dialog(self, title, message):
        """Show error dialog."""
        dialog = ft.AlertDialog(
            title=ft.Text(title),
            content=ft.Text(message),
            actions=[
                ft.TextButton("OK", on_click=lambda _: self.close_dialog(dialog)),
            ],
        )
        self.page.dialog = dialog
        dialog.open = True
        self.page.update()

    def show_about(self):
        """Show about dialog."""
        dialog = ft.AlertDialog(
            title=ft.Text("About Voice Training Data Creator"),
            content=ft.Column(
                [
                    ft.Text("Version 1.0", weight=ft.FontWeight.BOLD),
                    ft.Text("A GUI tool for creating voice training datasets."),
                    ft.Divider(),
                    ft.Text("Features:", weight=ft.FontWeight.BOLD),
                    ft.Text("• High-quality audio recording"),
                    ft.Text("• AI-powered text generation"),
                    ft.Text("• Multiple style options"),
                    ft.Text("• Custom vocabulary support"),
                ],
                tight=True,
            ),
            actions=[
                ft.TextButton("OK", on_click=lambda _: self.close_dialog(dialog)),
            ],
        )
        self.page.dialog = dialog
        dialog.open = True
        self.page.update()

    def close_dialog(self, dialog):
        """Close a dialog."""
        dialog.open = False
        self.page.update()


def main(page: ft.Page):
    """Main entry point for Flet app."""
    VoiceTrainingApp(page)


if __name__ == "__main__":
    ft.app(target=main)
