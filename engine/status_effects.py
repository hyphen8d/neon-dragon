"""Status effect application, per-round ticking, and curing."""

from __future__ import annotations

from rich.console import Console

from engine.character import Character

BLEED_DAMAGE = 3

EFFECT_LABELS: dict[str, str] = {
    "bleed": "Bleeding",
    "stunned": "Stunned",
}


def apply_effect(character: Character, effect: str, duration: int) -> None:
    character.status_effects[effect] = max(character.status_effects.get(effect, 0), duration)


def has_effect(character: Character, effect: str) -> bool:
    return character.status_effects.get(effect, 0) > 0


def process_round_start(character: Character, console: Console) -> bool:
    """Apply bleed damage and decay every active effect by one round.
    Returns True if the player was stunned at the start of this round
    (checked before decay, so a 1-round stun still blocks this round's action)."""
    stunned = has_effect(character, "stunned")

    if has_effect(character, "bleed"):
        character.hp = max(0, character.hp - BLEED_DAMAGE)
        console.print(f"[red]Bleeding out: -{BLEED_DAMAGE} HP.[/red]")

    for effect in list(character.status_effects.keys()):
        character.status_effects[effect] -= 1
        if character.status_effects[effect] <= 0:
            del character.status_effects[effect]
            console.print(f"[dim]{EFFECT_LABELS.get(effect, effect)} wears off.[/dim]")

    return stunned


def cure_all(character: Character) -> int:
    """Remove all status effects. Returns how many were cured."""
    count = len(character.status_effects)
    character.status_effects.clear()
    return count
