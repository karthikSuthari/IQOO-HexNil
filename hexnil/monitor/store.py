"""Monitoring session persistence layer."""

import json
import logging
from pathlib import Path
from typing import List, Optional

from hexnil.monitor.models import (
    MonitoringSample,
    MonitoringSession,
)

logger = logging.getLogger("hexnil.monitor.store")


class MonitoringStore:
    """Persists and retrieves monitoring sessions and streaming samples."""

    def __init__(self, base_dir: Path):
        self.base_dir = base_dir
        self.base_dir.mkdir(parents=True, exist_ok=True)

    def _session_dir(self, session_id: str) -> Path:
        d = self.base_dir / session_id
        d.mkdir(parents=True, exist_ok=True)
        return d

    def save_session(self, session: MonitoringSession) -> Path:
        """Persist a monitoring session record."""
        d = self._session_dir(session.session_id)
        path = d / "session.json"
        path.write_text(session.model_dump_json(indent=2), encoding="utf-8")
        logger.debug("Saved session %s to %s", session.session_id, path)
        return path

    def load_session(self, session_id: str) -> MonitoringSession:
        """Load a monitoring session record."""
        path = self._session_dir(session_id) / "session.json"
        if not path.exists():
            raise FileNotFoundError(f"Session '{session_id}' not found at {path}")
        data = json.loads(path.read_text(encoding="utf-8"))
        return MonitoringSession(**data)

    def list_sessions(self) -> List[MonitoringSession]:
        """List all persisted monitoring sessions."""
        sessions: List[MonitoringSession] = []
        if not self.base_dir.exists():
            return sessions
        for child in sorted(self.base_dir.iterdir()):
            if child.is_dir():
                session_file = child / "session.json"
                if session_file.exists():
                    try:
                        data = json.loads(session_file.read_text(encoding="utf-8"))
                        sessions.append(MonitoringSession(**data))
                    except Exception as exc:
                        logger.warning("Failed to load session from %s: %s", child, exc)
        return sessions

    def append_sample(self, session_id: str, sample: MonitoringSample) -> None:
        """Append a single monitoring sample to the streaming JSONL file."""
        d = self._session_dir(session_id)
        samples_path = d / "samples.jsonl"
        with open(samples_path, "a", encoding="utf-8") as f:
            f.write(sample.model_dump_json() + "\n")

    def load_samples(self, session_id: str) -> List[MonitoringSample]:
        """Load all monitoring samples for a session."""
        d = self._session_dir(session_id)
        samples_path = d / "samples.jsonl"
        if not samples_path.exists():
            return []

        samples: List[MonitoringSample] = []
        for line in samples_path.read_text(encoding="utf-8").splitlines():
            line = line.strip()
            if line:
                try:
                    data = json.loads(line)
                    samples.append(MonitoringSample(**data))
                except Exception as exc:
                    logger.warning("Failed to parse sample line: %s", exc)
        return samples

    def save_artifact(self, session_id: str, name: str, content: str) -> Path:
        """Save an arbitrary artifact JSON file to the session directory."""
        d = self._session_dir(session_id)
        path = d / name
        path.write_text(content, encoding="utf-8")
        return path

    def generate_session_id(self) -> str:
        """Generate a unique monotonic session ID."""
        existing = []
        if self.base_dir.exists():
            for child in self.base_dir.iterdir():
                if child.is_dir() and child.name.startswith("MON-"):
                    try:
                        seq = int(child.name.split("-")[1])
                        existing.append(seq)
                    except (IndexError, ValueError):
                        pass

        next_seq = max(existing, default=0) + 1
        return f"MON-{next_seq:04d}"
