"""Level-up progression, triggered whenever a character gains XP."""

from __future__ import annotations

from rich.console import Console

from engine.character import Character

XP_PER_LEVEL = 50

# Flat stat growth applied per level gained. Charisma is left out —
# it has no mechanical effect anywhere yet, so growing it would be noise.
STAT_GROWTH = {"max_hp": 3, "attack": 1, "defense": 1, "tech": 1}


def level_for_xp(xp: int) -> int:
    return 1 + xp // XP_PER_LEVEL


def xp_for_next_level(character: Character) -> int:
    return character.level * XP_PER_LEVEL


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
            f"\n[bold bright_magenta]LEVEL UP![/bold bright_magenta] "
            f"{character.name} reaches level {character.level}. "
            f"+{STAT_GROWTH['max_hp']} Max HP, +{STAT_GROWTH['attack']} Attack, "
            f"+{STAT_GROWTH['defense']} Defense, +{STAT_GROWTH['tech']} Tech — "
            f"and fully healed."
        )
