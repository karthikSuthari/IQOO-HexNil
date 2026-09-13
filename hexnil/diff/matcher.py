"""Workload configuration locking and run pair matching layer."""

import logging
from typing import Dict, List, Optional, Set, Tuple

from hexnil.diff.models import ComparisonRunPair, PairStatus
from hexnil.workloads.models import RunStatus, WorkloadRun

logger = logging.getLogger("hexnil.diff.matcher")


class WorkloadRunMatcher:
    """Enforces configuration hash locking and pairs V0 and V1 workload runs."""

    def verify_configuration_lock(
        self,
        v0_workload_hashes: Dict[str, str],
        v1_workload_hashes: Dict[str, str],
    ) -> Tuple[List[str], List[str]]:
        """Verify that V1 workload configuration hashes match V0 baseline hashes byte-for-byte.

        Returns:
            Tuple of (matched_workload_ids, mismatched_workload_ids)
        """
        matched: List[str] = []
        mismatched: List[str] = []

        for wid, v0_hash in v0_workload_hashes.items():
            v1_hash = v1_workload_hashes.get(wid)
            if v1_hash is None:
                logger.warning("Workload '%s' present in V0 but missing from V1 suite", wid)
                mismatched.append(wid)
            elif v0_hash != v1_hash:
                logger.error(
                    "CONFIGURATION MISMATCH for workload '%s': V0 (%s) != V1 (%s)",
                    wid,
                    v0_hash,
                    v1_hash,
                )
                mismatched.append(wid)
            else:
                matched.append(wid)

        return matched, mismatched

    def match_runs(
        self,
        comparison_id: str,
        v0_runs: List[WorkloadRun],
        v1_runs: List[WorkloadRun],
        v0_workload_hashes: Dict[str, str],
        v1_workload_hashes: Dict[str, str],
    ) -> List[ComparisonRunPair]:
        """Pair V0 and V1 workload runs iteration-by-iteration."""
        pairs: List[ComparisonRunPair] = []

        # Index runs by (workload_id, iteration)
        v0_map: Dict[Tuple[str, int], WorkloadRun] = {
            (r.workload_id, r.iteration): r for r in v0_runs
        }
        v1_map: Dict[Tuple[str, int], WorkloadRun] = {
            (r.workload_id, r.iteration): r for r in v1_runs
        }

        # Find all unique (workload_id, iteration) keys
        all_keys: Set[Tuple[str, int]] = set(v0_map.keys()) | set(v1_map.keys())
        sorted_keys = sorted(all_keys, key=lambda k: (k[0], k[1]))

        for wid, iter_num in sorted_keys:
            v0_run: Optional[WorkloadRun] = v0_map.get((wid, iter_num))
            v1_run: Optional[WorkloadRun] = v1_map.get((wid, iter_num))

            v0_hash = v0_workload_hashes.get(wid, v0_run.configuration_hash if v0_run else "unknown")
            v1_hash = v1_workload_hashes.get(wid, v1_run.configuration_hash if v1_run else "unknown")

            # Check configuration lock
            if v0_hash != v1_hash:
                pairs.append(
                    ComparisonRunPair(
                        comparison_id=comparison_id,
                        workload_id=wid,
                        iteration=iter_num,
                        v0_run_id=v0_run.run_id if v0_run else None,
                        v1_run_id=v1_run.run_id if v1_run else None,
                        v0_duration_ms=v0_run.duration_ms if v0_run else None,
                        v1_duration_ms=v1_run.duration_ms if v1_run else None,
                        v0_configuration_hash=v0_hash,
                        v1_configuration_hash=v1_hash,
                        pair_status=PairStatus.CONFIGURATION_MISMATCH,
                        mismatch_reason=f"Configuration hash mismatch: V0 ({v0_hash}) != V1 ({v1_hash})",
                    )
                )
                continue

            # Check matching presence
            if v0_run is None:
                pairs.append(
                    ComparisonRunPair(
                        comparison_id=comparison_id,
                        workload_id=wid,
                        iteration=iter_num,
                        v0_run_id=None,
                        v1_run_id=v1_run.run_id,
                        v0_duration_ms=None,
                        v1_duration_ms=v1_run.duration_ms,
                        v0_configuration_hash=v0_hash,
                        v1_configuration_hash=v1_hash,
                        pair_status=PairStatus.UNMATCHED_V0_MISSING,
                        mismatch_reason=f"No matching V0 baseline run for iteration {iter_num}",
                    )
                )
            elif v1_run is None:
                pairs.append(
                    ComparisonRunPair(
                        comparison_id=comparison_id,
                        workload_id=wid,
                        iteration=iter_num,
                        v0_run_id=v0_run.run_id,
                        v1_run_id=None,
                        v0_duration_ms=v0_run.duration_ms,
                        v1_duration_ms=None,
                        v0_configuration_hash=v0_hash,
                        v1_configuration_hash=v1_hash,
                        pair_status=PairStatus.UNMATCHED_V1_MISSING,
                        mismatch_reason=f"No matching V1 update run for iteration {iter_num}",
                    )
                )
            else:
                # Both runs exist: check validity
                v0_ok = (v0_run.status == RunStatus.SUCCESS)
                v1_ok = (v1_run.status == RunStatus.SUCCESS)

                if v0_ok and v1_ok:
                    pairs.append(
                        ComparisonRunPair(
                            comparison_id=comparison_id,
                            workload_id=wid,
                            iteration=iter_num,
                            v0_run_id=v0_run.run_id,
                            v1_run_id=v1_run.run_id,
                            v0_duration_ms=v0_run.duration_ms,
                            v1_duration_ms=v1_run.duration_ms,
                            v0_configuration_hash=v0_hash,
                            v1_configuration_hash=v1_hash,
                            pair_status=PairStatus.MATCHED,
                        )
                    )
                else:
                    pairs.append(
                        ComparisonRunPair(
                            comparison_id=comparison_id,
                            workload_id=wid,
                            iteration=iter_num,
                            v0_run_id=v0_run.run_id,
                            v1_run_id=v1_run.run_id,
                            v0_duration_ms=v0_run.duration_ms,
                            v1_duration_ms=v1_run.duration_ms,
                            v0_configuration_hash=v0_hash,
                            v1_configuration_hash=v1_hash,
                            pair_status=PairStatus.INVALID,
                            mismatch_reason=f"One or both runs invalid: V0={v0_run.status.value}, V1={v1_run.status.value}",
                        )
                    )

        return pairs
