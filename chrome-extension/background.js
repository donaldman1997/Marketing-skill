// Service worker — handles cross-tab messaging and badge updates.

chrome.runtime.onInstalled.addListener(() => {
  chrome.action.setBadgeBackgroundColor({ color: "#4F46E5" });
});

// Relay messages from popup to active tab content script
chrome.runtime.onMessage.addListener((msg, sender, sendResponse) => {
  if (msg.target === "content") {
    chrome.tabs.query({ active: true, currentWindow: true }, ([tab]) => {
      if (!tab) return sendResponse({ error: "No active tab" });
      chrome.tabs.sendMessage(tab.id, msg, sendResponse);
    });
    return true; // keep channel open for async response
  }
});
