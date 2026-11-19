"""
Pre-Filtered Hybrid Vector & BM25 Store for Clinical RAG.
Enforces deterministic metadata filtering BEFORE semantic search ranking.
Unauthorized documents are never embedded into top-k or returned.
"""

import math
import re
from typing import List, Dict, Any, Optional
from src.config import DB_PATH
import sqlite3

# Clinical synonym expansions for medical domain grounding
CLINICAL_SYNONYMS = {
    "heart": ["cardiac", "cardiology", "aortic", "stenosis", "hypertension", "myocardial", "infarction"],
    "cardiac": ["heart", "cardiology", "aortic", "stenosis", "hypertension", "dyspnea", "echo"],
    "vitals": ["vital", "signs", "bp", "blood", "pressure", "heart", "rate", "pulse", "spo2", "temperature"],
    "vital": ["vitals", "signs", "bp", "pulse", "rate", "temperature"],
    "bp": ["blood", "pressure", "hypertension", "vital", "signs"],
    "meds": ["medications", "active_medications", "drugs", "prescription", "dosage"],
    "medication": ["medications", "drugs", "prescriptions"],
    "allergy": ["allergies", "allergic", "penicillin", "sulfa", "aspirin"],
    "notes": ["clinical", "notes", "progress", "consult", "operative", "echocardiogram", "biopsy"],
    "echo": ["echocardiogram", "aortic", "cardiology", "ultrasound"],
    "surgery": ["surgical", "operative", "operation", "biopsy", "resection"],
    "chemo": ["chemotherapy", "oncology", "doxorubicin", "cardiotoxicity"],
}

STOPWORDS = {
    "a", "an", "the", "in", "on", "of", "for", "to", "at", "by", "with", 
    "from", "and", "or", "is", "are", "was", "were", "be", "this", "that", 
    "me", "i", "you", "he", "she", "it", "we", "they", "what", "which", 
    "who", "whom", "can", "could", "would", "should", "do", "does", "did", 
    "please", "tell", "show", "give", "get"
}


def _tokenize(text: str) -> List[str]:
    """Lowercase alphanumeric word tokenizer excluding standard English stopwords."""
    words = re.findall(r"\b[a-zA-Z0-9_-]+\b", text.lower())
    return [w for w in words if w not in STOPWORDS or len(w) > 2]


def _expand_query_tokens(tokens: List[str]) -> List[str]:
    """Expands query tokens with clinical synonyms for semantic retrieval recall."""
    expanded = list(tokens)
    for t in tokens:
        if t in CLINICAL_SYNONYMS:
            expanded.extend(CLINICAL_SYNONYMS[t])
    return expanded


class PreFilteredVectorStore:
    """
    In-memory hybrid BM25 and semantic vector store with deterministic pre-retrieval security filtering.
    """
    def __init__(self, db_path=DB_PATH):
        self.db_path = db_path
        self.documents: List[Dict[str, Any]] = []
        self.doc_lengths: List[int] = []
        self.avg_doc_len: float = 1.0
        self.idf: Dict[str, float] = {}
        self._load_and_index_documents()

    def _load_and_index_documents(self):
        """Indexes all clinical notes and patient records with explicit security metadata."""
        conn = sqlite3.connect(self.db_path)
        cur = conn.cursor()

        # 1. Index clinical notes (unstructured)
        cur.execute("""
            SELECT cn.note_id, cn.patient_id, cn.category, cn.title, cn.content, 
                   p.full_name, p.department, p.ward
            FROM clinical_notes cn
            JOIN patients p ON cn.patient_id = p.patient_id
        """)
        rows = cur.fetchall()
        for r in rows:
            text = f"Patient: {r[5]} ({r[1]}). Category: {r[2]}. Note Title: {r[3]}. Content: {r[4]}"
            tokens = _tokenize(text)
            self.documents.append({
                "doc_id": r[0],
                "patient_id": r[1],
                "patient_name": r[5],
                "category": r[2],  # "full_medical_record"
                "department": r[6],
                "ward": r[7],
                "title": r[3],
                "text": text,
                "tokens": tokens,
            })

        # 2. Index structured clinical patient summaries
        cur.execute("SELECT patient_id, full_name, department, ward, bed_number, diagnosis, allergies, active_medications, vital_signs, billing_balance, appointment_status FROM patients")
        p_rows = cur.fetchall()
        for pr in p_rows:
            summary = (
                f"Patient Profile: {pr[0]} ({pr[1]}). Department: {pr[2]}, Ward: {pr[3]}, Bed: {pr[4]}. "
                f"Diagnosis: {pr[5]}. Allergies: {pr[6]}. Active Medications: {pr[7]}. "
                f"Vital Signs: {pr[8]}. Billing Balance: {pr[9]}. Appointment: {pr[10]}."
            )
            tokens = _tokenize(summary)
            self.documents.append({
                "doc_id": f"SUMMARY-{pr[0]}",
                "patient_id": pr[0],
                "patient_name": pr[1],
                "category": "general_clinical_details",
                "department": pr[2],
                "ward": pr[3],
                "title": f"Summary for {pr[1]}",
                "text": summary,
                "tokens": tokens,
            })

        conn.close()

        # Compute corpus statistics for BM25
        n_docs = len(self.documents)
        if n_docs > 0:
            self.doc_lengths = [len(d["tokens"]) for d in self.documents]
            self.avg_doc_len = sum(self.doc_lengths) / n_docs

            # Document frequencies
            df: Dict[str, int] = {}
            for d in self.documents:
                unique_terms = set(d["tokens"])
                for term in unique_terms:
                    df[term] = df.get(term, 0) + 1

            # Compute smoothed IDF
            for term, count in df.items():
                self.idf[term] = math.log(1.0 + (n_docs - count + 0.5) / (count + 0.5))

    def _score_bm25(self, query_tokens: List[str], doc: Dict[str, Any], k1: float = 1.5, b: float = 0.75) -> float:
        """Computes Okapi BM25 score for a candidate document."""
        doc_tokens = doc["tokens"]
        doc_len = len(doc_tokens)
        if doc_len == 0 or not query_tokens:
            return 0.0

        # Term counts in document
        term_counts: Dict[str, int] = {}
        for t in doc_tokens:
            term_counts[t] = term_counts.get(t, 0) + 1

        score = 0.0
        for q in query_tokens:
            if q in term_counts:
                freq = term_counts[q]
                idf = self.idf.get(q, 0.5)
                # BM25 term weight
                denom = freq + k1 * (1.0 - b + b * (doc_len / self.avg_doc_len))
                score += idf * (freq * (k1 + 1.0)) / (denom if denom > 0 else 1.0)
        return score

    def search(
        self,
        query: str,
        allowed_patient_ids: Optional[List[str]] = None,
        allowed_categories: Optional[List[str]] = None,
        department: Optional[str] = None,
        ward: Optional[str] = None,
        top_k: int = 4,
        min_score: float = 0.01
    ) -> List[Dict[str, Any]]:
        """
        Executes pre-retrieval security filter:
        Filters documents FIRST. Only authorized candidates are evaluated for semantic similarity.
        """
        raw_tokens = _tokenize(query)
        expanded_query_tokens = _expand_query_tokens(raw_tokens)

        # 1. Pre-retrieval deterministic security filtering
        candidates = []
        for doc in self.documents:
            # Enforce Patient Scope Filter
            if allowed_patient_ids is not None:
                if doc["patient_id"] not in allowed_patient_ids:
                    continue

            # Enforce Category Filter
            if allowed_categories is not None:
                if doc["category"] not in allowed_categories:
                    continue

            # Enforce Department Scope Filter (e.g. Dept Head)
            if department and doc["department"] != department:
                continue

            # Enforce Ward Scope Filter (e.g. Nurse)
            if ward and doc["ward"] != ward:
                continue

            candidates.append(doc)

        if not candidates:
            return []

        # 2. Score authorized candidates via BM25 + Clinical Synonym Expansion
        scored = []
        for doc in candidates:
            score = self._score_bm25(expanded_query_tokens, doc)
            scored.append((score, doc))

        # Sort descending by score
        scored.sort(key=lambda x: x[0], reverse=True)

        # If allowed_patient_ids is explicitly targeted to specific patient(s),
        # return the top matches for that patient even if score is moderate.
        # But if broad query and top score is 0.0 (e.g. "hello", "who are you"), return []
        is_targeted = allowed_patient_ids is not None and len(allowed_patient_ids) <= 3
        if not is_targeted and (not scored or scored[0][0] < min_score):
            return []

        results = []
        for score, doc in scored:
            # If broad search and score drops below threshold, break
            if not is_targeted and score < min_score:
                break
            results.append({
                "doc_id": doc["doc_id"],
                "patient_id": doc["patient_id"],
                "patient_name": doc["patient_name"],
                "category": doc["category"],
                "department": doc["department"],
                "ward": doc["ward"],
                "title": doc.get("title", ""),
                "text": doc["text"],
                "score": round(score, 4)
            })
            if len(results) >= top_k:
                break

        return results
