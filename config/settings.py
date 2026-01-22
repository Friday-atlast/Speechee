"""
Speechee - Settings Manager
Load, save, and manage configuration settings.
"""

import os
import sys
import json
import copy
from pathlib import Path
from typing import Any, Dict, Optional, Union

# Project paths
CONFIG_DIR = Path(__file__).parent
PROJECT_ROOT = CONFIG_DIR.parent

# Config file paths
DEFAULTS_FILE = CONFIG_DIR / "defaults.json"
USER_CONFIG_FILE = CONFIG_DIR / "config.json"


class ConfigError(Exception):
    """Configuration related errors."""
    pass


class Settings:
    """
    Configuration settings manager.
    
    Loads settings from:
    1. defaults.json (base defaults)
    2. config.json (user overrides)
    3. Runtime overrides (optional)
    
    Usage:
        settings = Settings()
        model = settings.get("stt.model")
        settings.set("stt.model", "base")
        settings.save()
    """
    
    _instance = None
    _initialized = False
    
    def __new__(cls):
        """Singleton pattern - only one Settings instance."""
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance
    
    def __init__(self):
        """Initialize settings (only once due to singleton)."""
        if Settings._initialized:
            return
        
        self._defaults: Dict[str, Any] = {}
        self._user_config: Dict[str, Any] = {}
        self._runtime_overrides: Dict[str, Any] = {}
        self._config: Dict[str, Any] = {}
        
        # Load configuration
        self._load_defaults()
        self._load_user_config()
        self._merge_configs()
        
        Settings._initialized = True
    
    def _load_defaults(self) -> None:
        """Load default configuration."""
        if DEFAULTS_FILE.exists():
            try:
                with open(DEFAULTS_FILE, "r", encoding="utf-8") as f:
                    self._defaults = json.load(f)
            except json.JSONDecodeError as e:
                print(f"[WARN] Invalid defaults.json: {e}")
                self._defaults = self._get_hardcoded_defaults()
        else:
            self._defaults = self._get_hardcoded_defaults()
    
    def _load_user_config(self) -> None:
        """Load user configuration."""
        if USER_CONFIG_FILE.exists():
            try:
                with open(USER_CONFIG_FILE, "r", encoding="utf-8") as f:
                    self._user_config = json.load(f)
            except json.JSONDecodeError as e:
                print(f"[WARN] Invalid config.json: {e}. Using defaults.")
                self._user_config = {}
        else:
            self._user_config = {}
    
    def _get_hardcoded_defaults(self) -> Dict[str, Any]:
        """Hardcoded fallback defaults if files are missing."""
        return {
            "app": {
                "name": "Speechee",
                "version": "1.0.0-dev",
                "mode": "offline",
                "debug": False
            },
            "stt": {
                "model": "tiny.en",
                "language": "auto",
                "threads": 4,
                "translate": False
            },
            "audio": {
                "sample_rate": 16000,
                "channels": 1,
                "format": "wav",
                "default_duration": 5,
                "max_duration": 300,
                "device_id": None
            },
            "output": {
                "format": "txt",
                "save_audio": False,
                "auto_save": False,
                "include_timestamps": True,
                "transcripts_dir": "output/transcripts",
                "temp_dir": "output/temp"
            },
            "models": {
                "default": "tiny.en",
                "default_multilingual": "tiny",
                "auto_download": False,
                "models_dir": "engine/models"
            },
            "api": {
                "enabled": False,
                "host": "127.0.0.1",
                "port": 8000,
                "cors_origins": ["*"]
            },
            "cli": {
                "show_banner": True,
                "colored_output": True,
                "verbose": False
            }
        }
    
    def _merge_configs(self) -> None:
        """Merge defaults, user config, and runtime overrides."""
        self._config = copy.deepcopy(self._defaults)
        self._deep_merge(self._config, self._user_config)
        self._deep_merge(self._config, self._runtime_overrides)
    
    def _deep_merge(self, base: Dict, override: Dict) -> None:
        """Deep merge override into base dictionary."""
        for key, value in override.items():
            if key.startswith("_"):  # Skip comment fields
                continue
            if key in base and isinstance(base[key], dict) and isinstance(value, dict):
                self._deep_merge(base[key], value)
            else:
                base[key] = copy.deepcopy(value)
    
    def get(self, key: str, default: Any = None) -> Any:
        """
        Get configuration value using dot notation.
        
        Args:
            key: Dot-separated key path (e.g., "stt.model")
            default: Default value if key not found
            
        Returns:
            Configuration value
            
        Example:
            settings.get("stt.model")  # Returns "tiny.en"
            settings.get("stt.threads", 4)  # Returns 4 or default
        """
        keys = key.split(".")
        value = self._config
        
        try:
            for k in keys:
                value = value[k]
            return value
        except (KeyError, TypeError):
            return default
    
    def set(self, key: str, value: Any, persist: bool = False) -> None:
        """
        Set configuration value.
        
        Args:
            key: Dot-separated key path
            value: Value to set
            persist: Save to config.json immediately
            
        Example:
            settings.set("stt.model", "base")
            settings.set("stt.model", "base", persist=True)
        """
        keys = key.split(".")
        
        # Update runtime overrides
        target = self._runtime_overrides
        for k in keys[:-1]:
            if k not in target:
                target[k] = {}
            target = target[k]
        target[keys[-1]] = value
        
        # Re-merge configs
        self._merge_configs()
        
        # Persist if requested
        if persist:
            self._update_user_config(key, value)
            self.save()
    
    def _update_user_config(self, key: str, value: Any) -> None:
        """Update user config dict with new value."""
        keys = key.split(".")
        target = self._user_config
        
        for k in keys[:-1]:
            if k not in target:
                target[k] = {}
            target = target[k]
        target[keys[-1]] = value
    
    def save(self) -> bool:
        """
        Save current user configuration to config.json.
        
        Returns:
            True if successful
        """
        try:
            # Merge runtime overrides into user config
            self._deep_merge(self._user_config, self._runtime_overrides)
            
            # Add comment
            config_to_save = {"_comment": "Speechee User Configuration"}
            config_to_save.update(self._user_config)
            
            with open(USER_CONFIG_FILE, "w", encoding="utf-8") as f:
                json.dump(config_to_save, f, indent=2, ensure_ascii=False)
            
            return True
        except Exception as e:
            print(f"[ERROR] Failed to save config: {e}")
            return False
    
    def reload(self) -> None:
        """Reload configuration from files."""
        self._runtime_overrides = {}
        self._load_defaults()
        self._load_user_config()
        self._merge_configs()
    
    def reset(self, key: Optional[str] = None) -> None:
        """
        Reset configuration to defaults.
        
        Args:
            key: Specific key to reset, or None for all
        """
        if key:
            # Reset specific key
            keys = key.split(".")
            
            # Remove from user config
            target = self._user_config
            for k in keys[:-1]:
                if k not in target:
                    return
                target = target[k]
            if keys[-1] in target:
                del target[keys[-1]]
            
            # Remove from runtime overrides
            target = self._runtime_overrides
            for k in keys[:-1]:
                if k not in target:
                    return
                target = target[k]
            if keys[-1] in target:
                del target[keys[-1]]
        else:
            # Reset all
            self._user_config = {}
            self._runtime_overrides = {}
        
        self._merge_configs()
    
    def get_section(self, section: str) -> Dict[str, Any]:
        """
        Get entire configuration section.
        
        Args:
            section: Section name (e.g., "stt", "audio")
            
        Returns:
            Section dictionary
        """
        return self._config.get(section, {})
    
    def get_all(self) -> Dict[str, Any]:
        """Get entire configuration."""
        return copy.deepcopy(self._config)
    
    def get_user_config(self) -> Dict[str, Any]:
        """Get user configuration only."""
        return copy.deepcopy(self._user_config)
    
    def to_json(self, indent: int = 2) -> str:
        """Export configuration as JSON string."""
        return json.dumps(self._config, indent=indent, ensure_ascii=False)
    
    def validate(self) -> Dict[str, Any]:
        """
        Validate configuration.
        
        Returns:
            Dict with validation results
        """
        issues = []
        
        # Check model
        model = self.get("stt.model")
        valid_models = ["tiny.en", "tiny", "base", "small", "medium", "large"]
        if model and model not in valid_models:
            issues.append(f"Invalid model: {model}")
        
        # Check language
        language = self.get("stt.language")
        if language and language != "auto" and len(language) != 2:
            issues.append(f"Invalid language code: {language}")
        
        # Check sample rate
        sample_rate = self.get("audio.sample_rate")
        if sample_rate and sample_rate not in [8000, 16000, 22050, 44100, 48000]:
            issues.append(f"Unusual sample rate: {sample_rate}")
        
        # Check duration
        default_duration = self.get("audio.default_duration")
        max_duration = self.get("audio.max_duration")
        if default_duration and default_duration > max_duration:
            issues.append("default_duration > max_duration")
        
        return {
            "valid": len(issues) == 0,
            "issues": issues
        }
    
    def print_config(self, section: Optional[str] = None) -> None:
        """Print configuration in formatted way."""
        if section:
            data = self.get_section(section)
            title = f"CONFIG: {section.upper()}"
        else:
            data = self._config
            title = "SPEECHEE CONFIGURATION"
        
        print("\n" + "=" * 60)
        print(title)
        print("=" * 60)
        self._print_dict(data, indent=0)
        print("=" * 60)
    
    def _print_dict(self, d: Dict, indent: int = 0) -> None:
        """Print dictionary with indentation."""
        for key, value in d.items():
            if key.startswith("_"):
                continue
            prefix = "  " * indent
            if isinstance(value, dict):
                print(f"{prefix}{key}:")
                self._print_dict(value, indent + 1)
            else:
                print(f"{prefix}{key}: {value}")


# ================================================================
# CONVENIENCE FUNCTIONS
# ================================================================

_settings_instance: Optional[Settings] = None

def get_settings() -> Settings:
    """Get singleton Settings instance."""
    global _settings_instance
    if _settings_instance is None:
        _settings_instance = Settings()
    return _settings_instance


def get_config_value(key: str, default: Any = None) -> Any:
    """
    Quick access to config value.
    
    Args:
        key: Dot-separated key path
        default: Default value
        
    Returns:
        Configuration value
    """
    return get_settings().get(key, default)


# ================================================================
# CLI INTERFACE
# ================================================================

def print_help():
    """Print help message."""
    help_text = """
================================================================================
SPEECHEE CONFIG MANAGER - HELP
================================================================================

USAGE:
  python settings.py <command> [options]

COMMANDS:
  show              Show all configuration
  show <section>    Show specific section (stt, audio, output, etc.)
  get <key>         Get specific value (e.g., stt.model)
  set <key> <value> Set value (e.g., stt.model base)
  reset             Reset to defaults
  reset <key>       Reset specific key
  validate          Validate configuration
  path              Show config file paths
  help              Show this help

EXAMPLES:
  python settings.py show
  python settings.py show stt
  python settings.py get stt.model
  python settings.py set stt.model base
  python settings.py set audio.default_duration 10
  python settings.py reset stt.model
  python settings.py validate

SECTIONS:
  app       Application settings
  stt       Speech-to-text settings
  audio     Audio recording settings
  output    Output formatting settings
  models    Model management settings
  api       API server settings
  cli       CLI interface settings

================================================================================
"""
    print(help_text)


def main():
    """Command line interface."""
    import argparse
    
    parser = argparse.ArgumentParser(
        description="Speechee Config Manager",
        add_help=False
    )
    parser.add_argument("command", nargs="?", default="help")
    parser.add_argument("args", nargs="*")
    parser.add_argument("--help", "-h", action="store_true")
    
    args = parser.parse_args()
    
    if args.help or args.command == "help":
        print_help()
        return
    
    settings = get_settings()
    
    if args.command == "show":
        if args.args:
            settings.print_config(args.args[0])
        else:
            settings.print_config()
    
    elif args.command == "get":
        if not args.args:
            print("[ERROR] Key required. Example: python settings.py get stt.model")
            return
        key = args.args[0]
        value = settings.get(key)
        if value is not None:
            print(f"{key} = {value}")
        else:
            print(f"[WARN] Key not found: {key}")
    
    elif args.command == "set":
        if len(args.args) < 2:
            print("[ERROR] Key and value required. Example: python settings.py set stt.model base")
            return
        key = args.args[0]
        value = args.args[1]
        
        # Try to parse value type
        if value.lower() == "true":
            value = True
        elif value.lower() == "false":
            value = False
        elif value.lower() == "null" or value.lower() == "none":
            value = None
        else:
            try:
                value = int(value)
            except ValueError:
                try:
                    value = float(value)
                except ValueError:
                    pass  # Keep as string
        
        settings.set(key, value, persist=True)
        print(f"[SUCCESS] {key} = {value}")
        print(f"[SAVED] {USER_CONFIG_FILE}")
    
    elif args.command == "reset":
        if args.args:
            key = args.args[0]
            settings.reset(key)
            settings.save()
            print(f"[SUCCESS] Reset: {key}")
        else:
            confirm = input("Reset ALL settings to defaults? (yes/no): ")
            if confirm.lower() == "yes":
                settings.reset()
                settings.save()
                print("[SUCCESS] All settings reset to defaults")
            else:
                print("[CANCELLED]")
    
    elif args.command == "validate":
        result = settings.validate()
        if result["valid"]:
            print("[SUCCESS] Configuration is valid")
        else:
            print("[WARNING] Configuration issues found:")
            for issue in result["issues"]:
                print(f"  - {issue}")
    
    elif args.command == "path":
        print(f"\nConfig Directory: {CONFIG_DIR}")
        print(f"Defaults File:    {DEFAULTS_FILE}")
        print(f"User Config:      {USER_CONFIG_FILE}")
        print(f"Defaults exists:  {DEFAULTS_FILE.exists()}")
        print(f"User config exists: {USER_CONFIG_FILE.exists()}")
    
    elif args.command == "export":
        print(settings.to_json())
    
    else:
        print(f"[ERROR] Unknown command: {args.command}")
        print_help()


if __name__ == "__main__":
    main()