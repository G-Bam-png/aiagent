import json
import secrets

from sqlalchemy.orm import Session

from .models import Agent, Channel, KnowledgeDoc, User
from .security import hash_password

DEMO_EMAIL = "demo@nexus.ai"
DEMO_PASSWORD = "demo12345"


def seed_demo(db: Session) -> None:
    if db.query(User).filter(User.email == DEMO_EMAIL).first():
        return

    user = User(
        email=DEMO_EMAIL,
        name="Демо-аккаунт",
        password_hash=hash_password(DEMO_PASSWORD),
    )
    db.add(user)
    db.commit()
    db.refresh(user)

    agent = Agent(
        owner_id=user.id,
        name="Алиса — отдел продаж",
        description="ИИ-менеджер интернет-магазина электроники. Консультирует и доводит до заказа.",
        template_key="sales_manager",
        avatar="💼",
        system_prompt=(
            "Ты — менеджер по продажам интернет-магазина электроники «ТехноМир». "
            "Консультируй по товарам из базы знаний, предлагай выгоды, мягко веди к заказу. "
            "Если спрашивают то, чего нет в базе — честно скажи и предложи помощь оператора."
        ),
        tone="энергичный",
        greeting="Здравствуйте! 👋 Я Алиса из ТехноМир. Помогу выбрать технику и оформить заказ. Что ищете?",
        status="active",
    )
    db.add(agent)
    db.commit()
    db.refresh(agent)

    db.add(
        KnowledgeDoc(
            agent_id=agent.id,
            title="Каталог и цены",
            content=(
                "Ноутбук Lumix Air 14: 79 990 ₽, 16 ГБ RAM, 512 ГБ SSD, в наличии.\n"
                "Смартфон Nova X5: 49 990 ₽, 256 ГБ, 3 цвета, в наличии.\n"
                "Наушники SoundPro 2: 12 990 ₽, ANC, до 30 ч работы.\n"
                "Доставка по РФ: СДЭК 1-3 дня, бесплатно от 50 000 ₽. Самовывоз — Москва, "
                "ул. Тверская 1. Гарантия 24 месяца. Оплата: карта, СБП, рассрочка 0%."
            ),
        )
    )
    db.add(
        Channel(
            agent_id=agent.id,
            type="web",
            name="Виджет на сайте",
            status="connected",
            public_key=secrets.token_urlsafe(16),
            config=json.dumps({}, ensure_ascii=False),
        )
    )
    db.commit()
