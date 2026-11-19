"""
Relational Database Repository for Patient Records, Referrals, and Care Teams.
Enforces pre-retrieval SQL filtering based on role scope and referral validity.
"""

import sqlite3
from datetime import datetime, timezone
from typing import List, Dict, Any, Optional
from src.config import DB_PATH


class HospitalRepository:
    def __init__(self, db_path=DB_PATH):
        self.db_path = db_path

    def _get_connection(self):
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        return conn

    def get_patient_by_id(self, patient_id: str) -> Optional[Dict[str, Any]]:
        conn = self._get_connection()
        cur = conn.cursor()
        cur.execute("SELECT * FROM patients WHERE patient_id = ?", (patient_id,))
        row = cur.fetchone()
        conn.close()
        return dict(row) if row else None

    def get_care_team_patients_for_doctor(self, doctor_id: str) -> List[str]:
        """Returns patient IDs assigned to the doctor's primary care team."""
        conn = self._get_connection()
        cur = conn.cursor()
        cur.execute("SELECT patient_id FROM care_teams WHERE doctor_id = ?", (doctor_id,))
        rows = cur.fetchall()
        conn.close()
        return [r["patient_id"] for r in rows]

    def get_active_referrals_for_doctor(self, doctor_id: str, check_time: Optional[datetime] = None) -> List[str]:
        """
        Returns patient IDs actively referred to doctor_id where valid_from <= now <= valid_until.
        Expired referrals are strictly excluded!
        """
        now = check_time or datetime.now(timezone.utc)
        now_iso = now.isoformat()

        conn = self._get_connection()
        cur = conn.cursor()
        cur.execute("""
            SELECT patient_id FROM referrals 
            WHERE to_doctor_id = ? 
              AND valid_from <= ? 
              AND valid_until >= ?
              AND status = 'ACTIVE'
        """, (doctor_id, now_iso, now_iso))
        rows = cur.fetchall()
        conn.close()
        return [r["patient_id"] for r in rows]

    def query_patients_scoped(
        self,
        allowed_patient_ids: Optional[List[str]] = None,
        department: Optional[str] = None,
        ward: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        """
        Executes pre-filtered SQL query.
        Returns ONLY patients satisfying the scope filters.
        """
        conn = self._get_connection()
        cur = conn.cursor()

        query = "SELECT * FROM patients WHERE 1=1"
        params = []

        if allowed_patient_ids is not None:
            if not allowed_patient_ids:
                conn.close()
                return []  # Empty allowed scope -> return nothing
            placeholders = ",".join(["?"] * len(allowed_patient_ids))
            query += f" AND patient_id IN ({placeholders})"
            params.extend(allowed_patient_ids)

        if department:
            query += " AND department = ?"
            params.append(department)

        if ward:
            query += " AND ward = ?"
            params.append(ward)

        cur.execute(query, params)
        rows = cur.fetchall()
        conn.close()
        return [dict(r) for r in rows]

    def query_clinical_notes_scoped(
        self,
        patient_ids: List[str],
        allowed_categories: List[str]
    ) -> List[Dict[str, Any]]:
        """
        Retrieves clinical notes strictly restricted by allowed patient IDs and categories.
        """
        if not patient_ids or not allowed_categories:
            return []

        conn = self._get_connection()
        cur = conn.cursor()

        p_placeholders = ",".join(["?"] * len(patient_ids))
        c_placeholders = ",".join(["?"] * len(allowed_categories))

        query = f"""
            SELECT * FROM clinical_notes 
            WHERE patient_id IN ({p_placeholders}) 
              AND category IN ({c_placeholders})
        """
        params = patient_ids + allowed_categories

        cur.execute(query, params)
        rows = cur.fetchall()
        conn.close()
        return [dict(r) for r in rows]
