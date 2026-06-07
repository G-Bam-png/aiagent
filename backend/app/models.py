from datetime import datetime, timezone

from sqlalchemy import (
    DateTime,
    Float,
    ForeignKey,
    Integer,
    String,
    Text,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from .database import Base


def _now() -> datetime:
    return datetime.now(timezone.utc)


class User(Base):
    __tablename__ = "users"

    id: Mapped[int] = mapped_column(primary_key=True)
    email: Mapped[str] = mapped_column(String(255), unique=True, index=True)
    name: Mapped[str] = mapped_column(String(120), default="")
    password_hash: Mapped[str] = mapped_column(String(255))
    created_at: Mapped[datetime] = mapped_column(DateTime, default=_now)

    agents: Mapped[list["Agent"]] = relationship(
        back_populates="owner", cascade="all, delete-orphan"
    )


class Agent(Base):
    __tablename__ = "agents"

    id: Mapped[int] = mapped_column(primary_key=True)
    owner_id: Mapped[int] = mapped_column(ForeignKey("users.id"), index=True)
    name: Mapped[str] = mapped_column(String(120))
    description: Mapped[str] = mapped_column(String(500), default="")
    template_key: Mapped[str] = mapped_column(String(60), default="custom")
    avatar: Mapped[str] = mapped_column(String(20), default="🤖")

    system_prompt: Mapped[str] = mapped_column(Text, default="")
    tone: Mapped[str] = mapped_column(String(40), default="дружелюбный")
    language: Mapped[str] = mapped_column(String(20), default="ru")
    greeting: Mapped[str] = mapped_column(Text, default="")
    fallback_message: Mapped[str] = mapped_column(
        Text, default="Секунду, передаю ваш вопрос специалисту."
    )
    escalation_keywords: Mapped[str] = mapped_column(
        String(500), default="оператор,человек,жалоба,юрист,суд"
    )

    provider: Mapped[str] = mapped_column(String(20), default="auto")
    model: Mapped[str] = mapped_column(String(80), default="")
    temperature: Mapped[float] = mapped_column(Float, default=0.4)
    status: Mapped[str] = mapped_column(String(20), default="draft")  # draft|active|paused

    created_at: Mapped[datetime] = mapped_column(DateTime, default=_now)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=_now, onupdate=_now)

    owner: Mapped["User"] = relationship(back_populates="agents")
    docs: Mapped[list["KnowledgeDoc"]] = relationship(
        back_populates="agent", cascade="all, delete-orphan"
    )
    channels: Mapped[list["Channel"]] = relationship(
        back_populates="agent", cascade="all, delete-orphan"
    )
    conversations: Mapped[list["Conversation"]] = relationship(
        back_populates="agent", cascade="all, delete-orphan"
    )


class KnowledgeDoc(Base):
    __tablename__ = "knowledge_docs"

    id: Mapped[int] = mapped_column(primary_key=True)
    agent_id: Mapped[int] = mapped_column(ForeignKey("agents.id"), index=True)
    title: Mapped[str] = mapped_column(String(200))
    content: Mapped[str] = mapped_column(Text)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=_now)

    agent: Mapped["Agent"] = relationship(back_populates="docs")


class Channel(Base):
    __tablename__ = "channels"

    id: Mapped[int] = mapped_column(primary_key=True)
    agent_id: Mapped[int] = mapped_column(ForeignKey("agents.id"), index=True)
    type: Mapped[str] = mapped_column(String(30))  # avito|telegram|web|instagram|...
    name: Mapped[str] = mapped_column(String(120), default="")
    status: Mapped[str] = mapped_column(String(20), default="disconnected")
    public_key: Mapped[str] = mapped_column(String(40), unique=True, index=True)
    config: Mapped[str] = mapped_column(Text, default="{}")  # JSON credentials/settings
    created_at: Mapped[datetime] = mapped_column(DateTime, default=_now)

    agent: Mapped["Agent"] = relationship(back_populates="channels")


class Conversation(Base):
    __tablename__ = "conversations"

    id: Mapped[int] = mapped_column(primary_key=True)
    agent_id: Mapped[int] = mapped_column(ForeignKey("agents.id"), index=True)
    channel_id: Mapped[int | None] = mapped_column(
        ForeignKey("channels.id"), nullable=True
    )
    external_id: Mapped[str] = mapped_column(String(120), default="", index=True)
    contact: Mapped[str] = mapped_column(String(120), default="Гость")
    status: Mapped[str] = mapped_column(String(20), default="open")  # open|needs_human|closed
    created_at: Mapped[datetime] = mapped_column(DateTime, default=_now)
    last_message_at: Mapped[datetime] = mapped_column(DateTime, default=_now)

    agent: Mapped["Agent"] = relationship(back_populates="conversations")
    messages: Mapped[list["Message"]] = relationship(
        back_populates="conversation",
        cascade="all, delete-orphan",
        order_by="Message.id",
    )


class Message(Base):
    __tablename__ = "messages"

    id: Mapped[int] = mapped_column(primary_key=True)
    conversation_id: Mapped[int] = mapped_column(
        ForeignKey("conversations.id"), index=True
    )
    role: Mapped[str] = mapped_column(String(20))  # user|agent|human|system
    text: Mapped[str] = mapped_column(Text)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=_now)

    conversation: Mapped["Conversation"] = relationship(back_populates="messages")
