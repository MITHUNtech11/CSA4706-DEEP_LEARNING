"""
Hospital Identity Provider (IdP) Mock Service.
Manages predefined personas, staff login, and emergency break-glass elevation.
"""

import sqlite3
import json
from typing import List, Dict, Any, Optional
from src.config import DB_PATH
from src.module1_identity_policy.tokens import issue_token, AuthenticationError


class IdPService:
    def __init__(self, db_path=DB_PATH):
        self.db_path = db_path

    def list_personas(self) -> List[Dict[str, Any]]:
        """Returns all predefined hospital personas for demo & testing."""
        conn = sqlite3.connect(self.db_path)
        cur = conn.cursor()
        cur.execute("SELECT user_id, name, role, level, department, assigned_ward, assigned_patients, description FROM personas ORDER BY level DESC")
        rows = cur.fetchall()
        conn.close()

        personas = []
        for r in rows:
            personas.append({
                "user_id": r[0],
                "name": r[1],
                "role": r[2],
                "level": r[3],
                "department": r[4],
                "assigned_ward": r[5],
                "assigned_patients": json.loads(r[6]),
                "description": r[7]
            })
        return personas

    def get_persona(self, user_id: str) -> Optional[Dict[str, Any]]:
        """Retrieves a persona by user_id."""
        for p in self.list_personas():
            if p["user_id"] == user_id:
                return p
        return None

    def login(self, user_id: str) -> Dict[str, Any]:
        """Authenticates user ID against IdP and returns a signed token."""
        persona = self.get_persona(user_id)
        if not persona:
            raise AuthenticationError(f"FAIL-CLOSED: Unknown user identity '{user_id}'. Request refused.")

        token = issue_token(
            user_id=persona["user_id"],
            name=persona["name"],
            role=persona["role"],
            level=persona["level"],
            department=persona["department"],
            assigned_ward=persona["assigned_ward"],
            assigned_patients=persona["assigned_patients"],
            is_break_glass=False
        )

        return {
            "token": token,
            "persona": persona,
            "expires_in_minutes": 60,
            "token_type": "Bearer"
        }

    def issue_break_glass_token(self, user_id: str, justification: str) -> Dict[str, Any]:
        """
        Issues an emergency elevated break-glass token.
        Requires justification and sets 15-minute strict timeout.
        """
        if not justification or len(justification.strip()) < 10:
            raise ValueError("Emergency break-glass access requires a detailed clinical justification (minimum 10 characters).")

        persona = self.get_persona(user_id)
        if not persona:
            raise AuthenticationError(f"FAIL-CLOSED: Unknown user identity '{user_id}'.")

        token = issue_token(
            user_id=persona["user_id"],
            name=f"{persona['name']} [BREAK-GLASS EMERGENCY]",
            role=persona["role"],
            level=persona["level"],
            department="HOSPITAL_WIDE_EMERGENCY",
            assigned_ward="ALL",
            assigned_patients=["ALL"],
            is_break_glass=True,
            break_glass_reason=justification
        )

        return {
            "token": token,
            "user_id": user_id,
            "is_break_glass": True,
            "justification": justification,
            "expires_in_minutes": 15,
            "token_type": "Bearer"
        }
