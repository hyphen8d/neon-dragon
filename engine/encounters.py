"""Load and roll on the Undercity encounter tables."""

from __future__ import annotations

import json
import random
from pathlib import Path
from typing import Any

CONTENT_PATH = Path(__file__).resolve().parent.parent / "content" / "encounters.json"


def load_encounters() -> list[dict[str, Any]]:
    data = json.loads(CONTENT_PATH.read_text())
    return data["encounters"]


def _eligible(character_level: int) -> list[dict[str, Any]]:
    return [e for e in load_encounters() if character_level >= e.get("min_level", 1)]


def _weighted_pick(pool: list[dict[str, Any]]) -> dict[str, Any]:
    weights = [e["weight"] for e in pool]
    return random.choices(pool, weights=weights, k=1)[0]


def roll_combat_encounter(character_level: int, faction: str | None = None) -> dict[str, Any]:
    """Roll among combat encounters the player's level qualifies for, optionally
    restricted to one faction (used for Jack In's "traced" consequence)."""
    pool = [e for e in _eligible(character_level) if e["type"] == "combat"]
    if faction:
        pool = [e for e in pool if e["enemy"].get("faction") == faction]
    return _weighted_pick(pool)


def roll_scavenge_encounter(character_level: int) -> dict[str, Any]:
    """Roll among the low-risk loot/nothing encounters."""
    pool = [e for e in _eligible(character_level) if e["type"] in ("loot", "nothing")]
    return _weighted_pick(pool)
