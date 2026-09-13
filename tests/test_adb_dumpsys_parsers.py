"""Unit tests for ADB dumpsys parsers (meminfo, gfxinfo, thermalservice)."""

from unittest.mock import MagicMock
import pytest
from hexnil.telemetry.adb_collectors import (
    AdbGfxinfoCollector,
    AdbMeminfoCollector,
    AdbThermalCollector,
)


def test_parse_meminfo():
    raw_sample = """
** MEMINFO in pid 26342 [com.example.iqoo_hexnil] **
                   Pss  Private  Private  SwapPss      Rss     Heap
                 Total    Dirty    Clean    Dirty    Total     Size
                ------   ------   ------   ------   ------   ------
  Native Heap    26127    26076       28       74    27756    39080
  Dalvik Heap     3787     3768        0       82     4708    10441
TOTAL PSS:       75412
"""
    collector = AdbMeminfoCollector(MagicMock())
    metrics = collector.parse_meminfo(raw_sample)

    assert metrics["native_heap_pss_kb"] == 26127
    assert metrics["dalvik_heap_pss_kb"] == 3787
    assert metrics["total_pss_kb"] == 75412


def test_parse_gfxinfo():
    raw_sample = """
Applications Graphics Acceleration Info:
** Graphics info for pid 26342 [com.example.iqoo_hexnil] **

Total frames rendered: 120
Janky frames: 6 (5.00%)
50th percentile: 5ms
90th percentile: 14ms
95th percentile: 22ms
99th percentile: 45ms
"""
    collector = AdbGfxinfoCollector(MagicMock())
    metrics = collector.parse_gfxinfo(raw_sample)

    assert metrics["total_frames"] == 120
    assert metrics["janky_frames"] == 6
    assert metrics["janky_percentage"] == 5.0
    assert metrics["p50_ms"] == 5
    assert metrics["p90_ms"] == 14
    assert metrics["p95_ms"] == 22
    assert metrics["p99_ms"] == 45


def test_parse_thermal():
    raw_sample = """
Current temperatures from HAL:
	Temperature{mValue=34.603, mType=0, mName=CPU, mStatus=0}
	Temperature{mValue=31.6, mType=2, mName=BATTERY, mStatus=0}
	Temperature{mValue=33.3, mType=3, mName=SKIN, mStatus=0}
"""
    collector = AdbThermalCollector(MagicMock())
    temps = collector.parse_thermal(raw_sample)

    assert temps["cpu"] == 34.603
    assert temps["battery"] == 31.6
    assert temps["skin"] == 33.3


def test_parse_empty_dumpsys():
    mem_col = AdbMeminfoCollector(MagicMock())
    assert mem_col.parse_meminfo("") == {}

    gfx_col = AdbGfxinfoCollector(MagicMock())
    assert gfx_col.parse_gfxinfo("") == {}

    thermal_col = AdbThermalCollector(MagicMock())
    assert thermal_col.parse_thermal("") == {}
