"""
Dynamic Field-Level Redaction and Masking Engine.
Redacts personal identifiers and confidential attributes according to role policy.
"""

from typing import Dict, Any, List


class FieldMasker:
    @staticmethod
    def mask_patient_record(patient: Dict[str, Any], field_masks: List[str], role: str) -> Dict[str, Any]:
        """
        Clones patient dict and applies redaction to fields listed in field_masks.
        """
        masked = dict(patient)

        # Mask SSN by default for clinical chat safety
        raw_nid = str(masked.get("national_id", ""))
        last4 = raw_nid[-4:] if len(raw_nid) >= 4 else "XXXX"
        masked["national_id"] = f"***-**-{last4}"

        # Apply specific field masks
        for field in field_masks:
            if field in masked:
                masked[field] = f"[MASKED - RESTRICTED FOR {role.upper()}]"

        # If role is nurse or billing, ensure phone, address, and SSN are strictly masked
        if role in ("Nurse", "Front Desk / Billing Staff"):
            masked["national_id"] = "[MASKED - SSN/ID RESTRICTED]"
            masked["home_address"] = "[MASKED - ADDRESS RESTRICTED]"
            masked["phone_number"] = "[MASKED - CONTACT RESTRICTED]"

        # If Front Desk / Billing, clinical diagnosis and meds must also be redacted
        if role == "Front Desk / Billing Staff":
            masked["diagnosis"] = "[NOT PERMITTED FOR BILLING ROLE]"
            masked["active_medications"] = "[NOT PERMITTED FOR BILLING ROLE]"
            masked["clinical_notes"] = "[NOT PERMITTED FOR BILLING ROLE]"

        return masked

    @staticmethod
    def format_patient_context(patient: Dict[str, Any], role_policy: Dict[str, Any], role: str) -> str:
        """
        Formats a patient record into structured clinical context respecting role restrictions.
        """
        perms = role_policy.get("permissions", {})
        has_full_record = perms.get("full_medical_record") in (True, "ASSIGNED_OR_REFERRAL")
        has_general = perms.get("general_clinical_details") in (True, "ASSIGNED_OR_REFERRAL", "BILLING_ONLY")

        lines = [
            f"=== PATIENT RECORD: {patient.get('patient_id')} ===",
            f"Name: {patient.get('full_name')}",
            f"Department: {patient.get('department')} | Ward: {patient.get('ward')} | Bed: {patient.get('bed_number')}",
            f"Phone: {patient.get('phone_number')}",
            f"National ID: {patient.get('national_id')}",
        ]

        if has_general and role != "Front Desk / Billing Staff":
            lines.extend([
                f"Diagnosis: {patient.get('diagnosis')}",
                f"Allergies: {patient.get('allergies')}",
                f"Active Medications: {patient.get('active_medications')}",
                f"Vital Signs: {patient.get('vital_signs')}",
            ])
        elif role == "Front Desk / Billing Staff":
            lines.extend([
                f"Billing Balance: {patient.get('billing_balance')}",
                f"Appointment Status: {patient.get('appointment_status')}",
                "Clinical Notes / Diagnosis: [NOT PERMITTED FOR THIS ROLE]"
            ])

        if not has_full_record:
            lines.append("Full Medical Record (Notes/Imaging/Labs): [NOT PERMITTED FOR THIS ROLE - DENIED BY DEFAULT]")

        return "\n".join(lines)
