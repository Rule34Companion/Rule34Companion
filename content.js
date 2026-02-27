const normalize = t =>
  t
    .toLowerCase()
    .trim()
    .replace(/^-+/, "");

async function getFilters() {
  const data = await browser.storage.local.get(["whitelist", "blacklist"]);
  return {
    whitelist: (data.whitelist || []).map(normalize),
    blacklist: (data.blacklist || []).map(normalize)
  };
}

function extractTags(img) {
  if (!img || !img.alt) return [];

  return img.alt
    .split(" ")
    .map(normalize)
    .filter(t =>
      t &&
      !t.startsWith("score:") &&
      !t.startsWith("user:")
    );
}

async function evaluatePost(post) {
  const img = post.querySelector("img");
  if (!img) return;

  const tags = extractTags(img);
  const { whitelist, blacklist } = await getFilters();

  // BLACKLIST IS ABSOLUTE
  if (blacklist.some(t => tags.includes(t))) {
    post.style.display = "none";
    return;
  }

  // WHITELIST (if defined)
  if (whitelist.length && !whitelist.every(t => tags.includes(t))) {
    post.style.display = "none";
    return;
  }

  post.style.display = "";
}

async function filterPosts() {
  document.querySelectorAll(".thumb").forEach(post => {
    evaluatePost(post);

    const img = post.querySelector("img");
    if (!img) return;

    // Re-evaluate when image finishes loading
    if (!img.dataset.filtered) {
      img.dataset.filtered = "true";
      img.addEventListener("load", () => evaluatePost(post));
    }
  });
}

// Observe DOM changes
let pending = false;
const observer = new MutationObserver(() => {
  if (pending) return;
  pending = true;
  requestAnimationFrame(() => {
    filterPosts();
    pending = false;
  });
});

observer.observe(document.body, { childList: true, subtree: true });
filterPosts();
