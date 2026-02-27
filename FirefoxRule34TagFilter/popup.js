const whitelistEl = document.getElementById("whitelist");
const blacklistEl = document.getElementById("blacklist");

function normalizeInput(text) {
  // Ensure trailing newline
  return text.endsWith("\n") ? text : text + "\n";
}

function save() {
  browser.storage.local.set({
    whitelist: whitelistEl.value.split(/\s+/).filter(Boolean),
    blacklist: blacklistEl.value.split(/\s+/).filter(Boolean)
  });
}

browser.storage.local.get(["whitelist", "blacklist"]).then(data => {
  whitelistEl.value = normalizeInput((data.whitelist || []).join("\n"));
  blacklistEl.value = normalizeInput((data.blacklist || []).join("\n"));

  // Scroll to bottom
  whitelistEl.scrollTop = whitelistEl.scrollHeight;
  blacklistEl.scrollTop = blacklistEl.scrollHeight;

  // Place cursor at end
  whitelistEl.selectionStart = whitelistEl.selectionEnd = whitelistEl.value.length;
  blacklistEl.selectionStart = blacklistEl.selectionEnd = blacklistEl.value.length;
});

// Autosave on every change
whitelistEl.addEventListener("input", save);
blacklistEl.addEventListener("input", save);
