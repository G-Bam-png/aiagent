import logging
import time

import httpx

from ..config import settings
from .base import ChannelAdapter

log = logging.getLogger("channels.avito")


class AvitoAdapter(ChannelAdapter):
    type = "avito"
    live = True

    def __init__(self) -> None:
        self._cache: dict[str, tuple[str, float]] = {}  # client_id -> (token, expiry)

    async def _token(self, config: dict) -> str:
        cid = config.get("client_id")
        secret = config.get("client_secret")
        if not (cid and secret):
            raise ValueError("client_id / client_secret не заданы")
        cached = self._cache.get(cid)
        if cached and cached[1] > time.time() + 60:
            return cached[0]
        async with httpx.AsyncClient(base_url=settings.avito_api_base, timeout=30.0) as c:
            r = await c.post(
                "/token",
                data={
                    "grant_type": "client_credentials",
                    "client_id": cid,
                    "client_secret": secret,
                },
            )
            r.raise_for_status()
            data = r.json()
        token = data.get("access_token")
        if not token:
            raise ValueError(
                data.get("error_description") or data.get("error") or "ответ Avito без access_token"
            )
        self._cache[cid] = (token, time.time() + data.get("expires_in", 3600))
        return token

    async def get_self(self, config: dict) -> dict:
        """GET /core/v1/accounts/self — returns the account profile incl. its id."""
        token = await self._token(config)
        async with httpx.AsyncClient(base_url=settings.avito_api_base, timeout=30.0) as c:
            r = await c.get(
                "/core/v1/accounts/self",
                headers={"Authorization": f"Bearer {token}"},
            )
            r.raise_for_status()
            return r.json()

    async def enrich_config(self, config: dict) -> dict:
        """Auto-fill user_id from the account profile when only client creds given."""
        if config.get("user_id"):
            return config
        if not (config.get("client_id") and config.get("client_secret")):
            return config
        try:
            uid = (await self.get_self(config)).get("id")
            if uid:
                log.info("Avito user_id auto-detected: %s", uid)
                return {**config, "user_id": str(uid)}
        except Exception as e:  # noqa: BLE001
            log.info("Avito user_id auto-detect failed: %s", e)
        return config

    async def send(self, config: dict, external_id: str, text: str) -> None:
        token = await self._token(config)
        uid = config.get("user_id")
        async with httpx.AsyncClient(base_url=settings.avito_api_base, timeout=30.0) as c:
            r = await c.post(
                f"/messenger/v1/accounts/{uid}/chats/{external_id}/messages",
                json={"message": {"text": text}, "type": "text"},
                headers={"Authorization": f"Bearer {token}"},
            )
            r.raise_for_status()

    async def verify(self, config: dict) -> tuple[bool, str]:
        try:
            await self._token(config)
        except Exception as e:  # noqa: BLE001
            return False, f"Ошибка авторизации Avito: {e}"
        if not config.get("user_id"):
            return False, (
                "Ключи верны, но не удалось определить User ID — добавьте право "
                "user:read приложению или впишите User ID вручную"
            )
        return True, f"Avito подключён (User ID: {config['user_id']})"

    async def subscribe_webhook(self, config: dict, url: str) -> tuple[bool, str]:
        """Register an inbound webhook URL with Avito (POST /messenger/v3/webhook).

        Avito has no UI field for this — the URL must be registered via the API.
        """
        try:
            token = await self._token(config)
        except Exception as e:  # noqa: BLE001
            return False, f"Ошибка авторизации Avito: {e}"
        try:
            async with httpx.AsyncClient(base_url=settings.avito_api_base, timeout=30.0) as c:
                r = await c.post(
                    "/messenger/v3/webhook",
                    json={"url": url},
                    headers={"Authorization": f"Bearer {token}"},
                )
            if r.status_code >= 400:
                return False, f"Avito {r.status_code}: {r.text[:200]}"
        except Exception as e:  # noqa: BLE001
            return False, f"Сетевая ошибка: {e}"
        return True, "Webhook зарегистрирован в Avito ✓"
