import json
import os
import platform
import shutil
from pathlib import Path
from typing import Dict, Any


class ConfigManager:
    """Manages configuration loading and creation for PrimeMinister."""

    def __init__(self):
        self.system = platform.system().lower()
        self.user_config_path = self._get_user_config_path()
        self.system_config_path = self._get_system_config_path()
        self.module_config_path = Path(__file__).parent / "config.json"

    def _get_user_config_path(self) -> Path:
        """Get user-specific config directory path based on platform."""
        if self.system == "windows":
            # Windows: My Documents/primeminister/config.json
            docs_path = Path.home() / "Documents" / "primeminister"
            return docs_path / "config.json"
        else:
            # Linux/macOS: ~/.primeminister/config.json
            return Path.home() / ".primeminister" / "config.json"

    def _get_system_config_path(self) -> Path:
        """Get system-wide config path (only used if running as root)."""
        if self.system == "linux":
            return Path("/etc/primeminister/config.json")
        else:
            # No system-wide config for Windows/macOS
            return None

    def get_config_path(self) -> Path:
        """Determine which config file to use."""
        # Only use system config if we're on Linux and running as root and it exists
        if (
            self.system == "linux"
            and os.geteuid() == 0
            and self.system_config_path
            and self.system_config_path.exists()
        ):
            return self.system_config_path

        # Check if user config exists
        if self.user_config_path.exists():
            return self.user_config_path

        # Fall back to module path
        return self.module_config_path

    def ensure_config_exists(self) -> Path:
        """Ensure configuration file exists, creating it if necessary."""
        # Only try system config if running as root on Linux
        if self.system == "linux" and os.geteuid() == 0 and self.system_config_path:
            try:
                if not self.system_config_path.exists():
                    self.system_config_path.parent.mkdir(parents=True, exist_ok=True)
                    # Copy from module path to system location
                    if self.module_config_path.exists():
                        shutil.copy2(self.module_config_path, self.system_config_path)
                    else:
                        self._create_default_config(self.system_config_path)
                return self.system_config_path
            except (PermissionError, OSError):
                # Fall back to user config if system config fails
                pass

        # Use user config directory
        if not self.user_config_path.exists():
            # Create user config directory
            self.user_config_path.parent.mkdir(parents=True, exist_ok=True)
            # Copy from module path or create default
            if self.module_config_path.exists():
                shutil.copy2(self.module_config_path, self.user_config_path)
            else:
                self._create_default_config(self.user_config_path)
        return self.user_config_path

    def load_config(self) -> Dict[str, Any]:
        """Load configuration from the appropriate location."""
        config_path = self.ensure_config_exists()

        try:
            with open(config_path, "r", encoding="utf-8") as f:
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

            with open(config_path, "w", encoding="utf-8") as f:
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
            with open(self.module_config_path, "r", encoding="utf-8") as f:
                default_config = json.load(f)
        except (FileNotFoundError, json.JSONDecodeError) as e:
            raise RuntimeError(f"Failed to load embedded default configuration: {e}")

        # Ensure directory exists
        path.parent.mkdir(parents=True, exist_ok=True)

        # Write the config to the target path
        with open(path, "w", encoding="utf-8") as f:
            json.dump(default_config, f, indent=2, ensure_ascii=False)
