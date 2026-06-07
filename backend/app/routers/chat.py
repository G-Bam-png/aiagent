"""Public, unauthenticated endpoints: website widget + inbound channel webhooks.

Every conversation is keyed by a channel's `public_key`, so no auth is needed —
the key is the secret.
"""

import json
import logging

from fastapi import APIRouter, BackgroundTasks, Depends, HTTPException, Request
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session

from .. import service
from ..channels import get_adapter
from ..database import SessionLocal, get_db
from ..models import Channel

log = logging.getLogger("chat")
router = APIRouter(prefix="/api", tags=["public"])


class WidgetIn(BaseModel):
    message: str = Field(min_length=1)
    session_id: str = Field(min_length=1, max_length=120)


def _channel_by_key(db: Session, public_key: str) -> Channel:
    ch = db.query(Channel).filter(Channel.public_key == public_key).first()
    if not ch:
        raise HTTPException(404, "Канал не найден")
    return ch


# ─── Website widget ────────────────────────────────────
@router.get("/public/agent/{public_key}")
def widget_agent_info(public_key: str, db: Session = Depends(get_db)):
    ch = _channel_by_key(db, public_key)
    agent = ch.agent
    return {
        "name": agent.name,
        "avatar": agent.avatar,
        "greeting": agent.greeting or f"Здравствуйте! Я {agent.name}. Чем помочь?",
    }


@router.post("/public/chat/{public_key}")
async def widget_chat(
    public_key: str, data: WidgetIn, db: Session = Depends(get_db)
):
    ch = _channel_by_key(db, public_key)
    conv = service.get_or_create_conversation(
        db, ch.agent, channel=ch, external_id=data.session_id, contact="Посетитель сайта"
    )
    reply, needs_human = await service.process_message(db, ch.agent, conv, data.message)
    return {"reply": reply, "needs_human": needs_human}


# ─── Inbound webhooks ──────────────────────────────────
@router.get("/webhooks/{ctype}/{public_key}")
async def webhook_challenge(ctype: str, public_key: str, request: Request):
    """Meta (Instagram/WhatsApp) verification handshake: echo hub.challenge."""
    challenge = request.query_params.get("hub.challenge")
    if challenge:
        return int(challenge) if challenge.isdigit() else challenge
    return {"ok": True}


@router.post("/webhooks/{ctype}/{public_key}")
async def webhook(
    ctype: str,
    public_key: str,
    request: Request,
    background: BackgroundTasks,
    db: Session = Depends(get_db),
):
    ch = _channel_by_key(db, public_key)
    if ch.type != ctype:
        raise HTTPException(400, "Тип канала не совпадает")
    body = await request.json()
    config = json.loads(ch.config or "{}")

    parsed = _parse_inbound(ctype, body, config)
    if parsed is None:
        return _maybe_confirm(ctype, body, config)
    if not parsed.get("text"):
        return {"status": "skipped_no_text"}

    # Generate the reply and deliver it in the background so we return 200 fast —
    # Avito (and others) require the webhook to respond within ~2 seconds.
    background.add_task(
        _process_inbound,
        ch.id,
        ctype,
        parsed["external_id"],
        parsed.get("contact", "Гость"),
        parsed["text"],
    )
    return {"status": "accepted"}


async def _process_inbound(
    channel_id: int, ctype: str, external_id: str, contact: str, text: str
) -> None:
    """Reply + outbound send, run after the webhook 200 response.

    Opens its own DB session because the request-scoped one is already closed
    by the time a background task runs.
    """
    db = SessionLocal()
    try:
        ch = db.get(Channel, channel_id)
        if not ch:
            return
        config = json.loads(ch.config or "{}")
        conv = service.get_or_create_conversation(
            db, ch.agent, channel=ch, external_id=external_id, contact=contact
        )
        reply, _ = await service.process_message(db, ch.agent, conv, text)
        adapter = get_adapter(ctype)
        if adapter:
            await adapter.send(config, external_id, reply)
    except Exception:  # noqa: BLE001
        log.exception("Background inbound processing failed (%s)", ctype)
    finally:
        db.close()


def _parse_inbound(ctype: str, body: dict, config: dict) -> dict | None:
    if ctype == "telegram":
        msg = body.get("message") or body.get("edited_message")
        if not msg:
            return None
        chat = msg.get("chat", {})
        return {
            "external_id": str(chat.get("id")),
            "text": msg.get("text", ""),
            "contact": chat.get("first_name") or chat.get("username") or "Telegram",
        }

    if ctype == "avito":
        payload = body.get("payload", body)
        value = payload.get("value", payload)
        author = value.get("author_id")
        if author is not None and str(author) == str(config.get("user_id")):
            return {"external_id": "", "text": ""}  # our own echo
        content = value.get("content", {})
        return {
            "external_id": str(value.get("chat_id", "")),
            "text": content.get("text", ""),
            "contact": "Покупатель Avito",
        }

    # Scaffolded channels: accept a generic shape if present, else signal "confirm".
    if "external_id" in body and "text" in body:
        return {
            "external_id": str(body["external_id"]),
            "text": body.get("text", ""),
            "contact": body.get("contact", "Гость"),
        }
    return None


def _maybe_confirm(ctype: str, body: dict, config: dict):
    # VK Callback API confirmation handshake
    if ctype == "vk" and body.get("type") == "confirmation":
        return config.get("confirmation_token", "ok")
    return {"status": "ignored"}
