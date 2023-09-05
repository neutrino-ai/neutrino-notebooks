import json
import os
import uuid
from pathlib import Path
import requests
from neutrino_cli.__version__ import __version__

ANALYTICS_URL = "https://neutrino-notebooks-analytics-b8d66902d82c.herokuapp.com"
CLI_CONFIG_PATH = Path(os.path.expanduser("~/.neutrino-config.json"))


class Telemetry:
    """Telemetry class for CLI."""

    def __init__(self):
        self.config = {}
        self.load_config()

    def load_config(self) -> None:
        """Load the configuration data from file or create a default configuration."""
        try:
            with open(CLI_CONFIG_PATH, "r") as f:
                self.config = json.load(f)
        except FileNotFoundError:
            self.config = {
                "user_id": str(uuid.uuid4()),
                "telemetry_enabled": True,
                "include_traceback": False
            }
            self.save_config()

    def save_config(self) -> None:
        """Save the current configuration data to file."""
        with open(CLI_CONFIG_PATH, "w") as f:
            json.dump(self.config, f)

    def get_cli_id(self) -> str:
        """Retrieve or create a unique CLI identifier."""
        if 'user_id' not in self.config:
            self.config['user_id'] = str(uuid.uuid4())
            self.save_config()

        return self.config['user_id']

    def is_telemetry_enabled(self) -> bool:
        """Check if telemetry is enabled in the config."""
        return self.config.get("telemetry_enabled", True)

    def toggle_telemetry(self, status: bool) -> None:
        """Set the telemetry setting based on the provided status.

        Args:
            status (bool): Whether to enable telemetry.
        """
        self.config["telemetry_enabled"] = status
        self.save_config()

    def toggle_traceback(self, status: bool) -> None:
        """Set the traceback setting based on the provided status.

        Args:
            status (bool): Whether to include traceback in telemetry data.
        """
        self.config["include_traceback"] = status
        self.save_config()

    def send(self, action: str, success: bool, error: str = None, traceback: str = None):
        """Send telemetry data if enabled."""
        if not self.is_telemetry_enabled():
            return

        payload = {
            "user_id": self.get_cli_id(),
            "action": action,
            "version": __version__,
            "success": success,
        }

        if error:
            payload["error"] = error

        if self.config.get("include_traceback", False) and traceback:
            payload["traceback"] = traceback

        try:
            response = requests.post(
                f"{ANALYTICS_URL}/api/cli-analytics/track-cli-action",
                json=payload,
                headers={'Content-Type': 'application/json'},
                timeout=1,
            )
        except Exception as e:
            pass
