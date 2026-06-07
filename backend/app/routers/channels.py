import json
import secrets

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy.orm import Session

from ..catalog import CHANNEL_BY_TYPE
from ..channels import enrich_channel_config, get_adapter, verify_channel
from ..database import get_db
from ..deps import get_current_user, get_owned_agent
from ..models import Agent, Channel, User
from ..schemas import ChannelIn, ChannelOut

router = APIRouter(prefix="/api", tags=["channels"])


def _owned_channel(channel_id: int, user: User, db: Session) -> Channel:
    ch = db.get(Channel, channel_id)
    if not ch:
        raise HTTPException(404, "Канал не найден")
    agent = db.get(Agent, ch.agent_id)
    if not agent or agent.owner_id != user.id:
        raise HTTPException(404, "Канал не найден")
    return ch


@router.get("/agents/{agent_id}/channels", response_model=list[ChannelOut])
def list_channels(agent: Agent = Depends(get_owned_agent)):
    return agent.channels


@router.post("/agents/{agent_id}/channels", status_code=201)
async def add_channel(
    data: ChannelIn,
    agent: Agent = Depends(get_owned_agent),
    db: Session = Depends(get_db),
):
    if data.type not in CHANNEL_BY_TYPE:
        raise HTTPException(400, f"Неизвестный тип канала: {data.type}")
    config = await enrich_channel_config(data.type, data.config)
    ok, msg = await verify_channel(data.type, config)
    ch = Channel(
        agent_id=agent.id,
        type=data.type,
        name=data.name or CHANNEL_BY_TYPE[data.type]["name"],
        status="connected" if ok else "error",
        public_key=secrets.token_urlsafe(16),
        config=json.dumps(config, ensure_ascii=False),
    )
    db.add(ch)
    db.commit()
    db.refresh(ch)
    return {
        "channel": ChannelOut.model_validate(ch),
        "ok": ok,
        "message": msg,
        "detected_user_id": config.get("user_id"),
    }


@router.get("/channels/{channel_id}")
def channel_detail(
    channel_id: int,
    request_base: str = "",
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    ch = _owned_channel(channel_id, user, db)
    return {
        "id": ch.id,
        "type": ch.type,
        "name": ch.name,
        "status": ch.status,
        "public_key": ch.public_key,
        "config": json.loads(ch.config or "{}"),
        "webhook_path": f"/api/webhooks/{ch.type}/{ch.public_key}",
        "widget_snippet": _widget_snippet(ch) if ch.type == "web" else None,
    }


@router.patch("/channels/{channel_id}")
async def update_channel(
    data: ChannelIn,
    channel_id: int,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    ch = _owned_channel(channel_id, user, db)
    if data.name:
        ch.name = data.name
    config = await enrich_channel_config(ch.type, data.config)
    ch.config = json.dumps(config, ensure_ascii=False)
    ok, msg = await verify_channel(ch.type, config)
    ch.status = "connected" if ok else "error"
    db.commit()
    return {
        "ok": ok,
        "message": msg,
        "status": ch.status,
        "detected_user_id": config.get("user_id"),
    }


@router.post("/channels/{channel_id}/verify")
async def verify(
    channel_id: int,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    ch = _owned_channel(channel_id, user, db)
    stored = json.loads(ch.config or "{}")
    config = await enrich_channel_config(ch.type, stored)
    if config != stored:  # backfill newly-detected values (e.g. Avito user_id)
        ch.config = json.dumps(config, ensure_ascii=False)
    ok, msg = await verify_channel(ch.type, config)
    ch.status = "connected" if ok else "error"
    db.commit()
    return {
        "ok": ok,
        "message": msg,
        "status": ch.status,
        "detected_user_id": config.get("user_id"),
    }


class WebhookUrlIn(BaseModel):
    url: str


@router.post("/channels/{channel_id}/register-webhook")
async def register_webhook(
    data: WebhookUrlIn,
    channel_id: int,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Register the channel's inbound webhook URL with the platform (e.g. Avito API)."""
    ch = _owned_channel(channel_id, user, db)
    adapter = get_adapter(ch.type)
    if not adapter or not hasattr(adapter, "subscribe_webhook"):
        raise HTTPException(400, "Авторегистрация webhook поддерживается только для Avito")
    config = json.loads(ch.config or "{}")
    ok, msg = await adapter.subscribe_webhook(config, data.url)
    if ok and ch.status != "connected":
        ch.status = "connected"
        db.commit()
    return {"ok": ok, "message": msg}


@router.delete("/channels/{channel_id}", status_code=204)
def delete_channel(
    channel_id: int,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    ch = _owned_channel(channel_id, user, db)
    db.delete(ch)
    db.commit()


def _widget_snippet(ch: Channel) -> str:
    return (
        '<script src="https://ВАШ-ДОМЕН/widget.js" '
        f'data-key="{ch.public_key}" defer></script>'
    )
