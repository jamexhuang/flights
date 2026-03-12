from __future__ import annotations

from base64 import b64encode
from dataclasses import dataclass

from .types import ShoppingRankingMode, ShoppingResultSort


SHOPPING_RANKING_IDS: dict[ShoppingRankingMode, int] = {
    "best": 1,
    "cheapest": 2,
}

SHOPPING_SORT_IDS: dict[ShoppingResultSort, int] = {
    "top_flights": 1,
    "price": 2,
    "departure_time": 3,
    "arrival_time": 4,
    "duration": 5,
    "emissions": 6,
}

SHOPPING_ID_TO_RANKING: dict[int, ShoppingRankingMode] = {
    value: key for key, value in SHOPPING_RANKING_IDS.items()
}


@dataclass(frozen=True)
class ShoppingOptions:
    ranking_mode: ShoppingRankingMode = "best"
    result_sort: ShoppingResultSort = "top_flights"

    @property
    def ranking_id(self) -> int:
        return SHOPPING_RANKING_IDS[self.ranking_mode]

    @property
    def sort_id(self) -> int:
        return SHOPPING_SORT_IDS[self.result_sort]

    def tfu(self) -> str:
        payload = bytes(
            [
                0x12,
                0x0A,
                0x08,
                self.sort_id,
                0x10,
                0x00,
                0x18,
                0x00,
                0x20,
                self.ranking_id,
                0x28,
                0x0E if self.ranking_mode == "best" else 0x0F,
            ]
        )
        return b64encode(payload).decode("utf-8")
