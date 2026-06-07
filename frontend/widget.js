/* Nexus Agents — embeddable chat widget.
   Usage:  <script src="https://YOUR-HOST/widget.js" data-key="PUBLIC_KEY" defer></script> */
(function () {
  var script = document.currentScript;
  var key = script && script.getAttribute("data-key");
  if (!key) return console.error("[NexusWidget] data-key is required");
  var base = new URL(script.src).origin;
  var sid =
    localStorage.getItem("nexus_sid") ||
    (function () {
      var s = "w_" + Math.random().toString(36).slice(2) + Date.now().toString(36);
      localStorage.setItem("nexus_sid", s);
      return s;
    })();

  var css =
    "#nx-btn{position:fixed;bottom:22px;right:22px;width:62px;height:62px;border-radius:50%;" +
    "background:linear-gradient(120deg,#6d28d9,#4f46e5,#db2777);color:#fff;font-size:28px;border:0;" +
    "cursor:pointer;box-shadow:0 12px 34px rgba(79,70,229,.45);z-index:2147483000;transition:transform .2s}" +
    "#nx-btn:hover{transform:scale(1.08)}" +
    "#nx-win{position:fixed;bottom:96px;right:22px;width:370px;max-width:calc(100vw - 32px);height:540px;" +
    "max-height:calc(100vh - 130px);background:#fff;border-radius:18px;box-shadow:0 24px 70px rgba(0,0,0,.25);" +
    "display:none;flex-direction:column;overflow:hidden;z-index:2147483000;font-family:Inter,Segoe UI,sans-serif}" +
    "#nx-win.open{display:flex}" +
    "#nx-head{background:linear-gradient(120deg,#6d28d9,#4f46e5,#db2777);color:#fff;padding:15px 18px;display:flex;align-items:center;gap:11px}" +
    "#nx-head .a{width:38px;height:38px;border-radius:50%;background:rgba(255,255,255,.22);display:grid;place-items:center;font-size:19px}" +
    "#nx-head b{font-size:15px}#nx-head small{opacity:.85;font-size:12px}#nx-x{margin-left:auto;cursor:pointer;font-size:20px;opacity:.85}" +
    "#nx-body{flex:1;overflow-y:auto;padding:16px;background:#f6f7fb;display:flex;flex-direction:column;gap:10px}" +
    ".nx-b{max-width:80%;padding:10px 14px;border-radius:14px;font-size:14px;line-height:1.45;white-space:pre-wrap}" +
    ".nx-in{background:#fff;border:1px solid #e9e8f2;align-self:flex-start;border-bottom-left-radius:4px}" +
    ".nx-out{background:linear-gradient(120deg,#6d28d9,#4f46e5);color:#fff;align-self:flex-end;border-bottom-right-radius:4px}" +
    "#nx-foot{display:flex;gap:8px;padding:12px;border-top:1px solid #e9e8f2;background:#fff}" +
    "#nx-inp{flex:1;border:1px solid #e9e8f2;border-radius:10px;padding:10px 12px;font-size:14px;outline:none;font-family:inherit}" +
    "#nx-inp:focus{border-color:#6d28d9}" +
    "#nx-send{background:linear-gradient(120deg,#6d28d9,#4f46e5);color:#fff;border:0;border-radius:10px;padding:0 16px;cursor:pointer;font-size:18px}";
  var st = document.createElement("style");
  st.textContent = css;
  document.head.appendChild(st);

  var btn = document.createElement("button");
  btn.id = "nx-btn";
  btn.innerHTML = "💬";
  var win = document.createElement("div");
  win.id = "nx-win";
  win.innerHTML =
    '<div id="nx-head"><div class="a" id="nx-ava">🤖</div><div><b id="nx-name">Ассистент</b><br><small>онлайн</small></div><span id="nx-x">✕</span></div>' +
    '<div id="nx-body"></div>' +
    '<div id="nx-foot"><input id="nx-inp" placeholder="Напишите сообщение…" autocomplete="off"/><button id="nx-send">➤</button></div>';
  document.body.appendChild(btn);
  document.body.appendChild(win);

  var body = win.querySelector("#nx-body");
  var inp = win.querySelector("#nx-inp");
  var greeted = false;

  function bubble(text, cls) {
    var d = document.createElement("div");
    d.className = "nx-b " + cls;
    d.textContent = text;
    body.appendChild(d);
    body.scrollTop = body.scrollHeight;
    return d;
  }

  fetch(base + "/api/public/agent/" + key)
    .then((r) => r.json())
    .then((a) => {
      win.querySelector("#nx-name").textContent = a.name || "Ассистент";
      win.querySelector("#nx-ava").textContent = a.avatar || "🤖";
      win._greeting = a.greeting;
    })
    .catch(() => {});

  function toggle() {
    win.classList.toggle("open");
    if (win.classList.contains("open") && !greeted) {
      greeted = true;
      bubble(win._greeting || "Здравствуйте! Чем могу помочь?", "nx-in");
      inp.focus();
    }
  }
  btn.onclick = toggle;
  win.querySelector("#nx-x").onclick = toggle;

  function send() {
    var text = inp.value.trim();
    if (!text) return;
    inp.value = "";
    bubble(text, "nx-out");
    var t = bubble("…", "nx-in");
    fetch(base + "/api/public/chat/" + key, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ message: text, session_id: sid }),
    })
      .then((r) => r.json())
      .then((d) => {
        t.textContent = d.reply || "Извините, попробуйте ещё раз.";
        body.scrollTop = body.scrollHeight;
      })
      .catch(() => {
        t.textContent = "Ошибка соединения. Попробуйте позже.";
      });
  }
  win.querySelector("#nx-send").onclick = send;
  inp.addEventListener("keydown", function (e) {
    if (e.key === "Enter") send();
  });
})();
