// Injected into every page — extracts contact data and page context on request.

const EMAIL_RE = /[a-zA-Z0-9._%+\-]+@[a-zA-Z0-9.\-]+\.[a-zA-Z]{2,}/g;
const PHONE_RE = /(?:\+?1[-.\s]?)?\(?\d{3}\)?[-.\s]\d{3}[-.\s]\d{4}/g;

function extractContacts() {
  const text = document.body.innerText || "";
  const emails = [...new Set(text.match(EMAIL_RE) || [])];
  const phones = [...new Set(text.match(PHONE_RE) || [])];

  // Pull structured names from common markup patterns
  const nameSelectors = [
    'h1[class*="name"]', '[class*="contact-name"]', '[class*="person-name"]',
    '[itemprop="name"]', ".vcard .fn", "[data-name]",
  ];
  const names = [];
  nameSelectors.forEach((sel) => {
    document.querySelectorAll(sel).forEach((el) => {
      const n = el.textContent.trim();
      if (n && !names.includes(n)) names.push(n);
    });
  });

  return {
    emails,
    phones,
    names,
    url: location.href,
    title: document.title,
    timestamp: new Date().toISOString(),
  };
}

function getPageContext() {
  const metas = {};
  document.querySelectorAll("meta[name], meta[property]").forEach((m) => {
    const key = m.getAttribute("name") || m.getAttribute("property");
    metas[key] = m.getAttribute("content");
  });
  return {
    title: document.title,
    url: location.href,
    description: metas["description"] || metas["og:description"] || "",
    bodyText: (document.body.innerText || "").slice(0, 3000),
  };
}

chrome.runtime.onMessage.addListener((msg, _sender, sendResponse) => {
  if (msg.type === "EXTRACT_CONTACTS") {
    sendResponse(extractContacts());
  } else if (msg.type === "GET_PAGE_CONTEXT") {
    sendResponse(getPageContext());
  }
  return true;
});
