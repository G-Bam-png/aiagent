// Agent editor: settings / knowledge / channels / playground / conversations.
const TONES = ["дружелюбный", "деловой", "энергичный", "вежливый", "профессиональный", "тёплый", "заботливый", "строгий", "гостеприимный", "уверенный"];
const PROVIDERS = [["auto", "Авто (по умолчанию)"], ["anthropic", "Anthropic (Claude)"], ["openai", "OpenAI-совместимый"], ["demo", "Демо (офлайн)"]];
const CH_ICONS = { web: "🌐", avito: "🟢", telegram: "✈️", whatsapp: "💬", instagram: "📸", vk: "🅥", youtube: "▶️", tiktok: "🎵" };
const FIELD_LABELS = {
  client_id: "Client ID", client_secret: "Client Secret", user_id: "User ID Avito (необязательно — определим автоматически)",
  bot_token: "Bot Token (от @BotFather)", phone_number_id: "Phone Number ID", access_token: "Access Token",
  verify_token: "Verify Token", ig_account_id: "Instagram Account ID", group_id: "ID сообщества",
  confirmation_token: "Строка подтверждения", api_key: "API Key", channel_id: "Channel ID",
  oauth_token: "OAuth Token", client_key: "Client Key",
};
const TABS = [["settings", "⚙️ Настройки"], ["knowledge", "📚 База знаний"], ["channels", "🔌 Каналы"], ["playground", "💬 Тест"], ["conversations", "📨 Диалоги"]];

async function openAgent(id, tab) {
  tab = tab || "settings";
  try {
    App.currentAgent = await App.get("/agents/" + id);
  } catch (e) { toast(e.message, "err"); location.hash = "#agents"; return; }
  const a = App.currentAgent;
  document.getElementById("view").innerHTML = `
    <div class="page-head"><a href="#agents" style="color:var(--muted)">← Все агенты</a></div>
    <div class="ed-head">
      <div class="ava">${a.avatar}</div>
      <div><h2>${esc(a.name)}</h2><div class="sub">${esc(a.description || "Без описания")}</div></div>
      <div class="right">
        <select id="status-sel" style="width:150px">
          ${["draft", "active", "paused"].map((s) => `<option value="${s}" ${a.status === s ? "selected" : ""}>${STATUS_RU[s]}</option>`).join("")}
        </select>
      </div>
    </div>
    <div class="tabs" id="tabs">${TABS.map(([k, l]) => `<button data-tab="${k}" class="${k === tab ? "active" : ""}">${l}</button>`).join("")}</div>
    <div id="panel"></div>`;

  document.getElementById("status-sel").onchange = async (e) => {
    await App.patch("/agents/" + a.id, { status: e.target.value });
    App.currentAgent.status = e.target.value;
    toast("Статус обновлён", "ok");
  };
  document.querySelectorAll("#tabs button").forEach((b) =>
    b.onclick = () => { location.hash = `#agent/${a.id}/${b.dataset.tab}`; }
  );
  ({ settings: tabSettings, knowledge: tabKnowledge, channels: tabChannels, playground: tabPlayground, conversations: tabConversations }[tab] || tabSettings)();
}

// ─── Settings ───
function tabSettings() {
  const a = App.currentAgent;
  document.getElementById("panel").innerHTML = `<div class="panel"><div class="panel-grid">
    <div>
      <div class="field"><label>Имя агента</label><input id="f-name" value="${esc(a.name)}" /></div>
      <div class="row2">
        <div class="field"><label>Эмодзи</label><input id="f-avatar" value="${esc(a.avatar)}" maxlength="4" /></div>
        <div class="field"><label>Тон общения</label><select id="f-tone">${TONES.map((t) => `<option ${a.tone === t ? "selected" : ""}>${t}</option>`).join("")}</select></div>
      </div>
      <div class="field"><label>Описание</label><input id="f-desc" value="${esc(a.description)}" /></div>
      <div class="field"><label>Приветствие <span class="hint">(первое сообщение клиенту)</span></label><textarea id="f-greet">${esc(a.greeting)}</textarea></div>
    </div>
    <div>
      <div class="field"><label>Роль и инструкция <span class="hint">(что и как делает агент)</span></label><textarea id="f-prompt" style="min-height:140px">${esc(a.system_prompt)}</textarea></div>
      <div class="row2">
        <div class="field"><label>LLM-провайдер</label><select id="f-prov">${PROVIDERS.map(([v, l]) => `<option value="${v}" ${a.provider === v ? "selected" : ""}>${l}</option>`).join("")}</select></div>
        <div class="field"><label>Модель <span class="hint">(необязательно)</span></label><input id="f-model" value="${esc(a.model)}" placeholder="по умолчанию" /></div>
      </div>
      <div class="field"><label>Креативность: <span id="t-val">${a.temperature}</span></label>
        <input id="f-temp" type="range" min="0" max="1" step="0.1" value="${a.temperature}" oninput="document.getElementById('t-val').textContent=this.value" /></div>
      <div class="field"><label>Слова-триггеры передачи оператору</label><input id="f-esc" value="${esc(a.escalation_keywords)}" /></div>
      <div class="field"><label>Сообщение при передаче</label><input id="f-fb" value="${esc(a.fallback_message)}" /></div>
    </div>
  </div>
  <button class="btn btn-primary" id="save" style="margin-top:8px">💾 Сохранить изменения</button></div>`;

  document.getElementById("save").onclick = async () => {
    const get = (i) => document.getElementById(i).value;
    try {
      const upd = {
        name: get("f-name"), avatar: get("f-avatar"), tone: get("f-tone"), description: get("f-desc"),
        greeting: get("f-greet"), system_prompt: get("f-prompt"), provider: get("f-prov"),
        model: get("f-model"), temperature: parseFloat(get("f-temp")),
        escalation_keywords: get("f-esc"), fallback_message: get("f-fb"),
      };
      App.currentAgent = await App.patch("/agents/" + a.id, upd);
      toast("Сохранено ✓", "ok");
      openAgent(a.id, "settings");
    } catch (e) { toast(e.message, "err"); }
  };
}

// ─── Knowledge base ───
async function tabKnowledge() {
  const a = App.currentAgent;
  const p = document.getElementById("panel");
  p.innerHTML = `<div class="panel">
    <h3 style="margin-bottom:6px">База знаний</h3>
    <p style="color:var(--muted);margin-bottom:18px">Агент отвечает на основе этих материалов: прайсы, услуги, FAQ, условия.</p>
    <div id="docs"></div>
    <button class="btn btn-ghost" id="add-doc">➕ Добавить материал</button>
  </div>`;
  const docs = await App.get(`/agents/${a.id}/docs`);
  const list = document.getElementById("docs");
  list.innerHTML = docs.length ? "" : '<div class="empty">Пока нет материалов</div>';
  docs.forEach((d) => {
    const item = el(`<div class="litem"><span class="ic">📄</span>
      <div class="grow"><h4>${esc(d.title)}</h4><p>${esc(d.content.slice(0, 90))}…</p></div>
      <button class="icon-btn" title="Удалить">🗑️</button></div>`);
    item.querySelector("button").onclick = async () => {
      await App.del(`/agents/${a.id}/docs/${d.id}`); toast("Удалено", "ok"); tabKnowledge();
    };
    list.appendChild(item);
  });
  document.getElementById("add-doc").onclick = () => {
    const m = modal(`<span class="x">✕</span><h3>Новый материал</h3>
      <div class="field" style="margin-top:14px"><label>Заголовок</label><input id="d-title" placeholder="Например: Прайс-лист" /></div>
      <div class="field"><label>Содержание</label><textarea id="d-content" style="min-height:160px" placeholder="Текст, который будет знать агент…"></textarea></div>
      <button class="btn btn-primary" id="d-save" style="width:100%;justify-content:center">Сохранить</button>`);
    m.querySelector(".x").onclick = () => m.remove();
    m.querySelector("#d-save").onclick = async () => {
      const title = m.querySelector("#d-title").value.trim();
      const content = m.querySelector("#d-content").value.trim();
      if (!title || !content) return toast("Заполните оба поля", "err");
      try { await App.post(`/agents/${a.id}/docs`, { title, content }); m.remove(); toast("Добавлено ✓", "ok"); tabKnowledge(); }
      catch (e) { toast(e.message, "err"); }
    };
  };
}

// ─── Channels ───
async function tabChannels() {
  const a = App.currentAgent;
  const p = document.getElementById("panel");
  p.innerHTML = `<div class="panel">
    <h3 style="margin-bottom:6px">Каналы</h3>
    <p style="color:var(--muted);margin-bottom:18px">Подключите агента к мессенджерам, соцсетям и сайту.</p>
    <div id="chs"></div>
    <button class="btn btn-primary" id="add-ch">➕ Подключить канал</button>
  </div>`;
  const chs = await App.get(`/agents/${a.id}/channels`);
  const list = document.getElementById("chs");
  list.innerHTML = chs.length ? "" : '<div class="empty">Каналы не подключены</div>';
  chs.forEach((c) => {
    const item = el(`<div class="litem"><span class="ic">${CH_ICONS[c.type] || "🔌"}</span>
      <div class="grow"><h4>${esc(c.name)}</h4><p><span class="badge-status s-${c.status}">${c.status}</span></p></div>
      <button class="icon-btn" data-cfg title="Настроить">⚙️</button>
      <button class="icon-btn" data-vfy title="Проверить">🔄</button>
      <button class="icon-btn" data-del title="Удалить">🗑️</button></div>`);
    item.querySelector("[data-del]").onclick = async () => { await App.del("/channels/" + c.id); toast("Канал удалён", "ok"); tabChannels(); };
    item.querySelector("[data-vfy]").onclick = async () => { const r = await App.post(`/channels/${c.id}/verify`); toast(r.message, r.ok ? "ok" : "err"); tabChannels(); };
    item.querySelector("[data-cfg]").onclick = () => configChannel(c.id);
    list.appendChild(item);
  });
  document.getElementById("add-ch").onclick = pickChannel;
}

function pickChannel() {
  const a = App.currentAgent;
  const opts = App.channelCatalog.map((c) => `
    <div class="ch-opt" data-type="${c.type}">
      <div class="n">${c.icon} ${esc(c.name)} ${c.status === "live" ? '<span class="tag-live">live</span>' : '<span class="tag-soon">scaffold</span>'}</div>
      <div class="b">${esc(c.blurb)}</div>
    </div>`).join("");
  const m = modal(`<span class="x">✕</span><h3>Подключить канал</h3>
    <p style="color:var(--muted);margin:4px 0 16px">Выберите платформу</p>
    <div class="ch-pick">${opts}</div><div id="ch-form"></div>`);
  m.querySelector(".x").onclick = () => m.remove();
  m.querySelectorAll(".ch-opt").forEach((o) =>
    o.onclick = () => {
      m.querySelectorAll(".ch-opt").forEach((x) => x.classList.remove("sel"));
      o.classList.add("sel");
      renderChannelForm(m, a, o.dataset.type);
    }
  );
}

function avitoHelp() {
  return `<details class="help-box"><summary>Где взять Client ID и Client Secret?</summary>
    <ol>
      <li>Войдите в бизнес-аккаунт на <a href="https://www.avito.ru" target="_blank" rel="noopener">avito.ru</a>.</li>
      <li>Откройте кабинет разработчика <a href="https://developers.avito.ru" target="_blank" rel="noopener">developers.avito.ru</a> (или в ЛК Avito: «Для профессионалов» → «API»).</li>
      <li>Создайте приложение / заявку на доступ к API: название, описание и права (scope). Для агента нужен <b>Мессенджер</b> (messenger:read, messenger:write) и доступ к профилю.</li>
      <li>После одобрения в кабинете разработчика появятся <b>Client ID</b> и <b>Client Secret</b> (также приходят на e-mail вместе с User ID).</li>
      <li>Нет письма? <b>Client Secret</b> — в разделе «Для профессионалов» → «API»; <b>Client ID</b> — в «Настройки → Номер профиля».</li>
      <li>Доступ к <b>Messenger API</b> включается по заявке/модерации — при необходимости напишите в поддержку Avito API.</li>
    </ol></details>`;
}

function renderChannelForm(m, a, type) {
  const cat = App.channelCatalog.find((c) => c.type === type);
  const fields = cat.fields.map((f) =>
    `<div class="field"><label>${FIELD_LABELS[f] || f}</label><input data-f="${f}" /></div>`).join("");
  m.querySelector("#ch-form").innerHTML = `<div style="margin-top:14px;border-top:1px solid var(--line);padding-top:14px">
    ${cat.status !== "live" ? '<p style="color:var(--warn);font-size:13px;margin-bottom:10px">⚠️ Канал в режиме заглушки: учётные данные сохранятся, реальную отправку нужно дописать в адаптере.</p>' : ""}
    ${type === "avito" ? '<p style="color:var(--muted);font-size:13px;margin-bottom:10px">Введите Client ID и Client Secret — <b>User ID определится автоматически</b> через профиль Avito. Поле User ID можно оставить пустым.</p>' : ""}
    ${type === "avito" ? avitoHelp() : ""}
    ${fields || '<p style="color:var(--muted);font-size:14px">Дополнительных данных не требуется.</p>'}
    <button class="btn btn-primary" id="ch-save" style="width:100%;justify-content:center;margin-top:6px">Подключить</button></div>`;
  m.querySelector("#ch-save").onclick = async () => {
    const config = {};
    m.querySelectorAll("[data-f]").forEach((i) => { if (i.value.trim()) config[i.dataset.f] = i.value.trim(); });
    try {
      const r = await App.post(`/agents/${a.id}/channels`, { type, config });
      m.remove();
      toast(r.message, r.ok ? "ok" : "err");
      if (type === "web" || type === "avito") setTimeout(() => configChannel(r.channel.id), 300);
      tabChannels();
    } catch (e) { toast(e.message, "err"); }
  };
}

async function configChannel(id) {
  const d = await App.get("/channels/" + id);
  let inner = `<span class="x">✕</span><h3>${CH_ICONS[d.type] || ""} ${esc(d.name)}</h3>
    <p style="color:var(--muted);margin:4px 0 14px">Статус: <span class="badge-status s-${d.status}">${d.status}</span></p>`;
  if (d.type === "web") {
    inner += `<p style="font-size:14px;margin-bottom:8px">Вставьте этот код на свой сайт перед <code>&lt;/body&gt;</code>:</p>
      <div class="code">${esc(d.widget_snippet)}</div>
      <p style="color:var(--muted);font-size:13px;margin-top:8px">Замените <b>ВАШ-ДОМЕН</b> на адрес, где запущена платформа.</p>
      <a class="btn btn-ghost" style="margin-top:12px" target="_blank" href="/widget-demo.html?key=${d.public_key}">▶️ Открыть демо-страницу с виджетом</a>`;
  } else {
    const url = `${location.origin}${d.webhook_path}`;
    const isLocal = url.includes("localhost") || url.includes("127.0.0.1");
    if (d.config && d.config.user_id) {
      inner += `<p style="font-size:14px;margin-bottom:10px">✅ User ID определён: <b>${esc(String(d.config.user_id))}</b></p>`;
    }
    inner += `<p style="font-size:14px;margin-bottom:6px">Webhook URL платформы (входящие сообщения):</p>
      <div class="code">${url}</div>`;
    if (d.type === "avito") {
      inner += `<p style="color:var(--muted);font-size:13px;margin:10px 0">У Avito нет поля для webhook в кабинете — он регистрируется через API. Нажмите кнопку, и платформа сама вызовет <code>POST /messenger/v3/webhook</code> с этим адресом.</p>`;
      if (isLocal) {
        inner += `<p style="color:var(--warn);font-size:13px;margin-bottom:10px">⚠️ Avito не сможет достучаться до localhost. Откройте платформу по публичному HTTPS-домену или через туннель (ngrok / cloudflared), затем регистрируйте webhook.</p>`;
      }
      inner += `<button class="btn btn-primary" id="reg-wh" style="width:100%;justify-content:center">🔔 Зарегистрировать webhook в Avito</button>`;
    } else {
      inner += `<p style="color:var(--muted);font-size:13px;margin-top:8px">Укажите этот адрес в настройках вебхука ${esc(d.name)}.</p>`;
    }
  }
  const m = modal(inner);
  m.querySelector(".x").onclick = () => m.remove();
  const reg = m.querySelector("#reg-wh");
  if (reg)
    reg.onclick = async () => {
      reg.disabled = true;
      reg.textContent = "Регистрируем…";
      try {
        const r = await App.post(`/channels/${d.id}/register-webhook`, {
          url: `${location.origin}${d.webhook_path}`,
        });
        toast(r.message, r.ok ? "ok" : "err");
      } catch (e) {
        toast(e.message, "err");
      }
      reg.disabled = false;
      reg.textContent = "🔔 Зарегистрировать webhook в Avito";
    };
}

// ─── Playground ───
function tabPlayground() {
  const a = App.currentAgent;
  document.getElementById("panel").innerHTML = `<div class="panel">
    <div style="display:flex;justify-content:space-between;align-items:center;margin-bottom:14px">
      <div><h3>Песочница</h3><p style="color:var(--muted)">Проверьте ответы агента перед запуском</p></div>
      <button class="btn btn-ghost" id="pg-reset">↺ Сбросить</button>
    </div>
    <div class="pg"><div class="pg-body" id="pg-body"></div>
      <div class="pg-foot"><input id="pg-inp" placeholder="Напишите как клиент…" /><button class="btn btn-primary" id="pg-send">➤</button></div>
    </div></div>`;
  const body = document.getElementById("pg-body");
  const inp = document.getElementById("pg-inp");
  if (a.greeting) addCB(body, a.greeting, "a");

  async function send() {
    const text = inp.value.trim(); if (!text) return;
    inp.value = ""; addCB(body, text, "u");
    const t = addCB(body, "…", "a");
    try {
      const r = await App.post(`/agents/${a.id}/playground`, { message: text });
      t.textContent = r.reply;
      if (r.needs_human) addCB(body, "⚠️ Агент передал бы диалог оператору", "sys");
    } catch (e) { t.textContent = "Ошибка: " + e.message; }
    body.scrollTop = body.scrollHeight;
  }
  document.getElementById("pg-send").onclick = send;
  inp.onkeydown = (e) => { if (e.key === "Enter") send(); };
  document.getElementById("pg-reset").onclick = async () => {
    await App.post(`/agents/${a.id}/playground/reset`); body.innerHTML = "";
    if (a.greeting) addCB(body, a.greeting, "a"); toast("Сброшено", "ok");
  };
}
function addCB(body, text, cls) {
  const d = el(`<div class="cb ${cls}"></div>`); d.textContent = text;
  body.appendChild(d); body.scrollTop = body.scrollHeight; return d;
}

// ─── Conversations ───
async function tabConversations() {
  const a = App.currentAgent;
  const p = document.getElementById("panel");
  p.innerHTML = `<div class="panel"><h3 style="margin-bottom:14px">Диалоги</h3>
    <div class="panel-grid"><div id="conv-list"></div><div id="conv-msgs"><div class="empty">Выберите диалог</div></div></div></div>`;
  const convs = await App.get(`/agents/${a.id}/conversations`);
  const list = document.getElementById("conv-list");
  list.innerHTML = convs.length ? "" : '<div class="empty">Пока нет диалогов</div>';
  convs.forEach((c) => {
    const item = el(`<div class="litem" style="cursor:pointer"><span class="ic">${c.channel_id ? "🔌" : "🧪"}</span>
      <div class="grow"><h4>${esc(c.contact)}</h4><p>${new Date(c.last_message_at).toLocaleString("ru")}</p></div>
      <span class="badge-status s-${c.status === "needs_human" ? "error" : "active"}">${c.status === "needs_human" ? "оператор" : "ок"}</span></div>`);
    item.onclick = async () => {
      const msgs = await App.get(`/agents/${a.id}/conversations/${c.id}/messages`);
      const box = document.getElementById("conv-msgs");
      box.innerHTML = `<div class="pg" style="height:430px"><div class="pg-body" id="cm"></div></div>`;
      const cm = box.querySelector("#cm");
      msgs.forEach((mm) => addCB(cm, mm.text, mm.role === "user" ? "u" : "a"));
    };
    list.appendChild(item);
  });
}
