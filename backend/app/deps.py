from fastapi import Depends, Header, HTTPException
from sqlalchemy.orm import Session

from .database import get_db
from .models import Agent, User
from .security import decode_token


def get_current_user(
    authorization: str | None = Header(default=None),
    db: Session = Depends(get_db),
) -> User:
    if not authorization or not authorization.lower().startswith("bearer "):
        raise HTTPException(401, "Требуется авторизация")
    payload = decode_token(authorization.split(" ", 1)[1])
    if not payload:
        raise HTTPException(401, "Недействительный или истёкший токен")
    user = db.get(User, int(payload["sub"]))
    if not user:
        raise HTTPException(401, "Пользователь не найден")
    return user


def get_owned_agent(
    agent_id: int,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> Agent:
    agent = db.get(Agent, agent_id)
    if not agent or agent.owner_id != user.id:
        raise HTTPException(404, "Агент не найден")
    return agent
