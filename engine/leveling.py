"""Level-up progression, triggered whenever a character gains XP."""

from __future__ import annotations

from rich.console import Console
from rich.panel import Panel

from engine.achievements import check_achievements
from engine.character import Character
from engine.theme import ACCENT, BORDER_ACCENT, TEXT_DIM
from engine.ui import hotkey_prompt, press_any_key

XP_STEP = 50

# Flat stat growth applied per level gained. Charisma is left out of the
# automatic growth (it stays an opt-in build choice via
# LEVEL_UP_BONUS_STATS below, plus Buy a Round) rather than growing on
# every level regardless of build, the way combat stats do.
STAT_GROWTH = {"max_hp": 3, "attack": 1, "defense": 1, "tech": 1}

# On top of the flat STAT_GROWTH, the player picks one of these to bump an
# extra point — the one build-crafting decision in an otherwise fully
# deterministic level-up, so Street Samurai vs. Netrunner can diverge
# further than their starting templates over a playthrough. Charisma is
# included here (not in STAT_GROWTH) specifically so it has a genuine,
# level-up-paced growth path instead of being locked entirely behind
# skin-slot cyberware (Synth-Derm/Mirrorskin) — see also Buy a Round's
# stat encounters in engine/hub.py.
LEVEL_UP_BONUS_STATS: dict[str, tuple[str, str]] = {
    "A": ("attack", "Attack"),
    "D": ("defense", "Defense"),
    "T": ("tech", "Tech"),
    "C": ("charisma", "Charisma"),
}


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

        body = (
            f"[{ACCENT}]{character.name} reaches level {character.level}.[/{ACCENT}]\n"
            f"[{TEXT_DIM}]+{STAT_GROWTH['max_hp']} Max HP, +{STAT_GROWTH['attack']} Attack, "
            f"+{STAT_GROWTH['defense']} Defense, +{STAT_GROWTH['tech']} Tech — "
            f"and fully healed.[/{TEXT_DIM}]"
        )
        console.print()
        console.print(
            Panel(
                body,
                title=f"[{ACCENT}]LEVEL UP[/{ACCENT}]",
                border_style=BORDER_ACCENT,
                padding=(1, 2),
            )
        )
        press_any_key(console, "[SYS] STANDBY // PRESS ANY KEY TO ALLOCATE STAT_")

        options = [(key, label) for key, (_, label) in LEVEL_UP_BONUS_STATS.items()]
        choice = hotkey_prompt(console, options, prompt="Put a bonus point somewhere:")
        attr, label = LEVEL_UP_BONUS_STATS[choice]
        setattr(character, attr, getattr(character, attr) + 1)
        console.print(f"[{ACCENT}]+1 {label}[/{ACCENT}], your call.")

        check_achievements(character, console)
