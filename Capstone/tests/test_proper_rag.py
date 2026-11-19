"""
Tests for Proper Clinical RAG System, Grounded Extraction, and Intent Resolution.
"""

import pytest
from fastapi.testclient import TestClient
from src.api.app import app
from src.module1_identity_policy.idp_service import IdPService
from src.pipeline import RequestEnforcementPipeline


@pytest.fixture
def client():
    return TestClient(app)


@pytest.fixture
def idp():
    return IdPService()


@pytest.fixture
def pipeline():
    return RequestEnforcementPipeline()


def test_conversational_query_does_not_dump_patient(idp, pipeline):
    """
    Verifies conversational queries ('hello', 'who are you', 'help') respond
    professionally without dumping irrelevant patient records (Eleanor Vance).
    """
    tok = idp.login("DR_302")["token"]
    res = pipeline.process_query("Hello, who are you and what can you do?", token=tok)

    assert res["outcome"] == "ALLOWED"
    assert "Hospital Clinical RAG Assistant" in res["answer"]
    assert "Treating Doctor" in res["answer"]
    # Must NOT dump arbitrary patient records
    assert "Eleanor Vance" not in res["answer"]
    assert "P-1042" not in res["answer"]
    assert res["telemetry"]["step3_retrieval"]["documents_found"] == 0


def test_vital_signs_grounded_extraction(idp, pipeline):
    """
    Verifies that asking for vital signs extracts actual blood pressure and vitals.
    """
    tok = idp.login("RN_201")["token"]  # Nurse assigned to Ward 3 (P-1042)
    res = pipeline.process_query("What are the vital signs and blood pressure for P-1042?", token=tok)

    assert res["outcome"] == "ALLOWED"
    assert "Vital Signs" in res["answer"]
    assert "BP" in res["answer"]
    assert "142/88" in res["answer"]
    assert "SpO2" in res["answer"]


def test_patient_name_resolution(idp, pipeline):
    """
    Verifies natural language name matching ('Eleanor Vance' -> P-1042, 'Sophia Thorne' -> P-3307).
    """
    doc_tok = idp.login("DR_302")["token"]
    res = pipeline.process_query("What is the diagnosis for Eleanor Vance?", token=doc_tok)

    assert res["outcome"] == "ALLOWED"
    assert "Hypertension" in res["answer"] or "aortic stenosis" in res["answer"]


def test_clinical_synonym_retrieval(idp, pipeline):
    """
    Verifies clinical synonym expansion ('heart condition' retrieves Cardiology notes/diagnosis).
    """
    doc_tok = idp.login("DR_302")["token"]
    res = pipeline.process_query("Show me heart condition and cardiac notes for P-1042", token=doc_tok)

    assert res["outcome"] == "ALLOWED"
    assert "Hypertension" in res["answer"] or "aortic" in res["answer"] or "Clinical Note" in res["answer"]


def test_out_of_scope_name_query_refused(idp, pipeline):
    """
    Nurse querying an Oncology ICU patient by name ('Sophia Thorne') must be refused.
    """
    nurse_tok = idp.login("RN_201")["token"]
    res = pipeline.process_query("Give me medical details for Sophia Thorne in Oncology ICU", token=nurse_tok)

    assert res["outcome"] == "ALLOWED"  # Graceful refusal in answer
    assert "outside permitted scope" in res["answer"] or "No accessible patient records found" in res["answer"]


def test_poppins_font_and_chat_assets(client):
    """
    Verifies that Poppins font is referenced and portal common JS contains typing indicators.
    """
    res = client.get("/portal/doctor")
    assert res.status_code == 200
    assert "family=Poppins" in res.text

    css_res = client.get("/style.css")
    assert "Poppins" in css_res.text
    assert "typing-bubble" in css_res.text
    assert "typingBounce" in css_res.text

    js_res = client.get("/portal_common.js")
    assert "showTypingIndicator" in js_res.text
    assert "formatMarkdown" in js_res.text
    assert "resetChatDisplay" in js_res.text
