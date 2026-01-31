"""
SpecsAI Provider Manager
Handles connections to external brains (Groq, Gemini, Claude, Ollama)
"""
import aiohttp
import asyncio
import logging
import os
import base64
import io
import json
try:
    from groq import AsyncGroq
except ImportError:
    AsyncGroq = None

try:
    import google.generativeai as genai
except ImportError:
    genai = None

class AIProvider:
    def __init__(self, api_keys=None):
        self.api_keys = api_keys or {}
        self.logger = logging.getLogger("SpecsAI.Provider")
        
        # Initialize Persistent Clients
        self.groq_client = None
        if self.api_keys.get("groq") and AsyncGroq:
            self.groq_client = AsyncGroq(api_key=self.api_keys.get("groq"))
            
        if self.api_keys.get("gemini") and genai:
             genai.configure(api_key=self.api_keys.get("gemini"))
             # Default to 2.5-flash if available, otherwise 1.5-flash
             self.gemini_model = genai.GenerativeModel('gemini-2.5-flash')
        else:
             self.gemini_model = None

    async def process_query(self, text, system_prompt, history=None, provider="auto", image_data=None):
        """
        Auto-mode: Prioritizes Groq (Fastest) -> Gemini (Free/Reliable) -> Claude -> Local
        provider: 'auto', 'gemini', 'groq', 'claude', 'ollama', 'openai'
        image_data: Optional PIL Image or bytes for vision tasks.
        """
        provider = provider.lower()
        
        # --- Vision Handling (Force Gemini/Claude) ---
        if image_data:
            # Groq doesn't support vision yet (Llama 3). Fallback to Gemini.
            if self.gemini_model:
                # _query_gemini handles retries and returns a dict result
                return await self._query_gemini(text, system_prompt, history, image_data)
            return {"error": "Vision requires Gemini API Key."}
        
        # --- Specific Provider Requests ---
        if provider == "groq":
            if self.groq_client:
                try:
                    response = await self._query_groq(text, system_prompt, history)
                    return {"text": response, "source": "Groq"}
                except Exception as e:
                    return {"error": f"Groq Error: {e}"}
            return {"error": "Groq API Key missing."}
            
        if provider == "gemini":
            if self.gemini_model:
                try:
                    response = await self._query_gemini(text, system_prompt, history)
                    return {"text": response, "source": "Google Gemini"}
                except Exception as e:
                    return {"error": f"Gemini Error: {e}"}
            return {"error": "Gemini API Key missing."}

        if provider == "sambanova":
            try:
                response = await self._query_sambanova(text, system_prompt, history)
                return {"text": response, "source": "Sambanova"}
            except Exception as e:
                return {"error": f"Sambanova Error: {e}"}

        if provider == "huggingface":
            try:
                response = await self._query_huggingface(text, system_prompt, history)
                return {"text": response, "source": "Hugging Face"}
            except Exception as e:
                return {"error": f"Hugging Face Error: {e}"}

        # --- Auto / SpecsAI Logic (Default) ---
        if provider in ["auto", "specsai"]:
            # 1. Groq (Llama 3 70B - Super Fast)
            if self.groq_client:
                try:
                    # self.logger.info("Thinking with SpecsAI Brain (Groq Core)...")
                    response = await self._query_groq(text, system_prompt, history)
                    if response:
                         return {"text": response, "source": "SpecsAI (Fast Core)"}
                except Exception as e:
                    self.logger.warning(f"Groq Core failed: {e}")

            # 2. Sambanova (Llama 3.1 70B - Fast & Free)
            if self.api_keys.get("sambanova"):
                try:
                    response = await self._query_sambanova(text, system_prompt, history)
                    if response:
                        return {"text": response, "source": "SpecsAI (Sambanova Core)"}
                except Exception as e:
                    self.logger.warning(f"Sambanova Core failed: {e}")

            # 3. Gemini (Flash 2.5 - Reliable)
            if self.gemini_model:
                try:
                    # self.logger.info("Thinking with SpecsAI Brain (Gemini Core)...")
                    response = await self._query_gemini(text, system_prompt, history)
                    if response:
                        return {"text": response, "source": "SpecsAI (Smart Core)"}
                except Exception as e:
                    self.logger.warning(f"Gemini Core failed: {e}")

            # 4. Hugging Face (Free Inference - Backup)
            if self.api_keys.get("huggingface"):
                try:
                    response = await self._query_huggingface(text, system_prompt, history)
                    if response:
                        return {"text": response, "source": "SpecsAI (HF Core)"}
                except Exception as e:
                    self.logger.warning(f"Hugging Face Core failed: {e}")

            return {"error": "No active brain connection available for Auto Mode."}

        return {"error": f"Provider '{provider}' is not supported yet."}

    async def _query_groq(self, text, system_prompt, history):
        # Create client inside the async context to bind to the current event loop
        # This prevents "Event loop is closed" or "Future attached to a different loop" errors
        async with AsyncGroq(api_key=self.api_keys.get("groq")) as client:
            messages = [{"role": "system", "content": system_prompt}]
            
            # Add history
            if history:
                for msg in history:
                    role = "user" if msg['role'] == "user" else "assistant"
                    messages.append({"role": role, "content": msg['content']})
                    
            messages.append({"role": "user", "content": text})
            
            completion = await client.chat.completions.create(
                model="llama-3.3-70b-versatile",
                messages=messages,
                temperature=0.7,
                max_tokens=1024,
                top_p=1,
                stream=False,
                stop=None,
            )
            return completion.choices[0].message.content

    async def _query_gemini(self, text, system_prompt, history, image_data=None):
        # Configure system prompt dynamically
        # Note: Initial model creation is handled inside the try block below for text,
        # or we use the fallback logic for vision.
        
        if image_data:
            # Vision Request: Single turn usually
            # High-Tech Retry Logic for Model Versions
            # We prioritize REST API for Vision to avoid gRPC/Async loop conflicts in threaded contexts
            
            last_error = None
            
            # 1. Advanced Fallback: Direct REST API (Primary for Stability)
            try:
                # self.logger.info("Vision: Trying Direct REST API...")
                rest_response = await self._query_gemini_rest(text, image_data, self.api_keys.get("gemini"), system_prompt=system_prompt)
                if rest_response:
                    return {"text": rest_response, "source": "SpecsAI Vision (Direct Link)"}
            except Exception as e:
                last_error = f"REST Error: {e}"
            
            # 2. SDK Fallback (Only if REST fails)
            models_to_try = ['gemini-2.5-flash', 'gemini-1.5-flash', 'gemini-1.5-flash-8b', 'gemini-1.5-pro']
            for model_name in models_to_try:
                try:
                    # self.logger.info(f"Vision: Trying SDK {model_name}...")
                    vision_model = genai.GenerativeModel(model_name)
                    response = await vision_model.generate_content_async([text, image_data])
                    return {"text": response.text, "source": f"SpecsAI Vision ({model_name})"}
                except Exception as e:
                    last_error = f"{last_error} | SDK {model_name}: {e}"
                    # Continue to next model

            # If all failed, log it securely but return a polite message
            self.logger.error(f"Vision Analysis Failed after retries. Last error: {last_error}")
            return {"error": "I'm having trouble seeing the screen right now. My vision sensors are recalibrating. Please try again in a moment."}
            
        # --- Standard Text Chat ---
        # Switch to REST API as PRIMARY for text as well.
        # This avoids 'InterceptedUnaryUnaryCall' gRPC errors in threaded/async environments (PySide6).
        try:
            return await self._query_gemini_rest(text, None, self.api_keys.get("gemini"), history=history, system_prompt=system_prompt)
        except Exception as rest_error:
            # Fallback to SDK if REST fails (unlikely, but safe)
            try:
                chat_history = []
                if history:
                    for msg in history:
                        role = "user" if msg['role'] == "user" else "model"
                        chat_history.append({"role": role, "parts": [msg['content']]})
                
                # Re-initialize model with system prompt if needed
                try:
                     model = genai.GenerativeModel('gemini-2.5-flash', system_instruction=system_prompt)
                except:
                     model = genai.GenerativeModel('gemini-2.5-flash')

                chat = model.start_chat(history=chat_history)
                response = await chat.send_message_async(text)
                return response.text
            except Exception as sdk_error:
                raise ValueError(f"Gemini Failed (REST: {rest_error}) (SDK: {sdk_error})")

    async def _query_gemini_rest(self, text, image_data, api_key, history=None, system_prompt=None):
        """
        Advanced Fallback: Direct REST API call to Gemini
        Bypasses python-google-generativeai SDK if it's outdated or buggy.
        Supports both Text and Vision.
        """
        if not api_key:
            raise ValueError("No Gemini API Key provided for REST call")

        # List of models to try (Updated with 2.5-flash)
        models = ["gemini-2.5-flash", "gemini-1.5-flash", "gemini-1.5-flash-8b", "gemini-1.5-pro"]
        
        last_error = None
        
        async with aiohttp.ClientSession() as session:
            for model_name in models:
                try:
                    url = f"https://generativelanguage.googleapis.com/v1beta/models/{model_name}:generateContent?key={api_key}"
                    
                    headers = {'Content-Type': 'application/json'}
                    
                    # Construct Payload
                    contents = []
                    
                    # Add System Prompt (if supported by model via system_instruction, but for REST simple chat, 
                    # we often prepend it to the first message or use 'system_instruction' field)
                    # For v1beta, 'systemInstruction' is a separate field.
                    payload = {}
                    
                    if system_prompt:
                         payload["systemInstruction"] = {
                             "parts": [{"text": system_prompt}]
                         }

                    # Add History
                    if history:
                        for msg in history:
                            role = "user" if msg['role'] == "user" else "model"
                            contents.append({
                                "role": role,
                                "parts": [{"text": msg['content']}]
                            })
                            
                    # Add Current Message
                    current_parts = [{"text": text}]
                    if image_data:
                        # Convert PIL Image to Base64
                        img_byte_arr = io.BytesIO()
                        image_data.save(img_byte_arr, format='JPEG')
                        img_byte_arr = img_byte_arr.getvalue()
                        base64_image = base64.b64encode(img_byte_arr).decode('utf-8')
                        
                        current_parts.append({
                            "inline_data": {
                                "mime_type": "image/jpeg",
                                "data": base64_image
                            }
                        })
                        
                    contents.append({
                        "role": "user",
                        "parts": current_parts
                    })
                    
                    payload["contents"] = contents

                    async with session.post(url, headers=headers, json=payload) as response:
                        if response.status == 200:
                            result = await response.json()
                            # Extract text from response structure
                            try:
                                return result['candidates'][0]['content']['parts'][0]['text']
                            except (KeyError, IndexError):
                                 raise ValueError(f"Unexpected API Response structure: {result}")
                        else:
                            error_text = await response.text()
                            # If 404 (Model not found) or 500, try next model
                            if response.status in [404, 500, 503, 429]: # 429 is rate limit, try next model too
                                last_error = f"{model_name} {response.status}: {error_text}"
                                continue
                            else:
                                raise ValueError(f"REST API Error {response.status}: {error_text}")
                                
                except Exception as e:
                    last_error = e
                    continue
        
        # If we get here, all models failed
        raise ValueError(f"All REST models failed. Last error: {last_error}")

    async def _query_sambanova(self, text, system_prompt, history):
        """
        Sambanova Cloud (Fast Llama 3.1 70B)
        OpenAI-compatible API
        """
        api_key = self.api_keys.get("sambanova")
        if not api_key:
            raise ValueError("Sambanova API Key missing")
            
        url = "https://api.sambanova.ai/v1/chat/completions"
        headers = {
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json"
        }
        
        messages = [{"role": "system", "content": system_prompt}]
        if history:
            for msg in history:
                role = "user" if msg['role'] == "user" else "assistant"
                messages.append({"role": role, "content": msg['content']})
        messages.append({"role": "user", "content": text})
        
        payload = {
            "model": "Meta-Llama-3.1-70B-Instruct",
            "messages": messages,
            "temperature": 0.7,
            "max_tokens": 1024
        }
        
        async with aiohttp.ClientSession() as session:
            async with session.post(url, headers=headers, json=payload) as response:
                if response.status == 200:
                    data = await response.json()
                    return data['choices'][0]['message']['content']
                else:
                    error_text = await response.text()
                    raise ValueError(f"Sambanova Error {response.status}: {error_text}")

    async def _query_huggingface(self, text, system_prompt, history):
        """
        Hugging Face Inference API (Free Tier)
        """
        api_key = self.api_keys.get("huggingface")
        if not api_key:
            raise ValueError("Hugging Face API Key missing")
            
        # Default model or user selected? For now hardcode or get from somewhere. 
        # We'll use the one from settings passed via Config usually, but here we just use a sensible default if not passed.
        # Ideally we should pass the model name in arguments, but for now we hardcode the default from settings_manager logic
        model = "meta-llama/Meta-Llama-3-8B-Instruct" 
        
        url = f"https://api-inference.huggingface.co/models/{model}"
        headers = {"Authorization": f"Bearer {api_key}"}
        
        # Simple prompt formatting for Llama 3
        full_prompt = f"<|begin_of_text|><|start_header_id|>system<|end_header_id|>\n\n{system_prompt}<|eot_id|>"
        
        if history:
            for msg in history:
                role = "user" if msg['role'] == "user" else "assistant"
                full_prompt += f"<|start_header_id|>{role}<|end_header_id|>\n\n{msg['content']}<|eot_id|>"
                
        full_prompt += f"<|start_header_id|>user<|end_header_id|>\n\n{text}<|eot_id|><|start_header_id|>assistant<|end_header_id|>\n\n"
        
        payload = {
            "inputs": full_prompt,
            "parameters": {
                "max_new_tokens": 1024,
                "return_full_text": False,
                "temperature": 0.7
            }
        }
        
        async with aiohttp.ClientSession() as session:
            async with session.post(url, headers=headers, json=payload) as response:
                if response.status == 200:
                    data = await response.json()
                    if isinstance(data, list) and len(data) > 0:
                        return data[0]['generated_text']
                    elif isinstance(data, dict) and 'generated_text' in data:
                        return data['generated_text']
                    else:
                        return str(data)
                else:
                    error_text = await response.text()
                    # Check for loading error (common in free tier)
                    if "loading" in error_text.lower():
                         raise ValueError("Model is loading (Cold Boot). Try again in 20s.")
                    raise ValueError(f"Hugging Face Error {response.status}: {error_text}")

