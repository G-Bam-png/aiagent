from .base import ChannelAdapter


class WebAdapter(ChannelAdapter):
    """Website widget: replies are returned synchronously in the HTTP response,
    so there is nothing to push out-of-band."""

    type = "web"
    live = True

    async def send(self, config: dict, external_id: str, text: str) -> None:
        return None

    async def verify(self, config: dict) -> tuple[bool, str]:
        return True, "Виджет готов к встраиванию"
