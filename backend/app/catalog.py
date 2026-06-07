"""Static catalogs: agent templates gallery + channel/integration registry.

Exposed read-only via the API and used to pre-fill new agents.
"""

# ─── Agent templates (the gallery shown in the builder) ────────────────
TEMPLATES = [
    {
        "key": "sales_qualifier",
        "name": "Квалификатор лидов",
        "avatar": "🎯",
        "category": "Продажи",
        "tagline": "Задаёт правильные вопросы и отдаёт в CRM только горячих клиентов",
        "description": "Выявляет потребность, бюджет и сроки, квалифицирует заявку и "
        "передаёт менеджеру готового к покупке клиента.",
        "system_prompt": "Ты квалифицируешь входящие заявки. Выясни потребность, "
        "бюджет, сроки и контакт. Задавай по одному вопросу за раз. Когда данных "
        "достаточно — предложи звонок менеджера.",
        "tone": "деловой",
        "channels": ["web", "avito", "telegram"],
    },
    {
        "key": "support",
        "name": "Поддержка клиентов",
        "avatar": "🛟",
        "category": "Поддержка",
        "tagline": "Закрывает до 70% типовых вопросов без участия сотрудников",
        "description": "Отвечает на частые вопросы по заказам, оплате и доставке, "
        "работает 24/7 и эскалирует сложные случаи оператору.",
        "system_prompt": "Ты — служба поддержки. Помогай по статусам заказов, "
        "оплате, возвратам и доставке на основе базы знаний. Будь спокоен и точен.",
        "tone": "вежливый",
        "channels": ["web", "telegram", "whatsapp"],
    },
    {
        "key": "sales_manager",
        "name": "Менеджер по продажам",
        "avatar": "💼",
        "category": "Продажи",
        "tagline": "Отвечает за 5 секунд и доводит до сделки",
        "description": "Консультирует, обрабатывает возражения, предлагает товары и "
        "оформляет заказ. Заменяет менеджера на первой линии.",
        "system_prompt": "Ты — менеджер по продажам. Презентуй выгоды, отрабатывай "
        "возражения мягко, предлагай следующий шаг к покупке.",
        "tone": "энергичный",
        "channels": ["avito", "web", "instagram"],
    },
    {
        "key": "product_consultant",
        "name": "Консультант по товарам",
        "avatar": "🛍️",
        "category": "Продажи",
        "tagline": "Подбирает товар под задачу клиента",
        "description": "Помогает выбрать товар из каталога, сравнивает варианты и "
        "объясняет отличия простым языком.",
        "system_prompt": "Ты — товарный консультант. Подбирай позиции из базы "
        "знаний под запрос клиента, сравнивай и рекомендуй.",
        "tone": "дружелюбный",
        "channels": ["web", "avito", "instagram"],
    },
    {
        "key": "booking",
        "name": "Запись и бронирование",
        "avatar": "📅",
        "category": "Услуги",
        "tagline": "Записывает клиентов и напоминает о визитах",
        "description": "Принимает заявки на запись, предлагает свободные слоты и "
        "собирает контакты для подтверждения.",
        "system_prompt": "Ты администратор записи. Уточни услугу, удобную дату и "
        "время, имя и телефон. Подтверди запись.",
        "tone": "приветливый",
        "channels": ["web", "telegram", "instagram"],
    },
    {
        "key": "realestate",
        "name": "Агент по недвижимости",
        "avatar": "🏠",
        "category": "Отрасли",
        "tagline": "Квалифицирует и записывает на показ",
        "description": "Отвечает по объектам, выясняет параметры поиска и "
        "записывает на просмотр.",
        "system_prompt": "Ты — агент по недвижимости. Узнай бюджет, район, тип "
        "объекта и цель. Предлагай подходящие варианты и показ.",
        "tone": "деловой",
        "channels": ["avito", "web", "whatsapp"],
    },
    {
        "key": "auto",
        "name": "Автосалон",
        "avatar": "🚗",
        "category": "Отрасли",
        "tagline": "Продажа и аренда авто на автопилоте",
        "description": "Консультирует по наличию, комплектациям и условиям, "
        "записывает на тест-драйв.",
        "system_prompt": "Ты — консультант автосалона. Помогай с выбором модели, "
        "комплектации, trade-in и записью на тест-драйв.",
        "tone": "уверенный",
        "channels": ["avito", "web", "telegram"],
    },
    {
        "key": "beauty",
        "name": "Салон красоты",
        "avatar": "💅",
        "category": "Отрасли",
        "tagline": "Запись на услуги и ответы об услугах",
        "description": "Рассказывает об услугах и ценах, подбирает мастера и "
        "записывает клиента.",
        "system_prompt": "Ты — администратор салона красоты. Подскажи услуги, "
        "цены, мастеров и запиши клиента на удобное время.",
        "tone": "тёплый",
        "channels": ["instagram", "web", "telegram"],
    },
    {
        "key": "medical",
        "name": "Медклиника",
        "avatar": "🩺",
        "category": "Отрасли",
        "tagline": "Запись к врачу и ответы пациентам",
        "description": "Помогает выбрать специалиста, объясняет подготовку к "
        "приёму и записывает пациента.",
        "system_prompt": "Ты — администратор клиники. Помогай выбрать врача и "
        "услугу, записывай на приём. Не ставь диагнозы.",
        "tone": "заботливый",
        "channels": ["web", "whatsapp", "telegram"],
    },
    {
        "key": "hr",
        "name": "HR-рекрутер",
        "avatar": "🧑‍💼",
        "category": "Бизнес",
        "tagline": "Первичный отбор кандидатов",
        "description": "Проводит первичный скрининг, задаёт вопросы по вакансии и "
        "приглашает подходящих на интервью.",
        "system_prompt": "Ты — рекрутер. Расскажи о вакансии, задай отборочные "
        "вопросы и пригласи подходящих кандидатов на интервью.",
        "tone": "профессиональный",
        "channels": ["telegram", "web"],
    },
    {
        "key": "restaurant",
        "name": "Ресторан и доставка",
        "avatar": "🍽️",
        "category": "Отрасли",
        "tagline": "Приём заказов и бронь столов",
        "description": "Принимает заказы на доставку, бронирует столы и отвечает "
        "по меню.",
        "system_prompt": "Ты — администратор ресторана. Принимай заказы по меню из "
        "базы знаний, бронируй столы, уточняй адрес и время.",
        "tone": "гостеприимный",
        "channels": ["web", "instagram", "telegram"],
    },
    {
        "key": "custom",
        "name": "Свой агент с нуля",
        "avatar": "✨",
        "category": "Другое",
        "tagline": "Чистый лист — настройте под свою задачу",
        "description": "Пустой шаблон: задайте имя, роль, тон и подключите каналы "
        "самостоятельно.",
        "system_prompt": "",
        "tone": "дружелюбный",
        "channels": ["web"],
    },
]

TEMPLATE_BY_KEY = {t["key"]: t for t in TEMPLATES}


# ─── Channels / integrations ──────────────────────────────────────────
# status: "live"     — fully working in this build
#         "scaffold" — adapter + config wired, needs platform API credentials/approval
CHANNELS = [
    {
        "type": "web",
        "name": "Виджет на сайт",
        "icon": "🌐",
        "status": "live",
        "blurb": "Встраиваемый чат для любого сайта одной строкой кода.",
        "fields": [],
    },
    {
        "type": "avito",
        "name": "Avito",
        "icon": "🟢",
        "status": "live",
        "blurb": "Автоответы в мессенджере Авито через официальный API.",
        "fields": ["client_id", "client_secret", "user_id"],
    },
    {
        "type": "telegram",
        "name": "Telegram",
        "icon": "✈️",
        "status": "live",
        "blurb": "Бот Telegram: отвечает в личных сообщениях и группах.",
        "fields": ["bot_token"],
    },
    {
        "type": "whatsapp",
        "name": "WhatsApp",
        "icon": "💬",
        "status": "scaffold",
        "blurb": "WhatsApp Business Cloud API. Нужен токен Meta и номер.",
        "fields": ["phone_number_id", "access_token", "verify_token"],
    },
    {
        "type": "instagram",
        "name": "Instagram",
        "icon": "📸",
        "status": "scaffold",
        "blurb": "Direct и комментарии через Instagram Graph API (Meta).",
        "fields": ["ig_account_id", "access_token", "verify_token"],
    },
    {
        "type": "vk",
        "name": "ВКонтакте",
        "icon": "🅥",
        "status": "scaffold",
        "blurb": "Сообщения сообщества ВК через Callback API.",
        "fields": ["group_id", "access_token", "confirmation_token"],
    },
    {
        "type": "youtube",
        "name": "YouTube",
        "icon": "▶️",
        "status": "scaffold",
        "blurb": "Автоответы на комментарии через YouTube Data API v3.",
        "fields": ["api_key", "channel_id", "oauth_token"],
    },
    {
        "type": "tiktok",
        "name": "TikTok",
        "icon": "🎵",
        "status": "scaffold",
        "blurb": "Комментарии и сообщения через TikTok Business API.",
        "fields": ["client_key", "client_secret", "access_token"],
    },
]

CHANNEL_BY_TYPE = {c["type"]: c for c in CHANNELS}
