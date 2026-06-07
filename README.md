# Nexus Agents — платформа для создания ИИ-агентов

Платформа в стиле [nextbot.ru](https://nextbot.ru): пользователи создают ИИ-агентов,
обучают их на базе знаний и подключают к каналам (Avito, Telegram, сайт, Instagram,
YouTube, TikTok, WhatsApp, ВК) для автоматизации общения и продаж.

## Что внутри

- **Лендинг** (`/`) — как у NextBot: возможности, галерея агентов, интеграции, тарифы.
- **Личный кабинет** (`/app.html`) — регистрация/вход, дашборд, конструктор агентов:
  настройки, база знаний, каналы, песочница (тест), диалоги.
- **Встраиваемый виджет** (`/widget.js`) — чат для любого сайта одной строкой кода.
- **Бэкенд** — FastAPI + SQLite, мультиканальные адаптеры, движок ответа на GPT/Claude.

### Статус каналов
| Канал | Статус |
|-------|--------|
| Сайт (виджет), Telegram, Avito | ✅ работают «из коробки» |
| Instagram, YouTube, TikTok, WhatsApp, ВКонтакте | 🧩 каркас: креды сохраняются, реальную отправку нужно дописать в адаптере (нужен доступ к API платформ) |

## Запуск (Windows)

> На этой машине `python` — заглушка, используйте `py`.

```powershell
cd "agent-platform\backend"
py -m venv .venv
.\.venv\Scripts\Activate.ps1
$env:NO_PROXY="*"            # обход системного SOCKS-прокси при установке
pip install -r requirements.txt
copy .env.example .env       # при желании впишите ключи LLM/каналов
uvicorn app.main:app --reload --port 8000
```

Откройте **http://localhost:8000** — лендинг, и **http://localhost:8000/app.html** — кабинет.

Или просто запустите `run.ps1` из корня проекта.

## Демо-доступ

Создаётся автоматически при первом старте:

- **Email:** `demo@nexus.ai`
- **Пароль:** `demo12345`

Внутри — готовый агент «Алиса — отдел продаж» с базой знаний и виджетом.

## LLM-провайдеры

Задаются в `.env` (`LLM_PROVIDER=auto|anthropic|openai|demo`):

- **demo** — работает офлайн без ключей (ответы-заглушки), чтобы сразу попробовать платформу.
- **anthropic** — задайте `ANTHROPIC_API_KEY`.
- **openai** — задайте `OPENAI_API_KEY` (подходит любой OpenAI-совместимый endpoint через `OPENAI_BASE_URL`).

`auto` выбирает anthropic → openai → demo по наличию ключей.

## Архитектура

```
backend/app/
  main.py        FastAPI, отдаёт API + фронтенд
  models.py      User, Agent, KnowledgeDoc, Channel, Conversation, Message
  llm.py         провайдеры anthropic / openai / demo
  runtime.py     сборка промпта (роль + база знаний + история) → ответ + эскалация
  service.py     ведение диалога (общее для песочницы и каналов)
  channels/      адаптеры каналов (web, telegram, avito — живые; остальные — каркас)
  routers/       auth, agents, channels, chat (виджет/вебхуки), meta (каталог/статистика)
frontend/
  index.html     лендинг
  app.html       личный кабинет (SPA на ванильном JS)
  widget.js      встраиваемый чат
```
