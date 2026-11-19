"""
FastAPI Routes for Identity, Chat Enforcement, Policy Governance, and Audit.
"""

from fastapi import APIRouter, HTTPException, Depends
from src.api.schemas import (
    LoginRequest,
    BreakGlassRequest,
    ChatQueryRequest,
    PolicyApproveRequest,
    SimulateTamperRequest
)
from src.module1_identity_policy.idp_service import IdPService
from src.pipeline import RequestEnforcementPipeline

router = APIRouter()
idp_service = IdPService()
pipeline = RequestEnforcementPipeline()


@router.get("/personas")
def get_personas():
    """List predefined hospital staff personas for demonstration."""
    return {"personas": idp_service.list_personas()}


@router.post("/auth/login")
def login(req: LoginRequest):
    """Authenticate staff persona and issue verified JWT."""
    try:
        return idp_service.login(req.user_id)
    except Exception as e:
        raise HTTPException(status_code=401, detail=str(e))


@router.post("/auth/break-glass")
def break_glass(req: BreakGlassRequest):
    """Issue emergency break-glass token."""
    try:
        return idp_service.issue_break_glass_token(req.user_id, req.justification)
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.post("/chat/query")
def chat_query(req: ChatQueryRequest):
    """Execute query through the 6-step Request Enforcement Pipeline."""
    return pipeline.process_query(query=req.query, token=req.token)


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
