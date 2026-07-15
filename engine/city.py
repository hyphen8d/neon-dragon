"""Ambient City Conditions — weather and headline flavor for the Daily Data
Feed. Rolled once per sleep and stored on the Character (current_weather,
current_headline) so they persist for the whole day rather than being
re-rolled on every read. Most entries are pure worldbuilding, but a
`type` field on some marks a real mechanical effect elsewhere in the
engine: weather's "tech_interference" (engine/combat.py) and headlines'
"market_surge"/"market_discount" (engine/shop.py's roll_daily_market)."""

from __future__ import annotations

import json
import random
from pathlib import Path
from typing import Any

CONTENT_PATH = Path(__file__).resolve().parent.parent / "content" / "city_conditions.json"


def load_city_conditions() -> dict[str, Any]:
    return json.loads(CONTENT_PATH.read_text())


def roll_weather() -> dict[str, Any]:
    return random.choice(load_city_conditions()["weather"])


def roll_headline() -> dict[str, Any]:
    return random.choice(load_city_conditions()["headlines"])
