"""Supabase Fleet Client for Hexnil Multi-Device Cloud Sync."""

import logging
import os
import socket
from typing import Any, Dict, List, Optional
import requests
import urllib3.util.connection as urllib3_cn

# Force IPv4 resolution on Windows to avoid ISP IPv6 blackhole timeouts
urllib3_cn.allowed_gai_family = lambda: socket.AF_INET

logger = logging.getLogger("hexnil.cloud.client")

DEFAULT_SUPABASE_URL = "https://takhdmtsdbrqucrolzfh.supabase.co"
DEFAULT_ANON_KEY = (
    "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9."
    "eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6InRha2hkbXRzZGJycXVjcm9semZoIiwicm9sZSI6ImFub24iLCJpYXQiOjE3ODkzNTI3MzYsImV4cCI6MjEwNDkyODczNn0."
    "JJLm6HMQZhciXq69rZYw5JGQ91d5Rhi9v-AT3qWOPL4"
)


class SupabaseFleetClient:
    """Client for communicating with Supabase PostgreSQL via PostgREST API."""

    def __init__(
        self,
        supabase_url: Optional[str] = None,
        supabase_key: Optional[str] = None,
        timeout_seconds: float = 15.0,
    ):
        self.url = (supabase_url or os.environ.get("HEXNIL_SUPABASE_URL") or DEFAULT_SUPABASE_URL).rstrip("/")
        self.key = supabase_key or os.environ.get("HEXNIL_SUPABASE_KEY") or DEFAULT_ANON_KEY
        self.timeout = timeout_seconds

    @property
    def headers(self) -> Dict[str, str]:
        return {
            "apikey": self.key,
            "Authorization": f"Bearer {self.key}",
            "Content-Type": "application/json",
            "Prefer": "return=representation",
        }

    # 1. Device Registration & Querying
    def register_device(self, device_data: Dict[str, Any]) -> Dict[str, Any]:
        """Upsert a device record into the devices table."""
        endpoint = f"{self.url}/rest/v1/devices"
        headers = dict(self.headers)
        headers["Prefer"] = "resolution=merge-duplicates,return=representation"

        resp = requests.post(
            endpoint,
            headers=headers,
            json=device_data,
            timeout=self.timeout,
        )
        resp.raise_for_status()
        data = resp.json()
        return data[0] if isinstance(data, list) and data else device_data

    def list_devices(self) -> List[Dict[str, Any]]:
        """List all registered devices in the fleet."""
        endpoint = f"{self.url}/rest/v1/devices?select=*&order=last_seen_at.desc"
        resp = requests.get(endpoint, headers=self.headers, timeout=self.timeout)
        resp.raise_for_status()
        return resp.json()

    def get_device(self, device_id: str) -> Optional[Dict[str, Any]]:
        """Get details for a specific device."""
        endpoint = f"{self.url}/rest/v1/devices?device_id=eq.{device_id}&select=*"
        resp = requests.get(endpoint, headers=self.headers, timeout=self.timeout)
        resp.raise_for_status()
        data = resp.json()
        return data[0] if data else None

    # 2. Experiments
    def upload_experiment(self, exp_data: Dict[str, Any]) -> Dict[str, Any]:
        """Upsert an experiment record into the experiments table."""
        endpoint = f"{self.url}/rest/v1/experiments"
        headers = dict(self.headers)
        headers["Prefer"] = "resolution=merge-duplicates,return=representation"

        resp = requests.post(
            endpoint,
            headers=headers,
            json=exp_data,
            timeout=self.timeout,
        )
        resp.raise_for_status()
        data = resp.json()
        return data[0] if isinstance(data, list) and data else exp_data

    def list_experiments(self, device_id: Optional[str] = None) -> List[Dict[str, Any]]:
        """List experiments, optionally filtered by device."""
        endpoint = f"{self.url}/rest/v1/experiments?select=*&order=created_at.desc"
        if device_id:
            endpoint += f"&device_id=eq.{device_id}"
        resp = requests.get(endpoint, headers=self.headers, timeout=self.timeout)
        resp.raise_for_status()
        return resp.json()

    # 3. Telemetry Samples
    def upload_telemetry_batch(self, samples: List[Dict[str, Any]]) -> int:
        """Upload a batch of telemetry samples."""
        if not samples:
            return 0
        endpoint = f"{self.url}/rest/v1/telemetry_samples"
        resp = requests.post(
            endpoint,
            headers=self.headers,
            json=samples,
            timeout=self.timeout,
        )
        resp.raise_for_status()
        data = resp.json()
        return len(data) if isinstance(data, list) else len(samples)

    def get_telemetry_samples(
        self,
        device_id: str,
        experiment_id: Optional[str] = None,
        limit: int = 500,
    ) -> List[Dict[str, Any]]:
        """Fetch telemetry samples for a device and experiment."""
        endpoint = f"{self.url}/rest/v1/telemetry_samples?device_id=eq.{device_id}&select=*&order=timestamp.asc&limit={limit}"
        if experiment_id:
            endpoint += f"&experiment_id=eq.{experiment_id}"
        resp = requests.get(endpoint, headers=self.headers, timeout=self.timeout)
        resp.raise_for_status()
        return resp.json()

    def upload_telemetry_snapshot(self, snapshot_data: Dict[str, Any]) -> Dict[str, Any]:
        """Insert or upsert a comprehensive device telemetry snapshot row."""
        endpoint = f"{self.url}/rest/v1/device_telemetry_snapshots"
        headers = dict(self.headers)
        headers["Prefer"] = "resolution=merge-duplicates,return=representation"
        resp = requests.post(endpoint, headers=headers, json=snapshot_data, timeout=self.timeout)
        resp.raise_for_status()
        data = resp.json()
        return data[0] if isinstance(data, list) and data else snapshot_data

    def get_latest_telemetry_snapshot(self, device_id: Optional[str] = None) -> List[Dict[str, Any]]:
        """Query latest device telemetry view (temp, battery, refresh, latency, ram, storage)."""
        endpoint = f"{self.url}/rest/v1/latest_device_telemetry?select=*"
        if device_id:
            endpoint += f"&device_id=eq.{device_id}"
        resp = requests.get(endpoint, headers=self.headers, timeout=self.timeout)
        resp.raise_for_status()
        return resp.json()

    # 4. Device Reports & Issues
    def publish_device_report(self, report_data: Dict[str, Any]) -> Dict[str, Any]:
        """Upsert a final device evaluation report."""
        endpoint = f"{self.url}/rest/v1/device_reports"
        headers = dict(self.headers)
        headers["Prefer"] = "resolution=merge-duplicates,return=representation"

        resp = requests.post(
            endpoint,
            headers=headers,
            json=report_data,
            timeout=self.timeout,
        )
        resp.raise_for_status()
        data = resp.json()
        return data[0] if isinstance(data, list) and data else report_data

    def get_latest_device_report(self, device_id: str) -> Optional[Dict[str, Any]]:
        """Get the latest evaluation report for a specific device."""
        endpoint = f"{self.url}/rest/v1/device_reports?device_id=eq.{device_id}&select=*&order=updated_at.desc&limit=1"
        resp = requests.get(endpoint, headers=self.headers, timeout=self.timeout)
        resp.raise_for_status()
        data = resp.json()
        return data[0] if data else None

    def publish_issue_classifications(self, issues: List[Dict[str, Any]]) -> int:
        """Insert classified issues/regressions for a device report."""
        if not issues:
            return 0
        endpoint = f"{self.url}/rest/v1/issue_classifications"
        resp = requests.post(
            endpoint,
            headers=self.headers,
            json=issues,
            timeout=self.timeout,
        )
        resp.raise_for_status()
        data = resp.json()
        return len(data) if isinstance(data, list) else len(issues)

    def get_device_issues(self, device_id: str, report_id: Optional[str] = None) -> List[Dict[str, Any]]:
        """Get all issues/regressions logged for a specific device."""
        endpoint = f"{self.url}/rest/v1/issue_classifications?device_id=eq.{device_id}&select=*&order=created_at.desc"
        if report_id:
            endpoint += f"&report_id=eq.{report_id}"
        resp = requests.get(endpoint, headers=self.headers, timeout=self.timeout)
        resp.raise_for_status()
        return resp.json()
