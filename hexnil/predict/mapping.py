"""Subsystem, metric, condition, and expected direction mapping layer for Phase 7."""

import re
from typing import Optional, Tuple
from hexnil.predict.models import (
    ClaimSubsystem,
    ExtractionMethod,
    MetricStatus,
    StructuredClaim,
)
from hexnil.stats.models import MetricDirection
from hexnil.stats.registry import METRIC_REGISTRY, get_metric_direction

MAPPING_VERSION = "1.0.0"

# Keywords and patterns for subsystem mapping
_SUBSYSTEM_PATTERNS = [
    # 1. Battery / Power
    (
        ClaimSubsystem.BATTERY,
        [
            r"\bbatter(?:y|ies)\b",
            r"\bpower\s+consumption\b",
            r"\bpower\s+efficiency\b",
            r"\bbattery\s+drain\b",
            r"\bbattery\s+life\b",
            r"\bdischarge\b",
            r"\bwakelock\b",
            r"\benergy\b",
            r"\bmah\b",
        ],
    ),
    # 2. Startup / Launch
    (
        ClaimSubsystem.STARTUP,
        [
            r"\bstart(?:up)?\b",
            r"\bstart-up\b",
            r"\bcold\s+(?:\w+\s+)?start(?:up)?\b",
            r"\blaunch(?:ing)?\b",
            r"\bapp\s+launch\b",
            r"\bstartup\s+latency\b",
            r"\bstartup\s+duration\b",
            r"\bstartup\s+time\b",
            r"\binitial\s+launch\b",
            r"\binitial\s+splash\b",
            r"\bfaster\s+launch\b",
            r"\bfaster\s+start(?:up)?\b",
            r"\bopen\s+time\b",
            r"\bsplash\b",
        ],
    ),
    # 3. Memory / RAM
    (
        ClaimSubsystem.MEMORY,
        [
            r"\bmemor(?:y|ies)\b",
            r"\bheap\b",
            r"\bram\b",
            r"\boom\b",
            r"\bout\s+of\s+memory\b",
            r"\bmemory\s+leak\b",
            r"\bmemory\s+allocation\b",
            r"\bgarbage\s+collect(?:ion)?\b",
            r"\bgc\s+pause\b",
            r"\bavailable\s+ram\b",
        ],
    ),
    # 4. UI / Frame / Jank / Scrolling
    (
        ClaimSubsystem.UI_PERFORMANCE,
        [
            r"\bjank\b",
            r"\bframe\s+drop(?:s)?\b",
            r"\bframe\s+rate\b",
            r"\bscroll(?:ing)?\b",
            r"\b60\s*fps\b",
            r"\b120\s*fps\b",
            r"\bvsync\b",
            r"\bstutter\b",
            r"\bui\s+lag\b",
            r"\bfluid\s+scroll(?:ing)?\b",
            r"\bsmooth\s+scroll(?:ing)?\b",
            r"\bsmoothness\b",
        ],
    ),
    # 5. CPU / Processing / Computation
    (
        ClaimSubsystem.CPU_PERFORMANCE,
        [
            r"\bcpu\b",
            r"\bprocessor\b",
            r"\bcompute\b",
            r"\bcomputation\b",
            r"\bthread\s+contention\b",
            r"\bprocessing\s+speed\b",
            r"\bheavy\s+calculation\b",
            r"\bbackground\s+sync\b",
        ],
    ),
    # 6. Stability / Crash / ANR
    (
        ClaimSubsystem.STABILITY,
        [
            r"\bcrash(?:es)?\b",
            r"\banr(?:s)?\b",
            r"\bfreeze\b",
            r"\bhang\b",
            r"\bexception\b",
            r"\bnullpointer(?:exception)?\b",
            r"\bunexpectedly\s+close\b",
            r"\bstability\b",
            r"\breboot\b",
        ],
    ),
    # 7. Thermal
    (
        ClaimSubsystem.THERMAL,
        [
            r"\bthermal\b",
            r"\boverheat(?:ing)?\b",
            r"\bskin\s+temperature\b",
            r"\bdevice\s+temperature\b",
            r"\bheat\s+dissipation\b",
            r"\bthrottl(?:e|ing)\b",
        ],
    ),
]

# Patterns for extracting operational condition context
_CONDITION_PATTERNS = [
    (r"\b(?:during|in|while)\s+(?:continuous\s+)?background\s+video\s+(?:playback|streaming)\b", "continuous background video playback"),
    (r"\b(?:during|in|while)\s+video\s+(?:playback|streaming)\b", "video playback"),
    (r"\b(?:during|in|while)\s+cold\s+(?:start|launch)\b", "cold application launch"),
    (r"\b(?:on|during)\s+(?:initial\s+)?(?:splash|launch)\b", "initial launch"),
    (r"\b(?:during|in|while)\s+(?:fast\s+)?scroll(?:ing)?\b", "UI scrolling"),
    (r"\b(?:during|in|while)\s+(?:3d\s+)?gaming\b", "graphics / gaming"),
    (r"\b(?:in|during)\s+background\b", "background operation"),
    (r"\b(?:during|in|while)\s+(?:network\s+)?upload\b", "upload operation"),
    (r"\b(?:when|while)\s+rotating\s+screen\b", "screen rotation"),
]


def detect_subsystem(text: str) -> Tuple[ClaimSubsystem, float]:
    """Detect the most likely validation subsystem and confidence from normalized text."""
    lower_text = text.lower()
    best_subsystem = ClaimSubsystem.UNKNOWN
    max_matches = 0

    for subsystem, patterns in _SUBSYSTEM_PATTERNS:
        match_count = 0
        for pattern in patterns:
            if re.search(pattern, lower_text):
                match_count += 1
        if match_count > max_matches:
            max_matches = match_count
            best_subsystem = subsystem

    if max_matches >= 2:
        confidence = 0.95
    elif max_matches == 1:
        confidence = 0.85
    else:
        confidence = 0.20  # Unknown / vague

    return best_subsystem, confidence


def extract_condition(text: str) -> str:
    """Extract operational condition context from normalized claim text."""
    lower_text = text.lower()
    for pattern, condition in _CONDITION_PATTERNS:
        if re.search(pattern, lower_text):
            return condition
    return "general application execution"


def map_metric_and_direction(
    subsystem: ClaimSubsystem,
    text: str,
) -> Tuple[str, MetricStatus, MetricDirection, str]:
    """Map a claim to a real Phase 2/6 metric, status, and expected direction.

    Returns:
        Tuple of (metric_name, metric_status, expected_direction, mapping_reason)
    """
    lower_text = text.lower()

    if subsystem == ClaimSubsystem.BATTERY:
        # Check if text specifically mentions battery proxy measurement
        # Phase 6 metric: battery_discharge_proxy (video_power_01)
        direction = MetricDirection.LOWER_IS_BETTER
        return (
            "battery_discharge_proxy",
            MetricStatus.SUPPORTED,
            direction,
            "Mapped to measured Phase 6 battery_discharge_proxy (lower discharge is better).",
        )

    elif subsystem == ClaimSubsystem.STARTUP:
        direction = MetricDirection.LOWER_IS_BETTER
        return (
            "startup_duration_ms",
            MetricStatus.SUPPORTED,
            direction,
            "Mapped to measured Phase 6 startup_duration_ms (lower latency is better).",
        )

    elif subsystem == ClaimSubsystem.MEMORY:
        # Check if claim is about free/available RAM vs allocated heap
        if re.search(r"\b(?:available|free|more)\s+(?:ram|memory)\b", lower_text):
            return (
                "device_memory_available_mb",
                MetricStatus.SUPPORTED,
                MetricDirection.HIGHER_IS_BETTER,
                "Mapped to measured device_memory_available_mb (higher available RAM is better).",
            )
        else:
            return (
                "app_heap_allocated_mb",
                MetricStatus.SUPPORTED,
                MetricDirection.LOWER_IS_BETTER,
                "Mapped to measured app_heap_allocated_mb (lower heap allocation is better).",
            )

    elif subsystem == ClaimSubsystem.UI_PERFORMANCE:
        if re.search(r"\b(?:scroll\s+duration|scroll\s+speed)\b", lower_text):
            return (
                "scroll_duration_ms",
                MetricStatus.SUPPORTED,
                MetricDirection.LOWER_IS_BETTER,
                "Mapped to measured scroll_duration_ms (lower scroll duration is better).",
            )
        else:
            return (
                "ui_frame_jank_percent",
                MetricStatus.SUPPORTED,
                MetricDirection.LOWER_IS_BETTER,
                "Mapped to measured ui_frame_jank_percent (lower jank percentage is better).",
            )

    elif subsystem == ClaimSubsystem.CPU_PERFORMANCE:
        return (
            "compute_duration_ms",
            MetricStatus.SUPPORTED,
            MetricDirection.LOWER_IS_BETTER,
            "Mapped to measured compute_duration_ms (lower compute time is better).",
        )

    elif subsystem == ClaimSubsystem.STABILITY:
        # Stability is measured via process crashes during workload execution,
        # but Hexnil currently measures duration & telemetry; crash is a failure event.
        # Mark as UNSUPPORTED metric status to preserve data honesty.
        return (
            "UNSUPPORTED",
            MetricStatus.UNSUPPORTED,
            MetricDirection.UNKNOWN,
            "Crash/stability claims are captured as run execution status failures, not continuous telemetry metrics.",
        )

    elif subsystem == ClaimSubsystem.THERMAL:
        # Skin temperature is not directly exposed as a continuous baseline telemetry metric in Phase 2/6.
        return (
            "UNSUPPORTED",
            MetricStatus.UNSUPPORTED,
            MetricDirection.UNKNOWN,
            "Thermal temperature sensor telemetry is hardware-restricted on Android 16 without root.",
        )

    else:
        # Vague marketing text (e.g. "faster performance", "enhanced stability", "optimized experience")
        return (
            "UNSUPPORTED",
            MetricStatus.UNSUPPORTED,
            MetricDirection.UNKNOWN,
            "Claim wording lacks specific measurable telemetry indicator in Hexnil test suite.",
        )


def structure_claim(
    raw_text: str,
    normalized_text: str,
    claim_index: int,
    source: str = "release_notes",
) -> StructuredClaim:
    """Structure a raw claim into a validated StructuredClaim document."""
    claim_id = f"CLM-{claim_index:03d}"
    subsystem, confidence = detect_subsystem(normalized_text)
    condition = extract_condition(normalized_text)
    metric, metric_status, expected_dir, reason = map_metric_and_direction(
        subsystem, normalized_text
    )

    # If subsystem is UNKNOWN, degrade confidence
    if subsystem == ClaimSubsystem.UNKNOWN:
        confidence = 0.20

    return StructuredClaim(
        claim_id=claim_id,
        raw_text=raw_text,
        normalized_text=normalized_text,
        subsystem=subsystem.value,
        condition=condition,
        metric=metric,
        metric_status=metric_status,
        expected_direction=expected_dir,
        confidence=round(confidence, 2),
        source=source,
        extraction_method=ExtractionMethod.RULE_BASED,
        mapping_notes=reason,
    )
