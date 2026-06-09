"""LLM abstraction with interchangeable providers + automatic fallback chain.

- anthropic : official SDK (Claude) — needs a key with credit
- openai    : any OpenAI-compatible /chat/completions endpoint — needs a key
- free      : keyless OpenAI-compatible endpoint (Pollinations) — no key, free
- demo      : deterministic offline responder (last-resort, never fails)

`generate()` tries the preferred provider, then falls through to `free`, then
`demo`, so a conversation always gets the best available answer and never crashes.
"""

import asyncio
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

    # Try the preferred provider first, then every other one in priority order.
    # So a newly-added OpenAI/Gemini key is used even if a dead Anthropic key is
    # still set (anthropic fails → openai → free → demo). demo never fails.
    priority = ["anthropic", "openai", "free", "demo"]
    chain = [resolved] + [p for p in priority if p != resolved]

    for p in chain:
        try:
            if p == "anthropic" and settings.anthropic_api_key:
                return await _anthropic(system, messages, model, temperature, max_tokens)
            if p == "openai" and settings.openai_api_key:
                return await _openai(system, messages, model, temperature, max_tokens)
            if p == "free":
                return await _free(system, messages, model, temperature, max_tokens)
            if p == "demo":
                return _demo(system, messages)
        except Exception as e:  # noqa: BLE001 — try the next provider in the chain
            log.warning("LLM provider '%s' failed (%s) — trying next", p, e)

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
    # Build the full URL explicitly — httpx drops the base_url path (e.g.
    # /v1beta/openai for Gemini) when the request path starts with "/".
    url = settings.openai_base_url.rstrip("/") + "/chat/completions"
    headers = {
        "Authorization": f"Bearer {settings.openai_api_key}",
        # Used by OpenRouter for attribution; harmless/ignored by OpenAI & Gemini.
        "HTTP-Referer": settings.openai_referer,
        "X-Title": settings.openai_title,
    }
    async with httpx.AsyncClient(timeout=60.0) as c:
        r = await c.post(url, json=payload, headers=headers)
        r.raise_for_status()
        return r.json()["choices"][0]["message"]["content"].strip()


async def _free(system, messages, model, temperature, max_tokens) -> str:
    """Keyless OpenAI-compatible endpoint (Pollinations). Retries transient
    rate-limit / network errors with backoff."""
    payload = {
        "model": model or settings.free_model,
        "messages": [{"role": "system", "content": system}, *messages],
        "max_tokens": max_tokens,
        "temperature": temperature,
        "seed": 1,
    }
    headers = {"Referer": settings.free_referer, "Content-Type": "application/json"}
    last = "free provider failed"
    async with httpx.AsyncClient(timeout=60.0) as c:
        for attempt in range(4):
            try:
                r = await c.post(settings.free_base_url, json=payload, headers=headers)
                if r.status_code == 200:
                    return r.json()["choices"][0]["message"]["content"].strip()
                last = f"HTTP {r.status_code}: {r.text[:120]}"
                if r.status_code not in (429, 500, 502, 503, 504):
                    break
            except httpx.HTTPError as e:
                last = f"{type(e).__name__}: {e}"
            await asyncio.sleep(1.5 * (attempt + 1))
    raise RuntimeError(last)


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
    """Probe each available provider individually (no fallback masking) plus the
    effective reply generate() would return. Used by /api/diag/llm."""
    info: dict = {
        "resolved_provider": settings.resolved_provider,
        "anthropic_key_set": bool(settings.anthropic_api_key),
        "anthropic_model": settings.anthropic_model,
        "openai_key_set": bool(settings.openai_api_key),
        "free_model": settings.free_model,
        "providers": {},
    }
    test_msgs = [{"role": "user", "content": "Ответь одним словом: OK"}]

    async def _probe(name: str, coro) -> None:
        try:
            txt = await coro
            info["providers"][name] = {"ok": True, "reply": txt[:160]}
        except Exception as e:  # noqa: BLE001
            info["providers"][name] = {"ok": False, "error": f"{type(e).__name__}: {e}"}

    if settings.anthropic_api_key:
        await _probe("anthropic", _anthropic("Ты тест.", test_msgs, "", 0.0, 16))
    if settings.openai_api_key:
        await _probe("openai", _openai("Ты тест.", test_msgs, "", 0.0, 16))
    await _probe("free", _free("Ты тест.", test_msgs, "", 0.3, 32))

    info["effective_reply"] = await generate(
        "Ты — менеджер по продажам. Отвечай по-русски.", test_msgs,
        temperature=0.3, max_tokens=40,
    )
    info["ok"] = any(p.get("ok") for p in info["providers"].values())
    return info
