"""New-merc prologue: a scripted wake-up-in-the-clinic scene and tutorial
fight, run once between character creation and the player's first drop
into the hub."""

from __future__ import annotations

from rich.console import Console

from engine.character import Character
from engine.combat import run_combat
from engine.shop import get_item
from engine.theme import ACCENT, DANGER, INFO, ITALIC, LABEL, NAME, TEXT_DIM, WARNING
from engine.ui import press_any_key

# Debt Doc Wire puts the player in for patching them up — the whole reason
# they need to hit the Fixer Board or Chrome Noodle Bar once the prologue ends.
STARTING_DEBT = -150

# The starter chrome Doc Wire hands out, keyed by class so each archetype
# gets a bonus matching its headline stat (attack for Samurai, tech for
# Netrunner).
STARTER_GEAR: dict[str, str] = {
    "Street Samurai": "chrome_arm_mk1",
    "Netrunner": "optic_scanner",
}

TUTORIAL_ENEMY: dict = {
    "name": "Malfunctioning Med-Drone",
    "hp": 15,
    "attack": 3,
    "defense": 2,
    "credits_reward": 0,
    "xp_reward": 0,
    "is_droid": True,
    "faction": "Malfunctioning Hardware",
    "scan_desc": "A clinic drone, seized up and swinging its IV pole like a weapon.",
}

CLASS_SPECIAL_HINT: dict[str, str] = {
    "Street Samurai": "your Samurai Slash",
    "Netrunner": "your Override System",
}


def _equip_starter_gear(character: Character, console: Console) -> None:
    item_id = STARTER_GEAR.get(character.char_class)
    if item_id is None:
        return
    item = get_item(item_id)
    setattr(character, item["stat"], getattr(character, item["stat"]) + item["bonus"])
    character.cyberware[item["slot"]] = item_id
    console.print(
        f"[{INFO}]Doc Wire[/{INFO}] tosses you a [{ACCENT}]{item['name']}[/{ACCENT}]. "
        f"\"On the house. Well — on your tab.\"\n"
    )


def run_prologue(character: Character, console: Console) -> None:
    console.rule(f"[{LABEL}]Prologue[/{LABEL}]")
    console.print(
        f"[{ITALIC}]Fluorescent light. The smell of solder and antiseptic. Your last "
        f"memory is a job going sideways in an alley off the Fixer Board's turf — "
        f"then nothing.[/{ITALIC}]\n"
    )
    press_any_key(console, "[SYS] REGAINING CONSCIOUSNESS // PRESS ANY KEY_")

    console.print(
        f"You come to on a gurney in [{INFO}]Doc Wire's Clinic[/{INFO}], wires and "
        f"tubes running out of you in directions you'd rather not think about.\n"
    )
    console.print(
        f"[{INFO}]Doc Wire[/{INFO}] leans over, wiping his hands on a rag that's seen "
        f"better decades. \"Patched you up, {character.name}. Wasn't cheap, and it "
        f"sure wasn't free.\"\n"
    )

    character.credits = STARTING_DEBT
    console.print(
        f"[{DANGER}]Your ledger reads {character.credits} credits.[/{DANGER}] You're in the hole "
        f"before you've even hit the street.\n"
    )
    press_any_key(console, "[SYS] DEBT LOGGED // PRESS ANY KEY_")

    _equip_starter_gear(character, console)
    press_any_key(console, "[SYS] CHROME LINKED // PRESS ANY KEY_")

    console.print(
        f"Before you can swing your legs off the gurney, something in the corner "
        f"lets out a grinding whine. The clinic's Med-Drone — the one that's supposed "
        f"to be monitoring your vitals — twitches, sparks, and lurches upright.\n"
    )
    console.print(
        f"[{WARNING}]\"Ah, hell, not again,\"[/{WARNING}] Doc Wire mutters, already backing away. "
        f"\"That thing's been glitching for a week. Don't just lie there, {character.name} — "
        f"put it down!\"\n"
    )
    special_hint = CLASS_SPECIAL_HINT.get(character.char_class)
    if special_hint:
        console.print(
            f"[{TEXT_DIM}]This is as good a time as any to try {special_hint}.[/{TEXT_DIM}]\n"
        )
    press_any_key(console, "[SYS] THREAT DETECTED // PRESS ANY KEY_")

    won = run_combat(character, dict(TUTORIAL_ENEMY))

    if not won:
        character.hp = 10
        console.print(
            f"\n[{INFO}]Doc Wire[/{INFO}] sighs, hauls you back onto the gurney, and jams "
            f"another stim into your arm. \"Guess I'm patching you up twice today. "
            f"That's going on the tab too.\"\n"
        )
        press_any_key(console, "[SYS] STABILIZED // PRESS ANY KEY_")
    else:
        console.print(
            f"\n[{ACCENT}]The drone crashes to the floor in a shower of sparks.[/{ACCENT}] "
            f"Doc Wire nods, almost impressed.\n"
        )

    console.print(
        f"\"{character.name}, you're patched up and you're in the red,\" Doc Wire says, "
        f"jerking a thumb toward the door. \"Fixer Board's got work if you're desperate. "
        f"Chrome Noodle Bar's got noodles and rumors, usually in that order. Either way — "
        f"go earn your keep.\"\n"
    )
    press_any_key(console, "[SYS] PROLOGUE COMPLETE // PRESS ANY KEY_")
