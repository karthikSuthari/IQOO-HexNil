"""Evidence-hash keyed cache for Phase 8 AI Analyst explanations."""

import logging
from typing import Optional

from hexnil.explain.models import EvidenceExplanation, EvidencePackage
from hexnil.explain.store import ExplanationStore

logger = logging.getLogger("hexnil.explain.cache")


class ExplanationCache:
    """Cache manager enforcing comparison and evidence hash freshness."""

    def __init__(self, store: ExplanationStore):
        self.store = store

    def get_cached(self, package: EvidencePackage) -> Optional[EvidenceExplanation]:
        """Retrieve cached explanation only if comparison ID and evidence hash match exactly."""
        explanation = self.store.load_explanation(package.comparison_id)
        if not explanation:
            return None

        # Hash check: if evidence changed, cache is stale and must be discarded
        if explanation.evidence_hash != package.evidence_hash:
            logger.info(
                "Cached explanation for '%s' is stale (hash mismatch: cached=%s, current=%s)",
                package.comparison_id,
                explanation.evidence_hash[:8],
                package.evidence_hash[:8],
            )
            return None

        explanation.is_cached = True
        return explanation

    def put_cached(self, explanation: EvidenceExplanation) -> None:
        """Store an explanation in cache/persistence."""
        self.store.save_explanation(explanation)
