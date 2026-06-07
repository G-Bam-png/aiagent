"""Core agent engine: turn an incoming message into a grounded reply."""

from . import llm
from .models import Agent, KnowledgeDoc, Message

HUMAN_TAG = "[NEEDS_HUMAN]"
_MAX_HISTORY = 12
_MAX_KB_CHARS = 6000


def build_system_prompt(agent: Agent, docs: list[KnowledgeDoc]) -> str:
    kb = _format_kb(docs)
    role = agent.system_prompt.strip() or "Помогать клиентам и доводить обращения до результата."
    lang = "русском" if agent.language == "ru" else agent.language
    parts = [
        f'Ты — ИИ-агент по имени «{agent.name}».',
        f"Описание: {agent.description}" if agent.description else "",
        f"Твоя роль и задача: {role}",
        f"Тон общения: {agent.tone}. Всегда отвечай на {lang} языке.",
        "",
        "Правила:",
        "1. Отвечай кратко, по делу и вежливо. Без воды.",
        "2. Опирайся только на факты из базы знаний ниже. Не выдумывай цены, "
        "наличие, характеристики и условия.",
        "3. Если нужных данных нет — честно скажи об этом и предложи помощь оператора.",
        "4. Веди клиента к целевому действию: заявка, заказ, запись, контакт.",
        f"5. Если клиент просит оператора/человека, агрессивен или поднимает "
        f"вопросы ({agent.escalation_keywords}) — добавь в самый конец ответа тег "
        f"{HUMAN_TAG}.",
    ]
    if kb:
        parts += ["", "=== БАЗА ЗНАНИЙ ===", kb, "=== КОНЕЦ БАЗЫ ЗНАНИЙ ==="]
    return "\n".join(p for p in parts if p != "")


def detect_escalation(reply: str, user_text: str, keywords: str) -> bool:
    if HUMAN_TAG.lower() in reply.lower():
        return True
    kws = [k.strip().lower() for k in keywords.split(",") if k.strip()]
    low = user_text.lower()
    return any(k in low for k in kws)


def strip_tag(reply: str) -> str:
    return reply.replace(HUMAN_TAG, "").strip()


def history_to_messages(history: list[Message], user_text: str) -> list[llm.Message]:
    out: list[llm.Message] = []
    for m in history[-_MAX_HISTORY:]:
        if m.role in ("user", "agent"):
            role = "assistant" if m.role == "agent" else "user"
            out.append({"role": role, "content": m.text})
    out.append({"role": "user", "content": user_text})
    return out


async def agent_reply(
    agent: Agent,
    docs: list[KnowledgeDoc],
    history: list[Message],
    user_text: str,
) -> tuple[str, bool]:
    system = build_system_prompt(agent, docs)
    messages = history_to_messages(history, user_text)
    raw = await llm.generate(
        system,
        messages,
        provider=agent.provider,
        model=agent.model,
        temperature=agent.temperature,
    )
    escalate = detect_escalation(raw, user_text, agent.escalation_keywords)
    reply = strip_tag(raw)
    if escalate and agent.fallback_message:
        reply = f"{reply}\n\n{agent.fallback_message}".strip()
    return reply, escalate


def _format_kb(docs: list[KnowledgeDoc]) -> str:
    chunks, total = [], 0
    for d in docs:
        block = f"# {d.title}\n{d.content}"
        if total + len(block) > _MAX_KB_CHARS:
            block = block[: _MAX_KB_CHARS - total]
        chunks.append(block)
        total += len(block)
        if total >= _MAX_KB_CHARS:
            break
    return "\n\n".join(chunks)
