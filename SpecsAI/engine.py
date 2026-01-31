"""
SpecsAI Engine (Main Interface)
The brain of the operation. This is what external apps should import.
"""
import threading
import asyncio
import os
from .config import SpecsConfig
from .providers import AIProvider
from .memory import SpecsMemory

class SpecsEngine:
    def __init__(self, api_keys=None, storage_path=None):
        """
        Initialize SpecsAI Engine.
        api_keys: Dict containing 'groq', 'gemini', 'claude', 'openai' keys.
        storage_path: Path to save memory/history (optional).
        """
        self.api_keys = api_keys or {}
        self.memory = SpecsMemory(storage_path if storage_path else "specs_memory.json")
        self.provider = AIProvider(self.api_keys)
        self.history = [] # Runtime chat history
        
    def generate_response(self, text, callback=None, provider="auto", image_data=None, role="default"):
        """
        Generates a response using the unified brain.
        If callback is provided, runs async in background.
        provider: 'auto', 'gemini', 'groq', 'claude', 'ollama', 'openai'
        image_data: Optional PIL Image
        role: 'default', 'romantic', 'friendly', etc.
        """
        # Add to history
        self.history.append({"role": "user", "content": text})
        
        # Prepare System Prompt with Memory
        memory_context = self.memory.get_context_string()
        system_prompt = SpecsConfig.get_full_system_prompt(memory_context, role=role)
        
        if callback:
            thread = threading.Thread(target=self._run_async_wrapper, 
                                      args=(text, system_prompt, callback, provider, image_data))
            thread.daemon = True
            thread.start()
            return "Thinking..."
        else:
            # Synchronous call (blocking)
            return asyncio.run(self._process(text, system_prompt, provider, image_data))

    def _run_async_wrapper(self, text, system_prompt, callback, provider, image_data):
        response = asyncio.run(self._process(text, system_prompt, provider, image_data))
        if callback:
            callback(response)

    async def _process(self, text, system_prompt, provider="auto", image_data=None):
        # Pass last 10 messages for context
        context_history = self.history[-11:-1] if len(self.history) > 1 else []
        
        result = await self.provider.process_query(text, system_prompt, context_history, provider, image_data)
        
        response_text = ""
        if "text" in result:
            response_text = result["text"]
        elif "error" in result:
            # Sanitize errors for user-facing response; log internals to console
            print(f"[SpecsAI Error] {result['error']}")
            # Friendly generic message (no secret/error details)
            response_text = "I'm having trouble right now. Please try again in a moment."
        else:
            response_text = "I am lost for words."
            
        # Add to history
        self.history.append({"role": "assistant", "content": response_text})
        
        # Simple Memory Extraction (Self-Learning Stub)
        # In future, this can use a separate LLM call to extract facts
        if "my name is" in text.lower():
            name = text.lower().split("my name is")[-1].strip().split()[0].capitalize()
            self.memory.update("user_name", name)
            
        return response_text
