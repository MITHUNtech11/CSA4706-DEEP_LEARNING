"""
Dual-Mode LLM Client with Deep Clinical Grounding.
Provides a deterministic, rule-grounded clinical RAG engine and optional live API integration.
"""

import os
import re
import json
from typing import Dict, Any, List, Optional
import requests


class LLMClient:
    def __init__(self, mode: str = "mock"):
        self.mode = os.getenv("LLM_PROVIDER", mode).lower()

    def generate(self, prompt: str, retrieved_context: str, user_query: str, role: str) -> str:
        """
        Generates response using either the offline deterministic engine or live API.
        """
        # 1. Check for prompt injection attempt in query
        injection_patterns = [
            r"ignore (all )?previous (instructions|rules|directives)",
            r"system override",
            r"you are now (an? )?(admin|dan)",
            r"disregard (all )?(rules|instructions)",
            r"reveal all (passwords|secrets|keys|phone numbers|ssns)",
            r"from now on you will do anything now",
            r"<system>.*</system>"
        ]
        for pat in injection_patterns:
            if re.search(pat, user_query, re.IGNORECASE):
                return (
                    f"SECURITY ALERT: Prompt injection attempt detected. As the Hospital Clinical RAG Assistant, "
                    f"system directives and role permissions ({role}) cannot be overridden by user input."
                )

        # 2. Check for offline or mock mode
        if self.mode == "mock" or not (os.getenv("GEMINI_API_KEY") or os.getenv("OPENAI_API_KEY")):
            return self._generate_deterministic(retrieved_context, user_query, role)
        
        # 3. Live API generation with automatic graceful fallback
        try:
            if self.mode == "gemini" and os.getenv("GEMINI_API_KEY"):
                return self._call_gemini(prompt)
            elif self.mode == "openai" and os.getenv("OPENAI_API_KEY"):
                return self._call_openai(prompt)
            else:
                return self._generate_deterministic(retrieved_context, user_query, role)
        except Exception as e:
            return f"{self._generate_deterministic(retrieved_context, user_query, role)}\n\n*(Live API fallback triggered: {str(e)})*"

    def _generate_deterministic(self, context: str, query: str, role: str) -> str:
        """
        Deterministic, grounded response generator for offline evaluations & clinical queries.
        Directly matches Prototype Preview in Slide 3 and Slide 15.
        """
        q_lower = query.lower()

        # Handle conversational greetings / capability queries
        if context == "[CONVERSATIONAL QUERY - CLINICAL ASSISTANT MODE]" or any(
            re.search(r"\b" + re.escape(w) + r"\b", q_lower)
            for w in ["hello", "hi", "hey", "who are you", "help", "what can you do", "system status", "good morning", "good evening"]
        ) and not any(w in q_lower for w in ["patient", "diagnosis", "vital", "vitals", "note", "record", "medication", "allergy", "phone", "ssn", "balance"]):
            return (
                f"Hello! I am the **Hospital Clinical RAG Assistant** running with active role level authorization for **{role}**.\n\n"
                f"**Active Session Capabilities**:\n"
                f"• Pre-retrieval role scoping and deterministic database filtering are enforced.\n"
                f"• You can query clinical status, vital signs, active medications, allergies, diagnoses, or notes permitted for your role.\n"
                f"• Personal identifiers (SSN/Phone) are masked automatically according to hospital privacy policy.\n\n"
                f"*How can I assist your clinical workflow today?*"
            )

        # Handle out of scope or empty retrieval
        if not context or "[NO DOCUMENTS RETRIEVED" in context:
            return (
                f"No accessible patient records found matching your query within your permitted scope ({role}). "
                f"If you require cross-department access, please request an active referral from the attending physician."
            )

        response_parts = []

        # 1. Location / Bed / Ward Query
        if any(w in q_lower for w in ["bed", "ward", "room", "where is", "location"]):
            loc_match = re.search(r"Department:\s*([^|]+)\|\s*Ward:\s*([^|]+)\|\s*Bed:\s*([^\n\r]+)", context)
            if loc_match:
                dept = loc_match.group(1).strip()
                ward = loc_match.group(2).strip()
                bed = loc_match.group(3).strip()
                response_parts.append(f"**Location**: {dept} | {ward} | Bed: {bed}")

        # 2. Diagnosis Query
        if any(w in q_lower for w in ["diagnosis", "condition", "what is", "details", "status", "disease", "cardiac", "heart condition"]):
            diag_match = re.search(r"Diagnosis:\s*([^\n\r]+)", context)
            if diag_match:
                response_parts.append(f"**Diagnosis**: {diag_match.group(1).strip()}")

        # 3. Allergies Query
        if any(w in q_lower for w in ["allergy", "allergies", "allergic", "details", "what is", "status"]):
            allergy_match = re.search(r"Allergies:\s*([^\n\r]+)", context)
            if allergy_match:
                response_parts.append(f"**Allergies**: {allergy_match.group(1).strip()}")

        # 4. Active Medications Query
        if any(w in q_lower for w in ["medication", "medications", "meds", "drugs", "prescriptions", "dose", "dosage", "details", "status"]):
            med_match = re.search(r"Active Medications:\s*([^\n\r]+)", context)
            if med_match:
                response_parts.append(f"**Active Medications**: {med_match.group(1).strip()}")

        # 5. Vital Signs Query
        if any(w in q_lower for w in ["vital", "vitals", "signs", "bp", "blood pressure", "heart rate", "pulse", "spo2", "temperature", "status", "details"]):
            vital_match = re.search(r"Vital Signs:\s*([^\n\r]+)", context)
            if vital_match:
                response_parts.append(f"**Vital Signs**: {vital_match.group(1).strip()}")

        # 6. Phone / Contact Query
        if any(w in q_lower for w in ["phone", "contact", "address", "number"]):
            phone_match = re.search(r"Phone:\s*([^\n\r]+)", context)
            if phone_match:
                val = phone_match.group(1).strip()
                if "MASKED" in val or "RESTRICTED" in val:
                    response_parts.append("**Phone**: `[MASKED - RESTRICTED FOR THIS ROLE]`")
                else:
                    response_parts.append(f"**Phone**: {val}")

        # 7. Billing Balance & Appointment Query (Front Desk / CMO)
        if any(w in q_lower for w in ["billing", "balance", "cost", "account", "appointment", "schedule"]):
            bal_match = re.search(r"Billing Balance:\s*([^\n\r]+)", context)
            apt_match = re.search(r"Appointment Status:\s*([^\n\r]+)", context)
            if bal_match:
                response_parts.append(f"**Billing Balance**: {bal_match.group(1).strip()}")
            if apt_match:
                response_parts.append(f"**Appointment Status**: {apt_match.group(1).strip()}")

        # 8. Clinical Notes / Surgical / Imaging Query
        if any(w in q_lower for w in ["note", "notes", "surgery", "surgical", "progress", "biopsy", "echo", "echocardiogram", "consult", "operative", "history"]):
            if "NOT PERMITTED FOR THIS ROLE" in context or "DENIED BY DEFAULT" in context or role in ["Nurse", "Front Desk / Billing Staff"]:
                response_parts.append("**Full Medical Record**: `Not permitted for this role (Denied by default)`")
            else:
                # Extract clinical note content from context
                note_blocks = re.findall(r"Note Title:\s*([^\.]+)\.\s*Content:\s*([^\n\r]+)", context)
                if note_blocks:
                    for title, body in note_blocks[:2]:
                        response_parts.append(f"**Clinical Note ({title.strip()})**: {body.strip()[:240]}...")
                else:
                    alt_notes = re.findall(r"\[Document ([^\]]+)\]:\s*([^\n\r]+)", context)
                    if alt_notes:
                        doc_id, text = alt_notes[0]
                        response_parts.append(f"**Clinical Notes Summary** (Doc `{doc_id}`): {text[:220]}...")
                    else:
                        response_parts.append("**Clinical Notes**: Clinical records attached in verified context.")

        # 9. Census / Patient List Query (e.g. "list all cardiology patients")
        if any(w in q_lower for w in ["list", "census", "all patients", "who is admitted"]):
            pts = re.findall(r"=== PATIENT RECORD:\s*([^\s=]+)\s*===\s*\nName:\s*([^\n\r]+)", context)
            if pts:
                patient_list = [f"• **{name}** (`{pid}`)" for pid, name in pts]
                response_parts.append("**Patients in Permitted Scope**:\n" + "\n".join(patient_list))

        # Default fallback if query didn't match specific fields
        if not response_parts:
            safe_lines = [
                l for l in context.splitlines() 
                if l.strip() and not l.startswith("===") and "National ID" not in l
            ][:5]
            response_parts.append("\n".join(safe_lines))

        response_parts.append("\n*(Filter applied before the LLM | Logged | Deny-by-default enforced)*")
        return "\n".join(response_parts)

    def _call_gemini(self, prompt: str) -> str:
        api_key = os.getenv("GEMINI_API_KEY")
        url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-1.5-flash:generateContent?key={api_key}"
        payload = {
            "contents": [{"parts": [{"text": prompt}]}],
            "generationConfig": {"temperature": 0.2, "maxOutputTokens": 800}
        }
        res = requests.post(url, json=payload, timeout=12)
        res.raise_for_status()
        data = res.json()
        return data["candidates"][0]["content"]["parts"][0]["text"]

    def _call_openai(self, prompt: str) -> str:
        api_key = os.getenv("OPENAI_API_KEY")
        url = "https://api.openai.com/v1/chat/completions"
        headers = {
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json"
        }
        payload = {
            "model": "gpt-4o-mini",
            "messages": [{"role": "user", "content": prompt}],
            "temperature": 0.2
        }
        res = requests.post(url, headers=headers, json=payload, timeout=12)
        res.raise_for_status()
        data = res.json()
        return data["choices"][0]["message"]["content"]
