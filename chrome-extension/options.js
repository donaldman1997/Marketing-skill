const FIELDS = ["keapAccessToken", "keapBaseUrl", "claudeApiKey"];

// Load saved values
chrome.storage.sync.get(FIELDS, (data) => {
  FIELDS.forEach((key) => {
    const el = document.getElementById(key);
    if (el && data[key]) el.value = data[key];
  });
});

document.getElementById("btn-save").addEventListener("click", () => {
  const values = {};
  FIELDS.forEach((key) => {
    const el = document.getElementById(key);
    if (el) values[key] = el.value.trim();
  });

  chrome.storage.sync.set(values, () => {
    const status = document.getElementById("save-status");
    status.textContent = "Saved!";
    status.className = "";
    setTimeout(() => (status.textContent = ""), 2500);
  });
});
