// Dashboard: auth, shell, routing, overview, agents list, template picker.
const root = () => document.getElementById("root");

async function bootstrap() {
  try {
    [App.templates, App.channelCatalog] = await Promise.all([
      App.get("/catalog/templates"),
      App.get("/catalog/channels"),
    ]);
    App.provider = (await App.get("/catalog/provider")).provider;
  } catch (e) { /* backend may be warming up */ }

  if (App.token) {
    try {
      App.user = await App.get("/auth/me");
      renderShell();
      window.addEventListener("hashchange", route);
      route();
      return;
    } catch { App.setToken(null); }
  }
  renderAuth(location.hash === "#register" ? "register" : "login");
}

// ─── Auth ───
function renderAuth(mode) {
  const isReg = mode === "register";
  root().innerHTML = `
  <div class="auth-wrap"><div class="auth-card">
    <a href="/" class="logo"><span class="logo-mark">N</span> Nexus<span style="color:var(--brand)">Agents</span></a>
    <h2>${isReg ? "Создать аккаунт" : "С возвращением"}</h2>
    <p class="sub">${isReg ? "Запустите первого ИИ-агента бесплатно" : "Войдите в личный кабинет"}</p>
    <form id="auth-form">
      ${isReg ? '<div class="field"><label>Имя</label><input name="name" placeholder="Иван" /></div>' : ""}
      <div class="field"><label>Email</label><input name="email" type="email" required placeholder="you@company.ru" /></div>
      <div class="field"><label>Пароль</label><input name="password" type="password" required minlength="6" placeholder="Минимум 6 символов" /></div>
      <button class="btn btn-primary" style="width:100%;justify-content:center" type="submit">${isReg ? "Зарегистрироваться" : "Войти"} →</button>
    </form>
    <p class="auth-switch">${isReg ? "Уже есть аккаунт?" : "Нет аккаунта?"}
      <a id="switch">${isReg ? "Войти" : "Создать бесплатно"}</a></p>
    <div class="demo-hint">Демо-доступ: <b>demo@nexus.ai</b> / <b>demo12345</b></div>
  </div></div>`;

  document.getElementById("switch").onclick = () => renderAuth(isReg ? "login" : "register");
  document.getElementById("auth-form").onsubmit = async (e) => {
    e.preventDefault();
    const f = Object.fromEntries(new FormData(e.target));
    try {
      const res = await App[isReg ? "post" : "post"](isReg ? "/auth/register" : "/auth/login", f);
      App.setToken(res.token);
      App.user = res.user;
      location.hash = "#dashboard";
      renderShell();
      window.addEventListener("hashchange", route);
      route();
    } catch (err) { toast(err.message, "err"); }
  };
}

// ─── Shell ───
function renderShell() {
  const nav = [
    ["#dashboard", "📊", "Дашборд"],
    ["#agents", "🤖", "Мои агенты"],
    ["#new", "➕", "Создать агента"],
  ];
  root().innerHTML = `
  <div class="dash">
    <aside class="sidebar">
      <a href="/" class="logo"><span class="logo-mark">N</span> NexusAgents</a>
      <nav class="side-nav" id="side-nav">
        ${nav.map(([h, i, t]) => `<a href="${h}" data-h="${h}">${i} ${t}</a>`).join("")}
      </nav>
      <div class="side-foot">
        <div class="user">${esc(App.user.name || App.user.email)}</div>
        <div class="prov">⚙️ LLM: ${App.provider}${App.provider === "demo" ? " (офлайн)" : ""}</div>
        <div class="logout" id="logout">Выйти →</div>
      </div>
    </aside>
    <main class="content" id="view"></main>
  </div>`;
  document.getElementById("logout").onclick = () => {
    App.setToken(null); App.user = null; location.hash = ""; renderAuth("login");
  };
}

function setActiveNav() {
  const base = "#" + (location.hash.replace("#", "").split(/[/=]/)[0] || "dashboard");
  document.querySelectorAll("#side-nav a").forEach((a) =>
    a.classList.toggle("active", a.dataset.h === base)
  );
}

// ─── Router ───
function route() {
  if (!App.user) return;
  setActiveNav();
  const h = location.hash.replace("#", "");
  if (h.startsWith("agent/")) return openAgent(...h.split("/").slice(1)); // editor.js
  if (h.startsWith("new")) return viewNew(h.includes("=") ? h.split("=")[1] : null);
  if (h === "agents") return viewAgents();
  return viewDashboard();
}

// ─── Dashboard overview ───
async function viewDashboard() {
  const view = document.getElementById("view");
  view.innerHTML = `<div class="page-head"><div><h1>Дашборд</h1><p>Обзор ваших ИИ-агентов</p></div>
    <a href="#new" class="btn btn-primary">➕ Новый агент</a></div>
    <div class="stats" id="stats"></div>
    <h2 style="font-size:19px;margin:6px 0 14px">Последние агенты</h2>
    <div class="cards" id="cards"></div>`;
  try {
    const [s, agents] = await Promise.all([App.get("/stats"), App.get("/agents")]);
    document.getElementById("stats").innerHTML = [
      ["🤖", s.agents, "Агентов"],
      ["🟢", s.active, "Активных"],
      ["💬", s.conversations, "Диалогов"],
      ["🙋", s.needs_human, "Ждут оператора"],
    ].map(([i, v, l]) => `<div class="stat-card"><span class="ic">${i}</span><div class="v">${v}</div><div class="l">${l}</div></div>`).join("");
    renderAgentCards(agents.slice(0, 6), "cards");
  } catch (e) { toast(e.message, "err"); }
}

// ─── Agents list ───
async function viewAgents() {
  const view = document.getElementById("view");
  view.innerHTML = `<div class="page-head"><div><h1>Мои агенты</h1><p>Управляйте и настраивайте агентов</p></div>
    <a href="#new" class="btn btn-primary">➕ Новый агент</a></div><div class="cards" id="cards"></div>`;
  try {
    renderAgentCards(await App.get("/agents"), "cards");
  } catch (e) { toast(e.message, "err"); }
}

function renderAgentCards(agents, containerId) {
  const c = document.getElementById(containerId);
  if (!agents.length) {
    c.innerHTML = `<div class="empty" style="grid-column:1/-1">У вас пока нет агентов. <a href="#new" style="color:var(--brand);font-weight:600">Создайте первого →</a></div>`;
    return;
  }
  c.innerHTML = "";
  agents.forEach((a) => {
    const card = el(`<div class="acard">
      <div class="top"><div class="ava">${a.avatar}</div>
        <div><h3>${esc(a.name)}</h3><span class="badge-status s-${a.status}">${STATUS_RU[a.status] || a.status}</span></div></div>
      <div class="desc">${esc(a.description || "Без описания")}</div>
      <div class="foot">
        <a href="#agent/${a.id}" class="btn btn-ghost" style="padding:8px 16px">Открыть</a>
        <div class="actions"><button class="icon-btn" data-del="${a.id}" title="Удалить">🗑️</button></div>
      </div></div>`);
    card.querySelector("[data-del]").onclick = async (e) => {
      e.preventDefault();
      if (!confirm(`Удалить агента «${a.name}»?`)) return;
      await App.del("/agents/" + a.id);
      toast("Агент удалён", "ok");
      route();
    };
    c.appendChild(card);
  });
}

// ─── New agent (template picker) ───
async function viewNew(presetKey) {
  if (presetKey) { return createFromTemplate(presetKey); }
  const view = document.getElementById("view");
  view.innerHTML = `<div class="page-head"><div><h1>Создать агента</h1><p>Выберите готовый шаблон или начните с нуля</p></div></div>
    <div class="tpl-grid" id="tpl-grid"></div>`;
  document.getElementById("tpl-grid").innerHTML = App.templates.map((t) => `
    <div class="tpl" data-key="${t.key}">
      <div class="e">${t.avatar}</div><h4>${esc(t.name)}</h4>
      <div class="tl">${esc(t.tagline)}</div><p>${esc(t.description)}</p>
    </div>`).join("");
  document.querySelectorAll(".tpl").forEach((el2) =>
    el2.onclick = () => createFromTemplate(el2.dataset.key)
  );
}

async function createFromTemplate(key) {
  const t = App.templates.find((x) => x.key === key) || { key: "custom", name: "Новый агент", avatar: "🤖" };
  try {
    const agent = await App.post("/agents", {
      name: t.name === "Свой агент с нуля" ? "Новый агент" : t.name,
      template_key: t.key,
      avatar: t.avatar,
      description: t.description || "",
      system_prompt: t.system_prompt || "",
      tone: t.tone || "дружелюбный",
      status: "draft",
    });
    toast("Агент создан — настройте его", "ok");
    location.hash = "#agent/" + agent.id;
  } catch (e) { toast(e.message, "err"); }
}

bootstrap();
