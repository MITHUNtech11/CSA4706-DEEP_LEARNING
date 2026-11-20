# Role-Based Login Hub & Route Guarding Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Build an authentic, database-backed role-based login hub with separate tabs for all 6 hospital tiers, demo quick-fill presets, and strict route guarding across all clinical stations.

**Architecture:** Salted SHA-256 password hashing in SQLite `personas` table validated via FastAPI `/api/auth/login`. Responsive frontend tabbed interface at `/login` with dynamic role contexts and deep-linking query parameters. Client-side route guards in `portal_common.js` redirecting unauthenticated traffic to `/login?role=<key>`.

**Tech Stack:** Python 3.11, FastAPI, SQLite3, hashlib (PBKDF2/SHA-256), Vanilla JavaScript (ES6+), HTML5/CSS3, Pytest.

**Spec:** [2026-11-20-role-based-login-hub-design.md](file:///C:/Users/mithu/OneDrive/Desktop/CSA4706%20-%20DEEP%20LEARNING/docs/superpowers/specs/2026-11-20-role-based-login-hub-design.md)

## Global Constraints
- Zero new external Python dependencies; use Python standard library `hashlib` for salted SHA-256 hashing.
- Maintain fail-closed architecture: unknown users or mismatched passwords return HTTP 401 Unauthorized.
- Maintain backward-compatibility for existing automated tests: programmatic calls with `password=None` remain supported if permitted by test fixtures.
- Preserve consistent visual design tokens from `style.css` (fonts: Poppins & JetBrains Mono, sage green & medical blue theme).
- All 48 existing pytest regression tests must remain green.

## Review Focus
1. Password mismatch: Sending an incorrect password for an existing persona returns HTTP 401 with fail-closed message.
2. Direct URL tampering: An unauthenticated browser hitting `/portal/doctor` is redirected immediately to `/login?role=doctor&msg=auth_required`.
3. Cross-role session spoofing: A user authenticated as `Nurse` hitting `/portal/cmo` is redirected to `/login?role=cmo&msg=auth_required`.
4. Quick-fill accuracy: Clicking "Quick-Fill Demo Account" on any role tab accurately populates that role's exact User ID and demo password.
5. Session cleanup: Clicking "Log Out" in any station header flushes `sessionStorage` and returns to `/login`.

---

### Task 1: Database Migration & Salted Password Hashing Helper

**Files:**
- Modify: `Capstone/src/module1_identity_policy/idp_service.py:1-100`
- Test: `Capstone/tests/test_module1_identity_policy.py`

**Interfaces:**
- Produces:
  - `hash_password(password: str, salt: Optional[str] = None) -> str`: Returns `salt$sha256_hex`.
  - `verify_password(password: str, hashed: str) -> bool`: Verifies candidate against stored `salt$hash`.
  - `IdPService.ensure_password_schema()`: Migrates `personas` table and seeds default demo passwords.

- [ ] **Step 1: Write the failing tests for password hashing and verification**

In `Capstone/tests/test_module1_identity_policy.py`:
```python
def test_password_hashing_and_verification():
    from src.module1_identity_policy.idp_service import hash_password, verify_password
    hashed = hash_password("doc@123")
    assert "$" in hashed
    assert verify_password("doc@123", hashed) is True
    assert verify_password("wrong_password", hashed) is False
```

- [ ] **Step 2: Run test to verify it fails**

Run: `.\.venv\Scripts\python.exe -m pytest Capstone/tests/test_module1_identity_policy.py -k test_password_hashing_and_verification`  
Expected: FAIL with `ImportError: cannot import name 'hash_password'`

- [ ] **Step 3: Implement `hash_password`, `verify_password`, and `ensure_password_schema` in `Capstone/src/module1_identity_policy/idp_service.py`**

Implement helper functions:
```python
import os
import hashlib

def hash_password(password: str, salt: str = None) -> str:
    if salt is None:
        salt = os.urandom(16).hex()
    hashed = hashlib.sha256((salt + password).encode("utf-8")).hexdigest()
    return f"{salt}${hashed}"

def verify_password(password: str, hashed_str: str) -> bool:
    if not hashed_str or "$" not in hashed_str:
        return False
    salt, expected_hash = hashed_str.split("$", 1)
    actual_hash = hashlib.sha256((salt + password).encode("utf-8")).hexdigest()
    return actual_hash == expected_hash
```
In `IdPService.__init__`, call `self.ensure_password_schema()`:
- Check if `password_hash` column exists in `personas`. If not: `ALTER TABLE personas ADD COLUMN password_hash TEXT;`
- Seed default passwords:
  - `CMO_501`: `cmo@123`
  - `DH_401`: `dept@123`
  - `DR_302`: `doc@123`
  - `RN_201`: `nurse@123`
  - `FD_101`: `billing@123`
  - `SYS_999`: `admin@123`

- [ ] **Step 4: Run test to verify it passes**

Run: `.\.venv\Scripts\python.exe -m pytest Capstone/tests/test_module1_identity_policy.py -k test_password_hashing_and_verification`  
Expected: PASS

- [ ] **Step 5: Commit Task 1**

```powershell
git add Capstone/src/module1_identity_policy/idp_service.py Capstone/tests/test_module1_identity_policy.py
git commit -m "feat: add salted SHA-256 password hashing and persona schema migration"
```

---

### Task 2: API Login Authentication Logic & Schema Updates

**Files:**
- Modify: `Capstone/src/api/schemas.py:9-12`
- Modify: `Capstone/src/module1_identity_policy/idp_service.py:46-69`
- Modify: `Capstone/src/api/routes.py:132-139`
- Test: `Capstone/tests/test_module1_identity_policy.py`

**Interfaces:**
- Consumes: `verify_password` from Task 1.
- Produces: `IdPService.login(user_id: str, password: Optional[str] = None) -> Dict[str, Any]`

- [ ] **Step 1: Write the failing tests for credential authentication**

In `Capstone/tests/test_module1_identity_policy.py`:
```python
def test_login_valid_credentials():
    from src.module1_identity_policy.idp_service import IdPService
    idp = IdPService()
    res = idp.login("DR_302", "doc@123")
    assert "token" in res
    assert res["persona"]["role"] == "Treating Doctor"

def test_login_invalid_password_fails_closed():
    import pytest
    from src.module1_identity_policy.idp_service import IdPService, AuthenticationError
    idp = IdPService()
    with pytest.raises(AuthenticationError, match="FAIL-CLOSED: Invalid credentials"):
        idp.login("DR_302", "wrong_pass")
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `.\.venv\Scripts\python.exe -m pytest Capstone/tests/test_module1_identity_policy.py -k "test_login_valid_credentials or test_login_invalid_password_fails_closed"`  
Expected: FAIL

- [ ] **Step 3: Update `LoginRequest` in `src/api/schemas.py` and `login` in `idp_service.py` & `routes.py`**

In `src/api/schemas.py`:
```python
class LoginRequest(BaseModel):
    user_id: str = Field(..., json_schema_extra={"example": "DR_302"})
    password: Optional[str] = Field(None, json_schema_extra={"example": "doc@123"})
```
In `IdPService.login(user_id: str, password: Optional[str] = None)`:
- Query `password_hash` alongside persona data.
- If `password` is provided, check `verify_password(password, persona["password_hash"])`. If False, raise `AuthenticationError("FAIL-CLOSED: Invalid credentials for staff member.")`.
- If `password` is None (backward compatibility), issue token.
In `routes.py`:
- Pass `req.password` to `idp_service.login(req.user_id, req.password)`.

- [ ] **Step 4: Run tests to verify they pass**

Run: `.\.venv\Scripts\python.exe -m pytest Capstone/tests/test_module1_identity_policy.py -k "test_login_valid_credentials or test_login_invalid_password_fails_closed"`  
Expected: PASS

- [ ] **Step 5: Commit Task 2**

```powershell
git add Capstone/src/api/schemas.py Capstone/src/module1_identity_policy/idp_service.py Capstone/src/api/routes.py Capstone/tests/test_module1_identity_policy.py
git commit -m "feat: enforce credential validation on login endpoint"
```

---

### Task 3: Unified Role Login Hub UI (`web/login.html` & `web/login.js`)

**Files:**
- Create: `Capstone/web/login.html`
- Create: `Capstone/web/login.js`
- Modify: `Capstone/src/api/app.py:100-128`
- Test: `Capstone/tests/test_portal_pages.py`

**Interfaces:**
- Produces:
  - Route `/login` serving `login.html`.
  - Route `/` serving `login.html`.
  - Client script `login.js` managing tab switching, demo quick-fill, form submission, and redirection.

- [ ] **Step 1: Write test for `/login` route**

In `Capstone/tests/test_portal_pages.py`:
```python
def test_login_hub_accessible(client):
    res = client.get("/login")
    assert res.status_code == 200
    assert "Hospital Clinical RAG" in res.text
    assert "Role Login Hub" in res.text
    assert "Chief Medical Officer" in res.text
    assert "Treating Doctor" in res.text
    assert 'src="/login.js"' in res.text
```

- [ ] **Step 2: Run test to verify it fails**

Run: `.\.venv\Scripts\python.exe -m pytest Capstone/tests/test_portal_pages.py -k test_login_hub_accessible`  
Expected: FAIL (404 Not Found)

- [ ] **Step 3: Implement `login.html`, `login.js`, and mount routes in `app.py`**

1. In `src/api/app.py`:
   - `@app.get("/login") def login_page(): return FileResponse(WEB_DIR / "login.html")`
   - `@app.get("/") def root_page(): return FileResponse(WEB_DIR / "login.html")`
2. Create `Capstone/web/login.html`:
   - Hospital banner with policy indicators.
   - 6 role tabs with levels: CMO (L5), Dept Head (L4), Doctor (L3), Nurse (L2), Billing (L1), Admin (L0).
   - Dynamic role card: clearance badge, scope summary, Staff ID input, Password input with eye toggle.
   - Quick-Fill Demo Account chip.
   - Submit button with loading spinner.
   - Alert container for fail-closed errors and messages.
3. Create `Capstone/web/login.js`:
   - Role configuration dictionary containing user IDs, demo passwords, target portal URLs, and permissions descriptions.
   - Tab switching function.
   - URL parameter parser for `?role=...&msg=...`.
   - Form submission handler calling `/api/auth/login`. On success, saves to `sessionStorage` and redirects to `targetUrl`.

- [ ] **Step 4: Run test to verify it passes**

Run: `.\.venv\Scripts\python.exe -m pytest Capstone/tests/test_portal_pages.py -k test_login_hub_accessible`  
Expected: PASS

- [ ] **Step 5: Commit Task 3**

```powershell
git add Capstone/web/login.html Capstone/web/login.js Capstone/src/api/app.py Capstone/tests/test_portal_pages.py
git commit -m "feat: implement unified role-based login hub and routes"
```

---

### Task 4: Strict Route Guarding & Header Logout Integration

**Files:**
- Modify: `Capstone/web/portal_common.js:20-150`
- Modify: `Capstone/web/index.html:60-150`
- Test: `Capstone/tests/test_portal_pages.py`

**Interfaces:**
- Consumes: Session storage format `{ token, persona }` from `login.js`.
- Produces: Strict guard redirecting unauthenticated requests to `/login?role=<key>&msg=auth_required` and working "Log Out" action.

- [ ] **Step 1: Write test verifying portals require script guard and contain logout UI**

In `Capstone/tests/test_portal_pages.py`:
```python
def test_portals_include_logout_capability(client):
    for route in ["/portal/doctor", "/portal/nurse", "/portal/cmo", "/portal/dept-head", "/portal/billing", "/portal/admin"]:
        res = client.get(route)
        assert res.status_code == 200
        assert 'src="/portal_common.js"' in res.text
```

- [ ] **Step 2: Update `portal_common.js` with strict route guard and logout button**

1. In `portal_common.js` `initPortal`:
   - Remove auto-login fallback.
   - If `!stored` or `parsed.persona.role !== roleName`:
     - Determine `roleKey` (e.g. `doctor`, `nurse`, etc.).
     - `window.location.href = `/login?role=${roleKey}&msg=auth_required`;`
     - Return early.
2. In `renderPortalHeader`:
   - Add a `<button class="btn btn-outline" id="logoutBtn">Log Out</button>`.
   - Attach listener:
     ```javascript
     document.getElementById("logoutBtn").addEventListener("click", () => {
       sessionStorage.removeItem("hospital_auth");
       window.location.href = "/login";
     });
     ```
3. In `web/index.html`:
   - Update portal launch action so users are directed to login if not already authenticated for that station.

- [ ] **Step 3: Run test to verify portal pages**

Run: `.\.venv\Scripts\python.exe -m pytest Capstone/tests/test_portal_pages.py`  
Expected: PASS

- [ ] **Step 4: Commit Task 4**

```powershell
git add Capstone/web/portal_common.js Capstone/web/index.html Capstone/tests/test_portal_pages.py
git commit -m "feat: enforce strict route guards and add portal header logout"
```

---

### Task 5: Comprehensive Verification & Regression Suite

**Files:**
- Test: `Capstone/tests/test_portal_pages.py`
- Test: `Capstone/tests/test_module1_identity_policy.py`
- Test: `Capstone/tests/test_end_to_end_pipeline.py`

- [ ] **Step 1: Run full pytest test suite across all modules**

Run: `.\.venv\Scripts\python.exe -m pytest Capstone/tests/ -v`  
Expected: All tests PASS with 0 failures and 0 regressions.

- [ ] **Step 2: Run security evaluation benchmark**

Run: `.\.venv\Scripts\python.exe Capstone/scripts/run_security_eval.py`  
Expected: 100% PASS on all security benchmark adversarial attacks.

- [ ] **Step 3: Commit all remaining changes and update documentation**

```powershell
git add Capstone/
git commit -m "docs: finalize role login hub verification and readiness"
```
