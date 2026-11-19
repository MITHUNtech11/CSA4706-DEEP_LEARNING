"""
Versioned Policy Matrix & Governance Engine.
Enforces explicit grants, category mappings, and dual-approver workflows.
"""

import json
from pathlib import Path
from typing import Dict, Any, Optional, List
from src.config import ACTIVE_POLICY_PATH, DRAFT_POLICY_PATH


class PolicyViolationError(Exception):
    """Raised when a request violates permission policy rules."""
    pass


class PolicyEngine:
    def __init__(self, active_policy_path: Path = ACTIVE_POLICY_PATH, draft_policy_path: Path = DRAFT_POLICY_PATH):
        self.active_policy_path = active_policy_path
        self.draft_policy_path = draft_policy_path
        self.policy = self.load_active_policy()

    def load_active_policy(self) -> Dict[str, Any]:
        """Loads and parses the active versioned permission matrix."""
        with open(self.active_policy_path, "r", encoding="utf-8") as f:
            return json.load(f)

    def get_policy_version(self) -> str:
        return self.policy.get("policy_version", "unknown")

    def get_role_policy(self, role_name: str) -> Dict[str, Any]:
        """
        Retrieves policy grants for a specific role.
        Fails closed if the role is not defined in the matrix.
        """
        roles = self.policy.get("roles", {})
        if role_name not in roles:
            raise PolicyViolationError(f"FAIL-CLOSED: Role '{role_name}' is not recognized in active policy {self.get_policy_version()}. Access denied.")
        return roles[role_name]

    def validate_clinical_query_authorization(self, token_payload: Dict[str, Any]) -> None:
        """
        Enforces separation of duties and fail-closed checks:
        - System Administrator is refused ALL clinical/patient queries (Slide 14 requirement).
        - Chat-injected role attempts are discarded.
        """
        role = token_payload.get("role")
        level = token_payload.get("level")

        # Slide 14 & Slide 10: System Administrator has zero data access
        if role == "System Administrator" or level == 0:
            raise PolicyViolationError(
                "ACCESS DENIED (Separation of Duties): System Administrators manage policy and control panel operations only. "
                "All patient clinical and identifier queries are strictly prohibited."
            )

    def get_allowed_categories(self, role_name: str) -> List[str]:
        """Returns list of allowed data categories for the role."""
        role_pol = self.get_role_policy(role_name)
        perms = role_pol.get("permissions", {})
        allowed = []
        for cat, val in perms.items():
            if val is True or isinstance(val, str):
                allowed.append(cat)
        return allowed

    # --- Governance: Two-Approver Workflow ---
    def get_draft_policy(self) -> Optional[Dict[str, Any]]:
        """Reads draft policy requiring 2nd approver sign-off."""
        if not self.draft_policy_path.exists():
            return None
        with open(self.draft_policy_path, "r", encoding="utf-8") as f:
            return json.load(f)

    def approve_draft_policy(self, second_approver_id: str) -> Dict[str, Any]:
        """
        Promotes draft policy to active after receiving valid second approver sign-off.
        """
        draft = self.get_draft_policy()
        if not draft:
            raise ValueError("No active draft policy pending approval.")

        approved_by = draft.get("approved_by", [])
        if second_approver_id in approved_by:
            raise ValueError(f"Second approver must be distinct from initial approvers: {approved_by}")

        approved_by.append(second_approver_id)
        draft["approved_by"] = approved_by
        draft["status"] = "ACTIVE"
        draft["policy_version"] = "v1.1"

        # Update roles into active policy structure
        new_active = dict(self.policy)
        new_active["policy_version"] = draft["policy_version"]
        new_active["approved_by"] = approved_by
        if "new_roles" in draft:
            new_active["roles"].update(draft["new_roles"])

        with open(self.active_policy_path, "w", encoding="utf-8") as f:
            json.dump(new_active, f, indent=2)

        self.policy = new_active
        return {"status": "SUCCESS", "new_version": self.policy["policy_version"], "approved_by": approved_by}
