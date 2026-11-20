"""
Hospital Identity Provider (IdP) Mock Service.
Manages predefined personas, staff login, and emergency break-glass elevation.
"""

import os
import hmac
import hashlib
import sqlite3
import json
import logging
from typing import List, Dict, Any, Optional
from src.config import DB_PATH
from src.module1_identity_policy.tokens import issue_token, AuthenticationError

logger = logging.getLogger(__name__)

DEFAULT_PASSWORDS = {
    "CMO_501": "cmo@123",
    "DH_401": "dept@123",
    "DR_302": "doc@123",
    "RN_201": "nurse@123",
    "FD_101": "billing@123",
    "SYS_999": "admin@123"
}


def hash_password(password: str, salt: Optional[str] = None) -> str:
    """Hashes a password with a cryptographic salt using SHA-256."""
    if salt is None:
        salt = os.urandom(16).hex()
    hashed = hashlib.sha256((salt + password).encode("utf-8")).hexdigest()
    return f"{salt}${hashed}"


def verify_password(password: str, hashed_str: str) -> bool:
    """Verifies a plain password against the stored salt$hash string using constant-time comparison."""
    if not hashed_str or "$" not in hashed_str:
        return False
    salt, expected_hash = hashed_str.split("$", 1)
    actual_hash = hashlib.sha256((salt + password).encode("utf-8")).hexdigest()
    return hmac.compare_digest(actual_hash, expected_hash)


class IdPService:
    def __init__(self, db_path=DB_PATH):
        self.db_path = db_path
        self.ensure_password_schema()

    def ensure_password_schema(self):
        """Ensures password_hash column exists in personas and seeds demo credentials."""
        try:
            conn = sqlite3.connect(self.db_path)
            cur = conn.cursor()
            cur.execute("PRAGMA table_info(personas)")
            columns = [c[1] for c in cur.fetchall()]
            if "password_hash" not in columns:
                cur.execute("ALTER TABLE personas ADD COLUMN password_hash TEXT")

            for uid, pwd in DEFAULT_PASSWORDS.items():
                cur.execute("SELECT password_hash FROM personas WHERE user_id = ?", (uid,))
                row = cur.fetchone()
                if row and not row[0]:
                    h = hash_password(pwd)
                    cur.execute("UPDATE personas SET password_hash = ? WHERE user_id = ?", (h, uid))
            conn.commit()
            conn.close()
        except Exception as e:
            logger.warning(f"Could not verify password schema: {e}")

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

    def login(self, user_id: str, password: Optional[str] = None) -> Dict[str, Any]:
        """Authenticates user ID (and optional password) against IdP and returns a signed token."""
        persona = self.get_persona(user_id)
        if not persona:
            raise AuthenticationError(f"FAIL-CLOSED: Unknown user identity '{user_id}'. Request refused.")

        if password is not None:
            conn = sqlite3.connect(self.db_path)
            cur = conn.cursor()
            cur.execute("SELECT password_hash FROM personas WHERE user_id = ?", (user_id,))
            row = cur.fetchone()
            conn.close()
            stored_hash = row[0] if row else None

            if not stored_hash or not verify_password(password, stored_hash):
                raise AuthenticationError(f"FAIL-CLOSED: Invalid credentials for staff member '{user_id}'.")

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
