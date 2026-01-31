"""
SpecsAI Memory System
Manages Long-term Memory and Context.
"""
import json
import os

class SpecsMemory:
    def __init__(self, storage_path="specs_memory.json"):
        self.storage_path = storage_path
        self.memory = self._load_memory()

    def _load_memory(self):
        if os.path.exists(self.storage_path):
            try:
                with open(self.storage_path, "r", encoding="utf-8") as f:
                    return json.load(f)
            except:
                return {}
        return {}

    def save_memory(self):
        try:
            with open(self.storage_path, "w", encoding="utf-8") as f:
                json.dump(self.memory, f, ensure_ascii=False, indent=2)
        except Exception as e:
            print(f"Memory Save Error: {e}")

    def get_context_string(self):
        """Returns a formatted string of key memories"""
        if not self.memory:
            return ""
        
        context = []
        # User Info
        if "user_name" in self.memory:
            context.append(f"- User Name: {self.memory['user_name']}")
        
        # Facts
        if "facts" in self.memory:
            for fact in self.memory["facts"]:
                context.append(f"- {fact}")
                
        return "\n".join(context)

    def update(self, key, value):
        self.memory[key] = value
        self.save_memory()
        
    def add_fact(self, fact):
        if "facts" not in self.memory:
            self.memory["facts"] = []
        if fact not in self.memory["facts"]:
            self.memory["facts"].append(fact)
            self.save_memory()
