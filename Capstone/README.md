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

## 2. Dedicated Role-Specific Portal Pages

The application provides dedicated web portal pages tailored to each role's distinct hospital workflow:

| Portal Endpoint | Role Name | Security Level | Data Scope & Permissions | Dedicated Features |
| :--- | :--- | :---: | :--- | :--- |
| **`/portal/gateway`** | **Hospital Role Gateway** | N/A | Overview & Directory | Central launchpad for all 6 roles with permission matrix |
| **`/portal/cmo`** | **Chief Medical Officer** | Level 5 | All Patients | Cross-department clinical audit overview across all wards |
| **`/portal/dept-head`** | **Department Head** | Level 4 | Own Dept (Cardiology) | Department census, attending physician assignments |
| **`/portal/doctor`** | **Treating Doctor** | Level 3 | Care-Team + Referrals | Care-team roster + Active (`P-3307`) & Expired (`P-4180`) referrals |
| **`/portal/nurse`** | **Nurse** | Level 2 | Assigned Ward 3 | **Slide 3 Prototype**: Ward bedside care, phone masked, full notes denied |
| **`/portal/billing`** | **Front Desk / Billing** | Level 1 | Task-Specific | Inpatient billing balances & insurance; clinical notes strictly blocked |
| **`/portal/admin`** | **System Administrator** | Level 0 | Control Panel Only | **Separation of Duties**: Zero clinical access; SHA-256 audit & tamper engine |

---

## 3. Six-Step Request Enforcement Pipeline (Slide 8)

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

---

## 4. Quickstart Guide

### 1. Environment Setup
The project uses the Python 3.11 virtual environment configured at `.venv`:
```powershell
cd "c:\Users\mithu\OneDrive\Desktop\CSA4706 - DEEP LEARNING\Capstone"
& "..\.venv\Scripts\python.exe" -m pip list
```

### 2. Run Automated Pytest Suite (36 Tests)
```powershell
& "..\.venv\Scripts\python.exe" -m pytest tests/ -v
```

### 3. Run Red-Teaming Security Benchmark
```powershell
& "..\.venv\Scripts\python.exe" scripts/run_security_eval.py
```

### 4. Launch the Multi-Page Web Application
```powershell
& "..\.venv\Scripts\python.exe" -m uvicorn src.api.app:app --host 127.0.0.1 --port 8000 --reload
```
Open **`http://127.0.0.1:8000`** in your web browser.
