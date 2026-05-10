// ─── Tab switching ────────────────────────────────────────────────────────────
document.querySelectorAll(".tab-btn").forEach((btn) => {
  btn.addEventListener("click", () => {
    document.querySelectorAll(".tab-btn").forEach((b) => b.classList.remove("active"));
    document.querySelectorAll(".tab-panel").forEach((p) => p.classList.remove("active"));
    btn.classList.add("active");
    document.getElementById(`tab-${btn.dataset.tab}`).classList.add("active");
  });
});

document.getElementById("btn-settings").addEventListener("click", () => {
  chrome.runtime.openOptionsPage();
});

// ─── Helpers ──────────────────────────────────────────────────────────────────
function setStatus(id, msg, isError = false) {
  const el = document.getElementById(id);
  el.textContent = msg;
  el.className = "status-msg" + (isError ? " error" : "");
}

function setLoading(btn, loading) {
  btn.disabled = loading;
  if (loading) {
    btn._origText = btn.innerHTML;
    btn.innerHTML = '<span class="spin">&#9696;</span>';
  } else {
    btn.innerHTML = btn._origText || btn.innerHTML;
  }
}

async function getActiveTab() {
  const [tab] = await chrome.tabs.query({ active: true, currentWindow: true });
  return tab;
}

async function sendToContent(type) {
  const tab = await getActiveTab();
  return chrome.tabs.sendMessage(tab.id, { type });
}

// ─── LEADS TAB ────────────────────────────────────────────────────────────────
let scannedContacts = null;

document.getElementById("btn-scan").addEventListener("click", async () => {
  const btn = document.getElementById("btn-scan");
  setLoading(btn, true);
  setStatus("leads-status", "");
  try {
    const data = await sendToContent("EXTRACT_CONTACTS");
    scannedContacts = data;

    const resultsEl = document.getElementById("leads-results");
    if (!data.emails.length && !data.phones.length && !data.names.length) {
      resultsEl.innerHTML = '<p style="color:#6b7280">No contacts found on this page.</p>';
    } else {
      let html = "";
      data.emails.forEach((email, i) => {
        const name = data.names[i] || "";
        html += `<div class="contact-card">
          <strong>${name || email}</strong>
          <span>${name ? email + " &nbsp;·&nbsp; " : ""}${data.phones[i] || ""}</span>
        </div>`;
      });
      if (!data.emails.length && data.phones.length) {
        data.phones.forEach((p) => {
          html += `<div class="contact-card"><strong>${p}</strong></div>`;
        });
      }
      resultsEl.innerHTML = html;
    }

    resultsEl.classList.remove("hidden");
    document.getElementById("leads-actions").classList.remove("hidden");
    setStatus("leads-status", `Found ${data.emails.length} email(s), ${data.phones.length} phone(s).`);
  } catch (e) {
    setStatus("leads-status", e.message, true);
  } finally {
    setLoading(btn, false);
  }
});

document.getElementById("btn-push-crm").addEventListener("click", async () => {
  if (!scannedContacts?.emails?.length) {
    setStatus("leads-status", "No emails to push.", true);
    return;
  }
  const btn = document.getElementById("btn-push-crm");
  setLoading(btn, true);
  setStatus("leads-status", "");
  let pushed = 0;
  for (let i = 0; i < scannedContacts.emails.length; i++) {
    const email = scannedContacts.emails[i];
    const nameParts = (scannedContacts.names[i] || "").split(" ");
    try {
      await KeapAPI.createContact({
        email_addresses: [{ email, field: "EMAIL1" }],
        given_name: nameParts[0] || "",
        family_name: nameParts.slice(1).join(" ") || "",
      });
      pushed++;
    } catch (e) {
      console.warn("Push failed for", email, e.message);
    }
  }
  setLoading(btn, false);
  setStatus("leads-status", `Pushed ${pushed} contact(s) to CRM.`);
});

document.getElementById("btn-copy-leads").addEventListener("click", () => {
  if (!scannedContacts) return;
  const text = [
    ...scannedContacts.emails,
    ...scannedContacts.phones,
  ].join("\n");
  navigator.clipboard.writeText(text);
  setStatus("leads-status", "Copied to clipboard.");
});

// ─── CRM TAB ──────────────────────────────────────────────────────────────────
document.getElementById("btn-crm-search").addEventListener("click", async () => {
  const email = document.getElementById("crm-search-email").value.trim();
  if (!email) return;
  const btn = document.getElementById("btn-crm-search");
  setLoading(btn, true);
  setStatus("crm-status", "");
  const el = document.getElementById("crm-contact-result");
  try {
    const res = await KeapAPI.searchContacts(email);
    const contacts = res.contacts || [];
    if (!contacts.length) {
      el.innerHTML = '<p style="color:#6b7280">No contacts found.</p>';
    } else {
      el.innerHTML = contacts.map((c) => `
        <div class="contact-card">
          <strong>${c.given_name || ""} ${c.family_name || ""}</strong>
          <span>${c.email_addresses?.[0]?.email || ""} &nbsp;·&nbsp; ID: ${c.id}</span>
        </div>`).join("");
    }
    el.classList.remove("hidden");
  } catch (e) {
    setStatus("crm-status", e.message, true);
  } finally {
    setLoading(btn, false);
  }
});

document.getElementById("btn-crm-add").addEventListener("click", async () => {
  const first = document.getElementById("crm-first").value.trim();
  const last  = document.getElementById("crm-last").value.trim();
  const email = document.getElementById("crm-email").value.trim();
  const phone = document.getElementById("crm-phone").value.trim();

  if (!email) { setStatus("crm-status", "Email is required.", true); return; }

  const btn = document.getElementById("btn-crm-add");
  setLoading(btn, true);
  setStatus("crm-status", "");
  try {
    const payload = {
      given_name: first,
      family_name: last,
      email_addresses: [{ email, field: "EMAIL1" }],
    };
    if (phone) payload.phone_numbers = [{ number: phone, field: "PHONE1" }];
    const result = await KeapAPI.createContact(payload);
    setStatus("crm-status", `Contact created (ID: ${result.id}).`);
    ["crm-first","crm-last","crm-email","crm-phone"].forEach((id) => {
      document.getElementById(id).value = "";
    });
  } catch (e) {
    setStatus("crm-status", e.message, true);
  } finally {
    setLoading(btn, false);
  }
});

// ─── CONTENT TAB ──────────────────────────────────────────────────────────────
const contentTypePrompts = {
  email: (ctx) =>
    `Write a short, personalized cold email for: ${ctx}. Include subject line and body. Keep it under 150 words.`,
  subject: (ctx) =>
    `Write 5 compelling email subject lines for this offer or audience: ${ctx}. Number each one.`,
  ad: (ctx) =>
    `Write Facebook and Google ad copy (headline + primary text) for: ${ctx}. Keep each under 30/90 chars respectively.`,
  cta: (ctx) =>
    `Write 5 strong call-to-action button labels and accompanying microcopy for: ${ctx}.`,
  summary: (ctx) =>
    `Summarize this page content for a marketer. Highlight key value props, target audience, and any contact info.\n\n${ctx}`,
  custom: (ctx) => ctx,
};

document.getElementById("content-type").addEventListener("change", (e) => {
  const isCustom = e.target.value === "custom";
  document.getElementById("custom-prompt").classList.toggle("hidden", !isCustom);
  document.getElementById("custom-prompt-label").style.display = isCustom ? "block" : "none";
});

document.getElementById("btn-use-page").addEventListener("click", async () => {
  const btn = document.getElementById("btn-use-page");
  setLoading(btn, true);
  try {
    const ctx = await sendToContent("GET_PAGE_CONTEXT");
    const current = document.getElementById("content-context").value.trim();
    const pageInfo = `[Page: ${ctx.title}]\n${ctx.description || ctx.bodyText.slice(0, 400)}`;
    document.getElementById("content-context").value = current
      ? current + "\n\n" + pageInfo
      : pageInfo;
  } catch (e) {
    setStatus("content-status", "Could not read page context.", true);
  } finally {
    setLoading(btn, false);
  }
});

document.getElementById("btn-generate").addEventListener("click", async () => {
  const type = document.getElementById("content-type").value;
  const context = document.getElementById("content-context").value.trim();
  const custom  = document.getElementById("custom-prompt").value.trim();

  const input = type === "custom" ? custom : context;
  if (!input) { setStatus("content-status", "Add some context first.", true); return; }

  const btn = document.getElementById("btn-generate");
  setLoading(btn, true);
  setStatus("content-status", "");
  document.getElementById("content-output").classList.add("hidden");
  try {
    const prompt = contentTypePrompts[type](input);
    const output = await GeminiAPI.generate(prompt);
    document.getElementById("content-text").textContent = output;
    document.getElementById("content-output").classList.remove("hidden");
  } catch (e) {
    setStatus("content-status", e.message, true);
  } finally {
    setLoading(btn, false);
  }
});

document.getElementById("btn-copy-content").addEventListener("click", () => {
  const text = document.getElementById("content-text").textContent;
  navigator.clipboard.writeText(text);
  setStatus("content-status", "Copied to clipboard.");
});
