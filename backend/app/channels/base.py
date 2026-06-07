from abc import ABC, abstractmethod


class ChannelAdapter(ABC):
    """One adapter per channel type. `send` delivers an outbound reply.

    `verify` checks the stored credentials and returns (ok, human_message).
    """

    type: str = "base"
    live: bool = False

    @abstractmethod
    async def send(self, config: dict, external_id: str, text: str) -> None: ...

    async def verify(self, config: dict) -> tuple[bool, str]:
        return True, "OK"

    async def enrich_config(self, config: dict) -> dict:
        """Optionally derive/fill config fields (e.g. fetch an account id).

        Called before verify/save. Returns the (possibly updated) config.
        No-op by default — adapters override when they can auto-discover values.
        """
        return config
