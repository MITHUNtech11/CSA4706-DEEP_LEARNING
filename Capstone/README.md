# Secure Role-Based Access Control for a Retrieval-Augmented Generation (RAG) System in a Hospital

**Capstone Project | CSA4706 - Deep Learning**  
*SIMATS Engineering | Saveetha Institute of Medical and Technical Sciences (SIMATS)*  
**Guided by**: Dr. Vasantharaj K  
**Team Members**:
- **Joseph Asborn Daniel J** (192324009) — Module 1: Identity and Policy
- **Prajith K** (192324013) — Module 2: Enforced Retrieval
- **Mithunsenthil S** (192324009) — Module 3: Controlled Generation and Audit

---

## 1. System Overview

Standard Retrieval-Augmented Generation (RAG) pipelines in healthcare pose severe patient privacy and data exfiltration risks: an unauthorized user or prompt injection can manipulate an LLM into revealing confidential diagnoses, surgical notes, or personally identifiable information (PII).

This reference architecture implements a **fail-closed, defense-in-depth security model**:
1. **Primary Control (Retrieval Layer)**: Deterministic policy-driven SQL and vector pre-retrieval filtering. Out-of-scope records and expired referrals are never fetched from disk or memory.
2. **Secondary Control (Prompt Layer)**: Server-side versioned system prompt templates wrapping retrieved context inside strict `<untrusted_patient_context>` boundaries.
3. **Tertiary Control (Output Layer)**: Post-generation output guard verifying personal identifier masking, allowed category containment, and factual grounding (Algorithm 1).
4. **Tamper-Evident Accountability**: Monotonic SHA-256 hash-chained audit log with automated tamper detection (Algorithm 2).

---

## 2. Six-Step Request Enforcement Pipeline

Every clinical question passes through six control-panel stages:
```
1. Authenticate   --> Verify user identity and extract role from signed HMAC-SHA256 JWT
2. Build Filters  --> Translate matrix into patient scope, category, and field masks
3. Retrieve       --> Pre-filtered SQL + Vector search + Dynamic field redaction
4. Render Prompt  --> Inject server variables into versioned template with untrusted context
5. Check Output   --> Algorithm 1: Verify ids_ok, cats_ok, and factual grounding
6. Cryptographic  --> Algorithm 2: Append monotonic hash-chained entry: h_n = SHA256(entry_n + h_prev)
   Audit Log
```
*Fail-Closed Guarantee: If any step fails or cannot build an unambiguous filter, the query is immediately refused.*

---

## 3. Module Breakdown & Student Ownership

### Module 1: Identity and Policy (Joseph Asborn Daniel J)
- **Hospital Identity Provider (IdP)**: Manages authentication for 6 staff personas.
- **Signed Tokens**: Cryptographic HMAC-SHA256 JWTs with role level, department, assigned ward, and care assignments.
- **Versioned Policy Matrix**: Explicit grants across 6 roles and 3 categories (`full_medical_record`, `general_clinical_details`, `personal_identifiers`).
- **Separation of Duties**: System Administrator has zero clinical or identifier access (Level 0).
- **Dual-Approver Governance**: Proposed policy drafts require sign-off from two independent administrators.
- **Emergency Break-Glass**: 15-minute time-limited elevation requiring clinical justification and automatic audit flagging.

### Module 2: Enforced Retrieval (Prajith K)
- **Pre-Retrieval Filter Builder**: Translates token claims into deterministic SQL WHERE clauses and vector metadata filters.
- **Scope Enforcement**:
  - CMO (Level 5): All patients.
  - Department Head (Level 4): Own department only.
  - Treating Doctor (Level 3): Primary care-team patients + active valid referrals.
  - Nurse (Level 2): Assigned ward patients only (general clinical details only).
  - Front Desk / Billing (Level 1): Task-specific appointment and billing lookups.
- **Referral Expiry**: Expired referrals are automatically excluded at the database query layer.
- **Dynamic Field-Level Masker**: Automatically redacts telephone numbers, SSNs, and home addresses for nurses and billing clerks.

### Module 3: Controlled Generation and Audit (Mithunsenthil S)
- **Prompt Renderer**: Injects server-verified attributes (`{ROLE_NAME}`, `{ROLE_LEVEL}`, `{ALLOWED_CATEGORIES}`, `{PATIENT_SCOPE}`) into Jinja2 templates.
- **Dual-Mode LLM Client**: Offline deterministic rule-grounded engine for testing/defense presentations + optional live Gemini/OpenAI API integration.
- **Controlled Generation with Output Checks (Algorithm 1)**:
  - `ids_ok`: Scans generated text for unmasked SSNs or raw telephone numbers.
  - `cats_ok`: Ensures response only references clinical categories granted to that role.
  - `grounded`: Validates that clinical claims in the answer are strictly supported by the retrieved context.
- **Cryptographic Hash-Chained Audit Log (Algorithm 2)**:
  - Monotonic JSON-Lines log where $h_n = \text{SHA256}(\text{canonical\_json}(\text{entry}_n) + h_{n-1})$.
  - Cryptographic verification engine that detects unauthorized edits, deletions, or row reordering.
  - Includes tamper simulation and live audit explorer.

---

## 4. Quickstart Guide

### 1. Environment Setup
The project uses the Python 3.11 virtual environment configured at `.venv`:
```powershell
# Navigate to Capstone directory
cd "C:\Users\mithu\OneDrive\Desktop\CSA4706 - DEEP LEARNING\Capstone"

# Verify dependencies (fastapi, uvicorn, pydantic, pyjwt, pytest, requests)
& "..\.venv\Scripts\python.exe" -m pip list
```

### 2. Run Automated Pytest Suite
```powershell
& "..\.venv\Scripts\python.exe" -m pytest tests/ -v
```

### 3. Run Red-Teaming Security Benchmark
Evaluates 12 adversarial attacks and tests the cryptographic tamper detection:
```powershell
& "..\.venv\Scripts\python.exe" scripts/run_security_eval.py
```

### 4. Launch the Interactive Web Control Panel
```powershell
& "..\.venv\Scripts\python.exe" -m uvicorn src.api.app:app --host 127.0.0.1 --port 8000 --reload
```
Open **`http://127.0.0.1:8000`** in your web browser.

---

## 5. Control Panel Features

1. **Role Switcher**: Click between CMO, Dept Head, Treating Doctor, Nurse, Billing, and Admin to test identity token generation.
2. **Clinical Query Interface**: Pre-loaded scenario chips directly demonstrating the presentation slides:
   - *P-1042 Details (Slide 3)*: Nurse receives diagnosis & allergies with phone masked.
   - *Cross-Department (Slide 15)*: Doctor blocked from oncology patient without referral.
   - *Active Referral*: Doctor granted access to Oncology patient P-3307 via active consult.
   - *Expired Referral*: Doctor blocked from Orthopedic patient P-4180.
   - *Adversarial Prompt Injection*: Jailbreaks and role-spoofing attempts neutralized.
3. **6-Step Pipeline Telemetry**: Real-time visual cards highlighting pass/blocked status across all six pipeline steps.
4. **Tamper-Evident Audit Explorer**: Live SHA-256 hash chain table with one-click **"Verify Hash Chain"** and **"Simulate Secret Tamper"** to demonstrate cryptographic tamper alerts in real-time.
5. **Dual-Approver Governance**: Ratify draft policy v1.1 to demonstrate multi-administrator sign-off.
