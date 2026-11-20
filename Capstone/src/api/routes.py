"""
FastAPI Routes for Identity, Chat Enforcement, Policy Governance, Health & Metrics.
"""

import time
import sqlite3
from datetime import datetime, timezone
from typing import Dict, Any
from fastapi import APIRouter, HTTPException, Depends, Request
from src.api.schemas import (
    LoginRequest,
    BreakGlassRequest,
    ChatQueryRequest,
    PolicyApproveRequest,
    SimulateTamperRequest
)
from src.module1_identity_policy.idp_service import IdPService
from src.pipeline import RequestEnforcementPipeline
from src.config import DB_PATH, ACTIVE_POLICY_PATH

router = APIRouter()
idp_service = IdPService()
pipeline = RequestEnforcementPipeline()

SERVER_START_TIME = time.time()


# --- Operational Health & Readiness Probes ---

@router.get("/health/live")
def liveness_check():
    """Liveness probe for Kubernetes / Docker health monitoring."""
    return {"status": "ALIVE", "timestamp": datetime.now(timezone.utc).isoformat()}


@router.get("/health/ready")
def readiness_check():
    """
    Deep readiness probe validating:
    1. SQLite database connectivity and schema
    2. Active permission policy loading
    3. Audit log cryptographic integrity
    """
    checks: Dict[str, Any] = {}
    is_ready = True

    # 1. Database Connectivity Check
    try:
        conn = sqlite3.connect(DB_PATH, timeout=5.0)
        cur = conn.cursor()
        cur.execute("SELECT count(*) FROM patients")
        pt_count = cur.fetchone()[0]
        conn.close()
        checks["database"] = {"status": "HEALTHY", "patients_count": pt_count}
    except Exception as e:
        checks["database"] = {"status": "UNHEALTHY", "error": str(e)}
        is_ready = False

    # 2. Policy Matrix Integrity Check
    try:
        policy_ver = pipeline.policy_engine.get_policy_version()
        roles_count = len(pipeline.policy_engine.policy.get("roles", {}))
        checks["policy_matrix"] = {
            "status": "HEALTHY",
            "version": policy_ver,
            "roles_configured": roles_count
        }
    except Exception as e:
        checks["policy_matrix"] = {"status": "UNHEALTHY", "error": str(e)}
        is_ready = False

    # 3. Audit Log Integrity Check
    try:
        chain_valid, msg, steps = pipeline.audit_logger.verify_integrity()
        checks["audit_chain"] = {
            "status": "HEALTHY" if chain_valid else "TAMPER_DETECTED",
            "is_valid": chain_valid,
            "entries_verified": len(steps),
            "detail": msg
        }
        if not chain_valid:
            is_ready = False
    except Exception as e:
        checks["audit_chain"] = {"status": "UNHEALTHY", "error": str(e)}
        is_ready = False

    status_code = 200 if is_ready else 503
    if not is_ready:
        raise HTTPException(status_code=status_code, detail={"ready": False, "subsystems": checks})

    return {
        "ready": True,
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "subsystems": checks
    }


# --- Observability Metrics Endpoint ---

@router.get("/metrics")
def get_metrics():
    """Operational metrics: query volumes, enforcement outcomes, latency stats."""
    entries = pipeline.audit_logger.read_all_entries()
    total_queries = len(entries)
    allowed_count = sum(1 for e in entries if e.get("entry", {}).get("outcome") == "ALLOWED")
    blocked_count = sum(1 for e in entries if e.get("entry", {}).get("outcome") == "BLOCKED")

    is_valid, alert_msg, steps = pipeline.audit_logger.verify_integrity()

    uptime_seconds = round(time.time() - SERVER_START_TIME, 2)

    return {
        "uptime_seconds": uptime_seconds,
        "total_requests": total_queries,
        "allowed_requests": allowed_count,
        "blocked_requests": blocked_count,
        "block_ratio": round((blocked_count / total_queries) if total_queries > 0 else 0, 4),
        "audit_chain_depth": len(steps),
        "chain_integrity_verified": is_valid,
        "active_policy_version": pipeline.policy_engine.get_policy_version()
    }


# --- Identity & Persona Routes ---

@router.get("/personas")
def get_personas():
    """List predefined hospital staff personas for demonstration."""
    return {"personas": idp_service.list_personas()}


@router.post("/auth/login")
def login(req: LoginRequest):
    """Authenticate staff persona and issue verified JWT."""
    try:
        return idp_service.login(req.user_id, req.password)
    except Exception as e:
        raise HTTPException(status_code=401, detail=str(e))


@router.post("/auth/break-glass")
def break_glass(req: BreakGlassRequest):
    """Issue emergency break-glass token."""
    try:
        return idp_service.issue_break_glass_token(req.user_id, req.justification)
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


# --- Request Enforcement Chat Route ---

@router.post("/chat/query")
def chat_query(req: ChatQueryRequest):
    """Execute query through the 6-step Request Enforcement Pipeline."""
    return pipeline.process_query(query=req.query, token=req.token)


# --- Cryptographic Audit Log Routes ---

@router.get("/audit/logs")
def get_audit_logs():
    """Retrieve full append-only hash-chained audit log."""
    entries = pipeline.audit_logger.read_all_entries()
    return {"entries": entries, "total_records": len(entries)}


@router.post("/audit/verify")
def verify_audit_log():
    """Run cryptographic SHA-256 verification across the audit chain."""
    is_valid, alert, steps = pipeline.audit_logger.verify_integrity()
    return {
        "is_valid": is_valid,
        "message": alert,
        "verified_count": len(steps),
        "steps": steps
    }


@router.post("/audit/simulate-tamper")
def simulate_tamper(req: SimulateTamperRequest):
    """Secretly alter a row to demonstrate tamper detection alert."""
    return pipeline.audit_logger.simulate_tampering(req.entry_index)


# --- Policy Management & Dual-Approver Governance ---

@router.get("/policy")
def get_policy():
    """Retrieve active versioned policy matrix and pending draft."""
    return {
        "active_policy": pipeline.policy_engine.policy,
        "draft_policy": pipeline.policy_engine.get_draft_policy()
    }


@router.post("/policy/approve-draft")
def approve_draft(req: PolicyApproveRequest):
    """Dual-approver workflow: Approve and activate draft policy."""
    try:
        res = pipeline.policy_engine.approve_draft_policy(req.approver_id)
        return res
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))
