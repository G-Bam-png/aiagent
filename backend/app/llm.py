"""LLM abstraction with three interchangeable providers.

- anthropic : official SDK (Claude)
- openai    : any OpenAI-compatible /chat/completions endpoint
- demo      : deterministic offline responder (no API key needed)

The provider is resolved per call: an agent may pin a provider, otherwise the
platform default (settings.resolved_provider) is used.
"""

import logging

import httpx

from .config import settings

log = logging.getLogger("llm")

Message = dict[str, str]  # {"role": "user"|"assistant", "content": str}


async def generate(
    system: str,
    messages: list[Message],
    *,
    provider: str = "auto",
    model: str = "",
    temperature: float = 0.4,
    max_tokens: int | None = None,
) -> str:
    resolved = settings.resolved_provider if provider in ("", "auto") else provider
    max_tokens = max_tokens or settings.llm_max_tokens

    try:
        if resolved == "anthropic" and settings.anthropic_api_key:
            return await _anthropic(system, messages, model, temperature, max_tokens)
        if resolved == "openai" and settings.openai_api_key:
            return await _openai(system, messages, model, temperature, max_tokens)
    except Exception:  # noqa: BLE001 — never crash a conversation on provider error
        log.exception("LLM provider '%s' failed — falling back to demo", resolved)

    return _demo(system, messages)


async def _anthropic(system, messages, model, temperature, max_tokens) -> str:
    from anthropic import AsyncAnthropic

    client = AsyncAnthropic(api_key=settings.anthropic_api_key)
    resp = await client.messages.create(
        model=model or settings.anthropic_model,
        max_tokens=max_tokens,
        temperature=temperature,
        system=system,
        messages=messages,
    )
    return resp.content[0].text.strip()


async def _openai(system, messages, model, temperature, max_tokens) -> str:
    payload = {
        "model": model or settings.openai_model,
        "max_tokens": max_tokens,
        "temperature": temperature,
        "messages": [{"role": "system", "content": system}, *messages],
    }
    headers = {"Authorization": f"Bearer {settings.openai_api_key}"}
    async with httpx.AsyncClient(base_url=settings.openai_base_url, timeout=60.0) as c:
        r = await c.post("/chat/completions", json=payload, headers=headers)
        r.raise_for_status()
        return r.json()["choices"][0]["message"]["content"].strip()


def _demo(system: str, messages: list[Message]) -> str:
    """Offline responder — plausible Russian replies grounded in the last message."""
    last = next(
        (m["content"] for m in reversed(messages) if m["role"] == "user"), ""
    ).lower()

    if any(w in last for w in ("привет", "здравств", "добрый", "доброе", "hello")):
        return (
            "Здравствуйте! 👋 Я ИИ-ассистент. Подскажу по товарам, услугам и условиям — "
            "что вас интересует?"
        )
    if any(w in last for w in ("цена", "стоит", "стоимость", "сколько", "прайс", "почём")):
        return (
            "Стоимость зависит от выбранной конфигурации. Уточните, пожалуйста, что именно "
            "вас интересует — и я назову точную цену и доступные варианты."
        )
    if any(w in last for w in ("достав", "отправ", "самовывоз", "курьер")):
        return (
            "Доставка возможна по всей России, есть самовывоз и курьер. Назовите ваш город — "
            "рассчитаю сроки и стоимость."
        )
    if "?" in last:
        return (
            "Отличный вопрос! Чтобы ответить максимально точно, уточните пару деталей — "
            "и я сразу всё подскажу."
        )
    if last:
        return (
            "Понял вас. Подскажите, пожалуйста, чуть подробнее — что важно учесть, "
            "и я помогу подобрать лучшее решение."
        )
    return "Здравствуйте! Чем могу помочь?"


async def diagnostic() -> dict:
    """Test the configured provider WITHOUT the demo fallback, surfacing the real
    error. Used by the /api/diag/llm endpoint to debug why replies are demo-only."""
    resolved = settings.resolved_provider
    info: dict = {
        "resolved_provider": resolved,
        "anthropic_key_set": bool(settings.anthropic_api_key),
        "anthropic_model": settings.anthropic_model,
        "openai_key_set": bool(settings.openai_api_key),
    }
    test_msgs = [{"role": "user", "content": "Ответь одним словом: OK"}]
    try:
        if resolved == "anthropic" and settings.anthropic_api_key:
            info["reply"] = await _anthropic("Ты тест.", test_msgs, "", 0.0, 16)
        elif resolved == "openai" and settings.openai_api_key:
            info["reply"] = await _openai("Ты тест.", test_msgs, "", 0.0, 16)
        else:
            info["reply"] = _demo("", test_msgs)
        info["ok"] = True
    except Exception as e:  # noqa: BLE001
        info["ok"] = False
        info["error"] = f"{type(e).__name__}: {e}"
    return info
