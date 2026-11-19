"""
Production Readiness & Concurrency Tests.
Verifies thread-safe audit log serialization, health probes, security headers, and metrics.
"""

import threading
import pytest
from fastapi.testclient import TestClient
from src.api.app import app
from src.module3_generation_audit.audit_logger import HashChainedAuditLogger


@pytest.fixture
def client():
    return TestClient(app)


def test_concurrent_audit_log_thread_safety(tmp_path):
    """
    Stress-tests Algorithm 2 hash chaining under high concurrent load:
    Spawns 20 concurrent threads appending to the log simultaneously.
    Verifies that the resulting chain has zero broken links and 100% cryptographic integrity.
    """
    test_log = tmp_path / "concurrent_audit.jsonl"
    logger = HashChainedAuditLogger(log_path=test_log)

    threads = []
    num_threads = 20

    def worker(worker_id):
        logger.log_event(
            user_id=f"THREAD_USER_{worker_id}",
            role="Treating Doctor",
            policy_version="v1.0",
            template_version="v1",
            filters_applied={"worker": worker_id},
            document_ids=[f"DOC_{worker_id}"],
            outcome="ALLOWED",
            query_text=f"Concurrent stress test query from worker {worker_id}"
        )

    for i in range(num_threads):
        t = threading.Thread(target=worker, args=(i,))
        threads.append(t)
        t.start()

    for t in threads:
        t.join()

    # Verify all entries were recorded
    entries = logger.read_all_entries()
    assert len(entries) == num_threads

    # Verify that the hash chain is 100% intact with zero broken links
    is_valid, msg, steps = logger.verify_integrity()
    assert is_valid is True, f"Hash chain failed under concurrency: {msg}"
    assert len(steps) == num_threads


def test_liveness_probe(client):
    """Verifies /api/health/live returns HTTP 200 and ALIVE status."""
    res = client.get("/api/health/live")
    assert res.status_code == 200
    assert res.json()["status"] == "ALIVE"


def test_readiness_probe(client):
    """Verifies /api/health/ready validates database, policy, and audit subsystems."""
    res = client.get("/api/health/ready")
    assert res.status_code == 200
    data = res.json()
    assert data["ready"] is True
    assert data["subsystems"]["database"]["status"] == "HEALTHY"
    assert data["subsystems"]["policy_matrix"]["status"] == "HEALTHY"
    assert data["subsystems"]["audit_chain"]["is_valid"] is True


def test_metrics_endpoint(client):
    """Verifies /api/metrics exposes operational telemetry."""
    res = client.get("/api/metrics")
    assert res.status_code == 200
    data = res.json()
    assert "uptime_seconds" in data
    assert "total_requests" in data
    assert "chain_integrity_verified" in data
    assert data["chain_integrity_verified"] is True


def test_security_headers_and_correlation_id(client):
    """Verifies security response headers and X-Request-ID tracing."""
    res = client.get("/health")
    assert res.status_code == 200
    assert "X-Request-ID" in res.headers
    assert res.headers["X-Content-Type-Options"] == "nosniff"
    assert res.headers["X-Frame-Options"] == "SAMEORIGIN"
    assert res.headers["X-XSS-Protection"] == "1; mode=block"
