// Keap/Infusionsoft REST API client
const KeapAPI = {
  async getCredentials() {
    return new Promise((resolve) => {
      chrome.storage.sync.get(["keapAccessToken", "keapBaseUrl"], resolve);
    });
  },

  async request(method, path, body = null) {
    const { keapAccessToken, keapBaseUrl } = await this.getCredentials();
    if (!keapAccessToken) throw new Error("Keap API token not configured. Open Settings.");

    const base = keapBaseUrl || "https://api.infusionsoft.com/crm/rest/v1";
    const res = await fetch(`${base}${path}`, {
      method,
      headers: {
        Authorization: `Bearer ${keapAccessToken}`,
        "Content-Type": "application/json",
        "X-Keap-API-Key": keapAccessToken,
      },
      body: body ? JSON.stringify(body) : null,
    });

    if (!res.ok) {
      const err = await res.text();
      throw new Error(`Keap API ${res.status}: ${err}`);
    }
    return res.json();
  },

  async searchContacts(email) {
    return this.request("GET", `/contacts?email=${encodeURIComponent(email)}&limit=5`);
  },

  async createContact(contact) {
    return this.request("POST", "/contacts", contact);
  },

  async addTag(contactId, tagId) {
    return this.request("POST", `/contacts/${contactId}/tags`, { tagIds: [tagId] });
  },

  async addNote(contactId, note) {
    return this.request("POST", `/contacts/${contactId}/notes`, {
      title: note.title,
      body: note.body,
      type: "Other",
    });
  },

  async listTags(limit = 50) {
    return this.request("GET", `/tags?limit=${limit}`);
  },
};

// Claude API client for content generation
const ClaudeAPI = {
  async getKey() {
    return new Promise((resolve) => {
      chrome.storage.sync.get(["claudeApiKey"], (r) => resolve(r.claudeApiKey));
    });
  },

  async generate(prompt, systemPrompt = "") {
    const apiKey = await this.getKey();
    if (!apiKey) throw new Error("Claude API key not configured. Open Settings.");

    const res = await fetch("https://api.anthropic.com/v1/messages", {
      method: "POST",
      headers: {
        "x-api-key": apiKey,
        "anthropic-version": "2023-06-01",
        "content-type": "application/json",
      },
      body: JSON.stringify({
        model: "claude-sonnet-4-6",
        max_tokens: 1024,
        system: systemPrompt || "You are an expert marketing copywriter. Be concise and persuasive.",
        messages: [{ role: "user", content: prompt }],
      }),
    });

    if (!res.ok) {
      const err = await res.text();
      throw new Error(`Claude API ${res.status}: ${err}`);
    }
    const data = await res.json();
    return data.content[0].text;
  },
};

// Contact extraction utilities
const ContactExtractor = {
  EMAIL_RE: /[a-zA-Z0-9._%+\-]+@[a-zA-Z0-9.\-]+\.[a-zA-Z]{2,}/g,
  PHONE_RE: /(?:\+?1[-.\s]?)?\(?\d{3}\)?[-.\s]\d{3}[-.\s]\d{4}/g,
  NAME_RE: /(?:(?:Mr|Mrs|Ms|Dr|Prof)\.?\s+)?([A-Z][a-z]+(?:\s[A-Z][a-z]+){1,3})/g,

  fromText(text) {
    const emails = [...new Set(text.match(this.EMAIL_RE) || [])];
    const phones = [...new Set(text.match(this.PHONE_RE) || [])];
    const names = [...new Set((text.match(this.NAME_RE) || []).map((n) => n.trim()))];
    return { emails, phones, names };
  },
};
