"""Tests for Phase 9: Monitoring Store."""

import json
import pytest
from pathlib import Path

from hexnil.monitor.models import MonitoringPhase, MonitoringSample, MonitoringSession
from hexnil.monitor.store import MonitoringStore


class TestMonitoringStore:
    def setup_method(self, tmp_path=None):
        pass

    @pytest.fixture(autouse=True)
    def _setup_store(self, tmp_path):
        self.store = MonitoringStore(tmp_path / "sessions")
        self.tmp_path = tmp_path

    def _make_session(self, session_id="MON-0001"):
        return MonitoringSession(
            session_id=session_id,
            device_serial="ABC123",
            device_model="iQOO Neo9 Pro",
            created_at="2026-01-01T00:00:00Z",
        )

    def test_save_and_load_session(self):
        session = self._make_session()
        self.store.save_session(session)
        loaded = self.store.load_session("MON-0001")
        assert loaded.session_id == "MON-0001"
        assert loaded.device_serial == "ABC123"
        assert loaded.phase == MonitoringPhase.INITIALIZING

    def test_load_nonexistent_session(self):
        with pytest.raises(FileNotFoundError):
            self.store.load_session("MON-9999")

    def test_list_sessions_empty(self):
        sessions = self.store.list_sessions()
        assert len(sessions) == 0

    def test_list_sessions_multiple(self):
        self.store.save_session(self._make_session("MON-0001"))
        self.store.save_session(self._make_session("MON-0002"))
        sessions = self.store.list_sessions()
        assert len(sessions) == 2
        ids = {s.session_id for s in sessions}
        assert ids == {"MON-0001", "MON-0002"}

    def test_append_and_load_samples(self):
        sample1 = MonitoringSample(
            session_id="MON-0001", sample_index=0,
            timestamp="2026-01-01T00:00:00Z",
            battery_level_percent=90.0,
        )
        sample2 = MonitoringSample(
            session_id="MON-0001", sample_index=1,
            timestamp="2026-01-01T00:01:00Z",
            battery_level_percent=89.5,
        )
        self.store.append_sample("MON-0001", sample1)
        self.store.append_sample("MON-0001", sample2)
        samples = self.store.load_samples("MON-0001")
        assert len(samples) == 2
        assert samples[0].battery_level_percent == 90.0
        assert samples[1].battery_level_percent == 89.5

    def test_load_samples_empty(self):
        samples = self.store.load_samples("MON-9999")
        assert len(samples) == 0

    def test_save_artifact(self):
        path = self.store.save_artifact("MON-0001", "report.json", '{"test": true}')
        assert path.exists()
        assert json.loads(path.read_text(encoding="utf-8")) == {"test": True}

    def test_generate_session_id_first(self):
        sid = self.store.generate_session_id()
        assert sid == "MON-0001"

    def test_generate_session_id_sequential(self):
        self.store.save_session(self._make_session("MON-0001"))
        self.store.save_session(self._make_session("MON-0002"))
        sid = self.store.generate_session_id()
        assert sid == "MON-0003"

    def test_session_round_trip_preserves_phase(self):
        session = self._make_session()
        session.phase = MonitoringPhase.AWAITING_UPDATE
        session.status = "waiting"
        self.store.save_session(session)
        loaded = self.store.load_session("MON-0001")
        assert loaded.phase == MonitoringPhase.AWAITING_UPDATE
        assert loaded.status == "waiting"
