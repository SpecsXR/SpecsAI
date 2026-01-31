import json
import os
import datetime
import threading
from typing import List, Dict, Any

class HistoryService:
    """
    Manages recording of system activities, chats, and errors.
    """
    _instance = None

    def __new__(cls, *args, **kwargs):
        if not cls._instance:
            cls._instance = super(HistoryService, cls).__new__(cls)
        return cls._instance

    def __init__(self, log_file="activity_log.json"):
        if hasattr(self, 'initialized'):
            return
        self.log_file = log_file
        self.lock = threading.Lock()
        self.initialized = True
        self._ensure_file()

    def _ensure_file(self):
        if not os.path.exists(self.log_file):
            with open(self.log_file, "w", encoding="utf-8") as f:
                json.dump([], f)

    def log_event(self, category: str, detail: str, source: str = "System"):
        """
        Logs a general event.
        Categories: 'System', 'Error', 'Warning', 'Info'
        """
        self._add_entry({
            "timestamp": datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "type": "event",
            "category": category,
            "source": source,
            "detail": detail
        })

    def log_chat(self, sender: str, message: str):
        """
        Logs a chat message.
        """
        self._add_entry({
            "timestamp": datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "type": "chat",
            "sender": sender,
            "message": message
        })

    def _add_entry(self, entry: Dict[str, Any]):
        """Thread-safe append to log file"""
        threading.Thread(target=self._write_worker, args=(entry,), daemon=True).start()

    def _write_worker(self, entry):
        with self.lock:
            try:
                data = []
                if os.path.exists(self.log_file):
                    # Read existing (could be large, optimization needed for production but fine for now)
                    # For very large logs, we should append line by line or use SQLite.
                    # Using simple JSON list for simplicity as per current project scale.
                    try:
                        with open(self.log_file, "r", encoding="utf-8") as f:
                            data = json.load(f)
                    except json.JSONDecodeError:
                        data = []
                
                data.append(entry)
                
                # Limit log size (keep last 1000 entries)
                if len(data) > 1000:
                    data = data[-1000:]
                
                with open(self.log_file, "w", encoding="utf-8") as f:
                    json.dump(data, f, ensure_ascii=False, indent=2)
            except Exception as e:
                print(f"Failed to write history: {e}")

    def get_history(self, limit=100, filter_type=None) -> List[Dict[str, Any]]:
        """Returns recent history"""
        try:
            if not os.path.exists(self.log_file):
                return []
            
            with open(self.log_file, "r", encoding="utf-8") as f:
                data = json.load(f)
                
            if filter_type:
                data = [d for d in data if d.get("type") == filter_type]
                
            return data[-limit:][::-1] # Newest first
        except Exception:
            return []

    def clear_history(self):
        with self.lock:
            with open(self.log_file, "w", encoding="utf-8") as f:
                json.dump([], f)
