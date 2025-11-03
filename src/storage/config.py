"""Application configuration management."""
import json
from pathlib import Path
from typing import Optional, Dict, Any
import keyring


class ConfigManager:
    """Manages application configuration and settings."""

    APP_NAME = "VoiceTrainingDataCreator"
    CONFIG_FILE = Path.home() / ".config" / APP_NAME / "config.json"

    # Default configuration values
    DEFAULTS = {
        "base_path": None,
        "sample_rate": 44100,
        "bit_depth": 16,
        "default_wpm": 150,
        "default_duration": 3.0,
        "default_style": "General Purpose",
        "openai_model": "gpt-4o-mini",
        "theme": "light",
        "preferred_device_index": None,
        "preferred_device_name": None,
        "autogenerate_next": False
    }

    def __init__(self):
        """Initialize configuration manager."""
        self._config: Dict[str, Any] = {}
        self._load_config()

    def _load_config(self):
        """Load configuration from file."""
        if self.CONFIG_FILE.exists():
            try:
                with open(self.CONFIG_FILE, 'r') as f:
                    self._config = json.load(f)
            except Exception as e:
                print(f"Error loading config: {e}")
                self._config = self.DEFAULTS.copy()
        else:
            self._config = self.DEFAULTS.copy()

    def _save_config(self):
        """Save configuration to file."""
        try:
            self.CONFIG_FILE.parent.mkdir(parents=True, exist_ok=True)
            with open(self.CONFIG_FILE, 'w') as f:
                json.dump(self._config, f, indent=2)
        except Exception as e:
            print(f"Error saving config: {e}")

    def get(self, key: str, default: Any = None) -> Any:
        """Get a configuration value.

        Args:
            key: Configuration key.
            default: Default value if key not found.

        Returns:
            Configuration value or default.
        """
        return self._config.get(key, default)

    def set(self, key: str, value: Any):
        """Set a configuration value.

        Args:
            key: Configuration key.
            value: Value to set.
        """
        self._config[key] = value
        self._save_config()

    def get_base_path(self) -> Optional[Path]:
        """Get the base path for storing samples.

        Returns:
            Path object or None if not set.
        """
        base_path = self._config.get("base_path")
        if base_path:
            return Path(base_path)
        return None

    def set_base_path(self, path: Path):
        """Set the base path for storing samples.

        Args:
            path: Base path to use.
        """
        self.set("base_path", str(path))

    def get_api_key(self) -> Optional[str]:
        """Get OpenAI API key from secure storage.

        Returns:
            API key or None if not set.
        """
        try:
            return keyring.get_password(self.APP_NAME, "openai_api_key")
        except Exception as e:
            print(f"Error retrieving API key: {e}")
            return None

    def set_api_key(self, api_key: str):
        """Store OpenAI API key securely.

        Args:
            api_key: API key to store.
        """
        try:
            keyring.set_password(self.APP_NAME, "openai_api_key", api_key)
        except Exception as e:
            print(f"Error storing API key: {e}")

    def delete_api_key(self):
        """Delete stored API key."""
        try:
            keyring.delete_password(self.APP_NAME, "openai_api_key")
        except Exception as e:
            print(f"Error deleting API key: {e}")

    def is_configured(self) -> bool:
        """Check if the application is properly configured.

        Returns:
            True if base path is set, False otherwise.
        """
        return self.get_base_path() is not None

    def get_sample_rate(self) -> int:
        """Get configured sample rate."""
        return self.get("sample_rate", self.DEFAULTS["sample_rate"])

    def set_sample_rate(self, rate: int):
        """Set sample rate."""
        self.set("sample_rate", rate)

    def get_openai_model(self) -> str:
        """Get configured OpenAI model."""
        return self.get("openai_model", self.DEFAULTS["openai_model"])

    def set_openai_model(self, model: str):
        """Set OpenAI model."""
        self.set("openai_model", model)

    def get_preferred_device(self) -> Optional[Dict[str, Any]]:
        """Get preferred microphone device.

        Returns:
            Dictionary with device_index and device_name, or None if not set.
        """
        device_index = self.get("preferred_device_index")
        device_name = self.get("preferred_device_name")

        if device_index is not None:
            return {
                "device_index": device_index,
                "device_name": device_name
            }
        return None

    def set_preferred_device(self, device_index: int, device_name: str):
        """Set preferred microphone device.

        Args:
            device_index: Index of the preferred device.
            device_name: Name of the preferred device.
        """
        self.set("preferred_device_index", device_index)
        self.set("preferred_device_name", device_name)

    def get_autogenerate_next(self) -> bool:
        """Get autogenerate next sample setting.

        Returns:
            True if autogenerate is enabled, False otherwise.
        """
        return self.get("autogenerate_next", self.DEFAULTS["autogenerate_next"])

    def set_autogenerate_next(self, enabled: bool):
        """Set autogenerate next sample setting.

        Args:
            enabled: Whether to autogenerate next sample after saving.
        """
        self.set("autogenerate_next", enabled)
