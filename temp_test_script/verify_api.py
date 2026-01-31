import asyncio
import aiohttp
import json

import sys
import os

# Add project root to path to import core modules
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from core.settings.settings_manager import SettingsManager

# Load settings
settings_manager = SettingsManager()
API_KEY = settings_manager.get("ai", "gemini_api_key", "")
MODEL_NAME = settings_manager.get("ai", "gemini_model", "gemini-2.5-flash")

async def test_gemini():
    print(f"Testing Gemini API with Key: {API_KEY[:5]}...{API_KEY[-4:]}")
    # Note: Model name in URL usually doesn't need 'models/' prefix if we just use the ID, 
    # but the list returned 'models/gemini-2.5-flash'. 
    # The API usually accepts 'gemini-2.5-flash' or 'models/gemini-2.5-flash'.
    url = f"https://generativelanguage.googleapis.com/v1beta/models/{MODEL_NAME}:generateContent?key={API_KEY}"
    
    payload = {
        "contents": [{
            "parts": [{"text": "Hello, are you working?"}]
        }]
    }
    
    try:
        async with aiohttp.ClientSession() as session:
            async with session.post(url, json=payload) as resp:
                print(f"Status Code: {resp.status}")
                if resp.status == 200:
                    data = await resp.json()
                    print("Response Data:", json.dumps(data, indent=2))
                    try:
                        text = data['candidates'][0]['content']['parts'][0]['text']
                        print(f"\nSUCCESS! AI Reply: {text}")
                    except KeyError:
                        print("Failed to parse response structure.")
                else:
                    error_text = await resp.text()
                    print(f"API Error: {error_text}")
    except Exception as e:
        print(f"Exception: {e}")

if __name__ == "__main__":
    asyncio.run(test_gemini())
