// Hospital RAG RBAC - Shared Portal Engine & Route Guard

const DEFAULT_PERSONAS = {
  "Chief Medical Officer": "CMO_501",
  "Department Head": "DH_401",
  "Treating Doctor": "DR_302",
  "Nurse": "RN_201",
  "Front Desk / Billing Staff": "FD_101",
  "System Administrator": "SYS_999"
};

let currentAuth = {
  token: null,
  persona: null
};

let initialGreetingHtml = "";

/**
 * Initializes the portal page session, enforces route guards, and sets up common UI.
 */
async function initPortal(roleName, minLevel, isClinical = true) {
  // 1. Try to load existing session from sessionStorage
  const stored = sessionStorage.getItem("hospital_auth");
  let needLogin = true;

  if (stored) {
    try {
      const parsed = JSON.parse(stored);
      // Verify role matches this portal's requirements
      if (parsed.persona && parsed.persona.role === roleName && parsed.token) {
        currentAuth = parsed;
        needLogin = false;
      }
    } catch (e) {
      console.warn("Failed to parse stored session:", e);
    }
  }

  // 2. If no valid session for this role, auto-authenticate with the canonical persona
  if (needLogin) {
    const userId = DEFAULT_PERSONAS[roleName];
    if (userId) {
      try {
        const res = await fetch("/api/auth/login", {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({ user_id: userId })
        });
        const data = await res.json();
        currentAuth = {
          token: data.token,
          persona: data.persona
        };
        sessionStorage.setItem("hospital_auth", JSON.stringify(currentAuth));
      } catch (err) {
        console.error("Auto-login failed:", err);
      }
    }
  }

  // 3. Render common header elements
  renderPortalHeader(isClinical);

  // 4. Save initial greeting for chat reset
  const display = document.getElementById("chatDisplay");
  if (display && !initialGreetingHtml) {
    initialGreetingHtml = display.innerHTML;
  }

  // 5. Inject "Clear Chat" button into quick scenarios bar if not present
  injectClearChatButton();

  // 6. Attach chat submit handler if form exists
  const chatForm = document.getElementById("chatForm");
  if (chatForm) {
    chatForm.addEventListener("submit", handlePortalChatSubmit);
  }

  // 7. Attach quick scenario chip click handlers
  document.querySelectorAll(".chip").forEach(btn => {
    btn.addEventListener("click", () => {
      const query = btn.getAttribute("data-query");
      const input = document.getElementById("queryInput");
      if (input && chatForm) {
        input.value = query;
        chatForm.dispatchEvent(new Event("submit"));
      }
    });
  });

  // 8. Setup Token Inspector Modal
  setupTokenModal();

  // 9. Focus query input
  const qInput = document.getElementById("queryInput");
  if (qInput) qInput.focus();
}

/**
 * Dynamically builds the top portal header with role badges & switch controls.
 */
function renderPortalHeader(isClinical) {
  const p = currentAuth.persona || {};
  const headerContainer = document.getElementById("portalHeader");
  if (!headerContainer) return;

  const breakGlassBtn = isClinical && p.role !== "System Administrator" ? `
    <button class="btn btn-emergency" id="breakGlassBtn">
      <svg width="15" height="15" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M10.29 3.86L1.82 18a2 2 0 0 0 1.71 3h16.94a2 2 0 0 0 1.71-3L13.71 3.86a2 2 0 0 0-3.42 0z"/><line x1="12" y1="9" x2="12" y2="13"/><line x1="12" y1="17" x2="12.01" y2="17"/></svg>
      Emergency Break-Glass
    </button>
  ` : '';

  headerContainer.innerHTML = `
    <div class="header-content">
      <div class="brand">
        <a href="/portal/gateway" class="brand-link" title="Return to Hospital Gateway">
          <div class="brand-icon">
            <svg width="22" height="22" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.2">
              <path d="M12 2v20M2 12h20M4.93 4.93l14.14 14.14M19.07 4.93L4.93 19.07"/>
            </svg>
          </div>
        </a>
        <div>
          <h1 id="pageTitleText">${document.title.split('|')[0].trim()}</h1>
          <p class="subtitle" id="staffSubText">${p.name || 'Staff User'} | ${p.department || 'Hospital'} | ${p.assigned_ward || 'General'}</p>
        </div>
      </div>
      <div class="header-badges">
        <span class="badge policy-badge">Role Level ${p.level ?? '-'}</span>
        <span class="badge live-badge">Fail-Closed Active</span>
        <button class="btn btn-outline" id="viewTokenBtn">Inspect JWT</button>
        ${breakGlassBtn}
        <a href="/portal/gateway" class="btn btn-primary switch-btn">Switch Portal</a>
      </div>
    </div>
  `;

  const bgBtn = document.getElementById("breakGlassBtn");
  if (bgBtn) {
    bgBtn.addEventListener("click", handleBreakGlass);
  }
}

/**
 * Injects a small "Clear Chat" button into the quick-scenarios container.
 */
function injectClearChatButton() {
  const container = document.querySelector(".quick-scenarios");
  if (!container || document.getElementById("clearChatBtn")) return;

  const headerRow = document.createElement("div");
  headerRow.style.cssText = "display:flex; justify-content:space-between; align-items:center; margin-bottom:0.4rem;";

  const label = container.querySelector(".scenario-label");
  if (label) {
    container.insertBefore(headerRow, label);
    headerRow.appendChild(label);
    label.style.marginBottom = "0";
  }

  const clearBtn = document.createElement("button");
  clearBtn.id = "clearChatBtn";
  clearBtn.className = "btn btn-outline";
  clearBtn.style.cssText = "padding:0.2rem 0.55rem; font-size:0.75rem; border-radius:4px;";
  clearBtn.innerHTML = `
    <svg width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><polyline points="3 6 5 6 21 6"/><path d="M19 6v14a2 2 0 0 1-2 2H7a2 2 0 0 1-2-2V6m3 0V4a2 2 0 0 1 2-2h4a2 2 0 0 1 2 2v2"/></svg>
    Reset Chat
  `;
  clearBtn.addEventListener("click", resetChatDisplay);
  headerRow.appendChild(clearBtn);
}

function resetChatDisplay() {
  const display = document.getElementById("chatDisplay");
  if (display && initialGreetingHtml) {
    display.innerHTML = initialGreetingHtml;
  }
  const input = document.getElementById("queryInput");
  if (input) {
    input.value = "";
    input.focus();
  }
}

/**
 * Executes a clinical query through the 6-step request enforcement pipeline.
 */
async function handlePortalChatSubmit(e) {
  e.preventDefault();
  const input = document.getElementById("queryInput");
  const query = input.value.trim();
  if (!query) return;

  // Append user question
  appendMessage("User", query, "user-message");
  input.value = "";

  const sendBtn = document.getElementById("sendBtn");
  if (sendBtn) sendBtn.disabled = true;

  // Show typing / thinking indicator
  showTypingIndicator();

  try {
    // Ensure active token exists
    if (!currentAuth.token) {
      const p = currentAuth.persona || {};
      const fallbackId = p.user_id || "DR_302";
      const lRes = await fetch("/api/auth/login", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ user_id: fallbackId })
      });
      const lData = await lRes.json();
      currentAuth = { token: lData.token, persona: lData.persona };
      sessionStorage.setItem("hospital_auth", JSON.stringify(currentAuth));
    }

    const res = await fetch("/api/chat/query", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ query: query, token: currentAuth.token })
    });

    const result = await res.json();
    const isAllowed = result.outcome === "ALLOWED";
    const msgClass = isAllowed ? "assistant-message" : "refusal-message";

    hideTypingIndicator();
    appendMessage("Hospital Assistant", result.answer, msgClass);
    updatePipelineTelemetry(result.telemetry);
  } catch (err) {
    hideTypingIndicator();
    appendMessage("System Error", "Network or server failure: " + err.message, "refusal-message");
  } finally {
    hideTypingIndicator();
    if (sendBtn) sendBtn.disabled = false;
    if (input) input.focus();
  }
}

function showTypingIndicator() {
  const display = document.getElementById("chatDisplay");
  if (!display || document.getElementById("typingIndicator")) return;

  const typingEl = document.createElement("div");
  typingEl.id = "typingIndicator";
  typingEl.className = "chat-message assistant-message typing-bubble";
  typingEl.innerHTML = `
    <div class="typing-dots">
      <span></span><span></span><span></span>
    </div>
    <span class="typing-text">Enforcing pre-retrieval filters & generating response...</span>
  `;
  display.appendChild(typingEl);
  display.scrollTop = display.scrollHeight;
}

function hideTypingIndicator() {
  const el = document.getElementById("typingIndicator");
  if (el) el.remove();
}

/**
 * Rich markdown formatter for bold, code, lists, citations and line breaks.
 */
function formatMarkdown(text) {
  if (!text) return "";

  let out = text;

  // Format headers (e.g. ### Header)
  out = out.replace(/^### (.*$)/gim, '<h4 style="margin:0.4rem 0; font-size:1rem; font-weight:700;">$1</h4>');

  // Format bold (**text**)
  out = out.replace(/\*\*(.*?)\*\*/g, '<strong>$1</strong>');

  // Format inline code (`code`)
  out = out.replace(/`(.*?)`/g, '<code>$1</code>');

  // Format document / patient citation pills
  out = out.replace(/\[(Document [^\]]+)\]/g, '<span class="badge" style="background:var(--blue-light); color:var(--medical-blue-dark); font-size:0.75rem;">$1</span>');
  out = out.replace(/\[(Patient P-\d{4})\]/g, '<span class="badge" style="background:var(--teal-light); color:var(--primary-teal-hover); font-size:0.75rem;">$1</span>');

  // Format bullet points (lines starting with • or * or - )
  const lines = out.split("\n");
  let inList = false;
  let formattedLines = [];

  for (let line of lines) {
    const trimmed = line.trim();
    if (trimmed.startsWith("• ") || trimmed.startsWith("* ") || trimmed.startsWith("- ")) {
      if (!inList) {
        formattedLines.push('<ul style="margin:0.35rem 0 0.35rem 1.25rem; padding:0;">');
        inList = true;
      }
      formattedLines.push(`<li>${trimmed.substring(2)}</li>`);
    } else {
      if (inList) {
        formattedLines.push('</ul>');
        inList = false;
      }
      formattedLines.push(line);
    }
  }
  if (inList) formattedLines.push('</ul>');

  out = formattedLines.join("<br>");
  // Clean redundant <br> tags around lists
  out = out.replace(/<br><ul/g, '<ul').replace(/<\/ul><br>/g, '</ul>');

  return out;
}

function appendMessage(sender, text, cssClass) {
  const display = document.getElementById("chatDisplay");
  if (!display) return;

  const msgEl = document.createElement("div");
  msgEl.className = `chat-message ${cssClass}`;

  const formatted = formatMarkdown(text);

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

/**
 * Updates the 6-step Request Enforcement Telemetry Panel.
 */
function updatePipelineTelemetry(t) {
  if (!t) return;

  const timerEl = document.getElementById("executionTimer");
  if (timerEl) timerEl.textContent = `${t.execution_ms} ms`;

  setStepStatus("step1", t.step1_auth.success, JSON.stringify(t.step1_auth, null, 2));
  setStepStatus("step2", t.step2_filters.success, JSON.stringify(t.step2_filters, null, 2));

  const step3Ok = (t.step3_retrieval.documents_found || 0) > 0 || t.status === "ALLOWED";
  setStepStatus("step3", step3Ok, JSON.stringify(t.step3_retrieval, null, 2));
  setStepStatus("step4", true, JSON.stringify(t.step4_prompt, null, 2));

  const step5Ok = t.status === "ALLOWED";
  setStepStatus("step5", step5Ok, JSON.stringify(t.step5_guard, null, 2));
  setStepStatus("step6", true, JSON.stringify(t.step6_audit, null, 2));
}

function setStepStatus(stepPrefix, isSuccess, contentText) {
  const card = document.getElementById(`${stepPrefix}Card`);
  const statusBadge = document.getElementById(`${stepPrefix}Status`);
  const content = document.getElementById(`${stepPrefix}Content`);
  if (!card || !statusBadge || !content) return;

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

/**
 * Emergency Break-Glass workflow.
 */
async function handleBreakGlass() {
  const reason = prompt(
    "EMERGENCY BREAK-GLASS PROTOCOL\nPlease enter clinical justification for emergency hospital-wide override:",
    "Acute medical crisis; patient in severe cardiac arrest, immediate full history required."
  );
  if (!reason) return;

  try {
    const res = await fetch("/api/auth/break-glass", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ user_id: currentAuth.persona.user_id, justification: reason })
    });
    const data = await res.json();
    if (res.ok) {
      currentAuth.token = data.token;
      sessionStorage.setItem("hospital_auth", JSON.stringify(currentAuth));
      const sub = document.getElementById("staffSubText");
      if (sub) {
        sub.innerHTML = `🚨 <strong style="color:var(--amber-warning);">[BREAK-GLASS EMERGENCY ACTIVE]</strong> ${currentAuth.persona.name} | Justification: "${reason}"`;
      }
      alert("EMERGENCY ELEVATED TOKEN ISSUED (15 Mins).\nAll patient clinical records accessible. Logged with HIGH SEVERITY in tamper-evident audit chain.");
    } else {
      alert("Failed to issue break-glass token: " + data.detail);
    }
  } catch (err) {
    alert("Error: " + err.message);
  }
}

/**
 * Token Inspector Modal setup.
 */
function setupTokenModal() {
  const openBtn = document.getElementById("viewTokenBtn");
  const modal = document.getElementById("tokenModal");
  if (!openBtn || !modal) return;

  const closeBtn = document.getElementById("closeModalBtn");

  openBtn.addEventListener("click", () => {
    const rawEl = document.getElementById("rawTokenArea");
    const decEl = document.getElementById("decodedClaimsArea");
    if (rawEl) rawEl.value = currentAuth.token || "No token active";
    if (decEl) {
      try {
        if (currentAuth.token) {
          const payload = JSON.parse(atob(currentAuth.token.split(".")[1]));
          decEl.textContent = JSON.stringify(payload, null, 2);
        }
      } catch (e) {
        decEl.textContent = "Could not decode client-side.";
      }
    }
    modal.classList.remove("hidden");
  });

  if (closeBtn) {
    closeBtn.addEventListener("click", () => modal.classList.add("hidden"));
  }
  modal.addEventListener("click", (e) => {
    if (e.target === modal) modal.classList.add("hidden");
  });
}
