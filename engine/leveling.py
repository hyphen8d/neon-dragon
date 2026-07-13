"""Level-up progression, triggered whenever a character gains XP."""

from __future__ import annotations

from rich.console import Console

from engine.character import Character
from engine.theme import ACCENT

XP_STEP = 50

# Flat stat growth applied per level gained. Charisma is left out —
# it has no mechanical effect anywhere yet, so growing it would be noise.
STAT_GROWTH = {"max_hp": 3, "attack": 1, "defense": 1, "tech": 1}


def xp_for_level(level: int) -> int:
    """Total cumulative XP required to reach this level. Each level costs
    XP_STEP more than the last (level 2 costs 50, level 3 costs 100 more,
    level 4 costs 150 more...), so the curve steepens instead of staying flat."""
    return XP_STEP * level * (level - 1) // 2


def level_for_xp(xp: int) -> int:
    level = 1
    while xp_for_level(level + 1) <= xp:
        level += 1
    return level


def xp_for_next_level(character: Character) -> int:
    return xp_for_level(character.level + 1)


def check_level_up(character: Character, console: Console) -> None:
    """Apply any level(s) earned since the last XP gain. Handles multi-level
    jumps (e.g. a big quest reward) by looping one level at a time."""
    target_level = level_for_xp(character.xp)
    while character.level < target_level:
        character.level += 1
        for stat, amount in STAT_GROWTH.items():
            setattr(character, stat, getattr(character, stat) + amount)
        character.hp = character.max_hp

        console.print(
            f"\n[{ACCENT}]LEVEL UP![/{ACCENT}] "
            f"{character.name} reaches level {character.level}. "
            f"+{STAT_GROWTH['max_hp']} Max HP, +{STAT_GROWTH['attack']} Attack, "
            f"+{STAT_GROWTH['defense']} Defense, +{STAT_GROWTH['tech']} Tech — "
            f"and fully healed."
        )
