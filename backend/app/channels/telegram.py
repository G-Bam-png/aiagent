import httpx

from .base import ChannelAdapter

_API = "https://api.telegram.org"


class TelegramAdapter(ChannelAdapter):
    type = "telegram"
    live = True

    async def send(self, config: dict, external_id: str, text: str) -> None:
        token = config.get("bot_token")
        if not token:
            raise ValueError("bot_token не задан")
        async with httpx.AsyncClient(base_url=_API, timeout=30.0) as c:
            r = await c.post(
                f"/bot{token}/sendMessage",
                json={"chat_id": external_id, "text": text},
            )
            r.raise_for_status()

    async def verify(self, config: dict) -> tuple[bool, str]:
        token = config.get("bot_token")
        if not token:
            return False, "Укажите bot_token (получите у @BotFather)"
        try:
            async with httpx.AsyncClient(base_url=_API, timeout=15.0) as c:
                r = await c.get(f"/bot{token}/getMe")
                r.raise_for_status()
                bot = r.json()["result"]
            return True, f"Подключён бот @{bot.get('username', '?')}"
        except Exception as e:  # noqa: BLE001
            return False, f"Не удалось подключиться: {e}"
