"""Achievements & Milestones: evaluates character state against
content/achievements.json and unlocks/announces new ones.

Includes the "RoboDOJO belt ranks" idea floated in GAME_DESIGN.md's Future
Ideas section — stat-threshold achievements (Black Belt) that also grant a
small permanent combat passive once unlocked, applied in engine/combat.py."""

from __future__ import annotations

import json
from pathlib import Path

from rich.console import Console
from rich.panel import Panel

from engine.character import CLASSES, CYBERWARE_SLOTS, Character
from engine.theme import ACCENT, BORDER_RARE, RARE, TEXT_DIM

CONTENT_PATH = Path(__file__).resolve().parent.parent / "content" / "achievements.json"


def load_achievements() -> list[dict]:
    data = json.loads(CONTENT_PATH.read_text())
    return data["achievements"]


def _faction_kills(character: Character, faction: str) -> int:
    from engine.bestiary import enemy_faction

    return sum(count for name, count in character.kills.items() if enemy_faction(name) == faction)


def _equipped_count(character: Character) -> int:
    return sum(1 for slot in CYBERWARE_SLOTS if character.cyberware.get(slot))


def _condition_met(character: Character, condition: dict) -> bool:
    kind = condition["type"]
    if kind == "kill":
        return character.kills.get(condition["target"], 0) > 0
    if kind == "faction_kills":
        return _faction_kills(character, condition["faction"]) >= condition["min"]
    if kind == "cyberware_equipped":
        return _equipped_count(character) >= condition["min"]
    if kind == "stat":
        return getattr(character, condition["stat"], 0) >= condition["min"]
    if kind == "stat_gain":
        # Measured relative to the character's class starting value, not
        # an absolute number -- a flat threshold (e.g. "Attack >= 10")
        # was trivial for a class whose starting stat was already close
        # to it and a much bigger ask for a class starting far below it.
        stat = condition["stat"]
        baseline = CLASSES[character.char_class][stat]
        return getattr(character, stat, 0) - baseline >= condition["min_gain"]
    return False


def check_achievements(character: Character, console: Console) -> list[dict]:
    """Evaluate every locked achievement against the character's current
    state. Unlocks and announces any newly-earned ones (appending their id
    to character.achievements), and returns the list of achievement dicts
    unlocked just now — callers can ignore the return value if they don't
    need it."""
    newly_unlocked: list[dict] = []
    for achievement in load_achievements():
        if achievement["id"] in character.achievements:
            continue
        if not _condition_met(character, achievement["condition"]):
            continue
        character.achievements.append(achievement["id"])
        newly_unlocked.append(achievement)
        _announce(console, achievement)
    return newly_unlocked


def _announce(console: Console, achievement: dict) -> None:
    body = (
        f"[{ACCENT}]{achievement['name']}[/{ACCENT}]\n"
        f"[{TEXT_DIM}]{achievement['description']}[/{TEXT_DIM}]"
    )
    console.print(
        Panel(
            body,
            title=f"[{RARE}]ACHIEVEMENT UNLOCKED[/{RARE}]",
            border_style=BORDER_RARE,
            padding=(1, 2),
        )
    )
