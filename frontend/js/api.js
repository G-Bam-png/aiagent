// Tiny API client + shared UI helpers, exposed on window.App.
const App = {
  token: localStorage.getItem("nexus_token") || null,
  user: null,
  templates: [],
  channelCatalog: [],
  provider: "demo",

  setToken(t) {
    this.token = t;
    if (t) localStorage.setItem("nexus_token", t);
    else localStorage.removeItem("nexus_token");
  },

  async req(method, path, body) {
    const headers = { "Content-Type": "application/json" };
    if (this.token) headers.Authorization = "Bearer " + this.token;
    const res = await fetch("/api" + path, {
      method,
      headers,
      body: body !== undefined ? JSON.stringify(body) : undefined,
    });
    if (res.status === 204) return null;
    const data = await res.json().catch(() => ({}));
    if (!res.ok) throw new Error(data.detail || "Ошибка " + res.status);
    return data;
  },
  get(p) { return this.req("GET", p); },
  post(p, b) { return this.req("POST", p, b); },
  patch(p, b) { return this.req("PATCH", p, b); },
  del(p) { return this.req("DELETE", p); },
};

// ─── UI helpers ───
function el(html) {
  const t = document.createElement("template");
  t.innerHTML = html.trim();
  return t.content.firstElementChild;
}
function esc(s) {
  return (s || "").replace(/[&<>"]/g, (c) =>
    ({ "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;" }[c])
  );
}
function toast(msg, kind) {
  const t = el(`<div class="toast ${kind || ""}">${esc(msg)}</div>`);
  document.body.appendChild(t);
  setTimeout(() => t.remove(), 2800);
}
function modal(inner) {
  const bg = el('<div class="modal-bg"></div>');
  bg.appendChild(el(`<div class="modal">${inner}</div>`));
  bg.addEventListener("click", (e) => { if (e.target === bg) bg.remove(); });
  document.body.appendChild(bg);
  return bg;
}
const STATUS_RU = { active: "Активен", draft: "Черновик", paused: "Пауза" };
