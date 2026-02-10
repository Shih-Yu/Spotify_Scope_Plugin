"""Configuration manager for live config updates without restart."""

import json
import logging
import os
import time
from pathlib import Path
from typing import Any, Optional

logger = logging.getLogger(__name__)

# Default config location
DEFAULT_CONFIG_PATH = Path.home() / ".scope-spotify" / "config.json"

# Default configuration
DEFAULT_CONFIG = {
    "input_source": "manual",
    "song_title": "Blinding Lights",
    "artist": "The Weeknd",
    "album": "After Hours",
    "genre": "pop",
    "progress": 50.0,
    "prompt_mode": "lyrics",
    "art_style": "surreal digital art, cinematic lighting",
    "lyrics_lines": 2,
    "auto_advance_lyrics": True,
    "lyrics_advance_seconds": 5.0,
}


class ConfigManager:
    """Manages live configuration that can be updated without restart.
    
    The config file is checked for changes on each call, allowing
    real-time updates by simply editing the JSON file.
    """
    
    def __init__(self, config_path: Optional[Path] = None):
        """Initialize the config manager.
        
        Args:
            config_path: Path to config file. Defaults to ~/.scope-spotify/config.json
        """
        self.config_path = config_path or DEFAULT_CONFIG_PATH
        self._config: dict = DEFAULT_CONFIG.copy()
        self._last_modified: float = 0
        self._last_check: float = 0
        self._check_interval: float = 1.0  # Check file every 1 second max
        
        # Ensure config directory exists
        self.config_path.parent.mkdir(parents=True, exist_ok=True)
        
        # Create default config if it doesn't exist
        if not self.config_path.exists():
            self._write_config(DEFAULT_CONFIG)
            logger.info(f"Created default config at: {self.config_path}")
        
        # Load initial config
        self._load_config()
    
    def _write_config(self, config: dict) -> None:
        """Write config to file with nice formatting."""
        with open(self.config_path, 'w') as f:
            json.dump(config, f, indent=2)
    
    def _load_config(self) -> bool:
        """Load config from file if it has changed.
        
        Returns:
            True if config was reloaded, False if unchanged
        """
        try:
            # Check if file exists
            if not self.config_path.exists():
                return False
            
            # Check modification time
            mtime = self.config_path.stat().st_mtime
            
            if mtime > self._last_modified:
                with open(self.config_path, 'r') as f:
                    new_config = json.load(f)
                
                # Merge with defaults (so new fields get default values)
                self._config = {**DEFAULT_CONFIG, **new_config}
                self._last_modified = mtime
                logger.info(f"Reloaded config: {self._config.get('song_title')} by {self._config.get('artist')}")
                return True
            
            return False
            
        except json.JSONDecodeError as e:
            logger.error(f"Invalid JSON in config file: {e}")
            return False
        except Exception as e:
            logger.error(f"Error loading config: {e}")
            return False
    
    def get(self, key: str, default: Any = None) -> Any:
        """Get a config value, checking for file updates first.
        
        Args:
            key: Config key to get
            default: Default value if key not found
            
        Returns:
            Config value
        """
        # Rate-limit file checks
        now = time.time()
        if now - self._last_check >= self._check_interval:
            self._load_config()
            self._last_check = now
        
        return self._config.get(key, default)
    
    def get_all(self) -> dict:
        """Get all config values, checking for file updates first.
        
        Returns:
            Full config dictionary
        """
        now = time.time()
        if now - self._last_check >= self._check_interval:
            self._load_config()
            self._last_check = now
        
        return self._config.copy()
    
    def set(self, key: str, value: Any) -> None:
        """Set a config value and save to file.
        
        Args:
            key: Config key to set
            value: Value to set
        """
        self._config[key] = value
        self._write_config(self._config)
        self._last_modified = self.config_path.stat().st_mtime
    
    def update(self, updates: dict) -> None:
        """Update multiple config values and save to file.
        
        Args:
            updates: Dictionary of key-value pairs to update
        """
        self._config.update(updates)
        self._write_config(self._config)
        self._last_modified = self.config_path.stat().st_mtime
    
    @property
    def path(self) -> Path:
        """Get the config file path."""
        return self.config_path


# Global config manager instance
_config_manager: Optional[ConfigManager] = None


def get_config_manager() -> ConfigManager:
    """Get the global config manager instance."""
    global _config_manager
    if _config_manager is None:
        _config_manager = ConfigManager()
    return _config_manager
