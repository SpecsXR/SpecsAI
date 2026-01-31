import json
import os
import threading
from typing import List, Dict, Any

class MemoryService:
    def __init__(self, storage_file="user_memory.json"):
        self.storage_file = storage_file
        self.memory_lock = threading.Lock()
        self.data = self._load_memory()

    def _load_memory(self) -> Dict[str, Any]:
        """Loads memory from JSON file"""
        if os.path.exists(self.storage_file):
            try:
                with open(self.storage_file, "r", encoding="utf-8") as f:
                    return json.load(f)
            except Exception as e:
                print(f"[Memory] Error loading memory: {e}")
        
        # Default Structure
        return {
            "user_profile": {
                "name": None,
                "preferences": {},
                "facts": []
            },
            "conversation_summary": [], # Summaries of past topics
            "important_notes": [] # Specific things user asked to remember
        }

    def _save_memory(self):
        """Saves memory to JSON file"""
        with self.memory_lock:
            try:
                with open(self.storage_file, "w", encoding="utf-8") as f:
                    json.dump(self.data, f, ensure_ascii=False, indent=2)
            except Exception as e:
                print(f"[Memory] Error saving memory: {e}")

    def get_context_string(self) -> str:
        """Returns a formatted string of long-term memories for the LLM system prompt"""
        profile = self.data["user_profile"]
        facts = profile.get("facts", [])
        notes = self.data.get("important_notes", [])
        
        context = []
        if profile.get("name"):
            context.append(f"User's Name: {profile['name']}")
        
        if facts:
            context.append("Key Facts about User:\n- " + "\n- ".join(facts))
            
        if notes:
            context.append("Important Notes:\n- " + "\n- ".join(notes))
            
        return "\n".join(context)

    def add_fact(self, fact: str):
        """Adds a fact to the user profile"""
        if fact not in self.data["user_profile"]["facts"]:
            self.data["user_profile"]["facts"].append(fact)
            self._save_memory()
            print(f"[Memory] Added fact: {fact}")

    def set_user_name(self, name: str):
        """Sets the user's name"""
        self.data["user_profile"]["name"] = name
        self._save_memory()
        print(f"[Memory] Set user name: {name}")

    def add_note(self, note: str):
        """Adds an important note"""
        if note not in self.data["important_notes"]:
            self.data["important_notes"].append(note)
            self._save_memory()
            print(f"[Memory] Added note: {note}")

    def extract_and_update(self, user_input: str, ai_response: str):
        """
        Analyzes conversation to extract facts. 
        (This is a simple rule-based version, can be upgraded to LLM-based)
        """
        lower_input = user_input.lower()
        
        # 1. Name Extraction
        if "my name is" in lower_input:
            parts = lower_input.split("my name is")
            if len(parts) > 1:
                name = parts[1].strip().split(".")[0].title()
                self.set_user_name(name)
        elif "amar naam" in lower_input:
             parts = lower_input.split("amar naam")
             if len(parts) > 1:
                name = parts[1].strip().split(".")[0].title()
                self.set_user_name(name)

        # 2. Explicit "Remember" Command
        if "remember that" in lower_input:
            parts = lower_input.split("remember that")
            if len(parts) > 1:
                note = parts[1].strip()
                self.add_note(note)
        elif "mone rakhba je" in lower_input:
            parts = lower_input.split("mone rakhba je")
            if len(parts) > 1:
                note = parts[1].strip()
                self.add_note(note)

        # 3. Location (Simple)
        if "i live in" in lower_input:
            parts = lower_input.split("i live in")
            if len(parts) > 1:
                location = parts[1].strip().split(".")[0].title()
                self.add_fact(f"Lives in {location}")
