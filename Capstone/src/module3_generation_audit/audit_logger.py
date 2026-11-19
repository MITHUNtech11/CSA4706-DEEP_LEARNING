"""
Algorithm 2: Cryptographic Append-Only, Hash-Chained Audit Logger.
Thread-safe implementation with SHA-256 hash chaining and tamper-evident integrity verification.
"""

import json
import hashlib
import threading
from datetime import datetime, timezone
from pathlib import Path
from typing import Dict, Any, List, Optional, Tuple
from src.config import AUDIT_LOG_PATH

GENESIS_HASH = "0000000000000000000000000000000000000000000000000000000000000000"


class TamperAlertError(Exception):
    """Raised when cryptographic hash chain verification detects record tampering."""
    pass


class HashChainedAuditLogger:
    def __init__(self, log_path: Path = AUDIT_LOG_PATH):
        self.log_path = log_path
        self._lock = threading.RLock()  # Thread-safe re-entrant lock for concurrent appends
        self._ensure_log_exists()

    def _ensure_log_exists(self):
        with self._lock:
            if not self.log_path.exists():
                self.log_path.touch()

    def get_latest_hash(self) -> str:
        """Retrieves the hash of the most recent log entry, or GENESIS_HASH if empty."""
        with self._lock:
            if not self.log_path.exists() or self.log_path.stat().st_size == 0:
                return GENESIS_HASH

            last_line = ""
            with open(self.log_path, "r", encoding="utf-8") as f:
                for line in f:
                    if line.strip():
                        last_line = line.strip()

            if not last_line:
                return GENESIS_HASH

            try:
                record = json.loads(last_line)
                return record.get("current_hash", GENESIS_HASH)
            except Exception:
                return GENESIS_HASH

    @staticmethod
    def _compute_entry_hash(entry_payload: Dict[str, Any], prev_hash: str) -> str:
        """
        Computes SHA-256 hash over canonical serialized JSON entry + prev_hash.
        """
        canonical_str = json.dumps(entry_payload, sort_keys=True, separators=(",", ":"))
        combined = f"{canonical_str}|{prev_hash}"
        return hashlib.sha256(combined.encode("utf-8")).hexdigest()

    def log_event(
        self,
        user_id: str,
        role: str,
        policy_version: str,
        template_version: str,
        filters_applied: Dict[str, Any],
        document_ids: List[str],
        outcome: str,  # "ALLOWED" or "BLOCKED"
        query_text: str,
        extra_telemetry: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Appends a new cryptographically chained audit log entry (Algorithm 2).
        Thread-safe under concurrent requests.
        """
        with self._lock:
            prev_hash = self.get_latest_hash()
            timestamp = datetime.now(timezone.utc).isoformat()
            entry_index = len(self._read_all_unlocked()) + 1

            entry_data = {
                "entry_index": entry_index,
                "timestamp": timestamp,
                "user_id": user_id,
                "role": role,
                "policy_version": policy_version,
                "template_version": template_version,
                "filters_applied": filters_applied,
                "document_ids": document_ids,
                "outcome": outcome,
                "query_summary": query_text[:120],
                "telemetry": extra_telemetry or {}
            }

            current_hash = self._compute_entry_hash(entry_data, prev_hash)

            full_record = {
                "entry": entry_data,
                "prev_hash": prev_hash,
                "current_hash": current_hash
            }

            # Atomic append to log file
            with open(self.log_path, "a", encoding="utf-8") as f:
                f.write(json.dumps(full_record) + "\n")

            return full_record

    def _read_all_unlocked(self) -> List[Dict[str, Any]]:
        """Internal helper for reading entries while holding lock."""
        if not self.log_path.exists():
            return []

        entries = []
        with open(self.log_path, "r", encoding="utf-8") as f:
            for line in f:
                if line.strip():
                    try:
                        entries.append(json.loads(line.strip()))
                    except Exception:
                        pass
        return entries

    def read_all_entries(self) -> List[Dict[str, Any]]:
        """Thread-safe read of all records from the audit chain file."""
        with self._lock:
            return self._read_all_unlocked()

    def verify_integrity(self) -> Tuple[bool, Optional[str], List[Dict[str, Any]]]:
        """
        Algorithm 2 Verification:
        Recomputes hash chain sequentially from genesis.
        Returns: (is_valid, alert_message, verification_steps)
        """
        with self._lock:
            records = self._read_all_unlocked()
            if not records:
                return True, "Audit log is empty. Integrity intact.", []

            expected_prev_hash = GENESIS_HASH
            steps = []

            for idx, rec in enumerate(records):
                entry = rec.get("entry", {})
                logged_prev = rec.get("prev_hash")
                logged_current = rec.get("current_hash")

                # Check 1: Chain link consistency
                if logged_prev != expected_prev_hash:
                    alert = f"TAMPER ALERT at entry {idx + 1}: Chain link broken! Expected prev_hash '{expected_prev_hash[:10]}...', found '{logged_prev[:10]}...'."
                    return False, alert, steps

                # Check 2: Content hash recalculation
                computed_current = self._compute_entry_hash(entry, expected_prev_hash)
                if computed_current != logged_current:
                    alert = (
                        f"TAMPER ALERT at entry {idx + 1} (User: {entry.get('user_id')}, Role: {entry.get('role')}): "
                        f"Data modification detected! Entry hash mismatch.\n"
                        f"Stored:   {logged_current}\n"
                        f"Computed: {computed_current}"
                    )
                    return False, alert, steps

                steps.append({
                    "entry_index": entry.get("entry_index", idx + 1),
                    "timestamp": entry.get("timestamp"),
                    "outcome": entry.get("outcome"),
                    "hash_verified": True,
                    "current_hash": logged_current
                })

                expected_prev_hash = logged_current

            return True, f"Cryptographic integrity verified across all {len(records)} entries. Zero tampering detected.", steps

    def simulate_tampering(self, target_entry_index: int = 1) -> Dict[str, Any]:
        """
        Simulates an unauthorized database/log tamper attack by secretly modifying an outcome field.
        """
        with self._lock:
            records = self._read_all_unlocked()
            if not records:
                return {"status": "ERROR", "message": "No entries to tamper with."}

            target_idx = min(max(1, target_entry_index), len(records)) - 1
            original_outcome = records[target_idx]["entry"]["outcome"]
            tampered_outcome = "ALLOWED" if original_outcome == "BLOCKED" else "BLOCKED"

            records[target_idx]["entry"]["outcome"] = tampered_outcome
            records[target_idx]["entry"]["TAMPER_NOTE"] = "Attacker modified outcome without recomputing hash chain!"

            with open(self.log_path, "w", encoding="utf-8") as f:
                for rec in records:
                    f.write(json.dumps(rec) + "\n")

            return {
                "status": "TAMPERED",
                "entry_index": target_idx + 1,
                "original_outcome": original_outcome,
                "tampered_outcome": tampered_outcome,
                "message": f"Entry {target_idx + 1} secretly tampered in file without recalculating hashes."
            }
