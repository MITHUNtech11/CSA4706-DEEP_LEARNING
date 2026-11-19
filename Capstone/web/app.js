// Hospital RAG RBAC - Interactive Web Client Controller
let activeToken = null;
let activePersona = null;
let allPersonas = [];

document.addEventListener("DOMContentLoaded", async () => {
  initTabs();
  initModal();
  await loadPersonas();
  await refreshAuditLogs();

  // Attach Chat Form Handler
  document.getElementById("chatForm").addEventListener("submit", handleChatSubmit);

  // Quick Scenarios Buttons
  document.querySelectorAll(".chip").forEach(btn => {
    btn.addEventListener("click", () => {
      const query = btn.getAttribute("data-query");
      document.getElementById("queryInput").value = query;
      document.getElementById("chatForm").dispatchEvent(new Event("submit"));
    });
  });

  // Audit Actions
  document.getElementById("refreshAuditBtn").addEventListener("click", refreshAuditLogs);
  document.getElementById("verifyAuditBtn").addEventListener("click", verifyAuditChain);
  document.getElementById("simulateTamperBtn").addEventListener("click", simulateTamperAttack);

  // Emergency Break-Glass Handler
  document.getElementById("breakGlassBtn").addEventListener("click", handleBreakGlass);

  // Policy Approver Sign-off
  document.getElementById("signPolicyBtn").addEventListener("click", handlePolicyApproval);
});

// --- Tab Controller ---
function initTabs() {
  const tabs = document.querySelectorAll(".tab-btn");
  tabs.forEach(tab => {
    tab.addEventListener("click", () => {
      tabs.forEach(t => t.classList.remove("active"));
      document.querySelectorAll(".tab-pane").forEach(p => p.classList.remove("active"));

      tab.classList.add("active");
      const targetId = tab.getAttribute("data-tab");
      document.getElementById(targetId).classList.add("active");
    });
  });
}

// --- Personas & Auth ---
async function loadPersonas() {
  try {
    const res = await fetch("/api/personas");
    const data = await res.json();
    allPersonas = data.personas || [];

    const grid = document.getElementById("personaGrid");
    grid.innerHTML = "";

    allPersonas.forEach(p => {
      const card = document.createElement("div");
      card.className = "persona-card";
      card.id = `persona-${p.user_id}`;
      card.innerHTML = `
        <div class="persona-header">
          <span class="persona-name">${p.name}</span>
          <span class="persona-level">Lvl ${p.level}</span>
        </div>
        <div class="persona-role">${p.role}</div>
        <div class="persona-dept">${p.department}</div>
      `;
      card.addEventListener("click", () => selectPersona(p.user_id));
      grid.appendChild(card);
    });

    // Auto-select first persona (CMO)
    if (allPersonas.length > 0) {
      await selectPersona(allPersonas[0].user_id);
    }
  } catch (err) {
    console.error("Failed to load personas:", err);
  }
}

async function selectPersona(userId) {
  try {
    const res = await fetch("/api/auth/login", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ user_id: userId })
    });
    const authData = await res.json();

    activeToken = authData.token;
    activePersona = authData.persona;

    // Update active UI cards
    document.querySelectorAll(".persona-card").forEach(c => c.classList.remove("active"));
    const selectedEl = document.getElementById(`persona-${userId}`);
    if (selectedEl) selectedEl.classList.add("active");

    document.getElementById("activeRoleName").textContent = `${activePersona.role} (Level ${activePersona.level})`;
    document.getElementById("activeIdentityMeta").textContent = `${activePersona.name} | Dept: ${activePersona.department} | Ward: ${activePersona.assigned_ward}`;
  } catch (err) {
    console.error("Login failed:", err);
  }
}

async function handleBreakGlass() {
  const reason = prompt("EMERGENCY BREAK-GLASS PROTOCOL\nPlease enter clinical justification for emergency hospital-wide override:", "Patient in severe anaphylactic shock and cardiac arrest; immediate full history required.");
  if (!reason) return;

  try {
    const res = await fetch("/api/auth/break-glass", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ user_id: activePersona.user_id, justification: reason })
    });
    const data = await res.json();
    if (res.ok) {
      activeToken = data.token;
      document.getElementById("activeRoleName").textContent = `🚨 ${activePersona.role} [BREAK-GLASS EMERGENCY]`;
      document.getElementById("activeIdentityMeta").textContent = `Justification: "${reason}" | Valid for 15 mins`;
      alert("EMERGENCY ELEVATED TOKEN ISSUED.\nAll hospital patient records temporarily accessible. This event is logged with HIGH SEVERITY in the tamper-evident audit chain.");
    } else {
      alert("Failed to issue break-glass token: " + data.detail);
    }
  } catch (err) {
    alert("Error: " + err.message);
  }
}

// --- Chat Execution & Telemetry ---
async function handleChatSubmit(e) {
  e.preventDefault();
  const input = document.getElementById("queryInput");
  const query = input.value.trim();
  if (!query) return;

  // Add User Message to Chat Display
  appendChatMessage("User", query, "user-message");
  input.value = "";

  const sendBtn = document.getElementById("sendBtn");
  sendBtn.disabled = true;

  try {
    const res = await fetch("/api/chat/query", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ query: query, token: activeToken })
    });

    const result = await res.json();
    const isAllowed = result.outcome === "ALLOWED";

    // Add Assistant Message
    const msgClass = isAllowed ? "assistant-message" : "refusal-message";
    appendChatMessage("Hospital Assistant", result.answer, msgClass);

    // Update 6-Step Telemetry Panel
    updateTelemetry(result.telemetry);

    // Auto-refresh audit log table to show new entry
    await refreshAuditLogs();
  } catch (err) {
    appendChatMessage("System Error", "Network or server failure: " + err.message, "refusal-message");
  } finally {
    sendBtn.disabled = false;
  }
}

function appendChatMessage(sender, text, cssClass) {
  const display = document.getElementById("chatDisplay");
  const msgEl = document.createElement("div");
  msgEl.className = `chat-message ${cssClass}`;
  
  // Format markdown bold & code
  let formatted = text
    .replace(/\*\*(.*?)\*\*/g, '<strong>$1</strong>')
    .replace(/`(.*?)`/g, '<code>$1</code>')
    .replace(/\n/g, '<br>');

  msgEl.innerHTML = `
    <div class="message-header">
      <span class="sender-tag">${sender}</span>
      <span class="time-tag">${new Date().toLocaleTimeString()}</span>
    </div>
    <div class="message-body">${formatted}</div>
  `;
  display.appendChild(msgEl);
  display.scrollTop = display.scrollHeight;
}

function updateTelemetry(t) {
  if (!t) return;

  document.getElementById("executionTimer").textContent = `${t.execution_ms} ms`;

  // Step 1: Authenticate
  setStepStatus("step1", t.step1_auth.success, JSON.stringify(t.step1_auth, null, 2));

  // Step 2: Build Filters
  setStepStatus("step2", t.step2_filters.success, JSON.stringify(t.step2_filters, null, 2));

  // Step 3: Retrieve
  const step3Ok = (t.step3_retrieval.documents_found || 0) > 0 || t.status === "ALLOWED";
  setStepStatus("step3", step3Ok, JSON.stringify(t.step3_retrieval, null, 2));

  // Step 4: Render Prompt
  setStepStatus("step4", true, JSON.stringify(t.step4_prompt, null, 2));

  // Step 5: Check Output
  const step5Ok = t.status === "ALLOWED";
  setStepStatus("step5", step5Ok, JSON.stringify(t.step5_guard, null, 2));

  // Step 6: Hash Chained Audit Log
  setStepStatus("step6", true, JSON.stringify(t.step6_audit, null, 2));
}

function setStepStatus(stepPrefix, isSuccess, contentText) {
  const card = document.getElementById(`${stepPrefix}Card`);
  const statusBadge = document.getElementById(`${stepPrefix}Status`);
  const content = document.getElementById(`${stepPrefix}Content`);

  card.classList.remove("step-success", "step-blocked");
  statusBadge.classList.remove("status-pending", "status-success", "status-blocked");

  if (isSuccess) {
    card.classList.add("step-success");
    statusBadge.classList.add("status-success");
    statusBadge.textContent = "Passed";
  } else {
    card.classList.add("step-blocked");
    statusBadge.classList.add("status-blocked");
    statusBadge.textContent = "Refused / Filtered";
  }

  content.textContent = contentText;
}

// --- Audit Log & Tamper Verification (Algorithm 2) ---
async function refreshAuditLogs() {
  try {
    const res = await fetch("/api/audit/logs");
    const data = await res.json();
    const entries = data.entries || [];

    document.getElementById("totalAuditCount").textContent = entries.length;

    const tbody = document.getElementById("auditTableBody");
    tbody.innerHTML = "";

    entries.slice().reverse().forEach(item => {
      const rec = item.entry || {};
      const row = document.createElement("tr");

      const isAllowed = rec.outcome === "ALLOWED";
      const outcomeBadge = isAllowed 
        ? `<span class="badge badge-yes">ALLOWED</span>` 
        : `<span class="badge badge-no">BLOCKED</span>`;

      row.innerHTML = `
        <td>#${rec.entry_index || "-"}</td>
        <td>${rec.timestamp ? new Date(rec.timestamp).toLocaleTimeString() : "-"}</td>
        <td><strong>${rec.user_id || "-"}</strong></td>
        <td>${rec.role || "-"}</td>
        <td>${outcomeBadge}</td>
        <td><code>${rec.filters_applied ? rec.filters_applied.scope_desc || "Standard" : "-"}</code></td>
        <td><code title="${item.current_hash}">${item.current_hash ? item.current_hash.slice(0, 10) + '...' : '-'}</code></td>
        <td><code title="${item.prev_hash}">${item.prev_hash ? item.prev_hash.slice(0, 10) + '...' : '-'}</code></td>
      `;
      tbody.appendChild(row);
    });
  } catch (err) {
    console.error("Failed to load audit logs:", err);
  }
}

async function verifyAuditChain() {
  try {
    const res = await fetch("/api/audit/verify", { method: "POST" });
    const data = await res.json();

    const banner = document.getElementById("tamperAlertBanner");
    const integrityStatus = document.getElementById("chainIntegrityStatus");

    if (data.is_valid) {
      banner.classList.add("hidden");
      integrityStatus.textContent = "Verified (100% Chain Integrity)";
      integrityStatus.className = "text-success";
      alert("CRYPTOGRAPHIC HASH-CHAIN VERIFIED:\n" + data.message);
    } else {
      banner.classList.remove("hidden");
      banner.innerHTML = `
        <strong>🚨 TAMPER ALERT DETECTED BY ALGORITHM 2:</strong><br>
        ${data.message.replace(/\n/g, '<br>')}
      `;
      integrityStatus.textContent = "TAMPER DETECTED!";
      integrityStatus.className = "text-danger";
    }
  } catch (err) {
    alert("Verification error: " + err.message);
  }
}

async function simulateTamperAttack() {
  if (!confirm("This will simulate an attacker modifying a row in the audit database file without recalculating hashes.\nProceed?")) {
    return;
  }

  try {
    const res = await fetch("/api/audit/simulate-tamper", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ entry_index: 1 })
    });
    const data = await res.json();
    alert("ATTACK SIMULATED:\n" + data.message + "\nNow click 'Verify Hash Chain' to see the cryptographic verifier catch it!");
    await refreshAuditLogs();
  } catch (err) {
    alert("Error: " + err.message);
  }
}

// --- Policy Approval ---
async function handlePolicyApproval() {
  try {
    const res = await fetch("/api/policy/approve-draft", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ approver_id: "compliance_director_02" })
    });
    const data = await res.json();
    if (res.ok) {
      document.getElementById("approver2Status").textContent = "✓ Approver 2: Signed by compliance_director_02";
      document.getElementById("approver2Status").className = "sig-badge signed";
      document.getElementById("policyVersionBadge").textContent = `Policy: ${data.new_version} ACTIVE`;
      document.getElementById("policyVersionText").textContent = data.new_version;
      alert(`Policy ${data.new_version} successfully ratified by dual approvers and activated hospital-wide!`);
    } else {
      alert("Approval error: " + data.detail);
    }
  } catch (err) {
    alert("Error: " + err.message);
  }
}

// --- Modal Controller ---
function initModal() {
  const modal = document.getElementById("tokenModal");
  const openBtn = document.getElementById("viewTokenBtn");
  const closeBtn = document.getElementById("closeModalBtn");

  openBtn.addEventListener("click", () => {
    document.getElementById("rawTokenArea").value = activeToken || "No token active";
    try {
      if (activeToken) {
        const payload = JSON.parse(atob(activeToken.split(".")[1]));
        document.getElementById("decodedClaimsArea").textContent = JSON.stringify(payload, null, 2);
      }
    } catch (e) {
      document.getElementById("decodedClaimsArea").textContent = "Could not decode client-side.";
    }
    modal.classList.remove("hidden");
  });

  closeBtn.addEventListener("click", () => modal.classList.add("hidden"));
  modal.addEventListener("click", (e) => {
    if (e.target === modal) modal.classList.add("hidden");
  });
}
