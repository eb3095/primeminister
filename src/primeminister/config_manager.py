import json
import os
import platform
import shutil
from pathlib import Path
from typing import Dict, Any


class ConfigManager:
    """Manages configuration loading and creation for PrimeMinister."""

    def __init__(self):
        self.is_linux = platform.system().lower() == 'linux'
        self.etc_config_path = Path('/etc/primeminister/config.json')
        self.module_config_path = Path(__file__).parent / 'config.json'

    def get_config_path(self) -> Path:
        """Determine which config file to use."""
        if self.is_linux and self.etc_config_path.exists():
            return self.etc_config_path
        return self.module_config_path

    def ensure_config_exists(self) -> Path:
        """Ensure configuration file exists, creating it if necessary."""
        if self.is_linux:
            # On Linux, try to use /etc/primeminister/config.json
            if not self.etc_config_path.exists():
                # Create the directory if it doesn't exist
                try:
                    self.etc_config_path.parent.mkdir(parents=True, exist_ok=True)
                    # Copy from module path to /etc
                    if self.module_config_path.exists():
                        shutil.copy2(self.module_config_path, self.etc_config_path)
                        return self.etc_config_path
                    else:
                        # If module config doesn't exist, create default
                        self._create_default_config(self.etc_config_path)
                        return self.etc_config_path
                except (PermissionError, OSError):
                    # Fall back to module path if we can't write to /etc
                    pass
            else:
                return self.etc_config_path

        # Use module path (non-Linux or fallback)
        if not self.module_config_path.exists():
            self._create_default_config(self.module_config_path)
        return self.module_config_path

    def load_config(self) -> Dict[str, Any]:
        """Load configuration from the appropriate location."""
        config_path = self.ensure_config_exists()

        try:
            with open(config_path, 'r', encoding='utf-8') as f:
                config = json.load(f)
            return config
        except (json.JSONDecodeError, FileNotFoundError) as e:
            raise RuntimeError(f"Failed to load configuration from {config_path}: {e}")

    def save_config(self, config: Dict[str, Any]) -> None:
        """Save configuration to the appropriate location."""
        config_path = self.get_config_path()

        try:
            # Ensure directory exists
            config_path.parent.mkdir(parents=True, exist_ok=True)

            with open(config_path, 'w', encoding='utf-8') as f:
                json.dump(config, f, indent=2, ensure_ascii=False)
        except (OSError, PermissionError) as e:
            raise RuntimeError(f"Failed to save configuration to {config_path}: {e}")

    def _create_default_config(self, path) -> None:
        """Create a default configuration file by copying from the embedded config.json."""
        # Convert to Path object if it's a string
        if isinstance(path, str):
            path = Path(path)

        try:
            # Read the embedded default config
            with open(self.module_config_path, 'r', encoding='utf-8') as f:
                default_config = json.load(f)
        except (FileNotFoundError, json.JSONDecodeError) as e:
            raise RuntimeError(f"Failed to load embedded default configuration: {e}")

        # Ensure directory exists
        path.parent.mkdir(parents=True, exist_ok=True)

        # Write the config to the target path
        with open(path, 'w', encoding='utf-8') as f:
            json.dump(default_config, f, indent=2, ensure_ascii=False)