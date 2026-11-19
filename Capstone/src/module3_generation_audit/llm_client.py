"""
Dual-Mode LLM Client.
Provides a deterministic, rule-grounded offline engine and optional live API integration.
"""

import os
import re
from typing import Dict, Any, List, Optional
import requests


class LLMClient:
    def __init__(self, mode: str = "mock"):
        self.mode = os.getenv("LLM_PROVIDER", mode).lower()

    def generate(self, prompt: str, retrieved_context: str, user_query: str, role: str) -> str:
        """
        Generates response using either the offline deterministic engine or live API.
        """
        # Check for obvious prompt injection attempt in query
        injection_patterns = [
            r"ignore (all )?previous instructions",
            r"system override",
            r"you are now (an? )?admin",
            r"disregard (all )?rules",
            r"reveal all (passwords|secrets|keys)"
        ]
        for pat in injection_patterns:
            if re.search(pat, user_query, re.IGNORECASE):
                return (
                    f"SECURITY ALERT: Prompt injection attempt detected. As the Hospital Clinical RAG Assistant, "
                    f"system directives and role permissions ({role}) cannot be overridden by user input."
                )

        if self.mode == "mock" or not (os.getenv("GEMINI_API_KEY") or os.getenv("OPENAI_API_KEY")):
            return self._generate_deterministic(retrieved_context, user_query, role)
        
        # If API keys are present, attempt live generation with fallback
        try:
            if self.mode == "gemini" and os.getenv("GEMINI_API_KEY"):
                return self._call_gemini(prompt)
            elif self.mode == "openai" and os.getenv("OPENAI_API_KEY"):
                return self._call_openai(prompt)
            else:
                return self._generate_deterministic(retrieved_context, user_query, role)
        except Exception as e:
            return f"{self._generate_deterministic(retrieved_context, user_query, role)} (Generated via Offline Fallback: {str(e)})"

    def _generate_deterministic(self, context: str, query: str, role: str) -> str:
        """
        Deterministic, grounded response generator for offline evaluations & test cases.
        Directly matches Prototype Preview in Slide 3.
        """
        if not context or "[NO DOCUMENTS RETRIEVED" in context:
            return (
                f"No accessible patient records found matching your query within your permitted scope ({role}). "
                f"If you require cross-department access, please request an active referral from the attending physician."
            )

        response_parts = []
        q_lower = query.lower()

        # Check for diagnosis / status query
        if any(w in q_lower for w in ["diagnosis", "condition", "what is", "details", "status"]):
            diag_match = re.search(r"Diagnosis:\s*(.+)", context)
            if diag_match:
                response_parts.append(f"**Diagnosis**: {diag_match.group(1).strip()}")

        # Check for allergies query
        if any(w in q_lower for w in ["allergy", "allergies", "details", "what is", "status"]):
            allergy_match = re.search(r"Allergies:\s*(.+)", context)
            if allergy_match:
                response_parts.append(f"**Allergies**: {allergy_match.group(1).strip()}")

        # Check for medications query
        if any(w in q_lower for w in ["medication", "meds", "drugs", "details", "status"]):
            med_match = re.search(r"Active Medications:\s*(.+)", context)
            if med_match:
                response_parts.append(f"**Active Medications**: {med_match.group(1).strip()}")

        # Check for phone / contact query
        if any(w in q_lower for w in ["phone", "contact", "address"]):
            phone_match = re.search(r"Phone:\s*(.+)", context)
            if phone_match:
                val = phone_match.group(1).strip()
                if "MASKED" in val or "RESTRICTED" in val:
                    response_parts.append(f"**Phone**: `[MASKED - RESTRICTED FOR THIS ROLE]`")
                else:
                    response_parts.append(f"**Phone**: {val}")

        # Check for clinical notes / surgical history query
        if any(w in q_lower for w in ["note", "surgery", "progress", "biopsy", "echo", "consult"]):
            if "NOT PERMITTED FOR THIS ROLE" in context or "DENIED BY DEFAULT" in context:
                response_parts.append("**Full Medical Record**: `Not permitted for this role (Denied by default)`")
            else:
                # Extract notes content
                notes_matches = re.findall(r"Note:?\s*(.+)", context)
                if notes_matches:
                    response_parts.append(f"**Clinical Notes Summary**: {notes_matches[0].strip()[:200]}...")
                else:
                    response_parts.append("**Clinical Notes**: Clinical records attached in verified context.")

        # Default fallback if query didn't match specific fields
        if not response_parts:
            # Extract safe lines (omit National ID lines to prevent raw PII dump)
            safe_lines = [
                l for l in context.splitlines() 
                if l.strip() and not l.startswith("===") and "National ID" not in l
            ][:4]
            response_parts.append("\n".join(safe_lines))

        response_parts.append("\n*(Filter applied before the LLM | Logged | Deny-by-default enforced)*")
        return "\n".join(response_parts)

    def _call_gemini(self, prompt: str) -> str:
        api_key = os.getenv("GEMINI_API_KEY")
        url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-1.5-flash:generateContent?key={api_key}"
        payload = {"contents": [{"parts": [{"text": prompt}]}]}
        res = requests.post(url, json=payload, timeout=10)
        res.raise_for_status()
        data = res.json()
        return data["candidates"][0]["content"]["parts"][0]["text"]

    def _call_openai(self, prompt: str) -> str:
        api_key = os.getenv("OPENAI_API_KEY")
        url = "https://api.openai.com/v1/chat/completions"
        headers = {"Authorization": f"Bearer {api_key}", "Content-Type": "application/json"}
        payload = {
            "model": "gpt-4o-mini",
            "messages": [{"role": "user", "content": prompt}],
            "temperature": 0.2
        }
        res = requests.post(url, json=headers, timeout=10)
        res.raise_for_status()
        data = json.loads(res.text)
        return data["choices"][0]["message"]["content"]
