from .avito import AvitoAdapter
from .base import ChannelAdapter
from .stubs import (
    InstagramAdapter,
    TikTokAdapter,
    VKAdapter,
    WhatsAppAdapter,
    YouTubeAdapter,
)
from .telegram import TelegramAdapter
from .web import WebAdapter

_ADAPTERS: dict[str, ChannelAdapter] = {
    a.type: a
    for a in (
        WebAdapter(),
        AvitoAdapter(),
        TelegramAdapter(),
        WhatsAppAdapter(),
        InstagramAdapter(),
        VKAdapter(),
        YouTubeAdapter(),
        TikTokAdapter(),
    )
}


def get_adapter(channel_type: str) -> ChannelAdapter | None:
    return _ADAPTERS.get(channel_type)


async def verify_channel(channel_type: str, config: dict) -> tuple[bool, str]:
    adapter = get_adapter(channel_type)
    if not adapter:
        return False, f"Неизвестный тип канала: {channel_type}"
    return await adapter.verify(config)


async def enrich_channel_config(channel_type: str, config: dict) -> dict:
    adapter = get_adapter(channel_type)
    if not adapter:
        return config
    return await adapter.enrich_config(config)
