"""Status effect application, per-round ticking, and curing.

Works on both the player Character and combat Enemy objects — anything
with .hp, .name, and .status_effects attributes.
"""

from __future__ import annotations

from typing import Any

from rich.console import Console

from engine.theme import DANGER, TEXT_DIM, WARNING

BLEED_DAMAGE = 3

# Glyph badges, pre-colored WARNING so any consumer (combat lines, HUD
# panels, character-info tables) gets a striking, consistently-styled
# status tag just by dropping the label in — no extra markup needed.
EFFECT_LABELS: dict[str, str] = {
    "bleed": f"[{WARNING}][🩸 BLEED][/{WARNING}]",
    "stunned": f"[{WARNING}][⚡ STUN][/{WARNING}]",
    "drunk": f"[{WARNING}][☣ DRUNK][/{WARNING}]",
    "overclock": f"[{WARNING}][⚡ OVERCLOCK][/{WARNING}]",
}

# Plain adjective form for narration that embeds the effect mid-sentence
# (e.g. "leaves you bleeding!") — EFFECT_LABELS is a styled badge, not
# grammatical prose, so it can't just be lowercased for that.
EFFECT_ADJECTIVES: dict[str, str] = {
    "bleed": "bleeding",
    "stunned": "stunned",
    "drunk": "drunk",
    "overclock": "overclocked",
}

DRUNK_STAT_PENALTY = 3

# How long the crash-Bleed lasts once an Overclock Injector's buff (see
# engine/combat.py's OVERCLOCK_ATTACK_BONUS) wears off -- the high-risk
# half of that item's high-risk/high-reward deal.
OVERCLOCK_CRASH_BLEED_DURATION = 3


def apply_effect(combatant: Any, effect: str, duration: int) -> bool:
    """Apply a status effect. Returns False (and does nothing) if the
    combatant is immune — currently just droids, who have no blood to
    bleed, so Bleed never lands on them regardless of source."""
    if effect == "bleed" and getattr(combatant, "is_droid", False):
        return False
    combatant.status_effects[effect] = max(combatant.status_effects.get(effect, 0), duration)
    return True


def has_effect(combatant: Any, effect: str) -> bool:
    return combatant.status_effects.get(effect, 0) > 0


def process_round_start(combatant: Any, console: Console, is_player: bool = False) -> bool:
    """Apply bleed damage and decay every active effect by one round.
    Returns True if the combatant was stunned at the start of this round
    (checked before decay, so a 1-round stun still blocks this round's action)."""
    subject = "You" if is_player else combatant.name
    stunned = has_effect(combatant, "stunned")

    if has_effect(combatant, "bleed"):
        old_hp = combatant.hp
        combatant.hp = max(0, combatant.hp - BLEED_DAMAGE)
        new_hp = combatant.hp
        verb = "bleed" if is_player else "bleeds"
        hp_label = "Your" if is_player else combatant.name
        console.print(
            f"[{DANGER}]{subject} {verb} for {BLEED_DAMAGE} damage.[/{DANGER}] "
            f"[{TEXT_DIM}]({hp_label} HP: {old_hp} -> {new_hp})[/{TEXT_DIM}]"
        )

    for effect in list(combatant.status_effects.keys()):
        combatant.status_effects[effect] -= 1
        if combatant.status_effects[effect] <= 0:
            del combatant.status_effects[effect]
            label = EFFECT_LABELS.get(effect, effect)
            possessive = "Your" if is_player else f"{combatant.name}'s"
            console.print(f"[{TEXT_DIM}]{possessive} {label} wears off.[/{TEXT_DIM}]")
            if effect == "overclock":
                # The crash -- an Overclock Injector's Attack buff always
                # leaves you bleeding the moment it expires, win or lose.
                apply_effect(combatant, "bleed", OVERCLOCK_CRASH_BLEED_DURATION)
                verb = "start" if is_player else "starts"
                console.print(f"[{DANGER}]The crash hits hard — {subject} {verb} bleeding.[/{DANGER}]")

    return stunned


def cure_all(combatant: Any) -> int:
    """Remove all status effects. Returns how many were cured."""
    count = len(combatant.status_effects)
    combatant.status_effects.clear()
    return count
