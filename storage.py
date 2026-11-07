import json
import os
import tempfile
import threading
from pathlib import Path


class EventStore:
    def __init__(self, path):
        self.path = Path(path)
        self._lock = threading.Lock()

    def load(self):
        with self._lock:
            return self._read()

    def update(self, change):
        with self._lock:
            events = self._read()
            result = change(events)
            self._write(events)
            return result

    def _read(self):
        if not self.path.exists():
            return []
        with self.path.open(encoding="utf-8") as f:
            return json.load(f)

    def _write(self, events):
        self.path.parent.mkdir(parents=True, exist_ok=True)
        fd, tmp_path = tempfile.mkstemp(dir=self.path.parent, prefix=".events-", suffix=".tmp")
        with os.fdopen(fd, "w", encoding="utf-8") as f:
            json.dump(events, f, indent=2, ensure_ascii=False)
            f.write("\n")
            f.flush()
            os.fsync(f.fileno())
        os.replace(tmp_path, self.path)
