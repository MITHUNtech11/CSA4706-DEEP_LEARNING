# Secure Role-Based Access Control for a Retrieval-Augmented Generation (RAG) System in a Hospital

**Capstone Project | CSA4706 - Deep Learning**  
**Department of Computer Science and Engineering | SIMATS Engineering**  
*Saveetha Institute of Medical and Technical Sciences (SIMATS), Chennai, India*  

* **Academic Supervisor**: Dr. Vasantharaj K  
* **Project Team & Module Allocation**:
  * **Joseph Asborn Daniel J** (Reg. No: 192324009) — *Module 1: Identity Management, Authentication & Policy Engine*
  * **Prajith K** (Reg. No: 192324013) — *Module 2: Enforced Pre-Retrieval, Vector Scoping & Dynamic Redaction*
  * **Mithunsenthil S** (Reg. No: 192324009) — *Module 3: Controlled Generation, Output Guardrails & Cryptographic Audit*

---

## 1. Executive Summary

Standard Retrieval-Augmented Generation (RAG) systems deployed in healthcare environments present catastrophic privacy vulnerabilities: non-deterministic Large Language Models (LLMs) can be manipulated via prompt injections, indirect jailbreaks, or broad similarity searches to reveal confidential patient health information (PHI), surgical notes, and personally identifiable information (PII). 

This Capstone project delivers a **fail-closed, defense-in-depth reference architecture** that decouples access governance from the LLM. Instead of relying on post-generation filtering or model alignment, our system enforces deterministic security controls across three coordinated boundaries: **Pre-Retrieval Enforced Filtering**, **Server-Side Untrusted Context Demarcation**, and **Algorithmic Post-Generation Verification (Algorithm 1)**, all recorded into a **Monotonic Cryptographic SHA-256 Hash-Chained Audit Log (Algorithm 2)** with 100% automated tamper detection.

---

## 2. The Clinical Threat Model & Core Problem

Traditional RAG architectures query a vector database based purely on semantic cosine similarity and feed the resulting top-$k$ chunks directly into an LLM context prompt. In clinical settings, this design creates four major security vulnerabilities:

1. **Over-Retrieval & Lateral Data Leakage**: A nurse asking for vital signs might inadvertently retrieve unredacted surgical or psychiatric notes because the semantic embedding of the query matched words in the broader patient record.
2. **Adversarial Prompt Injection & Jailbreaking**: Attackers using Direct Instruction Overrides, DAN ("Do Anything Now") personas, or role claims (`"I am the Chief Medical Officer"`) can deceive the LLM into bypassing conversational boundaries.
3. **Privilege Escalation & Lack of Role Scoping**: Hospital staff possess radically different clearance levels. An administrative clerk or billing staff member should never access clinical diagnoses, while an attending physician should only access patients within their active care team or valid referrals.
4. **Unaudited Exfiltration & Log Tampering**: Generic application logs can be truncated, deleted, or altered by malicious insiders, destroying accountability for HIPAA and GDPR compliance audits.

### The Solution: Decoupled 3-Layer Defense
```
[ User Request + JWT Token ]
             |
             v
+----------------------------+
|  Layer 1: Identity & Scope |  --> Step 1: Verify HMAC-SHA256 & Enforce Separation of Duties
|  (Module 1 - Joseph)       |  --> Step 2: Build Deterministic SQL & Category Filters
+----------------------------+
             |
             v
+----------------------------+
|  Layer 2: Enforced Query   |  --> Step 3: Pre-Retrieval Vector Filter (Out-of-scope never loaded)
|  (Module 2 - Prajith)      |  --> Dynamic Field Redaction (PII / Masked SSN / Phone)
+----------------------------+
             |
             v
+----------------------------+
|  Layer 3: Generation/Guard |  --> Step 4: Inject Context into <untrusted_patient_context>
|  (Module 3 - Mithunsenthil)|  --> Step 5: Algorithm 1 Output Guard (ids_ok, cats_ok, grounded)
+----------------------------+  --> Step 6: Algorithm 2 SHA-256 Hash-Chained Monotonic Audit
             |
             v
[ Verified, Grounded Response ]
```

---

## 3. Hierarchical Role-Based Access Control (RBAC) Matrix

The system governs all interactions across **six operational hospital roles**, mapping each role to explicit clinical categories, clearance levels, data scopes, and field-level masking rules:

| Level | Role Name | Primary Scope | Permitted Categories | Field-Level Redaction | Separation of Duties Guarantee | Demo User |
| :---: | :--- | :--- | :--- | :--- | :--- | :--- |
| **5** | **Chief Medical Officer (CMO)** | All Hospital Patients | Full Medical Record, General Clinical, Identifiers | None (Full Access for Clinical Governance) | Full hospital clinical review; access logged in hash chain | `CMO_501` |
| **4** | **Department Head** | Own Department Ward | Full Medical Record, General Clinical, Identifiers | Cross-department records completely blocked | Restricted to assigned specialty (e.g. Cardiology only) | `DH_401` |
| **3** | **Treating Doctor** | Assigned Care Team + Active Referrals | Full Medical Record, General Clinical, Identifiers | Expired referrals return 0 records; non-assigned patients blocked | Cannot query unreferred patients from other clinics | `DR_302` |
| **2** | **Nurse** | Assigned Ward | General Clinical Details (Vitals, Meds, Allergies) | SSN masked (`***-**-XXXX`), Phone masked, Full surgical/imaging notes blocked | Cannot view unmasked patient contact info or deep operative notes | `RN_201` |
| **1** | **Front Desk / Billing** | Task-Specific Lookup | Registration, Billing Balance, Appointment Status | All clinical diagnoses, medical history, notes, and SSN strictly blocked | Zero clinical diagnosis visibility; billing and schedule only | `FD_101` |
| **0** | **System Administrator** | IT Control Panel Only | Policy Management, Audit Logs, System Health | Complete block on all patient records (`*`) | **Strict Separation of Duties**: Refused all clinical and patient data queries | `SYS_999` |

---

## 4. The 6-Step Request Enforcement Pipeline

Every request submitted to the system must complete six sequential enforcement steps before an answer is delivered:

```
+---------------+     +---------------+     +---------------+
| 1. AUTHENTICATE| --> | 2. BUILD      | --> | 3. ENFORCED   |
| (Module 1)    |     |    FILTERS    |     |    RETRIEVAL  |
| HMAC-SHA256   |     | Scope, Wards, |     | SQL & Vector  |
| Claims & Role |     | Categories    |     | Pre-Filtering |
+---------------+     +---------------+     +---------------+
                                                    |
                                                    v
+---------------+     +---------------+     +---------------+
| 6. CRYPTO     | <-- | 5. OUTPUT     | <-- | 4. RENDER     |
|    AUDIT LOG  |     |    GUARD      |     |    PROMPT     |
| Algorithm 2   |     | Algorithm 1   |     | Jinja2 & Tag  |
| Monotonic Hash|     | Tri-Factor    |     | Demarcation   |
+---------------+     +---------------+     +---------------+
```

1. **Step 1: Authenticate & Authorize Identity (Module 1)**:
   - Verifies the HMAC-SHA256 signature of the stateless JWT token.
   - Extracts role, level, department, assigned ward, and active patient scopes.
   - **Enforces Separation of Duties**: If the role is `System Administrator`, all data queries are immediately refused with `REFUSAL: ACCESS DENIED` and logged as security events.

2. **Step 2: Construct Pre-Retrieval Filters (Module 2)**:
   - Compiles active policy rules into deterministic SQL predicates and vector metadata criteria.
   - Dynamically resolves doctor care-teams and checks active referral expiration timestamps against current UTC time.

3. **Step 3: Enforced Retrieval & Dynamic Masking (Module 2)**:
   - Hybrid BM25 & semantic search queries only pre-filtered candidate document subsets. Out-of-scope records are never loaded into memory.
   - Expands query tokens using a domain-specific clinical synonym dictionary (e.g. mapping `"heart"` to `"cardiac"`, `"aortic stenosis"`, `"hypertension"`).
   - Applies dynamic field masking via `FieldMasker`: nurses receive masked phone numbers and redacted National IDs; billing receives masked clinical summaries.

4. **Step 4: Render Versioned Prompt Template (Module 3)**:
   - Context is injected into server-side Jinja2 templates (`system_prompt_v1.jinja2`).
   - Retrieved clinical documents are enclosed within strict `<untrusted_patient_context>` boundaries, preventing instruction manipulation.

5. **Step 5: Algorithmic Output Verification (Module 3 - Algorithm 1)**:
   - Post-generation verification evaluates three criteria:
     * $\text{ids\_ok}$: Verifies no unmasked SSNs (`\d{3}-\d{2}-\d{4}`) or restricted contact numbers are leaked.
     * $\text{cats\_ok}$: Verifies no restricted surgical or pathology categories appear for unauthorized roles.
     * $\text{grounded}$: Confirms that all claims in the generated response are strictly grounded in retrieved context $X$; prevents ungrounded hallucinations when retrieval returns zero documents.
   - If any condition fails, the response is replaced with a fail-closed refusal.

6. **Step 6: Monotonic Cryptographic Audit Logging (Module 3 - Algorithm 2)**:
   - Appends an immutable record to `logs/audit_chain.jsonl`.
   - Computes SHA-256 hash chaining: $h_n = \text{SHA-256}(\text{CanonicalJSON}(\text{entry}_n) + h_{n-1})$.
   - Uses thread-safe atomic file serialization to guarantee log integrity during concurrent queries.

---

## 5. Unique & Innovative Capabilities

### 1. Fail-Closed Security Philosophy
Unlike standard software systems that fail-open or degrade into permissive behavior upon missing parameters, our architecture is strictly **fail-closed**:
* Missing authentication token $\rightarrow$ HTTP 401 Refusal.
* Ambiguous role or missing department claim $\rightarrow$ Retrieval Filter Refusal.
* Expired cross-department referral $\rightarrow$ 0 documents retrieved.
* Ungrounded LLM claim or category violation $\rightarrow$ Immediate output refusal by Algorithm 1.

### 2. Strict Separation of Duties (Admin Zero-Data Invariant)
In standard hospital IT infrastructure, database and system administrators possess superuser privileges that expose sensitive patient charts. In our system, the **System Administrator (Level 0)** is strictly partitioned:
* Granted full control over policy draft approvals, audit log verification, and health monitoring.
* **100% blocked from querying clinical data, diagnoses, or patient identifiers**. Any query attempting to read patient data fails at Step 1.

### 3. Dual-Approver Policy Governance
Modifications to the hospital access matrix follow a multi-signature governance protocol:
* An administrator submits a draft policy update (e.g., promoting `v1.0` to `v1.1`).
* The update remains in `PENDING_SECOND_APPROVAL` status until a distinct, authenticated compliance officer signs off.
* Protects the hospital from rogue administrator attacks and unintended configuration drift.

### 4. Emergency Break-Glass Protocol
In life-threatening clinical emergencies where an unassigned patient requires immediate treatment:
* A doctor or nurse can trigger an **Emergency Break-Glass** request with mandatory clinical justification text.
* The system temporarily expands retrieval scope while issuing an ephemeral token with a shortened 15-minute expiration.
* The event is flagged with high priority and permanently anchored into the cryptographic audit log for compliance review.

### 5. Algorithmic Tamper Detection (100% Accuracy)
The SHA-256 audit log acts as a lightweight, self-contained blockchain:
* If an attacker alters a previous log entry (e.g. changing an `OUTCOME: BLOCKED` to `OUTCOME: ALLOWED` or deleting query text), the hash chain breaks from that entry forward.
* `/api/audit/verify` re-calculates the cumulative chain, pinpointing the exact line number, corrupted timestamp, and invalid hash.

### 6. Role-Specific Dedicated Web Portals & Login Hub
Rather than providing a single generic chat window, the application provides specialized web stations tailored to each hospital role's clinical workflow:
* **`/login` (Role Login Hub)**: Switchable role tabs with salted SHA-256 password authentication and demo quick-fill presets.
* **`/portal/gateway`**: Overview launchpad and interactive permission matrix.
* **`/portal/cmo`**: Executive clinical station with hospital-wide patient selection and deep audit log inspector.
* **`/portal/dept-head`**: Departmental ward oversight station.
* **`/portal/doctor`**: Clinical station showing care-team patients, referral lookups, and diagnosis tools.
* **`/portal/nurse`**: Ward-level station with vitals monitoring, medication schedules, and PII masking indicators.
* **`/portal/billing`**: Patient administration desk showing appointments and billing balances with clinical blocking alerts.
* **`/portal/admin`**: Security console with real-time audit verification, policy approval tools, and tamper simulation.
* **Glass-Box Telemetry Inspector**: All portals feature an expandable drawer displaying the live JSON execution trace across all 6 pipeline stages.

---

## 6. Quantitative Evaluation & Benchmark Results

The system was evaluated using automated unit, integration, and red-teaming security test suites:

### 1. Automated Test Suite Performance
```text
======================== 55 passed, 1 warning in 2.31s ========================
```
* **Identity & Policy Suite (`test_module1_identity_policy.py`)**: 8/8 tests passed.
* **Enforced Retrieval Suite (`test_module2_enforced_retrieval.py`)**: 5/5 tests passed.
* **Generation & Audit Suite (`test_module3_generation_audit.py`)**: 4/4 tests passed.
* **End-to-End Pipeline Suite (`test_end_to_end_pipeline.py`)**: 7/7 tests passed.
* **Portal Routing & Web Suite (`test_portal_pages.py`)**: 13/13 tests passed.
* **Production Readiness Suite (`test_production_readiness.py`)**: 5/5 tests passed.
* **Proper RAG & Grounded Retrieval (`test_proper_rag.py`)**: 6/6 tests passed.
* **Red-Team Adversarial Suite (`test_redteam_attacks.py`)**: 7/7 tests passed.

### 2. Adversarial Red-Teaming Benchmark (`scripts/run_security_eval.py`)
Twelve complex adversarial scenarios were evaluated against the live pipeline, testing direct prompt injections, DAN personas, role spoofing, cross-department probes, and expired referral exploits:

| Metric | Target | Evaluated Result | Evaluation Status |
| :--- | :---: | :---: | :---: |
| **Adversarial Scenarios Evaluated** | 12 | **12** | Complete |
| **Data Leakage Rate** | 0.0% | **0.0%** | **ZERO LEAKAGE (PASSED)** |
| **Policy Compliance & Pass Rate** | 100.0% | **100.0%** | **PERFECT (PASSED)** |
| **Cryptographic Tamper Detection** | 100.0% | **100.0%** | **100% IDENTIFICATION (PASSED)** |
| **Mean Pipeline Enforcement Latency** | < 50 ms | **17.17 ms** | **REAL-TIME READY** |

---

## 7. Technology Stack

* **Core Runtime**: Python 3.11.9
* **API Framework**: FastAPI 0.115+, Uvicorn (ASGI)
* **Data & Storage**: SQLite 3 (configured with Write-Ahead Logging `WAL` mode for high-concurrency read/write operations)
* **Cryptography & Security**:
  * PyJWT (stateless HMAC-SHA256 signature verification)
  * Standard Python `hashlib` (SHA-256 monotonic hash chaining and salted password hashing)
* **Templating & Prompts**: Jinja2 (versioned prompt templates with `<untrusted_patient_context>` tagging)
* **Search & Retrieval**: In-memory hybrid BM25 and keyword search with clinical synonym query expansion
* **Frontend**: Vanilla HTML5, Modern CSS (custom CSS properties, Poppins typography, responsive layout), JavaScript ES6 (Fetch API, route guards)
* **Testing & Quality Assurance**: Pytest 9.2+, Starlette TestClient, Requests
* **DevOps & Containerization**: Docker Engine, Docker Compose, multi-stage Dockerfile

---

## 8. Repository Layout

```text
Capstone/
├── .github/workflows/ci.yml       # Automated CI pipeline running pytest & security eval
├── data/
│   └── hospital.db                # SQLite database (patients, clinical notes, referrals, personas)
├── logs/
│   ├── audit_chain.jsonl          # Monotonic SHA-256 hash-chained audit log
│   └── system.log                 # Standardized application operational logs
├── policies/
│   ├── policy_v1.0.json           # Active hospital role-based access policy
│   └── policy_v1.1_draft.json     # Staged draft policy awaiting dual approval
├── scripts/
│   ├── demo_cli.py                # Interactive command-line testing utility
│   └── run_security_eval.py       # Automated 12-scenario red-teaming security benchmark
├── src/
│   ├── api/
│   │   ├── app.py                 # FastAPI application with security headers & route handlers
│   │   ├── routes.py              # Endpoints: /auth, /chat, /audit, /policy, /health, /metrics
│   │   └── schemas.py             # Pydantic v2 validation models
│   ├── module1_identity_policy/
│   │   ├── tokens.py              # JWT token issuance, validation & claims parsing
│   │   ├── policy_engine.py       # RBAC policy loading, dual-approver governance & validation
│   │   └── idp_service.py         # Mock Identity Provider with salted SHA-256 authentication
│   ├── module2_enforced_retrieval/
│   │   ├── database.py            # Scoped SQLite data repository
│   │   ├── filter_builder.py      # Pre-retrieval filter compiler (SQL & categories)
│   │   ├── vector_store.py        # Pre-filtered BM25 & semantic store with clinical synonyms
│   │   └── field_masker.py        # Dynamic field-level redaction (SSN, contact info)
│   ├── module3_generation_audit/
│   │   ├── prompt_renderer.py     # Jinja2 template renderer with untrusted context boundaries
│   │   ├── llm_client.py          # Dual-mode engine: offline deterministic & live API (Gemini/OpenAI)
│   │   ├── output_guard.py        # Algorithm 1: Multi-check output guard (ids_ok, cats_ok, grounded)
│   │   └── audit_logger.py        # Algorithm 2: Cryptographic SHA-256 hash-chain logger
│   ├── config.py                  # Central configuration and environment variable validation
│   └── pipeline.py                # Unified 6-step Request Enforcement Pipeline
├── templates/
│   └── system_prompt_v1.jinja2    # Versioned clinical assistant system prompt template
├── tests/
│   ├── conftest.py                # Shared pytest fixtures (IdP, Pipeline, TestClient)
│   ├── test_end_to_end_pipeline.py# Cross-module verification for all 6 roles
│   ├── test_module1_identity_policy.py
│   ├── test_module2_enforced_retrieval.py
│   ├── test_module3_generation_audit.py
│   ├── test_portal_pages.py       # Multi-page web portal route verification
│   ├── test_production_readiness.py# Observability, liveness, and thread safety tests
│   ├── test_proper_rag.py         # Grounded clinical extraction & conversational queries
│   └── test_redteam_attacks.py    # 12 adversarial attack test vectors
├── web/                           # Dedicated web portal stations & assets
│   ├── login.html                 # Unified Multi-Role Authentication Hub
│   ├── index.html                 # Hospital Role Gateway & Directory
│   ├── cmo.html                   # Chief Medical Officer Station (Level 5)
│   ├── dept_head.html             # Department Head Station (Level 4)
│   ├── doctor.html                # Treating Doctor Station (Level 3)
│   ├── nurse.html                 # Nurse Ward Station (Level 2)
│   ├── billing.html               # Front Desk / Billing Desk (Level 1)
│   ├── admin.html                 # System Admin Console (Level 0)
│   ├── portal_common.js           # Shared navigation, station header & route guard
│   ├── app.js                     # Chat interface logic & live telemetry renderer
│   ├── login.js                   # Login hub interaction & demo quick-fill presets
│   └── style.css                  # Modern responsive stylesheet (Poppins font)
├── Dockerfile                     # Multi-stage production container specification
├── docker-compose.yml             # Container orchestration with health check probes
├── PRODUCTION_GUIDE.md            # Comprehensive operational runbook & incident playbooks
├── pytest.ini                     # Pytest configuration
└── requirements.txt               # Locked project dependencies
```

---

## 9. Quickstart Guide

### 1. Environment & Dependencies
Ensure Python 3.11+ is installed. Navigate to the `Capstone` directory and activate the virtual environment:
```powershell
cd "c:\Users\mithu\OneDrive\Desktop\CSA4706 - DEEP LEARNING\Capstone"
& "..\.venv\Scripts\python.exe" -m pip install -r requirements.txt
```

### 2. Run the Full Test Suite (55 Tests)
```powershell
& "..\.venv\Scripts\python.exe" -m pytest tests/ -v
```

### 3. Run the Security & Red-Teaming Benchmark
```powershell
& "..\.venv\Scripts\python.exe" scripts/run_security_eval.py
```

### 4. Start the Multi-Page Web Application
Launch the FastAPI development server:
```powershell
& "..\.venv\Scripts\python.exe" -m uvicorn src.api.app:app --host 127.0.0.1 --port 8000 --reload
```
Open **`http://127.0.0.1:8000`** in your browser to access the **Role Login Hub**. Use any of the pre-seeded demo presets (`cmo@123`, `doc@123`, `nurse@123`, etc.) to enter each role station and test clinical queries.

---

## 10. Key Citations & Standards Alignment

* **HIPAA Privacy & Security Rules (45 CFR § 164.502)**: Minimum necessary standard enforced via deterministic pre-retrieval SQL/vector filtering and dynamic field masking.
* **Separation of Duties (NIST SP 800-53 AC-5)**: Enforced isolation between administrative operations and patient health data.
* **Cryptographic Hash Chaining (NIST FIPS 180-4 Secure Hash Standard)**: Monotonic SHA-256 chaining guaranteeing tamper-evident audit logging.
* **Fail-Closed Security Design (Saltzer and Schroeder, 1975)**: Deny-by-default access model across all stages of RAG retrieval and generation.
