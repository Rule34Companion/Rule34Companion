// content.js — Tag filtering + image-ID blacklist overlays for rule34.xxx
// Works on both the list/thumbnail pages and individual post/view pages.

// ── Utilities ─────────────────────────────────────────────────────────────────

const normalize = t =>
    t.toLowerCase().trim().replace(/^-+/, "");

async function getTagFilters() {
    const data = await browser.storage.local.get(["positive_tags", "negative_tags"]);
    return {
        positive_tags: (data.positive_tags || []).map(normalize),
        negative_tags: (data.negative_tags || []).map(normalize)
    };
}

function extractTags(img) {
    if (!img || !img.alt) return [];
    return img.alt
        .split(" ")
        .map(normalize)
        .filter(t => t && !t.startsWith("score:") && !t.startsWith("user:"));
}

// ── Image-ID blacklist (cached in memory, authoritative copy is on disk) ──────

let idBlacklist = new Set();
let showBlacklisted = false; // toggled by popup

// Ask background to load the full list from disk
async function loadBlacklist() {
    try {
        const resp = await browser.runtime.sendMessage({ type: "bl_load" });
        if (resp.ok) {
            idBlacklist = new Set(resp.ids.map(String));
        } else {
            console.warn("[R34Filter] bl_load failed:", resp.error);
        }
    } catch (e) {
        console.warn("[R34Filter] bl_load error:", e);
    }
}

async function addToBlacklist(id) {
    try {
        const resp = await browser.runtime.sendMessage({ type: "bl_add", id: String(id) });
        if (resp.ok) {
            idBlacklist = new Set(resp.ids.map(String));
        }
    } catch (e) {
        console.warn("[R34Filter] bl_add error:", e);
    }
}

async function removeFromBlacklist(id) {
    try {
        const resp = await browser.runtime.sendMessage({ type: "bl_remove", id: String(id) });
        if (resp.ok) {
            idBlacklist = new Set(resp.ids.map(String));
        }
    } catch (e) {
        console.warn("[R34Filter] bl_remove error:", e);
    }
}

// ── Extract image ID from various contexts ────────────────────────────────────

// Thumbnail list page: the .thumb <span> has id="p12345", or its <a> href contains id=12345
function getPostId(post) {
    // Try span id ("p12345")
    if (post.id && post.id.startsWith("p")) {
        const n = post.id.slice(1);
        if (/^\d+$/.test(n)) return n;
    }
    // Try anchor href (?page=post&s=view&id=12345)
    const a = post.querySelector("a[href*='id=']");
    if (a) {
        const m = a.href.match(/[?&]id=(\d+)/);
        if (m) return m[1];
    }
    return null;
}

// Full view page: extract from URL or from the image src
function getViewPageId() {
    const m = location.search.match(/[?&]id=(\d+)/);
    return m ? m[1] : null;
}

// ── Combined post evaluation (tag filters + ID blacklist) ────────────────────
// Single function so the two systems can never overwrite each other's decision.

async function evaluatePost(post) {
    const id = getPostId(post);

    // ID blacklist check — evaluated first, takes absolute priority
    if (id && idBlacklist.has(id)) {
        post.style.display = showBlacklisted ? "" : "none";
        return;
    }

    // Tag-based filtering
    const img = post.querySelector("img");
    if (!img) return;

    const tags = extractTags(img);
    const { positive_tags, negative_tags } = await getTagFilters();

    if (negative_tags.some(t => tags.includes(t))) {
        post.style.display = "none";
        return;
    }
    if (positive_tags.length && !positive_tags.every(t => tags.includes(t))) {
        post.style.display = "none";
        return;
    }

    post.style.display = "";
}

// ── ID-based fast re-apply ────────────────────────────────────────────────────
// Used when only the toggle or blacklist changes. Only touches blacklisted posts
// so it cannot accidentally un-hide a tag-filtered post.

function applyIdFilter(post) {
    const id = getPostId(post);
    if (!id || !idBlacklist.has(id)) return;
    post.style.display = showBlacklisted ? "" : "none";
}

// ── Overlay button on thumbnails ──────────────────────────────────────────────

function addThumbOverlay(post) {
    if (post.dataset.r34overlay) return; // already added
    post.dataset.r34overlay = "true";

    const id = getPostId(post);
    if (!id) return;

    // Ensure the wrapper is positioned so the button can be absolute inside it
    const style = window.getComputedStyle(post);
    if (style.position === "static") post.style.position = "relative";

    const btn = document.createElement("button");
    btn.className = "r34-bl-btn";
    btn.dataset.postId = id;
    updateThumbBtnLabel(btn, id);

    btn.addEventListener("click", async e => {
        e.preventDefault();
        e.stopPropagation();
        const pid = btn.dataset.postId;
        if (idBlacklist.has(pid)) {
            await removeFromBlacklist(pid);
            updateThumbBtnLabel(btn, pid);
            applyIdFilter(post);
        } else {
            await addToBlacklist(pid);
            updateThumbBtnLabel(btn, pid);
            applyIdFilter(post);
        }
        // Re-apply visibility to whole page
        applyAllIdFilters();
    });

    post.appendChild(btn);
}

function updateThumbBtnLabel(btn, id) {
    if (idBlacklist.has(id)) {
        btn.textContent = "Unblacklist";
        btn.classList.add("r34-bl-btn--active");
    } else {
        btn.textContent = "Blacklist";
        btn.classList.remove("r34-bl-btn--active");
    }
}

// ── Overlay button on the full view page ─────────────────────────────────────

function setupViewPageOverlay() {
    const id = getViewPageId();
    if (!id) return;

    // The main displayed image is typically #image or the first <img> in #post-view / section#content
    const img =
        document.getElementById("image") ||
        document.querySelector("section#content img") ||
        document.querySelector("#post-view img") ||
        document.querySelector("img[id]");

    if (!img) return;
    if (document.getElementById("r34-view-bl-btn")) return; // already added

    // Wrap the image in a positioned container if needed
    let container = img.parentElement;
    if (window.getComputedStyle(container).position === "static") {
        container.style.position = "relative";
        container.style.display = "inline-block";
    }

    const btn = document.createElement("button");
    btn.id = "r34-view-bl-btn";
    btn.className = "r34-bl-btn r34-bl-btn--view";
    btn.dataset.postId = id;
    updateViewBtnLabel(btn, id);

    btn.addEventListener("click", async e => {
        e.preventDefault();
        if (idBlacklist.has(id)) {
            await removeFromBlacklist(id);
        } else {
            await addToBlacklist(id);
        }
        updateViewBtnLabel(btn, id);
    });

    container.appendChild(btn);
}

function updateViewBtnLabel(btn, id) {
    if (idBlacklist.has(id)) {
        btn.textContent = "Unblacklist";
        btn.classList.add("r34-bl-btn--active");
    } else {
        btn.textContent = "Blacklist";
        btn.classList.remove("r34-bl-btn--active");
    }
}

// ── Apply everything to thumbnails ───────────────────────────────────────────

async function filterPosts() {
    document.querySelectorAll(".thumb").forEach(post => {
        evaluatePost(post);
        applyIdFilter(post);
        addThumbOverlay(post);

        const img = post.querySelector("img");
        if (!img) return;
        if (!img.dataset.filtered) {
            img.dataset.filtered = "true";
            img.addEventListener("load", () => evaluatePost(post));
        }
    });
}

function applyAllIdFilters() {
    document.querySelectorAll(".thumb").forEach(post => {
        applyIdFilter(post);
        const btn = post.querySelector(".r34-bl-btn");
        if (btn) updateThumbBtnLabel(btn, btn.dataset.postId);
    });
}

// ── Listen for messages from popup (toggle show/hide) ────────────────────────

browser.runtime.onMessage.addListener((msg, _sender) => {
    if (msg.type === "set_show_blacklisted") {
        showBlacklisted = msg.value;
        applyAllIdFilters();
    }
    if (msg.type === "bl_updated") {
        // Popup or another tab mutated the list — reload
        loadBlacklist().then(() => {
            applyAllIdFilters();
            // Refresh view-page button if present
            const vBtn = document.getElementById("r34-view-bl-btn");
            if (vBtn) updateViewBtnLabel(vBtn, vBtn.dataset.postId);
        });
    }
});

// ── Observe DOM changes (infinite scroll / dynamic content) ──────────────────

let pending = false;
const observer = new MutationObserver(() => {
    if (pending) return;
    pending = true;
    requestAnimationFrame(() => {
        filterPosts();
        pending = false;
    });
});

// ── Init ──────────────────────────────────────────────────────────────────────

(async () => {
    // Restore the toggle state from storage
    const data = await browser.storage.local.get(["show_blacklisted"]);
    showBlacklisted = !!data.show_blacklisted;

    await loadBlacklist();

    // Detect which page type we're on
    const isViewPage =
        location.search.includes("s=view") || location.search.includes("page=post");

    if (isViewPage && location.search.includes("s=view")) {
        setupViewPageOverlay();
    }

    filterPosts();

    observer.observe(document.body, { childList: true, subtree: true });
})();
