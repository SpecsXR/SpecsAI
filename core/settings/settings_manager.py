import json
import os
import logging
from core.config import Config

class SettingsManager:
    """
    Manages user settings and configuration persistence.
    Saves settings to 'user_settings.json' in the project root.
    """
    _instance = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(SettingsManager, cls).__new__(cls)
            cls._instance._initialized = False
        return cls._instance

    def __init__(self):
        if self._initialized:
            return
        
        self.logger = logging.getLogger("SettingsManager")
        self.settings_file = os.path.join(Config.BASE_DIR, "user_settings.json")
        self.settings = self._load_settings()
        self._initialized = True

    def _get_default_settings(self):
        """Returns the default configuration."""
        return {
            "ai": {
                "provider": "auto", # auto (Fastest/Smartest), gemini, ollama, openai, claude
                "gemini_api_key": "",
                "gemini_model": "gemini-1.5-flash", # Revert to 1.5-flash as default (most stable free tier)
                "ollama_url": "http://localhost:11434",
                "ollama_model": "llama3",
                "openai_api_key": "",
                "openai_model": "gpt-4o-mini",
                "groq_api_key": "",
                "groq_model": "llama-3.3-70b-versatile",
                "sambanova_api_key": "",
                "sambanova_model": "Meta-Llama-3.1-70B-Instruct",
                "huggingface_api_key": "",
                "huggingface_model": "meta-llama/Meta-Llama-3-8B-Instruct",
                "claude_api_key": "",
                "claude_model": "claude-3-5-sonnet-20240620"
            },
            "system": {
                "always_on_top": True,
                "transparent_mode": True,
                "language": "Auto"
            }
        }

    def _load_settings(self):
        """Loads settings from JSON file or creates default if not exists."""
        if not os.path.exists(self.settings_file):
            defaults = self._get_default_settings()
            self._save_settings_to_file(defaults)
            return defaults
        
        try:
            with open(self.settings_file, 'r', encoding='utf-8') as f:
                saved_settings = json.load(f)
                # Merge with defaults to ensure all keys exist (migration support)
                defaults = self._get_default_settings()
                return self._deep_merge(defaults, saved_settings)
        except Exception as e:
            self.logger.error(f"Failed to load settings: {e}")
            return self._get_default_settings()

    def _deep_merge(self, defaults, overrides):
        """Recursively merge dictionary overrides into defaults."""
        for key, value in overrides.items():
            if isinstance(value, dict) and key in defaults:
                defaults[key] = self._deep_merge(defaults[key], value)
            else:
                defaults[key] = value
        return defaults

    def _save_settings_to_file(self, settings):
        """Writes settings to the JSON file."""
        try:
            with open(self.settings_file, 'w', encoding='utf-8') as f:
                json.dump(settings, f, indent=4)
        except Exception as e:
            self.logger.error(f"Failed to save settings: {e}")

    def get(self, section, key, default=None):
        """Retrieves a setting value."""
        try:
            return self.settings.get(section, {}).get(key, default)
        except Exception:
            return default

    def set(self, section, key, value):
        """Updates a setting value and saves to file."""
        if section not in self.settings:
            self.settings[section] = {}
        self.settings[section][key] = value
        self._save_settings_to_file(self.settings)
        self.logger.info(f"Setting updated: {section}.{key} = {value}")

    def get_all(self):
        return self.settings
