"""Constrained prompt generation for Phase 8 Groq AI Analyst."""

import json
from hexnil.explain.models import EvidencePackage


def build_system_prompt() -> str:
    """Return the strict system instruction enforcing ground truth and non-hallucination."""
    return (
        "You are the Hexnil Engineering Evidence Analyst, a specialized technical AI assisting mobile release engineers.\n"
        "Your role is to explain verified differential experiment results in plain engineering language based EXCLUSIVELY on the provided EvidencePackage JSON.\n\n"
        "NON-NEGOTIABLE OPERATING PRINCIPLES:\n"
        "1. STRICT GROUND TRUTH: All measurements, deltas, p-values, confidence intervals, effect sizes, verdicts, and severities are authoritative and predetermined by Hexnil's statistical engine. You MUST NOT recalculate, modify, or contradict them.\n"
        "2. ZERO INVENTION: Never invent measurements, root causes, kernel behaviors, device states, or missing data. If a metric is unsupported or inconclusive, explicitly state that evidence is lacking.\n"
        "3. EXPLAIN, DON'T OVERCLAIM: Distinguish measured fact (e.g. 'workload_duration_ms increased by 3.05%') from statistical conclusion (e.g. 'classified as UNCHANGED because shift is within 5% threshold') and interpretation.\n"
        "4. ROOT CAUSE ATTRIBUTION: Never state 'The CPU governor caused this' or 'The update definitely caused X' unless direct telemetry in the evidence package establishes it. Frame unmeasured mechanisms strictly as hypotheses for further testing.\n"
        "5. SEVERITY & VERDICT LOCK: Your output 'severity' and 'verdict' MUST NOT exceed or contradict the authoritative package values.\n"
        "6. STRUCTURED JSON: You must respond ONLY with a valid JSON object adhering strictly to the requested schema. Do not enclose in markdown ticks or prefix text."
    )


def build_user_prompt(package: EvidencePackage) -> str:
    """Return the user prompt containing the structured EvidencePackage and required output schema."""
    package_json = package.model_dump_json(indent=2)
    package_severity = "NONE"
    if package.verdicts and "severity" in package.verdicts[0]:
        package_severity = str(package.verdicts[0]["severity"])
    elif package.metrics:
        package_severity = package.metrics[0].severity

    artifact_path = ""
    if isinstance(package.provenance, dict):
        artifact_path = package.provenance.get("comparison_path", "")

    return (
        f"EVIDENCE PACKAGE DATA:\n{package_json}\n\n"
        "INSTRUCTIONS:\n"
        "Analyze the above EvidencePackage and respond ONLY with a valid JSON object containing ALL 8 OF THE FOLLOWING KEYS:\n"
        "{\n"
        '  "summary": "2-3 sentence executive engineering summary explaining the release outcome.",\n'
        '  "claim_assessment": [\n'
        '    {\n'
        '      "claim_id": "CLM-001",\n'
        '      "claim_text": "claim description",\n'
        '      "target_metric": "metric_name",\n'
        '      "status": "SUPPORTED" | "CONTRADICTED" | "INCONCLUSIVE" | "UNSUPPORTED_METRIC",\n'
        '      "explanation": "why evidence supports or refutes"\n'
        '    }\n'
        '  ],\n'
        '  "observed_changes": [\n'
        '    "Factual string of measured metric shift (metric name, V0 -> V1, delta %, sample count)."\n'
        '  ],\n'
        '  "statistical_interpretation": "Detailed engineering explanation of p-values, confidence intervals, effect sizes, and thresholds.",\n'
        f'  "severity": "{package_severity}",\n'
        '  "limitations": [\n'
        '    "Bullet point noting sensor restrictions (e.g. Android 16 thermal sysfs), sample size limits, etc."\n'
        '  ],\n'
        '  "recommended_next_step": "Actionable, concrete engineering next step.",\n'
        '  "evidence_references": [\n'
        '    {\n'
        '      "reference_id": "REF-001",\n'
        '      "type": "comparison",\n'
        '      "identifier": "' + package.comparison_id + '",\n'
        f'      "artifact_path": "{artifact_path}",\n'
        '      "description": "Master comparison record"\n'
        '    }\n'
        '  ]\n'
        "}\n\n"
        "CRITICAL: You MUST include ALL 8 keys: 'summary', 'claim_assessment', 'observed_changes', 'statistical_interpretation', 'severity', 'limitations', 'recommended_next_step', and 'evidence_references'. Do not truncate or omit any key."
    )

