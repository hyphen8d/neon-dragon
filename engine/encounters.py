"""Load and roll on the Undercity encounter tables."""

from __future__ import annotations

import json
import random
from pathlib import Path
from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
    from engine.character import Character

CONTENT_PATH = Path(__file__).resolve().parent.parent / "content" / "encounters.json"


def load_encounters() -> list[dict[str, Any]]:
    data = json.loads(CONTENT_PATH.read_text())
    return data["encounters"]


def get_enemy_by_name(name: str) -> dict[str, Any]:
    """Look up a combat encounter's enemy dict by its display name — used
    by "coerce" quest steps (engine/quests.py) to build the fail-state
    fight from a plain enemy name in content/quests.json, the same enemy
    data Undercity random encounters already use."""
    for encounter in load_encounters():
        if encounter["type"] == "combat" and encounter["enemy"]["name"] == name:
            return encounter["enemy"]
    raise KeyError(name)


def _eligible(character: "Character") -> list[dict[str, Any]]:
    """Encounters the player's level qualifies for. A `requires_kill` entry
    (e.g. the Draxx grudge match) only enters the pool once that enemy's
    name shows up in character.kills — the Undercity noticing what
    happened in the Pit, not a generic level gate."""
    eligible = []
    for e in load_encounters():
        if character.level < e.get("min_level", 1):
            continue
        required = e.get("requires_kill")
        if required and character.kills.get(required, 0) < 1:
            continue
        eligible.append(e)
    return eligible


def _weighted_pick(pool: list[dict[str, Any]]) -> dict[str, Any]:
    weights = [e["weight"] for e in pool]
    return random.choices(pool, weights=weights, k=1)[0]


def roll_combat_encounter(character: "Character", faction: str | None = None) -> dict[str, Any]:
    """Roll among combat encounters the player qualifies for, optionally
    restricted to one faction (used for Jack In's "traced" consequence)."""
    pool = [e for e in _eligible(character) if e["type"] == "combat"]
    if faction:
        pool = [e for e in pool if e["enemy"].get("faction") == faction]
    return _weighted_pick(pool)


def roll_scavenge_encounter(character: "Character") -> dict[str, Any]:
    """Roll among the low-risk loot/nothing encounters."""
    pool = [e for e in _eligible(character) if e["type"] in ("loot", "nothing")]
    return _weighted_pick(pool)
