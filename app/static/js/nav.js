// ============================================================
// SHARED NAV — retractable sidebar + auth header helper.
// Included on every page. Keeps sidebar state in localStorage
// so it stays collapsed/expanded across page navigations
// (each page is a real reload, not an SPA).
// ============================================================

(function () {
  const sidebar = document.getElementById("sidebar");
  const hamburger = document.getElementById("hamburger");
  if (!sidebar || !hamburger) return;

  const STORAGE_KEY = "dev_dashboard_sidebar_collapsed";

  function applyState(collapsed) {
    sidebar.classList.toggle("collapsed", collapsed);
  }

  // Mobile defaults to collapsed on first load; desktop defaults to open.
  const stored = localStorage.getItem(STORAGE_KEY);
  const collapsedDefault = window.innerWidth <= 900;
  applyState(stored !== null ? stored === "1" : collapsedDefault);

  hamburger.addEventListener("click", () => {
    const nowCollapsed = !sidebar.classList.contains("collapsed");
    applyState(nowCollapsed);
    localStorage.setItem(STORAGE_KEY, nowCollapsed ? "1" : "0");
  });

  // Click-outside-to-close on mobile
  document.addEventListener("click", (e) => {
    if (window.innerWidth > 900) return;
    if (sidebar.classList.contains("collapsed")) return;
    if (sidebar.contains(e.target) || hamburger.contains(e.target)) return;
    applyState(true);
    localStorage.setItem(STORAGE_KEY, "1");
  });
})();

// ── Shared auth/fetch helper for every page's inline script ──
const DevAPI = {
  token() {
    return localStorage.getItem("dev_token");
  },
  headers() {
    const t = this.token();
    return t ? { Authorization: `Bearer ${t}`, "Content-Type": "application/json" } : { "Content-Type": "application/json" };
  },
  async get(url) {
    const r = await fetch(url, { headers: this.headers() });
    if (r.status === 401) return (window.location.href = "/login");
    return r.json();
  },
  async post(url, body) {
    const r = await fetch(url, { method: "POST", headers: this.headers(), body: JSON.stringify(body) });
    if (r.status === 401) return (window.location.href = "/login");
    return r.json();
  },
  async put(url, body) {
    const r = await fetch(url, { method: "PUT", headers: this.headers(), body: JSON.stringify(body) });
    if (r.status === 401) return (window.location.href = "/login");
    return r.json();
  },
  logout() {
    localStorage.removeItem("dev_token");
    window.location.href = "/login";
  },
};

function toast(msg) {
  const el = document.createElement("div");
  el.className = "toast";
  el.textContent = msg;
  document.body.appendChild(el);
  setTimeout(() => el.remove(), 3000);
}
