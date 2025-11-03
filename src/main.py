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
        self.page.window_width = 1200
        self.page.window_height = 850
        self.page.padding = 20
        self.page.theme_mode = ft.ThemeMode.LIGHT
        # Simple theme for a fresher look
        try:
            self.page.theme = ft.Theme()
        except Exception:
            pass

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

        # Build UI
        self.build_ui()

        # Check initial configuration
        if not self.config.is_configured():
            self.show_welcome_dialog()

    def build_ui(self):
        """Build the main UI."""
        # Title
        title = ft.Text(
            "Voice Training Data Creator",
            size=28,
            weight=ft.FontWeight.BOLD,
            color=COLORS.BLUE_700,
            text_align=ft.TextAlign.CENTER,
        )

        # Create tabs
        self.tabs = ft.Tabs(
            selected_index=0,
            animation_duration=300,
            tabs=[
                ft.Tab(
                    text="Record & Generate",
                    icon=ICONS.MIC,
                    content=self.build_recording_tab(),
                ),
                ft.Tab(
                    text="Dataset",
                    icon=ICONS.DATASET,
                    content=self.build_dataset_tab(),
                ),
                ft.Tab(
                    text="Settings",
                    icon=ICONS.SETTINGS,
                    content=self.build_settings_tab(),
                ),
            ],
            expand=True,
        )

        # Status bar
        self.status_bar = ft.Text(
            self.get_status_text(),
            size=12,
            color=COLORS.GREY_700,
        )

        # File/dir pickers (overlay components)
        self.dir_picker = ft.FilePicker(on_result=self.on_pick_directory)
        self.page.overlay.append(self.dir_picker)

        # Main layout
        self.page.add(
            ft.Column(
                [
                    title,
                    ft.Divider(height=20, color=COLORS.TRANSPARENT),
                    self.tabs,
                    ft.Divider(height=10, color=COLORS.TRANSPARENT),
                    self.status_bar,
                ],
                expand=True,
                spacing=10,
            )
        )

        # Menu bar
        self.page.appbar = ft.AppBar(
            title=ft.Text("Voice Training Data Creator"),
            center_title=False,
            bgcolor=COLORS.SURFACE,
            actions=[
                ft.IconButton(
                    ICONS.SETTINGS,
                    tooltip="Settings",
                    on_click=lambda _: self.open_settings(),
                ),
                ft.IconButton(
                    ICONS.BRIGHTNESS_6,
                    tooltip="Toggle theme",
                    on_click=lambda _: self.toggle_theme(),
                ),
                ft.IconButton(
                    ICONS.HELP,
                    tooltip="About",
                    on_click=lambda _: self.show_about(),
                ),
            ],
        )

    def build_recording_tab(self):
        """Build the recording and text generation tab.

        Returns:
            The tab content.
        """
        # Save button
        self.save_btn = ft.ElevatedButton(
            "💾 Save Sample",
            icon=ICONS.SAVE,
            on_click=self.save_sample,
            disabled=True,
            bgcolor=COLORS.GREEN_700,
            color=COLORS.WHITE,
            height=60,
        )

        # Auto-generate checkbox
        self.autogenerate_checkbox = ft.Checkbox(
            label="Auto-generate next sample after saving",
            value=self.config.get_autogenerate_next(),
            on_change=self.on_autogenerate_toggled,
        )

        # Text generation panel
        text_panel = self.build_text_panel()

        # Recording panel
        recording_panel = self.build_recording_panel()

        # Session statistics
        stats = self.build_statistics_panel()

        return ft.Container(
            content=ft.Column(
                [
                    self.save_btn,
                    self.autogenerate_checkbox,
                    text_panel,
                    recording_panel,
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
        )

        self.wpm_field = ft.TextField(
            label="Words Per Minute",
            value="150",
            width=200,
            keyboard_type=ft.KeyboardType.NUMBER,
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

        # Generate buttons
        self.generate_btn = ft.ElevatedButton(
            "🔄 Generate Text",
            icon=ICONS.REFRESH,
            on_click=self.generate_text,
            bgcolor=COLORS.BLUE_700,
            color=COLORS.WHITE,
        )

        self.new_sample_btn = ft.ElevatedButton(
            "➕ New Sample",
            icon=ICONS.ADD_CIRCLE,
            on_click=self.new_sample,
            disabled=True,
            bgcolor=COLORS.GREEN_700,
            color=COLORS.WHITE,
        )

        self.regenerate_btn = ft.ElevatedButton(
            "♻ Regenerate",
            icon=ICONS.REPLAY,
            on_click=self.generate_text,
            disabled=True,
            bgcolor=COLORS.CYAN_700,
            color=COLORS.WHITE,
        )

        self.view_text_btn = ft.OutlinedButton(
            "👁 View Text",
            icon=ICONS.VISIBILITY,
            on_click=lambda e: self.open_narration_view(),
            disabled=True,
        )

        # Text display
        self.text_edit = ft.TextField(
            label="Generated Text",
            multiline=True,
            min_lines=5,
            max_lines=10,
            hint_text="Generated text will appear here. You can edit it before saving.",
            on_change=self.on_text_changed,
        )

        self.char_count_label = ft.Text("Characters: 0 | Words: 0", size=12, color=COLORS.GREY_700)

        return ft.Card(
            content=ft.Container(
                content=ft.Column(
                    [
                        ft.Text("Text Generation", size=18, weight=ft.FontWeight.BOLD),
                        ft.Row([self.duration_field, self.wpm_field, self.style_dropdown]),
                        self.use_dict_checkbox,
                        self.dict_input,
                        ft.Row([self.generate_btn, self.new_sample_btn, self.regenerate_btn, self.view_text_btn], spacing=10),
                        ft.Divider(),
                        self.text_edit,
                        self.char_count_label,
                    ],
                    spacing=10,
                ),
                padding=15,
            ),
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
        )

        # Status and duration
        self.status_label = ft.Text(
            "Ready to record",
            size=16,
            weight=ft.FontWeight.BOLD,
            text_align=ft.TextAlign.CENTER,
        )

        self.duration_label = ft.Text(
            "Duration: 00:00",
            size=32,
            weight=ft.FontWeight.BOLD,
            color=COLORS.BLUE_700,
            text_align=ft.TextAlign.CENTER,
        )

        # Recording buttons (only one visible at a time)
        self.record_btn = ft.ElevatedButton(
            "⏺ Record",
            icon=ICONS.FIBER_MANUAL_RECORD,
            on_click=self.start_recording,
            bgcolor=COLORS.RED_700,
            color=COLORS.WHITE,
            expand=True,
            visible=True,
        )

        self.pause_btn = ft.ElevatedButton(
            "⏸ Pause",
            icon=ICONS.PAUSE,
            on_click=self.toggle_pause,
            bgcolor=COLORS.ORANGE_700,
            color=COLORS.WHITE,
            expand=True,
            visible=False,
        )

        self.stop_btn = ft.ElevatedButton(
            "⏹ Stop",
            icon=ICONS.STOP,
            on_click=self.stop_recording,
            bgcolor=COLORS.GREY_700,
            color=COLORS.WHITE,
            expand=True,
            visible=False,
        )

        self.retake_btn = ft.ElevatedButton(
            "🔄 Retake",
            icon=ICONS.REPLAY,
            on_click=self.retake_recording,
            bgcolor=COLORS.ORANGE_700,
            color=COLORS.WHITE,
            expand=True,
            visible=False,
        )

        self.delete_btn = ft.OutlinedButton(
            "🗑 Delete Recording",
            icon=ICONS.DELETE,
            on_click=self.delete_recording,
            disabled=True,
            expand=True,
        )

        return ft.Card(
            content=ft.Container(
                content=ft.Column(
                    [
                        ft.Text("Recording Controls", size=18, weight=ft.FontWeight.BOLD),
                        ft.Row([self.device_dropdown, self.test_mic_btn]),
                        self.status_label,
                        self.duration_label,
                        ft.Row([self.record_btn, self.pause_btn, self.stop_btn, self.retake_btn], spacing=10),
                        self.delete_btn,
                    ],
                    spacing=15,
                ),
                padding=15,
            ),
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
                        ft.Text("Session Statistics", size=18, weight=ft.FontWeight.BOLD),
                        ft.Row(
                            [self.session_label, self.total_label, self.duration_stats_label],
                            spacing=30,
                        ),
                    ],
                    spacing=10,
                ),
                padding=15,
            ),
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
        self.view_text_btn.disabled = not has_text
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
                self.view_text_btn.disabled = False
            else:
                self.show_error_dialog("No Text", "No text was generated. Please try again.")

        except Exception as ex:
            self.show_error_dialog("Error", str(ex))
        finally:
            self.generate_btn.disabled = False
            self.generate_btn.text = "🔄 Generate Text"
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
        self.view_text_btn.disabled = True
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

        # Update buttons visibility and status
        self.record_btn.visible = False
        self.pause_btn.visible = True
        self.stop_btn.visible = True
        self.retake_btn.visible = True
        self.delete_btn.disabled = True
        self.status_label.value = "Recording..."
        self.duration_label.value = "Duration: 00:00"
        self.page.update()

        # Start timer thread to update duration label live
        self._record_timer_stop.clear()

        def _timer_loop():
            while not self._record_timer_stop.is_set():
                seconds = self.audio_recorder.get_duration()
                mins = int(seconds // 60)
                secs = int(seconds % 60)
                self.duration_label.value = f"Duration: {mins:02d}:{secs:02d}"
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
            self.pause_btn.text = "▶ Resume"
            self.status_label.value = "Paused"
        else:
            self.audio_recorder.resume_recording()
            self.pause_btn.text = "⏸ Pause"
            self.status_label.value = "Recording..."
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
            self.status_label.value = "No audio captured"
            self.record_btn.visible = True
            self.pause_btn.visible = False
            self.stop_btn.visible = False
            self.retake_btn.visible = False
            self.delete_btn.disabled = True
            self.page.update()
            return

        self.current_audio = audio
        seconds = self.audio_recorder.get_duration(audio)
        mins = int(seconds // 60)
        secs = int(seconds % 60)
        self.duration_label.value = f"Duration: {mins:02d}:{secs:02d}"
        self.status_label.value = "Recording complete"

        # Update buttons visibility
        self.record_btn.visible = True
        self.pause_btn.visible = False
        self.pause_btn.text = "⏸ Pause"
        self.stop_btn.visible = False
        self.retake_btn.visible = False
        self.delete_btn.disabled = False

        # Enable save if text exists
        self.check_save_enabled()
        self.page.update()

    def delete_recording(self, e):
        """Delete current recording."""
        self.current_audio = None
        self.audio_recorder.clear_audio()
        self.duration_label.value = "Duration: 00:00"
        self.status_label.value = "Recording deleted"
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
