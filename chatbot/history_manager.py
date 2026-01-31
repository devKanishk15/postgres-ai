import json
import os
import time
from typing import List, Dict, Any, Optional

class HistoryManager:
    """Manages conversation history with basic persistence."""
    
    def __init__(self, storage_dir: str = "conversations", max_history: int = 20):
        self.storage_dir = storage_dir
        self.max_history = max_history
        self._ensure_storage()
        self.in_memory_cache: Dict[str, List[Dict[str, Any]]] = {}

    def _ensure_storage(self):
        if not os.path.exists(self.storage_dir):
            os.makedirs(self.storage_dir)

    def _get_file_path(self, conversation_id: str) -> str:
        return os.path.join(self.storage_dir, f"{conversation_id}.json")

    def get_history(self, conversation_id: str) -> List[Dict[str, Any]]:
        # Check cache
        if conversation_id in self.in_memory_cache:
            return self.in_memory_cache[conversation_id]
        
        # Check disk
        file_path = self._get_file_path(conversation_id)
        if os.path.exists(file_path):
            try:
                with open(file_path, 'r') as f:
                    history = json.load(f)
                    self.in_memory_cache[conversation_id] = history
                    return history
            except Exception:
                return []
        
        return []

    def save_history(self, conversation_id: str, history: List[Dict[str, Any]]):
        # Trim history if needed (excluding system prompt)
        if len(history) > self.max_history + 1:
            system_prompt = history[0] if history and history[0].get("role") == "system" else None
            remaining = history[-(self.max_history):]
            if system_prompt and remaining[0] != system_prompt:
                history = [system_prompt] + remaining
            else:
                history = remaining

        # Update cache
        self.in_memory_cache[conversation_id] = history
        
        # Save to disk
        file_path = self._get_file_path(conversation_id)
        try:
            with open(file_path, 'w') as f:
                json.dump(history, f, indent=2)
        except Exception as e:
            print(f"Error saving history: {e}")

    def clear_history(self, conversation_id: str):
        self.in_memory_cache.pop(conversation_id, None)
        file_path = self._get_file_path(conversation_id)
        if os.path.exists(file_path):
            os.remove(file_path)
