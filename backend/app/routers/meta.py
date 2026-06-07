from fastapi import APIRouter, Depends
from sqlalchemy import func
from sqlalchemy.orm import Session

from ..catalog import CHANNELS, TEMPLATES
from ..config import settings
from ..database import get_db
from ..deps import get_current_user
from ..models import Agent, Conversation, Message, User

router = APIRouter(prefix="/api", tags=["meta"])


@router.get("/catalog/templates")
def templates():
    return TEMPLATES


@router.get("/catalog/channels")
def channels():
    return CHANNELS


@router.get("/catalog/provider")
def provider():
    """Which LLM backend is active — surfaced in the UI so users know if they're
    in offline demo mode."""
    return {"provider": settings.resolved_provider}


@router.get("/stats")
def stats(user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    agent_ids = [a.id for a in db.query(Agent.id).filter(Agent.owner_id == user.id)]
    if not agent_ids:
        return {
            "agents": 0,
            "active": 0,
            "conversations": 0,
            "messages": 0,
            "needs_human": 0,
        }
    conv_q = db.query(Conversation).filter(Conversation.agent_id.in_(agent_ids))
    messages = (
        db.query(func.count(Message.id))
        .join(Conversation, Message.conversation_id == Conversation.id)
        .filter(Conversation.agent_id.in_(agent_ids))
        .scalar()
    )
    return {
        "agents": len(agent_ids),
        "active": db.query(Agent)
        .filter(Agent.owner_id == user.id, Agent.status == "active")
        .count(),
        "conversations": conv_q.count(),
        "messages": int(messages or 0),
        "needs_human": conv_q.filter(Conversation.status == "needs_human").count(),
    }
