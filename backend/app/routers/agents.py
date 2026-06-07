from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from .. import service
from ..catalog import TEMPLATE_BY_KEY
from ..database import get_db
from ..deps import get_current_user, get_owned_agent
from ..models import Agent, Conversation, KnowledgeDoc, Message, User
from ..schemas import (
    AgentIn,
    AgentOut,
    AgentUpdate,
    ChatIn,
    ChatOut,
    ConversationOut,
    DocIn,
    DocOut,
    MessageOut,
)

router = APIRouter(prefix="/api/agents", tags=["agents"])


# ─── CRUD ──────────────────────────────────────────────
@router.get("", response_model=list[AgentOut])
def list_agents(user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    return (
        db.query(Agent)
        .filter(Agent.owner_id == user.id)
        .order_by(Agent.id.desc())
        .all()
    )


@router.post("", response_model=AgentOut, status_code=201)
def create_agent(
    data: AgentIn, user: User = Depends(get_current_user), db: Session = Depends(get_db)
):
    payload = data.model_dump()
    tpl = TEMPLATE_BY_KEY.get(payload.get("template_key", ""))
    if tpl:  # fill blanks from the chosen template
        payload.setdefault("avatar", tpl["avatar"])
        if not payload.get("system_prompt"):
            payload["system_prompt"] = tpl["system_prompt"]
        if not payload.get("description"):
            payload["description"] = tpl["description"]
        if payload.get("avatar") in ("", "🤖"):
            payload["avatar"] = tpl["avatar"]
    agent = Agent(owner_id=user.id, **payload)
    db.add(agent)
    db.commit()
    db.refresh(agent)
    return agent


@router.get("/{agent_id}", response_model=AgentOut)
def get_agent(agent: Agent = Depends(get_owned_agent)):
    return agent


@router.patch("/{agent_id}", response_model=AgentOut)
def update_agent(
    data: AgentUpdate,
    agent: Agent = Depends(get_owned_agent),
    db: Session = Depends(get_db),
):
    for k, v in data.model_dump(exclude_unset=True).items():
        setattr(agent, k, v)
    db.commit()
    db.refresh(agent)
    return agent


@router.delete("/{agent_id}", status_code=204)
def delete_agent(agent: Agent = Depends(get_owned_agent), db: Session = Depends(get_db)):
    db.delete(agent)
    db.commit()


# ─── Knowledge base ────────────────────────────────────
@router.get("/{agent_id}/docs", response_model=list[DocOut])
def list_docs(agent: Agent = Depends(get_owned_agent)):
    return agent.docs


@router.post("/{agent_id}/docs", response_model=DocOut, status_code=201)
def add_doc(
    data: DocIn,
    agent: Agent = Depends(get_owned_agent),
    db: Session = Depends(get_db),
):
    doc = KnowledgeDoc(agent_id=agent.id, title=data.title, content=data.content)
    db.add(doc)
    db.commit()
    db.refresh(doc)
    return doc


@router.delete("/{agent_id}/docs/{doc_id}", status_code=204)
def delete_doc(
    doc_id: int,
    agent: Agent = Depends(get_owned_agent),
    db: Session = Depends(get_db),
):
    doc = db.get(KnowledgeDoc, doc_id)
    if not doc or doc.agent_id != agent.id:
        raise HTTPException(404, "Документ не найден")
    db.delete(doc)
    db.commit()


# ─── Playground (test chat) ────────────────────────────
@router.post("/{agent_id}/playground", response_model=ChatOut)
async def playground(
    data: ChatIn,
    agent: Agent = Depends(get_owned_agent),
    db: Session = Depends(get_db),
):
    conv = service.get_or_create_conversation(
        db, agent, channel=None, external_id="playground", contact="Тест"
    )
    reply, needs_human = await service.process_message(db, agent, conv, data.message)
    return ChatOut(reply=reply, conversation_id=conv.id, needs_human=needs_human)


@router.post("/{agent_id}/playground/reset", status_code=204)
def reset_playground(
    agent: Agent = Depends(get_owned_agent), db: Session = Depends(get_db)
):
    convs = (
        db.query(Conversation)
        .filter(Conversation.agent_id == agent.id, Conversation.external_id == "playground")
        .all()
    )
    for c in convs:
        db.delete(c)
    db.commit()


# ─── Conversations (inbox) ─────────────────────────────
@router.get("/{agent_id}/conversations", response_model=list[ConversationOut])
def list_conversations(
    agent: Agent = Depends(get_owned_agent), db: Session = Depends(get_db)
):
    return (
        db.query(Conversation)
        .filter(Conversation.agent_id == agent.id)
        .order_by(Conversation.last_message_at.desc())
        .limit(100)
        .all()
    )


@router.get("/{agent_id}/conversations/{conv_id}/messages", response_model=list[MessageOut])
def conversation_messages(
    conv_id: int,
    agent: Agent = Depends(get_owned_agent),
    db: Session = Depends(get_db),
):
    conv = db.get(Conversation, conv_id)
    if not conv or conv.agent_id != agent.id:
        raise HTTPException(404, "Диалог не найден")
    return (
        db.query(Message)
        .filter(Message.conversation_id == conv_id)
        .order_by(Message.id)
        .all()
    )
