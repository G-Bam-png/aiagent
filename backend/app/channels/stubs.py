"""Scaffolded adapters for channels that require platform approval / OAuth.

They implement the full interface so the rest of the system treats them like any
other channel. `verify` checks that the required credential fields are present;
`send` logs the outbound payload. Wire the real HTTP call where marked TODO.
"""

import logging

from ..catalog import CHANNEL_BY_TYPE
from .base import ChannelAdapter

log = logging.getLogger("channels")


class _ScaffoldAdapter(ChannelAdapter):
    live = False

    async def send(self, config: dict, external_id: str, text: str) -> None:
        # TODO: implement the platform's real outbound API call here.
        log.info("[%s] outbound → %s: %s", self.type, external_id, text)

    async def verify(self, config: dict) -> tuple[bool, str]:
        required = CHANNEL_BY_TYPE.get(self.type, {}).get("fields", [])
        missing = [f for f in required if not config.get(f)]
        if missing:
            return False, f"Не хватает полей: {', '.join(missing)}"
        return True, "Учётные данные сохранены (адаптер в режиме заглушки)"


class WhatsAppAdapter(_ScaffoldAdapter):
    type = "whatsapp"


class InstagramAdapter(_ScaffoldAdapter):
    type = "instagram"


class VKAdapter(_ScaffoldAdapter):
    type = "vk"


class YouTubeAdapter(_ScaffoldAdapter):
    type = "youtube"


class TikTokAdapter(_ScaffoldAdapter):
    type = "tiktok"
