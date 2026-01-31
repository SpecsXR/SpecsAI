import threading
from typing import Optional, Callable
from SpecsAI.engine import SpecsEngine
from core.settings.settings_manager import SettingsManager

class AIService:
    """
    Bridge between the App UI and the standalone SpecsAI Engine.
    """
    def __init__(self, online_manager=None, model: str = "llama3"):
        self.settings = SettingsManager()
        
        # Load API Keys from main project settings
        api_keys = {
            "groq": self.settings.get("ai", "groq_api_key", ""),
            "gemini": self.settings.get("ai", "gemini_api_key", ""),
            "claude": self.settings.get("ai", "claude_api_key", ""),
            "openai": self.settings.get("ai", "openai_api_key", ""),
            "sambanova": self.settings.get("ai", "sambanova_api_key", ""),
            "huggingface": self.settings.get("ai", "huggingface_api_key", "")
        }
        
        # Initialize the Portable SpecsAI Engine
        self.engine = SpecsEngine(api_keys=api_keys, storage_path="specs_memory.json")
        self.force_offline = False 

    def set_force_offline(self, enabled: bool):
        # SpecsEngine currently handles auto-fallback, but we can add explicit offline flag later
        self.force_offline = enabled

    def set_system_prompt(self, prompt: str):
        # SpecsEngine has its own Identity Lock (Config.py)
        # But if we need to inject UI-specific instructions (like 'You are currently in SpecsAI App'):
        pass 

    def generate_response(self, prompt: str, callback: Optional[Callable[[str], None]] = None, image_data=None) -> str:
        """
        Delegates generation to the SpecsAI Engine.
        """
        # Get active provider from settings (auto/specsai, gemini, groq, etc.)
        provider = self.settings.get("ai", "provider", "auto")
        
        # Get active role/persona
        role = self.settings.get("ai", "role", "default")
        
        return self.engine.generate_response(prompt, callback, provider=provider, image_data=image_data, role=role)
