"""Hexnil Phase 8: Evidence-Grounded AI Analyst (Groq)."""

from hexnil.explain.cache import ExplanationCache
from hexnil.explain.client import GroqClient
from hexnil.explain.contract import build_evidence_package, compute_evidence_hash
from hexnil.explain.eligibility import validate_evidence_eligibility
from hexnil.explain.fallback import generate_deterministic_explanation
from hexnil.explain.models import (
    ClaimAssessment,
    EvidenceEligibilityState,
    EvidenceExplanation,
    EvidencePackage,
    EvidenceReference,
    ExplanationSource,
    MetricEvidenceSummary,
)
from hexnil.explain.orchestrator import EvidenceExplanationOrchestrator
from hexnil.explain.prompt import build_system_prompt, build_user_prompt
from hexnil.explain.store import ExplanationStore
from hexnil.explain.validator import validate_groq_response

__all__ = [
    "ClaimAssessment",
    "EvidenceEligibilityState",
    "EvidenceExplanation",
    "EvidenceExplanationOrchestrator",
    "EvidencePackage",
    "EvidenceReference",
    "ExplanationCache",
    "ExplanationSource",
    "ExplanationStore",
    "GroqClient",
    "MetricEvidenceSummary",
    "build_evidence_package",
    "build_system_prompt",
    "build_user_prompt",
    "compute_evidence_hash",
    "generate_deterministic_explanation",
    "validate_evidence_eligibility",
    "validate_groq_response",
]
