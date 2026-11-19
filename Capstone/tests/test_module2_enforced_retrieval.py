"""
Tests for Module 2: Enforced Retrieval (Slide 15 Tests to Pass).
- A doctor cannot read another department's patient without a referral
- A nurse never receives identifiers outside assigned patients
- Expired referrals or over-broad queries return nothing
"""

import pytest
from src.module1_identity_policy.idp_service import IdPService
from src.pipeline import RequestEnforcementPipeline


@pytest.fixture
def idp():
    return IdPService()


@pytest.fixture
def pipeline():
    return RequestEnforcementPipeline()


def test_doctor_cannot_read_another_department_without_referral(idp, pipeline):
    """
    Slide 15: A doctor cannot read another department's patient without a referral.
    Dr. Sharma (Cardiology) attempts to access P-4180 (Orthopedics) where no active referral exists.
    """
    dr_login = idp.login("DR_302")
    dr_token = dr_login["token"]

    res = pipeline.process_query("What is the orthopedic surgical note for patient P-4180?", token=dr_token)
    # The pre-retrieval filter excludes P-4180, so 0 documents are retrieved and system states no accessible records
    assert "P-4180" not in res["telemetry"]["step3_retrieval"]["patients_in_scope"]
    assert "No accessible patient records found" in res["answer"]


def test_doctor_with_active_referral_can_access_patient(idp, pipeline):
    """
    Dr. Sharma (Cardiology) CAN access P-3307 (Oncology) because an ACTIVE referral exists!
    """
    dr_login = idp.login("DR_302")
    dr_token = dr_login["token"]

    res = pipeline.process_query("Show me diagnosis and cardiotoxicity consult for P-3307.", token=dr_token)
    assert res["outcome"] == "ALLOWED"
    assert "P-3307" in res["telemetry"]["step3_retrieval"]["patients_in_scope"]
    assert "Acute Myeloid Leukemia" in res["answer"] or "Leukemia" in res["answer"]


def test_expired_referrals_return_nothing(idp, pipeline):
    """
    Slide 15: Expired referrals or over-broad queries return nothing.
    P-4180 was referred to Dr. Sharma, but expired on 2026-10-31.
    """
    dr_login = idp.login("DR_302")
    dr_token = dr_login["token"]

    res = pipeline.process_query("What is the pre-op clearance status for P-4180?", token=dr_token)
    assert "P-4180" not in res["telemetry"]["step3_retrieval"]["patients_in_scope"]
    assert "No accessible patient records found" in res["answer"]


def test_nurse_never_receives_identifiers_outside_assigned(idp, pipeline):
    """
    Slide 15: A nurse never receives identifiers outside assigned patients.
    Nurse Sarah (Ward 3) queries P-4180 in Ward 5 (Ortho).
    """
    nurse_login = idp.login("RN_201")
    nurse_token = nurse_login["token"]

    # Out of ward query
    res = pipeline.process_query("Give me patient P-4180's name, phone, and diagnosis.", token=nurse_token)
    assert "P-4180" not in res["telemetry"]["step3_retrieval"]["patients_in_scope"]
    assert "No accessible patient records found" in res["answer"]


def test_nurse_assigned_patient_has_identifiers_masked(idp, pipeline):
    """
    Slide 3 & 15: For assigned ward patient P-1042, Nurse receives clinical details but phone/SSN is masked.
    """
    nurse_login = idp.login("RN_201")
    nurse_token = nurse_login["token"]

    res = pipeline.process_query("Diagnosis and phone for P-1042?", token=nurse_token)
    assert res["outcome"] == "ALLOWED"
    assert "Hypertension" in res["answer"]
    assert "[MASKED" in res["answer"]
    assert "+1-555-0142" not in res["answer"]  # Raw phone must not be present
    assert "987-65-4321" not in res["answer"]  # SSN must not be present
