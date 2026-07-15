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


# Trash-mob fatigue: a combat encounter's pick weight is untouched until
# the player is OUTLEVEL_GRACE+ levels above its min_level, then halves
# per level past that (capped so it never bottoms out at 0 and a pick
# stays possible). Without this, the original min_level-1 enemies (Street
# Ganger, Rogue Drone, etc.) stay in the pool at full weight forever as
# tougher encounters are only ever added on top, not swapped in — by
# level 9 they made up ~59% of the total pick weight. This tapers that
# down instead of hard-excluding them, so Undercity fights skew toward
# appropriately-tiered content as a character levels, while low-tier
# enemies still turn up occasionally (which is also what Intimidate is
# for — see engine/combat.py).
OUTLEVEL_GRACE = 2
OUTLEVEL_HALVING_CAP = 4


def _combat_weight(character: "Character", encounter: dict[str, Any]) -> int:
    # Boss/callback encounters (requires_kill, e.g. the Draxx grudge
    # match) are exempt -- those are meant to persist, not fade out.
    if encounter.get("requires_kill"):
        return encounter["weight"]
    gap = character.level - encounter.get("min_level", 1)
    if gap <= OUTLEVEL_GRACE:
        return encounter["weight"]
    halvings = min(gap - OUTLEVEL_GRACE, OUTLEVEL_HALVING_CAP)
    return max(1, encounter["weight"] // (2**halvings))


def roll_combat_encounter(character: "Character", faction: str | None = None) -> dict[str, Any]:
    """Roll among combat encounters the player qualifies for, optionally
    restricted to one faction (used for Jack In's "traced" consequence).
    Weighted by _combat_weight rather than the encounter's raw weight, so
    the pool skews toward the player's current tier instead of staying
    static across the whole game."""
    pool = [e for e in _eligible(character) if e["type"] == "combat"]
    if faction:
        pool = [e for e in pool if e["enemy"].get("faction") == faction]
    weights = [_combat_weight(character, e) for e in pool]
    return random.choices(pool, weights=weights, k=1)[0]


def roll_scavenge_encounter(character: "Character") -> dict[str, Any]:
    """Roll among the low-risk loot/nothing encounters."""
    pool = [e for e in _eligible(character) if e["type"] in ("loot", "nothing")]
    return _weighted_pick(pool)
