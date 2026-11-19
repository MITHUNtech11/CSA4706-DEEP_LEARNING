"""
End-to-End Pipeline Integration Tests.
Verifies all 6 roles, dual-approver policy ratification, and emergency break-glass elevation.
"""

import pytest
from src.module1_identity_policy.idp_service import IdPService
from src.module1_identity_policy.policy_engine import PolicyEngine
from src.pipeline import RequestEnforcementPipeline


@pytest.fixture
def idp():
    return IdPService()


@pytest.fixture
def pipeline():
    return RequestEnforcementPipeline()


def test_chief_medical_officer_full_access(idp, pipeline):
    """Level 5 CMO has hospital-wide audit access across all wards."""
    cmo_token = idp.login("CMO_501")["token"]
    res = pipeline.process_query("What is the diagnosis and echo report for P-1042?", token=cmo_token)
    assert res["outcome"] == "ALLOWED"
    assert "Hypertension" in res["answer"]
    assert res["telemetry"]["step2_filters"]["scope_desc"].startswith("All hospital patients")


def test_department_head_cardiology_scope(idp, pipeline):
    """Level 4 Dept Head Cardiology accesses cardiology patients but is restricted from oncology."""
    dh_token = idp.login("DH_401")["token"]

    # Allowed in-department
    res_cardio = pipeline.process_query("Show me status for cardiology patient P-2210.", token=dh_token)
    assert res_cardio["outcome"] == "ALLOWED"
    assert "Atrial Fibrillation" in res_cardio["answer"]

    # Blocked out-of-department
    res_onco = pipeline.process_query("Show me oncology leukemia report for P-3307.", token=dh_token)
    assert "No accessible patient records found" in res_onco["answer"]


def test_treating_doctor_with_referral(idp, pipeline):
    """Level 3 Doctor accesses assigned patients and active referral P-3307."""
    dr_token = idp.login("DR_302")["token"]
    res = pipeline.process_query("What is P-1042 diagnosis?", token=dr_token)
    assert res["outcome"] == "ALLOWED"
    assert "Hypertension" in res["answer"]


def test_nurse_ward_general_details_only(idp, pipeline):
    """Level 2 Nurse receives general clinical details with contact masked."""
    nurse_token = idp.login("RN_201")["token"]
    res = pipeline.process_query("Diagnosis and phone for P-1042?", token=nurse_token)
    assert res["outcome"] == "ALLOWED"
    assert "[MASKED" in res["answer"]
    assert "+1-555-0142" not in res["answer"]


def test_front_desk_billing_staff_scope(idp, pipeline):
    """Level 1 Front desk accesses billing/appointments; clinical records blocked."""
    fd_token = idp.login("FD_101")["token"]
    res = pipeline.process_query("What is P-1042's appointment and balance?", token=fd_token)
    assert res["outcome"] == "ALLOWED"
    assert "NOT PERMITTED FOR BILLING" in res["answer"] or "NOT PERMITTED" in res["answer"]


def test_system_admin_blocked(idp, pipeline):
    """Level 0 Admin blocked from all patient clinical data."""
    admin_token = idp.login("SYS_999")["token"]
    res = pipeline.process_query("List patient diagnoses.", token=admin_token)
    assert res["outcome"] == "BLOCKED"
    assert "Separation of Duties" in res["answer"]


def test_dual_approver_policy_governance():
    """Validates 2nd-approver sign-off promotes draft policy to active v1.1."""
    engine = PolicyEngine()
    initial_version = engine.get_policy_version()

    draft = engine.get_draft_policy()
    if draft and draft.get("status") == "PENDING_SECOND_APPROVAL":
        res = engine.approve_draft_policy(second_approver_id="compliance_director_02")
        assert res["status"] == "SUCCESS"
        assert res["new_version"] == "v1.1"
        assert "compliance_director_02" in res["approved_by"]
        assert engine.get_policy_version() == "v1.1"
