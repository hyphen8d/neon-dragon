"""Load and roll on the Undercity random encounter table."""

from __future__ import annotations

import json
import random
from pathlib import Path
from typing import Any

CONTENT_PATH = Path(__file__).resolve().parent.parent / "content" / "encounters.json"


def load_encounters() -> list[dict[str, Any]]:
    data = json.loads(CONTENT_PATH.read_text())
    return data["encounters"]


def roll_encounter(character_level: int) -> dict[str, Any]:
    """Roll among encounters the player's level qualifies for. Higher-tier
    threats stay out of the pool until you're leveled enough to meet them."""
    encounters = [e for e in load_encounters() if character_level >= e.get("min_level", 1)]
    weights = [e["weight"] for e in encounters]
    return random.choices(encounters, weights=weights, k=1)[0]
