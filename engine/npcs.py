"""Load NPC definitions and pick dialogue lines."""

from __future__ import annotations

import json
import random
from pathlib import Path
from typing import TYPE_CHECKING, Any

from engine.bestiary import enemy_faction

if TYPE_CHECKING:
    from engine.character import Character

CONTENT_PATH = Path(__file__).resolve().parent.parent / "content" / "npcs.json"


def load_npcs() -> list[dict[str, Any]]:
    data = json.loads(CONTENT_PATH.read_text())
    return data["npcs"]


def npc_at(location: str) -> dict[str, Any] | None:
    for npc in load_npcs():
        if npc["location"] == location:
            return npc
    return None


def get_npc(npc_id: str) -> dict[str, Any]:
    for npc in load_npcs():
        if npc["id"] == npc_id:
            return npc
    raise KeyError(npc_id)


def _condition_value(character: "Character", condition: str) -> float:
    """Resolve a conditional_lines condition key to a number, checked
    against that line's `min` in random_line. Reuses existing Character
    fields only — no new state added just for flavor text."""
    if condition == "corp_kills":
        return sum(count for name, count in character.kills.items() if enemy_faction(name) == "Corp")
    if condition == "street_gang_kills":
        return sum(count for name, count in character.kills.items() if enemy_faction(name) == "Street Gang")
    if condition == "total_kills":
        return sum(character.kills.values())
    if condition == "quantum_cores":
        return character.quantum_cores
    if condition == "completed_quests":
        return len(character.completed_quests)
    if condition == "charisma":
        return character.charisma
    if condition == "banked_credits":
        return character.banked_credits
    if condition == "in_debt":
        return 1 if character.credits < 0 else 0
    if condition == "learned_abilities":
        return len(character.learned_abilities)
    if condition.startswith("equipped_"):
        item_id = condition[len("equipped_"):]
        return 1 if item_id in character.cyberware.values() else 0
    return 0


def random_line(npc: dict[str, Any], character: "Character | None" = None) -> str:
    """Pick a line of dialogue. When `character` is given and any of the
    NPC's conditional_lines thresholds are met, picks among those instead
    of the generic pool — the world noticing what you've actually done,
    not just idle flavor. Falls back to the generic pool otherwise."""
    if character is not None:
        eligible = [
            cl["line"]
            for cl in npc.get("conditional_lines", [])
            if _condition_value(character, cl["condition"]) >= cl["min"]
        ]
        if eligible:
            return random.choice(eligible)
    return random.choice(npc["lines"])
