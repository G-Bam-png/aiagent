from datetime import datetime

from pydantic import BaseModel, ConfigDict, EmailStr, Field


# ─── Auth ──────────────────────────────────────────────
class RegisterIn(BaseModel):
    email: EmailStr
    password: str = Field(min_length=6, max_length=200)
    name: str = ""


class LoginIn(BaseModel):
    email: EmailStr
    password: str


class TokenOut(BaseModel):
    token: str
    user: "UserOut"


class UserOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: int
    email: str
    name: str


# ─── Agents ────────────────────────────────────────────
class AgentIn(BaseModel):
    name: str = Field(min_length=1, max_length=120)
    description: str = ""
    template_key: str = "custom"
    avatar: str = "🤖"
    system_prompt: str = ""
    tone: str = "дружелюбный"
    language: str = "ru"
    greeting: str = ""
    fallback_message: str = "Секунду, передаю ваш вопрос специалисту."
    escalation_keywords: str = "оператор,человек,жалоба,юрист,суд"
    provider: str = "auto"
    model: str = ""
    temperature: float = Field(default=0.4, ge=0.0, le=1.0)
    status: str = "draft"


class AgentUpdate(BaseModel):
    name: str | None = None
    description: str | None = None
    avatar: str | None = None
    system_prompt: str | None = None
    tone: str | None = None
    language: str | None = None
    greeting: str | None = None
    fallback_message: str | None = None
    escalation_keywords: str | None = None
    provider: str | None = None
    model: str | None = None
    temperature: float | None = Field(default=None, ge=0.0, le=1.0)
    status: str | None = None


class AgentOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: int
    name: str
    description: str
    template_key: str
    avatar: str
    system_prompt: str
    tone: str
    language: str
    greeting: str
    fallback_message: str
    escalation_keywords: str
    provider: str
    model: str
    temperature: float
    status: str
    created_at: datetime
    updated_at: datetime


# ─── Knowledge base ────────────────────────────────────
class DocIn(BaseModel):
    title: str = Field(min_length=1, max_length=200)
    content: str = Field(min_length=1)


class DocOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: int
    title: str
    content: str
    created_at: datetime


# ─── Channels ──────────────────────────────────────────
class ChannelIn(BaseModel):
    type: str
    name: str = ""
    config: dict = {}


class ChannelOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: int
    type: str
    name: str
    status: str
    public_key: str
    created_at: datetime


# ─── Chat / playground ─────────────────────────────────
class ChatIn(BaseModel):
    message: str = Field(min_length=1)
    conversation_id: int | None = None


class ChatOut(BaseModel):
    reply: str
    conversation_id: int
    needs_human: bool


class MessageOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: int
    role: str
    text: str
    created_at: datetime


class ConversationOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: int
    contact: str
    status: str
    external_id: str
    last_message_at: datetime
    channel_id: int | None


TokenOut.model_rebuild()
