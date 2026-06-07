// Landing page: render the live agent gallery + integrations from the API.
const ICONS = {
  web: "🌐", avito: "🟢", telegram: "✈️", whatsapp: "💬",
  instagram: "📸", vk: "🅥", youtube: "▶️", tiktok: "🎵",
};
const CH_NAME = {
  web: "Сайт", avito: "Avito", telegram: "Telegram", whatsapp: "WhatsApp",
  instagram: "Instagram", vk: "ВК", youtube: "YouTube", tiktok: "TikTok",
};

let templates = [];
let activeCat = "Все";

async function load() {
  try {
    const res = await fetch("/api/catalog/templates");
    templates = await res.json();
  } catch (e) {
    document.getElementById("agents-grid").innerHTML =
      '<div class="agent-card"><p>Не удалось загрузить галерею. Запустите бэкенд.</p></div>';
    return;
  }
  renderFilters();
  renderAgents();
}

function renderFilters() {
  const cats = ["Все", ...new Set(templates.map((t) => t.category))];
  const el = document.getElementById("cat-filter");
  el.innerHTML = cats
    .map(
      (c) =>
        `<button class="${c === activeCat ? "active" : ""}" data-cat="${c}">${c}</button>`
    )
    .join("");
  el.querySelectorAll("button").forEach((b) =>
    b.addEventListener("click", () => {
      activeCat = b.dataset.cat;
      renderFilters();
      renderAgents();
    })
  );
}

function renderAgents() {
  const list =
    activeCat === "Все"
      ? templates
      : templates.filter((t) => t.category === activeCat);
  document.getElementById("agents-grid").innerHTML = list
    .map(
      (t) => `
    <div class="agent-card">
      <span class="emoji">${t.avatar}</span>
      <span class="cat-tag">${t.category}</span>
      <h4>${t.name}</h4>
      <div class="tagline">${t.tagline}</div>
      <p>${t.description}</p>
      <div class="ch-row">${(t.channels || [])
        .map((c) => `<span>${ICONS[c] || "•"} ${CH_NAME[c] || c}</span>`)
        .join("")}</div>
      <a href="/app.html#new=${t.key}" class="btn btn-ghost" style="justify-content:center">Использовать шаблон</a>
    </div>`
    )
    .join("");
}

load();
