import aiohttp
import asyncio
import json
import logging
from core.settings.settings_manager import SettingsManager

class OnlineManager:
    """
    Manages online connectivity and API communication for Specs Online Mode.
    Uses Google Gemini API (Free Tier) for high-performance AI.
    """
    def __init__(self):
        self.is_connected = False
        self.logger = logging.getLogger("OnlineManager")
        self.settings_manager = SettingsManager()
        
        # Load initial config
        self._load_config()

    def _load_config(self):
        self.provider = self.settings_manager.get("ai", "provider", "auto")
        
        # Load all keys
        self.gemini_key = self.settings_manager.get("ai", "gemini_api_key", "")
        self.groq_key = self.settings_manager.get("ai", "groq_api_key", "")
        self.claude_key = self.settings_manager.get("ai", "claude_api_key", "")
        self.openai_key = self.settings_manager.get("ai", "openai_api_key", "")
        
        # Set active key based on provider (legacy support)
        if self.provider == "gemini":
            self.api_key = self.gemini_key
            self.model_name = self.settings_manager.get("ai", "gemini_model", "gemini-1.5-flash")
        elif self.provider == "groq":
            self.api_key = self.groq_key
            self.model_name = self.settings_manager.get("ai", "groq_model", "llama3-70b-8192")
        elif self.provider == "claude":
            self.api_key = self.claude_key
            self.model_name = self.settings_manager.get("ai", "claude_model", "claude-3-5-sonnet-20240620")
        elif self.provider == "openai":
            self.api_key = self.openai_key
            self.model_name = self.settings_manager.get("ai", "openai_model", "gpt-3.5-turbo")
        else:
            # Auto Mode
            self.api_key = None 
            self.model_name = ""

    async def connect(self):
        """Establishes connection to the online service."""
        try:
            self._load_config() # Reload config on connect
            
            # Check if ANY Provider is Online
            if self.provider == "auto":
                 if (self.groq_key and len(self.groq_key) > 10) or \
                    (self.gemini_key and len(self.gemini_key) > 10) or \
                    (self.claude_key and len(self.claude_key) > 10):
                     self.is_connected = True
                     self.logger.info("Online Manager initialized (Auto Mode)")
                 else:
                     self.is_connected = False
                     self.logger.info("Online Manager initialized (Passive Mode - No Keys)")
            elif self.api_key and len(self.api_key) > 10:
                self.is_connected = True
                self.logger.info(f"Online Manager initialized ({self.provider.capitalize()} AI Active)")
            else:
                self.is_connected = False
                self.logger.info(f"Online Manager initialized (Passive Mode - Provider: {self.provider})")
                
            return True
        except Exception as e:
            self.logger.error(f"Failed to connect to online service: {e}")
            self.is_connected = False
            return False

    async def close(self):
        self.is_connected = False

    async def process_query(self, text, system_prompt="", history=None):
        """Sends user query to selected Online Provider."""
        # Always reload config to get latest key
        self._load_config()
        
        # Check connection status again after reload
        if self.provider == "auto":
            # Auto Mode Logic: FASTEST PRIORITY (Groq -> Gemini -> Claude)
            
            # 1. Try Groq (Fastest)
            if self.groq_key and len(self.groq_key) > 10:
                self.api_key = self.groq_key
                self.model_name = self.settings_manager.get("ai", "groq_model", "llama3-70b-8192")
                res = await self._process_groq(text, system_prompt, history)
                if res and not res.get("error"):
                    return res
                # If Groq fails, fall through to Gemini
                self.logger.warning("Groq failed in Auto Mode, falling back to Gemini...")
            
            # 2. Try Gemini (Reliable/Free)
            if self.gemini_key and len(self.gemini_key) > 10:
                self.api_key = self.gemini_key
                self.model_name = self.settings_manager.get("ai", "gemini_model", "gemini-1.5-flash")
                res = await self._process_gemini(text, system_prompt, history)
                if res and not res.get("error"):
                    return res
            
            return {
                "text": "Online Mode Unavailable. No valid API keys found for Auto Mode (Groq/Gemini).",
                "error": "auth_error"
            }
        
        # Specific Provider Logic
        if not self.api_key or len(self.api_key) < 10:
             return {
                "text": f"Online Mode Unavailable. Please check your API Key for {self.provider.upper()} in Settings.",
                "error": "auth_error"
            }
            
        if self.provider == "claude":
            return await self._process_claude(text, system_prompt, history)
            
        if self.provider == "openai":
            # return await self._process_openai(text, system_prompt, history)
            return {"text": "OpenAI not implemented yet.", "error": "not_implemented"}
            
        if self.provider == "groq":
            return await self._process_groq(text, system_prompt, history)

        # Default to Gemini
        return await self._process_gemini(text, system_prompt, history)

    async def _process_gemini(self, text, system_prompt="", history=None):
        """Encapsulated Gemini Logic"""
        url = f"https://generativelanguage.googleapis.com/v1beta/models/{self.model_name}:generateContent?key={self.api_key}"
        
        contents = []
        
        if history:
             # Re-map history to Gemini format
             sanitized_contents = []
             last_role = None
             
             for msg in history:
                 role = "user" if msg["role"] == "user" else "model"
                 content = msg["content"]
                 
                 if role == last_role:
                     sanitized_contents[-1]["parts"][0]["text"] += f"\n\n{content}"
                 else:
                     sanitized_contents.append({
                         "role": role,
                         "parts": [{"text": content}]
                     })
                     last_role = role
             
             contents = sanitized_contents
        else:
            contents.append({
                "role": "user",
                "parts": [{"text": f"System Instruction: {system_prompt}\n\nUser: {text}"}]
            })

        if contents:
            if contents[0]["role"] == "user":
                contents[0]["parts"][0]["text"] = f"System Instruction: {system_prompt}\n\n" + contents[0]["parts"][0]["text"]
            else:
                contents.insert(0, {
                    "role": "user",
                    "parts": [{"text": f"System Instruction: {system_prompt}"}]
                })

        payload = {
            "contents": contents,
            "generationConfig": {
                "temperature": 0.9, 
                "topK": 40,
                "topP": 0.95,
                "maxOutputTokens": 1024,
            }
        }
        
        try:
            async with aiohttp.ClientSession() as session:
                async with session.post(url, json=payload) as resp:
                    if resp.status == 200:
                        data = await resp.json()
                        try:
                            result_text = data['candidates'][0]['content']['parts'][0]['text']
                            return {"text": result_text.strip(), "emotion": "neutral"}
                        except KeyError:
                            self.logger.error(f"Invalid Gemini response format: {data}")
                            return None
                    elif resp.status == 429:
                        self.logger.warning("Gemini API Quota Exceeded (429)")
                        return {
                            "text": "API Quota Exceeded. You have reached the limit for the Free Tier. Please wait a while.",
                            "error": "quota_exceeded"
                        }
                    else:
                        error_text = await resp.text()
                        self.logger.error(f"Gemini API Error {resp.status}: {error_text}")
                        return None
                    
        except Exception as e:
            self.logger.error(f"Network Error: {e}")
            return None

    async def _process_groq(self, text, system_prompt="", history=None):
        """Sends user query to Groq API (OpenAI compatible)"""
        url = "https://api.groq.com/openai/v1/chat/completions"
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json"
        }
        
        messages = [{"role": "system", "content": system_prompt}]
        
        if history:
            for msg in history:
                messages.append({
                    "role": msg["role"],
                    "content": msg["content"]
                })
        else:
             messages.append({"role": "user", "content": text})
             
        payload = {
            "model": self.model_name,
            "messages": messages,
            "temperature": 0.7,
            "max_completion_tokens": 1024
        }
        
        try:
            async with aiohttp.ClientSession() as session:
                async with session.post(url, json=payload, headers=headers) as resp:
                    if resp.status == 200:
                        data = await resp.json()
                        result_text = data['choices'][0]['message']['content']
                        return {"text": result_text.strip(), "emotion": "neutral"}
                    elif resp.status == 429:
                         return {
                             "text": "Groq API Limit Reached. Please wait a moment.",
                             "error": "quota_exceeded"
                         }
                    elif resp.status == 400:
                         # Try to detect decommissioned model and auto-fallback
                         data = await resp.json()
                         message = str(data)
                         if "model_decommissioned" in message or "decommissioned" in message:
                             fallback_chain = [
                                 "llama-3.3-70b-versatile",
                                 "llama-3.1-8b-instant"
                             ]
                             for fb in fallback_chain:
                                 payload["model"] = fb
                                 try:
                                     async with session.post(url, json=payload, headers=headers) as resp2:
                                         if resp2.status == 200:
                                             data2 = await resp2.json()
                                             result_text2 = data2['choices'][0]['message']['content']
                                             self.settings_manager.set("ai", "groq_model", fb)
                                             return {"text": result_text2.strip(), "emotion": "neutral"}
                                 except Exception:
                                     pass
                         error_text = await resp.text()
                         self.logger.error(f"Groq API Error 400: {error_text}")
                         return None
                    else:
                        error_text = await resp.text()
                        self.logger.error(f"Groq API Error {resp.status}: {error_text}")
                        return None
        except Exception as e:
            self.logger.error(f"Groq Network Error: {e}")
            return None

    async def _process_claude(self, text, system_prompt="", history=None):
        """Sends user query to Anthropic Claude API"""
        url = "https://api.anthropic.com/v1/messages"
        headers = {
            "x-api-key": self.api_key,
            "anthropic-version": "2023-06-01",
            "content-type": "application/json"
        }
        
        messages = []
        
        if history:
            for msg in history:
                messages.append({
                    "role": msg["role"],
                    "content": msg["content"]
                })
        else:
             messages.append({"role": "user", "content": text})
             
        payload = {
            "model": self.model_name,
            "max_tokens": 1024,
            "messages": messages,
            "system": system_prompt
        }
        
        try:
             async with aiohttp.ClientSession() as session:
                async with session.post(url, json=payload, headers=headers) as resp:
                    if resp.status == 200:
                        data = await resp.json()
                        result_text = data['content'][0]['text']
                        return {"text": result_text.strip(), "emotion": "neutral"}
                    else:
                        error_text = await resp.text()
                        self.logger.error(f"Claude API Error {resp.status}: {error_text}")
                        return None
        except Exception as e:
            self.logger.error(f"Claude Network Error: {e}")
            return None
