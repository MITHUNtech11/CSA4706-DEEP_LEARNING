"""
Pre-Filtered Vector Store for Clinical RAG.
Enforces deterministic metadata filtering BEFORE semantic search ranking.
Unauthorized documents are never embedded into top-k or returned.
"""

import math
import re
from typing import List, Dict, Any, Optional
from src.config import DB_PATH
import sqlite3


def _tokenize(text: str) -> List[str]:
    """Simple lowercase alphanumeric word tokenizer."""
    return re.findall(r"\b[a-zA-Z0-9]+\b", text.lower())


def _compute_tf(tokens: List[str]) -> Dict[str, float]:
    tf = {}
    for t in tokens:
        tf[t] = tf.get(t, 0.0) + 1.0
    total = len(tokens) or 1
    return {k: v / total for k, v in tf.items()}


def _cosine_similarity(vec1: Dict[str, float], vec2: Dict[str, float]) -> float:
    common = set(vec1.keys()) & set(vec2.keys())
    if not common:
        return 0.0
    dot = sum(vec1[k] * vec2[k] for k in common)
    mag1 = math.sqrt(sum(v * v for v in vec1.values()))
    mag2 = math.sqrt(sum(v * v for v in vec2.values()))
    if mag1 == 0 or mag2 == 0:
        return 0.0
    return dot / (mag1 * mag2)


class PreFilteredVectorStore:
    """
    In-memory embedded vector store with deterministic pre-retrieval metadata filtering.
    """
    def __init__(self, db_path=DB_PATH):
        self.db_path = db_path
        self.documents: List[Dict[str, Any]] = []
        self._load_and_index_documents()

    def _load_and_index_documents(self):
        """Indexes all clinical notes and patient records with explicit security metadata."""
        conn = sqlite3.connect(self.db_path)
        cur = conn.cursor()

        # Index clinical notes
        cur.execute("""
            SELECT cn.note_id, cn.patient_id, cn.category, cn.title, cn.content, 
                   p.department, p.ward
            FROM clinical_notes cn
            JOIN patients p ON cn.patient_id = p.patient_id
        """)
        rows = cur.fetchall()
        for r in rows:
            text = f"{r[3]}: {r[4]}"
            self.documents.append({
                "doc_id": r[0],
                "patient_id": r[1],
                "category": r[2],  # "full_medical_record"
                "department": r[5],
                "ward": r[6],
                "text": text,
                "tokens": _tokenize(text),
                "vector": _compute_tf(_tokenize(text))
            })

        # Index general clinical patient summaries
        cur.execute("SELECT patient_id, full_name, department, ward, diagnosis, allergies, active_medications, vital_signs FROM patients")
        p_rows = cur.fetchall()
        for pr in p_rows:
            summary = (
                f"Patient {pr[0]} ({pr[1]}), Dept: {pr[2]}, Ward: {pr[3]}. "
                f"Diagnosis: {pr[4]}. Allergies: {pr[5]}. Medications: {pr[6]}. Vitals: {pr[7]}."
            )
            self.documents.append({
                "doc_id": f"SUMMARY-{pr[0]}",
                "patient_id": pr[0],
                "category": "general_clinical_details",
                "department": pr[2],
                "ward": pr[3],
                "text": summary,
                "tokens": _tokenize(summary),
                "vector": _compute_tf(_tokenize(summary))
            })

        conn.close()

    def search(
        self,
        query: str,
        allowed_patient_ids: Optional[List[str]] = None,
        allowed_categories: Optional[List[str]] = None,
        department: Optional[str] = None,
        ward: Optional[str] = None,
        top_k: int = 4
    ) -> List[Dict[str, Any]]:
        """
        Executes pre-retrieval security filter:
        Filters documents FIRST. Only authorized candidates are evaluated for semantic similarity.
        """
        query_vec = _compute_tf(_tokenize(query))

        candidates = []
        for doc in self.documents:
            # 1. Enforce Patient Scope Filter
            if allowed_patient_ids is not None:
                if doc["patient_id"] not in allowed_patient_ids:
                    continue

            # 2. Enforce Category Filter
            if allowed_categories is not None:
                if doc["category"] not in allowed_categories:
                    continue

            # 3. Enforce Department Scope Filter (e.g. Dept Head)
            if department and doc["department"] != department:
                continue

            # 4. Enforce Ward Scope Filter (e.g. Nurse)
            if ward and doc["ward"] != ward:
                continue

            candidates.append(doc)

        if not candidates:
            return []

        # Rank candidates by semantic cosine similarity
        scored = []
        for doc in candidates:
            score = _cosine_similarity(query_vec, doc["vector"])
            scored.append((score, doc))

        # Sort descending by score
        scored.sort(key=lambda x: x[0], reverse=True)

        results = []
        for score, doc in scored[:top_k]:
            results.append({
                "doc_id": doc["doc_id"],
                "patient_id": doc["patient_id"],
                "category": doc["category"],
                "department": doc["department"],
                "ward": doc["ward"],
                "text": doc["text"],
                "score": round(score, 4)
            })

        return results
