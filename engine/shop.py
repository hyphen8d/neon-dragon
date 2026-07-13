"""Load Hyphen8d's Hut cyberware catalog and handle buying/selling/equipping."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from engine.character import Character

CONTENT_PATH = Path(__file__).resolve().parent.parent / "content" / "items.json"

SELL_BACK_RATE = 0.5


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
    character.credits -= item["cost"]
    _apply_bonus(character, item, sign=1)
    character.cyberware[item["slot"]] = item["id"]
    return item
