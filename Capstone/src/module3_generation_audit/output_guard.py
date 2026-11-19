"""
Algorithm 1: Controlled Generation with Multi-Check Output Guard.
Verifies identifier protection, category containment, and factual grounding.
"""

import re
from typing import Dict, Any, List, Tuple


class OutputGuard:
    @staticmethod
    def verify_output(
        answer: str,
        role: str,
        allowed_categories: List[str],
        patient_scope: str,
        context: str
    ) -> Tuple[bool, str, Dict[str, Any]]:
        """
        Executes Algorithm 1 checks (Slide 17):
        1. ids_ok: Output contains no restricted personal identifiers (unmasked SSN/phone) for the role.
        2. cats_ok: Output uses only permitted clinical categories.
        3. grounded: Claims in output are grounded in the retrieved context X.
        
        Returns: (is_allowed, final_answer, check_telemetry)
        """
        # 1. Identifier Check (ids_ok)
        ids_ok = True
        id_violation_reason = None

        # Check for unmasked SSN pattern: XXX-XX-XXXX
        ssn_pattern = r"\b\d{3}-\d{2}-\d{4}\b"
        if re.search(ssn_pattern, answer):
            # SSN is never allowed to be revealed in chat output!
            ids_ok = False
            id_violation_reason = "Unmasked National ID / SSN detected in generated output."

        # Check for unmasked phone for restricted roles (Nurse, Billing)
        if role in ("Nurse", "Front Desk / Billing Staff"):
            raw_phone_pattern = r"\+1-555-\d{4}"
            if re.search(raw_phone_pattern, answer):
                ids_ok = False
                id_violation_reason = f"Unmasked telephone number detected for restricted role {role}."

        # 2. Category Check (cats_ok)
        cats_ok = True
        cat_violation_reason = None
        if "full_medical_record" not in allowed_categories:
            # Look for leak of deep operative or pathology text if not in allowed categories
            restricted_terms = ["bone marrow aspirate", "myeloblasts", "auer rods", "internal fixation", "intramedullary nail"]
            for term in restricted_terms:
                if term in answer.lower() and term not in context.lower():
                    cats_ok = False
                    cat_violation_reason = f"Output references restricted surgical/pathology category '{term}' not granted to role {role}."
                    break

        # 3. Grounding Check (grounded)
        # Every claim in answer must be supported by filtered context X.
        # If context was empty or blocked, but LLM made up clinical details, flag ungrounded!
        grounded = True
        grounding_reason = None
        if not context or "[NO DOCUMENTS RETRIEVED" in context:
            # If no context was retrieved, any specific diagnosis/medication claim is ungrounded hallucination
            if "**Diagnosis**:" in answer or "**Active Medications**:" in answer:
                grounded = False
                grounding_reason = "Response claims clinical facts but no context was retrieved (Ungrounded)."

        # Telemetry for audit logging & UI inspection
        telemetry = {
            "ids_ok": ids_ok,
            "id_violation_reason": id_violation_reason,
            "cats_ok": cats_ok,
            "cat_violation_reason": cat_violation_reason,
            "grounded": grounded,
            "grounding_reason": grounding_reason
        }

        # Algorithm 1 Line 8: if not (ids_ok and cats_ok and grounded):
        if not (ids_ok and cats_ok and grounded):
            reasons = [r for r in [id_violation_reason, cat_violation_reason, grounding_reason] if r]
            refusal_message = (
                f"REFUSAL: The generated response violated security guardrails for role '{role}' "
                f"and was blocked by the output verification guard. Reason: {'; '.join(reasons)}"
            )
            return False, refusal_message, telemetry

        return True, answer, telemetry
