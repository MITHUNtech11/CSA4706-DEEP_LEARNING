"""
Command-Line Interactive Walkthrough for Secure Hospital RAG RBAC.
Demonstrates the 6 roles and pipeline enforcement without needing a browser.
"""

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from src.module1_identity_policy.idp_service import IdPService
from src.pipeline import RequestEnforcementPipeline


def main():
    print("=" * 65)
    print(" HOSPITAL RAG ROLE-BASED ACCESS CONTROL - CLI DEMO")
    print("=" * 65)

    idp = IdPService()
    pipeline = RequestEnforcementPipeline()
    personas = idp.list_personas()

    print("\nAvailable Staff Personas:")
    for idx, p in enumerate(personas, 1):
        print(f" {idx}. [{p['user_id']}] {p['name']} - {p['role']} (Level {p['level']}) - {p['department']}")

    # Let user select persona or run automatic demo
    print("\n--- Running Automated 3-Persona Demonstration ---")

    # Scenario 1: Nurse querying P-1042
    print("\n[SCENARIO 1] Nurse querying Ward 3 patient P-1042:")
    nurse_tok = idp.login("RN_201")["token"]
    res1 = pipeline.process_query("Diagnosis and phone for P-1042?", token=nurse_tok)
    print("Query:  'Diagnosis and phone for P-1042?'")
    print("Answer:\n" + res1["answer"])
    print(f"Step 2 Filters: {res1['telemetry']['step2_filters']['scope_desc']}")

    # Scenario 2: Doctor querying cross-department without referral
    print("\n[SCENARIO 2] Treating Doctor (Cardiology) querying Oncology patient P-3307:")
    dr_tok = idp.login("DR_302")["token"]
    res2 = pipeline.process_query("Show me diagnosis for P-3307.", token=dr_tok)
    print("Query:  'Show me diagnosis for P-3307.'")
    print("Answer:\n" + res2["answer"])

    # Scenario 3: Admin querying clinical data
    print("\n[SCENARIO 3] System Administrator attempting clinical query:")
    admin_tok = idp.login("SYS_999")["token"]
    res3 = pipeline.process_query("List all patient names and diagnoses.", token=admin_tok)
    print("Query:  'List all patient names and diagnoses.'")
    print("Answer:\n" + res3["answer"])

    # Scenario 4: Hash verification
    print("\n[SCENARIO 4] Verifying SHA-256 Audit Hash Chain:")
    valid, msg, steps = pipeline.audit_logger.verify_integrity()
    print(f"Result: {msg}")
    print(f"Chain depth: {len(steps)} entries verified.\n")


if __name__ == "__main__":
    main()
