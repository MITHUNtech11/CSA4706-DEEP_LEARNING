// Hospital RAG RBAC - Role Login Hub Client Engine

const ROLES = {
  cmo: {
    key: "cmo",
    roleName: "Chief Medical Officer",
    level: 5,
    levelName: "Level 5 Clearance",
    userId: "CMO_501",
    personaName: "Dr. Arthur Campbell",
    department: "Executive / Clinical Quality",
    password: "cmo@123",
    portalUrl: "/portal/cmo",
    title: "Chief Medical Officer Station",
    scopeBadge: "All Hospital Patients",
    rules: [
      {
        icon: "📋",
        title: "Full Medical Record Access",
        badge: "ALLOWED",
        badgeClass: "badge-allowed",
        desc: "Full operative notes, ICU telemetry, pathology reports, and comprehensive medical histories across all hospital departments."
      },
      {
        icon: "🩺",
        title: "Clinical Diagnoses & Consults",
        badge: "ALLOWED",
        badgeClass: "badge-allowed",
        desc: "Unrestricted retrieval of multi-specialty progress notes, attending physician consultations, and clinical treatment plans."
      },
      {
        icon: "🆔",
        title: "Personal Identifiers (PII)",
        badge: "UNMASKED",
        badgeClass: "badge-allowed",
        desc: "Full unmasked patient names, phone numbers, and addresses for hospital-wide clinical quality audits and regulatory compliance."
      },
      {
        icon: "👥",
        title: "Patient Population Scope",
        badge: "ALL WARDS",
        badgeClass: "badge-allowed",
        desc: "Authorized to query all active inpatients, discharged patients, ICU cases, and outpatients across Cardiology, Oncology, and Orthopedics."
      },
      {
        icon: "🛡️",
        title: "Strict Refusal Boundaries",
        badge: "NONE",
        badgeClass: "badge-scope",
        desc: "Executive tier operates with zero department fences. Every query is logged into the SHA-256 hash-chain for accountability."
      }
    ]
  },
  "dept-head": {
    key: "dept-head",
    roleName: "Department Head",
    level: 4,
    levelName: "Level 4 Clearance",
    userId: "DH_401",
    personaName: "Dr. Helena Vance",
    department: "Cardiology Department",
    password: "dept@123",
    portalUrl: "/portal/dept-head",
    title: "Cardiology Department Head Station",
    scopeBadge: "Cardiology Dept Scope",
    rules: [
      {
        icon: "📋",
        title: "Department Full Records",
        badge: "OWN DEPT ONLY",
        badgeClass: "badge-allowed",
        desc: "Full operative notes, echo reports, and attending physician assignments for Cardiology patients (e.g. P-1042, P-2210, P-5592)."
      },
      {
        icon: "🩺",
        title: "Clinical Progress Notes",
        badge: "ALLOWED",
        badgeClass: "badge-allowed",
        desc: "Authorized to review attending doctor rounds, cardiology diagnostics, and ward physician performance."
      },
      {
        icon: "🆔",
        title: "Personal Identifiers (PII)",
        badge: "UNMASKED",
        badgeClass: "badge-allowed",
        desc: "Identified patient data permitted exclusively for patients admitted to the Cardiology census."
      },
      {
        icon: "🚫",
        title: "Cross-Department Fence",
        badge: "BLOCKED",
        badgeClass: "badge-denied",
        desc: "Queries for out-of-department records (e.g. Oncology P-3307 or Orthopedics) are strictly refused at the deterministic SQL layer."
      },
      {
        icon: "🛡️",
        title: "Fail-Closed Boundary",
        badge: "FAIL-CLOSED",
        badgeClass: "badge-scope",
        desc: "Department scope is bound to the signed JWT. Prompt injection claiming other roles will not override SQL pre-retrieval filters."
      }
    ]
  },
  doctor: {
    key: "doctor",
    roleName: "Treating Doctor",
    level: 3,
    levelName: "Level 3 Clearance",
    userId: "DR_302",
    personaName: "Dr. Rohit Sharma",
    department: "Cardiology Department",
    password: "doc@123",
    portalUrl: "/portal/doctor",
    title: "Treating Doctor Clinical Station",
    scopeBadge: "Care-Team + Active Referrals",
    rules: [
      {
        icon: "📋",
        title: "Care-Team Medical Records",
        badge: "CARE-TEAM ONLY",
        badgeClass: "badge-allowed",
        desc: "Full clinical and operative notes permitted for assigned care-team patients (P-1042, P-2210, P-5592)."
      },
      {
        icon: "🔄",
        title: "Cross-Department Referrals",
        badge: "ACTIVE ONLY",
        badgeClass: "badge-allowed",
        desc: "Granted access to active inter-departmental consultation referrals (e.g. Active Oncology referral for patient P-3307)."
      },
      {
        icon: "⏳",
        title: "Expired Referrals",
        badge: "STRICTLY BLOCKED",
        badgeClass: "badge-denied",
        desc: "Expired referrals (such as Orthopedic referral for patient P-4180) return zero records from disk or memory."
      },
      {
        icon: "🆔",
        title: "Personal Identifiers (PII)",
        badge: "ALLOWED",
        badgeClass: "badge-allowed",
        desc: "Demographics and names permitted for direct patient care of assigned care-team patients."
      },
      {
        icon: "🛡️",
        title: "Factual Grounding Guard",
        badge: "ENFORCED",
        badgeClass: "badge-scope",
        desc: "Algorithm 1 output guard verifies all numerical vitals and lab figures match retrieved context before delivery."
      }
    ]
  },
  nurse: {
    key: "nurse",
    roleName: "Nurse",
    level: 2,
    levelName: "Level 2 Clearance",
    userId: "RN_201",
    personaName: "Nurse Sarah Connor",
    department: "Cardiology (Ward 3)",
    password: "nurse@123",
    portalUrl: "/portal/nurse",
    title: "Nurse Ward Station",
    scopeBadge: "Ward 3 Bedside Care",
    rules: [
      {
        icon: "🩺",
        title: "Bedside Clinical Details",
        badge: "ALLOWED (ASSIGNED)",
        badgeClass: "badge-allowed",
        desc: "Current vitals, medication administration schedules, and bedside nursing instructions for Ward 3 patients."
      },
      {
        icon: "🔒",
        title: "Full Operative Notes",
        badge: "DENIED",
        badgeClass: "badge-denied",
        desc: "In-depth surgeon operative dictations, psychiatric notes, and cross-department histories are blocked from retrieval."
      },
      {
        icon: "🙈",
        title: "Personal Identifiers (PII)",
        badge: "MASKED",
        badgeClass: "badge-masked",
        desc: "Phone numbers, social security numbers, and direct contact details are redacted with [REDACTED PHONE] at Output Guard."
      },
      {
        icon: "🚪",
        title: "Ward Boundary Control",
        badge: "WARD 3 ONLY",
        badgeClass: "badge-scope",
        desc: "Bedside nurse scope is restricted to assigned Ward 3 beds. Unassigned patient queries trigger automatic refusal."
      },
      {
        icon: "🛡️",
        title: "Slide 3 Compliance",
        badge: "PROTOTYPE 1",
        badgeClass: "badge-allowed",
        desc: "Implements Slide 3 benchmark requirements: vital signs permitted, phone numbers masked, surgical notes refused."
      }
    ]
  },
  billing: {
    key: "billing",
    roleName: "Front Desk / Billing Staff",
    level: 1,
    levelName: "Level 1 Clearance",
    userId: "FD_101",
    personaName: "Alex Jenkins",
    department: "Patient Administration",
    password: "billing@123",
    portalUrl: "/portal/billing",
    title: "Front Desk & Billing Station",
    scopeBadge: "Financial & Admissions",
    rules: [
      {
        icon: "💳",
        title: "Billing & Insurance Data",
        badge: "ALLOWED",
        badgeClass: "badge-allowed",
        desc: "Inpatient balances, insurance policy IDs, copays, and admission dates for active patient accounts."
      },
      {
        icon: "🚫",
        title: "Clinical Medical Records",
        badge: "STRICTLY BLOCKED",
        badgeClass: "badge-denied",
        desc: "Clinical diagnoses, doctor notes, operative records, and medication charts are completely inaccessible."
      },
      {
        icon: "👤",
        title: "Demographic Identifiers",
        badge: "CONTACT ONLY",
        badgeClass: "badge-allowed",
        desc: "Patient name, emergency contact, and insurance subscriber numbers for registration and billing lookups."
      },
      {
        icon: "🛡️",
        title: "Privacy Pre-Filtering",
        badge: "FAIL-CLOSED",
        badgeClass: "badge-scope",
        desc: "SQL queries execute with category pre-filter: category IN ('ADMISSIONS', 'BILLING'). Clinical tables are never queried."
      }
    ]
  },
  admin: {
    key: "admin",
    roleName: "System Administrator",
    level: 0,
    levelName: "Level 0 Clearance",
    userId: "SYS_999",
    personaName: "Root System Admin",
    department: "IT Operations & Security",
    password: "admin@123",
    portalUrl: "/portal/admin",
    title: "System Admin Security Console",
    scopeBadge: "IT Control Panel Only",
    rules: [
      {
        icon: "🔐",
        title: "Separation of Duties",
        badge: "ZERO PATIENT DATA",
        badgeClass: "badge-denied",
        desc: "System Administrators manage infrastructure only. Absolute zero access to patient clinical, demographic, or billing records."
      },
      {
        icon: "⛓️",
        title: "SHA-256 Audit Log Verification",
        badge: "AUTHORIZED",
        badgeClass: "badge-allowed",
        desc: "Full access to append-only cryptographic audit chain and automated tamper detection verification engine."
      },
      {
        icon: "📝",
        title: "Dual-Approver Policy Governance",
        badge: "AUTHORIZED",
        badgeClass: "badge-allowed",
        desc: "Review and approve draft access control policies (requires two independent compliance sign-offs to activate)."
      },
      {
        icon: "🚫",
        title: "Clinical Query Refusal",
        badge: "AUTOMATIC REFUSAL",
        badgeClass: "badge-denied",
        desc: "Any prompt asking about a patient name, diagnosis, or health record returns immediate refusal: 'Separation of Duties Violation'."
      }
    ]
  }
};

let currentRoleKey = null;

// Initialize on DOM load
document.addEventListener("DOMContentLoaded", () => {
  initLoginHub();
});

function initLoginHub() {
  const urlParams = new URLSearchParams(window.location.search);
  const requestedRole = urlParams.get("role");
  const msgParam = urlParams.get("msg");

  // Wire password toggle
  const toggleBtn = document.getElementById("stationTogglePassword");
  const pwdInput = document.getElementById("stationPassword");
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

  // Wire quick-fill demo button
  const qfBtn = document.getElementById("stationQuickFillBtn");
  if (qfBtn) {
    qfBtn.addEventListener("click", handleQuickFill);
  }

  // Wire form submit
  const form = document.getElementById("stationLoginForm");
  if (form) {
    form.addEventListener("submit", handleLoginSubmit);
  }

  // Handle redirect notice
  if (msgParam === "auth_required") {
    const noticeText = "<strong>Authentication Required:</strong> Please select your role and sign in with authorized credentials to access clinical stations.";
    const banner1 = document.getElementById("noticeBanner");
    const banner2 = document.getElementById("stationNoticeBox");
    if (banner1) {
      banner1.style.display = "block";
      banner1.innerHTML = noticeText;
    }
    if (banner2) {
      banner2.style.display = "block";
      banner2.innerHTML = noticeText;
    }
  }

  // If a role was passed in the query param (e.g. from an unauthenticated redirect), open Step 2 directly!
  if (requestedRole && ROLES[requestedRole]) {
    selectRole(requestedRole, false);
  } else {
    // Show Step 1 Role Selection Grid by default
    backToRoleSelection(false);
  }
}

/**
 * Step 1 -> Step 2: Opens the focused role station and displays user-friendly access controls.
 */
function selectRole(roleKey, updateHistory = true) {
  if (!ROLES[roleKey]) return;
  currentRoleKey = roleKey;
  const r = ROLES[roleKey];

  // 1. Hide Step 1 (Role Selection), Show Step 2 (Station Details)
  const step1 = document.getElementById("roleSelectionSection");
  const step2 = document.getElementById("roleStationSection");
  if (step1) step1.style.display = "none";
  if (step2) step2.style.display = "block";

  // 2. Update Quick Pill Buttons in Step 2 header
  document.querySelectorAll(".quick-pill-btn").forEach(btn => {
    if (btn.getAttribute("data-role") === roleKey) {
      btn.classList.add("active");
    } else {
      btn.classList.remove("active");
    }
  });

  // 3. Update Station Form Headers
  const titleEl = document.getElementById("stationTitle");
  const personaEl = document.getElementById("stationPersona");
  const badgeEl = document.getElementById("stationLevelBadge");
  const qfText = document.getElementById("stationQuickFillText");
  const submitText = document.getElementById("stationSubmitText");
  const errBox = document.getElementById("stationErrorBox");
  const scopeBadge = document.getElementById("controlScopeBadge");

  if (titleEl) titleEl.textContent = r.title;
  if (personaEl) personaEl.textContent = `${r.personaName} | ${r.department}`;
  if (badgeEl) badgeEl.textContent = r.levelName;
  if (qfText) qfText.textContent = `Quick-Fill Demo Account (${r.userId} / ${r.password})`;
  if (submitText) submitText.textContent = `Authenticate & Enter ${r.roleName} Station`;
  if (scopeBadge) scopeBadge.textContent = r.scopeBadge;

  if (errBox) {
    errBox.style.display = "none";
    errBox.textContent = "";
  }

  // 4. Pre-fill credentials input fields
  const uidInput = document.getElementById("stationUserId");
  const pwdInput = document.getElementById("stationPassword");
  if (uidInput) uidInput.value = r.userId;
  if (pwdInput) {
    pwdInput.value = "";
    pwdInput.placeholder = `Enter password for ${r.roleName}`;
  }

  // 5. Render User-Friendly Access Controls List
  const listEl = document.getElementById("accessControlsList");
  if (listEl) {
    listEl.innerHTML = r.rules.map(rule => `
      <div class="access-rule-item">
        <div class="access-rule-icon" style="background:#f1f5f9;">${rule.icon}</div>
        <div class="access-rule-content">
          <div class="access-rule-row">
            <span class="access-rule-title">${rule.title}</span>
            <span class="${rule.badgeClass}">${rule.badge}</span>
          </div>
          <p class="access-rule-desc">${rule.desc}</p>
        </div>
      </div>
    `).join("");
  }

  // 6. Update URL parameter
  if (updateHistory && window.history && window.history.pushState) {
    const url = new URL(window.location);
    url.searchParams.set("role", roleKey);
    window.history.pushState({ role: roleKey }, "", url);
  }

  // Scroll to top smoothly
  window.scrollTo({ top: 0, behavior: "smooth" });
}

/**
 * Step 2 -> Step 1: Returns to the clean Role Selection Grid.
 */
function backToRoleSelection(updateHistory = true) {
  currentRoleKey = null;

  const step1 = document.getElementById("roleSelectionSection");
  const step2 = document.getElementById("roleStationSection");
  if (step1) step1.style.display = "block";
  if (step2) step2.style.display = "none";

  // Clean URL parameter
  if (updateHistory && window.history && window.history.pushState) {
    const url = new URL(window.location);
    url.searchParams.delete("role");
    window.history.pushState({}, "", url);
  }

  window.scrollTo({ top: 0, behavior: "smooth" });
}

/**
 * Handles Quick-Fill button click
 */
function handleQuickFill() {
  if (!currentRoleKey || !ROLES[currentRoleKey]) return;
  const r = ROLES[currentRoleKey];

  const uidInput = document.getElementById("stationUserId");
  const pwdInput = document.getElementById("stationPassword");
  if (uidInput) uidInput.value = r.userId;
  if (pwdInput) pwdInput.value = r.password;

  const errBox = document.getElementById("stationErrorBox");
  if (errBox) errBox.style.display = "none";
}

/**
 * Handles Login form submission
 */
async function handleLoginSubmit(e) {
  if (e) e.preventDefault();
  if (!currentRoleKey || !ROLES[currentRoleKey]) return;
  const r = ROLES[currentRoleKey];

  const uidInput = document.getElementById("stationUserId");
  const pwdInput = document.getElementById("stationPassword");
  const errBox = document.getElementById("stationErrorBox");
  const submitBtn = document.getElementById("stationSubmitBtn");

  const userId = uidInput ? uidInput.value.trim() : "";
  const password = pwdInput ? pwdInput.value.trim() : "";

  if (!userId || !password) {
    if (errBox) {
      errBox.style.display = "block";
      errBox.textContent = "Please provide both Staff User ID and Station Password.";
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

    // Save verified session in sessionStorage
    sessionStorage.setItem("hospital_auth", JSON.stringify({
      token: data.token,
      persona: data.persona
    }));

    // Redirect to matching portal for authenticated persona's role
    const matchingRole = Object.values(ROLES).find(x => x.roleName === data.persona.role);
    const destination = matchingRole ? matchingRole.portalUrl : r.portalUrl;
    window.location.href = destination;
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
