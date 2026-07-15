"""Ambient City Conditions — weather and headline flavor for the Daily Data
Feed. Pure worldbuilding, no mechanical effect: the city moving and
breathing while the player sleeps."""

from __future__ import annotations

import json
import random
from pathlib import Path
from typing import Any

CONTENT_PATH = Path(__file__).resolve().parent.parent / "content" / "city_conditions.json"


def load_city_conditions() -> dict[str, Any]:
    return json.loads(CONTENT_PATH.read_text())


def random_weather() -> str:
    return random.choice(load_city_conditions()["weather"])


def random_headline() -> str:
    return random.choice(load_city_conditions()["headlines"])
