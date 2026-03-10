// background.js — Native Messaging bridge between content scripts and the Python helper

const HOST = "rule34_blacklist_host";

function nativeRequest(msg) {
  return new Promise((resolve, reject) => {
    const port = browser.runtime.connectNative(HOST);
    port.onMessage.addListener(response => {
      port.disconnect();
      resolve(response);
    });
    port.onDisconnect.addListener(() => {
      const err = browser.runtime.lastError;
      reject(err ? err.message : "Native host disconnected");
    });
    port.postMessage(msg);
  });
}

browser.runtime.onMessage.addListener((msg, _sender) => {
  switch (msg.type) {

    case "bl_load":
      return nativeRequest({ action: "load" })
        .then(r => ({ ok: true, ids: r.ids || [], path: r.path || "" }))
        .catch(e => ({ ok: false, error: String(e) }));

    case "bl_add":
      return nativeRequest({ action: "add", id: msg.id })
        .then(r => ({ ok: true, ids: r.ids || [], path: r.path || "" }))
        .catch(e => ({ ok: false, error: String(e) }));

    case "bl_remove":
      return nativeRequest({ action: "remove", id: msg.id })
        .then(r => ({ ok: true, ids: r.ids || [], path: r.path || "" }))
        .catch(e => ({ ok: false, error: String(e) }));

    case "bl_get_path":
      return nativeRequest({ action: "get_path" })
        .then(r => ({ ok: true, path: r.path || "" }))
        .catch(e => ({ ok: false, error: String(e) }));

    case "bl_set_path":
      return nativeRequest({ action: "set_path", path: msg.path })
        .then(r => ({ ok: !r.error, path: r.path || "", ids: r.ids || [], error: r.error }))
        .catch(e => ({ ok: false, error: String(e) }));

    default:
      return Promise.resolve({ ok: false, error: "unknown message type" });
  }
});
