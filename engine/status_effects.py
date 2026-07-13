"""Status effect application, per-round ticking, and curing.

Works on both the player Character and combat Enemy objects — anything
with .hp, .name, and .status_effects attributes.
"""

from __future__ import annotations

from typing import Any

from rich.console import Console

BLEED_DAMAGE = 3

EFFECT_LABELS: dict[str, str] = {
    "bleed": "Bleeding",
    "stunned": "Stunned",
    "drunk": "Drunk",
}

DRUNK_STAT_PENALTY = 3


def apply_effect(combatant: Any, effect: str, duration: int) -> None:
    combatant.status_effects[effect] = max(combatant.status_effects.get(effect, 0), duration)


def has_effect(combatant: Any, effect: str) -> bool:
    return combatant.status_effects.get(effect, 0) > 0


def process_round_start(combatant: Any, console: Console, is_player: bool = False) -> bool:
    """Apply bleed damage and decay every active effect by one round.
    Returns True if the combatant was stunned at the start of this round
    (checked before decay, so a 1-round stun still blocks this round's action)."""
    subject = "You" if is_player else combatant.name
    stunned = has_effect(combatant, "stunned")

    if has_effect(combatant, "bleed"):
        combatant.hp = max(0, combatant.hp - BLEED_DAMAGE)
        verb = "bleed" if is_player else "bleeds"
        console.print(f"[red]{subject} {verb} for {BLEED_DAMAGE} damage.[/red]")

    for effect in list(combatant.status_effects.keys()):
        combatant.status_effects[effect] -= 1
        if combatant.status_effects[effect] <= 0:
            del combatant.status_effects[effect]
            label = EFFECT_LABELS.get(effect, effect)
            possessive = "Your" if is_player else f"{combatant.name}'s"
            console.print(f"[dim]{possessive} {label} wears off.[/dim]")

    return stunned


def cure_all(combatant: Any) -> int:
    """Remove all status effects. Returns how many were cured."""
    count = len(combatant.status_effects)
    combatant.status_effects.clear()
    return count
