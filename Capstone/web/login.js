// Hospital RAG RBAC - Role Login Hub Client Script

const ROLES = {
  cmo: {
    key: "cmo",
    roleName: "Chief Medical Officer",
    level: 5,
    levelName: "Level 5",
    userId: "CMO_501",
    personaName: "Dr. Arthur Campbell",
    department: "Executive / Clinical Quality",
    password: "cmo@123",
    portalUrl: "/portal/cmo",
    title: "Chief Medical Officer Portal",
    scope: "Hospital-wide clinical quality oversight across all wards and specialties. Full clinical record and identifier access.",
    permissions: [
      { text: "Full Records: Yes", allowed: true },
      { text: "Clinical Details: Yes", allowed: true },
      { text: "Identifiers: Yes", allowed: true },
      { text: "Scope: All Patients", allowed: true }
    ]
  },
  "dept-head": {
    key: "dept-head",
    roleName: "Department Head",
    level: 4,
    levelName: "Level 4",
    userId: "DH_401",
    personaName: "Dr. Helena Vance",
    department: "Cardiology",
    password: "dept@123",
    portalUrl: "/portal/dept-head",
    title: "Department Head Portal",
    scope: "Cardiology department census, physician assignments, and clinical progress notes. Out-of-department queries refused.",
    permissions: [
      { text: "Full Records: Yes", allowed: true },
      { text: "Clinical Details: Yes", allowed: true },
      { text: "Identifiers: Yes", allowed: true },
      { text: "Scope: Own Dept (Cardiology)", cond: true }
    ]
  },
  doctor: {
    key: "doctor",
    roleName: "Treating Doctor",
    level: 3,
    levelName: "Level 3",
    userId: "DR_302",
    personaName: "Dr. Rohit Sharma",
    department: "Cardiology",
    password: "doc@123",
    portalUrl: "/portal/doctor",
    title: "Treating Doctor Clinical Station",
    scope: "Care-team assigned patients and active cross-department referrals (e.g. P-3307). Expired referrals (P-4180) strictly refused.",
    permissions: [
      { text: "Full Records: Care-Team / Referral", allowed: true },
      { text: "Clinical Details: Yes", allowed: true },
      { text: "Identifiers: Yes", allowed: true },
      { text: "Scope: Assigned Patients", cond: true }
    ]
  },
  nurse: {
    key: "nurse",
    roleName: "Nurse",
    level: 2,
    levelName: "Level 2",
    userId: "RN_201",
    personaName: "Nurse Sarah Connor",
    department: "Cardiology (Ward 3)",
    password: "nurse@123",
    portalUrl: "/portal/nurse",
    title: "Nurse Ward Station",
    scope: "Bedside clinical care for assigned Ward 3 patients. Allowed general clinical details; phone numbers and PII masked.",
    permissions: [
      { text: "Full Records: No", denied: true },
      { text: "Clinical Details: Yes (Assigned)", allowed: true },
      { text: "Identifiers: Masked", cond: true },
      { text: "Scope: Assigned Ward 3", cond: true }
    ]
  },
  billing: {
    key: "billing",
    roleName: "Front Desk / Billing Staff",
    level: 1,
    levelName: "Level 1",
    userId: "FD_101",
    personaName: "Alex Jenkins",
    department: "Patient Administration",
    password: "billing@123",
    portalUrl: "/portal/billing",
    title: "Front Desk & Billing Desk",
    scope: "Patient demographics, insurance, and inpatient billing balances. Clinical notes, diagnoses, and medical records strictly blocked.",
    permissions: [
      { text: "Full Records: No", denied: true },
      { text: "Clinical Details: Billing Only", cond: true },
      { text: "Identifiers: Contact Only", cond: true },
      { text: "Scope: Task-Specific", cond: true }
    ]
  },
  admin: {
    key: "admin",
    roleName: "System Administrator",
    level: 0,
    levelName: "Level 0",
    userId: "SYS_999",
    personaName: "Root System Admin",
    department: "IT Operations",
    password: "admin@123",
    portalUrl: "/portal/admin",
    title: "System Admin Security Console",
    scope: "Separation of Duties: SHA-256 audit log verification, policy governance, and tamper engine. Zero access to patient clinical data.",
    permissions: [
      { text: "Full Records: No", denied: true },
      { text: "Clinical Details: No", denied: true },
      { text: "Identifiers: No", denied: true },
      { text: "Scope: IT Operations Only", cond: true }
    ]
  }
};

let activeRoleKey = "doctor";

document.addEventListener("DOMContentLoaded", () => {
  initLoginHub();
});

function initLoginHub() {
  const urlParams = new URLSearchParams(window.location.search);
  const requestedRole = urlParams.get("role");
  const msgParam = urlParams.get("msg");

  if (requestedRole && ROLES[requestedRole]) {
    activeRoleKey = requestedRole;
  }

  // Display notice banner if redirected from an unauthenticated portal attempt
  if (msgParam === "auth_required") {
    const banner = document.getElementById("noticeBanner");
    if (banner) {
      banner.style.display = "block";
      const targetRole = ROLES[activeRoleKey] ? ROLES[activeRoleKey].roleName : "Hospital Station";
      banner.innerHTML = `<strong>Authentication Required:</strong> Please log in with authorized credentials to access the <em>${targetRole}</em>.`;
    }
  }

  // Bind tab buttons
  const tabButtons = document.querySelectorAll(".role-tab-btn");
  tabButtons.forEach(btn => {
    btn.addEventListener("click", () => {
      const role = btn.getAttribute("data-role");
      if (role && ROLES[role]) {
        switchRoleTab(role);
      }
    });
  });

  // Bind quick-fill demo button
  const qfBtn = document.getElementById("quickFillBtn");
  if (qfBtn) {
    qfBtn.addEventListener("click", handleQuickFill);
  }

  // Bind password toggle
  const toggleBtn = document.getElementById("togglePasswordBtn");
  const pwdInput = document.getElementById("passwordInput");
  if (toggleBtn && pwdInput) {
    toggleBtn.addEventListener("click", () => {
      if (pwdInput.type === "password") {
        pwdInput.type = "text";
        toggleBtn.textContent = "Hide Password";
      } else {
        pwdInput.type = "password";
        toggleBtn.textContent = "Show Password";
      }
    });
  }

  // Bind form submit
  const form = document.getElementById("roleLoginForm");
  if (form) {
    form.addEventListener("submit", handleLoginSubmit);
  }

  // Render initial active role
  switchRoleTab(activeRoleKey, false);
}

function switchRoleTab(roleKey, updateUrl = true) {
  if (!ROLES[roleKey]) return;
  activeRoleKey = roleKey;
  const r = ROLES[roleKey];

  // Update tabs active state
  document.querySelectorAll(".role-tab-btn").forEach(btn => {
    if (btn.getAttribute("data-role") === roleKey) {
      btn.classList.add("active");
    } else {
      btn.classList.remove("active");
    }
  });

  // Update card elements
  const titleEl = document.getElementById("roleCardTitle");
  const badgeEl = document.getElementById("roleLevelBadge");
  const personaEl = document.getElementById("rolePersonaSub");
  const deptEl = document.getElementById("roleDeptPill");
  const scopeEl = document.getElementById("roleScopeDesc");
  const permsEl = document.getElementById("rolePermsList");
  const qfLabel = document.getElementById("quickFillLabel");
  const submitText = document.getElementById("submitBtnText");
  const errBox = document.getElementById("loginErrorBox");

  if (titleEl) titleEl.textContent = r.title;
  if (badgeEl) badgeEl.textContent = r.levelName;
  if (personaEl) personaEl.textContent = `${r.personaName} | ${r.department}`;
  if (deptEl) deptEl.textContent = r.department.split('/')[0].trim();
  if (scopeEl) scopeEl.textContent = r.scope;
  if (qfLabel) qfLabel.textContent = `Quick-Fill Demo Account (${r.userId} / ${r.password})`;
  if (submitText) submitText.textContent = `Authenticate & Enter ${r.roleName} Station`;

  if (errBox) {
    errBox.style.display = "none";
    errBox.textContent = "";
  }

  // Render permissions list
  if (permsEl) {
    permsEl.innerHTML = r.permissions.map(p => {
      let cls = "perm-allowed";
      if (p.denied) cls = "perm-denied";
      if (p.cond) cls = "perm-conditional";
      return `<span class="perm-item ${cls}">${p.text}</span>`;
    }).join("");
  }

  // Pre-fill inputs with the selected role's ID and empty password (or placeholder)
  const uidInput = document.getElementById("userIdInput");
  const pwdInput = document.getElementById("passwordInput");
  if (uidInput) uidInput.value = r.userId;
  if (pwdInput) {
    pwdInput.value = "";
    pwdInput.placeholder = `Enter password for ${r.roleName}`;
  }

  // Update URL without reloading
  if (updateUrl && window.history && window.history.replaceState) {
    const url = new URL(window.location);
    url.searchParams.set("role", roleKey);
    window.history.replaceState({}, "", url);
  }
}

function handleQuickFill() {
  const r = ROLES[activeRoleKey];
  if (!r) return;
  const uidInput = document.getElementById("userIdInput");
  const pwdInput = document.getElementById("passwordInput");
  if (uidInput) uidInput.value = r.userId;
  if (pwdInput) pwdInput.value = r.password;

  // Clear any existing error
  const errBox = document.getElementById("loginErrorBox");
  if (errBox) errBox.style.display = "none";
}

async function handleLoginSubmit(e) {
  if (e) e.preventDefault();
  const r = ROLES[activeRoleKey];
  if (!r) return;

  const uidInput = document.getElementById("userIdInput");
  const pwdInput = document.getElementById("passwordInput");
  const errBox = document.getElementById("loginErrorBox");
  const submitBtn = document.getElementById("submitLoginBtn");

  const userId = uidInput ? uidInput.value.trim() : "";
  const password = pwdInput ? pwdInput.value.trim() : "";

  if (!userId || !password) {
    if (errBox) {
      errBox.style.display = "block";
      errBox.textContent = "Please provide both Staff ID and Password.";
    }
    return;
  }

  if (submitBtn) {
    submitBtn.disabled = true;
    submitBtn.style.opacity = "0.7";
  }

  try {
    const res = await fetch("/api/auth/login", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ user_id: userId, password: password })
    });

    const data = await res.json();

    if (!res.ok) {
      const msg = data.detail || "Authentication refused by Hospital IdP.";
      throw new Error(msg);
    }

    // Save session in sessionStorage
    sessionStorage.setItem("hospital_auth", JSON.stringify({
      token: data.token,
      persona: data.persona
    }));

    // Redirect to the portal
    window.location.href = r.portalUrl;
  } catch (err) {
    if (errBox) {
      errBox.style.display = "block";
      errBox.textContent = err.message || "Failed to authenticate.";
    }
    if (submitBtn) {
      submitBtn.disabled = false;
      submitBtn.style.opacity = "1";
    }
  }
}
