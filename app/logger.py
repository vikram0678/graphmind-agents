import json
import logging
import os
from datetime import datetime, timezone
from pathlib import Path


class JSONLogger:
    """Writes structured JSON logs to logs/agent_activity.log"""

    def __init__(self):
        log_dir = Path("/app/logs")
        log_dir.mkdir(parents=True, exist_ok=True)
        self.log_file = log_dir / "agent_activity.log"

    def _write(self, level: str, data: dict):
        if isinstance(data, str):
            data = {"message": data}
        data["level"] = level
        if "timestamp" not in data:
            data["timestamp"] = datetime.now(timezone.utc).isoformat()
        with open(self.log_file, "a") as f:
            f.write(json.dumps(data) + "\n")

    def info(self, data):
        self._write("INFO", data)

    def warning(self, data):
        self._write("WARNING", data)

    def error(self, data):
        self._write("ERROR", data)


_logger_instance = None


def get_logger() -> JSONLogger:
    global _logger_instance
    if _logger_instance is None:
        _logger_instance = JSONLogger()
    return _logger_instance