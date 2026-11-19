"""
Pre-Retrieval Filter Builder.
Translates JWT claims and active policy into deterministic SQL & Vector DB filters.
Enforces the Fail-Closed security invariant.
"""

from typing import Dict, Any, List, Optional
from datetime import datetime, timezone
from src.module1_identity_policy.policy_engine import PolicyEngine, PolicyViolationError
from src.module2_enforced_retrieval.database import HospitalRepository


class FilterBuilderError(Exception):
    """Raised when a pre-retrieval filter cannot be safely constructed."""
    pass


class FilterBuilder:
    def __init__(self, policy_engine: PolicyEngine, repository: HospitalRepository):
        self.policy_engine = policy_engine
        self.repository = repository

    def build_filters(self, token_payload: Dict[str, Any]) -> Dict[str, Any]:
        """
        Builds retrieval filters: allowed_patient_ids, allowed_categories, department, ward, field_masks.
        Fail-closed: If role or scope is ambiguous, raises FilterBuilderError.
        """
        role = token_payload.get("role")
        level = token_payload.get("level")
        user_id = token_payload.get("user_id")
        department = token_payload.get("department")
        assigned_ward = token_payload.get("assigned_ward")
        is_break_glass = token_payload.get("is_break_glass", False)

        if not role or level is None or not user_id:
            raise FilterBuilderError("FAIL-CLOSED: Missing essential identity claims in token.")

        # 1. Admin check (Slide 14: System admin is refused all data queries)
        if role == "System Administrator" or level == 0:
            raise PolicyViolationError("ACCESS DENIED: System Administrator has zero patient data access privileges.")

        # 2. Emergency Break-Glass Override
        if is_break_glass:
            return {
                "role": role,
                "level": level,
                "allowed_patient_ids": None,  # All patients accessible in emergency
                "allowed_categories": ["full_medical_record", "general_clinical_details", "personal_identifiers"],
                "department": None,
                "ward": None,
                "field_masks": [],
                "is_break_glass": True,
                "scope_desc": "EMERGENCY_BREAK_GLASS_ALL_PATIENTS"
            }

        # 3. Retrieve Role Policy Matrix
        role_pol = self.policy_engine.get_role_policy(role)
        scope_type = role_pol.get("scope")

        # Determine allowed categories
        allowed_categories = []
        perms = role_pol.get("permissions", {})
        if perms.get("full_medical_record") in (True, "ASSIGNED_OR_REFERRAL"):
            allowed_categories.append("full_medical_record")
        if perms.get("general_clinical_details") in (True, "ASSIGNED_OR_REFERRAL", "BILLING_ONLY"):
            allowed_categories.append("general_clinical_details")

        field_masks = list(role_pol.get("field_masking", []))

        # 4. Resolve Patient Scope
        allowed_patient_ids: Optional[List[str]] = None
        filter_dept: Optional[str] = None
        filter_ward: Optional[str] = None

        if scope_type == "ALL_PATIENTS":  # Level 5 CMO
            allowed_patient_ids = None  # No patient restriction
            scope_desc = "All hospital patients (Clinical Audit Scope)"

        elif scope_type == "OWN_DEPARTMENT":  # Level 4 Department Head
            filter_dept = department
            # Get patient IDs in this department
            dept_patients = self.repository.query_patients_scoped(department=department)
            allowed_patient_ids = [p["patient_id"] for p in dept_patients]
            scope_desc = f"Department '{department}' patients only"

        elif scope_type == "ASSIGNED_AND_REFERRED":  # Level 3 Treating Doctor
            # A doctor can ONLY access primary care-team patients + active valid referrals
            care_patients = self.repository.get_care_team_patients_for_doctor(user_id)
            active_referrals = self.repository.get_active_referrals_for_doctor(user_id)
            combined_patients = list(set(care_patients + active_referrals))
            allowed_patient_ids = combined_patients
            scope_desc = f"Assigned care team ({len(care_patients)}) + Active referrals ({len(active_referrals)})"

        elif scope_type == "ASSIGNED_WARD":  # Level 2 Nurse
            filter_ward = assigned_ward
            ward_patients = self.repository.query_patients_scoped(ward=assigned_ward)
            allowed_patient_ids = [p["patient_id"] for p in ward_patients]
            scope_desc = f"Assigned ward '{assigned_ward}' patients only"

        elif scope_type == "TASK_SPECIFIC":  # Level 1 Front Desk / Billing
            # Task-specific: allowed registration/appointment queries
            allowed_patient_ids = None
            scope_desc = "Task-specific appointment and billing lookups"

        else:
            raise FilterBuilderError(f"FAIL-CLOSED: Unknown or unhandled scope type '{scope_type}'.")

        return {
            "role": role,
            "level": level,
            "allowed_patient_ids": allowed_patient_ids,
            "allowed_categories": allowed_categories,
            "department": filter_dept,
            "ward": filter_ward,
            "field_masks": field_masks,
            "is_break_glass": False,
            "scope_desc": scope_desc
        }
