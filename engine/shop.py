"""Load Hyphen8d's Hut cyberware catalog and handle buying/selling/equipping."""

from __future__ import annotations

import json
import random
from pathlib import Path
from typing import Any

from engine.character import Character

CONTENT_PATH = Path(__file__).resolve().parent.parent / "content" / "items.json"
BLACK_MARKET_PATH = Path(__file__).resolve().parent.parent / "content" / "black_market.json"

SELL_BACK_RATE = 0.5

# Every point of Charisma haggles 2% off cyberware, capped at 40%.
CHARISMA_DISCOUNT_PER_POINT = 0.02
CHARISMA_DISCOUNT_CAP = 0.40

# Daily market: one slot gets a discount or surge, and Hyphen8d only
# stocks a handful of items at a time. Rolled fresh each day the player
# sleeps (see hub.py's _sleep_and_advance_day), stored on the Character.
DAILY_STOCK_SIZE = 4
MARKET_EVENT_TYPES = ("discount", "surge")
MARKET_EVENT_MIN_PERCENT = 0.10
MARKET_EVENT_MAX_PERCENT = 0.30

DISCOUNT_FLAVOR = (
    "a fence is dumping surplus stock",
    "black-market knockoffs flooding the shelves",
    "Hyphen8d's overstocked and wants it gone",
)
SURGE_FLAVOR = (
    "a supply crunch on the parts",
    "corp export controls tightening",
    "street tax hike on the components",
)


def load_cyberware() -> list[dict[str, Any]]:
    data = json.loads(CONTENT_PATH.read_text())
    return data["cyberware"]


def load_black_market() -> list[dict[str, Any]]:
    data = json.loads(BLACK_MARKET_PATH.read_text())
    return data["black_market"]


def get_item(item_id: str) -> dict[str, Any]:
    """Look up an item by id across both the regular catalog and the Black
    Market — anything that can end up in character.cyberware needs to
    resolve here, regardless of which shop it was bought from."""
    for item in load_cyberware():
        if item["id"] == item_id:
            return item
    for item in load_black_market():
        if item["id"] == item_id:
            return item
    raise KeyError(item_id)


def currency_of(item: dict[str, Any]) -> str:
    return item.get("currency", "credits")


def format_price(item: dict[str, Any], amount: int) -> str:
    if currency_of(item) == "quantum_core":
        return f"{amount} Quantum Core{'s' if amount != 1 else ''}"
    return f"{amount} credits"


def _apply_bonus(character: Character, item: dict[str, Any], sign: int) -> None:
    stat = item["stat"]
    setattr(character, stat, getattr(character, stat) + sign * item["bonus"])


def sell_back_value(item: dict[str, Any]) -> int:
    return int(item["cost"] * SELL_BACK_RATE)


def discounted_cost(character: Character, item: dict[str, Any]) -> int:
    """Charisma haggles down cyberware prices — 2% off per point, capped at
    40% — then today's market event (if it hits this item's slot) discounts
    or surges the price further on top."""
    discount = min(CHARISMA_DISCOUNT_CAP, character.charisma * CHARISMA_DISCOUNT_PER_POINT)
    price = item["cost"] * (1 - discount)

    modifier = character.market_modifier
    if modifier and modifier.get("slot") == item["slot"]:
        pct = modifier["percent"]
        if modifier["type"] == "discount":
            price *= 1 - pct
        else:
            price *= 1 + pct

    return max(1, int(price))


def roll_daily_market(character: Character) -> None:
    """Roll a fresh economic modifier and restock Hyphen8d's Hut for the
    day. Called once per day, when the player sleeps."""
    catalog = load_cyberware()
    slot = random.choice(sorted({item["slot"] for item in catalog}))
    event_type = random.choice(MARKET_EVENT_TYPES)
    percent = round(random.uniform(MARKET_EVENT_MIN_PERCENT, MARKET_EVENT_MAX_PERCENT), 2)
    flavor = random.choice(DISCOUNT_FLAVOR if event_type == "discount" else SURGE_FLAVOR)
    character.market_modifier = {"slot": slot, "type": event_type, "percent": percent, "flavor": flavor}
    character.market_stock = [item["id"] for item in random.sample(catalog, min(DAILY_STOCK_SIZE, len(catalog)))]


def get_daily_catalog(character: Character) -> list[dict[str, Any]]:
    """Today's stock at Hyphen8d's Hut. Rolls a fresh market if the
    character has none yet (a brand-new save, or one from before this
    system existed)."""
    if not character.market_stock:
        roll_daily_market(character)
    catalog = load_cyberware()
    by_id = {item["id"]: item for item in catalog}
    return [by_id[item_id] for item_id in character.market_stock if item_id in by_id]


def describe_market_modifier(character: Character) -> str:
    modifier = character.market_modifier
    if not modifier:
        return "Market's steady today — no unusual pricing."
    slot = modifier["slot"].capitalize()
    pct = int(modifier["percent"] * 100)
    verb = "cheaper" if modifier["type"] == "discount" else "pricier"
    return f"{slot} gear is running {pct}% {verb} today — {modifier['flavor']}."


def unequip(character: Character, slot: str) -> dict[str, Any] | None:
    """Remove whatever's in a slot and refund its trade-in value, in
    whichever currency it was originally priced in. Returns the removed
    item, or None."""
    item_id = character.cyberware.get(slot)
    if item_id is None:
        return None
    item = get_item(item_id)
    _apply_bonus(character, item, sign=-1)
    refund = sell_back_value(item)
    if currency_of(item) == "quantum_core":
        character.quantum_cores += refund
    else:
        character.credits += refund
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


def buy_black_market_item(character: Character, item_id: str) -> dict[str, Any]:
    """Buy a Black Market prototype with Quantum Cores instead of credits.
    Fixed price — no Charisma discount, no daily market event. Swaps out
    (and refunds) whatever currently fills its slot, same as buy_and_equip."""
    item = get_black_market_item(item_id)
    unequip(character, item["slot"])
    character.quantum_cores -= item["cost"]
    _apply_bonus(character, item, sign=1)
    character.cyberware[item["slot"]] = item["id"]
    return item


def get_black_market_item(item_id: str) -> dict[str, Any]:
    for item in load_black_market():
        if item["id"] == item_id:
            return item
    raise KeyError(item_id)
