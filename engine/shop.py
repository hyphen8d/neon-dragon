"""Load Hyphen8d's Hut cyberware catalog and handle buying/selling/equipping."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from engine.character import Character

CONTENT_PATH = Path(__file__).resolve().parent.parent / "content" / "items.json"

SELL_BACK_RATE = 0.5

# Every point of Charisma haggles 2% off cyberware, capped at 40% —
# the Grifter's headline economic edge (see CLASSES in character.py).
CHARISMA_DISCOUNT_PER_POINT = 0.02
CHARISMA_DISCOUNT_CAP = 0.40


def load_cyberware() -> list[dict[str, Any]]:
    data = json.loads(CONTENT_PATH.read_text())
    return data["cyberware"]


def get_item(item_id: str) -> dict[str, Any]:
    for item in load_cyberware():
        if item["id"] == item_id:
            return item
    raise KeyError(item_id)


def _apply_bonus(character: Character, item: dict[str, Any], sign: int) -> None:
    stat = item["stat"]
    setattr(character, stat, getattr(character, stat) + sign * item["bonus"])


def sell_back_value(item: dict[str, Any]) -> int:
    return int(item["cost"] * SELL_BACK_RATE)


def discounted_cost(character: Character, item: dict[str, Any]) -> int:
    """Charisma haggles down cyberware prices — 2% off per point, capped at 40%."""
    discount = min(CHARISMA_DISCOUNT_CAP, character.charisma * CHARISMA_DISCOUNT_PER_POINT)
    return int(item["cost"] * (1 - discount))


def unequip(character: Character, slot: str) -> dict[str, Any] | None:
    """Remove whatever's in a slot and refund its trade-in value. Returns the removed item, or None."""
    item_id = character.cyberware.get(slot)
    if item_id is None:
        return None
    item = get_item(item_id)
    _apply_bonus(character, item, sign=-1)
    character.credits += sell_back_value(item)
    character.cyberware[slot] = None
    return item


def buy_and_equip(character: Character, item_id: str) -> dict[str, Any]:
    """Buy an item, swapping out (and refunding) whatever currently fills its slot."""
    item = get_item(item_id)
    unequip(character, item["slot"])
    character.credits -= discounted_cost(character, item)
    _apply_bonus(character, item, sign=1)
    character.cyberware[item["slot"]] = item["id"]
    return item
