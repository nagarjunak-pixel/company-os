import json
import os
import time
from typing import Dict, List, Any, Optional

class Store:
    """Manages file-backed JSON data storage and event logging for CompanyOS."""

    def __init__(self, data_dir: str = "data"):
        self.data_dir = data_dir
        self.ensure_data_dir()

    def ensure_data_dir(self) -> None:
        if not os.path.exists(self.data_dir):
            os.makedirs(self.data_dir, exist_ok=True)

    def _get_path(self, filename: str) -> str:
        return os.path.join(self.data_dir, filename)

    def load_json(self, filename: str, default: Any = None) -> Any:
        path = self._get_path(filename)
        if not os.path.exists(path):
            return default if default is not None else {}
        try:
            with open(path, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception:
            return default if default is not None else {}

    def save_json(self, filename: str, data: Any) -> None:
        self.ensure_data_dir()
        path = self._get_path(filename)
        with open(path, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2)

    def append_event(self, event_type: str, details: Dict[str, Any], agent: Optional[str] = None) -> Dict[str, Any]:
        self.ensure_data_dir()
        path = self._get_path("events.jsonl")
        
        # Calculate auto-incrementing ID
        events = self.get_events(after_id=0)
        next_id = events[-1]["id"] + 1 if events else 1

        event = {
            "id": next_id,
            "timestamp": time.strftime("%Y-%m-%d %H:%M:%S"),
            "epoch": time.time(),
            "type": event_type,
            "agent": agent or "System",
            "details": details
        }

        with open(path, "a", encoding="utf-8") as f:
            f.write(json.dumps(event) + "\n")

        return event

    def get_events(self, after_id: int = 0) -> List[Dict[str, Any]]:
        path = self._get_path("events.jsonl")
        if not os.path.exists(path):
            return []
        
        events = []
        try:
            with open(path, "r", encoding="utf-8") as f:
                for line in f:
                    line = line.strip()
                    if line:
                        try:
                            ev = json.loads(line)
                            if ev.get("id", 0) > after_id:
                                events.append(ev)
                        except Exception:
                            continue
        except Exception:
            pass
        return events
