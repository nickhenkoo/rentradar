from abc import ABC, abstractmethod
from core.models import Listing


class BaseParser(ABC):
    SOURCE: str = ""

    @abstractmethod
    async def fetch_listings(self) -> list[Listing]:
        """Fetch latest listings from source. Return list of Listing objects."""
        ...
