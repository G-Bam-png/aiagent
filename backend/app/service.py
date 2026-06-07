"""Conversation orchestration shared by the playground and every public channel."""

from datetime import datetime, timezone

from sqlalchemy.orm import Session

from . import runtime
from .models import Agent, Channel, Conversation, Message


def get_or_create_conversation(
    db: Session,
    agent: Agent,
    *,
    channel: Channel | None,
    external_id: str,
    contact: str,
) -> Conversation:
    q = db.query(Conversation).filter(Conversation.agent_id == agent.id)
    if channel is not None:
        q = q.filter(Conversation.channel_id == channel.id)
    if external_id:
        q = q.filter(Conversation.external_id == external_id)
    conv = q.order_by(Conversation.id.desc()).first()
    if conv:
        return conv
    conv = Conversation(
        agent_id=agent.id,
        channel_id=channel.id if channel else None,
        external_id=external_id,
        contact=contact,
    )
    db.add(conv)
    db.commit()
    db.refresh(conv)
    return conv


async def process_message(
    db: Session,
    agent: Agent,
    conversation: Conversation,
    text: str,
) -> tuple[str, bool]:
    """Run the agent on `text`, persist both turns, return (reply, needs_human)."""
    docs = list(agent.docs)
    history = list(conversation.messages)  # snapshot before appending the new turn

    reply, escalate = await runtime.agent_reply(agent, docs, history, text)

    now = datetime.now(timezone.utc)
    db.add(Message(conversation_id=conversation.id, role="user", text=text))
    db.add(Message(conversation_id=conversation.id, role="agent", text=reply))
    conversation.last_message_at = now
    conversation.status = "needs_human" if escalate else "open"
    db.commit()
    return reply, escalate
