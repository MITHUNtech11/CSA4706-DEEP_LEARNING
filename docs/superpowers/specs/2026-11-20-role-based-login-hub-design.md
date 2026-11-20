# Technical Design Document: Role-Based Authentication Hub & Route Guarding

**Project:** Secure Role-Based Access Control Reference Architecture for Hospital RAG (Capstone CSA4706)  
**Date:** 2026-11-20  
**Status:** Approved by User  
**Topic:** Role-Based Login Hub & Station Route Guarding  

---

## 1. Executive Summary & Problem Statement

In the existing Hospital RAG RBAC system, six role levels are defined (from Chief Medical Officer down to System Administrator). However, the application currently lacks an interactive, multi-role authentication experience:
1. Entering role portals automatically authenticates via hardcoded fallback personas in `portal_common.js`.
2. The root landing page acts only as a direct launcher without credential challenges or verification.
3. Evaluators and clinical users have no role-tailored login screen reflecting distinct clearance levels, data scopes, and departmental identities.

This design implements a unified **Role-Based Login Hub** (`/login`) featuring dedicated tabs for each of the six hospital roles, database-backed salted SHA-256 password hashing, quick-fill demo presets for seamless academic evaluation, and fail-closed route guards across all portal endpoints.

---

## 2. Architecture & Authentication Flow

```
[ Unauthenticated User / Evaluator ]
                 |
                 v
        GET / or GET /login
                 |
                 v
   +-------------------------------------------------------------+
   |             Unified Hospital Login Hub (/login)             |
   |                                                             |
   |  [CMO (L5)] [Dept Head (L4)] [Doctor (L3)] [Nurse (L2)] ... |
   +-------------------------------------------------------------+
                 |
                 | 1. Selects Role Tab (or pre-selected via ?role=...)
                 | 2. Enters credentials or clicks "Demo Quick-Fill"
                 | 3. Clicks "Authenticate & Enter Station"
                 v
        POST /api/auth/login { user_id, password }
                 |
        +--------+--------+
        |                 |
  [Valid Hash]      [Invalid / Mismatch]
        |                 |
        v                 v
Issue signed JWT    HTTP 401 Unauthorized
Store session       Fail-closed alert displayed
Redirect to:
/portal/<role>
```

---

## 3. Database Schema & Password Security

### 3.1 SQLite Migration (`Capstone/data/hospital.db`)
Add `password_hash` column to the existing `personas` table:
```sql
ALTER TABLE personas ADD COLUMN password_hash TEXT;
```

### 3.2 Salted SHA-256 Hashing Algorithm
To avoid platform-dependent native C extensions while maintaining cryptographic security, password hashing uses Python's standard library `hashlib`:
- Format: `salt$sha256_hex`
- Salt: 16 cryptographically random bytes (hex-encoded)
- Verification: `hashlib.sha256((salt + password).encode('utf-8')).hexdigest() == stored_hash`

### 3.3 Pre-Seeded Academic Demo Personas
| Role | Level | User ID | Name | Department | Demo Password | Scope / Permissions |
| :--- | :---: | :--- | :--- | :--- | :--- | :--- |
| **Chief Medical Officer** | 5 | `CMO_501` | Dr. Arthur Campbell | Exec / Clinical Quality | `cmo@123` | Hospital-wide all patients |
| **Department Head** | 4 | `DH_401` | Dr. Helena Vance | Cardiology | `dept@123` | Cardiology department ward |
| **Treating Doctor** | 3 | `DR_302` | Dr. Rohit Sharma | Cardiology | `doc@123` | Care-team & active referrals |
| **Nurse** | 2 | `RN_201` | Nurse Sarah Connor | Cardiology | `nurse@123` | Assigned Ward 3 (PII masked) |
| **Front Desk / Billing** | 1 | `FD_101` | Alex Jenkins | Patient Administration | `billing@123` | Billing & insurance only |
| **System Administrator** | 0 | `SYS_999` | Root System Admin | IT Operations | `admin@123` | Control panel only (0 patient data) |

---

## 4. API Endpoints & Contract Updates

### 4.1 `POST /api/auth/login`
- **Request Body (Pydantic v2 `LoginRequest`)**:
  ```json
  {
    "user_id": "DR_302",
    "password": "doc@123"
  }
  ```
  *(Note: `password` is optional in the Pydantic schema to maintain backward compatibility with existing automated test fixtures, but enforced in production UI authentication.)*
- **Response (200 OK)**:
  ```json
  {
    "token": "<Signed HMAC-SHA256 JWT>",
    "persona": {
      "user_id": "DR_302",
      "name": "Dr. Rohit Sharma",
      "role": "Treating Doctor",
      "level": 3,
      "department": "Cardiology",
      "assigned_ward": "Ward 3",
      "assigned_patients": ["P-1042", "P-2210", "P-5592"],
      "description": "..."
    },
    "expires_in_minutes": 60,
    "token_type": "Bearer"
  }
  ```
- **Error Responses**:
  - `401 Unauthorized`: `{"detail": "FAIL-CLOSED: Invalid credentials for staff member."}`
  - `401 Unauthorized`: `{"detail": "FAIL-CLOSED: Unknown user identity 'XYZ'. Request refused."}`

### 4.2 Web Route Registration (`src/api/app.py`)
- `GET /`: Serves `web/login.html` as the primary hospital entry point.
- `GET /login`: Serves `web/login.html`.
- `GET /portal/gateway`: Continues to serve `web/index.html` as the directory matrix overview.

---

## 5. Frontend Specification

### 5.1 Unified Login Hub (`web/login.html` & `web/login.js`)
1. **Brand Header**: Medical SVG emblem, "Hospital Clinical RAG System", active policy and fail-closed security badges.
2. **Role Navigation Tabs**: 6 tab items with level tags (`L5` through `L0`). Selecting a tab updates the active role state and synchronizes URL query `?role=<key>`.
3. **Role Specific Context Banner**:
   - Title (e.g., "Treating Doctor Clinical Station")
   - Persona name and department badge
   - Security level pill and data access summary
4. **Interactive Credentials Form**:
   - Staff ID input
   - Password input with toggle visibility eye icon
   - "Quick-Fill Demo Account" button
   - Submit button with loading state
   - Dismissible error banner for failed authentication
5. **Role Capability Card**: Brief explanation of what this role is authorized to query under the fail-closed security policy.

### 5.2 Deep-Linking via URL Parameters
- Navigating to `/login?role=doctor` auto-activates the Doctor tab.
- Navigating to `/login?role=nurse&msg=auth_required` activates the Nurse tab and displays: *"Authentication required: Please log in to access the Nurse Ward Station."*

### 5.3 Strict Route Guarding & Header Navigation (`web/portal_common.js`)
1. **Session Enforcement**:
   - `initPortal(roleName, minLevel, isClinical)` checks `sessionStorage.getItem("hospital_auth")`.
   - If missing, or if `persona.role !== roleName`, the user is immediately redirected to `/login?role=<key>&msg=auth_required`.
   - Auto-login fallback is removed to enforce authentic security.
2. **Portal Header Controls**:
   - Added **"Log Out"** button (`#logoutBtn`): Clears `sessionStorage.removeItem("hospital_auth")` and redirects to `/login`.
   - "Switch Portal" link directs to `/login` to switch credentials cleanly.

---

## 6. Testing & Quality Assurance

1. **Unit & Integration Tests (`tests/test_portal_pages.py`)**:
   - Verify `/login` returns HTTP 200 and includes all 6 role tab identifiers.
   - Verify static assets `/login.js` and `/style.css` load properly.
2. **Identity & Auth Tests (`tests/test_module1_identity_policy.py`)**:
   - Verify valid password authentication returns verified JWT and persona.
   - Verify incorrect password raises `AuthenticationError` / HTTP 401.
   - Verify backward compatibility for password-less programmatic calls where permitted.
3. **Regression Suite**:
   - All 48 existing pytest tests must pass without regressions.
